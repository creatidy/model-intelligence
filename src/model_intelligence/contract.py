"""Working public-evidence grammar and source notices, not consumer admission."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal, InvalidOperation
from typing import Literal, cast

from model_intelligence.deltas import evidence_delta
from model_intelligence.evidence import (
    BaselineClaim,
    Benchmark,
    Capability,
    DailyWindow,
    Evidence,
    EvidenceClaim,
    Model,
    ModelClaim,
    Money,
    NativeLimit,
    Observation,
    OverrideClaim,
    Period,
    Plan,
    Quota,
    Surface,
    SurfaceClaim,
    SurfaceEvidence,
    Terms,
    instant,
)
from model_intelligence.publication import CutReference, SourceRevision, decode_cut, encode_cut

PAYLOAD_SCHEMA = "mi.public-evidence-working/1"
NATIVE_PAYLOAD_SCHEMA = "mi.public-evidence-working/2"
PUBLIC_PAYLOAD_SCHEMAS = frozenset({PAYLOAD_SCHEMA, NATIVE_PAYLOAD_SCHEMA})
type _SurfaceCapability = Literal[
    "headless",
    "structured-output",
    "workspace-editing",
    "model-selection",
    "physical-model-observability",
    "physical-model-enforceability",
]


def _shape(value: object, keys: set[str]) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("payload-shape")
    result = cast(dict[str, object], value)
    if set(result) != keys:
        raise ValueError("payload-shape")
    return result


def _text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("payload-text")
    return value


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError("payload-list")
    result = tuple(_text(item) for item in cast(list[object], value))
    if len(set(result)) != len(result):
        raise ValueError("payload-duplicate")
    return result


def _rows(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("payload-list")
    return cast(list[object], value)


def _optional(value: object) -> str | None:
    return None if value is None else _text(value)


def _at(value: object) -> datetime:
    return instant(datetime.fromisoformat(_text(value)))


def _optional_at(value: object) -> datetime | None:
    return None if value is None else _at(value)


def _boolean(value: object) -> bool | None:
    if value is not None and type(value) is not bool:
        raise ValueError("payload-boolean")
    return value


def _decimal(value: object) -> Decimal:
    try:
        result = Decimal(_text(value))
    except InvalidOperation as error:
        raise ValueError("payload-number") from error
    if not result.is_finite():
        raise ValueError("payload-number")
    return result


def _date(value: datetime | None) -> str | None:
    return None if value is None else instant(value).isoformat()


def _json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


@dataclass(frozen=True)
class Applicability:
    scope_id: str
    channel: str | None
    configuration: tuple[tuple[str, str | None], ...] | None
    source_ids: frozenset[str]

    def __post_init__(self) -> None:
        _text(self.scope_id)
        _optional(self.channel)
        for source_id in self.source_ids:
            _text(source_id)
        if self.configuration is not None:
            names: list[str] = []
            for name, value in self.configuration:
                names.append(_text(name))
                _optional(value)
            if len(set(names)) != len(names):
                raise ValueError("duplicate-configuration")
            object.__setattr__(self, "configuration", tuple(sorted(self.configuration)))


@dataclass(frozen=True)
class SourceNotice:
    """An attributed source assertion. Critical reporting is NOT action authority."""

    notice_id: str
    observation_id: str
    targets: frozenset[str]
    effective_from: datetime
    action: Literal["revocation", "retraction"]
    reported_critical: bool | None
    revises: str | None = None

    def __post_init__(self) -> None:
        _text(self.notice_id)
        _text(self.observation_id)
        if not self.targets or any(not _text(target) for target in self.targets):
            raise ValueError("notice-targets")
        object.__setattr__(self, "effective_from", instant(self.effective_from))
        if self.action not in {"revocation", "retraction"}:
            raise ValueError("notice-action")
        _boolean(self.reported_critical)
        _optional(self.revises)
        if self.action == "retraction" and (self.revises is None or self.reported_critical is not None):
            raise ValueError("notice-retraction")


@dataclass(frozen=True)
class UncertainCampaign:
    """Retain source terms with unknown bounds; never manufacture an R2 Period."""

    annotation_id: str
    observation_id: str
    subject: Plan
    campaign_id: str
    terms: Terms
    effective_from: datetime
    start: datetime | None
    end: datetime | None
    conditions: frozenset[str] = frozenset()
    window: DailyWindow | None = None

    def __post_init__(self) -> None:
        for value in (self.annotation_id, self.observation_id, self.campaign_id, *self.conditions):
            _text(value)
        object.__setattr__(self, "effective_from", instant(self.effective_from))
        for name in ("start", "end"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, instant(value))
        if self.start is not None and self.end is not None:
            raise ValueError("use-bounded-override")
        if self.terms == Terms():
            raise ValueError("empty-campaign")


@dataclass(frozen=True)
class PublicEvidence:
    applicability: Applicability
    evidence: Evidence
    revisions: tuple[tuple[str, str | None], ...]
    notices: tuple[SourceNotice, ...] = ()
    uncertain_campaigns: tuple[UncertainCampaign, ...] = ()

    def __post_init__(self) -> None:
        observed = {item.observation_id: item for item in self.evidence.observations}
        if frozenset(item.source_id for item in observed.values()) != self.applicability.source_ids:
            raise ValueError("incomplete-declared-source-coverage")
        if len(dict(self.revisions)) != len(self.revisions) or set(dict(self.revisions)) != set(observed):
            raise ValueError("revision-coverage")
        for identity, revision in self.revisions:
            _text(identity)
            _optional(revision)
        annotations = {item.annotation_id: item for item in self.uncertain_campaigns}
        notices = {item.notice_id: item for item in self.notices}
        if len(annotations) != len(self.uncertain_campaigns) or len(notices) != len(self.notices):
            raise ValueError("duplicate-public-member")
        targets = {f"statement:{item.claim_id}" for item in self.evidence.claims} | {
            f"uncertain:{identity}" for identity in annotations
        }
        for annotation in annotations.values():
            if annotation.observation_id not in observed:
                raise ValueError("missing-annotation-observation")
        if any(notice.observation_id not in observed or not notice.targets <= targets for notice in notices.values()):
            raise ValueError("missing-notice-provenance-or-target")
        for notice in notices.values():
            cursor = notice
            seen = {notice.notice_id}
            while cursor.revises is not None:
                parent = notices.get(cursor.revises)
                if (
                    parent is None
                    or parent.targets != cursor.targets
                    or observed[parent.observation_id].source_id != observed[cursor.observation_id].source_id
                ):
                    raise ValueError("incomparable-notice-revision")
                if parent.notice_id in seen or cursor.effective_from < parent.effective_from:
                    raise ValueError("invalid-notice-lineage")
                seen.add(parent.notice_id)
                cursor = parent
        object.__setattr__(self, "revisions", tuple(sorted(self.revisions)))
        object.__setattr__(self, "notices", tuple(sorted(self.notices, key=lambda item: item.notice_id)))
        object.__setattr__(
            self, "uncertain_campaigns", tuple(sorted(self.uncertain_campaigns, key=lambda item: item.annotation_id))
        )

    def members(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                [f"observation:{item.observation_id}" for item in self.evidence.observations]
                + [f"statement:{item.claim_id}" for item in self.evidence.claims]
                + [f"notice:{item.notice_id}" for item in self.notices]
                + [f"uncertain:{item.annotation_id}" for item in self.uncertain_campaigns]
            )
        )

    def sources(self) -> frozenset[SourceRevision]:
        revisions = dict(self.revisions)
        return frozenset(
            SourceRevision(item.source_id, item.reference, revisions[item.observation_id])
            for item in self.evidence.observations
        )

    def active_notices(self, at: datetime) -> tuple[SourceNotice, ...]:
        current = {item.notice_id: item for item in self.notices if item.effective_from <= instant(at)}
        replaced = {item.revises for item in current.values()}
        return tuple(
            item for item in current.values() if item.notice_id not in replaced and item.action == "revocation"
        )

    def check_update(self, newer: PublicEvidence) -> None:
        if self.applicability != newer.applicability:
            raise ValueError("scope-change-needs-consumer-review")
        evidence_delta(self.evidence, newer.evidence)
        for old_items, new_items in (
            (dict(self.revisions), dict(newer.revisions)),
            ({item.notice_id: item for item in self.notices}, {item.notice_id: item for item in newer.notices}),
            (
                {item.annotation_id: item for item in self.uncertain_campaigns},
                {item.annotation_id: item for item in newer.uncertain_campaigns},
            ),
        ):
            if any(identity not in new_items or new_items[identity] != value for identity, value in old_items.items()):
                raise ValueError("public-history-rewritten-or-lost")


def _terms(value: Terms) -> dict[str, object]:
    return {
        "price": None if value.price is None else _value(value.price),
        "quota": None
        if value.quota is None
        else {"amount": str(value.quota.amount), "unit": value.quota.unit, "period": value.quota.period},
        "available": value.available,
        "rules": None if value.rules is None else list(value.rules),
    }


def _read_terms(value: object) -> Terms:
    item = _shape(value, {"price", "quota", "available", "rules"})
    price = None if item["price"] is None else _read_value(item["price"])
    if price is not None and not isinstance(price, Money):
        raise ValueError("not-money")
    q = None if item["quota"] is None else _shape(item["quota"], {"amount", "unit", "period"})
    return Terms(
        price,
        None if q is None else Quota(_decimal(q["amount"]), _text(q["unit"]), _text(q["period"])),
        _boolean(item["available"]),
        None if item["rules"] is None else tuple(_text(rule) for rule in _rows(item["rules"])),
    )


def _subject(value: Model | Plan | Surface, schema: str = PAYLOAD_SCHEMA) -> dict[str, object]:
    match value:
        case Model():
            result: dict[str, object] = {
                "kind": "model",
                "id": value.model_id,
                "provider": value.provider_id,
                "request_id": value.provider_model_id,
            }
            if schema == PAYLOAD_SCHEMA:
                if value != Model(value.model_id, value.provider_id, value.provider_model_id):
                    raise ValueError("identity-needs-native-grammar")
            else:
                result.update(
                    {
                        "physical_model": value.physical_model_id,
                        "revision": value.revision,
                        "channel": value.channel,
                        "interface": {
                            "id": value.interface_id,
                            "provider": value.interface_provider_id,
                            "version": value.interface_version,
                        },
                        "configuration": None if value.configuration is None else dict(value.configuration),
                    }
                )
            return result
        case Plan():
            return {"kind": "plan", "id": value.plan_id, "provider": value.provider_id, "generation": value.generation}
        case Surface():
            return {"kind": "surface", "id": value.surface_id, "provider": value.provider_id, "version": value.version}


def _read_subject(value: object, schema: str = PAYLOAD_SCHEMA) -> Model | Plan | Surface:
    if not isinstance(value, dict):
        raise ValueError("subject-shape")
    item = cast(dict[str, object], value)
    kind = item.get("kind")
    extra = {"model": "request_id", "plan": "generation", "surface": "version"}.get(_text(kind))
    if extra is None:
        raise ValueError("subject-kind")
    keys = {"kind", "id", "provider", extra}
    if kind == "model" and schema == NATIVE_PAYLOAD_SCHEMA:
        keys |= {"physical_model", "revision", "channel", "interface", "configuration"}
    item = _shape(item, keys)
    args = (_text(item["id"]), _text(item["provider"]), _text(item[extra]))
    if kind == "model" and schema == NATIVE_PAYLOAD_SCHEMA:
        interface = _shape(item["interface"], {"id", "provider", "version"})
        cfg = item["configuration"]
        if cfg is not None and not isinstance(cfg, dict):
            raise ValueError("configuration-shape")
        return Model(
            *args,
            _optional(item["physical_model"]),
            _optional(item["revision"]),
            _optional(item["channel"]),
            _optional(interface["id"]),
            _optional(interface["provider"]),
            _optional(interface["version"]),
            None if cfg is None else tuple((_text(k), _optional(v)) for k, v in cast(dict[str, object], cfg).items()),
        )
    return Model(*args) if kind == "model" else Plan(*args) if kind == "plan" else Surface(*args)


def _value(
    value: Money | Capability | Benchmark | SurfaceEvidence | NativeLimit, schema: str = PAYLOAD_SCHEMA
) -> dict[str, object]:
    match value:
        case NativeLimit():
            if schema != NATIVE_PAYLOAD_SCHEMA:
                raise ValueError("limit-needs-native-grammar")
            return {
                "kind": "native-limit",
                "dimension": value.dimension,
                "meaning": value.meaning,
                "amount": None if value.amount is None else str(value.amount),
                "unit": value.unit,
                "basis": value.basis,
                "assertion": value.assertion,
            }
        case Money():
            return {"kind": "money", "amount": str(value.amount), "currency": value.currency, "unit": value.unit}
        case Capability():
            return {"kind": "capability", "name": value.name, "supported": value.supported}
        case Benchmark():
            return {
                "kind": "benchmark",
                "name": value.name,
                "version": value.version,
                "method": value.methodology,
                "configuration": value.configuration,
                "amount": str(value.value),
                "unit": value.unit,
            }
        case SurfaceEvidence():
            return {
                "kind": "surface",
                "capability": value.capability,
                "advertised": value.advertised,
                "observed": value.observed,
                "selectable": value.selectable,
                "enforceable": value.enforceable,
                "physical_model": value.physical_model_id,
            }


def _read_value(
    value: object, schema: str = PAYLOAD_SCHEMA
) -> Money | Capability | Benchmark | SurfaceEvidence | NativeLimit:
    if not isinstance(value, dict):
        raise ValueError("value-shape")
    raw = cast(dict[str, object], value)
    match raw.get("kind"):
        case "native-limit" if schema == NATIVE_PAYLOAD_SCHEMA:
            item = _shape(raw, {"kind", "dimension", "meaning", "amount", "unit", "basis", "assertion"})
            assertion = _text(item["assertion"])
            if assertion not in {"advertised", "source-observed", "source-supported", "unknown"}:
                raise ValueError("native-assertion")
            return NativeLimit(
                _text(item["dimension"]),
                _text(item["meaning"]),
                None if item["amount"] is None else _decimal(item["amount"]),
                _optional(item["unit"]),
                _optional(item["basis"]),
                cast("Literal['advertised','source-observed','source-supported','unknown']", assertion),
            )
        case "money":
            item = _shape(raw, {"kind", "amount", "currency", "unit"})
            return Money(_decimal(item["amount"]), _text(item["currency"]), _text(item["unit"]))
        case "capability":
            item = _shape(raw, {"kind", "name", "supported"})
            return Capability(_text(item["name"]), _boolean(item["supported"]))
        case "benchmark":
            item = _shape(raw, {"kind", "name", "version", "method", "configuration", "amount", "unit"})
            return Benchmark(
                _text(item["name"]),
                _text(item["version"]),
                _text(item["method"]),
                _text(item["configuration"]),
                _decimal(item["amount"]),
                _text(item["unit"]),
            )
        case "surface":
            item = _shape(
                raw, {"kind", "capability", "advertised", "observed", "selectable", "enforceable", "physical_model"}
            )
            capability = _text(item["capability"])
            if capability not in {
                "headless",
                "structured-output",
                "workspace-editing",
                "model-selection",
                "physical-model-observability",
                "physical-model-enforceability",
            }:
                raise ValueError("surface-capability")
            return SurfaceEvidence(
                cast(_SurfaceCapability, capability),
                _boolean(item["advertised"]),
                _boolean(item["observed"]),
                _boolean(item["selectable"]),
                _boolean(item["enforceable"]),
                _optional(item["physical_model"]),
            )
        case _:
            raise ValueError("unsupported-value")


def _window(value: DailyWindow | None) -> dict[str, object] | None:
    return (
        None
        if value is None
        else {"timezone": value.timezone, "start": value.start.isoformat(), "end": value.end.isoformat()}
    )


def _read_window(value: object) -> DailyWindow | None:
    if value is None:
        return None
    item = _shape(value, {"timezone", "start", "end"})
    return DailyWindow(
        _text(item["timezone"]), time.fromisoformat(_text(item["start"])), time.fromisoformat(_text(item["end"]))
    )


def _statement(claim: EvidenceClaim, schema: str = PAYLOAD_SCHEMA) -> dict[str, object]:
    row: dict[str, object] = {
        "id": claim.claim_id,
        "origin": claim.observation_id,
        "effective": _date(claim.effective_from),
        "replaces": claim.revises,
        "subject": _subject(claim.subject, schema),
    }
    if isinstance(claim, BaselineClaim):
        row.update({"kind": "baseline", "value": _terms(claim.terms)})
    elif isinstance(claim, OverrideClaim):
        row.update(
            {
                "kind": "campaign",
                "campaign": claim.campaign_id,
                "value": None if claim.terms is None else _terms(claim.terms),
                "interval": None
                if claim.period is None
                else {"start": _date(claim.period.start), "end": _date(claim.period.end)},
                "conditions": sorted(claim.conditions),
                "window": _window(claim.window),
            }
        )
    else:
        row.update(
            {"kind": "model" if isinstance(claim, ModelClaim) else "surface", "value": _value(claim.payload, schema)}
        )
    return row


def _read_statement(value: object, schema: str = PAYLOAD_SCHEMA) -> EvidenceClaim:
    if not isinstance(value, dict):
        raise ValueError("statement-shape")
    raw = cast(dict[str, object], value)
    kind = raw.get("kind")
    keys = {"id", "origin", "effective", "replaces", "subject", "kind", "value"}
    if kind == "campaign":
        keys |= {"campaign", "interval", "conditions", "window"}
    item = _shape(raw, keys)
    subject = _read_subject(item["subject"], schema)
    common = (_text(item["id"]), _text(item["origin"]), _at(item["effective"]), _optional(item["replaces"]))
    if kind == "baseline" and isinstance(subject, Plan):
        return BaselineClaim(
            subject,
            _read_terms(item["value"]),
            claim_id=common[0],
            observation_id=common[1],
            effective_from=common[2],
            revises=common[3],
        )
    if kind == "campaign" and isinstance(subject, Plan):
        period = None if item["interval"] is None else _shape(item["interval"], {"start", "end"})
        return OverrideClaim(
            subject,
            _text(item["campaign"]),
            None if item["value"] is None else _read_terms(item["value"]),
            None if period is None else Period(_at(period["start"]), _at(period["end"])),
            frozenset(_strings(item["conditions"])),
            _read_window(item["window"]),
            claim_id=common[0],
            observation_id=common[1],
            effective_from=common[2],
            revises=common[3],
        )
    payload = _read_value(item["value"], schema)
    if (
        kind == "model"
        and isinstance(subject, Model)
        and isinstance(payload, Money | Capability | Benchmark | NativeLimit)
    ):
        return ModelClaim(
            subject, payload, claim_id=common[0], observation_id=common[1], effective_from=common[2], revises=common[3]
        )
    if kind == "surface" and isinstance(subject, Surface) and isinstance(payload, SurfaceEvidence):
        return SurfaceClaim(
            subject, payload, claim_id=common[0], observation_id=common[1], effective_from=common[2], revises=common[3]
        )
    raise ValueError("statement-kind-or-subject")


def encode_public_evidence(
    cut: PublicEvidence, *, produced_at: datetime, payload_schema: str = PAYLOAD_SCHEMA
) -> tuple[bytes, CutReference]:
    if payload_schema not in PUBLIC_PAYLOAD_SCHEMAS:
        raise ValueError("unsupported-version")
    revisions = dict(cut.revisions)
    payload = {
        "applicability": {
            "scope": cut.applicability.scope_id,
            "channel": cut.applicability.channel,
            "configuration": None if cut.applicability.configuration is None else dict(cut.applicability.configuration),
            "source_ids": sorted(cut.applicability.source_ids),
        },
        "observations": [
            {
                "id": o.observation_id,
                "source": o.source_id,
                "authority": o.authority,
                "type": o.source_type,
                "reference": o.reference,
                "revision": revisions[o.observation_id],
                "rights": {"distribution": o.distribution, "license": o.license},
                "times": {
                    "acquired": _date(o.retrieved_at),
                    "observed": _date(o.observed_at),
                    "published": _date(o.published_at),
                    "fresh_until": _date(o.fresh_until),
                },
            }
            for o in cut.evidence.observations
        ],
        "statements": [_statement(c, payload_schema) for c in cut.evidence.claims],
        "notices": [
            {
                "id": n.notice_id,
                "origin": n.observation_id,
                "targets": sorted(n.targets),
                "effective": _date(n.effective_from),
                "action": n.action,
                "reported_critical": n.reported_critical,
                "replaces": n.revises,
            }
            for n in cut.notices
        ],
        "uncertain_campaigns": [
            {
                "id": c.annotation_id,
                "origin": c.observation_id,
                "subject": _subject(c.subject),
                "campaign": c.campaign_id,
                "value": _terms(c.terms),
                "effective": _date(c.effective_from),
                "start": _date(c.start),
                "end": _date(c.end),
                "conditions": sorted(c.conditions),
                "window": _window(c.window),
            }
            for c in cut.uncertain_campaigns
        ],
    }
    data, reference = encode_cut(
        _json(payload),
        payload_schema=payload_schema,
        produced_at=produced_at,
        scope=cut.applicability.scope_id,
        members=cut.members(),
        sources=tuple(cut.sources()),
    )
    if decode_public_evidence(data, reference, max_bytes=len(data)) != cut:
        raise ValueError("public-payload-not-lossless")
    return data, reference


def decode_public_evidence(
    data: bytes,
    expected: CutReference,
    *,
    max_bytes: int,
    supported_payload_schemas: frozenset[str] = PUBLIC_PAYLOAD_SCHEMAS,
) -> PublicEvidence:
    frame = decode_cut(
        data,
        expected,
        supported_payload_schemas=PUBLIC_PAYLOAD_SCHEMAS & supported_payload_schemas,
        max_bytes=max_bytes,
    )
    root = _shape(
        json.loads(frame.payload, parse_float=Decimal),
        {"applicability", "observations", "statements", "notices", "uncertain_campaigns"},
    )
    a = _shape(root["applicability"], {"scope", "channel", "configuration", "source_ids"})
    cfg = a["configuration"]
    if cfg is not None and not isinstance(cfg, dict):
        raise ValueError("configuration-shape")
    applicability = Applicability(
        _text(a["scope"]),
        _optional(a["channel"]),
        None if cfg is None else tuple((_text(k), _optional(v)) for k, v in cast(dict[str, object], cfg).items()),
        frozenset(_strings(a["source_ids"])),
    )
    observations: list[Observation] = []
    revisions: list[tuple[str, str | None]] = []
    for raw in _rows(root["observations"]):
        o = _shape(raw, {"id", "source", "authority", "type", "reference", "revision", "rights", "times"})
        rights = _shape(o["rights"], {"distribution", "license"})
        times = _shape(o["times"], {"acquired", "observed", "published", "fresh_until"})
        authority, source_type, distribution = _text(o["authority"]), _text(o["type"]), _text(rights["distribution"])
        if (
            authority not in {"official", "secondary", "community"}
            or source_type not in {"documentation", "catalog", "measurement"}
            or distribution not in {"public", "restricted", "unknown"}
        ):
            raise ValueError("observation-classification")
        observations.append(
            Observation(
                _text(o["id"]),
                _text(o["source"]),
                cast("Literal['official','secondary','community']", authority),
                cast("Literal['documentation','catalog','measurement']", source_type),
                _text(o["reference"]),
                _at(times["acquired"]),
                cast("Literal['public','restricted','unknown']", distribution),
                _text(rights["license"]),
                _optional_at(times["observed"]),
                _optional_at(times["published"]),
                _optional_at(times["fresh_until"]),
            )
        )
        revisions.append((_text(o["id"]), _optional(o["revision"])))
    notices: list[SourceNotice] = []
    for raw in _rows(root["notices"]):
        n = _shape(raw, {"id", "origin", "targets", "effective", "action", "reported_critical", "replaces"})
        action = _text(n["action"])
        if action not in {"revocation", "retraction"}:
            raise ValueError("notice-action")
        notices.append(
            SourceNotice(
                _text(n["id"]),
                _text(n["origin"]),
                frozenset(_strings(n["targets"])),
                _at(n["effective"]),
                cast("Literal['revocation','retraction']", action),
                _boolean(n["reported_critical"]),
                _optional(n["replaces"]),
            )
        )
    uncertain: list[UncertainCampaign] = []
    for raw in _rows(root["uncertain_campaigns"]):
        c = _shape(
            raw, {"id", "origin", "subject", "campaign", "value", "effective", "start", "end", "conditions", "window"}
        )
        subject = _read_subject(c["subject"])
        if not isinstance(subject, Plan):
            raise ValueError("campaign-subject")
        uncertain.append(
            UncertainCampaign(
                _text(c["id"]),
                _text(c["origin"]),
                subject,
                _text(c["campaign"]),
                _read_terms(c["value"]),
                _at(c["effective"]),
                _optional_at(c["start"]),
                _optional_at(c["end"]),
                frozenset(_strings(c["conditions"])),
                _read_window(c["window"]),
            )
        )
    result = PublicEvidence(
        applicability,
        Evidence(
            tuple(observations),
            tuple(_read_statement(c, frame.reference.payload_schema) for c in _rows(root["statements"])),
        ),
        tuple(revisions),
        tuple(notices),
        tuple(uncertain),
    )
    if (
        frame.scope != result.applicability.scope_id
        or set(frame.members) != set(result.members())
        or frozenset(frame.sources) != result.sources()
    ):
        raise ValueError("incomplete-or-mismatched-public-cut")
    return result
