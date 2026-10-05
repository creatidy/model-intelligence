"""Candidate publication framing; payload semantics and admission remain explicit."""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import cast

from model_intelligence.evidence import instant


def _text(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("invalid-text")
    return value


def _object(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("invalid-object")
    return cast(dict[str, object], value)


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate-key")
        result[key] = value
    return result


def _constant(value: str) -> object:
    raise ValueError(f"nonfinite-number:{value}")


def _load(data: bytes) -> dict[str, object]:
    try:
        return _object(json.loads(data.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant))
    except (UnicodeDecodeError, RecursionError) as error:
        raise ValueError("invalid-json") from error


def _dump(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class SourceRevision:
    source_id: str
    reference: str
    revision: str | None

    def __post_init__(self) -> None:
        _text(self.source_id)
        _text(self.reference)
        if self.revision is not None:
            _text(self.revision)


@dataclass(frozen=True)
class CutReference:
    format_version: int
    payload_schema: str
    sha256: str

    def __post_init__(self) -> None:
        if type(self.format_version) is not int or self.format_version < 1:
            raise ValueError("invalid-format-version")
        _text(self.payload_schema)
        if len(self.sha256) != 64 or any(character not in "0123456789abcdef" for character in self.sha256):
            raise ValueError("invalid-digest")


@dataclass(frozen=True)
class Publication:
    reference: CutReference
    produced_at: datetime
    scope: str
    members: tuple[str, ...]
    sources: tuple[SourceRevision, ...]
    payload: bytes


def encode_cut(
    payload: bytes,
    *,
    payload_schema: str,
    produced_at: datetime,
    scope: str,
    members: tuple[str, ...],
    sources: tuple[SourceRevision, ...],
) -> tuple[bytes, CutReference]:
    """Encode an explicit cut. The caller must validate its payload and completeness."""
    payload_schema, scope = _text(payload_schema), _text(scope)
    if len(set(members)) != len(members) or any(not _text(member) for member in members):
        raise ValueError("invalid-membership")
    if len(set(sources)) != len(sources):
        raise ValueError("duplicate-source-revision")
    data = _dump(
        {
            "format_version": 1,
            "payload_schema": payload_schema,
            "produced_at": instant(produced_at).isoformat(),
            "scope": scope,
            "members": sorted(members),
            "sources": [
                {"source_id": item.source_id, "reference": item.reference, "revision": item.revision}
                for item in sorted(sources, key=lambda item: (item.source_id, item.reference, item.revision or ""))
            ],
            "payload": _load(payload),
        }
    )
    return data, CutReference(1, payload_schema, hashlib.sha256(data).hexdigest())


def decode_cut(
    data: bytes,
    expected: CutReference,
    *,
    supported_payload_schemas: frozenset[str],
    max_bytes: int,
) -> Publication:
    """Verify framing against an independently supplied reference, not authenticity."""
    if type(max_bytes) is not int or max_bytes < 1:
        raise ValueError("invalid-size-policy")
    if len(data) > max_bytes:
        raise ValueError("size-limit")
    if expected.format_version != 1 or expected.payload_schema not in supported_payload_schemas:
        raise ValueError("unsupported-version")
    if hashlib.sha256(data).hexdigest() != expected.sha256:
        raise ValueError("digest-mismatch")
    value = _load(data)
    if set(value) != {"format_version", "payload_schema", "produced_at", "scope", "members", "sources", "payload"}:
        raise ValueError("invalid-frame-shape")
    if type(value["format_version"]) is not int or value["format_version"] != expected.format_version:
        raise ValueError("unsupported-version")
    if value["payload_schema"] != expected.payload_schema:
        raise ValueError("payload-schema-mismatch")
    raw_members, raw_sources = value["members"], value["sources"]
    if not isinstance(raw_members, list) or not isinstance(raw_sources, list):
        raise ValueError("invalid-membership")
    members = tuple(_text(item) for item in cast(list[object], raw_members))
    sources: list[SourceRevision] = []
    for raw_source in cast(list[object], raw_sources):
        source = _object(raw_source)
        if set(source) != {"source_id", "reference", "revision"}:
            raise ValueError("invalid-source-shape")
        revision = None if source["revision"] is None else _text(source["revision"])
        sources.append(SourceRevision(_text(source["source_id"]), _text(source["reference"]), revision))
    if len(set(members)) != len(members) or len(set(sources)) != len(sources):
        raise ValueError("duplicate-membership")
    return Publication(
        expected,
        instant(datetime.fromisoformat(_text(value["produced_at"]))),
        _text(value["scope"]),
        members,
        tuple(sources),
        _dump(_object(value["payload"])),
    )
