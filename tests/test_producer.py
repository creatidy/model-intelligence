import tempfile
import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from test_native_evidence import claim, cut
from test_router_conformance import DAY, PLAN, T, augment, base, observation

from model_intelligence.contract import encode_public_evidence
from model_intelligence.evidence import BaselineClaim, Money, OverrideClaim, Period, Terms
from model_intelligence.producer import import_legacy, publish, retained
from model_intelligence.projection import effective_at


class ProducerTests(unittest.TestCase):
    def test_version_two_explicit_future_correction_withdrawal_and_expiry_retain_cuts(self) -> None:
        original = base()
        future = BaselineClaim(
            PLAN,
            Terms(price=Money(Decimal("25"), "USD", "month")),
            claim_id="future",
            observation_id="future",
            effective_from=T + DAY,
            revises="base",
        )
        promotion = OverrideClaim(
            PLAN,
            "owned-campaign",
            Terms(price=Money(Decimal("5"), "USD", "month")),
            Period(T, T + DAY),
            claim_id="promotion",
            observation_id="promotion",
            effective_from=T,
        )
        declared = augment(
            original, observed=(observation("future"), observation("promotion")), claims=(future, promotion)
        )
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            old_ref = publish(root, original, expected=original.applicability, produced_at=T, max_bytes=65536)
            next_ref = publish(root, declared, expected=original.applicability, produced_at=T, max_bytes=65536)
            assert promotion.terms is not None
            self.assertEqual(effective_at(declared.evidence, T).offers[0].terms.price, promotion.terms.price)
            self.assertEqual(effective_at(declared.evidence, T + DAY).offers[0].terms.price, future.terms.price)
            withdrawal = OverrideClaim(
                PLAN,
                "owned-campaign",
                None,
                None,
                claim_id="withdrawal",
                observation_id="withdrawal",
                effective_from=T,
                revises="promotion",
            )
            corrected = augment(declared, observed=(observation("withdrawal"),), claims=(withdrawal,))
            final_ref = publish(root, corrected, expected=original.applicability, produced_at=T + DAY, max_bytes=65536)
            self.assertEqual(
                effective_at(corrected.evidence, T).offers[0].terms.price,
                effective_at(original.evidence, T).offers[0].terms.price,
            )
            self.assertTrue(all((root / f"{ref.sha256}.json").exists() for ref in (old_ref, next_ref, final_ref)))
            with self.assertRaises(ValueError):
                publish(root, original, expected=original.applicability, produced_at=T + 2 * DAY, max_bytes=65536)
            actual = retained(root, max_bytes=65536)
            assert actual is not None
            self.assertEqual(actual[1], final_ref)

    def test_explicit_legacy_migration_preserves_original_and_is_retryable(self) -> None:
        original = base()
        data, reference = encode_public_evidence(original, produced_at=T)
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            changed = import_legacy(
                root, data, reference, expected=original.applicability, produced_at=T + DAY, max_bytes=65536
            )
            self.assertNotEqual(changed, reference)
            self.assertEqual((root / f"{reference.sha256}.legacy.json").read_bytes(), data)
            self.assertEqual(
                import_legacy(
                    root, data, reference, expected=original.applicability, produced_at=T + DAY, max_bytes=65536
                ),
                changed,
            )
            current = retained(root, max_bytes=65536)
            assert current is not None
            self.assertEqual(current[2], original)
            with self.assertRaisesRegex(ValueError, "unsupported-version"):
                import_legacy(
                    root,
                    current[0],
                    current[1],
                    expected=original.applicability,
                    produced_at=T + 2 * DAY,
                    max_bytes=65536,
                )
            self.assertEqual(retained(root, max_bytes=65536), current)

    def test_validated_atomic_publication_and_same_generation_retry(self) -> None:
        public = cut(claim())
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            reference = publish(root, public, expected=public.applicability, produced_at=T, max_bytes=65536)
            self.assertEqual(
                publish(root, public, expected=public.applicability, produced_at=T, max_bytes=65536), reference
            )
            stored = retained(root, max_bytes=65536)
            assert stored is not None
            self.assertEqual((stored[1], stored[2]), (reference, public))

    def test_partial_unsupported_and_history_losing_update_never_activates(self) -> None:
        public = cut(claim())
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            original = publish(root, public, expected=public.applicability, produced_at=T, max_bytes=65536)
            old_bytes = retained(root, max_bytes=65536)
            with self.assertRaises(ValueError):
                publish(
                    root,
                    public,
                    expected=replace(public.applicability, channel="different"),
                    produced_at=T + DAY,
                    max_bytes=65536,
                )
            with self.assertRaises(ValueError):
                publish(root, public, expected=public.applicability, produced_at=T + DAY, max_bytes=1)
            with self.assertRaises(ValueError):
                publish(root, cut(), expected=public.applicability, produced_at=T + DAY, max_bytes=65536)
            self.assertEqual(retained(root, max_bytes=65536), old_bytes)
            self.assertEqual((root / "current").read_text(), original.sha256)

    def test_interrupted_activation_keeps_old_cut_and_retry_preserves_both(self) -> None:
        public = cut(claim())
        newer = cut(claim(), claim("future", effective=T + DAY, revises="native"))
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            original = publish(root, public, expected=public.applicability, produced_at=T, max_bytes=65536)
            with patch("model_intelligence.producer.os.replace", side_effect=OSError("owned interruption")):
                with self.assertRaises(OSError):
                    publish(root, newer, expected=public.applicability, produced_at=T + DAY, max_bytes=65536)
            stored = retained(root, max_bytes=65536)
            assert stored is not None
            self.assertEqual(stored[1], original)
            reference = publish(root, newer, expected=public.applicability, produced_at=T + DAY, max_bytes=65536)
            self.assertTrue((root / f"{original.sha256}.json").exists())
            self.assertTrue((root / f"{reference.sha256}.json").exists())
            self.assertEqual((root / "current").read_text(), reference.sha256)


if __name__ == "__main__":
    unittest.main()
