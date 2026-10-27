"""Bounded, separately scoped coding-benchmark evidence from models.dev."""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import cast
from urllib.parse import urlsplit

from model_intelligence.acquisition import Capture, Source, fetch
from model_intelligence.contract import Applicability, PublicEvidence
from model_intelligence.evidence import Benchmark, Evidence, Model, ModelClaim, Observation, instant
from model_intelligence.producer import publish, record_refresh_status, retained
from model_intelligence.publication import CutReference, decode_cut

MODELS_DEV_PIN = "3fb4bb98e633ff1af1b94f84ba07c8549e859aa8"
_MODEL_ROWS = (
    ("sol", "openai/gpt-6.1-sol", "GPT-6.1 Sol"),
    ("luna", "openai/gpt-6-luna", "GPT-6 Luna"),
    ("glm", "zhipuai/glm-5.3", "GLM-5.3"),
    ("flash", "zhipuai/glm-5.3-flash", "GLM-5.3-Flash"),
)
SOURCES = tuple(
    Source(
        source_id=f"models-dev:{source_id}",
        reference=f"https://raw.githubusercontent.com/anomalyco/models.dev/{MODELS_DEV_PIN}/models/{model_id}.toml",
        max_bytes=8192,
        license=f"MIT models.dev, commit {MODELS_DEV_PIN}",
    )
    for source_id, model_id, _ in _MODEL_ROWS
)
_SELECTED_BENCHMARKS = frozenset({"DeepSWE", "SWE-Marathon"})
_BENCHMARK_ROW_FIELDS = frozenset(
    {"name", "score", "metric", "source", "version", "variant", "harness", "dataset", "date"}
)
_VARIANT_EFFORT = re.compile(r"\b(low|medium|high|xhigh|max)\s+effort\b", re.IGNORECASE)
_CITATIONS = {
    "openai/gpt-6-luna": "https://openai.com/index/introducing-gpt-6-sol-and-luna/",
    "zhipuai/glm-5.3": "https://huggingface.co/zai-org/GLM-5.3",
    "zhipuai/glm-5.3-flash": "https://huggingface.co/zai-org/GLM-5.3-Flash",
}
_PROVIDER_REPORT_CONFIGURATION = {
    ("zhipuai/glm-5.3", "DeepSWE"): {
        "evaluator": "Z.ai (provider-run)",
        "harness": "mini-swe-agent",
        "temperature": "0.95",
        "top_p": "1.0",
        "timeout": "6h",
        "context_tokens": 400_000,
        "source_reference": "https://huggingface.co/zai-org/GLM-5.3/raw/ba32f8c19c8738e2c57c71798c601d477a7bf844/README.md",
        "source_revision": "ba32f8c19c8738e2c57c71798c601d477a7bf844",
    },
    ("zhipuai/glm-5.3-flash", "DeepSWE"): {
        "evaluator": "Z.ai (provider-run)",
        "harness": "mini-swe-agent",
        "temperature": "0.95",
        "top_p": "1.0",
        "timeout": "6h",
        "context_tokens": 400_000,
        "source_reference": "https://huggingface.co/zai-org/GLM-5.3-Flash/raw/46a050bec13002ad29ee795c16e61cf4fa3c4a9c/README.md",
        "source_revision": "46a050bec13002ad29ee795c16e61cf4fa3c4a9c",
    },
    ("zhipuai/glm-5.3", "SWE-Marathon"): {
        "evaluator": "Z.ai (provider-run)",
        "harness": "Claude Code 2.1.207",
        "temperature": "1.0",
        "top_p": "0.95",
        "max_new_tokens": 128_000,
        "context_tokens": 1_000_000,
        "source_reference": "https://huggingface.co/zai-org/GLM-5.3/raw/ba32f8c19c8738e2c57c71798c601d477a7bf844/README.md",
        "source_revision": "ba32f8c19c8738e2c57c71798c601d477a7bf844",
    },
}
SOURCE_CONFIG = hashlib.sha256(
    json.dumps(
        {
            "sources": repr(SOURCES),
            "provider_report_configuration": {
                "|".join(key): value for key, value in _PROVIDER_REPORT_CONFIGURATION.items()
            },
        },
        sort_keys=True,
    ).encode()
).hexdigest()
SCOPE = Applicability(
    "models-dev.coding-benchmarks/1",
    "public-benchmark-evidence",
    (
        ("adapter", "models-dev-coding-benchmarks/1"),
        ("source-pin", MODELS_DEV_PIN),
        ("source-config-sha256", SOURCE_CONFIG),
    ),
    frozenset(source.source_id for source in SOURCES),
)


@dataclass(frozen=True)
class RefreshResult:
    reference: CutReference | None
    sources: tuple[tuple[str, str | None], ...]
    succeeded: bool


def _table(value: object, source: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in cast(dict[object, object], value)):
        raise ValueError(f"{source}:source-table")
    return cast(dict[str, object], value)


def _text(value: object, source: str, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{source}:source-text")
    return value.strip()


def _score(value: object, source: str) -> Decimal:
    if type(value) is int:
        result = Decimal(value)
    elif isinstance(value, Decimal):
        result = value
    else:
        raise ValueError(f"{source}:source-score")
    if not result.is_finite():
        raise ValueError(f"{source}:source-score")
    return result


def _citation(value: object, source: str) -> str:
    text = _text(value, source)
    assert text is not None
    parsed = urlsplit(text)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.port not in {None, 443}
    ):
        raise ValueError(f"{source}:source-citation")
    return text


def _model(model_id: str, variant: str | None) -> Model:
    effort_values = [] if variant is None else _VARIANT_EFFORT.findall(variant)
    efforts = {value.lower() for value in effort_values}
    if len(efforts) > 1:
        raise ValueError("source-conflicting-effort")
    effort = next(iter(efforts), None)
    provider, provider_model_id = model_id.split("/", 1)
    return Model(
        model_id=model_id,
        provider_id=provider,
        provider_model_id=provider_model_id,
        configuration=None if effort is None else (("reasoning_effort", effort),),
    )


def _benchmark_rows(document: dict[str, object], source: str) -> tuple[dict[str, object], ...]:
    raw = document.get("benchmarks", [])
    if not isinstance(raw, list):
        raise ValueError(f"{source}:source-benchmark-shape")
    rows: list[dict[str, object]] = []
    for item in cast(list[object], raw):
        row = _table(item, source)
        if not set(row) <= _BENCHMARK_ROW_FIELDS:
            raise ValueError(f"{source}:source-benchmark-schema")
        name = _text(row.get("name"), source)
        _ = _score(row.get("score"), source)
        _ = _text(row.get("metric"), source)
        _ = _citation(row.get("source"), source)
        for key in ("version", "variant", "harness", "dataset", "date"):
            _ = _text(row.get(key), source, optional=True)
        if name in _SELECTED_BENCHMARKS:
            rows.append(row)
    return tuple(rows)


def normalize(captures: tuple[Capture, ...], *, at: datetime, previous: PublicEvidence | None = None) -> PublicEvidence:
    """Validate all four pinned model records and retain only two coding benchmarks."""
    at = instant(at)
    if len(captures) != len(SOURCES) or {item.source for item in captures} != set(SOURCES):
        raise ValueError("incomplete-or-unexpected-source-generation")
    if previous is not None and previous.applicability != SCOPE:
        raise ValueError("source-adapter-migration-required")
    by_source = {item.source.source_id: item for item in captures}
    observations = {item.observation_id: item for item in (() if previous is None else previous.evidence.observations)}
    claims = {item.claim_id: item for item in (() if previous is None else previous.evidence.claims)}
    revisions = {} if previous is None else dict(previous.revisions)

    for (_source_id, model_id, expected_name), source in zip(_MODEL_ROWS, SOURCES, strict=True):
        capture = by_source[source.source_id]
        try:
            document = _table(tomllib.loads(capture.data.decode("utf-8"), parse_float=Decimal), source.source_id)
        except (UnicodeError, tomllib.TOMLDecodeError) as error:
            raise ValueError(f"{source.source_id}:source-toml") from error
        if document.get("schema") != 2 or document.get("name") != expected_name:
            raise ValueError(f"{source.source_id}:source-model-identity")
        observation_id = f"{source.source_id}:{capture.revision.removeprefix('content-sha256:')}"
        if observation_id not in observations:
            observations[observation_id] = Observation(
                observation_id,
                source.source_id,
                "secondary",
                "catalog",
                source.reference,
                capture.acquired_at,
                "public",
                source.license,
                observed_at=capture.acquired_at,
            )
            revisions[observation_id] = capture.revision
        rows = _benchmark_rows(document, source.source_id)
        for row in rows:
            name = _text(row.get("name"), source.source_id)
            assert name is not None
            citation = _citation(row.get("source"), source.source_id)
            if citation != _CITATIONS.get(model_id):
                raise ValueError(f"{source.source_id}:source-rights-or-provenance")
            metric = _text(row.get("metric"), source.source_id)
            assert metric is not None
            version = _text(row.get("version"), source.source_id, optional=True) or "UNKNOWN"
            variant = _text(row.get("variant"), source.source_id, optional=True)
            harness = _text(row.get("harness"), source.source_id, optional=True)
            dataset = _text(row.get("dataset"), source.source_id, optional=True)
            reported_date = _text(row.get("date"), source.source_id, optional=True)
            if reported_date is not None:
                try:
                    _ = date.fromisoformat(reported_date)
                except ValueError as error:
                    raise ValueError(f"{source.source_id}:source-date") from error
            provider_configuration = _PROVIDER_REPORT_CONFIGURATION.get((model_id, name), {})
            configuration = json.dumps(
                {
                    "context_tokens": provider_configuration.get("context_tokens"),
                    "dataset": dataset,
                    "evaluator": provider_configuration.get("evaluator", "UNKNOWN"),
                    "harness": provider_configuration.get("harness", harness),
                    "max_new_tokens": provider_configuration.get("max_new_tokens"),
                    "provider_configuration_reference": provider_configuration.get("source_reference"),
                    "provider_configuration_revision": provider_configuration.get("source_revision"),
                    "provider_configuration_verified_on": "2026-10-27" if provider_configuration else None,
                    "reported_date": reported_date,
                    "reported_source": citation,
                    "temperature": provider_configuration.get("temperature"),
                    "timeout": provider_configuration.get("timeout"),
                    "top_p": provider_configuration.get("top_p"),
                    "variant": variant,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            model = _model(model_id, variant)
            payload = Benchmark(
                name, version, metric, configuration, _score(row.get("score"), source.source_id), "UNKNOWN"
            )
            identity = observation_id + ":claim:" + hashlib.sha256(repr((model, payload)).encode()).hexdigest()
            if not any(
                isinstance(claim, ModelClaim)
                and claim.subject == model
                and claim.payload == payload
                and claim.observation_id == observation_id
                for claim in claims.values()
            ):
                claims[identity] = ModelClaim(
                    model,
                    payload,
                    claim_id=identity,
                    observation_id=observation_id,
                    effective_from=observations[observation_id].observed_at or at,
                )

    return PublicEvidence(
        SCOPE,
        previous.evidence.extend(observations=tuple(observations.values()), claims=tuple(claims.values()))
        if previous is not None
        else Evidence(tuple(observations.values()), tuple(claims.values())),
        tuple(sorted(revisions.items())),
    )


def compare(public: PublicEvidence) -> dict[str, object]:
    """Render an unranked evidence comparison; never normalize or choose a winner."""
    if public.applicability != SCOPE:
        raise ValueError("benchmark-comparison-scope")
    model_names = {model_id: name for _, model_id, name in _MODEL_ROWS}
    benchmark_claims: list[tuple[ModelClaim, Benchmark]] = []
    for claim in public.evidence.claims:
        if isinstance(claim, ModelClaim) and isinstance(claim.payload, Benchmark):
            if claim.payload.name in _SELECTED_BENCHMARKS:
                benchmark_claims.append((claim, claim.payload))
    candidates: list[dict[str, object]] = []
    for _, model_id, display_name in _MODEL_ROWS:
        records: list[dict[str, object]] = []
        for claim, payload in benchmark_claims:
            if claim.subject.model_id != model_id:
                continue
            observation = next(
                item for item in public.evidence.observations if item.observation_id == claim.observation_id
            )
            peer_rows = [
                (peer, peer_payload)
                for peer, peer_payload in benchmark_claims
                if peer.subject.model_id != model_id and peer_payload.name == payload.name
            ]
            same_version = [
                (peer, peer_payload) for peer, peer_payload in peer_rows if peer_payload.version == payload.version
            ]
            same_metric = [
                (peer, peer_payload)
                for peer, peer_payload in same_version
                if peer_payload.methodology == payload.methodology and peer_payload.unit == payload.unit
            ]
            matching_context: list[str] = []
            for peer, peer_payload in same_metric:
                peer_configuration = json.loads(peer_payload.configuration)
                configuration = json.loads(payload.configuration)
                fields = (
                    "harness",
                    "evaluator",
                    "temperature",
                    "top_p",
                    "timeout",
                    "context_tokens",
                    "max_new_tokens",
                )
                if all(configuration.get(field) == peer_configuration.get(field) for field in fields) and dict(
                    claim.subject.configuration or ()
                ) == dict(peer.subject.configuration or ()):
                    matching_context.append(model_names[peer.subject.model_id])
            if matching_context:
                comparability = (
                    "same reported configuration with "
                    + ", ".join(sorted(set(matching_context)))
                    + "; native unit, exact task sampling and repeated-run uncertainty remain UNKNOWN"
                )
            elif peer_rows and not same_version:
                comparability = "not comparable to selected peers: benchmark version differs"
            elif same_version and not same_metric:
                comparability = "not comparable to selected peers: source metric labels differ"
            elif peer_rows:
                comparability = "configuration match not established for selected peers"
            else:
                comparability = "no selected peer row for this benchmark"
            records.append(
                {
                    "benchmark": payload.name,
                    "version": payload.version,
                    "metric": payload.methodology,
                    "value": str(payload.value),
                    "unit": payload.unit,
                    "configuration": json.loads(payload.configuration),
                    "model_configuration": dict(claim.subject.configuration or ()),
                    "source_authority": observation.authority,
                    "source_reference": observation.reference,
                    "source_revision": dict(public.revisions)[observation.observation_id],
                    "observed_at": observation.observed_at.isoformat() if observation.observed_at else None,
                    "comparability": comparability,
                    "same_reported_configuration_peers": sorted(set(matching_context)),
                }
            )
        candidates.append(
            {
                "model_id": model_id,
                "name": display_name,
                "requested_variant": {"openai/gpt-6.1-sol": "high", "openai/gpt-6-luna": "max"}.get(model_id),
                "benchmarks": sorted(
                    records, key=lambda record: (cast(str, record["benchmark"]), str(record["version"]))
                ),
                "evidence_state": "available"
                if records
                else "UNKNOWN: no selected benchmark record in this source slice",
            }
        )
    return {
        "scenario": (
            "Autonomous Kilo coding task: diagnose a repository defect, implement a fix, run tests and prepare a PR."
        ),
        "relevant_benchmarks": {
            "DeepSWE": (
                "Relevant to long-horizon repository engineering, but not an exact proxy "
                "for a bounded defect/test/PR task."
            ),
            "SWE-Marathon": (
                "Relevant to extended software-engineering agents; its leaderboard dataset "
                "is excluded because no data-use license was verified."
            ),
        },
        "candidates": candidates,
        "conclusion": (
            "Observed model-plus-harness records are contextual facts, not a controlled "
            "model-only comparison. No winner or Router rating is inferred."
        ),
    }


def refresh(
    directory: Path, *, at: datetime, max_artifact_bytes: int, timeout: float
) -> tuple[CutReference | None, RefreshResult]:
    """Fetch the pinned source set and atomically publish only a complete valid cut."""
    at = instant(at)
    if type(max_artifact_bytes) is not int or max_artifact_bytes < 1:
        raise ValueError("invalid-artifact-size-policy")
    prior = retained(directory, max_bytes=max_artifact_bytes)
    previous = None if prior is None else prior[2]
    captures: list[Capture] = []
    health: list[dict[str, object]] = []
    for source in SOURCES:
        try:
            capture = fetch(source, at=at, timeout=timeout)
            captures.append(capture)
            health.append(
                {
                    "source_id": source.source_id,
                    "reference": source.reference,
                    "retrieved": True,
                    "revision": capture.revision,
                    "bytes_received": len(capture.data),
                    "diagnostic": None,
                    "remediation": None,
                }
            )
        except (ValueError, OSError) as error:
            code = error.args[0] if error.args else None
            diagnostic = code if isinstance(code, str) and ":" not in code else "source-retrieval-failed"
            health.append(
                {
                    "source_id": source.source_id,
                    "reference": source.reference,
                    "retrieved": False,
                    "revision": None,
                    "bytes_received": None,
                    "diagnostic": diagnostic,
                    "remediation": "Inspect the pinned source availability; never shrink the declared source set.",
                }
            )
    if len(captures) != len(SOURCES):
        active = prior[1] if prior is not None else None
        _write_status(directory, at, active, False, "retrieval", health, max_artifact_bytes)
        return active, RefreshResult(
            active, tuple((str(row["source_id"]), cast(str | None, row["diagnostic"])) for row in health), False
        )
    try:
        public = normalize(tuple(captures), at=at, previous=previous)
        reference = publish(directory, public, expected=SCOPE, produced_at=at, max_bytes=max_artifact_bytes)
    except (ValueError, OSError) as error:
        diagnostic = error.args[0] if error.args and isinstance(error.args[0], str) else "source-validation-failed"
        health = [
            dict(
                row,
                diagnostic=diagnostic,
                remediation="Inspect the selected record identity, source references, and benchmark schema.",
            )
            for row in health
        ]
        active = prior[1] if prior is not None else None
        _write_status(directory, at, active, False, "normalization", health, max_artifact_bytes, diagnostic)
        return active, RefreshResult(
            active, tuple((str(row["source_id"]), cast(str | None, row["diagnostic"])) for row in health), False
        )
    _write_status(directory, at, reference, True, "complete", health, max_artifact_bytes)
    return reference, RefreshResult(reference, tuple((str(row["source_id"]), None) for row in health), True)


def _write_status(
    directory: Path,
    at: datetime,
    active: CutReference | None,
    succeeded: bool,
    phase: str,
    sources: list[dict[str, object]],
    max_artifact_bytes: int,
    diagnostic: str | None = None,
) -> None:
    stored = retained(directory, max_bytes=max_artifact_bytes)
    last_successful_publication_at = None
    if stored is not None:
        last_successful_publication_at = decode_cut(
            stored[0],
            stored[1],
            supported_payload_schemas=frozenset({stored[1].payload_schema}),
            max_bytes=max_artifact_bytes,
        ).produced_at.isoformat()
    record_refresh_status(
        directory,
        json.dumps(
            {
                "schema": "mi.source-refresh-working/1",
                "adapter": SCOPE.scope_id,
                "attempted_at": at.isoformat(),
                "succeeded": succeeded,
                "diagnostic": diagnostic,
                "phase": phase,
                "active": None if active is None else active.sha256,
                "last_successful_publication_at": last_successful_publication_at,
                "freshness_policy": "No automatic freshness or evaluation date is inferred.",
                "remediation": None
                if succeeded
                else "Inspect the named source diagnostics; keep the previous publication intact.",
                "sources": sources,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode(),
    )
