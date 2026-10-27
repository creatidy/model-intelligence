import json
import unittest
from email.message import Message
from http.client import IncompleteRead
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from model_intelligence.aa_probe import FREE_ENDPOINT, ProbeResult, probe

SECRET = "synthetic-test-key-never-persist"


def payload() -> bytes:
    return json.dumps(
        {
            "tier": "free",
            "intelligence_index_version": 4.1,
            "pagination": {"page": 1, "page_size": 200, "total_pages": 4, "has_more": True},
            "data": [
                {
                    "id": "synthetic-id",
                    "name": "GPT-6 Luna (max)",
                    "slug": "gpt-6-luna",
                    "release_date": "2026-09-22",
                    "model_creator": {"id": "synthetic-creator", "name": "OpenAI"},
                    "evaluations": {
                        "artificial_analysis_intelligence_index": 50,
                        "artificial_analysis_coding_index": 45,
                        "artificial_analysis_agentic_index": 47,
                        "artificial_analysis_finance_and_accounting_index": 20,
                        "artificial_analysis_strategy_and_ops_index": 21,
                        "artificial_analysis_legal_index": 22,
                        "artificial_analysis_healthcare_and_medical_index": 23,
                        "artificial_analysis_engineering_index": 24,
                        "artificial_analysis_economics_index": 25,
                    },
                    "artificial_analysis_intelligence_index_cost": {
                        "total_cost": 1,
                        "cost_per_task": {"total_cost": 0.1},
                    },
                    "pricing": {"price_1m_input_tokens": 1, "price_1m_output_tokens": 2},
                    "performance": {"median_output_tokens_per_second": 2},
                },
                {
                    "id": "synthetic-id-2",
                    "name": "GLM-5.3-Flash (max)",
                    "slug": "glm-5.3-flash",
                    "release_date": None,
                    "model_creator": {"id": "synthetic-creator-2", "name": "Z.ai"},
                    "evaluations": {"artificial_analysis_coding_index": 40},
                    "artificial_analysis_intelligence_index_cost": None,
                    "pricing": {},
                    "performance": {},
                },
            ],
        }
    ).encode()


def response(body: bytes | None = None, *, headers: Message | None = None) -> MagicMock:
    result = MagicMock()
    result.__enter__.return_value = result
    result.status = 200
    result.geturl.return_value = FREE_ENDPOINT
    result.headers = headers or Message()
    result.read.return_value = payload() if body is None else body
    return result


class ArtificialAnalysisProbeTests(unittest.TestCase):
    def test_absent_credential_does_not_construct_or_send_request(self) -> None:
        with patch.dict("os.environ", {}, clear=True), patch("model_intelligence.aa_probe.build_opener") as opener:
            result = probe()
        self.assertEqual(result, ProbeResult("AUTH_ABSENT", False))
        opener.assert_not_called()

    def test_one_bounded_free_page_returns_metadata_not_scores_or_body(self) -> None:
        headers = Message()
        headers["X-RateLimit-Limit"] = "100"
        headers["X-RateLimit-Remaining"] = "99"
        headers["X-RateLimit-Reset"] = "synthetic-reset"
        opener = MagicMock()
        opener.open.return_value = response(headers=headers)
        with patch("model_intelligence.aa_probe.build_opener", return_value=opener):
            result = probe(api_key=SECRET)
        self.assertEqual(result.outcome, "SUCCESS")
        self.assertTrue(result.request_made)
        self.assertEqual((result.status, result.tier), (200, "free"))
        self.assertEqual((result.page, result.page_size, result.total_pages, result.has_more), (1, 200, 4, True))
        self.assertEqual(result.candidate_records, ("glm-5.3-flash", "gpt-6-luna-max"))
        self.assertIn("evaluations.artificial_analysis_coding_index", result.field_categories)
        self.assertIn("evaluations.artificial_analysis_agentic_index", result.field_categories)
        self.assertIn("evaluations.artificial_analysis_engineering_index", result.field_categories)
        self.assertIn("artificial_analysis_intelligence_index_cost.cost_per_task.total_cost", result.field_categories)
        self.assertIn("pricing.price_1m_output_tokens", result.field_categories)
        self.assertIn("performance.median_output_tokens_per_second", result.field_categories)
        self.assertEqual(opener.open.call_count, 1)
        (request,) = opener.open.call_args.args[:1]
        self.assertEqual(request.full_url, FREE_ENDPOINT)
        sent_headers = {name.casefold(): value for name, value in request.header_items()}
        self.assertEqual(sent_headers["x-api-key"], SECRET)
        rendered = repr(result)
        self.assertNotIn(SECRET, rendered)
        self.assertNotIn("synthetic-id", rendered)
        self.assertNotIn('artificial_analysis_coding_index": 40', rendered)

    def test_auth_tier_and_quota_statuses_are_distinct_and_bodies_are_ignored(self) -> None:
        for status, expected in ((401, "AUTH_FAILED"), (403, "TIER_RESTRICTED"), (429, "QUOTA_LIMITED")):
            with self.subTest(status=status):
                headers = Message()
                headers["Retry-After"] = "30"
                error = HTTPError(FREE_ENDPOINT, status, "synthetic private body", headers, None)
                opener = MagicMock()
                opener.open.side_effect = error
                with patch("model_intelligence.aa_probe.build_opener", return_value=opener):
                    result = probe(api_key=SECRET)
                self.assertEqual((result.outcome, result.status), (expected, status))
                self.assertIn(("Retry-After", 30), result.rate_limits)
                self.assertNotIn("synthetic private body", repr(result))
                self.assertEqual(opener.open.call_count, 1)

    def test_unsupported_pagination_fields_and_oversized_or_truncated_bodies_fail_closed(self) -> None:
        decoded = json.loads(payload())
        decoded["pagination"]["next_cursor"] = "private-cursor"
        unknown = response(json.dumps(decoded).encode())
        with patch(
            "model_intelligence.aa_probe.build_opener", return_value=MagicMock(open=MagicMock(return_value=unknown))
        ):
            result = probe(api_key=SECRET)
        self.assertEqual(result.outcome, "UNSUPPORTED_SCHEMA")
        self.assertEqual(result.unsupported_fields, ("pagination",))
        self.assertNotIn("private-cursor", repr(result))

        decoded = json.loads(payload())
        decoded["data"][0]["new_api_field"] = "private-value"
        unknown = response(json.dumps(decoded).encode())
        with patch(
            "model_intelligence.aa_probe.build_opener", return_value=MagicMock(open=MagicMock(return_value=unknown))
        ):
            result = probe(api_key=SECRET)
        self.assertEqual(result.outcome, "UNSUPPORTED_SCHEMA")
        self.assertEqual(result.unsupported_fields, ("model-record",))

        oversized = response(b"x" * 33)
        with patch(
            "model_intelligence.aa_probe.build_opener", return_value=MagicMock(open=MagicMock(return_value=oversized))
        ):
            result = probe(api_key=SECRET, max_bytes=32)
        self.assertEqual(result.outcome, "UNSUPPORTED_SCHEMA")

        truncated = response()
        truncated.read.side_effect = IncompleteRead(b'{"tier":', 30)
        with patch(
            "model_intelligence.aa_probe.build_opener", return_value=MagicMock(open=MagicMock(return_value=truncated))
        ):
            result = probe(api_key=SECRET)
        self.assertEqual(result.outcome, "NETWORK_FAILED")

    def test_malformed_json_and_transport_failure_are_sanitized(self) -> None:
        malformed = response(b"not-json-secret-value")
        with patch(
            "model_intelligence.aa_probe.build_opener", return_value=MagicMock(open=MagicMock(return_value=malformed))
        ):
            result = probe(api_key=SECRET)
        self.assertEqual(result.outcome, "UNSUPPORTED_SCHEMA")
        self.assertNotIn("not-json-secret-value", repr(result))
        opener = MagicMock()
        opener.open.side_effect = URLError("private transport response")
        with patch("model_intelligence.aa_probe.build_opener", return_value=opener):
            result = probe(api_key=SECRET)
        self.assertEqual(result.outcome, "NETWORK_FAILED")
        self.assertNotIn("private transport response", repr(result))

    def test_malformed_tier_value_is_not_reflected_from_authenticated_body(self) -> None:
        decoded = json.loads(payload())
        decoded["tier"] = {"private": SECRET}
        result_response = response(json.dumps(decoded).encode())
        with patch(
            "model_intelligence.aa_probe.build_opener",
            return_value=MagicMock(open=MagicMock(return_value=result_response)),
        ):
            result = probe(api_key=SECRET)
        self.assertEqual(result.outcome, "UNSUPPORTED_SCHEMA")
        self.assertIsNone(result.tier)
        self.assertNotIn(SECRET, repr(result))

    def test_response_field_and_rate_header_values_are_sanitized(self) -> None:
        decoded = json.loads(payload())
        decoded[SECRET] = "ignored-secret-value"
        headers = Message()
        headers["X-RateLimit-Limit"] = SECRET
        result_response = response(json.dumps(decoded).encode(), headers=headers)
        with patch(
            "model_intelligence.aa_probe.build_opener",
            return_value=MagicMock(open=MagicMock(return_value=result_response)),
        ):
            result = probe(api_key=SECRET)
        self.assertEqual(result.outcome, "UNSUPPORTED_SCHEMA")
        self.assertNotIn(SECRET, repr(result))


if __name__ == "__main__":
    unittest.main()
