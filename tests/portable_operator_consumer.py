"""Independent offline consumer for the frozen mi.operator-working/1 contract.

Original implementation returned by a separate contributor context; no producer
imports or validator reuse. JSON-boundary Any is checked by closed runtime schemas.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Any, Literal, NoReturn, cast

type Object = dict[str, Any]
type Groups = dict[str, dict[str, Object]]
type Validator = Callable[[Any], Any]
type Rule = Validator | dict[str, Rule] | list[Rule] | tuple[str, ...] | str | int | bool | None
type Disposition = Literal["accepted", "duplicate", "resync-required", "rejected"]
type History = Literal["initial", "same", "extension", "gap", "unavailable"]


class ValidationError(ValueError):
    """Messages are constant, data-free diagnostic codes."""


def _fail(code: str) -> NoReturn:
    raise ValidationError(code)


def _string(value: Any) -> str:
    if type(value) is not str:
        _fail("string-type")
    result: str = value
    try:
        result.encode("utf-8")
    except UnicodeError:
        _fail("invalid-utf8")
    return result


def _text(value: Any) -> str:
    result: str = _string(value)
    if not result.strip():
        _fail("empty-text")
    return result


def _boolean(value: Any) -> bool:
    if type(value) is not bool:
        _fail("boolean-type")
    return value


def _pass(value: Any) -> Any:
    return value


def _optional(rule: Rule) -> Validator:
    def validator(value: Any) -> Any:
        return None if value is None else _check(value, rule)

    return validator


def _check(value: Any, rule: Rule) -> Any:
    if callable(rule):
        return rule(value)
    if isinstance(rule, dict):
        if type(value) is not dict:
            _fail("closed-shape")
        obj: Object = cast(Object, value)
        if obj.keys() != rule.keys():
            _fail("closed-shape")
        for key, child in rule.items():
            _check(obj[key], child)
    elif isinstance(rule, list):
        if type(value) is not list:
            _fail("array-type")
        items: list[Any] = cast(list[Any], value)
        if len(rule) == 1:
            for item in items:
                _check(item, rule[0])
        else:
            if len(items) != len(rule):
                _fail("array-shape")
            for item, child in zip(items, rule, strict=True):
                _check(item, child)
    elif isinstance(rule, tuple):
        if type(value) is not str or value not in rule:
            _fail("unsupported-value")
    elif type(value) is not type(rule) or value != rule:
        _fail("unsupported-value")
    return cast(Any, value)


def _strings(value: Any, ordered: bool = False) -> list[str]:
    _check(value, [_text])
    result: list[str] = cast(list[str], value)
    if len(set(result)) != len(result) or (ordered and result != sorted(result)):
        _fail("duplicate-or-unordered")
    return result


def _ordered(value: Any) -> list[str]:
    return _strings(value, True)


def _refs(value: Any, allowed: set[str] | frozenset[str]) -> list[str]:
    result: list[str] = _ordered(value)
    if not set(result) <= allowed:
        _fail("unknown-reference")
    return result


def _ref_rule(allowed: set[str] | frozenset[str]) -> Validator:
    def validator(value: Any) -> list[str]:
        return _refs(value, allowed)

    return validator


def _digest(value: Any) -> str:
    result: str = _string(value)
    if len(result) != 64 or any(c not in "0123456789abcdef" for c in result):
        _fail("digest-shape")
    return result


def _date(value: Any, utc: bool = False) -> datetime:
    try:
        result: datetime = datetime.fromisoformat(_text(value))
        offset: timedelta | None = result.utcoffset()
        if offset is None or (utc and offset.total_seconds() != 0):
            _fail("timestamp-zone")
        return result
    except ValidationError:
        raise
    except (ValueError, OverflowError):
        _fail("timestamp-shape")


def _utc(value: Any) -> datetime:
    return _date(value, True)


def _digits(value: str) -> bool:
    return bool(value) and all(c in "0123456789" for c in value)


def _decimal(value: Any, nonnegative: bool = False) -> str:
    raw: str = _text(value)
    body: str = raw[1:] if raw[:1] in ("+", "-") else raw
    parts: list[str] = body.lower().split("e")
    if len(parts) > 2:
        _fail("decimal-shape")
    if len(parts) == 2:
        exponent: str = parts[1]
        if not _digits(exponent[1:] if exponent[:1] in ("+", "-") else exponent):
            _fail("decimal-shape")
    mantissa: list[str] = parts[0].split(".")
    if len(mantissa) > 2 or not _digits("".join(mantissa)):
        _fail("decimal-shape")
    if nonnegative and raw.startswith("-") and any(c in "123456789" for c in parts[0]):
        _fail("negative-quantity")
    return raw


def _nonnegative(value: Any) -> str:
    return _decimal(value, True)


def _configuration(value: Any) -> Object | None:
    if value is None:
        return None
    if type(value) is not dict:
        _fail("configuration-shape")
    result: Object = cast(Object, value)
    for key, item in result.items():
        _text(key)
        _check(item, _optional(_text))
    return result


def _window(value: Any) -> Object | None:
    if value is None:
        return None
    result: Object = _check(value, dict(timezone=_text, start=_text, end=_text))
    try:
        for key in ("start", "end"):
            parsed: time = time.fromisoformat(result[key])
            if parsed.tzinfo is not None:
                _fail("window-zone")
    except ValidationError:
        raise
    except ValueError:
        _fail("window-time")
    return result


def _pairs(items: list[tuple[str, Any]]) -> Object:
    result: Object = {}
    for key, value in items:
        if key in result:
            _fail("duplicate-key")
        result[key] = value
    return result


def _number(_: str) -> NoReturn:
    _fail("unsupported-number")


def _load(data: bytes) -> Object:
    try:
        result: Any = json.loads(
            data.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_number, parse_float=_number
        )
    except ValidationError:
        raise
    except (UnicodeError, ValueError, RecursionError, OverflowError):
        _fail("invalid-json")
    if type(result) is not dict:
        _fail("root-object")
    return cast(Object, result)


def _hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _version(value: Any) -> int:
    if type(value) is not int or value != 1:
        _fail("unsupported-version")
    return 1


def _payload_schema(value: Any) -> str:
    result: str = _string(value)
    if result not in ("mi.public-evidence-working/1", "mi.public-evidence-working/2"):
        _fail("unsupported-version")
    return result


_MONEY: dict[str, Rule] = dict(kind="money", amount=_nonnegative, currency=_text, unit=_text)
_QUOTA: dict[str, Rule] = dict(amount=_nonnegative, unit=_text, period=_text)
_TERMS: dict[str, Rule] = dict(
    price=_optional(_MONEY), quota=_optional(_QUOTA), available=_optional(_boolean), rules=_optional([_text])
)
_VALUES: dict[str, dict[str, Rule]] = {
    "money": _MONEY,
    "capability": dict(kind="capability", name=_text, supported=_optional(_boolean)),
    "benchmark": dict(
        kind="benchmark", name=_text, version=_text, method=_text, configuration=_text, amount=_decimal, unit=_text
    ),
    "surface": dict(
        kind="surface",
        capability=(
            "headless",
            "structured-output",
            "workspace-editing",
            "model-selection",
            "physical-model-observability",
            "physical-model-enforceability",
        ),
        advertised=_optional(_boolean),
        observed=_optional(_boolean),
        selectable=_optional(_boolean),
        enforceable=_optional(_boolean),
        physical_model=_optional(_text),
    ),
    "native-limit": dict(
        kind="native-limit",
        dimension=_text,
        meaning=_text,
        amount=_optional(_nonnegative),
        unit=_optional(_text),
        basis=_optional(_text),
        assertion=("advertised", "source-observed", "source-supported", "unknown"),
    ),
}


def _subject(value: Any, schema: str) -> Object:
    if type(value) is not dict:
        _fail("subject-kind")
    obj: Object = cast(Object, value)
    kind: str = _text(obj.get("kind"))
    if kind not in ("model", "plan", "surface"):
        _fail("subject-kind")
    extra: str = {"model": "request_id", "plan": "generation", "surface": "version"}[kind]
    rule: dict[str, Rule] = dict(kind=kind, id=_text, provider=_text)
    rule[extra] = _text
    if kind == "model" and schema.endswith("/2"):
        rule.update(
            physical_model=_optional(_text),
            revision=_optional(_text),
            channel=_optional(_text),
            configuration=_configuration,
            interface=dict(id=_optional(_text), provider=_optional(_text), version=_optional(_text)),
        )
    return cast(Object, _check(obj, rule))


def _subject_rule(schema: str) -> Validator:
    def validator(value: Any) -> Object:
        return _subject(value, schema)

    return validator


def _statement(value: Any, schema: str) -> Object:
    if type(value) is not dict:
        _fail("statement-shape")
    obj: Object = cast(Object, value)
    kind: str = _text(obj.get("kind"))
    if kind not in ("baseline", "campaign", "model", "surface"):
        _fail("statement-kind")
    rule: dict[str, Rule] = dict(
        id=_text,
        origin=_text,
        effective=_date,
        replaces=_optional(_text),
        subject=_subject_rule(schema),
        kind=kind,
        value=_pass,
    )
    if kind == "campaign":
        rule.update(
            campaign=_text, interval=_optional(dict(start=_date, end=_date)), conditions=_strings, window=_window
        )
    _check(obj, rule)
    expected: str = "plan" if kind in ("baseline", "campaign") else kind
    if obj["subject"]["kind"] != expected:
        _fail("statement-subject")
    if kind in ("baseline", "campaign"):
        _check(obj["value"], _optional(_TERMS) if kind == "campaign" else _TERMS)
        if kind == "campaign":
            interval = obj["interval"]
            if obj["value"] is None:
                if obj["replaces"] is None or interval is not None or obj["conditions"] or obj["window"] is not None:
                    _fail("withdrawal-shape")
            elif (
                interval is None
                or all(item is None for item in obj["value"].values())
                or _date(interval["end"]) <= _date(interval["start"])
            ):
                _fail("campaign-lifecycle")
    else:
        if type(obj["value"]) is not dict:
            _fail("value-kind")
        item: Object = cast(Object, obj["value"])
        tag: str = _text(item.get("kind"))
        if tag not in _VALUES or (kind == "surface") != (tag == "surface"):
            _fail("value-kind")
        if tag == "native-limit" and schema.endswith("/1"):
            _fail("value-kind")
        _check(item, _VALUES[tag])
    return obj


def _dimension(row: Object) -> tuple[Any, ...]:
    """Independent declared comparability keys, not temporal projection selection."""
    subject = json.dumps(row["subject"], sort_keys=True, separators=(",", ":"))
    kind = row["kind"]
    if kind == "baseline":
        return kind, subject
    if kind == "campaign":
        return kind, subject, row["campaign"]
    value = row["value"]
    tag = value["kind"]
    keys = {
        "money": ("currency", "unit"),
        "capability": ("name",),
        "surface": ("capability",),
        "benchmark": ("name", "version", "method", "configuration", "unit"),
        "native-limit": ("dimension", "meaning", "unit", "basis"),
    }[tag]
    return kind, subject, tag, *(value[key] for key in keys)


def _same_observation(before: Object, after: Object) -> bool:
    old = dict(before)
    new = dict(after)
    old["times"] = {key: value for key, value in before["times"].items() if key != "acquired"}
    new["times"] = {key: value for key, value in after["times"].items() if key != "acquired"}
    return old == new


def _statement_rule(schema: str) -> Validator:
    def validator(value: Any) -> Object:
        return _statement(value, schema)

    return validator


_OBSERVATION: dict[str, Rule] = dict(
    id=_text,
    source=_text,
    authority=("official", "secondary", "community"),
    type=("documentation", "catalog", "measurement"),
    reference=_text,
    revision=_optional(_text),
    rights=dict(distribution=("public", "restricted", "unknown"), license=_text),
    times=dict(acquired=_date, observed=_optional(_date), published=_optional(_date), fresh_until=_optional(_date)),
)
_NOTICE: dict[str, Rule] = dict(
    id=_text,
    origin=_text,
    targets=_strings,
    effective=_date,
    action=("revocation", "retraction"),
    reported_critical=_optional(_boolean),
    replaces=_optional(_text),
)


def _public(frame: Object) -> tuple[Object, Groups, frozenset[str]]:
    schema: str = frame["payload_schema"]
    uncertain: dict[str, Rule] = dict(
        id=_text,
        origin=_text,
        subject=_subject_rule(schema),
        campaign=_text,
        value=_TERMS,
        effective=_date,
        start=_optional(_date),
        end=_optional(_date),
        conditions=_strings,
        window=_window,
    )
    payload: Object = _check(
        _load(frame["payload"].encode("utf-8")),
        dict(
            applicability=dict(
                scope=_text, channel=_optional(_text), configuration=_configuration, source_ids=_strings
            ),
            observations=[_OBSERVATION],
            statements=[_statement_rule(schema)],
            notices=[_NOTICE],
            uncertain_campaigns=[uncertain],
        ),
    )
    groups: Groups = {}
    for name, prefix in (
        ("observations", "observation"),
        ("statements", "statement"),
        ("notices", "notice"),
        ("uncertain_campaigns", "uncertain"),
    ):
        rows: list[Object] = payload[name]
        index: dict[str, Object] = {row["id"]: row for row in rows}
        if len(index) != len(rows):
            _fail("duplicate-identity")
        groups[prefix] = index
    observations: dict[str, Object] = groups["observation"]
    targets: set[str] = {f"{kind}:{key}" for kind in ("statement", "uncertain") for key in groups[kind]}
    for kind in ("statement", "notice", "uncertain"):
        for row in groups[kind].values():
            if row["origin"] not in observations:
                _fail("missing-origin")
            if kind == "uncertain" and row["subject"]["kind"] != "plan":
                _fail("uncertain-subject")
            if kind == "uncertain" and (
                row["start"] is not None
                and row["end"] is not None
                or all(item is None for item in row["value"].values())
            ):
                _fail("uncertain-lifecycle")
            if kind == "notice":
                if not row["targets"] or not set(row["targets"]) <= targets:
                    _fail("notice-target")
                if row["action"] == "retraction" and (row["replaces"] is None or row["reported_critical"] is not None):
                    _fail("notice-retraction")
            if kind != "uncertain":
                seen: set[str] = set()
                cursor: Object = row
                while cursor["replaces"] is not None:
                    parent: str = cursor["replaces"]
                    if parent in seen or parent not in groups[kind]:
                        _fail("revision-reference")
                    previous = groups[kind][parent]
                    if _date(cursor["effective"]) < _date(previous["effective"]):
                        _fail("revision-boundary")
                    if kind == "statement" and _dimension(cursor) != _dimension(previous):
                        _fail("revision-comparability")
                    if kind == "notice" and cursor["targets"] != previous["targets"]:
                        _fail("notice-comparability")
                    if kind == "notice" and (
                        observations[cursor["origin"]]["source"] != observations[previous["origin"]]["source"]
                    ):
                        _fail("notice-source-lineage")
                    seen.add(parent)
                    cursor = groups[kind][parent]
    members: frozenset[str] = frozenset(f"{kind}:{key}" for kind, rows in groups.items() for key in rows)
    app: Object = payload["applicability"]
    sources: set[tuple[str, str, str | None]] = {
        (o["source"], o["reference"], o["revision"]) for o in observations.values()
    }
    manifest: list[tuple[str, str, str | None]] = [
        (s["source_id"], s["reference"], s["revision"]) for s in frame["sources"]
    ]
    if (
        frame["scope"] != app["scope"]
        or set(frame["members"]) != set(members)
        or len(set(manifest)) != len(manifest)
        or set(manifest) != sources
        or set(app["source_ids"]) != {o["source"] for o in observations.values()}
    ):
        _fail("manifest-mismatch")
    return payload, groups, members


@dataclass(frozen=True)
class _Cut:
    reference: Object
    frame: Object
    payload: Object
    groups: Groups
    members: frozenset[str]


def _publication(value: Any) -> _Cut | None:
    obj: Object = _check(
        value,
        dict(
            state=("available", "empty", "invalid", "unsupported"),
            reference=_pass,
            artifact=_pass,
            diagnostics=_strings,
        ),
    )
    codes: set[str] = {
        "retained-publication-invalid-or-unreadable",
        "publication-changed-during-read",
        "retained-publication-unsupported",
    }
    if not set(obj["diagnostics"]) <= codes:
        _fail("diagnostic-code")
    if obj["state"] != "available":
        if obj["reference"] is not None or obj["artifact"] is not None:
            _fail("absent-publication-shape")
        if bool(obj["diagnostics"]) != (obj["state"] != "empty"):
            _fail("diagnostic-state")
        return None
    if obj["diagnostics"]:
        _fail("diagnostic-state")
    reference: Object = _check(
        obj["reference"], dict(format_version=_version, payload_schema=_payload_schema, sha256=_digest)
    )
    artifact: bytes = _text(obj["artifact"]).encode("utf-8")
    if _hash(artifact) != reference["sha256"]:
        _fail("artifact-digest")
    frame: Object = _check(
        _load(artifact),
        dict(
            format_version=_version,
            payload_schema=_payload_schema,
            produced_at=_date,
            scope=_text,
            members=_strings,
            sources=[dict(source_id=_text, reference=_text, revision=_optional(_text))],
            payload=_text,
        ),
    )
    if frame["payload_schema"] != reference["payload_schema"]:
        _fail("payload-schema-mismatch")
    payload, groups, members = _public(frame)
    return _Cut(reference, frame, payload, groups, members)


def _bytes_received(value: Any) -> int | None:
    if value is not None and (type(value) is not int or value < 0):
        _fail("byte-count")
    return value


def _health(value: Any, cut: _Cut | None) -> None:
    obj: Object = _check(
        value,
        dict(
            state=("valid", "missing", "invalid", "unsupported"),
            sha256=_pass,
            data=_pass,
            correlation=("matched", "mismatch", "unavailable"),
        ),
    )
    if obj["state"] != "valid":
        if obj["sha256"] is not None or obj["data"] is not None or obj["correlation"] != "unavailable":
            _fail("absent-health-shape")
        return
    data: Object = _check(
        obj["data"],
        dict(
            schema="mi.source-refresh-working/1",
            adapter=_text,
            attempted_at=_date,
            succeeded=_boolean,
            diagnostic=_optional(_string),
            phase=("retrieval", "normalization", "publication", "complete"),
            active=_optional(_digest),
            last_successful_publication_at=_optional(_date),
            freshness_policy=_text,
            remediation=_optional(_string),
            sources=[
                dict(
                    source_id=_text,
                    reference=_text,
                    retrieved=_boolean,
                    revision=_optional(_string),
                    bytes_received=_bytes_received,
                    diagnostic=_optional(_string),
                    remediation=_optional(_string),
                )
            ],
        ),
    )
    ids: list[str] = [row["source_id"] for row in data["sources"]]
    if len(set(ids)) != len(ids):
        _fail("duplicate-health-source")
    canonical: bytes = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    if _digest(obj["sha256"]) != _hash(canonical):
        _fail("health-digest")
    correlation: str = "unavailable"
    if cut is not None:
        app: Object = cut.payload["applicability"]
        agrees: bool = data["adapter"] == app["scope"] and set(ids) == set(app["source_ids"])
        correlation = "matched" if agrees and data["active"] == cut.reference["sha256"] else "mismatch"
    if obj["correlation"] != correlation:
        _fail("health-correlation")


def _facts(value: Any, cut: _Cut | None) -> None:
    obj: Object = _check(
        value,
        dict(
            latest=_strings,
            future=_strings,
            stale=_strings,
            unknown_freshness=_strings,
            notices=_strings,
            uncertain_campaigns=_strings,
            conflicts=[_pass],
            projection=dict(offers=[_pass], models=_strings, surfaces=_strings, conflicts=[_pass]),
        ),
    )
    groups: Groups = {} if cut is None else cut.groups
    statements: dict[str, Object] = groups.get("statement", {})
    all_claims: set[str] = {f"statement:{key}" for key in statements}

    def by_kind(kind: str) -> set[str]:
        return {f"statement:{key}" for key, row in statements.items() if row["kind"] == kind}

    def conflicts(rows: list[Object]) -> None:
        for row in rows:
            _check(row, dict(subject=[_string], field=_text, claim_ids=_ref_rule(all_claims)))

    for key in ("latest", "future"):
        _refs(obj[key], all_claims)
    observation_ids = {f"observation:{key}" for key in groups.get("observation", {})}
    for key in ("stale", "unknown_freshness"):
        _refs(obj[key], observation_ids)
    _refs(obj["notices"], {f"notice:{key}" for key in groups.get("notice", {})})
    _refs(obj["uncertain_campaigns"], {f"uncertain:{key}" for key in groups.get("uncertain", {})})
    projection: Object = obj["projection"]
    _refs(projection["models"], by_kind("model"))
    _refs(projection["surfaces"], by_kind("surface"))
    conflicts(obj["conflicts"])
    conflicts(projection["conflicts"])
    plans: set[tuple[str, str, str]] = set()
    for offer in projection["offers"]:
        _check(
            offer,
            dict(
                plan=dict(plan_id=_text, provider_id=_text, generation=_text),
                baselines=_ref_rule(by_kind("baseline")),
                overrides=_ref_rule(by_kind("campaign")),
                terms=dict(
                    price=_optional(dict(amount=_nonnegative, currency=_text, unit=_text)),
                    quota=_optional(_QUOTA),
                    available=_optional(_boolean),
                    rules=_optional([_text]),
                ),
                conflicts=[_pass],
            ),
        )
        plan: tuple[str, str, str] = tuple(offer["plan"][k] for k in ("plan_id", "provider_id", "generation"))
        if plan in plans:
            _fail("duplicate-plan")
        plans.add(plan)
        for ref in offer["baselines"] + offer["overrides"]:
            subject: Object = statements[ref.removeprefix("statement:")]["subject"]
            if plan != (subject["id"], subject["provider"], subject["generation"]):
                _fail("offer-subject")
        conflicts(offer["conflicts"])
    if cut is None and (any(obj[k] for k in obj if k != "projection") or any(projection.values())):
        _fail("facts-without-publication")


def _verify(data: bytes, max_bytes: int) -> tuple[Object, _Cut | None]:
    if type(max_bytes) is not int or max_bytes < 1:
        _fail("size-policy")
    if type(data) is not bytes:
        _fail("bytes-type")
    if len(data) > max_bytes:
        _fail("size-limit")
    root: Object = _check(
        _load(data),
        dict(
            schema="mi.operator-working/1",
            product="model-intelligence",
            instance=_text,
            evaluated_at=_utc,
            capabilities=dict(reads=["status", "inspect", "export"], commands=[], replay=False),
            publication=_pass,
            health=_pass,
            facts=_pass,
            history=_pass,
        ),
    )
    cut: _Cut | None = _publication(root["publication"])
    _health(root["health"], cut)
    _facts(root["facts"], cut)
    history: Object = _check(
        root["history"],
        dict(
            scope="retained-publication-cuts-only",
            replay=False,
            checkpoint=_optional(_digest),
            relation=("initial", "same", "extension", "gap", "unavailable"),
            evidence_added=_ref_rule(frozenset() if cut is None else cut.members),
            projection_changed=_optional(_boolean),
        ),
    )
    relation: str = history["relation"]
    checkpoint: str | None = history["checkpoint"]
    if relation == "initial" and checkpoint is not None:
        _fail("history-shape")
    if relation in ("same", "extension"):
        if cut is None or checkpoint is None or type(history["projection_changed"]) is not bool:
            _fail("history-shape")
        if relation == "same" and (checkpoint != cut.reference["sha256"] or history["evidence_added"]):
            _fail("history-shape")
        if relation == "extension" and checkpoint == cut.reference["sha256"]:
            _fail("history-shape")
    if relation == "unavailable" and (history["evidence_added"] or history["projection_changed"] is not None):
        _fail("history-shape")
    if cut is None and relation != "unavailable":
        _fail("history-shape")
    return root, cut


def decode(data: bytes, *, max_bytes: int) -> dict[str, object]:
    """Validate the whole envelope; diagnostics never contain input data."""
    return cast(dict[str, object], _verify(data, max_bytes)[0])


@dataclass(frozen=True, slots=True)
class State:
    snapshot: bytes
    snapshot_sha256: str
    instance: str
    cut_sha256: str | None
    history_gap: bool


@dataclass(frozen=True, slots=True)
class Receipt:
    disposition: Disposition
    state: State | None
    diagnostics: tuple[str, ...] = ()
    history: History = "unavailable"
    replayed: bool = False


def receive(state: State | None, data: bytes, *, max_bytes: int, resync: bool = False) -> Receipt:
    """Follow an independently checked cut chain, or explicitly resynchronize."""
    try:
        if type(resync) is not bool or (state is not None and type(state) is not State):
            _fail("receiver-argument")
        root, cut = _verify(data, max_bytes)
        digest: str = _hash(data)
        cut_digest: str | None = None if cut is None else cut.reference["sha256"]
        old: Object | None = None
        old_cut: _Cut | None = None
        if state is not None:
            if type(state.snapshot) is not bytes:
                _fail("invalid-state")
            old, old_cut = _verify(state.snapshot, len(state.snapshot))
            previous_digest: str | None = None if old_cut is None else old_cut.reference["sha256"]
            if (
                state.snapshot_sha256 != _hash(state.snapshot)
                or state.instance != old["instance"]
                or state.cut_sha256 != previous_digest
                or type(state.history_gap) is not bool
            ):
                _fail("invalid-state")
            if digest == state.snapshot_sha256 and data == state.snapshot:
                return Receipt("duplicate", state)
        history: Object = root["history"]
        gap: bool = resync or history["relation"] in ("gap", "unavailable")
        if state is not None and not resync:
            if (
                old is None
                or root["instance"] != state.instance
                or cut is None
                or old_cut is None
                or history["checkpoint"] != state.cut_sha256
                or history["relation"] not in ("same", "extension")
                or _date(root["evaluated_at"]) < _date(old["evaluated_at"])
                or _date(cut.frame["produced_at"]) < _date(old_cut.frame["produced_at"])
            ):
                return Receipt("resync-required", state, ("checkpoint-not-followed",))
            if cut.payload["applicability"] != old_cut.payload["applicability"]:
                return Receipt("resync-required", state, ("applicability-changed",))
            for kind, rows in old_cut.groups.items():
                if any(
                    key not in cut.groups[kind]
                    or (
                        not _same_observation(row, cut.groups[kind][key])
                        if kind == "observation"
                        else cut.groups[kind][key] != row
                    )
                    for key, row in rows.items()
                ):
                    return Receipt("resync-required", state, ("history-not-preserved",))
            if set(history["evidence_added"]) != set(cut.members - old_cut.members):
                _fail("history-additions-mismatch")
            # Both endpoint cuts are evaluated at the producer's current time.
            # Earlier receiver display facts cannot validate that temporal result.
            gap = state.history_gap
        elif state is None and history["relation"] != "initial":
            gap = True
        accepted: State = State(data, digest, root["instance"], cut_digest, gap)
        receipt_history: History = "unavailable" if resync or gap else cast(History, history["relation"])
        return Receipt("accepted", accepted, ("history-unavailable",) if resync else (), receipt_history)
    except ValidationError as error:
        return Receipt("rejected", state, (str(error),))
