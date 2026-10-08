"""Explicit public evidence and knowledge lineage, independent of effective projection."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime, time
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo


def instant(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("time must be timezone-aware")
    return value.astimezone(UTC)


def _nonempty(*values: str) -> None:
    if any(not value.strip() for value in values):
        raise ValueError("identity, reference and units must be nonempty")


@dataclass(frozen=True)
class Observation:
    observation_id: str
    source_id: str
    authority: Literal["official", "secondary", "community"]
    source_type: Literal["documentation", "catalog", "measurement"]
    reference: str
    retrieved_at: datetime
    distribution: Literal["public", "restricted", "unknown"]
    license: str
    observed_at: datetime | None = None
    published_at: datetime | None = None
    fresh_until: datetime | None = None

    def __post_init__(self) -> None:
        _nonempty(self.observation_id, self.source_id, self.reference, self.license)
        for name in ("retrieved_at", "observed_at", "published_at", "fresh_until"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, instant(value))

    def stale(self, at: datetime) -> bool:
        return self.fresh_until is not None and instant(at) >= self.fresh_until


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str
    unit: str

    def __post_init__(self) -> None:
        _nonempty(self.currency, self.unit)
        if not self.amount.is_finite() or self.amount < 0:
            raise ValueError("price must be finite and nonnegative")


@dataclass(frozen=True)
class Quota:
    amount: Decimal
    unit: str
    period: str

    def __post_init__(self) -> None:
        _nonempty(self.unit, self.period)
        if not self.amount.is_finite() or self.amount < 0:
            raise ValueError("quota must be finite and nonnegative")


@dataclass(frozen=True)
class Model:
    model_id: str
    provider_id: str
    provider_model_id: str
    physical_model_id: str | None = None
    revision: str | None = None
    channel: str | None = None
    interface_id: str | None = None
    interface_provider_id: str | None = None
    interface_version: str | None = None
    configuration: tuple[tuple[str, str | None], ...] | None = None

    def __post_init__(self) -> None:
        _nonempty(self.model_id, self.provider_id, self.provider_model_id)
        for value in (
            self.physical_model_id,
            self.revision,
            self.channel,
            self.interface_id,
            self.interface_provider_id,
            self.interface_version,
        ):
            if value is not None:
                _nonempty(value)
        if self.configuration is not None:
            names: set[str] = set()
            for name, value in self.configuration:
                _nonempty(name)
                if name in names:
                    raise ValueError("duplicate-configuration")
                names.add(name)
                if value is not None:
                    _nonempty(value)
            object.__setattr__(self, "configuration", tuple(sorted(self.configuration)))


@dataclass(frozen=True)
class Plan:
    plan_id: str
    provider_id: str
    generation: str

    def __post_init__(self) -> None:
        _nonempty(self.plan_id, self.provider_id, self.generation)


@dataclass(frozen=True)
class Surface:
    surface_id: str
    provider_id: str
    version: str

    def __post_init__(self) -> None:
        _nonempty(self.surface_id, self.provider_id, self.version)


@dataclass(frozen=True)
class Capability:
    name: str
    supported: bool | None

    def __post_init__(self) -> None:
        _nonempty(self.name)


@dataclass(frozen=True)
class Benchmark:
    name: str
    version: str
    methodology: str
    configuration: str
    value: Decimal
    unit: str

    def __post_init__(self) -> None:
        _nonempty(self.name, self.version, self.methodology, self.configuration, self.unit)
        if not self.value.is_finite():
            raise ValueError("benchmark must be finite")


@dataclass(frozen=True)
class NativeLimit:
    """Attributed native assertion, never a consumer hard property or conversion."""

    dimension: str
    meaning: str
    amount: Decimal | None
    unit: str | None
    basis: str | None
    assertion: Literal["advertised", "source-observed", "source-supported", "unknown"]

    def __post_init__(self) -> None:
        _nonempty(self.dimension, self.meaning)
        for value in (self.unit, self.basis):
            if value is not None:
                _nonempty(value)
        if self.amount is not None and (
            type(self.amount) is not Decimal or not self.amount.is_finite() or self.amount < 0
        ):
            raise ValueError("native limit must be an exact finite nonnegative decimal or unknown")
        if self.assertion not in {"advertised", "source-observed", "source-supported", "unknown"}:
            raise ValueError("native assertion strength")


@dataclass(frozen=True)
class SurfaceEvidence:
    capability: Literal[
        "headless",
        "structured-output",
        "workspace-editing",
        "model-selection",
        "physical-model-observability",
        "physical-model-enforceability",
    ]
    advertised: bool | None = None
    observed: bool | None = None
    selectable: bool | None = None
    enforceable: bool | None = None
    physical_model_id: str | None = None


@dataclass(frozen=True)
class Terms:
    """Unknown baseline fields; omitted (inherited) override fields."""

    price: Money | None = None
    quota: Quota | None = None
    available: bool | None = None
    rules: tuple[str, ...] | None = None


@dataclass(frozen=True)
class Period:
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "start", instant(self.start))
        object.__setattr__(self, "end", instant(self.end))
        if self.end <= self.start:
            raise ValueError("period end must follow start")

    def contains(self, at: datetime) -> bool:
        return self.start <= instant(at) < self.end


@dataclass(frozen=True)
class DailyWindow:
    timezone: str
    start: time
    end: time

    def __post_init__(self) -> None:
        _ = ZoneInfo(self.timezone)
        if self.start.tzinfo is not None or self.end.tzinfo is not None or self.start == self.end:
            raise ValueError("distinct naive local wall times required")

    def contains(self, at: datetime) -> bool:
        wall = instant(at).astimezone(ZoneInfo(self.timezone)).time()
        return self.start <= wall < self.end if self.start < self.end else wall >= self.start or wall < self.end


@dataclass(frozen=True, kw_only=True)
class Claim:
    claim_id: str
    observation_id: str
    effective_from: datetime
    revises: str | None = None

    def __post_init__(self) -> None:
        _nonempty(self.claim_id, self.observation_id)
        object.__setattr__(self, "effective_from", instant(self.effective_from))
        if self.revises is not None:
            _nonempty(self.revises)
        if self.revises == self.claim_id:
            raise ValueError("self revision")


@dataclass(frozen=True)
class ModelClaim(Claim):
    subject: Model
    payload: Capability | Benchmark | Money | NativeLimit


@dataclass(frozen=True)
class BaselineClaim(Claim):
    """Durable normal terms, never a bounded promotion."""

    subject: Plan
    terms: Terms


@dataclass(frozen=True)
class OverrideClaim(Claim):
    """effective_from versions the campaign; period bounds its active terms.

    A withdrawal has no terms/period and takes effect at its explicit version boundary.
    Once a revision takes effect, its predecessor never returns after campaign expiry.
    """

    subject: Plan
    campaign_id: str
    terms: Terms | None
    period: Period | None
    conditions: frozenset[str] = frozenset()
    window: DailyWindow | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        _nonempty(self.campaign_id, *self.conditions)
        if self.terms is None:
            if self.revises is None or self.period is not None or self.conditions or self.window is not None:
                raise ValueError("withdrawal needs explicit revision and no active terms")
        elif self.terms == Terms() or self.period is None:
            raise ValueError("temporary override needs declared fields and bounded period")

    def active(self, at: datetime, conditions: frozenset[str]) -> bool:
        return (
            self.effective_from <= instant(at)
            and self.terms is not None
            and self.period is not None
            and self.period.contains(at)
            and self.conditions <= conditions
            and (self.window is None or self.window.contains(at))
        )


@dataclass(frozen=True)
class SurfaceClaim(Claim):
    subject: Surface
    payload: SurfaceEvidence


type EvidenceClaim = ModelClaim | BaselineClaim | OverrideClaim | SurfaceClaim


def dimension(claim: EvidenceClaim) -> tuple[str, ...]:
    """Typed comparability only; never infers identity, lineage or authority."""
    if isinstance(claim, BaselineClaim | OverrideClaim):
        prefix = ("offer", claim.subject.plan_id, claim.subject.provider_id, claim.subject.generation)
        return (*prefix, "override", claim.campaign_id) if isinstance(claim, OverrideClaim) else (*prefix, "baseline")
    if isinstance(claim, SurfaceClaim):
        return (
            "surface",
            claim.subject.surface_id,
            claim.subject.provider_id,
            claim.subject.version,
            claim.payload.capability,
        )
    prefix = ("model", claim.subject.model_id, claim.subject.provider_id, claim.subject.provider_model_id)
    context = (
        claim.subject.physical_model_id,
        claim.subject.revision,
        claim.subject.channel,
        claim.subject.interface_id,
        claim.subject.interface_provider_id,
        claim.subject.interface_version,
        claim.subject.configuration,
    )
    if any(value is not None for value in context):
        # Null, omitted configuration and literal strings remain different keys.
        prefix = (*prefix, "applicability", json.dumps(context, separators=(",", ":")))
    match claim.payload:
        case Capability(name=name):
            return (*prefix, "capability", name)
        case Money(currency=currency, unit=unit):
            return (*prefix, "price", currency, unit)
        case Benchmark() as benchmark:
            return (
                *prefix,
                "benchmark",
                benchmark.name,
                benchmark.version,
                benchmark.methodology,
                benchmark.configuration,
                benchmark.unit,
            )
        case NativeLimit() as limit:
            return (
                *prefix,
                "native-limit",
                limit.dimension,
                limit.meaning,
                json.dumps((limit.unit, limit.basis), separators=(",", ":")),
            )


@dataclass(frozen=True)
class Evidence:
    observations: tuple[Observation, ...] = ()
    claims: tuple[EvidenceClaim, ...] = ()

    def __post_init__(self) -> None:
        observed = {item.observation_id for item in self.observations}
        claims = {item.claim_id: item for item in self.claims}
        if len(observed) != len(self.observations) or len(claims) != len(self.claims):
            raise ValueError("duplicate identity")
        for claim in self.claims:
            if claim.observation_id not in observed:
                raise ValueError("missing observation")
            cursor = claim
            seen = {claim.claim_id}
            while cursor.revises is not None:
                parent = claims.get(cursor.revises)
                if parent is None or type(parent) is not type(cursor) or dimension(parent) != dimension(cursor):
                    raise ValueError("revision must reference comparable retained history")
                if parent.claim_id in seen:
                    raise ValueError("cyclic lineage")
                if cursor.effective_from < parent.effective_from:
                    raise ValueError("revision effective boundary cannot precede its predecessor")
                seen.add(parent.claim_id)
                cursor = parent
        object.__setattr__(self, "observations", tuple(sorted(self.observations, key=lambda item: item.observation_id)))
        object.__setattr__(self, "claims", tuple(sorted(self.claims, key=lambda item: item.claim_id)))

    def extend(self, *, observations: tuple[Observation, ...] = (), claims: tuple[EvidenceClaim, ...] = ()) -> Evidence:
        observed = {item.observation_id: item for item in self.observations}
        known = {item.claim_id: item for item in self.claims}
        for observation in observations:
            previous = observed.get(observation.observation_id)
            if previous is not None and replace(observation, retrieved_at=previous.retrieved_at) != previous:
                raise ValueError("observation semantics cannot be rewritten or freshness renewed")
            observed[observation.observation_id] = observation
        for claim in claims:
            if claim.claim_id in known and known[claim.claim_id] != claim:
                raise ValueError("claim identity cannot be rewritten")
            known[claim.claim_id] = claim
        return Evidence(tuple(observed.values()), tuple(known.values()))


@dataclass(frozen=True)
class KnowledgeView:
    history: tuple[EvidenceClaim, ...]
    latest: tuple[EvidenceClaim, ...]
    future: tuple[EvidenceClaim, ...]
    stale_observations: tuple[Observation, ...]


def knowledge(evidence: Evidence, at: datetime) -> KnowledgeView:
    at = instant(at)
    revised = {claim.revises for claim in evidence.claims}
    return KnowledgeView(
        evidence.claims,
        tuple(claim for claim in evidence.claims if claim.claim_id not in revised),
        tuple(
            claim
            for claim in evidence.claims
            if claim.effective_from > at
            or (isinstance(claim, OverrideClaim) and claim.period is not None and claim.period.start > at)
        ),
        tuple(item for item in evidence.observations if item.stale(at)),
    )
