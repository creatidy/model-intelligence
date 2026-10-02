"""Small representation proof, not a catalog, eligibility engine or source reconciler."""

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, time
from decimal import Decimal
from enum import StrEnum
from zoneinfo import ZoneInfo


class Authority(StrEnum):
    OFFICIAL = "official"
    SECONDARY = "secondary"
    OBSERVATION = "observation"
    SYNTHETIC = "synthetic"


class Distribution(StrEnum):
    OPEN_LICENSE = "open_license"
    REFERENCE_ONLY = "reference_only"
    UNKNOWN = "unknown"
    SYNTHETIC = "synthetic"


class State(StrEnum):
    CURRENT = "current"
    FUTURE = "future"
    STALE = "stale"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"
    CONFLICTING = "conflicting"
    UNKNOWN = "unknown"


class Assertion(StrEnum):
    ADVERTISED = "advertised"
    OBSERVED = "observed"
    SELECTABLE = "selectable"
    ENFORCEABLE = "enforceable"


class Capability(StrEnum):
    HEADLESS = "headless"
    STRUCTURED_OUTPUT = "structured_output"
    WORKSPACE_READ = "workspace_read"
    WORKSPACE_EDIT = "workspace_edit"
    MODEL_DISCOVERY = "model_discovery"
    MODEL_SELECTION = "model_selection"
    REASONING_STEERING = "reasoning_steering"
    PHYSICAL_MODEL_OBSERVABILITY = "physical_model_observability"
    PHYSICAL_MODEL_ENFORCEABILITY = "physical_model_enforceability"


class IdentityMode(StrEnum):
    PROVIDER_MANAGED = "provider_managed"
    PHYSICAL = "physical"


class ChangeKind(StrEnum):
    MODEL_OBSERVED = "model_observed"
    MODEL_EVIDENCE_CHANGED = "model_evidence_changed"
    PRICE_CHANGED = "price_changed"
    PROMOTION_STARTED = "promotion_started"
    PROMOTION_ENDED = "promotion_ended"
    OFFER_CHANGED = "offer_changed"
    EXECUTION_SURFACE_CHANGED = "execution_surface_changed"
    EVIDENCE_CONFLICT_DETECTED = "evidence_conflict_detected"


def _aware(value: datetime) -> None:
    if value.utcoffset() is None:
        raise ValueError("timestamps must be timezone-aware")


def _instant(value: datetime) -> datetime:
    _aware(value)
    return value.astimezone(UTC)


def _text(*values: str) -> None:
    if any(not value.strip() or value != value.strip() for value in values):
        raise ValueError("identifiers and labels must be nonempty and trimmed")


def _identity(value: str) -> None:
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]*:[a-z0-9][a-z0-9_.-]*", value):
        raise ValueError("model identity must be explicit namespace:release, not an alias or display name")
    if value.split(":")[1] in {"auto", "default", "unknown", "latest"}:
        raise ValueError("a routing alias is not a physical model identity")


def _positive(value: Decimal, *, zero: bool = False) -> None:
    if not value.is_finite() or (value < 0 if zero else value <= 0):
        raise ValueError("numeric evidence must be finite and nonnegative" if zero else "must be finite and positive")


def _encode(value: object) -> str:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, Decimal):
        if value.is_zero():
            return "0"
        number = format(value, "f")
        return number.rstrip("0").rstrip(".") if "." in number else number
    raise TypeError(f"not serializable: {type(value).__name__}")


def _json(value: object) -> str:
    return json.dumps(value, default=_encode, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


@dataclass(frozen=True)
class Source:
    source_id: str
    authority: Authority
    reference: str
    observed_at: datetime
    retrieved_at: datetime
    distribution: Distribution
    license_id: str | None = None

    def __post_init__(self) -> None:
        _text(self.source_id, self.reference)
        object.__setattr__(self, "observed_at", _instant(self.observed_at))
        object.__setattr__(self, "retrieved_at", _instant(self.retrieved_at))
        if self.observed_at > self.retrieved_at:
            raise ValueError("observation cannot follow retrieval")
        if self.distribution == Distribution.OPEN_LICENSE and not self.license_id:
            raise ValueError("open distribution needs an explicit license")


@dataclass(frozen=True)
class Validity:
    """Effective interval is [start, end); observation time does not define it."""

    start: datetime
    end: datetime | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "start", _instant(self.start))
        if self.end is not None:
            object.__setattr__(self, "end", _instant(self.end))
            if self.end <= self.start:
                raise ValueError("effective end must follow start")

    def state_at(self, at: datetime) -> State:
        at = _instant(at)
        if at < self.start:
            return State.FUTURE
        if self.end is not None and at >= self.end:
            return State.EXPIRED
        return State.CURRENT


@dataclass(frozen=True)
class Evidence:
    source: Source
    validity: Validity
    fresh_until: datetime | None = None
    superseded_at: datetime | None = None

    def __post_init__(self) -> None:
        for name in ("fresh_until", "superseded_at"):
            timestamp = self.fresh_until if name == "fresh_until" else self.superseded_at
            if timestamp is not None:
                timestamp = _instant(timestamp)
                object.__setattr__(self, name, timestamp)
                if timestamp < self.source.retrieved_at:
                    raise ValueError("freshness/supersession boundary cannot predate retrieval")

    def states_at(self, at: datetime) -> tuple[State, ...]:
        at = _instant(at)
        temporal = self.validity.state_at(at)
        states = [temporal]
        if self.superseded_at is not None and at >= self.superseded_at:
            states.append(State.SUPERSEDED)
        if self.fresh_until is not None and at >= self.fresh_until:
            states.append(State.STALE)
        return tuple(states)


@dataclass(frozen=True)
class Price:
    input_per_million: Decimal
    output_per_million: Decimal
    currency: str

    def __post_init__(self) -> None:
        _positive(self.input_per_million, zero=True)
        _positive(self.output_per_million, zero=True)
        if not re.fullmatch(r"[A-Z]{3}", self.currency):
            raise ValueError("currency must be a three-letter uppercase code")


@dataclass(frozen=True)
class Benchmark:
    name: str
    version: str
    methodology: str
    configuration: str
    score: Decimal
    unit: str

    def __post_init__(self) -> None:
        _text(self.name, self.version, self.methodology, self.configuration, self.unit)
        _positive(self.score, zero=True)


@dataclass(frozen=True)
class ModelFact:
    """One comparable source assertion, referencing an upstream identity rather than a catalog."""

    model_id: str
    provider: str
    provider_model_id: str
    capabilities: tuple[str, ...]
    benchmark: Benchmark
    price: Price
    evidence: Evidence

    def __post_init__(self) -> None:
        _identity(self.model_id)
        _text(self.provider, self.provider_model_id, *self.capabilities)
        object.__setattr__(self, "capabilities", tuple(sorted(set(self.capabilities))))


@dataclass(frozen=True)
class DailyWindow:
    """Daily wall-clock window; overnight windows are allowed, equal bounds are ambiguous."""

    timezone: str
    start: time
    end: time

    def __post_init__(self) -> None:
        _ = ZoneInfo(self.timezone)
        if self.start.tzinfo is not None or self.end.tzinfo is not None or self.start == self.end:
            raise ValueError("window needs distinct naive wall-clock bounds and an IANA timezone")

    def contains(self, at: datetime) -> bool:
        _aware(at)
        local = at.astimezone(ZoneInfo(self.timezone)).time()
        if self.start < self.end:
            return self.start <= local < self.end
        return local >= self.start or local < self.end


@dataclass(frozen=True)
class OfferRule:
    """Public conditional terms, not an account balance or computed combined discount."""

    plan_id: str
    generation: str
    promotion_id: str
    monthly_price: Decimal
    currency: str
    quota_multiplier: Decimal
    quota_basis: str
    conditions: tuple[str, ...]
    composable_with: tuple[str, ...]
    window: DailyWindow
    evidence: Evidence

    def __post_init__(self) -> None:
        _text(
            self.plan_id, self.generation, self.promotion_id, self.quota_basis, *self.conditions, *self.composable_with
        )
        _positive(self.monthly_price, zero=True)
        _positive(self.quota_multiplier)
        if not re.fullmatch(r"[A-Z]{3}", self.currency):
            raise ValueError("currency must be a three-letter uppercase code")
        if self.evidence.validity.end is None:
            raise ValueError("proof promotions must have an explicit end")
        object.__setattr__(self, "conditions", tuple(sorted(set(self.conditions))))
        object.__setattr__(self, "composable_with", tuple(sorted(set(self.composable_with))))

    def window_active_at(self, at: datetime) -> bool:
        """Time gate only; this does not assert that prerequisites have been fulfilled."""
        states = self.evidence.states_at(at)
        return State.CURRENT in states and State.SUPERSEDED not in states and self.window.contains(at)


@dataclass(frozen=True)
class ExecutionFact:
    surface_id: str
    version: str
    capability: Capability
    assertion: Assertion
    supported: bool | None
    identity_mode: IdentityMode
    physical_model_id: str | None
    evidence: Evidence

    def __post_init__(self) -> None:
        _text(self.surface_id, self.version)
        if self.identity_mode == IdentityMode.PROVIDER_MANAGED:
            if self.physical_model_id is not None:
                raise ValueError("provider-managed execution cannot invent a physical identity")
            if self.capability == Capability.PHYSICAL_MODEL_ENFORCEABILITY and self.supported:
                raise ValueError("provider-managed execution cannot promise physical enforceability")
        else:
            if self.physical_model_id is None:
                raise ValueError("physical identity mode needs a concrete model reference")
            _identity(self.physical_model_id)


type Fact = ModelFact | OfferRule | ExecutionFact
type Key = tuple[str, ...]


def _key(fact: Fact) -> Key:
    if isinstance(fact, ModelFact):
        return ("model", fact.model_id, fact.provider, fact.provider_model_id)
    if isinstance(fact, OfferRule):
        return ("offer", fact.plan_id, fact.generation, fact.promotion_id)
    return (
        "execution",
        fact.surface_id,
        fact.version,
        fact.capability,
        fact.assertion,
        fact.identity_mode,
        fact.physical_model_id or "",
    )


def _meaning(fact: Fact, *, schedule: bool = False) -> str:
    data = asdict(fact)
    del data["evidence"]
    if schedule and isinstance(fact, OfferRule):
        data["validity"] = asdict(fact.evidence.validity)
    return _json(data)


@dataclass(frozen=True)
class Snapshot:
    version: int
    at: datetime
    facts: tuple[Fact, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "at", _instant(self.at))
        if self.version < 1:
            raise ValueError("snapshot version must be positive")
        if any(fact.evidence.source.retrieved_at > self.at for fact in self.facts):
            raise ValueError("snapshot cannot contain evidence not yet retrieved")
        # Exact duplicates are harmless; disagreeing observations are never collapsed.
        ordered = tuple(sorted(set(self.facts), key=lambda fact: _json(asdict(fact))))
        object.__setattr__(self, "facts", ordered)

    def effective(self) -> dict[Key, tuple[Fact, ...]]:
        groups: dict[Key, tuple[Fact, ...]] = {}
        for fact in self.facts:
            states = fact.evidence.states_at(self.at)
            if State.CURRENT in states and State.SUPERSEDED not in states:
                key = _key(fact)
                groups[key] = (*groups.get(key, ()), fact)
        return groups

    def conflicts(self) -> tuple[Key, ...]:
        conflicts: list[Key] = []
        for key, facts in self.effective().items():
            models = tuple(f for f in facts if isinstance(f, ModelFact))
            if models:
                # Prices share a provider identity; benchmark scores additionally need comparable context.
                benchmarks: dict[Key, set[Decimal]] = {}
                for fact in models:
                    b = fact.benchmark
                    context = (b.name, b.version, b.methodology, b.configuration, b.unit)
                    benchmarks.setdefault(context, set()).add(b.score)
                disagrees = (
                    len({f.price for f in models}) > 1
                    or len({f.capabilities for f in models}) > 1
                    or any(len(scores) > 1 for scores in benchmarks.values())
                )
            else:
                disagrees = (
                    len(
                        {
                            _meaning(f, schedule=True)
                            for f in facts
                            if not isinstance(f, ExecutionFact) or f.supported is not None
                        }
                    )
                    > 1
                )
            if disagrees:
                conflicts.append(key)
        return tuple(sorted(conflicts))

    def states(self, fact: Fact) -> tuple[State, ...]:
        if fact not in self.facts:
            raise ValueError("fact is not in this snapshot")
        states = fact.evidence.states_at(self.at)
        if isinstance(fact, ExecutionFact) and fact.supported is None:
            states += (State.UNKNOWN,)
        unknown = isinstance(fact, ExecutionFact) and fact.supported is None
        if (
            not unknown
            and State.SUPERSEDED not in states
            and State.CURRENT in states
            and _key(fact) in self.conflicts()
        ):
            states += (State.CONFLICTING,)
        return states

    def serialize(self) -> str:
        return _json({"schema_version": 1, **asdict(self)})

    @property
    def snapshot_id(self) -> str:
        return hashlib.sha256(self.serialize().encode("ascii")).hexdigest()


@dataclass(frozen=True, order=True)
class Change:
    kind: ChangeKind
    subject: Key


def semantic_changes(before: Snapshot, after: Snapshot) -> tuple[Change, ...]:
    """Endpoint comparison, not replay of transitions that occurred between snapshots."""
    if after.at < before.at or after.version <= before.version:
        raise ValueError("semantic comparison needs increasing versions and nondecreasing time")
    old, new = before.effective(), after.effective()
    changes: set[Change] = set()
    for key in sorted(old.keys() | new.keys()):
        prior, current = old.get(key, ()), new.get(key, ())
        if key[0] == "offer":
            if not prior and current:
                changes.add(Change(ChangeKind.PROMOTION_STARTED, key))
            elif prior and not current:
                # Missing rows are not evidence that a bounded promotion ended.
                retained = tuple(f for f in after.facts if _key(f) == key and State.SUPERSEDED not in after.states(f))
                if retained and all(State.EXPIRED in after.states(f) for f in retained):
                    changes.add(Change(ChangeKind.PROMOTION_ENDED, key))
            elif {_meaning(f, schedule=True) for f in prior} != {_meaning(f, schedule=True) for f in current}:
                changes.add(Change(ChangeKind.OFFER_CHANGED, key))
        elif key[0] == "execution":
            if {_meaning(f) for f in prior} != {_meaning(f) for f in current}:
                changes.add(Change(ChangeKind.EXECUTION_SURFACE_CHANGED, key))
        elif current:
            if not prior:
                known_release = any(_key(f) == key for f in before.facts)
                kind = ChangeKind.MODEL_EVIDENCE_CHANGED if known_release else ChangeKind.MODEL_OBSERVED
                changes.add(Change(kind, key))
            else:
                old_prices = {f.price for f in prior if isinstance(f, ModelFact)}
                new_prices = {f.price for f in current if isinstance(f, ModelFact)}
                if old_prices != new_prices:
                    changes.add(Change(ChangeKind.PRICE_CHANGED, key))
                old_details = {(f.capabilities, f.benchmark) for f in prior if isinstance(f, ModelFact)}
                new_details = {(f.capabilities, f.benchmark) for f in current if isinstance(f, ModelFact)}
                if old_details != new_details:
                    changes.add(Change(ChangeKind.MODEL_EVIDENCE_CHANGED, key))
    for key in set(after.conflicts()) - set(before.conflicts()):
        changes.add(Change(ChangeKind.EVIDENCE_CONFLICT_DETECTED, key))
    return tuple(sorted(changes))


def serialize_changes(changes: tuple[Change, ...]) -> str:
    return _json([asdict(change) for change in sorted(set(changes))])
