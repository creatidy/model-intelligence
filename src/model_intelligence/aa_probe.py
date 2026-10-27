"""One-request, metadata-only Artificial Analysis Free-endpoint diagnostic."""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from email.message import Message
from http.client import HTTPException, IncompleteRead
from typing import NoReturn, cast
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

FREE_ENDPOINT = "https://artificialanalysis.ai/api/v2/language/models/free?page=1"
MAX_RESPONSE_BYTES = 2_000_000
_TOP_LEVEL = {"tier", "intelligence_index_version", "pagination", "data"}
_PAGINATION = {"page", "page_size", "total_pages", "has_more"}
_ROW = {
    "id",
    "name",
    "slug",
    "release_date",
    "model_creator",
    "evaluations",
    "artificial_analysis_intelligence_index_cost",
    "pricing",
    "performance",
}
_RATE_HEADERS = ("X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset", "Retry-After")
_FIELD_CATEGORIES = ("evaluations", "artificial_analysis_intelligence_index_cost", "pricing", "performance")
_NESTED_FIELDS = {
    "model_creator": {"id", "name"},
    "evaluations": {
        "artificial_analysis_intelligence_index",
        "artificial_analysis_coding_index",
        "artificial_analysis_agentic_index",
        "artificial_analysis_finance_and_accounting_index",
        "artificial_analysis_strategy_and_ops_index",
        "artificial_analysis_legal_index",
        "artificial_analysis_healthcare_and_medical_index",
        "artificial_analysis_engineering_index",
        "artificial_analysis_economics_index",
    },
    "artificial_analysis_intelligence_index_cost": {"total_cost", "cost_per_task"},
    "pricing": {
        "price_1m_input_tokens",
        "price_1m_output_tokens",
        "price_1m_cache_hit_tokens",
        "price_1m_cache_write_tokens",
    },
    "performance": {
        "median_output_tokens_per_second",
        "median_time_to_first_token_seconds",
        "median_time_to_first_answer_token_seconds",
        "median_end_to_end_response_time_seconds",
    },
}


@dataclass(frozen=True)
class ProbeResult:
    outcome: str
    request_made: bool
    status: int | None = None
    tier: str | None = None
    rate_limits: tuple[tuple[str, int], ...] = ()
    page: int | None = None
    page_size: int | None = None
    total_pages: int | None = None
    has_more: bool | None = None
    records_on_page: int | None = None
    candidate_records: tuple[str, ...] = ()
    field_categories: tuple[str, ...] = ()
    unsupported_fields: tuple[str, ...] = ()


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req: object, fp: object, code: int, msg: str, headers: object, newurl: str) -> None:
        return None


def _headers(headers: Message) -> tuple[tuple[str, int], ...]:
    values: list[tuple[str, int]] = []
    for name in _RATE_HEADERS:
        raw = headers.get(name)
        if raw is None:
            continue
        value = str(raw)
        if value.isascii() and value.isdigit() and len(value) <= 20:
            values.append((name, int(value)))
    return tuple(values)


def _tier_header(headers: Message) -> str | None:
    tier = headers.get("X-AA-Tier")
    return tier if tier in {"free", "pro", "commercial"} else None


def _reject_json_constant(_value: str) -> NoReturn:
    raise ValueError("nonstandard-json-number")


def _candidate(name: str, slug: str) -> tuple[str, ...]:
    text = f"{name} {slug}".casefold().replace("_", "-")
    matches: list[str] = []
    if "gpt-6.1-sol" in text or "gpt-6-1-sol" in text:
        matches.append("gpt-6.1-sol")
    if "gpt-6-luna" in text and "max" in text:
        matches.append("gpt-6-luna-max")
    if "glm-5.3-flash" in text:
        matches.append("glm-5.3-flash")
    elif "glm-5.3" in text:
        matches.append("glm-5.3")
    return tuple(matches)


def _metadata(raw: bytes, status: int, headers: Message) -> ProbeResult:
    try:
        decoded = json.loads(raw, parse_constant=_reject_json_constant)
    except (UnicodeError, ValueError, RecursionError):
        return ProbeResult("UNSUPPORTED_SCHEMA", True, status, rate_limits=_headers(headers))
    if not isinstance(decoded, dict):
        return ProbeResult("UNSUPPORTED_SCHEMA", True, status, rate_limits=_headers(headers))
    envelope = cast(dict[str, object], decoded)
    if set(envelope) != _TOP_LEVEL:
        raw_tier = envelope.get("tier")
        safe_tier = raw_tier if isinstance(raw_tier, str) and raw_tier in {"free", "pro", "commercial"} else None
        return ProbeResult(
            "UNSUPPORTED_SCHEMA",
            True,
            status,
            safe_tier,
            _headers(headers),
            unsupported_fields=("envelope",),
        )
    tier = envelope["tier"]
    page = envelope["pagination"]
    rows = envelope["data"]
    version = envelope["intelligence_index_version"]
    if (
        not isinstance(tier, str)
        or tier not in {"free", "pro", "commercial"}
        or not isinstance(page, dict)
        or set(cast(dict[str, object], page)) != _PAGINATION
        or not isinstance(rows, list)
        or type(version) not in {int, float}
        or (type(version) is float and not math.isfinite(version))
    ):
        safe_tier = tier if isinstance(tier, str) and tier in {"free", "pro", "commercial"} else None
        return ProbeResult(
            "UNSUPPORTED_SCHEMA",
            True,
            status,
            safe_tier,
            _headers(headers),
            unsupported_fields=("pagination",),
        )
    pagination = cast(dict[str, object], page)
    if (
        any(
            type(pagination[key]) is not int or cast(int, pagination[key]) < 1
            for key in ("page", "page_size", "total_pages")
        )
        or type(pagination["has_more"]) is not bool
    ):
        return ProbeResult("UNSUPPORTED_SCHEMA", True, status, tier, _headers(headers))
    hits: set[str] = set()
    categories: set[str] = set()
    records = cast(list[object], rows)
    for item in records:
        if not isinstance(item, dict):
            return ProbeResult("UNSUPPORTED_SCHEMA", True, status, tier, _headers(headers))
        row = cast(dict[str, object], item)
        if set(row) != _ROW or not isinstance(row.get("name"), str) or not isinstance(row.get("slug"), str):
            return ProbeResult(
                "UNSUPPORTED_SCHEMA",
                True,
                status,
                tier,
                _headers(headers),
                unsupported_fields=("model-record",),
            )
        for field, accepted in _NESTED_FIELDS.items():
            value = row[field]
            if field in _FIELD_CATEGORIES:
                categories.add(field)
            if value is None and field in {"model_creator", "artificial_analysis_intelligence_index_cost"}:
                continue
            if not isinstance(value, dict):
                return ProbeResult("UNSUPPORTED_SCHEMA", True, status, tier, _headers(headers))
            nested_unknown = set(cast(dict[str, object], value)) - accepted
            if nested_unknown:
                return ProbeResult(
                    "UNSUPPORTED_SCHEMA",
                    True,
                    status,
                    tier,
                    _headers(headers),
                    unsupported_fields=("nested-model-record",),
                )
            if field in _FIELD_CATEGORIES:
                categories.update(f"{field}.{key}" for key in cast(dict[str, object], value))
        cost = row["artificial_analysis_intelligence_index_cost"]
        if isinstance(cost, dict):
            breakdown = cast(dict[str, object], cost).get("cost_per_task")
            if breakdown is not None and (
                not isinstance(breakdown, dict) or set(cast(dict[str, object], breakdown)) != {"total_cost"}
            ):
                return ProbeResult("UNSUPPORTED_SCHEMA", True, status, tier, _headers(headers))
            if isinstance(breakdown, dict):
                categories.update(
                    {
                        "artificial_analysis_intelligence_index_cost.cost_per_task",
                        "artificial_analysis_intelligence_index_cost.cost_per_task.total_cost",
                    }
                )
        hits.update(_candidate(cast(str, row["name"]), cast(str, row["slug"])))
    return ProbeResult(
        "SUCCESS",
        True,
        status,
        tier,
        _headers(headers),
        cast(int, pagination["page"]),
        cast(int, pagination["page_size"]),
        cast(int, pagination["total_pages"]),
        pagination["has_more"],
        len(records),
        tuple(sorted(hits)),
        tuple(sorted(categories)),
        (),
    )


def probe(*, api_key: str | None = None, timeout: float = 10.0, max_bytes: int = MAX_RESPONSE_BYTES) -> ProbeResult:
    """Make one bounded Free request; never return or persist its response body."""
    if api_key is None:
        api_key = os.environ.get("AA_API_KEY")
    if api_key is None or not api_key.strip():
        return ProbeResult("AUTH_ABSENT", False)
    if (
        not math.isfinite(timeout)
        or timeout <= 0
        or type(max_bytes) is not int
        or not 1 <= max_bytes <= MAX_RESPONSE_BYTES
    ):
        raise ValueError("invalid-probe-policy")
    if "\r" in api_key or "\n" in api_key:
        return ProbeResult("AUTH_ABSENT", False)
    request = Request(
        FREE_ENDPOINT,
        headers={"x-api-key": api_key, "Accept": "application/json", "Accept-Encoding": "identity"},
    )
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            if response.status != 200 or response.geturl() != FREE_ENDPOINT:
                return ProbeResult("NETWORK_FAILED", True, response.status, rate_limits=_headers(response.headers))
            if response.headers.get("Content-Encoding", "identity").lower() != "identity":
                return ProbeResult("UNSUPPORTED_SCHEMA", True, response.status, rate_limits=_headers(response.headers))
            raw = response.read(max_bytes + 1)
            if len(raw) > max_bytes:
                return ProbeResult("UNSUPPORTED_SCHEMA", True, response.status, rate_limits=_headers(response.headers))
            return _metadata(raw, response.status, response.headers)
    except HTTPError as error:
        outcome = {401: "AUTH_FAILED", 403: "TIER_RESTRICTED", 429: "QUOTA_LIMITED"}.get(error.code, "NETWORK_FAILED")
        try:
            return ProbeResult(outcome, True, error.code, _tier_header(error.headers), _headers(error.headers))
        finally:
            error.close()
    except (IncompleteRead, HTTPException, OSError, URLError, TimeoutError):
        return ProbeResult("NETWORK_FAILED", True)
