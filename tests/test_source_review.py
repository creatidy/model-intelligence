"""Offline packet consistency, not source truth, rights clearance or A/B/C proof."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "SOURCE_VALUE_REVIEW.md"


class SourceReviewTests(unittest.TestCase):
    def test_original_acceptance_remains_partial_or_unmet(self) -> None:
        packet = PACKET.read_text()
        rows = re.findall(r"^\| AC([1-5]) [^|]+\| ([A-Z]+) \|", packet, re.MULTILINE)
        self.assertEqual(rows, [("1", "PARTIAL"), ("2", "PARTIAL"), ("3", "PARTIAL"), ("4", "UNMET"), ("5", "PARTIAL")])
        for boundary in (
            "Citation-Only ADAPT",
            "not a full A/B/C proof and not product",
            "Unresolved redistribution rights remain",
            "No contemporaneous same-context benchmark/price conflict was established",
            "campaign terminal boundary remains uncertain",
            "Keep issue #12 open and downstream value/rights gates unmet",
        ):
            with self.subTest(boundary=boundary):
                self.assertIn(boundary, " ".join(packet.split()))

    def test_citations_are_resolved_and_git_sources_are_pinned(self) -> None:
        packet = PACKET.read_text()
        definitions = dict(re.findall(r"^\[([^\]]+)\]: (https://\S+)$", packet, re.MULTILINE))
        references = re.findall(r"\[[^\]\n]+\]\[([^\]]+)\]", packet)
        self.assertEqual(set(references), set(definitions))
        for name in ("models", "watch", "prices", "genai", "plans", "model-card", "zcode"):
            with self.subTest(source=name):
                self.assertRegex(definitions[name], r"/(?:tree|blob)/[0-9a-f]{40}(?:/|$)")
        self.assertIn("no retained durable capture", packet)
        self.assertIn("no successful parent re-fetch is claimed", packet)

    def test_indices_preserve_the_limited_receipt(self) -> None:
        for name in ("README.md", "ROADMAP.md"):
            with self.subTest(index=name):
                self.assertIn("(SOURCE_VALUE_REVIEW.md)", (ROOT / name).read_text())
        self.assertIn("partial/unmet criteria; no product GO", (ROOT / "ROADMAP.md").read_text())


if __name__ == "__main__":
    unittest.main()
