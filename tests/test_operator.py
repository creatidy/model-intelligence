import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_native_evidence import claim, cut
from test_router_conformance import DAY, T

from model_intelligence.cli import main
from model_intelligence.operator import canonical, snapshot
from model_intelligence.producer import publish, record_refresh_status


def health(publication: str, scope: str, source_ids: frozenset[str]) -> bytes:
    return canonical(
        {
            "schema": "mi.source-refresh-working/1",
            "adapter": scope,
            "attempted_at": T.isoformat(),
            "succeeded": False,
            "diagnostic": "source-generation-or-config-rejected",
            "phase": "normalization",
            "active": publication,
            "last_successful_publication_at": T.isoformat(),
            "freshness_policy": "consumer-owned",
            "remediation": "Inspect named source schema",
            "sources": [
                {
                    "source_id": name,
                    "reference": "https://example.invalid/source",
                    "retrieved": True,
                    "revision": "owned",
                    "bytes_received": 20,
                    "diagnostic": "source-object",
                    "remediation": "Inspect source schema",
                }
                for name in sorted(source_ids)
            ],
        }
    )


class OperatorTests(unittest.TestCase):
    def test_snapshot_cli_export_same_facts_and_no_writes_or_retrieval(self) -> None:
        public = cut(claim())
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            reference = publish(root, public, expected=public.applicability, produced_at=T, max_bytes=65536)
            record_refresh_status(
                root, health(reference.sha256, public.applicability.scope_id, public.applicability.source_ids)
            )
            original = {path.name: path.read_bytes() for path in root.iterdir()}
            outputs: list[str] = []
            for operation in ("status", "inspect", "export"):
                stream = io.StringIO()
                with (
                    patch("model_intelligence.zai.fetch", side_effect=AssertionError("no source read")),
                    contextlib.redirect_stdout(stream),
                ):
                    self.assertEqual(
                        main(
                            [
                                operation,
                                str(root),
                                "--instance",
                                "owned",
                                "--at",
                                T.isoformat(),
                                "--max-bytes",
                                "65536",
                                "--json",
                            ]
                        ),
                        0,
                    )
                outputs.append(stream.getvalue())
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual(outputs[1], outputs[2])
            self.assertEqual(json.loads(outputs[0])["health"]["correlation"], "matched")
            self.assertEqual({path.name: path.read_bytes() for path in root.iterdir()}, original)

    def test_health_mismatch_unknown_freshness_and_missing_checkpoint_are_not_current_timeline(self) -> None:
        public = cut(claim())
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            _ = publish(root, public, expected=public.applicability, produced_at=T, max_bytes=65536)
            record_refresh_status(root, health("0" * 64, "other-scope", public.applicability.source_ids))
            view = snapshot(root, instance="owned", at=T, max_bytes=65536, checkpoint="1" * 64)
            self.assertEqual(json.loads(canonical(view))["health"]["correlation"], "mismatch")
            self.assertEqual(json.loads(canonical(view))["history"]["relation"], "gap")
            self.assertFalse(json.loads(canonical(view))["capabilities"]["replay"])
            self.assertEqual(json.loads(canonical(view))["capabilities"]["commands"], [])

    def test_retained_extension_future_and_stale_diagnostics(self) -> None:
        original = cut(claim())
        updated = cut(claim(), claim("future", effective=T + DAY, revises="native"))
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            previous = publish(root, original, expected=original.applicability, produced_at=T, max_bytes=65536)
            _ = publish(root, updated, expected=updated.applicability, produced_at=T, max_bytes=65536)
            view = json.loads(
                canonical(snapshot(root, instance="owned", at=T, max_bytes=65536, checkpoint=previous.sha256))
            )
            self.assertEqual(view["history"]["relation"], "extension")
            self.assertIn("statement:future", view["facts"]["future"])
            later = json.loads(canonical(snapshot(root, instance="owned", at=T + 2 * DAY, max_bytes=65536)))
            self.assertTrue(later["facts"]["stale"])
            self.assertNotIn("statement:future", later["facts"]["future"])

    def test_empty_corrupt_health_and_invalid_retained_cut_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            view = json.loads(canonical(snapshot(root, instance="owned", at=T, max_bytes=65536)))
            self.assertEqual(view["publication"]["state"], "empty")
            self.assertEqual(view["health"]["state"], "missing")
            record_refresh_status(root, canonical({"schema": "future/99"}))
            view = json.loads(canonical(snapshot(root, instance="owned", at=T, max_bytes=65536)))
            self.assertEqual(view["health"]["state"], "unsupported")
            with patch("model_intelligence.operator.retained", side_effect=ValueError("OWNED-SECRET-PRIVATE-PATH")):
                value = canonical(snapshot(root, instance="owned", at=T, max_bytes=65536))
            self.assertNotIn(b"OWNED-SECRET", value)
            self.assertEqual(json.loads(value)["publication"]["state"], "invalid")


if __name__ == "__main__":
    unittest.main()
