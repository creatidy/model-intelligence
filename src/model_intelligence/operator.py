"""Read-only offline full snapshots; no transport, replay, commands or event store."""

from __future__ import annotations

import hashlib
import json
from dataclasses import fields, is_dataclass
from datetime import datetime, time
from decimal import Decimal
from pathlib import Path
from typing import cast
from zoneinfo import ZoneInfoNotFoundError

from model_intelligence.contract import PUBLIC_PAYLOAD_SCHEMAS, PublicEvidence, decode_public_evidence
from model_intelligence.deltas import projection_delta
from model_intelligence.evidence import instant, knowledge
from model_intelligence.producer import retained
from model_intelligence.projection import Conflict, effective_at
from model_intelligence.publication import CutReference, decode_json_object

SCHEMA = "mi.operator-working/1"
CAPABILITIES: dict[str, object] = {"reads": ["status", "inspect", "export"], "commands": [], "replay": False}
FACT_KEYS = (
    "latest",
    "future",
    "stale",
    "unknown_freshness",
    "notices",
    "uncertain_campaigns",
    "conflicts",
    "projection",
)


def _json(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime | time):
        return value.isoformat()
    if isinstance(value, tuple | list):
        return [_json(item) for item in cast(tuple[object, ...] | list[object], value)]
    if isinstance(value, set | frozenset):
        return sorted(cast(set[str] | frozenset[str], value))
    if isinstance(value, dict):
        return {key: _json(item) for key, item in cast(dict[str, object], value).items()}
    return value


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":")).encode()


def _read(path: Path, limit: int) -> bytes:
    if path.is_symlink() or path.stat().st_size > limit:
        raise ValueError("read-policy")
    return path.read_bytes()


def _health(data: bytes) -> dict[str, object]:
    raw = decode_json_object(data)
    keys = {
        "schema",
        "adapter",
        "attempted_at",
        "succeeded",
        "diagnostic",
        "phase",
        "active",
        "last_successful_publication_at",
        "freshness_policy",
        "remediation",
        "sources",
    }
    if raw.get("schema") != "mi.source-refresh-working/1":
        raise ValueError("unsupported-health")
    if (
        set(raw) != keys
        or type(raw["succeeded"]) is not bool
        or not isinstance(raw["adapter"], str)
        or not raw["adapter"].strip()
    ):
        raise ValueError("invalid-health")
    for key in ("attempted_at", "last_successful_publication_at"):
        value = raw[key]
        if value is None and key == "last_successful_publication_at":
            continue
        if not isinstance(value, str):
            raise ValueError("invalid-health")
        _ = instant(datetime.fromisoformat(value))
    if not isinstance(raw["phase"], str) or raw["phase"] not in {
        "retrieval",
        "normalization",
        "publication",
        "complete",
    }:
        raise ValueError("invalid-health")
    active = raw["active"]
    if active is not None:
        if not isinstance(active, str):
            raise ValueError("invalid-health")
        _ = CutReference(1, "mi.public-evidence-working/2", active)
    for key in ("diagnostic", "remediation", "freshness_policy"):
        if raw[key] is not None and not isinstance(raw[key], str):
            raise ValueError("invalid-health")
    if not isinstance(raw["freshness_policy"], str) or not raw["freshness_policy"].strip():
        raise ValueError("invalid-health")
    sources = raw["sources"]
    if not isinstance(sources, list):
        raise ValueError("invalid-health")
    identifiers: set[str] = set()
    for row in cast(list[object], sources):
        if not isinstance(row, dict):
            raise ValueError("invalid-health")
        item = cast(dict[str, object], row)
        if set(item) != {
            "source_id",
            "reference",
            "retrieved",
            "revision",
            "bytes_received",
            "diagnostic",
            "remediation",
        }:
            raise ValueError("invalid-health")
        name = item["source_id"]
        if not isinstance(name, str) or not name.strip() or name in identifiers:
            raise ValueError("invalid-health")
        identifiers.add(name)
        if (
            not isinstance(item["reference"], str)
            or not item["reference"].strip()
            or type(item["retrieved"]) is not bool
        ):
            raise ValueError("invalid-health")
        count = item["bytes_received"]
        if count is not None and (type(count) is not int or count < 0):
            raise ValueError("invalid-health")
        for key in ("revision", "diagnostic", "remediation"):
            if item[key] is not None and not isinstance(item[key], str):
                raise ValueError("invalid-health")
    return raw


def snapshot(
    directory: Path, *, instance: str, at: datetime, max_bytes: int, checkpoint: str | None = None
) -> dict[str, object]:
    at = instant(at)
    if not instance.strip() or type(max_bytes) is not int or max_bytes < 1:
        raise ValueError("operator-policy")
    if checkpoint is not None:
        _ = CutReference(1, "mi.public-evidence-working/2", checkpoint)
    publication: dict[str, object] = {"state": "empty", "reference": None, "artifact": None, "diagnostics": []}
    health: dict[str, object] = {"state": "missing", "sha256": None, "data": None, "correlation": "unavailable"}
    facts: dict[str, object] = {key: [] for key in FACT_KEYS}
    facts["projection"] = {"offers": [], "models": [], "surfaces": [], "conflicts": []}
    history: dict[str, object] = {
        "scope": "retained-publication-cuts-only",
        "replay": False,
        "checkpoint": checkpoint,
        "relation": "unavailable",
        "evidence_added": [],
        "projection_changed": None,
    }
    public: PublicEvidence | None = None
    reference: CutReference | None = None
    try:
        stored = retained(directory, max_bytes=max_bytes)
        if stored is not None:
            data, reference, public = stored
            publication = {
                "state": "available",
                "reference": _json(reference),
                "artifact": data.decode(),
                "diagnostics": [],
            }
    except (ValueError, OSError, UnicodeError, TypeError, ZoneInfoNotFoundError) as error:
        unsupported = isinstance(error, ValueError) and str(error) == "unsupported-version"
        publication["state"] = "unsupported" if unsupported else "invalid"
        publication["diagnostics"] = [
            "retained-publication-unsupported" if unsupported else "retained-publication-invalid-or-unreadable"
        ]
    status_path = directory / "source-status.json"
    if status_path.exists():
        try:
            raw_health = _health(_read(status_path, max_bytes))
            health.update(state="valid", data=raw_health, sha256=hashlib.sha256(canonical(raw_health)).hexdigest())
            if reference is not None and public is not None:
                names = {cast(dict[str, object], row)["source_id"] for row in cast(list[object], raw_health["sources"])}
                matched = (
                    raw_health["active"] == reference.sha256
                    and raw_health["adapter"] == public.applicability.scope_id
                    and names == set(public.applicability.source_ids)
                )
                health["correlation"] = "matched" if matched else "mismatch"
        except (ValueError, OSError, UnicodeError, TypeError) as error:
            health["state"] = (
                "unsupported" if isinstance(error, ValueError) and str(error) == "unsupported-health" else "invalid"
            )
    if reference is not None and public is not None:
        # Publication and health are separate; do not mix a concurrent active-pointer change.
        try:
            if _read(directory / "current", 64).decode("ascii") != reference.sha256:
                raise ValueError("changed")
        except (ValueError, OSError, UnicodeError):
            publication = {
                "state": "invalid",
                "reference": None,
                "artifact": None,
                "diagnostics": ["publication-changed-during-read"],
            }
            public, reference = None, None
            health["correlation"] = "unavailable"
    if reference is not None and public is not None:
        if checkpoint is None:
            history["relation"] = "initial"
        known = knowledge(public.evidence, at)
        projection = effective_at(public.evidence, at)

        def conflicts(items: tuple[Conflict, ...]) -> list[dict[str, object]]:
            return [
                {
                    "subject": list(item.subject),
                    "field": item.field,
                    "claim_ids": sorted("statement:" + name for name in item.claim_ids),
                }
                for item in items
            ]

        projected = {
            "offers": [
                {
                    "plan": _json(offer.plan),
                    "baselines": sorted("statement:" + item.claim_id for item in offer.baselines),
                    "overrides": sorted("statement:" + item.claim_id for item in offer.overrides),
                    "terms": _json(offer.terms),
                    "conflicts": conflicts(offer.conflicts),
                }
                for offer in projection.offers
            ],
            "models": sorted("statement:" + item.claim_id for item in projection.models),
            "surfaces": sorted("statement:" + item.claim_id for item in projection.surfaces),
            "conflicts": conflicts(projection.conflicts),
        }
        facts.update(
            latest=sorted("statement:" + item.claim_id for item in known.latest),
            future=sorted("statement:" + item.claim_id for item in known.future),
            stale=sorted("observation:" + item.observation_id for item in known.stale_observations),
            unknown_freshness=sorted(
                "observation:" + item.observation_id
                for item in public.evidence.observations
                if item.fresh_until is None
            ),
            notices=sorted("notice:" + item.notice_id for item in public.active_notices(at)),
            uncertain_campaigns=sorted("uncertain:" + item.annotation_id for item in public.uncertain_campaigns),
            conflicts=conflicts(projection.conflicts),
            projection=projected,
        )
        if checkpoint is not None:
            try:
                old_ref = CutReference(1, reference.payload_schema, checkpoint)
                old = decode_public_evidence(
                    _read(directory / f"{old_ref.sha256}.json", max_bytes),
                    old_ref,
                    max_bytes=max_bytes,
                    supported_payload_schemas=PUBLIC_PAYLOAD_SCHEMAS,
                )
                old.check_update(public)
                projected = projection_delta(effective_at(old.evidence, at), projection)
                history.update(
                    relation="same" if old_ref == reference else "extension",
                    evidence_added=sorted(set(public.members()) - set(old.members())),
                    projection_changed=any(
                        (
                            projected.offers,
                            projected.models_before,
                            projected.models_after,
                            projected.surfaces_before,
                            projected.surfaces_after,
                            projected.conflicts_before,
                            projected.conflicts_after,
                        )
                    ),
                )
            except (ValueError, OSError, UnicodeError, ZoneInfoNotFoundError):
                history["relation"] = "gap"
    return {
        "schema": SCHEMA,
        "product": "model-intelligence",
        "instance": instance,
        "evaluated_at": at.isoformat(),
        "capabilities": json.loads(canonical(CAPABILITIES)),
        "publication": publication,
        "health": health,
        "facts": facts,
        "history": history,
    }
