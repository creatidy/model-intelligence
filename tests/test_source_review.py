"""Offline analysis structure, not external source truth or a product-value proof."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "SOURCE_VALUE_REVIEW.md"


class SourceReviewTests(unittest.TestCase):
    def test_product_question_cases_and_alternatives_are_present(self) -> None:
        packet = PACKET.read_text()
        cases = re.findall(r"^### E([1-6]):", packet, re.MULTILINE)
        self.assertEqual(cases, list("123456"))
        recommendation = packet.split("## Recommendation\n", 1)[1]
        self.assertRegex(recommendation.lstrip(), r"^\*\*ADAPT\*\*: the accepted outcome")
        for responsibility in (
            "Reference/fetch upstream",
            "Normalize in thin MI",
            "Preserve public history in MI",
            "Own locally in Router",
            "Direct upstream + Router adapters (STOP separate MI)",
            "Thin reusable MI layer (ADAPT)",
            "Broad separate MI service (GO)",
        ):
            with self.subTest(responsibility=responsibility):
                self.assertIn(responsibility, packet)

    def test_citations_are_resolved_and_git_sources_are_pinned(self) -> None:
        packet = PACKET.read_text()
        definitions = dict(re.findall(r"^\[([^\]]+)\]: (https://\S+)$", packet, re.MULTILINE))
        references = re.findall(r"\[[^\]\n]+\]\[([^\]]+)\]", packet)
        self.assertEqual(set(references), set(definitions))
        for name in ("models", "watch", "prices", "genai", "plans", "zcode"):
            with self.subTest(source=name):
                self.assertRegex(definitions[name], r"/(?:tree|blob)/[0-9a-f]{40}(?:/|$)")
        self.assertIn("no retained durable capture", " ".join(packet.split()))
        self.assertRegex(definitions["router-source"], r"/src/commit/[0-9a-f]{40}$")

    def test_indices_preserve_the_limited_receipt(self) -> None:
        for name in ("README.md", "ROADMAP.md"):
            with self.subTest(index=name):
                self.assertIn("(SOURCE_VALUE_REVIEW.md)", (ROOT / name).read_text())
        self.assertIn("No owner GO", (ROOT / "ROADMAP.md").read_text())

    def test_analysis_does_not_reintroduce_false_viability_gates(self) -> None:
        packet = " ".join(PACKET.read_text().split())
        for boundary in (
            "A same-context benchmark/price conflict is not a viability prerequisite",
            "Unknown campaign boundaries and conflicting claims are normal domain states",
            "no generalized dataset-redistribution gate",
            "not independently reproduced consumer receipts",
            "not authorization for GO",
            "Issue #12 is completed/closed; PR #23 is merged",
        ):
            with self.subTest(boundary=boundary):
                self.assertIn(boundary, packet)
        self.assertNotIn("## Original Acceptance Disposition", packet)
        self.assertNotIn("Keep issue #12 open", packet)
        self.assertNotIn("PR #23 unmerged", packet)
        for name in ("README.md", "ROADMAP.md", "ARCHITECTURE.md"):
            with self.subTest(document=name):
                text = " ".join((ROOT / name).read_text().split())
                self.assertIn("ADAPT", text)
                self.assertIn("completed/closed", text.lower())
                self.assertIn("not product go", text.lower())
                self.assertNotIn("Issue #12 is open", text)
                self.assertNotIn("Complete #12", text)

    def test_completed_publication_contract_is_not_documented_as_missing(self) -> None:
        for name in ("README.md", "ROADMAP.md", "ARCHITECTURE.md", "PUBLICATION_CONTRACT.md"):
            with self.subTest(document=name):
                text = " ".join((ROOT / name).read_text().split())
                self.assertIn("#13", text)
                self.assertIn("completed/closed", text.lower())
                self.assertIn("PR #26", text)
                self.assertIn("permanent", text)
                self.assertNotIn("not an agreed consumer wire API", text)
                self.assertNotIn("consumer contract is still To Prove", text)
                self.assertNotIn("Only in-memory evidence/views/deltas exist", text)
                self.assertNotIn("Approve the actual contract through", text)

    def test_completed_capability_research_is_not_production_mapping_approval(self) -> None:
        for name in ("README.md", "ROADMAP.md", "ARCHITECTURE.md"):
            with self.subTest(document=name):
                text = " ".join((ROOT / name).read_text().split())
                self.assertIn("#14", text)
                self.assertIn("PR #31", text)
                self.assertIn("completed/closed", text.lower())
                self.assertIn("production mapping", text)
                self.assertIn("installed acceptance", text)
                self.assertNotIn("To Prove small versioned language", text)
                self.assertNotIn("remaining #14 mapping", text)
                self.assertNotIn("#14 mapping remains", text)


if __name__ == "__main__":
    unittest.main()
