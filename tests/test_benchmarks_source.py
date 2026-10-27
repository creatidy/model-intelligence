import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import cast
from unittest.mock import patch

from test_router_conformance import DAY, T

from model_intelligence.acquisition import Capture
from model_intelligence.benchmarks import SCOPE, SOURCES, compare, normalize, refresh
from model_intelligence.contract import NATIVE_PAYLOAD_SCHEMA, decode_public_evidence, encode_public_evidence
from model_intelligence.evidence import Benchmark, ModelClaim
from model_intelligence.operator import snapshot
from model_intelligence.producer import publish, retained
from model_intelligence.zai import SCOPE as ZAI_SCOPE

TEXT = {
    "models-dev:sol": 'schema = 2\nname = "GPT-6.1 Sol"\nrelease_date = "2026-09-29"\n',
    "models-dev:luna": (
        'schema = 2\nname = "GPT-6 Luna"\n'
        '[[benchmarks]]\nname = "DeepSWE"\nscore = 66.6\nmetric = "score"\n'
        'version = "1.1"\nvariant = "max effort"\n'
        'source = "https://openai.com/index/introducing-gpt-6-sol-and-luna/"\n'
        'date = "2026-09-22"\n'
    ),
    "models-dev:glm": (
        'schema = 2\nname = "GLM-5.3"\n'
        '[[benchmarks]]\nname = "DeepSWE"\nscore = 66.9\nmetric = "resolved"\n'
        'version = "1.1"\nvariant = "max effort; 6h timeout; 400K context"\n'
        'harness = "mini-swe-agent"\nsource = "https://huggingface.co/zai-org/GLM-5.3"\n'
        '[[benchmarks]]\nname = "SWE-Marathon"\nscore = 42.5\nmetric = "score"\n'
        'version = "1.1"\nvariant = "max effort; modified anti-cheat checks"\n'
        'harness = "Claude Code 2.1.207"\nsource = "https://huggingface.co/zai-org/GLM-5.3"\n'
    ),
    "models-dev:flash": (
        'schema = 2\nname = "GLM-5.3-Flash"\n'
        '[[benchmarks]]\nname = "DeepSWE"\nscore = 63.4\nmetric = "resolved"\n'
        'version = "1.1"\nvariant = "max effort"\nharness = "mini-swe-agent"\n'
        'source = "https://huggingface.co/zai-org/GLM-5.3-Flash"\n'
    ),
}


def captures(*, texts: dict[str, str] | None = None, at: datetime = T) -> tuple[Capture, ...]:
    contents = TEXT if texts is None else texts
    return tuple(Capture(source, contents[source.source_id].encode(), at) for source in SOURCES)


def benchmark(claim: ModelClaim) -> Benchmark:
    if not isinstance(claim.payload, Benchmark):
        raise AssertionError("expected benchmark claim")
    return claim.payload


class CodingBenchmarkTests(unittest.TestCase):
    def test_pinned_subset_is_separate_from_zai_and_preserves_native_claims(self) -> None:
        self.assertNotEqual(SCOPE, ZAI_SCOPE)
        public = normalize(captures(), at=T)
        records = [claim for claim in public.evidence.claims if isinstance(claim, ModelClaim)]
        self.assertEqual(len(records), 4)
        self.assertEqual(
            {(claim.subject.model_id, benchmark(claim).name, benchmark(claim).value) for claim in records},
            {
                ("openai/gpt-6-luna", "DeepSWE", Decimal("66.6")),
                ("zhipuai/glm-5.3", "DeepSWE", Decimal("66.9")),
                ("zhipuai/glm-5.3", "SWE-Marathon", Decimal("42.5")),
                ("zhipuai/glm-5.3-flash", "DeepSWE", Decimal("63.4")),
            },
        )
        glm = next(
            claim
            for claim in records
            if claim.subject.model_id == "zhipuai/glm-5.3" and benchmark(claim).name == "DeepSWE"
        )
        glm_benchmark = benchmark(glm)
        self.assertEqual(glm_benchmark.methodology, "resolved")
        self.assertEqual(glm_benchmark.unit, "UNKNOWN")
        self.assertEqual(dict(glm.subject.configuration or ()), {"reasoning_effort": "max"})
        context = json.loads(glm_benchmark.configuration)
        self.assertEqual(context["harness"], "mini-swe-agent")
        self.assertEqual(context["variant"], "max effort; 6h timeout; 400K context")
        self.assertEqual(context["evaluator"], "Z.ai (provider-run)")
        self.assertEqual(
            (context["temperature"], context["top_p"], context["timeout"], context["context_tokens"]),
            ("0.95", "1.0", "6h", 400_000),
        )
        self.assertEqual(context["provider_configuration_revision"], "ba32f8c19c8738e2c57c71798c601d477a7bf844")
        flash = next(claim for claim in records if claim.subject.model_id == "zhipuai/glm-5.3-flash")
        flash_context = json.loads(benchmark(flash).configuration)
        self.assertEqual(flash_context["provider_configuration_revision"], "46a050bec13002ad29ee795c16e61cf4fa3c4a9c")
        marathon = next(
            claim
            for claim in records
            if claim.subject.model_id == "zhipuai/glm-5.3" and benchmark(claim).name == "SWE-Marathon"
        )
        marathon_context = json.loads(benchmark(marathon).configuration)
        self.assertEqual(marathon_context["harness"], "Claude Code 2.1.207")
        self.assertEqual(
            (
                marathon_context["temperature"],
                marathon_context["top_p"],
                marathon_context["max_new_tokens"],
                marathon_context["context_tokens"],
            ),
            ("1.0", "0.95", 128_000, 1_000_000),
        )

    def test_comparison_keeps_missing_candidate_and_units_unknown_without_ranking(self) -> None:
        result = compare(normalize(captures(), at=T))
        rows = cast(list[dict[str, object]], result["candidates"])
        candidates = {cast(str, row["model_id"]): row for row in rows}
        self.assertIn("UNKNOWN", cast(str, candidates["openai/gpt-6.1-sol"]["evidence_state"]))
        luna_records = cast(list[dict[str, object]], candidates["openai/gpt-6-luna"]["benchmarks"])
        luna = luna_records[0]
        luna_config = cast(dict[str, object], luna["configuration"])
        self.assertEqual((luna["value"], luna["unit"], luna_config["harness"]), ("66.6", "UNKNOWN", None))
        self.assertEqual(luna_config["evaluator"], "UNKNOWN")
        self.assertIn("metric labels differ", cast(str, luna["comparability"]))
        glm_records = cast(list[dict[str, object]], candidates["zhipuai/glm-5.3"]["benchmarks"])
        flash_records = cast(list[dict[str, object]], candidates["zhipuai/glm-5.3-flash"]["benchmarks"])
        glm_deepswe = next(record for record in glm_records if record["benchmark"] == "DeepSWE")
        flash_deepswe = flash_records[0]
        self.assertEqual(glm_deepswe["same_reported_configuration_peers"], ["GLM-5.3-Flash"])
        self.assertIn("native unit", cast(str, glm_deepswe["comparability"]))
        self.assertEqual(flash_deepswe["same_reported_configuration_peers"], ["GLM-5.3"])
        self.assertIn("No winner", cast(str, result["conclusion"]))
        self.assertNotIn("ranking", result)
        self.assertNotIn("recommendation", result)

    def test_zero_is_a_score_but_null_or_missing_score_is_rejected(self) -> None:
        changed = dict(TEXT)
        changed["models-dev:flash"] = changed["models-dev:flash"].replace("score = 63.4", "score = 0")
        zero = normalize(captures(texts=changed), at=T)
        flash = next(
            claim
            for claim in zero.evidence.claims
            if isinstance(claim, ModelClaim) and claim.subject.model_id.endswith("flash")
        )
        self.assertEqual(benchmark(flash).value, Decimal(0))
        for malformed in ("score = null", "", 'score = "63.4"'):
            invalid = dict(TEXT)
            invalid["models-dev:flash"] = invalid["models-dev:flash"].replace("score = 63.4", malformed)
            with self.subTest(score=malformed), self.assertRaises(ValueError):
                normalize(captures(texts=invalid), at=T)

    def test_wrong_model_citation_license_and_partial_generation_are_refused(self) -> None:
        wrong_identity = dict(TEXT)
        wrong_identity["models-dev:flash"] = wrong_identity["models-dev:flash"].replace("GLM-5.3-Flash", "GLM-5.3")
        with self.assertRaisesRegex(ValueError, "source-model-identity"):
            normalize(captures(texts=wrong_identity), at=T)
        wrong_citation = dict(TEXT)
        wrong_citation["models-dev:flash"] = wrong_citation["models-dev:flash"].replace(
            "https://huggingface.co/zai-org/GLM-5.3-Flash", "https://example.invalid/data"
        )
        with self.assertRaisesRegex(ValueError, "source-rights-or-provenance"):
            normalize(captures(texts=wrong_citation), at=T)
        unlicensed = list(captures())
        unlicensed[0] = replace(unlicensed[0], source=replace(unlicensed[0].source, license="UNKNOWN"))
        with self.assertRaisesRegex(ValueError, "incomplete-or-unexpected-source-generation"):
            normalize(tuple(unlicensed), at=T)
        with self.assertRaisesRegex(ValueError, "incomplete-or-unexpected-source-generation"):
            normalize(captures()[:-1], at=T)

    def test_unknown_effort_harness_and_source_retraction_are_not_invented(self) -> None:
        unknown_effort = dict(TEXT)
        unknown_effort["models-dev:flash"] = unknown_effort["models-dev:flash"].replace(
            'variant = "max effort"', 'variant = "extended private reasoning"'
        )
        public = normalize(captures(texts=unknown_effort), at=T)
        flash = next(
            claim
            for claim in public.evidence.claims
            if isinstance(claim, ModelClaim) and claim.subject.model_id.endswith("flash")
        )
        self.assertIsNone(flash.subject.configuration)
        flash_benchmark = benchmark(flash)
        config = json.loads(flash_benchmark.configuration)
        self.assertEqual(config["evaluator"], "Z.ai (provider-run)")
        self.assertEqual(
            (config["temperature"], config["top_p"], config["timeout"], config["context_tokens"]),
            ("0.95", "1.0", "6h", 400_000),
        )
        self.assertEqual(config["harness"], "mini-swe-agent")
        self.assertEqual(flash_benchmark.unit, "UNKNOWN")
        self.assertEqual(flash_benchmark.methodology, "resolved")

        source_retraction = dict(TEXT)
        source_retraction["models-dev:flash"] += "retracted = true\n"
        with self.assertRaisesRegex(ValueError, "source-benchmark-schema"):
            normalize(captures(texts=source_retraction), at=T)

    def test_changed_benchmark_version_is_retained_as_an_attributed_fact(self) -> None:
        original = normalize(captures(), at=T)
        revised = dict(TEXT)
        revised["models-dev:flash"] = revised["models-dev:flash"].replace('version = "1.1"', 'version = "2.0"')
        updated = normalize(captures(texts=revised, at=T + DAY), at=T + DAY, previous=original)
        flash_versions: set[str] = {
            benchmark(claim).version
            for claim in updated.evidence.claims
            if isinstance(claim, ModelClaim) and claim.subject.model_id.endswith("flash")
        }
        self.assertEqual(flash_versions, {"1.1", "2.0"})

    def test_invalid_or_oversized_source_bytes_fail_closed(self) -> None:
        for data in (b"schema = [", b'schema = 2\nname = "wrong"\n'):
            changed = list(captures())
            changed[0] = replace(changed[0], data=data)
            with self.subTest(data=data[:20]), self.assertRaises(ValueError):
                normalize(tuple(changed), at=T)
        with self.assertRaisesRegex(ValueError, "source-encoding"):
            Capture(SOURCES[0], b"\xff", T)
        with self.assertRaisesRegex(ValueError, "source-size-policy"):
            Capture(SOURCES[0], b"x" * (SOURCES[0].max_bytes + 1), T)

    def test_source_disappearance_does_not_forge_retraction_and_changes_append_history(self) -> None:
        original = normalize(captures(), at=T)
        without_flash_benchmark = dict(TEXT)
        without_flash_benchmark["models-dev:flash"] = 'schema = 2\nname = "GLM-5.3-Flash"\n'
        disappeared = normalize(captures(texts=without_flash_benchmark, at=T + DAY), at=T + DAY, previous=original)
        self.assertEqual(len(disappeared.evidence.claims), len(original.evidence.claims))
        self.assertEqual(len(disappeared.evidence.observations), 5)
        changed_score = dict(TEXT)
        changed_score["models-dev:flash"] = changed_score["models-dev:flash"].replace("score = 63.4", "score = 64")
        updated = normalize(captures(texts=changed_score, at=T + DAY), at=T + DAY, previous=original)
        scores: set[Decimal] = {
            benchmark(claim).value
            for claim in updated.evidence.claims
            if isinstance(claim, ModelClaim) and claim.subject.model_id == "zhipuai/glm-5.3-flash"
        }
        self.assertEqual(scores, {Decimal("63.4"), Decimal("64")})

    def test_native_encode_retention_and_operator_inspection_round_trip(self) -> None:
        public = normalize(captures(), at=T)
        data, reference = encode_public_evidence(public, produced_at=T, payload_schema=NATIVE_PAYLOAD_SCHEMA)
        self.assertEqual(decode_public_evidence(data, reference, max_bytes=65536), public)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _ = publish(root, public, expected=SCOPE, produced_at=T, max_bytes=65536)
            retained_result = retained(root, max_bytes=65536)
            assert retained_result is not None
            self.assertEqual(retained_result[2], public)
            view = snapshot(root, instance="coding-benchmark-test", at=T, max_bytes=65536)
            publication = cast(dict[str, object], view["publication"])
            health = cast(dict[str, object], view["health"])
            self.assertEqual(publication["state"], "available")
            self.assertEqual(health["state"], "missing")

    def test_refresh_fetches_complete_source_set_and_preserves_existing_zai_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch("model_intelligence.benchmarks.fetch", side_effect=captures()):
                reference, report = refresh(Path(directory), at=T, max_artifact_bytes=65536, timeout=1)
            self.assertIsNotNone(reference)
            self.assertTrue(report.succeeded)
            actual = retained(Path(directory), max_bytes=65536)
            assert actual is not None
            self.assertEqual(actual[2].applicability, SCOPE)
            self.assertEqual(set(actual[2].applicability.source_ids), {source.source_id for source in SOURCES})
            view = snapshot(Path(directory), instance="coding-benchmark-refresh", at=T, max_bytes=65536)
            publication = cast(dict[str, object], view["publication"])
            health = cast(dict[str, object], view["health"])
            self.assertEqual(publication["state"], "available")
            self.assertEqual(health["state"], "valid")
            self.assertEqual(health["correlation"], "matched")


if __name__ == "__main__":
    unittest.main()
