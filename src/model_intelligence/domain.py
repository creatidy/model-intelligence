"""Small immutable evidence model. Identity and revision links are supplied, never inferred."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, time
from decimal import Decimal
from typing import Literal
from zoneinfo import ZoneInfo


def utc_instant(value: datetime) -> datetime:
    """Validate aware public timestamps and compare their actual instants, including DST folds."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")
    return value.astimezone(UTC)


def _required(*values: str) -> None:
    if any(not value.strip() for value in values):
        raise ValueError("identities, references and units must be nonempty")


@dataclass(frozen=True)
class Period:
    start: datetime
    end: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "start", utc_instant(self.start))
        if self.end is not None:
            object.__setattr__(self, "end", utc_instant(self.end))
            if self.end <= self.start:
                raise ValueError("end must be after start")

    def contains(self, at: datetime) -> bool:
        return self.start <= utc_instant(at) and (self.end is None or utc_instant(at) < self.end)


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
        _required(self.observation_id, self.source_id, self.reference, self.license)
        for name in ("retrieved_at", "observed_at", "published_at", "fresh_until"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, utc_instant(value))

    def stale(self, at: datetime) -> bool:
        return self.fresh_until is not None and utc_instant(at) >= self.fresh_until


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str
    unit: str

    def __post_init__(self) -> None:
        _required(self.currency, self.unit)
        if not self.amount.is_finite() or self.amount < 0:
            raise ValueError("price must be finite and nonnegative")


@dataclass(frozen=True)
class Quota:
    amount: Decimal
    unit: str
    period: str

    def __post_init__(self) -> None:
        _required(self.unit, self.period)
        if not self.amount.is_finite() or self.amount < 0:
            raise ValueError("quota must be finite and nonnegative")


@dataclass(frozen=True)
class Model:
    model_id: str
    provider_id: str
    provider_model_id: str

    def __post_init__(self) -> None:
        _required(self.model_id, self.provider_id, self.provider_model_id)


@dataclass(frozen=True)
class Capability:
    name: str
    supported: bool | None

    def __post_init__(self) -> None:
        _required(self.name)


@dataclass(frozen=True)
class Benchmark:
    name: str
    version: str
    methodology: str
    configuration: str
    value: Decimal
    unit: str

    def __post_init__(self) -> None:
        _required(self.name, self.version, self.methodology, self.configuration, self.unit)
        if not self.value.is_finite():
            raise ValueError("benchmark value must be finite")


@dataclass(frozen=True)
class Plan:
    plan_id: str
    provider_id: str
    generation: str

    def __post_init__(self) -> None:
        _required(self.plan_id, self.provider_id, self.generation)


@dataclass(frozen=True)
class Terms:
    """None means unknown in a baseline/projection, and unmodified in an override."""

    price: Money | None = None
    quota: Quota | None = None
    available: bool | None = None
    rules: tuple[str, ...] | None = None


@dataclass(frozen=True)
class DailyWindow:
    timezone: str
    start: time
    end: time

    def __post_init__(self) -> None:
        _ = ZoneInfo(self.timezone)
        if self.start.tzinfo is not None or self.end.tzinfo is not None or self.start == self.end:
            raise ValueError("window needs distinct naive local wall times")

    def contains(self, at: datetime) -> bool:
        local = utc_instant(at).astimezone(ZoneInfo(self.timezone)).time()
        if self.start < self.end:
            return self.start <= local < self.end
        return local >= self.start or local < self.end


@dataclass(frozen=True)
class Override:
    """Campaign identity is explicit, including when independent sources dispute its boundaries."""

    campaign_id: str
    terms: Terms
    window: DailyWindow | None = None
    conditions: frozenset[str] = frozenset()
    withdrawn: bool = False

    def __post_init__(self) -> None:
        _required(self.campaign_id, *self.conditions)
        if self.terms == Terms() and not self.withdrawn:
            raise ValueError("override must declare at least one field")


@dataclass(frozen=True)
class Surface:
    surface_id: str
    provider_id: str
    version: str

    def __post_init__(self) -> None:
        _required(self.surface_id, self.provider_id, self.version)


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


@dataclass(frozen=True, kw_only=True)
class Claim:
    claim_id: str
    observation_id: str
    applicability: Period
    revises: str | None = None

    def __post_init__(self) -> None:
        _required(self.claim_id, self.observation_id)
        if self.revises is not None:
            _required(self.revises)
        if self.revises == self.claim_id:
            raise ValueError("claim cannot revise itself")


@dataclass(frozen=True)
class ModelClaim(Claim):
    subject: Model
    payload: Capability | Benchmark | Money


@dataclass(frozen=True)
class OfferClaim(Claim):
    subject: Plan
    payload: Terms | Override

    def __post_init__(self) -> None:
        super().__post_init__()
        if isinstance(self.payload, Override):
            if self.applicability.end is None:
                raise ValueError("temporary override must be bounded")
            if self.payload.withdrawn and self.revises is None:
                raise ValueError("withdrawal must explicitly revise a claim")

    def active(self, at: datetime, conditions: frozenset[str] = frozenset()) -> bool:
        if not self.applicability.contains(at):
            return False
        if isinstance(self.payload, Terms):
            return True
        return (
            not self.payload.withdrawn
            and self.payload.conditions <= conditions
            and (self.payload.window is None or self.payload.window.contains(at))
        )


@dataclass(frozen=True)
class SurfaceClaim(Claim):
    subject: Surface
    payload: SurfaceEvidence


type EvidenceClaim = ModelClaim | OfferClaim | SurfaceClaim


def comparison_key(claim: EvidenceClaim) -> tuple[str, ...]:
    """Comparability, not identity or lineage. Values and source rankings never enter this key."""
    subject = claim.subject
    payload = claim.payload
    if isinstance(claim, ModelClaim):
        prefix = ("model", claim.subject.model_id, claim.subject.provider_id, claim.subject.provider_model_id)
        if isinstance(payload, Capability):
            return (*prefix, "capability", payload.name)
        if isinstance(payload, Benchmark):
            return (
                *prefix,
                "benchmark",
                payload.name,
                payload.version,
                payload.methodology,
                payload.configuration,
                payload.unit,
            )
        if isinstance(payload, Money):
            return (*prefix, "price", payload.currency, payload.unit)
    if isinstance(claim, OfferClaim):
        return (
            "offer",
            claim.subject.plan_id,
            claim.subject.provider_id,
            claim.subject.generation,
            "override" if isinstance(claim.payload, Override) else "baseline",
            claim.payload.campaign_id if isinstance(claim.payload, Override) else "",
        )
    assert isinstance(subject, Surface) and isinstance(payload, SurfaceEvidence)
    return ("surface", subject.surface_id, subject.provider_id, subject.version, payload.capability)


@dataclass(frozen=True)
class Evidence:
    """Historical evidence, not a stream/store. All revision targets must remain present.

    A supplied revision immediately replaces its predecessor in this knowledge set;
    applicability controls whether the new head contributes at T, not when the link exists.
    Use the earlier Evidence value to inspect what was known before that revision.
    """

    observations: tuple[Observation, ...] = ()
    claims: tuple[EvidenceClaim, ...] = ()

    def __post_init__(self) -> None:
        observations = {item.observation_id: item for item in self.observations}
        claims = {item.claim_id: item for item in self.claims}
        if len(observations) != len(self.observations) or len(claims) != len(self.claims):
            raise ValueError("duplicate explicit identity")
        for claim in self.claims:
            if claim.observation_id not in observations:
                raise ValueError("missing observation")
            visited = {claim.claim_id}
            current = claim
            while current.revises is not None:
                previous = claims.get(current.revises)
                if previous is None or comparison_key(previous) != comparison_key(current):
                    raise ValueError("revision must reference a comparable historical claim")
                if previous.claim_id in visited:
                    raise ValueError("cyclic lineage")
                visited.add(previous.claim_id)
                current = previous
        object.__setattr__(self, "observations", tuple(sorted(self.observations, key=lambda item: item.observation_id)))
        object.__setattr__(self, "claims", tuple(sorted(self.claims, key=lambda item: item.claim_id)))

    def extend(
        self,
        *,
        observations: tuple[Observation, ...] = (),
        claims: tuple[EvidenceClaim, ...] = (),
    ) -> Evidence:
        known_observations = {item.observation_id: item for item in self.observations}
        known_claims = {item.claim_id: item for item in self.claims}
        for item in observations:
            previous = known_observations.get(item.observation_id)
            if previous is not None and replace(item, retrieved_at=previous.retrieved_at) != previous:
                raise ValueError("observation identity cannot be rewritten; only retrieval may change")
            known_observations[item.observation_id] = item
        for claim in claims:
            if claim.claim_id in known_claims and known_claims[claim.claim_id] != claim:
                raise ValueError("claim identity cannot be rewritten; supply an explicit revision")
            known_claims[claim.claim_id] = claim
        return Evidence(tuple(known_observations.values()), tuple(known_claims.values()))

    def heads(self) -> tuple[EvidenceClaim, ...]:
        superseded = {claim.revises for claim in self.claims}
        return tuple(claim for claim in self.claims if claim.claim_id not in superseded)

    def status(self, claim_id: str, at: datetime) -> Literal["superseded", "withdrawn", "future", "expired", "current"]:
        claim = next(claim for claim in self.claims if claim.claim_id == claim_id)
        if claim not in self.heads():
            return "superseded"
        if isinstance(claim, OfferClaim) and isinstance(claim.payload, Override) and claim.payload.withdrawn:
            return "withdrawn"
        if utc_instant(at) < claim.applicability.start:
            return "future"
        return "current" if claim.applicability.contains(at) else "expired"
