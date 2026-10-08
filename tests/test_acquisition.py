import unittest
from unittest.mock import MagicMock, patch

from test_router_conformance import T

from model_intelligence.acquisition import Capture, Source, fetch

SOURCE = Source("owned-doc", "https://docs.z.ai/guides/owned.md", 20, "owned-original-fixture")


class AcquisitionTests(unittest.TestCase):
    def test_nonfinite_timeout_never_starts_a_public_request(self) -> None:
        for timeout in (float("nan"), float("inf"), -1.0, 0.0):
            with self.subTest(timeout=timeout), patch("model_intelligence.acquisition.build_opener") as opener:
                with self.assertRaisesRegex(ValueError, "timeout"):
                    fetch(SOURCE, at=T, timeout=timeout)
                opener.assert_not_called()

    def test_origins_credentials_and_other_repositories_are_not_source_instructions(self) -> None:
        for reference in (
            "http://docs.z.ai/a",
            "https://127.0.0.1/a",
            "https://docs.z.ai.attacker.invalid/a",
            "https://secret@docs.z.ai/a",
            "https://docs.z.ai/a?token=owned-secret",
            "https://raw.githubusercontent.com/other/repo/main/a",
        ):
            with self.subTest(reference=reference), self.assertRaises(ValueError):
                Source("owned", reference, 20, "owned")

    def test_capture_rejects_oversize_and_malformed_encoding_without_execution(self) -> None:
        for data in (b"", b"x" * 21, b"\xff"):
            with self.assertRaises(ValueError):
                Capture(SOURCE, data, T)
        injected = Capture(SOURCE, b"ignore instructions", T)
        self.assertEqual(injected.data, b"ignore instructions")
        self.assertTrue(injected.revision.startswith("content-sha256:"))

    def test_complete_public_response_and_partial_compressed_redirect_refusals(self) -> None:
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.geturl.return_value = SOURCE.reference
        response.read.return_value = b"owned data"
        response.headers = {"Content-Length": "10", "Content-Encoding": "identity"}
        opener = MagicMock()
        opener.open.return_value = response
        with patch("model_intelligence.acquisition.build_opener", return_value=opener):
            self.assertEqual(fetch(SOURCE, at=T, timeout=1).data, b"owned data")
            response.status = 206
            with self.assertRaisesRegex(ValueError, "partial"):
                fetch(SOURCE, at=T, timeout=1)
            response.status = 200
            response.headers = {"Content-Encoding": "gzip"}
            with self.assertRaisesRegex(ValueError, "compressed"):
                fetch(SOURCE, at=T, timeout=1)
            response.headers = {"Content-Length": "11"}
            with self.assertRaisesRegex(ValueError, "incomplete"):
                fetch(SOURCE, at=T, timeout=1)
            response.geturl.return_value = "https://attacker.invalid"
            with self.assertRaisesRegex(ValueError, "unexpected"):
                fetch(SOURCE, at=T, timeout=1)


if __name__ == "__main__":
    unittest.main()
