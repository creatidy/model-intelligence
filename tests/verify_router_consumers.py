"""Supplemental exact-pin pure-parser conformance; not routing or installed acceptance.

Run with an empty allowlisted environment, -I -B, and read-only git-archive sources.
Arguments: router source, router object repo, kernel source, kernel object repo.
"""

import hashlib
import importlib
import json
import os
import subprocess
import sys
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Protocol, cast

ROUTER_PIN = "6c337a400b4cdc28ded543d2ae8ccf3749d79cb7"
KERNEL_PIN = "5048c5cef95e546377d5e20baeae16b99b1bd088"
_read_roots: tuple[Path, ...] = ()


class AttemptShape(Protocol):
    @property
    def digest(self) -> str: ...

    @property
    def allocation_reference(self) -> str | None: ...

    @property
    def context_reference(self) -> str | None: ...


def verify_sources(directory: Path, repo: Path, pin: str, prefix: str) -> None:
    tree = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-r", pin, prefix], check=True, capture_output=True, text=True
    ).stdout
    if not tree:
        raise ValueError("empty-source-tree")
    for line in tree.splitlines():
        metadata, name = line.split("\t", 1)
        mode, kind, expected = metadata.split()
        if mode != "100644" or kind != "blob":
            raise ValueError("nonregular-source")
        data = (directory / name).read_bytes()
        actual = hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
        if actual != expected:
            raise ValueError(f"source-pin-mismatch:{name}")


def guard(event: str, args: tuple[object, ...]) -> None:
    if event in {
        "socket.connect",
        "socket.bind",
        "socket.getaddrinfo",
        "subprocess.Popen",
        "os.system",
        "os.remove",
        "os.rmdir",
        "os.rename",
        "os.mkdir",
        "os.chmod",
        "os.chown",
        "os.truncate",
        "os.utime",
        "os.symlink",
        "os.link",
        "os.exec",
        "os.fork",
    }:
        raise RuntimeError("verification-side-effect-forbidden")
    if event == "open" and len(args) >= 3:
        mode, flags = args[1], args[2]
        if (isinstance(mode, str) and any(character in mode for character in "wax+")) or (
            isinstance(flags, int) and flags & 0x243
        ):
            raise RuntimeError("verification-write-forbidden")
    if event in {"open", "os.listdir", "os.scandir"}:
        if not args:
            raise RuntimeError("verification-read-path-required")
        path = args[0]
        if not isinstance(path, str | bytes):
            raise RuntimeError("verification-descriptor-read-forbidden")
        actual = Path(os.fsdecode(path)).resolve()
        if not any(actual.is_relative_to(root) for root in _read_roots):
            raise RuntimeError("verification-read-outside-allowlist")


def method(value: object, name: str) -> Callable[..., object]:
    return cast(Callable[..., object], getattr(value, name))


def main() -> None:
    global _read_roots
    if len(sys.argv) != 5:
        raise ValueError("four-source-arguments-required")
    router, router_git, kernel, kernel_git = (Path(value).resolve() for value in sys.argv[1:])
    verify_sources(router, router_git, ROUTER_PIN, "scarcity_router")
    verify_sources(kernel, kernel_git, KERNEL_PIN, "src/creatidy_kernel")
    # Import only inspected pure types/parsers; never CLI/application/provider adapters.
    root = Path(__file__).resolve().parents[1]
    _read_roots = (root / "src", root / "tests", router, kernel / "src", Path(sys.base_prefix).resolve())
    sys.dont_write_bytecode = True
    sys.addaudithook(guard)
    sys.path[:0] = [str(root / "src"), str(root / "tests"), str(router), str(kernel / "src")]
    import test_router_conformance as fixture

    types = importlib.import_module("scarcity_router.selection_types")
    selector = importlib.import_module("scarcity_router.selector")
    parser = importlib.import_module("creatidy_kernel.adapters.scarcity_router")
    resources = importlib.import_module("creatidy_kernel.core.resources")
    allocations = importlib.import_module("creatidy_kernel.ports.allocation")
    domain = importlib.import_module("creatidy_kernel.core.domain")
    from model_intelligence.contract import encode_public_evidence

    evidence_ref = types.EvidenceRef
    reference_error = cast(
        type[Exception], importlib.import_module("scarcity_router.errors").SelectionContractValidationError
    )
    requirement = method(types.TaskRequirement, "from_dict")(fixture.requirement())
    identity = method(types.ModelIdentity, "from_dict")(
        {"provider": "zai", "model": "owned-model", "variant": "owned-variant"}
    )
    passed = 0
    for effort in (None, "none"):
        context = fixture.canonical([])
        cut = replace(
            fixture.base(),
            applicability=replace(fixture.SCOPE, configuration=(("effort", effort), ("physical-model", None))),
        )
        consumer = fixture.RouterConsumerFixture(expected=cut.applicability)
        consumer.adopt(*encode_public_evidence(cut, produced_at=fixture.T))
        old_cut = consumer.current[1] if consumer.current else None
        later_cut = fixture.augment(
            cut,
            observed=(fixture.observation("later"),),
            claims=(
                fixture.BaselineClaim(
                    fixture.PLAN,
                    fixture.Terms(price=fixture.Money(fixture.Decimal("9"), "USD", "month")),
                    claim_id="later",
                    observation_id="later",
                    effective_from=fixture.T,
                    revises="base",
                ),
            ),
        )

        def actual_decision_path(
            inputs: fixture.EvaluationInput,
            owner: fixture.RouterConsumerFixture = consumer,
            refreshed: fixture.PublicEvidence = later_cut,
        ) -> dict[str, object]:
            candidate = cast(Callable[..., object], selector.CandidateEvaluation)(
                identity=identity,
                display_name=inputs.explanation(),
                eligible=True,
                reasoning_effort=inputs.effort,
                capability_margin=0,
            )
            decision = cast(Callable[..., object], selector.SelectionDecision)(
                evaluated_at=inputs.at,
                requirement=requirement,
                catalog_version=5,
                catalog_updated_on="2026-01-01",
                selector_mode="balanced",
                resource_policy_version=9,
                selected=candidate,
                reason_codes=("selected_balanced",),
            )
            result = cast(dict[str, object], method(decision, "to_dict")())
            assert result == fixture.fixture_decision(inputs)
            owner.adopt(*encode_public_evidence(refreshed, produced_at=fixture.T))
            return result

        use = consumer.evaluate(at=fixture.T, context=context, decide=actual_decision_path, effort=effort)
        actual = json.loads(use.decision_bytes)
        cut_ref = use.inputs.cut_reference
        assert cut_ref == old_cut and (consumer.current[1] if consumer.current else None) != cut_ref
        manifest, reference = use.utilization_bytes, dict(use.utilization_reference)
        assert method(method(evidence_ref, "from_dict")(reference), "to_dict")() == reference
        response = {"schema_version": 1, "decision": actual, "mi_utilization": reference}
        raw = fixture.canonical(response)
        parsed = method(parser, "_parse")(raw)
        checked, provenance = cast(
            tuple[dict[str, object], str], method(parser, "_decision")(parsed, fixture.requirement())
        )
        assert checked == actual and json.loads(provenance)["mi_utilization"] == reference
        allocation = cast(Callable[..., object], resources.Allocation)(
            runtime_id="owned-runtime",
            provider_id="zai",
            model_id="owned-model",
            capabilities=frozenset({"chat"}),
            context_tokens=4096,
            rationale="Owned pre-authorized fixture",
            reasoning_effort=effort,
            variant="owned-variant",
            decision_provenance=provenance,
        )
        encoded = cast(bytes, method(allocations, "encode_allocation")(allocation))
        assert method(allocations, "decode_allocation")(encoded) == allocation
        allocation_ref, context_ref = (
            "sha256:" + hashlib.sha256(encoded).hexdigest(),
            "sha256:" + hashlib.sha256(context).hexdigest(),
        )
        attempt_spec = cast(
            AttemptShape,
            cast(Callable[..., object], domain.AttemptSpec)(
                "owned-attempt",
                "owned-program",
                "owned-work-unit",
                1,
                "owned-spec-digest",
                allocation_reference=allocation_ref,
                context_reference=context_ref,
                agent_definition_reference="owned-agent-definition",
                workspace_reference="owned-workspace",
            ),
        )
        retained_digest = attempt_spec.digest
        assert attempt_spec.allocation_reference == allocation_ref
        assert attempt_spec.context_reference == context_ref
        retained = consumer.preserve_authorized(attempt_id="owned-attempt", use=use)
        assert retained.allocation == encoded
        assert json.loads(retained.intent)["attempt"] == retained_digest
        for broken in (b"MI unavailable", b"interrupted refresh"):
            try:
                consumer.adopt(broken, cut_ref)
            except ValueError:
                pass
            else:
                raise AssertionError("malformed-update-activated")
            retained.restore()
            assert attempt_spec.digest == retained_digest
            assert "sha256:" + hashlib.sha256(encoded).hexdigest() == allocation_ref
        assert manifest == retained.utilization_bytes
        passed += 1
        changed_use = consumer.evaluate(at=fixture.T, context=context, decide=actual_decision_path, effort=effort)
        assert changed_use.decision_bytes != use.decision_bytes
        assert changed_use.utilization_reference != use.utilization_reference
        retained.restore()
        passed += 1
    for invalid in (
        {"source": "model_intelligence", "identifier": "x", "date": fixture.T.isoformat()},
        {"source": "model_intelligence", "identifier": {"sha256": "x"}},
        {"source": "model_intelligence", "identifier": "x", "evaluated_at": fixture.T.isoformat()},
    ):
        try:
            method(evidence_ref, "from_dict")(invalid)
        except reference_error:
            passed += 1
        else:
            raise AssertionError("invalid-reference-accepted")
    reference_cases: tuple[dict[str, object], ...] = (
        {"source": "model_intelligence", "identifier": "owned-reference"},
        {"source": "model_intelligence", "identifier": "owned-reference", "version": None, "date": None},
        {"source": "model_intelligence", "identifier": "owned-reference", "version": "owned-v", "date": "2026-01-01"},
        {"source": "model_intelligence", "identifier": "x" * 513},
        {"source": "model_intelligence", "identifier": "x\n"},
        {"source": "INVALID", "identifier": "owned-reference"},
        {"source": "model_intelligence", "identifier": " owned-reference"},
        {"source": "model_intelligence", "identifier": "owned-reference", "version": "x" * 129},
        {"source": "model_intelligence", "identifier": "owned-reference", "date": "2026-02-30"},
    )
    for case in reference_cases:
        try:
            owned = fixture.evidence_ref(case)
        except ValueError:
            owned = None
        try:
            actual_ref = method(method(evidence_ref, "from_dict")(case), "to_dict")()
        except reference_error:
            actual_ref = None
        assert owned == actual_ref
        passed += 1
    print(
        json.dumps(
            {
                "router_pin": ROUTER_PIN,
                "kernel_pin": KERNEL_PIN,
                "pure_shape_cases": passed,
                "installed_acceptance": False,
                "router_emits_mi_extension": False,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
