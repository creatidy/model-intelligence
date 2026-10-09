import ast
import json
import tempfile
import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from portable_operator_consumer import decode, receive
from test_native_evidence import LIMIT, claim, cut
from test_operator import health
from test_router_conformance import DAY, PLAN, T, augment, base, observation

from model_intelligence.evidence import Money, OverrideClaim, Period, Terms
from model_intelligence.operator import canonical, snapshot
from model_intelligence.producer import publish, record_refresh_status


class PortableOperatorTests(unittest.TestCase):
    def test_conflicting_native_assertions_are_present_without_a_consumer_winner(self) -> None:
        public = cut(claim(), claim("disagreement", limit=replace(LIMIT, amount=Decimal("2048"))))
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            _ = publish(root, public, expected=public.applicability, produced_at=T, max_bytes=65536)
            view = snapshot(root, instance="owned", at=T, max_bytes=65536)
            parsed = json.loads(canonical(view))
            self.assertTrue(parsed["facts"]["conflicts"])
            self.assertEqual(receive(None, canonical(view), max_bytes=65536).disposition, "accepted")
            self.assertEqual(parsed["capabilities"]["commands"], [])

    def test_withdrawal_expiry_and_transport_only_republication_are_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            original = base()
            promotion = OverrideClaim(
                PLAN,
                "owned",
                Terms(price=Money(Decimal("5"), "USD", "month")),
                Period(T, T + DAY),
                claim_id="promo",
                observation_id="promo",
                effective_from=T,
            )
            public = augment(original, observed=(observation("promo"),), claims=(promotion,))
            first_ref = publish(root, public, expected=public.applicability, produced_at=T, max_bytes=65536)
            first = receive(None, canonical(snapshot(root, instance="owned", at=T, max_bytes=65536)), max_bytes=65536)
            self.assertEqual(first.disposition, "accepted")
            later = snapshot(root, instance="owned", at=T + DAY, max_bytes=65536, checkpoint=first_ref.sha256)
            self.assertEqual(receive(first.state, canonical(later), max_bytes=65536).disposition, "accepted")
            offers = json.loads(canonical(later))["facts"]["projection"]["offers"]
            self.assertNotEqual(offers[0]["terms"]["price"]["amount"], "5")
            withdrawal = OverrideClaim(
                PLAN,
                "owned",
                None,
                None,
                claim_id="withdrawal",
                observation_id="withdrawal",
                effective_from=T,
                revises="promo",
            )
            corrected = augment(public, observed=(observation("withdrawal"),), claims=(withdrawal,))
            _ = publish(root, corrected, expected=public.applicability, produced_at=T + DAY, max_bytes=65536)
            view = snapshot(root, instance="owned", at=T, max_bytes=65536, checkpoint=first_ref.sha256)
            self.assertIn("statement:withdrawal", json.loads(canonical(view))["facts"]["latest"])
            self.assertEqual(receive(first.state, canonical(view), max_bytes=65536).disposition, "accepted")
            _ = publish(root, corrected, expected=corrected.applicability, produced_at=T + 2 * DAY, max_bytes=65536)
            same = snapshot(root, instance="owned", at=T, max_bytes=65536)
            self.assertEqual(decode(canonical(same), max_bytes=65536)["facts"], view["facts"])

    def test_fact_namespace_and_invalid_health_are_not_coerced(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            public = cut(claim())
            _ = publish(root, public, expected=public.applicability, produced_at=T, max_bytes=65536)
            view = snapshot(root, instance="owned", at=T, max_bytes=65536)
            accepted = receive(None, canonical(view), max_bytes=65536)
            bad = json.loads(canonical(view))
            bad["facts"]["latest"] = ["observation:native"]
            self.assertEqual(receive(accepted.state, canonical(bad), max_bytes=65536).disposition, "rejected")
            raw_health = json.loads(health("0" * 64, "owned", public.applicability.source_ids))
            raw_health["phase"] = []
            record_refresh_status(root, canonical(raw_health))
            invalid = snapshot(root, instance="owned", at=T, max_bytes=65536)
            self.assertEqual(json.loads(canonical(invalid))["health"]["state"], "invalid")
            self.assertEqual(receive(None, canonical(invalid), max_bytes=65536).disposition, "accepted")

    def test_consumer_has_no_producer_imports_or_dynamic_validation_delegation(self) -> None:
        code = (Path(__file__).parent / "portable_operator_consumer.py").read_text()
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertTrue(all(not item.name.startswith("model_intelligence") for item in node.names))
            if isinstance(node, ast.ImportFrom):
                self.assertFalse((node.module or "").startswith("model_intelligence"))
        self.assertNotIn("importlib", code)

    def test_independent_available_empty_health_and_unsupported_consumer(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            empty = canonical(snapshot(root, instance="owned", at=T, max_bytes=65536))
            self.assertEqual(decode(empty, max_bytes=65536)["product"], "model-intelligence")
            public = cut(claim())
            reference = publish(root, public, expected=public.applicability, produced_at=T, max_bytes=65536)
            record_refresh_status(
                root, health(reference.sha256, public.applicability.scope_id, public.applicability.source_ids)
            )
            view = snapshot(root, instance="owned", at=T, max_bytes=65536)
            receipt = receive(None, canonical(view), max_bytes=65536)
            self.assertEqual(receipt.disposition, "accepted")
            self.assertFalse(receipt.replayed)
            bad = dict(view)
            bad["schema"] = "unknown/9"
            rejected = receive(receipt.state, canonical(bad), max_bytes=65536)
            self.assertEqual(rejected.disposition, "rejected")
            self.assertEqual(rejected.state, receipt.state)

    def test_duplicate_reordered_reconnect_and_explicit_gap_resync(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            first = cut(claim())
            old_ref = publish(root, first, expected=first.applicability, produced_at=T, max_bytes=65536)
            old = canonical(snapshot(root, instance="owned", at=T, max_bytes=65536))
            accepted = receive(None, old, max_bytes=65536)
            self.assertEqual(accepted.disposition, "accepted")
            self.assertEqual(receive(accepted.state, old, max_bytes=65536).disposition, "duplicate")
            newer = cut(claim(), claim("future", effective=T + DAY, revises="native"))
            _ = publish(root, newer, expected=newer.applicability, produced_at=T + DAY, max_bytes=65536)
            linked = canonical(snapshot(root, instance="owned", at=T + DAY, max_bytes=65536, checkpoint=old_ref.sha256))
            current = receive(accepted.state, linked, max_bytes=65536)
            self.assertEqual(current.disposition, "accepted")
            self.assertEqual(receive(current.state, old, max_bytes=65536).disposition, "resync-required")
            unknown = canonical(snapshot(root, instance="owned", at=T + 2 * DAY, max_bytes=65536, checkpoint="0" * 64))
            held = receive(current.state, unknown, max_bytes=65536)
            self.assertEqual(held.disposition, "resync-required")
            self.assertEqual(held.state, current.state)
            resynced = receive(current.state, unknown, max_bytes=65536, resync=True)
            self.assertEqual(resynced.disposition, "accepted")
            self.assertEqual(resynced.history, "unavailable")
            assert resynced.state is not None
            self.assertTrue(resynced.state.history_gap)
            self.assertFalse(resynced.replayed)

    def test_whole_envelope_tampering_and_boolean_integer_coercion_reject(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            public = cut(claim())
            _ = publish(root, public, expected=public.applicability, produced_at=T, max_bytes=65536)
            view = snapshot(root, instance="owned", at=T, max_bytes=65536)
            original = canonical(view)
            accepted = receive(None, original, max_bytes=65536)
            for case in ("digest", "commands", "replay", "extra", "reference", "fact"):
                raw = json.loads(original)
                if case == "digest":
                    raw["publication"]["reference"]["sha256"] = "f" * 64
                elif case == "commands":
                    raw["capabilities"]["commands"] = ["refresh"]
                elif case == "replay":
                    raw["capabilities"]["replay"] = 0
                elif case == "extra":
                    raw["unexpected"] = "OWNED-SECRET"
                elif case == "reference":
                    raw["publication"]["reference"]["format_version"] = True
                else:
                    raw["facts"]["latest"] = ["statement:unknown"]
                rejected = receive(accepted.state, canonical(raw), max_bytes=65536)
                with self.subTest(case=case):
                    self.assertEqual(rejected.disposition, "rejected")
                    self.assertEqual(rejected.state, accepted.state)
                    self.assertNotIn("OWNED-SECRET", " ".join(rejected.diagnostics))
            self.assertEqual(receive(accepted.state, original, max_bytes=1).disposition, "rejected")
            duplicate_key = b'{"schema":"mi.operator-working/1","schema":"mi.operator-working/1"}'
            self.assertEqual(receive(accepted.state, duplicate_key, max_bytes=65536).disposition, "rejected")

    def test_unknown_stale_time_only_changes_do_not_invent_evidence_events(self) -> None:
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            public = cut(claim())
            public = replace(
                public,
                evidence=replace(
                    public.evidence,
                    observations=tuple(
                        replace(item, fresh_until=None) if item.observation_id == "native" else item
                        for item in public.evidence.observations
                    ),
                ),
            )
            reference = publish(root, public, expected=public.applicability, produced_at=T, max_bytes=65536)
            first = canonical(snapshot(root, instance="owned", at=T, max_bytes=65536))
            accepted = receive(None, first, max_bytes=65536)
            raw = snapshot(root, instance="owned", at=T + 2 * DAY, max_bytes=65536, checkpoint=reference.sha256)
            current = receive(accepted.state, canonical(raw), max_bytes=65536)
            self.assertEqual(current.disposition, "accepted")
            parsed = json.loads(canonical(raw))
            self.assertIn("observation:native", parsed["facts"]["unknown_freshness"])
            self.assertTrue(parsed["facts"]["stale"])
            self.assertEqual(parsed["history"]["evidence_added"], [])


if __name__ == "__main__":
    unittest.main()
