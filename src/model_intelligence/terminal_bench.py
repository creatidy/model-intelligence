"""Bounded evidence adapter for official Terminal-Bench 4.0 submissions."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import cast
from urllib.parse import urlsplit
from uuid import UUID

from model_intelligence.acquisition import (
    Capture,
    Source,
    fetch,
)
from model_intelligence.benchmarks import SCOPE as CODING_SCOPE
from model_intelligence.benchmarks import compare as compare_coding
from model_intelligence.contract import Applicability, PublicEvidence
from model_intelligence.evidence import Benchmark, Evidence, Model, ModelClaim, Observation, instant
from model_intelligence.producer import publish, record_refresh_status, retained
from model_intelligence.publication import CutReference, decode_cut

TERMINAL_BENCH_REPOSITORY_PIN = "6964e9252c90227fc1cfa26cbc59aee4134792e4"
TERMINAL_BENCH_DATASET_REF = "sha256:39d9f44b40420cde8fdcc087579c0d72a7e14fa3656d603c3f0d22fb35e27732"
TERMINAL_BENCH_DATASET_VERSION = "4.0.0"
TERMINAL_BENCH_TASK_COUNT = 66
TERMINAL_BENCH_MIN_TRIALS_PER_TASK = 5
TERMINAL_BENCH_TRIAL_COUNT = TERMINAL_BENCH_TASK_COUNT * TERMINAL_BENCH_MIN_TRIALS_PER_TASK
TERMINAL_BENCH_LICENSE = (
    "Apache-2.0 Terminal-Bench repository submission contribution; "
    f"commit {TERMINAL_BENCH_REPOSITORY_PIN}, root LICENSE Sections 2 and 5"
)
_METHOD = (
    "accuracy/resolution rate; verifier reward > 0 is success; 95% CI half-width uses "
    "1.96 times the official per-task standard error, where variance is "
    "sum(p_i*(1-p_i)/(k_i-1))/n_tasks^2"
)
_METRIC_FIELDS = frozenset(
    {
        "accuracy",
        "accuracy_ci95_half_width",
        "display_accuracy",
        "n_trials",
        "successes",
        "pass_at_2",
        "pass_at_3",
        "pass_at_4",
        "pass_at_5",
        "uncached_input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "total_tokens",
        "display_total_tokens",
        "total_cost_usd",
        "display_cost",
        "display_total_cost_usd",
        "avg_trial_duration_sec",
    }
)
_SUBMISSION_FIELDS = frozenset({"source_jobs", "source_filter", "metadata", "metrics", "disqualified_trials", "trials"})
_FILTER_FIELDS = frozenset({"agent", "agent_version", "model_name", "reasoning_effort"})
_METADATA_FIELDS = frozenset(
    {"agent_display", "agent_org", "model_display", "model_org", "date", "display_date", "reasoning_effort"}
)
_DISPLAY_FIELDS = frozenset({"url", "label"})
_DISPLAY_DATE = re.compile(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2}),\s+(\d{4})$")
_MONTHS = {
    name: number
    for number, name in enumerate(
        ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"), 1
    )
}


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    model_id: str
    provider_id: str
    provider_model_id: str
    display_name: str
    model_org: str
    model_org_url: str
    model_url: str
    source_model_id: str
    agent_id: str
    agent_version: str
    agent_display: str
    agent_url: str
    agent_org: str
    agent_org_url: str
    effort: str
    source_filter_effort: str | None
    release_date: str
    filename: str
    source_job_id: str


TERMINAL_BENCH_CANDIDATES = (
    CandidateSpec(
        "sol",
        "openai/gpt-6.1-sol",
        "openai",
        "gpt-6.1-sol",
        "GPT-6.1 Sol",
        "OpenAI",
        "https://openai.com",
        "https://developers.openai.com/api/docs/models/gpt-6.1-sol",
        "openai/gpt-6.1-sol",
        "codex",
        "0.159.0",
        "Codex",
        "https://openai.com/codex/",
        "OpenAI",
        "https://openai.com",
        "max",
        "max",
        "2026-09-29",
        "2026-09-30-openai-gpt-6-1-sol-max-codex.json",
        "3837153f-6673-539d-b3e2-99a6edd3c5db",
    ),
    CandidateSpec(
        "luna",
        "openai/gpt-6-luna",
        "openai",
        "gpt-6-luna",
        "GPT-6 Luna",
        "OpenAI",
        "https://openai.com",
        "https://developers.openai.com/api/docs/models/gpt-6-luna",
        "openai/gpt-6-luna",
        "codex",
        "0.159.0",
        "Codex",
        "https://openai.com/codex/",
        "OpenAI",
        "https://openai.com",
        "max",
        "max",
        "2026-09-22",
        "2026-09-30-openai-gpt-6-luna-max-codex.json",
        "38bcca13-9ed9-5cf2-a864-d777ae4c76d1",
    ),
    CandidateSpec(
        "glm",
        "zhipuai/glm-5.3",
        "zhipuai",
        "glm-5.3",
        "GLM-5.3",
        "Z.ai",
        "https://z.ai",
        "https://docs.z.ai/guides/llm/glm-5.3",
        "anthropic/glm-5.3",
        "claude-code",
        "2.1.207",
        "Claude Code",
        "https://claude.com/product/claude-code",
        "Anthropic",
        "https://www.anthropic.com",
        "max",
        "max",
        "2026-08-14",
        "2026-08-26-anthropic-glm-5-3-max-claude-code.json",
        "18e4ee29-d8b4-516b-b79d-b8bad5bcd5be",
    ),
    CandidateSpec(
        "flash",
        "zhipuai/glm-5.3-flash",
        "zhipuai",
        "glm-5.3-flash",
        "GLM-5.3-Flash",
        "Z.ai",
        "https://z.ai",
        "https://z.ai/blog/glm-5.3-flash",
        "z-ai/glm-5.3-flash",
        "claude-code",
        "2.1.285",
        "Claude Code",
        "https://claude.com/product/claude-code",
        "Anthropic",
        "https://www.anthropic.com",
        "none",
        None,
        "2026-08-26",
        "2026-10-06-z-ai-glm-5-3-flash-none-claude-code.json",
        "e498ef42-3647-58ea-8790-b18f53c18d89",
    ),
)

SOURCES = tuple(
    Source(
        source_id=f"terminal-bench-4:{candidate.candidate_id}",
        reference=f"https://raw.githubusercontent.com/harbor-framework/terminal-bench/{TERMINAL_BENCH_REPOSITORY_PIN}/leaderboard/submissions/{candidate.filename}",
        max_bytes=65_536,
        license=TERMINAL_BENCH_LICENSE,
    )
    for candidate in TERMINAL_BENCH_CANDIDATES
)
_SOURCE_CONFIG = hashlib.sha256(
    json.dumps(
        {
            "sources": repr(SOURCES),
            "candidate_specs": repr(TERMINAL_BENCH_CANDIDATES),
            "dataset": "terminal-bench/terminal-bench",
            "dataset_version": TERMINAL_BENCH_DATASET_VERSION,
            "dataset_ref": TERMINAL_BENCH_DATASET_REF,
            "task_count": TERMINAL_BENCH_TASK_COUNT,
            "min_trials_per_task": TERMINAL_BENCH_MIN_TRIALS_PER_TASK,
            "methodology": _METHOD,
            "apache_contribution_basis": True,
        },
        sort_keys=True,
    ).encode()
).hexdigest()
SCOPE = Applicability(
    "official-terminal-bench-coding-evidence/1",
    "terminal-bench-4.0.0-submissions",
    (
        ("adapter", "terminal-bench-submissions/1"),
        ("repository-pin", TERMINAL_BENCH_REPOSITORY_PIN),
        ("dataset-version", TERMINAL_BENCH_DATASET_VERSION),
        ("dataset-content-ref", TERMINAL_BENCH_DATASET_REF),
        ("source-config-sha256", _SOURCE_CONFIG),
    ),
    frozenset(source.source_id for source in SOURCES),
)


@dataclass(frozen=True)
class SubmissionFacts:
    candidate_id: str
    model_id: str
    display_name: str
    reported_model_id: str
    model_org: str
    model_revision: str
    model_release_date: str
    effort: str
    agent: str
    agent_version: str
    evaluator: str
    source_job_id: str
    successes: int
    trials: int
    accuracy: Decimal
    ci95_half_width: Decimal
    uncached_input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    total_tokens: int
    total_cost_usd: Decimal
    average_trial_seconds: Decimal
    source_reference: str
    source_revision: str
    source_bytes: int
    http_status: int


@dataclass(frozen=True)
class RefreshResult:
    reference: CutReference | None
    submissions: tuple[SubmissionFacts, ...]
    sources: tuple[tuple[str, str | None], ...]
    succeeded: bool


def _object(value: object, source: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in cast(dict[object, object], value)):
        raise ValueError(f"{source}:submission-object")
    return cast(dict[str, object], value)


def _text(value: object, source: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{source}:submission-text")
    return value.strip()


def _integer(value: object, source: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{source}:submission-integer")
    return value


def _decimal(value: object, source: str, *, minimum: Decimal = Decimal(0)) -> Decimal:
    if type(value) is int:
        result = Decimal(value)
    elif isinstance(value, Decimal):
        result = value
    else:
        raise ValueError(f"{source}:submission-decimal")
    if not result.is_finite() or result < minimum:
        raise ValueError(f"{source}:submission-decimal")
    return result


def _date(value: object, source: str) -> date:
    text = _text(value, source)
    try:
        return date.fromisoformat(text)
    except ValueError as error:
        raise ValueError(f"{source}:submission-date") from error


def _job_id(value: object, source: str) -> str:
    text = _text(value, source)
    if text.startswith("https://"):
        parsed = urlsplit(text)
        if (
            parsed.hostname != "hub.harborframework.com"
            or parsed.path.count("/") != 2
            or not parsed.path.startswith("/jobs/")
            or parsed.query
            or parsed.fragment
            or parsed.username
            or parsed.password
        ):
            raise ValueError(f"{source}:submission-job-reference")
        text = parsed.path.rsplit("/", 1)[1]
    try:
        return str(UUID(text))
    except ValueError as error:
        raise ValueError(f"{source}:submission-job-id") from error


def _parse_constant(_value: str) -> object:
    raise ValueError("nonstandard-json-number")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate-json-key")
        result[key] = value
    return result


def _json_document(data: bytes, source: str) -> dict[str, object]:
    try:
        value = json.loads(
            data,
            parse_float=Decimal,
            parse_constant=_parse_constant,
            object_pairs_hook=_unique_object,
        )
    except (UnicodeError, ValueError, RecursionError) as error:
        raise ValueError(f"{source}:submission-json") from error
    return _object(value, source)


def _display_accuracy(accuracy: Decimal, ci95: Decimal) -> str:
    one_decimal = Decimal("0.1")
    shown_accuracy = accuracy.quantize(one_decimal, rounding=ROUND_HALF_UP)
    shown_ci = ci95.quantize(one_decimal, rounding=ROUND_HALF_UP)
    return f"**{shown_accuracy:.1f}%** ± {shown_ci:.1f}%"


def _parse_capture(capture: Capture, candidate: CandidateSpec) -> tuple[ModelClaim, Observation, SubmissionFacts]:
    source_id = capture.source.source_id
    root = _json_document(capture.data, source_id)
    if frozenset(root) != _SUBMISSION_FIELDS:
        raise ValueError(f"{source_id}:submission-schema")

    source_filter = _object(root["source_filter"], source_id)
    if frozenset(source_filter) != _FILTER_FIELDS:
        raise ValueError(f"{source_id}:submission-filter-schema")
    if (
        source_filter["model_name"] != candidate.source_model_id
        or source_filter["agent"] != candidate.agent_id
        or source_filter["agent_version"] != candidate.agent_version
        or source_filter["reasoning_effort"] != candidate.source_filter_effort
    ):
        raise ValueError(f"{source_id}:submission-filter-identity")

    metadata = _object(root["metadata"], source_id)
    if frozenset(metadata) != _METADATA_FIELDS:
        raise ValueError(f"{source_id}:submission-metadata-schema")
    agent_display = _object(metadata["agent_display"], source_id)
    agent_org = _object(metadata["agent_org"], source_id)
    model_display = _object(metadata["model_display"], source_id)
    model_org = _object(metadata["model_org"], source_id)
    for item in (agent_display, agent_org, model_display, model_org):
        if frozenset(item) != _DISPLAY_FIELDS:
            raise ValueError(f"{source_id}:submission-display-schema")
    if (
        agent_display["label"] != candidate.agent_display
        or agent_display["url"] != candidate.agent_url
        or agent_org["label"] != candidate.agent_org
        or agent_org["url"] != candidate.agent_org_url
        or model_display["label"] != candidate.display_name
        or model_display["url"] != candidate.model_url
        or model_org["label"] != candidate.model_org
        or model_org["url"] != candidate.model_org_url
        or metadata["reasoning_effort"] != candidate.effort
    ):
        raise ValueError(f"{source_id}:submission-display-identity")
    release_date = _date(metadata["date"], source_id)
    if release_date.isoformat() != candidate.release_date:
        raise ValueError(f"{source_id}:submission-release-date")
    display_date = _text(metadata["display_date"], source_id)
    date_match = _DISPLAY_DATE.fullmatch(display_date)
    if (
        date_match is None
        or date(int(date_match.group(3)), _MONTHS[date_match.group(1)], int(date_match.group(2))) != release_date
    ):
        raise ValueError(f"{source_id}:submission-display-date")

    jobs = root["source_jobs"]
    if not isinstance(jobs, list):
        raise ValueError(f"{source_id}:submission-job-coverage")
    job_rows = cast(list[object], jobs)
    if len(job_rows) != 1:
        raise ValueError(f"{source_id}:submission-job-coverage")
    job_id = _job_id(job_rows[0], source_id)
    if job_id != candidate.source_job_id:
        raise ValueError(f"{source_id}:submission-job-provenance")

    metrics = _object(root["metrics"], source_id)
    if frozenset(metrics) != _METRIC_FIELDS:
        raise ValueError(f"{source_id}:submission-metric-schema")
    accuracy = _decimal(metrics["accuracy"], source_id)
    ci95 = _decimal(metrics["accuracy_ci95_half_width"], source_id)
    trials = _integer(metrics["n_trials"], source_id, minimum=1)
    successes = _integer(metrics["successes"], source_id)
    if successes > trials or trials != TERMINAL_BENCH_TRIAL_COUNT or accuracy > Decimal(100) or ci95 > Decimal(100):
        raise ValueError(f"{source_id}:submission-metric-range")
    expected_accuracy = (Decimal(successes) * Decimal(100) / Decimal(trials)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    if accuracy != expected_accuracy or metrics["display_accuracy"] != _display_accuracy(accuracy, ci95):
        raise ValueError(f"{source_id}:submission-accuracy-mismatch")
    pass_rates = tuple(_decimal(metrics[f"pass_at_{count}"], source_id) for count in range(2, 6))
    if any(value > 1 for value in pass_rates):
        raise ValueError(f"{source_id}:submission-pass-rate")
    uncached = _integer(metrics["uncached_input_tokens"], source_id)
    cached = _integer(metrics["cached_input_tokens"], source_id)
    output_tokens = _integer(metrics["output_tokens"], source_id)
    total_tokens = _integer(metrics["total_tokens"], source_id)
    if uncached + output_tokens != total_tokens:
        raise ValueError(f"{source_id}:submission-token-total")
    _ = _text(metrics["display_total_tokens"], source_id)
    total_cost = _decimal(metrics["total_cost_usd"], source_id)
    _ = _text(metrics["display_cost"], source_id)
    _ = _text(metrics["display_total_cost_usd"], source_id)
    average_duration = _decimal(metrics["avg_trial_duration_sec"], source_id)

    disqualified = root["disqualified_trials"]
    if not isinstance(disqualified, list) or disqualified:
        raise ValueError(f"{source_id}:unsupported-disqualified-trials")
    trial_ids = root["trials"]
    if not isinstance(trial_ids, list):
        raise ValueError(f"{source_id}:submission-trial-coverage")
    trial_rows = cast(list[object], trial_ids)
    if len(trial_rows) != trials:
        raise ValueError(f"{source_id}:submission-trial-coverage")
    normalized_trial_ids = tuple(_job_id(trial_id, source_id) for trial_id in trial_rows)
    if len(set(normalized_trial_ids)) != trials:
        raise ValueError(f"{source_id}:submission-trial-identity")

    observation_id = source_id + ":" + capture.revision.removeprefix("content-sha256:")
    observation = Observation(
        observation_id,
        source_id,
        "official",
        "measurement",
        capture.source.reference,
        capture.acquired_at,
        "public",
        capture.source.license,
        observed_at=capture.acquired_at,
    )
    model = Model(
        candidate.model_id,
        candidate.provider_id,
        candidate.provider_model_id,
        configuration=(("reasoning_effort", candidate.effort),),
    )
    methodology = (
        "Resolution rate: accuracy = 100*successful selected trials/n_trials; "
        "reward > 0 is success; official 95% CI half-width is "
        f"{ci95} percentage points via the per-task SE and z=1.96 method"
    )
    configuration = "; ".join(
        (
            f"reported_model_id={candidate.source_model_id}",
            f"model_org={candidate.model_org}",
            f"model_org_url={candidate.model_org_url}",
            f"model_url={candidate.model_url}",
            f"model_release_date={release_date.isoformat()}",
            "model_revision=UNKNOWN",
            f"agent={candidate.agent_display}",
            f"agent_version={candidate.agent_version}",
            f"reasoning_effort={candidate.effort}",
            f"dataset=terminal-bench/terminal-bench@{TERMINAL_BENCH_DATASET_VERSION}",
            f"dataset_ref={TERMINAL_BENCH_DATASET_REF}",
            f"tasks={TERMINAL_BENCH_TASK_COUNT}",
            f"selected_trials={trials}",
            f"successes={successes}",
            f"agent_url={candidate.agent_url}",
            f"agent_org={candidate.agent_org}",
            f"agent_org_url={candidate.agent_org_url}",
            f"source_job=https://hub.harborframework.com/jobs/{job_id}",
            "evaluation_date=UNKNOWN in the versioned submission JSON",
        )
    )
    payload = Benchmark(
        "Terminal-Bench",
        TERMINAL_BENCH_DATASET_VERSION,
        methodology,
        configuration,
        accuracy,
        "percent",
    )
    claim_id = observation_id + ":claim:" + hashlib.sha256(repr((model, payload)).encode()).hexdigest()
    claim = ModelClaim(
        model,
        payload,
        claim_id=claim_id,
        observation_id=observation_id,
        effective_from=capture.acquired_at,
    )
    facts = SubmissionFacts(
        candidate.candidate_id,
        candidate.model_id,
        candidate.display_name,
        candidate.source_model_id,
        candidate.model_org,
        "UNKNOWN",
        release_date.isoformat(),
        candidate.effort,
        candidate.agent_display,
        candidate.agent_version,
        "Terminal-Bench official submission pipeline and verifier",
        job_id,
        successes,
        trials,
        accuracy,
        ci95,
        uncached,
        cached,
        output_tokens,
        total_tokens,
        total_cost,
        average_duration,
        capture.source.reference,
        capture.revision,
        len(capture.data),
        capture.http_status,
    )
    return claim, observation, facts


def normalize_with_receipt(
    captures: tuple[Capture, ...], *, at: datetime, previous: PublicEvidence | None = None
) -> tuple[PublicEvidence, tuple[SubmissionFacts, ...]]:
    at = instant(at)
    if len(captures) != len(SOURCES) or {capture.source for capture in captures} != set(SOURCES):
        raise ValueError("incomplete-or-unexpected-terminal-bench-generation")
    if previous is not None and previous.applicability != SCOPE:
        raise ValueError("terminal-bench-source-adapter-migration-required")
    captures_by_id = {capture.source.source_id: capture for capture in captures}
    claims = {} if previous is None else {claim.claim_id: claim for claim in previous.evidence.claims}
    observations = {} if previous is None else {item.observation_id: item for item in previous.evidence.observations}
    revisions = {} if previous is None else dict(previous.revisions)
    facts: list[SubmissionFacts] = []
    for candidate, source in zip(TERMINAL_BENCH_CANDIDATES, SOURCES, strict=True):
        claim, observation, fact = _parse_capture(captures_by_id[source.source_id], candidate)
        old_claim = claims.get(claim.claim_id)
        if old_claim is not None:
            if replace(claim, effective_from=old_claim.effective_from) != old_claim:
                raise ValueError(f"{source.source_id}:claim-identity-conflict")
        else:
            claims[claim.claim_id] = claim
        old_observation = observations.get(observation.observation_id)
        if old_observation is not None:
            preserved = replace(
                observation,
                retrieved_at=old_observation.retrieved_at,
                observed_at=old_observation.observed_at,
            )
            if preserved != old_observation:
                raise ValueError(f"{source.source_id}:observation-identity-conflict")
        else:
            observations[observation.observation_id] = observation
            revisions[observation.observation_id] = captures_by_id[source.source_id].revision
        facts.append(fact)
    evidence = (
        previous.evidence.extend(observations=tuple(observations.values()), claims=tuple(claims.values()))
        if previous is not None
        else Evidence(tuple(observations.values()), tuple(claims.values()))
    )
    return PublicEvidence(SCOPE, evidence, tuple(sorted(revisions.items()))), tuple(facts)


def normalize(captures: tuple[Capture, ...], *, at: datetime, previous: PublicEvidence | None = None) -> PublicEvidence:
    return normalize_with_receipt(captures, at=at, previous=previous)[0]


def compare(
    coding_public: PublicEvidence,
    terminal_public: PublicEvidence,
    submissions: tuple[SubmissionFacts, ...],
) -> dict[str, object]:
    if coding_public.applicability != CODING_SCOPE or terminal_public.applicability != SCOPE:
        raise ValueError("coding-comparison-scope")
    by_candidate = {item.candidate_id: item for item in submissions}
    if set(by_candidate) != {candidate.candidate_id for candidate in TERMINAL_BENCH_CANDIDATES}:
        raise ValueError("incomplete-terminal-bench-comparison")
    deepswe = compare_coding(coding_public)
    entries: list[dict[str, object]] = []
    for candidate in TERMINAL_BENCH_CANDIDATES:
        fact = by_candidate[candidate.candidate_id]
        claims = [
            claim
            for claim in terminal_public.evidence.claims
            if isinstance(claim, ModelClaim)
            and claim.subject.model_id == candidate.model_id
            and isinstance(claim.payload, Benchmark)
            and claim.payload.name == "Terminal-Bench"
        ]
        if len(claims) != 1:
            raise ValueError(f"{candidate.candidate_id}:terminal-bench-comparison-evidence")
        claim = claims[0]
        observation = next(
            item for item in terminal_public.evidence.observations if item.observation_id == claim.observation_id
        )
        assert isinstance(claim.payload, Benchmark)
        entries.append(
            {
                "candidate_id": candidate.candidate_id,
                "model": candidate.display_name,
                "model_id": candidate.model_id,
                "reported_model_id": fact.reported_model_id,
                "model_org": fact.model_org,
                "model_revision": fact.model_revision,
                "effort": fact.effort,
                "agent": fact.agent,
                "agent_version": fact.agent_version,
                "evaluator": fact.evaluator,
                "benchmark": claim.payload.name,
                "version": claim.payload.version,
                "metric": "resolution rate (official field accuracy)",
                "value_percent": str(claim.payload.value),
                "ci95_half_width_percentage_points": str(fact.ci95_half_width),
                "successes": fact.successes,
                "selected_trials": fact.trials,
                "task_count": TERMINAL_BENCH_TASK_COUNT,
                "trials_per_task": TERMINAL_BENCH_MIN_TRIALS_PER_TASK,
                "higher_is_better": True,
                "model_release_date": fact.model_release_date,
                "evaluation_date": "UNKNOWN in the pinned submission JSON; Hub links identify source jobs",
                "configuration": claim.payload.configuration,
                "methodology": claim.payload.methodology,
                "source_authority": observation.authority,
                "source_reference": observation.reference,
                "source_revision": dict(terminal_public.revisions)[observation.observation_id],
                "comparability": _comparability(candidate.candidate_id),
            }
        )
    resource_receipt = [
        {
            "candidate_id": fact.candidate_id,
            "source_token_total": fact.total_tokens,
            "uncached_input_tokens": fact.uncached_input_tokens,
            "cached_input_tokens_reported_separately": fact.cached_input_tokens,
            "output_tokens": fact.output_tokens,
            "source_reported_job_cost_usd": str(fact.total_cost_usd),
            "cost_basis": (
                "sum of selected trials' Harbor cost_usd telemetry; billing/subscription basis not established"
            ),
            "source_reference": fact.source_reference,
            "source_revision": fact.source_revision,
            "http_status": fact.http_status,
            "bytes": fact.source_bytes,
        }
        for fact in submissions
    ]
    return {
        "existing_coding_benchmark_evidence": deepswe,
        "terminal_bench_dataset": {
            "name": "terminal-bench/terminal-bench",
            "version": TERMINAL_BENCH_DATASET_VERSION,
            "dataset_ref": TERMINAL_BENCH_DATASET_REF,
            "task_count": TERMINAL_BENCH_TASK_COUNT,
            "minimum_trials_per_task": TERMINAL_BENCH_MIN_TRIALS_PER_TASK,
            "source_revision": TERMINAL_BENCH_REPOSITORY_PIN,
            "rights": (
                "Apache-2.0 for selected submission contributions; no raw Hub trial payloads or task content copied"
            ),
        },
        "terminal_bench_observations": entries,
        "resource_receipt": resource_receipt,
        "scenario": (
            "Autonomous Kilo coding task: diagnose a repository defect, implement a fix, run tests and prepare a PR."
        ),
        "relevance": (
            "Terminal-Bench is a repository-task agent benchmark, but its harness, effort "
            "and trial setup are not a Kilo run."
        ),
        "conclusion": (
            "Observations are configuration-specific. Sol/Luna share a Codex version/effort; "
            "GLM uses Claude Code with different versions/efforts. Confidence intervals are "
            "descriptive, not pairwise winner tests. No Router rating or global ranking is inferred."
        ),
    }


def _comparability(candidate_id: str) -> str:
    if candidate_id == "sol":
        return (
            "same source benchmark/task version, Codex 0.159.0 and max effort; "
            "not evidence for Kilo Sol High or its harness"
        )
    if candidate_id == "luna":
        return (
            "same source benchmark/task version, Codex 0.159.0 and max effort; "
            "Kilo Luna Max harness/configuration is not established"
        )
    if candidate_id == "glm":
        return (
            "not directly comparable with other candidates: Claude Code/max; raw model route "
            "id is anthropic/glm-5.3 while metadata identifies Z.ai"
        )
    return "not directly comparable with GLM-5.3: Claude Code version 2.1.285 and no-effort setting differ"


def _source_error(error: Exception) -> str:
    code = error.args[0] if error.args else None
    return code if isinstance(code, str) and ":" not in code else "source-validation-failed"


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
    previous = retained(directory, max_bytes=max_artifact_bytes)
    last_successful = None
    if previous is not None:
        last_successful = decode_cut(
            previous[0],
            previous[1],
            supported_payload_schemas=frozenset({previous[1].payload_schema}),
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
                "last_successful_publication_at": last_successful,
                "freshness_policy": "No automatic freshness or evaluation date is inferred.",
                "remediation": None
                if succeeded
                else "Inspect the source diagnostics; retain the previous publication.",
                "sources": sources,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode(),
    )


def refresh(
    directory: Path,
    *,
    at: datetime,
    max_artifact_bytes: int,
    timeout: float,
) -> tuple[CutReference | None, RefreshResult]:
    """Acquire only the four pinned official submission summaries and publish all or none."""
    at = instant(at)
    if type(max_artifact_bytes) is not int or max_artifact_bytes < 1:
        raise ValueError("invalid-artifact-size-policy")
    directory.mkdir(parents=True, exist_ok=True)
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
            diagnostic = _source_error(error)
            health.append(
                {
                    "source_id": source.source_id,
                    "reference": source.reference,
                    "retrieved": False,
                    "revision": None,
                    "bytes_received": None,
                    "diagnostic": diagnostic,
                    "remediation": "Inspect the pinned official submission source; do not shrink candidate coverage.",
                }
            )
    if len(captures) != len(SOURCES):
        active = prior[1] if prior is not None else None
        _write_status(directory, at, active, False, "retrieval", health, max_artifact_bytes, "source-retrieval-failed")
        return active, RefreshResult(
            active,
            (),
            tuple((str(row["source_id"]), cast(str | None, row["diagnostic"])) for row in health),
            False,
        )
    try:
        public, submissions = normalize_with_receipt(tuple(captures), at=at, previous=previous)
        reference = publish(directory, public, expected=SCOPE, produced_at=at, max_bytes=max_artifact_bytes)
    except (ValueError, OSError) as error:
        diagnostic = _source_error(error)
        health = [
            dict(
                row,
                diagnostic=diagnostic,
                remediation="Inspect the pinned candidate identity, license basis and official submission schema.",
            )
            for row in health
        ]
        active = prior[1] if prior is not None else None
        _write_status(directory, at, active, False, "normalization", health, max_artifact_bytes, diagnostic)
        return active, RefreshResult(
            active,
            (),
            tuple((str(row["source_id"]), cast(str | None, row["diagnostic"])) for row in health),
            False,
        )
    _write_status(directory, at, reference, True, "complete", health, max_artifact_bytes)
    return reference, RefreshResult(
        reference,
        submissions,
        tuple((source.source_id, None) for source in SOURCES),
        True,
    )
