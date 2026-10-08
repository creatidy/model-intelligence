"""Pinned pure Router-field proof, not raw MI adoption or a production MI mapper."""

import importlib
import json
import sys
from collections.abc import Callable
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import cast

ROUTER_PIN = "5c48d51f1eb1f11424a5100eb2ccf20a6cba4581"
KERNEL_PIN = "19775b9679cf04f071e4fe5f2542fe230272ea36"


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
    import test_native_evidence as fixture

    from model_intelligence.contract import (
        NATIVE_PAYLOAD_SCHEMA,
        SourceNotice,
        decode_public_evidence,
        encode_public_evidence,
    )
    from model_intelligence.evidence import Model, NativeLimit
    from model_intelligence.projection import effective_at

    types = importlib.import_module("scarcity_router.selection_types")
    matcher = importlib.import_module("scarcity_router.selector")
    call = constructor
    subject = replace(fixture.SUBJECT, provider_id="zai")

    def owned_router_projection(public: fixture.PublicEvidence, expected: Model) -> int | str:
        """Research-only prospective Router adapter; never a shipped MI decision."""
        if expected.configuration is None or dict(expected.configuration).get("reasoning_effort") != "none":
            return "unknown-or-unsupported-effort"
        view = effective_at(public.evidence, fixture.T)
        rows = tuple(row for row in view.models if row.subject == expected and isinstance(row.payload, NativeLimit))
        if not rows:
            return "incompatible-or-missing-subject"
        members = {"statement:" + row.claim_id for row in rows}
        if any(
            members & notice.targets and notice.action == "revocation" for notice in public.active_notices(fixture.T)
        ):
            return "source-retracted-or-revoked"
        if view.conflicts:
            return "conflicting-evidence"
        observations = {item.observation_id: item for item in public.evidence.observations}
        values: set[int] = set()
        for row in rows:
            assert isinstance(row.payload, NativeLimit)
            value = row.payload
            observed = observations[row.observation_id]
            if observed.source_id != "owned-source" or observed.retrieved_at > fixture.T:
                return "unadmitted-source-or-future-acquisition"
            if observed.fresh_until is None or observed.stale(fixture.T):
                return "unknown-or-stale-freshness"
            if (
                value.dimension != "owned.input"
                or value.meaning != "input-allowance"
                or value.unit != "tokens"
                or value.basis != "owned-declared-scope"
                or value.assertion != "advertised"
            ):
                return "incompatible-native-semantics"
            amount = value.amount
            # This is an explicitly owned test policy bound, not a model/global limit.
            if amount is None or amount <= 0 or amount > Decimal("4096") or amount != amount.to_integral_value():
                return "unknown-or-unrepresentable-value"
            values.add(int(amount))
        return next(iter(values)) if len(values) == 1 else "conflicting-evidence"

    public = fixture.cut(fixture.claim(subject=subject, limit=replace(fixture.LIMIT, amount=Decimal("4096"))))
    data, reference = encode_public_evidence(public, produced_at=fixture.T, payload_schema=NATIVE_PAYLOAD_SCHEMA)
    admitted = decode_public_evidence(data, reference, max_bytes=65536)
    projected = owned_router_projection(admitted, subject)
    assert projected == 4096
    identity = method(types.ModelIdentity, "from_dict")(
        {"provider": "zai", "model": "owned-alias", "variant": "opaque-max"}
    )
    unknown = call(types.CapabilityAssessment)(rating=None)
    capabilities = call(types.CapabilityAssessments)(unknown, unknown, unknown, unknown, unknown, unknown)
    constraints = call(types.HardConstraints)(minimum_input_context_tokens=128)
    passed = 0
    for amount, reason in ((projected, None), (64, "insufficient"), (None, "unknown")):
        entry = call(types.ModelCatalogEntry)(
            identity=identity,
            display_name="Owned original fixture",
            hard_properties=call(types.ModelHardProperties)(input_context_tokens=amount, supports_reasoning_mode=True),
            capabilities=capabilities,
            capacity_bindings=None,
            reasoning_effort="none",
        )
        failures = cast(tuple[object, ...], method(matcher, "evaluate_hard_constraints")(constraints, entry))
        assert tuple(field(item, "reason") for item in failures) == (() if reason is None else (reason,))
        passed += 1
    for changed in (
        replace(subject, provider_model_id="other-alias"),
        replace(subject, channel="plan-managed"),
        replace(subject, revision="other-revision"),
        replace(subject, interface_version="2.0"),
    ):
        assert owned_router_projection(admitted, changed) == "incompatible-or-missing-subject"
        passed += 1
    for configuration in (
        None,
        (),
        (("reasoning_effort", None),),
        (("variant", "max"),),
        (("reasoning_effort", "unsupported"),),
    ):
        assert (
            owned_router_projection(admitted, replace(subject, configuration=configuration))
            == "unknown-or-unsupported-effort"
        )
        passed += 1
    for value in (
        replace(fixture.LIMIT, meaning="total-context-window"),
        replace(fixture.LIMIT, meaning="execution-ceiling"),
        replace(fixture.LIMIT, unit="characters"),
        replace(fixture.LIMIT, basis=None),
    ):
        assert (
            owned_router_projection(fixture.cut(fixture.claim(subject=subject, limit=value)), subject)
            == "incompatible-native-semantics"
        )
        passed += 1
    for amount in (None, Decimal("1.5"), Decimal(0), Decimal("1e1000000")):
        assert (
            owned_router_projection(
                fixture.cut(fixture.claim(subject=subject, limit=replace(fixture.LIMIT, amount=amount))), subject
            )
            == "unknown-or-unrepresentable-value"
        )
        passed += 1
    for expiry in (None, fixture.T):
        changed = replace(
            admitted,
            evidence=replace(
                admitted.evidence,
                observations=tuple(
                    replace(item, fresh_until=expiry) if item.observation_id == "native" else item
                    for item in admitted.evidence.observations
                ),
            ),
        )
        assert owned_router_projection(changed, subject) == "unknown-or-stale-freshness"
        passed += 1
    conflicted = fixture.cut(
        fixture.claim(subject=subject, limit=replace(fixture.LIMIT, amount=Decimal(4096))),
        fixture.claim("disagreement", subject=subject, limit=replace(fixture.LIMIT, amount=Decimal(2048))),
    )
    assert owned_router_projection(conflicted, subject) == "conflicting-evidence"
    passed += 1
    withdrawn = replace(
        admitted,
        notices=(SourceNotice("withdrawal", "native", frozenset({"statement:native"}), fixture.T, "revocation", None),),
    )
    assert owned_router_projection(withdrawn, subject) == "source-retracted-or-revoked"
    passed += 1
    # Existing consumer constructors reject the raw producer grammar; no adoption claim.
    try:
        method(types.ModelHardProperties, "from_dict")(json.loads(data))
    except Exception as error:
        assert type(error).__name__ == "SelectionContractValidationError"
    else:
        raise AssertionError("raw MI grammar was treated as hard properties")
    print(
        json.dumps(
            {
                "router_pin": ROUTER_PIN,
                "kernel_pin": KERNEL_PIN,
                "cases_passed": passed,
                "raw_mi_adoption": False,
                "installed_acceptance": False,
                "live_execution": False,
                "production_mi_mapping": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
