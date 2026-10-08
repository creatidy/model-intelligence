"""Selected upstream-backed GLM Flash facts and original public-offer annotations.

No linked examples, weights, indexes or billing/account endpoints are followed.
"""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal
from pathlib import Path
from typing import cast

from model_intelligence.acquisition import Capture, Source, fetch
from model_intelligence.contract import Applicability, PublicEvidence, UncertainCampaign
from model_intelligence.evidence import (
    BaselineClaim,
    Benchmark,
    Capability,
    DailyWindow,
    Evidence,
    Model,
    ModelClaim,
    Money,
    NativeLimit,
    Observation,
    Plan,
    Quota,
    Surface,
    SurfaceClaim,
    SurfaceEvidence,
    Terms,
)
from model_intelligence.producer import publish, record_refresh_status, retained
from model_intelligence.publication import CutReference, decode_cut

CATALOG_PIN = "f014f106dd414d575de2d0160d91267e2e7cb119"
CATALOG = f"https://raw.githubusercontent.com/anomalyco/models.dev/{CATALOG_PIN}/"
ADAPTER = "zai-flash-public/1"
FACT_RIGHTS = "Original public factual annotations/citations; source pages not redistributed"
SOURCES = (
    Source("catalog", CATALOG + "models/zhipuai/glm-5.3-flash.toml", 1661, "MIT models.dev 2025"),
    Source("api", CATALOG + "providers/zai/models/glm-5.3-flash.toml", 551, "MIT models.dev 2025"),
    Source("coding", CATALOG + "providers/zai-coding-plan/models/glm-5.3-flash.toml", 437, "MIT models.dev 2025"),
    Source("prices", "https://docs.z.ai/guides/overview/pricing.md", 2620, FACT_RIGHTS),
    Source("plans", "https://docs.z.ai/devpack/overview.md", 8315, FACT_RIGHTS),
    Source("campaign", "https://docs.z.ai/devpack/notice/event-glm-5.3-flash.md", 1947, FACT_RIGHTS),
    Source("interface", "https://docs.z.ai/api-reference/llm/chat-completion.md", 44328, FACT_RIGHTS),
    Source("cohort", "https://docs.z.ai/devpack/notice/usage-revision.md", 10063, FACT_RIGHTS),
)
SOURCE_CONFIG = hashlib.sha256(repr(SOURCES).encode()).hexdigest()
SCOPE = Applicability(
    ADAPTER,
    None,
    (("adapter", ADAPTER), ("source-config-sha256", SOURCE_CONFIG)),
    frozenset(source.source_id for source in SOURCES),
)


def _one(pattern: str, text: str) -> tuple[str, ...]:
    matches = tuple(re.finditer(pattern, text, re.MULTILINE))
    if len(matches) != 1:
        raise ValueError("source-selector-missing-or-ambiguous")
    return matches[0].groups()


def _number(value: object) -> Decimal:
    if type(value) is not int and not isinstance(value, Decimal | str):
        raise ValueError("source-number-type")
    try:
        result = Decimal(value)
    except (ValueError, ArithmeticError) as error:
        raise ValueError("source-number") from error
    if not result.is_finite() or result < 0:
        raise ValueError("source-number")
    return result


def _table(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("source-object")
    return cast(dict[str, object], value)


def _text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("source-text")
    return value


def _model(channel: str | None, *, interface_version: str | None = None, requested: str = "glm-5.3-flash") -> Model:
    return Model(
        "zhipuai/glm-5.3-flash",
        "zai",
        requested,
        channel=channel,
        interface_id="chat-completions" if channel == "zai-api" else None,
        interface_provider_id="zai" if channel == "zai-api" else None,
        interface_version=interface_version,
    )


def normalize(captures: tuple[Capture, ...], *, previous: PublicEvidence | None = None) -> PublicEvidence:
    """All eight declared source inputs or no new publication; no authority winner.

    Different unlinked assertions remain independent conflicts. Corrections require
    explicit source evidence/curation, never a latest-retrieval heuristic.
    """
    if len(captures) != len(SOURCES) or {item.source for item in captures} != set(SOURCES):
        raise ValueError("incomplete-or-unexpected-source-generation")
    if previous is not None and previous.applicability != SCOPE:
        raise ValueError("source-adapter-migration-required")
    by_source = {item.source.source_id: item for item in captures}
    observations = {item.observation_id: item for item in (() if previous is None else previous.evidence.observations)}
    claims = {item.claim_id: item for item in (() if previous is None else previous.evidence.claims)}
    revisions = {} if previous is None else dict(previous.revisions)
    uncertain = {item.annotation_id: item for item in (() if previous is None else previous.uncertain_campaigns)}

    def origin(source: str, value: object) -> tuple[str, datetime]:
        capture = by_source[source]
        identity = source + ":" + hashlib.sha256((ADAPTER + repr(value)).encode()).hexdigest()
        if identity not in observations:
            observations[identity] = Observation(
                identity,
                source,
                "secondary" if source in {"catalog", "api", "coding"} else "official",
                "catalog" if source in {"catalog", "api", "coding"} else "documentation",
                capture.source.reference,
                capture.acquired_at,
                "public",
                capture.source.license,
                observed_at=capture.acquired_at,
            )
            revisions[identity] = capture.revision
        # Re-reading identical facts never changes their freshness or first observation.
        return identity, observations[identity].retrieved_at

    def model_fact(source: str, subject: Model, value: Capability | Money | Benchmark | NativeLimit) -> None:
        identity, at = origin(source, (subject, value))
        claims[identity] = ModelClaim(subject, value, claim_id=identity, observation_id=identity, effective_from=at)

    def baseline(source: str, subject: Plan, terms: Terms) -> None:
        identity, at = origin(source, (subject, terms))
        claims[identity] = BaselineClaim(subject, terms, claim_id=identity, observation_id=identity, effective_from=at)

    canonical = _table(tomllib.loads(by_source["catalog"].data.decode(), parse_float=Decimal))
    if canonical.get("name") != "GLM-5.3-Flash":
        raise ValueError("source-model-identity")
    limits = _table(canonical.get("limit"))
    for field, meaning in (
        ("context", "total-context-window"),
        ("input", "input-allowance"),
        ("output", "output-allowance"),
    ):
        if field != "input" and field not in limits:
            raise ValueError("source-required-native-limit")
        model_fact(
            "catalog",
            _model(None),
            NativeLimit(
                "limit." + field,
                meaning,
                None if field not in limits else _number(limits[field]),
                "tokens",
                "models.dev canonical model",
                "advertised" if field in limits else "unknown",
            ),
        )
    benchmarks = canonical.get("benchmarks")
    if not isinstance(benchmarks, list):
        raise ValueError("source-benchmark-shape")
    selected: set[str] = set()
    for raw in cast(list[object], benchmarks):
        row = _table(raw)
        # No AA-derived index/Elo dataset is copied into the selected evidence scope.
        if row.get("name") not in {"Terminal-Bench", "DeepSWE"}:
            continue
        name = _text(row["name"])
        if name in selected:
            raise ValueError("source-duplicate-benchmark")
        selected.add(name)
        model_fact(
            "catalog",
            _model(None),
            Benchmark(
                name,
                _text(row["version"]),
                _text(row["metric"]),
                json.dumps({key: _text(row[key]) for key in ("harness", "variant", "source")}, sort_keys=True),
                _number(row["score"]),
                "unreported",
            ),
        )
    if selected != {"Terminal-Bench", "DeepSWE"}:
        raise ValueError("source-required-benchmark")

    for source, channel in (("api", "zai-api"), ("coding", "zai-coding-plan")):
        offering = _table(tomllib.loads(by_source[source].data.decode(), parse_float=Decimal))
        if offering.get("base_model") != "zhipuai/glm-5.3-flash":
            raise ValueError("source-base-model-mismatch")
        costs = _table(offering.get("cost"))
        model_fact(source, _model(channel), Capability("catalog-base-reference:zhipuai/glm-5.3-flash", True))
        options = offering.get("reasoning_options")
        if not isinstance(options, list):
            raise ValueError("source-effort-schema")
        raw_options = cast(list[object], options)
        if len(raw_options) != 1:
            raise ValueError("source-effort-schema")
        option = _table(raw_options[0])
        choices = option.get("values")
        if option.get("type") != "effort" or not isinstance(choices, list) or not choices:
            raise ValueError("source-effort-schema")
        efforts = tuple(_text(value) for value in cast(list[object], choices))
        if len(set(efforts)) != len(efforts):
            raise ValueError("source-duplicate-effort")
        for effort in efforts:
            model_fact(source, _model(channel), Capability("source-available-reasoning-effort:" + effort, True))
        for key in ("input", "output", "cache_read", "cache_write"):
            if key not in costs:
                raise ValueError("source-required-price")
            model_fact(
                source,
                _model(channel),
                Money(
                    _number(costs[key]),
                    "USD",
                    ("incremental-token-price/included-plan-credits/" if source == "coding" else "API-price/")
                    + key
                    + "/1000000-tokens",
                ),
            )

    prices = by_source["prices"].data.decode()
    if "All prices are in USD." not in prices or "Prices per 1M tokens." not in prices:
        raise ValueError("source-price-unit-or-basis")
    amount_in, amount_cached, storage, amount_out = _one(
        r"^\| GLM-5\.3-Flash \| \\\$(\d+(?:\.\d+)?) \| \\\$(\d+(?:\.\d+)?) \| ([^|]+) \| \\\$(\d+(?:\.\d+)?) \|$",
        prices,
    )
    for key, amount in (("input", amount_in), ("cache_read", amount_cached), ("output", amount_out)):
        model_fact("prices", _model("zai-api"), Money(_number(amount), "USD", "API-price/" + key + "/1000000-tokens"))
    if storage.strip() != "Limited-time Free":
        raise ValueError("source-storage-promotion-change")
    identity, at = origin("prices", ("storage-free", storage.strip()))
    uncertain[identity] = UncertainCampaign(
        identity,
        identity,
        Plan("api-cache-storage", "zai", "public-unspecified"),
        "storage-limited-free",
        Terms(rules=("advertised-temporary-free", "billing-unit:unreported")),
        at,
        None,
        None,
    )

    interface = by_source["interface"].data.decode()
    (version,) = _one(r"^  version: ([\w.]+)$", interface)
    segment = _one(r"(?s)    ChatCompletionVisionRequest:(.*?)\n    \w", interface)[0]
    lower, upper = _one(r"(?s)        max_tokens:.*?\n          minimum: (\d+)\n          maximum: (\d+)", segment)
    if "- glm-5.3-flash\n" not in segment or "type: integer" not in segment:
        raise ValueError("source-interface-subject")
    subject = _model("zai-api", interface_version=version)
    model_fact(
        "interface",
        subject,
        NativeLimit(
            "max_tokens",
            "request-parameter-maximum",
            _number(upper),
            "tokens",
            "ChatCompletionVisionRequest; minimum=" + lower,
            "advertised",
        ),
    )
    identity, at = origin("interface", (subject, "advertised-model-selection"))
    claims[identity] = SurfaceClaim(
        Surface("zai-chat-completions", "zai", version),
        SurfaceEvidence("model-selection", advertised=True),
        claim_id=identity,
        observation_id=identity,
        effective_from=at,
    )

    plans = by_source["plans"].data.decode()
    if "requests for GLM-4.7 will automatically be routed to GLM-5.3-Flash" not in plans:
        raise ValueError("source-plan-alias-schema")
    model_fact(
        "plans",
        _model("zai-coding-plan", requested="glm-4.7"),
        Capability("source-advertised-alias-target:glm-5.3-flash", True),
    )
    (amount,) = _one(r"Starting at just (\d+(?:\.\d+)?) USD per month", plans)
    baseline(
        "plans",
        Plan("coding-plan-starting-offer", "zai", "public-unspecified"),
        Terms(price=Money(_number(amount), "USD", "advertised-starting-monthly-subscription")),
    )
    five_hour, weekly = _one(r"^\| Lite \| ([\d,]+) \| ([\d,]+) \|$", plans)
    cohort = by_source["cohort"].data.decode()
    (publication_date,) = _one(r"Publication date: ([A-Za-z]+ \d+, \d{4})", cohort)
    if (
        publication_date != "July 30, 2026"
        or "UTC+8" not in cohort
        or "Plans are not switched automatically" not in cohort
    ):
        raise ValueError("source-cohort-schema")
    cohort_identity, _ = origin("cohort", ("credit-cohort", "2026-07-30", "UTC+8"))
    baseline(
        "plans",
        Plan("coding-lite", "zai", "credits-2026-07-30"),
        Terms(
            quota=Quota(_number(five_hour.replace(",", "")), "credits", "5h-after-consumption"),
            rules=(
                "weekly-ceiling:" + weekly.replace(",", "") + "credits/7d-from-subscription",
                "cohort-source:" + cohort_identity,
                "not-automatic-migration-of-existing-plans",
            ),
        ),
    )

    campaign = by_source["campaign"].data.decode()
    start, end = _one(r"Campaign period: ([A-Za-z]+ \d+, \d{4}) to ([A-Za-z]+ \d+, \d{4})", campaign)
    required = ("23:00 to 09:00", "UTC+8", "paid plan users", "Zero quota consumption", "doubled", "3.10")
    if any(value not in campaign for value in required):
        raise ValueError("source-campaign-schema")
    identity, at = origin("campaign", (start, end, required))
    uncertain[identity] = UncertainCampaign(
        identity,
        identity,
        Plan("coding-plan-campaign", "zai", "public-paid"),
        "glm-flash-usage",
        Terms(
            rules=(
                "advertised-calendar-start:" + start,
                "advertised-calendar-end:" + end,
                "exact-terminal-instant:unknown",
                "zcode/autoclaw:reported-zero-consumption",
                "other-agents:reported-double-quota",
                "exhausted-5h/week-restriction:source-reported",
                "no-private-balance-or-entitlement",
            )
        ),
        at,
        None,
        None,
        frozenset({"paid-plan", "glm-5.3-flash", "zcode>=3.10-for-zcode-lane"}),
        DailyWindow("Asia/Singapore", time(23), time(9)),
    )
    return PublicEvidence(
        SCOPE,
        Evidence(tuple(observations.values()), tuple(claims.values())),
        tuple(revisions.items()),
        () if previous is None else previous.notices,
        tuple(uncertain.values()),
    )


@dataclass(frozen=True)
class RefreshResult:
    reference: CutReference | None
    succeeded: bool
    diagnostic: str | None
    attempted_at: datetime
    sources: tuple[SourceHealth, ...]


@dataclass(frozen=True)
class SourceHealth:
    source_id: str
    reference: str
    retrieved: bool
    revision: str | None
    bytes_received: int | None
    diagnostic: str | None


def refresh(directory: Path, *, at: datetime, max_artifact_bytes: int, timeout: float) -> RefreshResult:
    old = retained(directory, max_bytes=max_artifact_bytes)
    captures: list[Capture] = []
    health: list[SourceHealth] = []
    for source in SOURCES:
        try:
            capture = fetch(source, at=at, timeout=timeout)
            captures.append(capture)
            health.append(
                SourceHealth(source.source_id, source.reference, True, capture.revision, len(capture.data), None)
            )
        except (ValueError, OSError):
            health.append(
                SourceHealth(source.source_id, source.reference, False, None, None, "source-retrieval-failed")
            )
    succeeded, diagnostic = False, None
    try:
        cut = normalize(tuple(captures), previous=None if old is None else old[2])
        _ = publish(directory, cut, expected=SCOPE, produced_at=at, max_bytes=max_artifact_bytes)
        succeeded = True
    except (ValueError, OSError, KeyError, TypeError):
        diagnostic = "source-generation-not-activated"
    # Re-read the actual pointer even after an uncertain post-rename durability error.
    active = retained(directory, max_bytes=max_artifact_bytes)
    reference = None if active is None else active[1]
    if not succeeded and reference is not None and (old is None or reference != old[1]):
        diagnostic = "complete-activation-durability-unconfirmed"
    status = {
        "schema": "mi.source-refresh-working/1",
        "adapter": ADAPTER,
        "attempted_at": at.isoformat(),
        "succeeded": succeeded,
        "diagnostic": diagnostic,
        "active": None if reference is None else reference.sha256,
        "last_successful_publication_at": None
        if active is None
        else decode_cut(
            active[0],
            active[1],
            supported_payload_schemas=frozenset({active[1].payload_schema}),
            max_bytes=max_artifact_bytes,
        ).produced_at.isoformat(),
        "freshness_policy": "consumer-owned; publication/retrieval does not renew observations",
        "remediation": None
        if succeeded
        else (
            "Inspect named source URL, byte bound, encoding and adapter schema; "
            "retry complete generation, do not shrink scope or erase history"
        ),
        "sources": [
            {
                "source_id": item.source_id,
                "reference": item.reference,
                "retrieved": item.retrieved,
                "revision": item.revision,
                "bytes_received": item.bytes_received,
                "diagnostic": item.diagnostic,
            }
            for item in health
        ],
    }
    record_refresh_status(directory, json.dumps(status, sort_keys=True, separators=(",", ":")).encode())
    return RefreshResult(reference, succeeded, diagnostic, at, tuple(health))
