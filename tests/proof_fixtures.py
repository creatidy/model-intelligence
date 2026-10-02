"""Invented values and exact boundaries, NOT redistributed data or current market claims.

Concept references inspected for the proof (no copied code/data):
models.dev catalog/provider identities and benchmark context; genai-prices temporal
pricing; codingplan measured/estimated/unknown terms. Official shape references:
https://docs.z.ai/devpack/notice/event-glm-5.3-flash.md
https://docs.z.ai/devpack/notice/usage-revision.md
https://github.com/zai-org/ZCode/tree/29628c9acdb81b703bbd4080c207a0e7ce5e276e
Official campaign date wording does not specify exact boundary instants. These
fixtures deliberately supply exact synthetic boundaries and a synthetic version.
"""

from dataclasses import replace
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

from model_intelligence.domain import (
    Assertion,
    Authority,
    Benchmark,
    Capability,
    DailyWindow,
    Distribution,
    Evidence,
    ExecutionFact,
    IdentityMode,
    ModelFact,
    OfferRule,
    Price,
    Snapshot,
    Source,
    Validity,
)

LEARNED = datetime(2026, 9, 1, tzinfo=UTC)
START = datetime(2026, 9, 3, 15, tzinfo=UTC)  # 23:00 Singapore, fixture convention
END = datetime(2026, 10, 7, 1, tzinfo=UTC)  # 09:00 Singapore, fixture convention
BEFORE = START - timedelta(microseconds=1)
DURING = START + timedelta(hours=1)


def evidence(source_id: str = "fixture-primary", *, bounded: bool = False) -> Evidence:
    source = Source(
        source_id,
        Authority.SYNTHETIC,
        f"fixture:{source_id}",
        LEARNED,
        LEARNED,
        Distribution.SYNTHETIC,
    )
    return Evidence(source, Validity(START, END) if bounded else Validity(LEARNED))


def model() -> ModelFact:
    return ModelFact(
        model_id="z-ai:glm-5.3-flash",
        provider="z.ai",
        provider_model_id="glm-5.3-flash",
        capabilities=("text", "tool-use"),
        benchmark=Benchmark(
            "fixture-code-bench", "1.0", "pass@1", "harness=fixture-1; temperature=0", Decimal("80"), "%"
        ),
        price=Price(Decimal("0.10"), Decimal("0.30"), "USD"),
        evidence=evidence(),
    )


def disagreement() -> ModelFact:
    return replace(
        model(), price=Price(Decimal("0.20"), Decimal("0.30"), "USD"), evidence=evidence("fixture-secondary")
    )


def promotion() -> OfferRule:
    return OfferRule(
        plan_id="z.ai:coding-lite",
        generation="fixture-credits-v3",
        promotion_id="fixture-night-promotion",
        monthly_price=Decimal("18"),
        currency="USD",
        quota_multiplier=Decimal("2"),
        quota_basis="available public plan credits relative to baseline; NOT API price or remaining user credits",
        conditions=(
            "paid plan",
            "GLM-5.3-Flash requested",
            "supported non-ZCode agent",
            "baseline quota not exhausted",
        ),
        composable_with=(),
        window=DailyWindow("Asia/Singapore", time(23), time(9)),
        evidence=evidence(bounded=True),
    )


def execution(
    capability: Capability = Capability.HEADLESS,
    assertion: Assertion = Assertion.ADVERTISED,
    supported: bool | None = True,
) -> ExecutionFact:
    return ExecutionFact(
        "z.ai:zcode-cli",
        "fixture-3.14.x",
        capability,
        assertion,
        supported,
        IdentityMode.PROVIDER_MANAGED,
        None,
        evidence(),
    )


def surfaces() -> tuple[ExecutionFact, ...]:
    return (
        execution(),
        execution(Capability.HEADLESS, Assertion.OBSERVED, False),
        execution(Capability.STRUCTURED_OUTPUT),  # CLI JSON events, not schema-constrained answers
        execution(Capability.STRUCTURED_OUTPUT, Assertion.OBSERVED, False),
        execution(Capability.WORKSPACE_READ),
        execution(Capability.WORKSPACE_EDIT),
        execution(Capability.MODEL_DISCOVERY),
        execution(Capability.MODEL_SELECTION, Assertion.SELECTABLE),
        execution(Capability.REASONING_STEERING, Assertion.SELECTABLE),
        execution(Capability.PHYSICAL_MODEL_OBSERVABILITY, Assertion.OBSERVED, None),
        execution(Capability.PHYSICAL_MODEL_ENFORCEABILITY, Assertion.ENFORCEABLE, False),
    )


def proof_snapshots() -> tuple[Snapshot, Snapshot, Snapshot]:
    initial = (model(), promotion(), *surfaces())
    n = Snapshot(1, BEFORE, initial)
    n_plus_one = Snapshot(2, DURING, (*initial, disagreement()))
    changed = tuple(
        replace(fact, supported=True)
        if isinstance(fact, ExecutionFact)
        and fact.capability == Capability.STRUCTURED_OUTPUT
        and fact.assertion == Assertion.OBSERVED
        else fact
        for fact in n_plus_one.facts
    )
    expired = Snapshot(3, END, changed)
    return n, n_plus_one, expired
