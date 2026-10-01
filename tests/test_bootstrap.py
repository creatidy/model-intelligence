"""Deterministic smoke tests for the installed bootstrap package."""

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
        self.assertEqual(metadata["Requires-Python"], ">=3.12")
        self.assertEqual(metadata["License-Expression"], "Apache-2.0")
        self.assertEqual(metadata.get_all("Requires-Dist", []), [])
