"""Owned research examples, not a receiver, consent checker or redaction proof."""

import hashlib
import re
import unittest
from fractions import Fraction
from pathlib import Path

from test_router_conformance import T, base

from model_intelligence.contract import decode_public_evidence, encode_public_evidence

ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTICS = frozenset(
    {
        "LOCAL_ONLY",
        "PROPOSAL_ONLY",
        "CONSENT_ABSENT",
        "CONSENT_EXPIRED",
        "CONSENT_WITHDRAWN",
        "CONSENT_SCOPE_MISMATCH",
        "PROVENANCE_UNKNOWN",
        "PRIVATE_CONTENT_OR_LINKAGE",
        "COMPARISON_UNSUPPORTED",
        "CONTRACT_OR_RIGHTS_UNACCEPTED",
    }
)


class OperationalSharingReviewTests(unittest.TestCase):
    def test_owner_reject_and_nonimplementation_bounds_are_explicit(self) -> None:
        text = " ".join((ROOT / "OPERATIONAL_SHARING_REVIEW.md").read_text().split())
        for boundary in (
            "Owner decision: REJECT current operational intake",
            "#17 AC5",
            "not restart",
            "not an intake API",
            "no secret scanner/redactor/intake validator",
            "before separately selecting implementation",
            "code, not rights",
            "not a privacy guarantee",
            "whole-journey",
        ):
            with self.subTest(boundary=boundary):
                self.assertIn(boundary.lower(), text.lower())
        self.assertIn("https://arxiv.org/abs/2107.07002v1", text)
        self.assertIn("https://www.rfc-editor.org/rfc/rfc6973.html", text)
        self.assertIn("9dfa20931a46931d1e97d1f0efddcf2692afb7a7", text)
        self.assertIn("1dae1948f372e0f1739896655bb7db97d6b08460", text)
        self.assertIn("issues/17#issuecomment-15400", text)
        self.assertNotIn("Owner decision pending", text)

    def test_owner_reconsideration_and_rationale_are_preserved_without_authorization(self) -> None:
        text = " ".join((ROOT / "OPERATIONAL_SHARING_REVIEW.md").read_text().split())
        for criterion in (
            "specific named public-evidence/product problem",
            "Demonstrated improvement over public sources/reproduction and origin-local analysis",
            "proposed shared fields are necessary",
            "Explicit producer/consumer contract and lifecycle",
            "Voluntary scoped consent where private records are involved",
            "Source/user rights and negative conformance",
            "Separate owner approval before implementation",
            "core public-evidence role does not currently require private operational intake",
            "No material incremental product benefit",
            "confounded by workload, prompt, harness, reviewer",
            "privacy/linkage/lifecycle obligations without a demonstrated need",
            "not a permanent prohibition",
            "does not authorize a new receiver or bypass #15's production contract gate",
            "Neither the decision nor closure grants product GO",
        ):
            with self.subTest(criterion=criterion):
                self.assertIn(criterion, text)

    def test_public_status_records_reject_not_pending_or_production_permission(self) -> None:
        for name in ("README.md", "ARCHITECTURE.md", "ROADMAP.md"):
            text = " ".join((ROOT / name).read_text().split())
            with self.subTest(document=name):
                self.assertIn("REJECT current operational intake", text)
                self.assertIn("OPERATIONAL_SHARING_REVIEW.md", text)
                self.assertNotIn("explicit owner decision pending", text)

    def test_policy_table_has_fixed_diagnostics_not_raw_input_values(self) -> None:
        text = (ROOT / "OPERATIONAL_SHARING_REVIEW.md").read_text()
        rows = re.findall(r"^\| (EX\d+) \| [^\n]+ \| `([A-Z_]+)` \|$", text, re.MULTILINE)
        self.assertEqual(len(rows), len(DIAGNOSTICS))
        self.assertEqual({case for case, _ in rows}, {f"EX{i:02}" for i in range(1, 11)})
        self.assertEqual({code for _, code in rows}, DIAGNOSTICS)
        for _, code in rows:
            self.assertNotIn("SECRET-MARKER", code)
            self.assertNotIn("/owned-private/", code)

    def test_current_public_artifact_never_requires_optional_sharing_consent(self) -> None:
        public = base()
        control = encode_public_evidence(public, produced_at=T)
        for diagnostic in sorted(DIAGNOSTICS):
            with self.subTest(research_example=diagnostic):
                # No consent/scenario is passed into the existing public producer.
                data, reference = encode_public_evidence(public, produced_at=T)
                self.assertEqual((data, reference), control)
                self.assertEqual(decode_public_evidence(data, reference, max_bytes=65536), public)

    def test_owned_mixture_reverses_aggregate_without_proving_quality(self) -> None:
        a = Fraction(4, 5), Fraction(19, 20)
        b = Fraction(7, 10), Fraction(9, 10)
        self.assertTrue(all(x > y for x, y in zip(a, b, strict=True)))
        mixed_a = (9 * a[0] + a[1]) / 10
        mixed_b = (b[0] + 9 * b[1]) / 10
        self.assertEqual(mixed_a, Fraction(163, 200))
        self.assertEqual(mixed_b, Fraction(22, 25))
        self.assertLess(mixed_a, mixed_b)
        self.assertGreater(sum(a) / 2, sum(b) / 2)

    def test_owned_persistent_hash_can_link_a_small_known_dictionary(self) -> None:
        candidates = ("/owned-private/project-a", "/owned-private/project-b", "/owned-private/project-c")
        observed = hashlib.sha256(candidates[1].encode()).hexdigest()
        dictionary = {hashlib.sha256(value.encode()).hexdigest(): value for value in candidates}
        self.assertEqual(dictionary[observed], candidates[1])
        self.assertEqual(observed, hashlib.sha256(candidates[1].encode()).hexdigest())
        # This controlled attack says nothing about all hashes or actual user data.


if __name__ == "__main__":
    unittest.main()
