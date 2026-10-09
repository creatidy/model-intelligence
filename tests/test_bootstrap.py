"""Deterministic checks for truthful package metadata and installed support."""

import unittest
from importlib.metadata import distribution
from importlib.resources import files

import model_intelligence


class BootstrapTests(unittest.TestCase):
    def test_package_import_and_typing_marker(self) -> None:
        self.assertEqual(model_intelligence.__name__, "model_intelligence")
        self.assertTrue(files(model_intelligence).joinpath("py.typed").is_file())

    def test_installed_distribution_metadata(self) -> None:
        metadata = distribution("model-intelligence").metadata
        self.assertEqual(metadata["Name"], "model-intelligence")
        self.assertEqual(metadata["Summary"], "Public AI ecosystem evidence, provenance and immutable publication")
        self.assertEqual(metadata["Requires-Python"], ">=3.12")
        self.assertEqual(metadata["License-Expression"], "Apache-2.0")
        self.assertEqual(metadata.get_all("Requires-Dist", []), [])

    def test_support_resource_preserves_explicit_compatibility_and_scope(self) -> None:
        support = files(model_intelligence).joinpath("INSTALLATION.md").read_text(encoding="utf-8")
        for required in (
            "mi.public-evidence-working/1",
            "mi.public-evidence-working/2",
            "mi.operator-working/1",
            "import_legacy",
            "history-losing publication",
            "not a published",
            "uv_build==0.9.30",
            "#19",
        ):
            self.assertIn(required, support)
