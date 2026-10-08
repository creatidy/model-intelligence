"""Original tiny source-shaped fixtures, not copied provider documents/data tables."""

import json
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from test_router_conformance import DAY, T

from model_intelligence.acquisition import Capture
from model_intelligence.contract import NATIVE_PAYLOAD_SCHEMA, decode_public_evidence, encode_public_evidence
from model_intelligence.evidence import ModelClaim, Money, NativeLimit
from model_intelligence.producer import retained
from model_intelligence.zai import SOURCES, normalize, refresh

CATALOG = """name = "GLM-5.3-Flash"
[limit]
context = 4096
output = 1024
[[benchmarks]]
name = "Terminal-Bench"
version = "2.1"
metric = "pass@1"
harness = "owned harness"
variant = "owned variant"
source = "https://example.invalid/owned"
score = 37.125
[[benchmarks]]
name = "DeepSWE"
version = "1.1"
metric = "resolved"
harness = "owned harness"
variant = "owned variant"
source = "https://example.invalid/owned"
score = 42.0625
"""
OFFER = """base_model = "zhipuai/glm-5.3-flash"
reasoning_options = [{type = "effort", values = ["low", "high", "max"]}]
[cost]
input = 0.15
output = 0.50
cache_read = 0.03
cache_write = 0
"""
TEXT = {
    "catalog": CATALOG,
    "api": OFFER,
    "coding": OFFER.replace("0.15", "0").replace("0.50", "0").replace("0.03", "0"),
    "prices": (
        "All prices are in USD.\nPrices per 1M tokens.\n"
        "| GLM-5.3-Flash | \\$0.15 | \\$0.03 | Limited-time Free | \\$0.50 |\n"
    ),
    "plans": (
        "Starting at just 18 USD per month\n| Lite | 2,000 | 10,000 |\n"
        "requests for GLM-4.7 will automatically be routed to GLM-5.3-Flash\n"
    ),
    "campaign": (
        "Campaign period: September 3, 2026 to October 7, 2026\n"
        "23:00 to 09:00 UTC+8 paid plan users Zero quota consumption doubled 3.10\n"
    ),
    "cohort": "Publication date: July 30, 2026\nUTC+8 Plans are not switched automatically\n",
    "interface": (
        "  version: 1.0.0\n    ChatCompletionVisionRequest:\n      enum:\n        - glm-5.3-flash\n"
        "        max_tokens:\n          type: integer\n          minimum: 1\n"
        "          maximum: 131072\n    NextSchema:\n"
    ),
}


def captures(*, texts: dict[str, str] | None = None, at: datetime = T) -> tuple[Capture, ...]:
    data = TEXT if texts is None else texts
    return tuple(Capture(source, data[source.source_id].encode(), at) for source in SOURCES)


class ZaiSourceTests(unittest.TestCase):
    def test_complete_scope_roundtrip_native_distinctions_and_unknowns(self) -> None:
        public = normalize(captures())
        data, reference = encode_public_evidence(public, produced_at=T, payload_schema=NATIVE_PAYLOAD_SCHEMA)
        self.assertEqual(decode_public_evidence(data, reference, max_bytes=65536), public)
        limits = tuple(
            (row.subject, row.payload)
            for row in public.evidence.claims
            if isinstance(row, ModelClaim) and isinstance(row.payload, NativeLimit)
        )
        self.assertEqual(len(limits), 4)
        self.assertEqual(
            {value.meaning for _, value in limits},
            {"total-context-window", "input-allowance", "output-allowance", "request-parameter-maximum"},
        )
        self.assertTrue(any(value.amount is None for _, value in limits))
        self.assertTrue(
            all(subject.physical_model_id is None and subject.configuration is None for subject, _ in limits)
        )
        self.assertTrue(all(row.start is None and row.end is None for row in public.uncertain_campaigns))
        self.assertTrue(
            all(row.fresh_until is None and row.published_at is None for row in public.evidence.observations)
        )

    def test_price_zero_plan_basis_and_same_fact_reread_are_not_free_or_fresh(self) -> None:
        original = normalize(captures())
        updated = normalize(captures(at=T + DAY), previous=original)
        self.assertEqual(updated, original)
        zero = tuple(
            row.payload
            for row in updated.evidence.claims
            if isinstance(row, ModelClaim) and isinstance(row.payload, Money) and row.payload.amount == Decimal(0)
        )
        self.assertTrue(any("included-plan-credits" in value.unit for value in zero))
        self.assertTrue(all(row.fresh_until is None for row in updated.evidence.observations))
        formatted = dict(TEXT)
        formatted["catalog"] = "# owned formatting only\n" + formatted["catalog"]
        self.assertEqual(normalize(captures(texts=formatted, at=T + DAY), previous=original), original)

    def test_missing_duplicate_base_model_and_ambiguous_sections_refuse(self) -> None:
        inputs = captures()
        with self.assertRaisesRegex(ValueError, "generation"):
            normalize(inputs[:-1])
        with self.assertRaisesRegex(ValueError, "generation"):
            normalize((*inputs[:-1], inputs[0]))
        for source, text in (
            ("api", OFFER.replace("zhipuai/glm-5.3-flash", "other/model")),
            ("prices", TEXT["prices"] * 2),
            ("interface", TEXT["interface"].replace("maximum: 131072", "maximum: unknown")),
            ("catalog", CATALOG.replace('name = "DeepSWE"', 'name = "Terminal-Bench"')),
        ):
            modified = dict(TEXT)
            modified[source] = text
            with self.subTest(source=source), self.assertRaises(ValueError):
                normalize(captures(texts=modified))

    def test_source_disagreement_is_retained_without_implicit_correction(self) -> None:
        original = normalize(captures())
        modified = dict(TEXT)
        modified["api"] = OFFER.replace("0.15", "0.16")
        updated = normalize(captures(texts=modified, at=T + DAY), previous=original)
        original.check_update(updated)
        self.assertGreater(len(updated.evidence.claims), len(original.evidence.claims))
        self.assertTrue(all(row.revises is None for row in updated.evidence.claims))

    def test_config_migration_alias_drift_and_missing_price_fail_without_replacing_history(self) -> None:
        original = normalize(captures())
        wrong = replace(
            original, applicability=replace(original.applicability, configuration=(("adapter", "unknown/3"),))
        )
        with self.assertRaisesRegex(ValueError, "migration"):
            normalize(captures(), previous=wrong)
        for key, replacement in (
            ("prices", TEXT["prices"].replace("GLM-5.3-Flash |", "other-model |")),
            ("plans", TEXT["plans"].replace("GLM-4.7", "ambiguous-alias")),
            ("prices", TEXT["prices"].replace("USD", "EUR")),
        ):
            modified = dict(TEXT)
            modified[key] = replacement
            with self.subTest(key=key), self.assertRaises(ValueError):
                normalize(captures(texts=modified), previous=original)
        self.assertEqual(normalize(captures(at=T + DAY), previous=original), original)

    def test_failed_partial_and_malformed_refresh_keep_last_valid_bytes_and_health(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            with patch("model_intelligence.zai.fetch", side_effect=captures()):
                result = refresh(root, at=T, max_artifact_bytes=65536, timeout=1)
            self.assertTrue(result.succeeded)
            original = retained(root, max_bytes=65536)
            with patch("model_intelligence.zai.fetch", side_effect=ValueError("owned failure")):
                result = refresh(root, at=T + DAY, max_artifact_bytes=65536, timeout=1)
            self.assertFalse(result.succeeded)
            self.assertEqual(retained(root, max_bytes=65536), original)
            status = json.loads((root / "source-status.json").read_text())
            self.assertFalse(status["succeeded"])
            self.assertEqual(len(status["sources"]), len(SOURCES))
            self.assertTrue(all(not item.retrieved for item in result.sources))
            self.assertNotIn("owned failure", (root / "source-status.json").read_text())


if __name__ == "__main__":
    unittest.main()
