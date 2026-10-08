"""Complete immutable local publication, not a catalog or consumer admission policy."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

from model_intelligence.contract import (
    NATIVE_PAYLOAD_SCHEMA,
    Applicability,
    PublicEvidence,
    decode_public_evidence,
    encode_public_evidence,
)
from model_intelligence.publication import CutReference, decode_json_object


def _write_atomic(path: Path, data: bytes) -> None:
    temporary: str | None = None
    try:
        with NamedTemporaryFile(dir=path.parent, prefix=".publication-", delete=False) as output:
            temporary = output.name
            _ = output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def record_refresh_status(directory: Path, data: bytes) -> None:
    """Operator facts only; this write cannot change the active publication."""
    _ = decode_json_object(data)
    _write_atomic(directory / "source-status.json", data)


def retained(directory: Path, *, max_bytes: int) -> tuple[bytes, CutReference, PublicEvidence] | None:
    pointer = directory / "current"
    if not pointer.exists():
        return None
    if pointer.stat().st_size != 64:
        raise ValueError("invalid-retained-pointer")
    reference = CutReference(1, NATIVE_PAYLOAD_SCHEMA, pointer.read_text(encoding="ascii"))
    path = directory / f"{reference.sha256}.json"
    if type(max_bytes) is not int or max_bytes < 1 or path.stat().st_size > max_bytes:
        raise ValueError("retained-size-policy")
    data = path.read_bytes()
    return (
        data,
        reference,
        decode_public_evidence(
            data, reference, max_bytes=max_bytes, supported_payload_schemas=frozenset({NATIVE_PAYLOAD_SCHEMA})
        ),
    )


def publish(
    directory: Path, cut: PublicEvidence, *, expected: Applicability, produced_at: datetime, max_bytes: int
) -> CutReference:
    """One mutator: validate all source/history inputs before changing active bytes."""
    if cut.applicability != expected:
        raise ValueError("incomplete-or-unexpected-source-scope")
    previous = retained(directory, max_bytes=max_bytes)
    if previous is not None:
        previous[2].check_update(cut)
    data, reference = encode_public_evidence(cut, produced_at=produced_at, payload_schema=NATIVE_PAYLOAD_SCHEMA)
    decode_public_evidence(data, reference, max_bytes=max_bytes)
    path = directory / f"{reference.sha256}.json"
    if path.exists():
        if path.stat().st_size != len(data) or path.read_bytes() != data:
            raise ValueError("retained-artifact-corrupt")
    else:
        _write_atomic(path, data)
    _write_atomic(directory / "current", reference.sha256.encode("ascii"))
    return reference


def import_legacy(
    directory: Path,
    data: bytes,
    reference: CutReference,
    *,
    expected: Applicability,
    produced_at: datetime,
    max_bytes: int,
) -> CutReference:
    """Explicit /1 -> /2 import; retain original immutable bytes and unknown fields.

    This changes encoding, not evidence or source scope. An unsupported version,
    missing history or wrong expected scope fails before any active-pointer write.
    """
    from model_intelligence.contract import PAYLOAD_SCHEMA

    original = decode_public_evidence(
        data, reference, max_bytes=max_bytes, supported_payload_schemas=frozenset({PAYLOAD_SCHEMA})
    )
    if original.applicability != expected:
        raise ValueError("migration-scope")
    path = directory / f"{reference.sha256}.legacy.json"
    if path.exists():
        if path.stat().st_size != len(data) or path.read_bytes() != data:
            raise ValueError("legacy-artifact-corrupt")
    else:
        _write_atomic(path, data)
    return publish(directory, original, expected=expected, produced_at=produced_at, max_bytes=max_bytes)
