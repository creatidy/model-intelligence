"""Exact-pin offline matching proof; no selector/ranker, HTTP or consumer installation.

Arguments are read-only Router archive/object repo and Kernel archive/object repo.
Run with the documented allowlisted environment and -I -S -B.
"""

import importlib
import json
import sys
from collections.abc import Callable
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import cast
from unittest.mock import patch

ROUTER_PIN = "1dae1948f372e0f1739896655bb7db97d6b08460"
KERNEL_PIN = "9dfa20931a46931d1e97d1f0efddcf2692afb7a7"


def method(value: object, name: str) -> Callable[..., object]:
    return cast(Callable[..., object], getattr(value, name))


def constructor(value: object) -> Callable[..., object]:
    return cast(Callable[..., object], value)


def field(value: object, name: str) -> object:
    return getattr(value, name)


def main() -> None:
    if len(sys.argv) != 5:
        raise ValueError("four-source-arguments-required")
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "tests"))
    from verify_router_consumers import install_guard, verify_sources

    router, router_git, kernel, kernel_git = (Path(value).resolve() for value in sys.argv[1:])
    verify_sources(router, router_git, ROUTER_PIN, "scarcity_router")
    verify_sources(kernel, kernel_git, KERNEL_PIN, "src/creatidy_kernel")
    install_guard(root, router, kernel)
    import test_capability_boundary as fixture

    from model_intelligence.utilization import decode_decision_utilization, encode_utilization

    types = importlib.import_module("scarcity_router.selection_types")
    matcher = importlib.import_module("scarcity_router.selector")
    resources = importlib.import_module("creatidy_kernel.core.resources")
    parser = importlib.import_module("creatidy_kernel.adapters.scarcity_router")
    allocations = importlib.import_module("creatidy_kernel.ports.allocation")
    call = constructor
    passed = 0
    unknown = call(types.CapabilityAssessment)(rating=None)
    capabilities = call(types.CapabilityAssessments)(unknown, unknown, unknown, unknown, unknown, unknown)
    requirement = fixture.narrow_requirement()
    request = call(resources.ResourceRequest)("owned-work", frozenset({"reference"}), 128)
    assert field(request, "context_tokens") == 128
    typed_requirement = method(types.TaskRequirement, "from_dict")(requirement)
    assert method(typed_requirement, "to_dict")() == requirement
    data, cut = fixture.framed_record(fixture.record_payload())
    limits = fixture.admitted_limits(data, cut)
    amount = fixture.project_limit(limits, fixture.SUBJECT, "input_context_tokens")
    for rows, diagnostic in (
        ((), "missing-compatible-evidence"),
        ((replace(fixture.INPUT, amount=None),), "unknown-limit"),
        (
            (replace(fixture.INPUT, observation=replace(fixture.INPUT.observation, fresh_until=None)),),
            "unknown-freshness",
        ),
        (
            (replace(fixture.INPUT, observation=replace(fixture.INPUT.observation, fresh_until=fixture.T)),),
            "stale-evidence",
        ),
        ((fixture.INPUT, replace(fixture.INPUT, identity="conflict", amount=Decimal("512"))), "conflicting-evidence"),
    ):
        rejected_data, rejected_ref = fixture.framed_record(fixture.record_payload(limits=rows))
        try:
            fixture.project_limit(
                fixture.admitted_limits(rejected_data, rejected_ref), fixture.SUBJECT, "input_context_tokens"
            )
        except ValueError as error:
            assert str(error) == diagnostic
        else:
            raise AssertionError("negative public artifact reached matching")
        passed += 1
    identity = method(types.ModelIdentity, "from_dict")(
        {"provider": "zai", "model": "owned-model", "variant": "opaque"}
    )
    for known in (amount, 64, None):
        entry = call(types.ModelCatalogEntry)(
            identity=identity,
            display_name="Owned research only",
            hard_properties=call(types.ModelHardProperties)(input_context_tokens=known, supports_tool_use=True),
            capabilities=capabilities,
            capacity_bindings=None,
        )
        failures = method(matcher, "evaluate_hard_constraints")(field(typed_requirement, "hard_constraints"), entry)
        reasons = tuple(field(failure, "reason") for failure in cast(tuple[object, ...], failures))
        assert reasons == (() if known == amount else ("insufficient",) if known == 64 else ("unknown",))
        passed += 1
    # No ranking: one preauthorized candidate, using the real pure hard matcher above.
    utilized_cuts: set[str] = set()
    for effort in ("none", "ultra"):
        subject = replace(fixture.SUBJECT, configuration=(("effort", effort), ("opaque-variant", "opaque")))
        data, cut = fixture.framed_record(fixture.record_payload(subject))
        limits = fixture.admitted_limits(data, cut, subject)
        amount = fixture.project_limit(limits, subject, "input_context_tokens")
        utilized_cuts.add(cut.sha256)
        entry = call(types.ModelCatalogEntry)(
            identity=identity,
            display_name="Owned research only",
            hard_properties=call(types.ModelHardProperties)(
                input_context_tokens=amount, supports_tool_use=True, supports_reasoning_mode=True
            ),
            capabilities=capabilities,
            capacity_bindings=None,
            reasoning_effort=effort,
        )
        context = fixture.canonical(
            {
                "mapping_version": fixture.RESEARCH_VERSION,
                "requirement": requirement,
                "local_calibration": "owned-reviewed",
                "local_binding": "owned-preauthorized",
                "reasoning_effort": effort,
                "matching_entry": method(entry, "to_dict")(),
            }
        )
        assert not method(matcher, "evaluate_hard_constraints")(field(typed_requirement, "hard_constraints"), entry)
        candidate = call(matcher.CandidateEvaluation)(
            identity=identity,
            display_name=f"Owned admitted input={amount}",
            eligible=True,
            reasoning_effort=field(entry, "reasoning_effort"),
            capability_margin=0,
        )
        decision = call(matcher.SelectionDecision)(
            evaluated_at=fixture.T,
            requirement=typed_requirement,
            catalog_version=1,
            catalog_updated_on="2026-01-01",
            selector_mode="balanced",
            resource_policy_version=1,
            selected=candidate,
            reason_codes=("selected_balanced",),
        )
        result = method(decision, "to_dict")()
        decision_bytes = fixture.canonical(result)
        manifest, reference = encode_utilization(cut, evaluated_at=fixture.T, decision=decision_bytes, context=context)
        envelope = fixture.canonical({"schema_version": 1, "decision": result, "mi_utilization": reference})
        checked, provenance = cast(
            tuple[object, str], method(parser, "_decision")(method(parser, "_parse")(envelope), requirement)
        )
        assert checked == result
        assert (
            decode_decision_utilization(
                manifest,
                response=provenance.encode(),
                expected_cut=cut,
                evaluated_at=fixture.T,
                decision=decision_bytes,
                context=context,
                max_bytes=65536,
            ).cut
            == cut
        )
        allocation = call(resources.Allocation)(
            runtime_id="owned-runtime",
            provider_id="zai",
            model_id="owned-model",
            capabilities=frozenset({"reference"}),
            context_tokens=amount,
            rationale="Owned fixture",
            reasoning_effort=effort,
            variant="opaque",
            decision_provenance=provenance,
        )
        assert (
            method(allocations, "decode_allocation")(method(allocations, "encode_allocation")(allocation)) == allocation
        )
        allocator = call(parser.ScarcityRouterAllocator)(
            base_url="https://example.invalid", runtime_bindings=(allocation,)
        )

        def owned_exchange(_self: object, emitted: dict[str, object], response: bytes = envelope) -> bytes:
            assert emitted == requirement  # Actual narrow Kernel translation, not rich intake.
            return response

        with patch.object(parser.ScarcityRouterAllocator, "_exchange", new=owned_exchange):
            received = method(allocator, "select")(request)
        assert field(received, "decision_provenance") == provenance
        assert field(received, "reasoning_effort") == effort
        passed += 1
    assert len(utilized_cuts) == 2
    # Unconfigured effort is only a DTO case; it gets no mapped limit or MI receipt.
    unknown_subject = replace(fixture.SUBJECT, configuration=(("effort", None), ("opaque-variant", "opaque")))
    unknown_data, unknown_cut = fixture.framed_record(fixture.record_payload(unknown_subject))
    try:
        fixture.project_limit(
            fixture.admitted_limits(unknown_data, unknown_cut, unknown_subject), unknown_subject, "input_context_tokens"
        )
    except ValueError as error:
        assert str(error) == "unknown-applicability"
    else:
        raise AssertionError("unknown effort obtained a mapped limit")
    unconfigured = call(matcher.CandidateEvaluation)(
        identity=identity,
        display_name="Unconfigured serialization only",
        eligible=True,
        reasoning_effort=None,
        capability_margin=0,
    )
    assert cast(dict[str, object], method(unconfigured, "to_dict")())["reasoning_effort"] is None
    passed += 1
    # Public benchmarks are not a calibration conversion; unknown quality still fails.
    minima = method(types.CapabilityMinima, "from_dict")({"coding": 5})
    failures = cast(
        tuple[object, ...],
        method(matcher, "evaluate_capability_sufficiency")(minima, capabilities),
    )
    assert len(failures) == 1 and field(failures[0], "reason") == "unknown"
    passed += 1
    print(
        json.dumps(
            {
                "router_pin": ROUTER_PIN,
                "kernel_pin": KERNEL_PIN,
                "pure_cases_passed": passed,
                "installed_acceptance": False,
                "rich_kernel_requirement_producer": False,
                "production_mapping_accepted": False,
                "router_emits_mi_reference": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
