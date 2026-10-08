"""Selected upstream-backed GLM Flash facts and original public-offer annotations.

No linked examples, weights, indexes or billing/account endpoints are followed.
"""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from dataclasses import dataclass, replace
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


class SourceFailure(ValueError):
    def __init__(self, source_id: str, code: str) -> None:
        self.source_id = source_id
        self.code = code
        super().__init__(code)


RETRIEVAL_REMEDIATION = {
    "source-retrieval-failed": "Check public connectivity/status; retry the same complete source generation.",
    "source-redirect-rejected": "Inspect URL relocation; never follow or widen origins automatically.",
    "source-compressed-response": "Require identity encoding; never decode unbounded compression.",
    "source-partial-or-unexpected-response": "Require a complete 200 reply at the declared URL.",
    "source-incomplete-response": "Compare response framing/length; discard partial bytes and retry complete capture.",
    "source-http-protocol-failed": "Inspect HTTP framing/status; discard and retry complete capture.",
    "source-size-policy": "Inspect measured size/config changes; review bounds, never truncate evidence.",
    "source-encoding": "Inspect source UTF-8 format; discard malformed text without guessing another encoding.",
    "invalid-source-timeout": "Supply a finite positive retrieval timeout before retry.",
}
NORMALIZATION_CODES = frozenset(
    {
        "source-selector-missing-or-ambiguous",
        "source-number-type",
        "source-number",
        "source-object",
        "source-text",
        "source-toml-schema",
        "source-model-identity",
        "source-required-native-limit",
        "source-benchmark-shape",
        "source-duplicate-benchmark",
        "source-required-benchmark",
        "source-base-model-mismatch",
        "source-effort-schema",
        "source-duplicate-effort",
        "source-required-price",
        "source-price-unit-or-basis",
        "source-storage-promotion-change",
        "source-interface-subject",
        "source-plan-alias-schema",
        "source-plan-unit-reset-schema",
        "source-cohort-schema",
        "source-campaign-schema",
        "source-campaign-lane-or-eligibility",
        "source-table-row-missing-or-ambiguous",
        "source-table-columns-or-framing",
    }
)


def _one(pattern: str, text: str, source: str) -> tuple[str, ...]:
    matches = tuple(re.finditer(pattern, text, re.MULTILINE))
    if len(matches) != 1:
        raise SourceFailure(source, "source-selector-missing-or-ambiguous")
    return matches[0].groups()


def _row(text: str, first: str, columns: tuple[str, ...], source: str) -> tuple[str, ...]:
    """Only the selected row's contiguous Markdown table defines its columns."""
    tables: list[list[tuple[str, ...]]] = []
    current: list[tuple[str, ...]] = []
    for line in (*text.splitlines(), ""):
        line = line.strip()
        if line.startswith("|") and line.endswith("|"):
            current.append(tuple(cell.strip() for cell in line[1:-1].split("|")))
        elif current:
            tables.append(current)
            current = []
    matches = [(table, index, row) for table in tables for index, row in enumerate(table) if row and row[0] == first]
    if len(matches) != 1:
        raise SourceFailure(source, "source-table-row-missing-or-ambiguous")
    table, index, row = matches[0]
    if (
        index < 2
        or table[0] != columns
        or len(row) != len(columns)
        or len(table[1]) != len(columns)
        or any(re.fullmatch(r":?-+:?", cell) is None for cell in table[1])
    ):
        raise SourceFailure(source, "source-table-columns-or-framing")
    return row


def _number(value: object, source: str) -> Decimal:
    if type(value) is not int and not isinstance(value, Decimal | str):
        raise SourceFailure(source, "source-number-type")
    try:
        result = Decimal(value)
    except (ValueError, ArithmeticError) as error:
        raise SourceFailure(source, "source-number") from error
    if not result.is_finite() or result < 0:
        raise SourceFailure(source, "source-number")
    return result


def _table(value: object, source: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise SourceFailure(source, "source-object")
    return cast(dict[str, object], value)


def _text(value: object, source: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourceFailure(source, "source-text")
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
        # Decimal equality is exact and context-independent; repr is not semantic identity.
        if any(
            isinstance(row, ModelClaim)
            and row.subject == subject
            and row.payload == value
            and observations[row.observation_id].source_id == source
            for row in claims.values()
        ):
            return
        identity, at = origin(source, (subject, value))
        claims[identity] = ModelClaim(subject, value, claim_id=identity, observation_id=identity, effective_from=at)

    def baseline(source: str, subject: Plan, terms: Terms) -> None:
        if any(
            isinstance(row, BaselineClaim)
            and row.subject == subject
            and row.terms == terms
            and observations[row.observation_id].source_id == source
            for row in claims.values()
        ):
            return
        identity, at = origin(source, (subject, terms))
        claims[identity] = BaselineClaim(subject, terms, claim_id=identity, observation_id=identity, effective_from=at)

    def toml(source: str) -> dict[str, object]:
        try:
            return _table(tomllib.loads(by_source[source].data.decode(), parse_float=Decimal), source)
        except (ValueError, TypeError) as error:
            if isinstance(error, SourceFailure):
                raise
            raise SourceFailure(source, "source-toml-schema") from error

    canonical = toml("catalog")
    if canonical.get("name") != "GLM-5.3-Flash":
        raise SourceFailure("catalog", "source-model-identity")
    limits = _table(canonical.get("limit"), "catalog")
    for field, meaning in (
        ("context", "total-context-window"),
        ("input", "input-allowance"),
        ("output", "output-allowance"),
    ):
        if field != "input" and field not in limits:
            raise SourceFailure("catalog", "source-required-native-limit")
        model_fact(
            "catalog",
            _model(None),
            NativeLimit(
                "limit." + field,
                meaning,
                None if field not in limits else _number(limits[field], "catalog"),
                "tokens",
                "models.dev canonical model",
                "advertised" if field in limits else "unknown",
            ),
        )
    benchmarks = canonical.get("benchmarks")
    if not isinstance(benchmarks, list):
        raise SourceFailure("catalog", "source-benchmark-shape")
    selected: set[str] = set()
    for raw in cast(list[object], benchmarks):
        row = _table(raw, "catalog")
        # No AA-derived index/Elo dataset is copied into the selected evidence scope.
        name = _text(row.get("name"), "catalog")
        if name not in {"Terminal-Bench", "DeepSWE"}:
            continue
        if name in selected:
            raise SourceFailure("catalog", "source-duplicate-benchmark")
        selected.add(name)
        model_fact(
            "catalog",
            _model(None),
            Benchmark(
                name,
                _text(row.get("version"), "catalog"),
                _text(row.get("metric"), "catalog"),
                json.dumps(
                    {key: _text(row.get(key), "catalog") for key in ("harness", "variant", "source")}, sort_keys=True
                ),
                _number(row.get("score"), "catalog"),
                "unreported",
            ),
        )
    if selected != {"Terminal-Bench", "DeepSWE"}:
        raise SourceFailure("catalog", "source-required-benchmark")

    for source, channel in (("api", "zai-api"), ("coding", "zai-coding-plan")):
        offering = toml(source)
        if offering.get("base_model") != "zhipuai/glm-5.3-flash":
            raise SourceFailure(source, "source-base-model-mismatch")
        costs = _table(offering.get("cost"), source)
        model_fact(source, _model(channel), Capability("catalog-base-reference:zhipuai/glm-5.3-flash", True))
        options = offering.get("reasoning_options")
        if not isinstance(options, list):
            raise SourceFailure(source, "source-effort-schema")
        raw_options = cast(list[object], options)
        if len(raw_options) != 1:
            raise SourceFailure(source, "source-effort-schema")
        option = _table(raw_options[0], source)
        choices = option.get("values")
        if option.get("type") != "effort" or not isinstance(choices, list) or not choices:
            raise SourceFailure(source, "source-effort-schema")
        efforts = tuple(_text(value, source) for value in cast(list[object], choices))
        if len(set(efforts)) != len(efforts):
            raise SourceFailure(source, "source-duplicate-effort")
        for effort in efforts:
            model_fact(source, _model(channel), Capability("source-available-reasoning-effort:" + effort, True))
        for key in ("input", "output", "cache_read", "cache_write"):
            if key not in costs:
                raise SourceFailure(source, "source-required-price")
            model_fact(
                source,
                _model(channel),
                Money(
                    _number(costs[key], source),
                    "USD",
                    ("incremental-token-price/included-plan-credits/" if source == "coding" else "API-price/")
                    + key
                    + "/1000000-tokens",
                ),
            )

    prices = by_source["prices"].data.decode()
    prologue = _one(r"(?ms)^# Pricing\n(.*?)(?=^## |\Z)", prices, "prices")[0]
    section = _one(r"(?ms)^### Latest Models\n(.*?)(?=^#{1,3} |\Z)", prices, "prices")[0]
    unit_basis = _one(r"^Prices per ([^\n]+) tokens\.$", section, "prices")[0]
    if "All prices are in USD." not in prologue or unit_basis != "1M":
        raise SourceFailure("prices", "source-price-unit-or-basis")
    _, raw_in, raw_cached, storage, raw_out = _row(
        section, "GLM-5.3-Flash", ("Model", "Input", "Cached Input", "Cached Input Storage", "Output"), "prices"
    )
    amount_in = _one(r"^\\\$(\d+(?:\.\d+)?)$", raw_in, "prices")[0]
    amount_cached = _one(r"^\\\$(\d+(?:\.\d+)?)$", raw_cached, "prices")[0]
    amount_out = _one(r"^\\\$(\d+(?:\.\d+)?)$", raw_out, "prices")[0]
    for key, amount in (("input", amount_in), ("cache_read", amount_cached), ("output", amount_out)):
        model_fact(
            "prices", _model("zai-api"), Money(_number(amount, "prices"), "USD", "API-price/" + key + "/1000000-tokens")
        )
    if storage.strip() != "Limited-time Free":
        raise SourceFailure("prices", "source-storage-promotion-change")
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
    interface = _one(r"(?ms)^````yaml POST /paas/v4/chat/completions\n(.*?)^````$", interface, "interface")[0]
    _ = _one(r"^openapi: 3\.0\.1$", interface, "interface")
    info = _one(r"(?ms)^info:\n(.*?)(?=^\w|\Z)", interface, "interface")[0]
    (version,) = _one(r"^  version: ([\w.]+)$", info, "interface")
    servers = _one(r"(?ms)^servers:\n(.*?)(?=^\w|\Z)", interface, "interface")[0]
    _ = _one(r"^  - url: https://api\.z\.ai/api$", servers, "interface")
    paths = _one(r"(?ms)^paths:\n(.*?)(?=^\w|\Z)", interface, "interface")[0]
    path = _one(r"(?ms)^  /paas/v4/chat/completions:\n(.*?)(?=^  \S|\Z)", paths, "interface")[0]
    operation = _one(r"(?ms)^    post:\n(.*?)(?=^    \w|\Z)", path, "interface")[0]
    body = _one(r"(?ms)^      requestBody:\n(.*?)(?=^      \w|\Z)", operation, "interface")[0]
    content = _one(r"(?ms)^        content:\n(.*?)(?=^        \w|\Z)", body, "interface")[0]
    media = _one(r"(?ms)^          application/json:\n(.*?)(?=^          \S|\Z)", content, "interface")[0]
    schema = _one(r"(?ms)^            schema:\n(.*?)(?=^            \w|\Z)", media, "interface")[0]
    variants = _one(r"(?ms)^              oneOf:\n(.*?)(?=^              \w|\Z)", schema, "interface")[0]
    _ = _one(r"^                - \$ref: '#/components/schemas/ChatCompletionVisionRequest'$", variants, "interface")
    components = _one(r"(?ms)^components:\n(.*?)(?=^\w|\Z)", interface, "interface")[0]
    schemas = _one(r"(?ms)^  schemas:\n(.*?)(?=^  \w|\Z)", components, "interface")[0]
    segment = _one(r"(?ms)^    ChatCompletionVisionRequest:\n(.*?)(?=^    \w|\Z)", schemas, "interface")[0]
    properties = _one(r"(?ms)^      properties:\n(.*?)(?=^      \w|\Z)", segment, "interface")[0]
    model_property = _one(r"(?ms)^        model:\n(.*?)(?=^        \w|\Z)", properties, "interface")[0]
    model_enum = _one(r"(?ms)^          enum:\n(.*?)(?=^          \w|\Z)", model_property, "interface")[0]
    token_property = _one(r"(?ms)^        max_tokens:\n(.*?)(?=^        \w|\Z)", properties, "interface")[0]
    (lower,) = _one(r"^          minimum: (\d+)$", token_property, "interface")
    (upper,) = _one(r"^          maximum: (\d+)$", token_property, "interface")
    if (
        "            - glm-5.3-flash\n" not in model_enum
        or "          type: string\n" not in model_property
        or "          type: integer\n" not in token_property
        or "The maximum number of tokens for model output." not in token_property
    ):
        raise SourceFailure("interface", "source-interface-subject")
    subject = _model("zai-api", interface_version=version)
    model_fact(
        "interface",
        subject,
        NativeLimit(
            "max_tokens",
            "request-parameter-maximum",
            _number(upper, "interface"),
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
        raise SourceFailure("plans", "source-plan-alias-schema")
    model_fact(
        "plans",
        _model("zai-coding-plan", requested="glm-4.7"),
        Capability("source-advertised-alias-target:glm-5.3-flash", True),
    )
    (amount,) = _one(r"Starting at just (\d+(?:\.\d+)?) USD per month", plans, "plans")
    baseline(
        "plans",
        Plan("coding-plan-starting-offer", "zai", "public-unspecified"),
        Terms(price=Money(_number(amount, "plans"), "USD", "advertised-starting-monthly-subscription")),
    )
    plan_plain = plans.replace("*", "").replace("`", "")
    plan_features = _one(r"(?ms)^#### Usage Credit Allowance\n(.*?)(?=^#{1,4} |\Z)", plan_plain, "plans")[0]
    _, five_hour, weekly = _row(plan_features, "Lite", ("Plan Type", "5-Hour Credits", "Weekly Credits"), "plans")
    for value in (five_hour, weekly):
        if re.fullmatch(r"\d+(?:,\d{3})*", value) is None:
            raise SourceFailure("plans", "source-number")
    (five_reset,) = _one(
        r"5-hour credits:[ \t]*Dynamically refreshed; credit quota resets (\d+) hours after consumption\.",
        plan_features,
        "plans",
    )
    (week_reset,) = _one(
        r"Weekly credits:[ \t]*Activated upon subscription; resets every (\d+) days\.", plan_features, "plans"
    )
    if five_reset != "5" or week_reset != "7":
        raise SourceFailure("plans", "source-plan-unit-reset-schema")
    cohort = by_source["cohort"].data.decode()
    (publication_date,) = _one(r"Publication date: ([A-Za-z]+ \d+, \d{4})", cohort, "cohort")
    if (
        publication_date != "July 30, 2026"
        or "UTC+8" not in cohort
        or "Plans are not switched automatically" not in cohort
    ):
        raise SourceFailure("cohort", "source-cohort-schema")
    cohort_identity, _ = origin("cohort", ("credit-cohort", "2026-07-30", "UTC+8"))
    baseline(
        "plans",
        Plan("coding-lite", "zai", "credits-2026-07-30"),
        Terms(
            quota=Quota(_number(five_hour.replace(",", ""), "plans"), "credits", "5h-after-consumption"),
            rules=(
                "weekly-ceiling:" + weekly.replace(",", "") + "credits/7d-from-subscription",
                "cohort-source:" + cohort_identity,
                "not-automatic-migration-of-existing-plans",
            ),
        ),
    )

    campaign = by_source["campaign"].data.decode()
    start, end = _one(r"Campaign period: ([A-Za-z]+ \d+, \d{4}) to ([A-Za-z]+ \d+, \d{4})", campaign, "campaign")
    required = ("23:00 to 09:00", "UTC+8", "paid plan users", "Zero quota consumption", "doubled", "3.10")
    if any(value not in campaign for value in required):
        raise SourceFailure("campaign", "source-campaign-schema")
    campaign_plain = campaign.replace("*", "").replace("`", "")
    _ = _one(r"^\|[ \t]*Usage Method[ \t]*\|[ \t]*Quota Consumption Rule[ \t]*\|$", campaign_plain, "campaign")
    _ = _one(
        r"^\|[ \t]*Use via \[ZCode\]\([^\n)]+\)\u3001\[AutoClaw\]\([^\n)]+\)[ \t]*\|"
        r"[ \t]*Zero quota consumption for unlimited usage[ \t]*\|$",
        campaign_plain,
        "campaign",
    )
    _ = _one(
        r"^\|[ \t]*Use via other supported Agents[ \t]*\|"
        r"[ \t]*Available quota is doubled based on your plan.s standard quota rules[ \t]*\|$",
        campaign_plain,
        "campaign",
    )
    qualified = " ".join(campaign_plain.split())
    for pattern in (
        r"(?i)campaign is available to all paid plan users",
        r"usage of GLM-5\.3-Flash through GLM Coding Plan",
        r"every day from 23:00 to 09:00 the following day",
        r"(?i)campaign applies only to GLM-5\.3-Flash",
        r"reached the 5 hours/week quota limit,[^.]*temporarily be unable to participate",
        r"(?i)campaign takes effect only in ZCode version 3\.10 and later",
    ):
        _ = _one(pattern, qualified, "campaign")
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
                "source-stated-ZCode-version:3.10-and-later; other-lane-version-applicability-unconfirmed",
                "no-private-balance-or-entitlement",
            )
        ),
        at,
        None,
        None,
        frozenset({"paid-plan", "glm-5.3-flash", "source-stated-ZCode-version>=3.10"}),
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
        except (ValueError, OSError) as error:
            code = error.args[0] if error.args else None
            diagnostic = code if isinstance(code, str) and code in RETRIEVAL_REMEDIATION else "source-retrieval-failed"
            health.append(SourceHealth(source.source_id, source.reference, False, None, None, diagnostic))
    succeeded, diagnostic, phase = False, None, "normalization"
    cut: PublicEvidence | None = None
    try:
        cut = normalize(tuple(captures), previous=None if old is None else old[2])
    except SourceFailure as error:
        diagnostic = error.code if error.code in NORMALIZATION_CODES else "source-schema-rejected"
        health = [
            replace(item, diagnostic=diagnostic) if item.source_id == error.source_id else item for item in health
        ]
    except (ValueError, KeyError, TypeError):
        diagnostic = "source-generation-or-config-rejected"
        phase = "retrieval" if len(captures) != len(SOURCES) else "normalization"
    if cut is not None:
        phase = "publication"
        try:
            _ = publish(directory, cut, expected=SCOPE, produced_at=at, max_bytes=max_artifact_bytes)
            succeeded, phase = True, "complete"
        except ValueError:
            diagnostic = "publication-scope-history-or-size-rejected"
        except OSError:
            diagnostic = "publication-storage-failed"
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
        "phase": phase,
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
                "remediation": None
                if item.diagnostic is None
                else RETRIEVAL_REMEDIATION.get(
                    item.diagnostic,
                    "Inspect this source's schema/units/identity/conditions and adapter version; "
                    "reject changed semantics until reviewed.",
                ),
            }
            for item in health
        ],
    }
    record_refresh_status(directory, json.dumps(status, sort_keys=True, separators=(",", ":")).encode())
    return RefreshResult(reference, succeeded, diagnostic, at, tuple(health))
