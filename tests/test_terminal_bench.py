import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import cast
from unittest.mock import patch
from uuid import NAMESPACE_URL, uuid5

from test_benchmarks_source import captures as coding_captures
from test_router_conformance import DAY, T

from model_intelligence.acquisition import Capture, Source
from model_intelligence.benchmarks import SCOPE as CODING_SCOPE
from model_intelligence.benchmarks import normalize as normalize_coding
from model_intelligence.contract import (
    NATIVE_PAYLOAD_SCHEMA,
    PublicEvidence,
    decode_public_evidence,
    encode_public_evidence,
)
from model_intelligence.evidence import Benchmark, ModelClaim
from model_intelligence.operator import snapshot
from model_intelligence.producer import publish, retained
from model_intelligence.terminal_bench import (
    SCOPE,
    SOURCES,
    TERMINAL_BENCH_CANDIDATES,
    TERMINAL_BENCH_DATASET_REF,
    TERMINAL_BENCH_REPOSITORY_PIN,
    TERMINAL_BENCH_TRIAL_COUNT,
    CandidateSpec,
    compare,
    normalize,
    normalize_with_receipt,
    refresh,
)
from model_intelligence.zai import SCOPE as ZAI_SCOPE

_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _submission(candidate: CandidateSpec, *, successes: int = 165, accuracy: float = 50.0, ci: float = 2.0) -> bytes:
    candidate_id = candidate.candidate_id
    effort = candidate.effort
    source_filter_effort = candidate.source_filter_effort
    release_date = candidate.release_date
    year, month, day = (int(part) for part in release_date.split("-"))
    date_display = f"{_MONTHS[month - 1]} {day}, {year}"
    trial_count = TERMINAL_BENCH_TRIAL_COUNT
    trial_ids = [str(uuid5(NAMESPACE_URL, f"synthetic-tb4-{candidate_id}-{index}")) for index in range(trial_count)]
    source_job_id = candidate.source_job_id
    source_job: str = source_job_id
    if candidate_id == "glm":
        source_job = f"https://hub.harborframework.com/jobs/{source_job_id}"
    agent_url = candidate.agent_url
    uncached = 1_000
    cached = 200
    output_tokens = 500
    metrics = {
        "accuracy": accuracy,
        "accuracy_ci95_half_width": ci,
        "display_accuracy": f"**{accuracy:.1f}%** ± {ci:.1f}%",
        "n_trials": trial_count,
        "successes": successes,
        "pass_at_2": 0.5,
        "pass_at_3": 0.5,
        "pass_at_4": 0.5,
        "pass_at_5": 0.5,
        "uncached_input_tokens": uncached,
        "cached_input_tokens": cached,
        "output_tokens": output_tokens,
        "total_tokens": uncached + output_tokens,
        "display_total_tokens": "1.5K",
        "total_cost_usd": 4.5,
        "display_cost": "$4.50",
        "display_total_cost_usd": "$4.50",
        "avg_trial_duration_sec": 10.0,
    }
    model_org = candidate.model_org
    model_org_url = candidate.model_org_url
    model_display = candidate.display_name
    model_url = candidate.model_url
    agent_display = candidate.agent_display
    agent_org = candidate.agent_org
    agent_org_url = candidate.agent_org_url
    submission = {
        "source_jobs": [source_job],
        "source_filter": {
            "agent": candidate.agent_id,
            "agent_version": candidate.agent_version,
            "model_name": candidate.source_model_id,
            "reasoning_effort": source_filter_effort,
        },
        "metadata": {
            "agent_display": {"url": agent_url, "label": agent_display},
            "agent_org": {"url": agent_org_url, "label": agent_org},
            "model_display": {"url": model_url, "label": model_display},
            "model_org": {"url": model_org_url, "label": model_org},
            "date": release_date,
            "display_date": date_display,
            "reasoning_effort": effort,
        },
        "metrics": metrics,
        "disqualified_trials": [],
        "trials": trial_ids,
    }
    return json.dumps(submission, separators=(",", ":")).encode()


def captures(
    *,
    contents: dict[str, bytes] | None = None,
    at: datetime = T,
) -> tuple[Capture, ...]:
    by_id = {} if contents is None else contents
    return tuple(
        Capture(source, by_id.get(source.source_id, _submission(candidate)), at)
        for candidate, source in zip(TERMINAL_BENCH_CANDIDATES, SOURCES, strict=True)
    )


def _metric_claims(public: PublicEvidence) -> list[ModelClaim]:
    return [
        claim
        for claim in public.evidence.claims
        if isinstance(claim, ModelClaim) and isinstance(claim.payload, Benchmark)
    ]


def _benchmark(claim: ModelClaim) -> Benchmark:
    if not isinstance(claim.payload, Benchmark):
        raise AssertionError("expected Terminal-Bench benchmark claim")
    return claim.payload


class TerminalBenchTests(unittest.TestCase):
    def test_source_scope_is_separate_from_m1_01_and_pinned_to_official_release(self) -> None:
        self.assertNotEqual(SCOPE, CODING_SCOPE)
        self.assertNotEqual(SCOPE, ZAI_SCOPE)
        self.assertEqual(TERMINAL_BENCH_REPOSITORY_PIN, "6964e9252c90227fc1cfa26cbc59aee4134792e4")
        self.assertEqual(
            TERMINAL_BENCH_DATASET_REF, "sha256:39d9f44b40420cde8fdcc087579c0d72a7e14fa3656d603c3f0d22fb35e27732"
        )
        self.assertEqual(len(SOURCES), 4)
        self.assertTrue(
            all(
                source.reference.startswith(
                    "https://raw.githubusercontent.com/harbor-framework/terminal-bench/6964e9252c90227fc1cfa26cbc59aee4134792e4/leaderboard/submissions/"
                )
                for source in SOURCES
            )
        )
        self.assertTrue(all("Apache-2.0" in source.license for source in SOURCES))

    def test_real_schema_claims_preserve_model_route_harness_effort_and_native_ci(self) -> None:
        public, facts = normalize_with_receipt(captures(), at=T)
        self.assertEqual(len(facts), 4)
        claims = _metric_claims(public)
        self.assertEqual(len(claims), 4)
        by_candidate = {fact.candidate_id: fact for fact in facts}
        self.assertEqual(by_candidate["sol"].accuracy, Decimal("50.0"))
        self.assertEqual(by_candidate["sol"].effort, "max")
        self.assertEqual(by_candidate["sol"].agent_version, "0.159.0")
        self.assertEqual(by_candidate["flash"].effort, "none")
        glm = by_candidate["glm"]
        self.assertEqual(glm.reported_model_id, "anthropic/glm-5.3")
        self.assertEqual(glm.model_id, "zhipuai/glm-5.3")
        self.assertEqual(glm.model_org, "Z.ai")
        claim = next(item for item in claims if item.subject.model_id == glm.model_id)
        assert isinstance(claim.payload, Benchmark)
        self.assertEqual((claim.payload.version, claim.payload.unit), ("4.0.0", "percent"))
        self.assertIn("95% CI half-width", claim.payload.methodology)
        self.assertIn("evaluation_date=UNKNOWN", claim.payload.configuration)
        self.assertIn("reported_model_id=anthropic/glm-5.3", claim.payload.configuration)

    def test_accuracy_metric_matches_selected_trials_and_zero_is_not_unknown(self) -> None:
        source = SOURCES[0]
        sol = TERMINAL_BENCH_CANDIDATES[0]
        zero = _submission(sol, successes=0, accuracy=0, ci=1.1)
        public = normalize((Capture(source, zero, T), *captures()[1:]), at=T)
        sol_claim = next(claim for claim in _metric_claims(public) if claim.subject.model_id == "openai/gpt-6.1-sol")
        assert isinstance(sol_claim.payload, Benchmark)
        self.assertEqual(sol_claim.payload.value, Decimal("0.0"))
        self.assertEqual(sol_claim.payload.unit, "percent")
        invalid = _submission(sol, successes=2, accuracy=0, ci=1.1)
        with self.assertRaisesRegex(ValueError, "accuracy-mismatch"):
            normalize((Capture(source, invalid, T), *captures()[1:]), at=T)

    def test_wrong_identity_effort_display_or_model_org_is_rejected(self) -> None:
        source = SOURCES[0]
        sol = TERMINAL_BENCH_CANDIDATES[0]
        data = json.loads(_submission(sol))
        data["source_filter"]["model_name"] = "openai/gpt-6-sol"
        with self.assertRaisesRegex(ValueError, "submission-filter-identity"):
            normalize((Capture(source, json.dumps(data).encode(), T), *captures()[1:]), at=T)
        data = json.loads(_submission(sol))
        data["metadata"]["reasoning_effort"] = "high"
        with self.assertRaisesRegex(ValueError, "submission-display-identity"):
            normalize((Capture(source, json.dumps(data).encode(), T), *captures()[1:]), at=T)
        data = json.loads(_submission(sol))
        data["metadata"]["model_org"]["label"] = "Unknown vendor"
        with self.assertRaisesRegex(ValueError, "submission-display-identity"):
            normalize((Capture(source, json.dumps(data).encode(), T), *captures()[1:]), at=T)

    def test_release_date_and_official_display_date_must_agree(self) -> None:
        source = SOURCES[0]
        sol = TERMINAL_BENCH_CANDIDATES[0]
        for release_date, display_date in (
            ("not-a-date", "Sep 29, 2026"),
            ("2026-09-28", "Sep 29, 2026"),
            ("2026-09-29", "2036-09-29"),
        ):
            data = json.loads(_submission(sol))
            data["metadata"]["date"] = release_date
            data["metadata"]["display_date"] = display_date
            with self.subTest(release_date=release_date), self.assertRaises(ValueError):
                normalize((Capture(source, json.dumps(data).encode(), T), *captures()[1:]), at=T)

    def test_missing_null_out_of_range_or_inconsistent_confidence_fails_closed(self) -> None:
        source = SOURCES[0]
        sol = TERMINAL_BENCH_CANDIDATES[0]
        cases = (
            {"accuracy_ci95_half_width": None},
            {"accuracy_ci95_half_width": -1.0},
            {"accuracy_ci95_half_width": 101.0},
            {"accuracy": None},
            {"n_trials": 329},
            {"successes": 331},
        )
        for changes in cases:
            data = json.loads(_submission(sol))
            data["metrics"].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                normalize((Capture(source, json.dumps(data).encode(), T), *captures()[1:]), at=T)

    def test_exact_selected_trial_ids_are_validated_but_never_published(self) -> None:
        raw = list(captures())
        sol_data = json.loads(raw[0].data)
        sol_data["trials"] = sol_data["trials"][:-1]
        with self.assertRaisesRegex(ValueError, "trial-coverage"):
            normalize((Capture(raw[0].source, json.dumps(sol_data).encode(), T), *raw[1:]), at=T)
        sol_data = json.loads(raw[0].data)
        sol_data["trials"][1] = sol_data["trials"][0]
        with self.assertRaisesRegex(ValueError, "trial-identity"):
            normalize((Capture(raw[0].source, json.dumps(sol_data).encode(), T), *raw[1:]), at=T)
        public, _ = normalize_with_receipt(tuple(raw), at=T)
        self.assertNotIn(sol_data["trials"][0], repr(public))

    def test_source_license_pin_completeness_and_closed_schema_are_mandatory(self) -> None:
        unlicensed = list(captures())
        unlicensed[0] = replace(unlicensed[0], source=replace(unlicensed[0].source, license="UNVERIFIED"))
        with self.assertRaisesRegex(ValueError, "incomplete-or-unexpected-terminal-bench-generation"):
            normalize(tuple(unlicensed), at=T)
        with self.assertRaisesRegex(ValueError, "incomplete-or-unexpected-terminal-bench-generation"):
            normalize(captures()[:-1], at=T)
        data = json.loads(captures()[0].data)
        data["source_license"] = "Apache-2.0"
        with self.assertRaisesRegex(ValueError, "submission-schema"):
            normalize((Capture(SOURCES[0], json.dumps(data).encode(), T), *captures()[1:]), at=T)
        data = json.loads(captures()[0].data)
        data["retracted"] = True
        with self.assertRaisesRegex(ValueError, "submission-schema"):
            normalize((Capture(SOURCES[0], json.dumps(data).encode(), T), *captures()[1:]), at=T)
        data = json.loads(captures()[0].data)
        data["metrics"]["unit"] = "source-native-score"
        with self.assertRaisesRegex(ValueError, "submission-metric-schema"):
            normalize((Capture(SOURCES[0], json.dumps(data).encode(), T), *captures()[1:]), at=T)
        with self.assertRaises(ValueError):
            Source(
                "wrong-pin",
                "https://raw.githubusercontent.com/harbor-framework/terminal-bench/main/leaderboard/submissions/file.json",
                65536,
                "Apache-2.0",
            )

    def test_malformed_truncated_oversized_and_disqualified_sources_are_rejected(self) -> None:
        source = SOURCES[0]
        for payload in (b"{", b"\xff", b"NaN", b'{"metadata":{},"metadata":{}}'):
            rows = list(captures())
            with self.subTest(payload=payload[:32]), self.assertRaises(ValueError):
                Capture(source, payload, T)
                rows[0] = Capture(source, payload, T)
                normalize(tuple(rows), at=T)
        with self.assertRaisesRegex(ValueError, "source-size-policy"):
            Capture(source, b"x" * (source.max_bytes + 1), T)
        rows = list(captures())
        data = json.loads(rows[0].data)
        data["disqualified_trials"] = ["synthetic-trial"]
        with self.assertRaisesRegex(ValueError, "unsupported-disqualified-trials"):
            normalize((Capture(source, json.dumps(data).encode(), T), *rows[1:]), at=T)

    def test_history_repeated_observation_change_and_disappearance_are_safe(self) -> None:
        original, _ = normalize_with_receipt(captures(), at=T)
        repeated = normalize(captures(at=T + DAY), at=T + DAY, previous=original)
        self.assertEqual(repeated, original)
        modified = json.loads(captures()[0].data)
        modified["metrics"]["successes"] = 198
        modified["metrics"]["accuracy"] = 60.0
        modified["metrics"]["display_accuracy"] = "**60.0%** ± 2.0%"
        content = {source.source_id: capture.data for source, capture in zip(SOURCES, captures(), strict=True)}
        content[SOURCES[0].source_id] = json.dumps(modified).encode()
        updated = normalize(captures(contents=content, at=T + DAY), at=T + DAY, previous=original)
        values: set[Decimal] = set()
        for claim in _metric_claims(updated):
            if claim.subject.model_id == "openai/gpt-6.1-sol":
                values.add(_benchmark(claim).value)
        self.assertEqual(values, {Decimal("50.0"), Decimal("60.0")})
        with self.assertRaisesRegex(ValueError, "incomplete-or-unexpected-terminal-bench-generation"):
            normalize(captures()[:-1], at=T + DAY, previous=original)

    def test_failed_source_refresh_retains_the_last_known_immutable_cut(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("model_intelligence.terminal_bench.fetch", side_effect=captures()):
                first_reference, first_report = refresh(root, at=T, max_artifact_bytes=65_536, timeout=1)
            self.assertTrue(first_report.succeeded)
            first = retained(root, max_bytes=65_536)
            assert first is not None
            failed_fetches = [*captures()[:-1], OSError("source-incomplete-response")]
            with patch("model_intelligence.terminal_bench.fetch", side_effect=failed_fetches):
                current_reference, report = refresh(root, at=T + DAY, max_artifact_bytes=65_536, timeout=1)
            self.assertFalse(report.succeeded)
            self.assertEqual(current_reference, first_reference)
            current = retained(root, max_bytes=65_536)
            assert current is not None
            self.assertEqual(current[1], first[1])
            self.assertEqual(current[2], first[2])

    def test_comparison_keeps_m1_01_context_and_does_not_rank_or_convert(self) -> None:
        terminal_public, facts = normalize_with_receipt(captures(), at=T)
        coding_public = normalize_coding(coding_captures(), at=T)
        comparison = compare(coding_public, terminal_public, facts)
        observations = cast(list[dict[str, object]], comparison["terminal_bench_observations"])
        candidates: dict[str, dict[str, object]] = {cast(str, entry["candidate_id"]): entry for entry in observations}
        self.assertEqual(set(candidates), {"sol", "luna", "glm", "flash"})
        self.assertIn("Codex 0.159.0", cast(str, candidates["sol"]["comparability"]))
        self.assertIn("anthropic/glm-5.3", cast(str, candidates["glm"]["comparability"]))
        self.assertIn("Claude Code version 2.1.285", cast(str, candidates["flash"]["comparability"]))
        self.assertIn("existing_coding_benchmark_evidence", comparison)
        self.assertNotIn("ranking", comparison)
        self.assertNotIn("winner", comparison)
        resources = cast(list[dict[str, object]], comparison["resource_receipt"])
        self.assertIn("source_reported_job_cost_usd", resources[0])
        self.assertIn("not established", cast(str, resources[0]["cost_basis"]))
        changed_scope = replace(
            terminal_public.applicability,
            configuration=tuple(
                (key, "5.0.0" if key == "dataset-version" else value)
                for key, value in terminal_public.applicability.configuration or ()
            ),
        )
        incompatible = replace(terminal_public, applicability=changed_scope)
        with self.assertRaisesRegex(ValueError, "coding-comparison-scope"):
            compare(coding_public, incompatible, facts)

    def test_native_encode_decode_retention_and_operator_health(self) -> None:
        public = normalize(captures(), at=T)
        encoded, reference = encode_public_evidence(public, produced_at=T, payload_schema=NATIVE_PAYLOAD_SCHEMA)
        self.assertEqual(decode_public_evidence(encoded, reference, max_bytes=65_536), public)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _ = publish(root, public, expected=SCOPE, produced_at=T, max_bytes=65_536)
            retained_result = retained(root, max_bytes=65_536)
            assert retained_result is not None
            self.assertEqual(retained_result[2], public)
            view = snapshot(root, instance="terminal-bench-test", at=T, max_bytes=65_536)
            self.assertEqual(cast(dict[str, object], view["publication"])["state"], "available")

    def test_refresh_publishes_complete_real_scope_and_operator_source_health(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch("model_intelligence.terminal_bench.fetch", side_effect=captures()):
                reference, report = refresh(Path(directory), at=T, max_artifact_bytes=65_536, timeout=1)
            self.assertIsNotNone(reference)
            self.assertTrue(report.succeeded)
            self.assertTrue(all(fact.http_status == 200 for fact in report.submissions))
            actual = retained(Path(directory), max_bytes=65_536)
            assert actual is not None
            self.assertEqual(actual[2].applicability, SCOPE)
            self.assertEqual(len(_metric_claims(actual[2])), 4)
            view = snapshot(Path(directory), instance="terminal-bench-refresh-test", at=T, max_bytes=65_536)
            health = cast(dict[str, object], view["health"])
            self.assertEqual(health["state"], "valid")
            self.assertEqual(health["correlation"], "matched")


if __name__ == "__main__":
    unittest.main()
