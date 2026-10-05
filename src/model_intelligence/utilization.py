"""Working local utilization sidecar; no claim that Router currently emits it."""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import cast

from model_intelligence.evidence import instant
from model_intelligence.publication import CutReference, decode_cut, encode_cut

UTILIZATION_SCHEMA = "mi.utilization-working/1"


@dataclass(frozen=True)
class Utilization:
    cut: CutReference | None
    evaluated_at: datetime
    decision_sha256: str
    context_sha256: str


def encode_utilization(
    cut: CutReference | None,
    *,
    evaluated_at: datetime,
    decision: bytes,
    context: bytes,
) -> tuple[bytes, dict[str, str]]:
    """Bind exact caller-retained bytes, without publishing private decision/context."""
    payload = json.dumps(
        {
            "cut": None
            if cut is None
            else {"format": cut.format_version, "schema": cut.payload_schema, "sha256": cut.sha256},
            "evaluated_at": instant(evaluated_at).isoformat(),
            "decision_sha256": hashlib.sha256(decision).hexdigest(),
            "context_sha256": hashlib.sha256(context).hexdigest(),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    data, reference = encode_cut(
        payload,
        payload_schema=UTILIZATION_SCHEMA,
        produced_at=evaluated_at,
        scope="local-utilization",
        members=(),
        sources=(),
    )
    return data, {
        "source": "model_intelligence",
        "identifier": f"urn:mi:utilization:sha256:{reference.sha256}",
        "version": UTILIZATION_SCHEMA,
    }


def decode_utilization(
    data: bytes,
    reference: dict[str, object],
    *,
    evaluated_at: datetime,
    decision: bytes,
    context: bytes,
    max_bytes: int,
) -> Utilization:
    if (
        set(reference) != {"source", "identifier", "version"}
        or reference["source"] != "model_intelligence"
        or reference["version"] != UTILIZATION_SCHEMA
    ):
        raise ValueError("utilization-reference-shape")
    identifier = reference["identifier"]
    prefix = "urn:mi:utilization:sha256:"
    if not isinstance(identifier, str) or not identifier.startswith(prefix):
        raise ValueError("utilization-reference-identifier")
    frame = decode_cut(
        data,
        CutReference(1, UTILIZATION_SCHEMA, identifier[len(prefix) :]),
        supported_payload_schemas=frozenset({UTILIZATION_SCHEMA}),
        max_bytes=max_bytes,
    )
    if frame.scope != "local-utilization" or frame.members or frame.sources:
        raise ValueError("utilization-frame-shape")
    raw: object = json.loads(frame.payload)
    if not isinstance(raw, dict):
        raise ValueError("utilization-payload-shape")
    value = cast(dict[str, object], raw)
    if set(value) != {"cut", "evaluated_at", "decision_sha256", "context_sha256"}:
        raise ValueError("utilization-payload-shape")
    if (
        value["evaluated_at"] != instant(evaluated_at).isoformat()
        or frame.produced_at != instant(evaluated_at)
        or value["decision_sha256"] != hashlib.sha256(decision).hexdigest()
        or value["context_sha256"] != hashlib.sha256(context).hexdigest()
    ):
        raise ValueError("utilization-input-mismatch")
    cut_value = value["cut"]
    cut: CutReference | None = None
    if cut_value is not None:
        if not isinstance(cut_value, dict):
            raise ValueError("utilization-cut-shape")
        fields = cast(dict[str, object], cut_value)
        if set(fields) != {"format", "schema", "sha256"}:
            raise ValueError("utilization-cut-shape")
        if (
            type(fields["format"]) is not int
            or not isinstance(fields["schema"], str)
            or not isinstance(fields["sha256"], str)
        ):
            raise ValueError("utilization-cut-types")
        cut = CutReference(fields["format"], fields["schema"], fields["sha256"])
    return Utilization(
        cut, instant(evaluated_at), hashlib.sha256(decision).hexdigest(), hashlib.sha256(context).hexdigest()
    )
