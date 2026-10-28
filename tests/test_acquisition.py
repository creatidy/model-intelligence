import unittest
from http.client import IncompleteRead
from unittest.mock import MagicMock, patch

from test_router_conformance import T

from model_intelligence.acquisition import Capture, Source, fetch
from model_intelligence.terminal_bench import SOURCES as TERMINAL_BENCH_SOURCES

SOURCE = Source("owned-doc", "https://docs.z.ai/guides/owned.md", 20, "owned-original-fixture")


class AcquisitionTests(unittest.TestCase):
    def test_pinned_terminal_bench_submission_paths_are_the_only_new_raw_github_origin(self) -> None:
        self.assertEqual(len(TERMINAL_BENCH_SOURCES), 4)
        for source in TERMINAL_BENCH_SOURCES:
            self.assertEqual(source.license.split()[0], "Apache-2.0")
            self.assertIn(
                "/harbor-framework/terminal-bench/6964e9252c90227fc1cfa26cbc59aee4134792e4/leaderboard/submissions/",
                source.reference,
            )
        for reference in (
            "https://raw.githubusercontent.com/harbor-framework/terminal-bench/main/leaderboard/submissions/model.json",
            "https://raw.githubusercontent.com/harbor-framework/terminal-bench/0000000000000000000000000000000000000000/leaderboard/submissions/model.json",
            "https://raw.githubusercontent.com/harbor-framework/terminal-bench/6964e9252c90227fc1cfa26cbc59aee4134792e4/leaderboard/model.json",
        ):
            with self.subTest(reference=reference), self.assertRaisesRegex(ValueError, "source-path"):
                Source("unapproved-terminal-bench-source", reference, 32_768, "Apache-2.0")

    def test_truncated_body_protocol_exception_is_safe_incomplete_response(self) -> None:
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.geturl.return_value = SOURCE.reference
        response.headers = {"Content-Encoding": "identity"}
        response.read.side_effect = IncompleteRead(b"OWNED-SECRET-PARTIAL", 10)
        opener = MagicMock()
        opener.open.return_value = response
        with patch("model_intelligence.acquisition.build_opener", return_value=opener):
            with self.assertRaisesRegex(ValueError, "source-incomplete-response"):
                fetch(SOURCE, at=T, timeout=1)

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
        with self.assertRaisesRegex(ValueError, "source-http-status"):
            Capture(SOURCE, b"owned data", T, 204)
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
            captured = fetch(SOURCE, at=T, timeout=1)
            self.assertEqual(captured.data, b"owned data")
            self.assertEqual(captured.http_status, 200)
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

    def test_bounded_oversize_reads_are_not_misclassified_as_incomplete(self) -> None:
        cases = (
            (b"x" * SOURCE.max_bytes, str(SOURCE.max_bytes), None),
            (b"x" * (SOURCE.max_bytes + 1), str(SOURCE.max_bytes + 1), "source-size-policy"),
            (b"x" * (SOURCE.max_bytes + 1), None, "source-size-policy"),
            (b"x" * (SOURCE.max_bytes + 1), str(SOURCE.max_bytes), "source-incomplete-response"),
            (b"short", str(SOURCE.max_bytes + 10), "source-incomplete-response"),
            (b"short", "not-a-length", "source-incomplete-response"),
        )
        for data, length, diagnostic in cases:
            with self.subTest(size=len(data), length=length, diagnostic=diagnostic):
                response = MagicMock()
                response.__enter__.return_value = response
                response.status = 200
                response.geturl.return_value = SOURCE.reference
                response.headers = {"Content-Encoding": "identity"}
                if length is not None:
                    response.headers["Content-Length"] = length
                response.read.return_value = data
                opener = MagicMock()
                opener.open.return_value = response
                with patch("model_intelligence.acquisition.build_opener", return_value=opener):
                    if diagnostic is None:
                        self.assertEqual(fetch(SOURCE, at=T, timeout=1).data, data)
                    else:
                        with self.assertRaisesRegex(ValueError, diagnostic):
                            fetch(SOURCE, at=T, timeout=1)


if __name__ == "__main__":
    unittest.main()
