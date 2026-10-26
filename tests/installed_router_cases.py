"""Outside-checkout installed producer -> actual Router -> retained binding cases."""

from __future__ import annotations

import hashlib
import importlib
import json
import sys
import zipfile
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from typing import cast
from unittest.mock import patch


def method(value: object, name: str) -> Callable[..., object]:
    return cast(Callable[..., object], getattr(value, name))


def field(value: object, name: str) -> object:
    return getattr(value, name)


def changed(value: object, **kwargs: object) -> object:
    return cast(Callable[..., object], replace)(value, **kwargs)


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def main() -> None:
    mode, directory = sys.argv[1:]
    root = Path(directory).resolve()
    # Only separately staged test helpers are added, never either package source.
    sys.path.insert(0, str(Path(__file__).parent))
    router = importlib.import_module("scarcity_router")
    app = importlib.import_module("scarcity_router.selection_app")
    machine = importlib.import_module("scarcity_router.machine_api")
    types = importlib.import_module("scarcity_router.selection_types")
    status = importlib.import_module("scarcity_router.status")
    capacity = importlib.import_module("scarcity_router.capacity")
    observation = importlib.import_module("tests.observation")
    at = datetime(2026, 10, 26, 0, 0, 0, 123456, tzinfo=UTC)
    day = timedelta(days=1)
    bound = 256 * 1024
    origin = Path(str(field(router, "__file__"))).resolve()
    assert Path(sys.prefix).resolve() in origin.parents and "site-packages" in origin.parts
    catalog, profiles, policy_version = cast(
        tuple[object, object, int],
        method(app, "load_configured_artifacts")(
            field(app, "DEFAULT_CATALOG_PATH"), field(app, "DEFAULT_MODEL_POLICY_PATH")
        ),
    )
    assert "site-packages" in Path(str(field(app, "DEFAULT_CATALOG_PATH"))).parts
    entries = cast(tuple[object, ...], field(catalog, "entries"))
    entry = entries[0]
    catalog = changed(catalog, entries=(entry,))
    requirement = method(field(types, "TaskRequirement"), "from_dict")(
        {"task_level": "L0", "capability_minima": {}, "hard_constraints": {}}
    )

    def snapshot(provider: str, retrieved_at: str) -> object:
        return method(capacity, "CapacitySnapshot")(
            schema_version=3,
            provider=provider,
            source="synthetic_test",
            retrieved_at=retrieved_at,
            status="ok",
            diagnostics=(),
            windows=tuple(
                method(capacity, "CapacityWindow")(
                    resource="tokens",
                    kind=kind,
                    scope_id="codex" if provider == "openai" else "coding_plan",
                    remaining_percent=80,
                    used_percent=20,
                    duration_seconds=seconds,
                )
                for kind, seconds in (("five_hour", 18000), ("weekly", 604800))
            ),
        )

    def openai(*, retrieved_at: str) -> object:
        return method(observation, "paired_observation")(snapshot("openai", retrieved_at))

    def zai(*, retrieved_at: str) -> object:
        return snapshot("zai", retrieved_at)

    collectors = method(status, "StatusCollectors")(openai=openai, zai=zai)

    def decide(owner: object = None, *, dependencies: object = collectors, when: datetime = at) -> object:
        return method(app, "select_from_inputs")(
            catalog=catalog,
            profiles=profiles,
            profile_policy_version=policy_version,
            profile_id=None,
            requirement=requirement,
            tightening=None,
            policy=None,
            collectors=dependencies,
            clock=lambda: when,
            mi_consumer=owner,
        )

    def dto(decision: object) -> dict[str, object]:
        return cast(dict[str, object], method(decision, "to_dict")())

    def label(decision: object) -> str:
        selected = field(decision, "selected")
        assert selected is not None
        return str(field(selected, "display_name"))

    def no_network(event: str, args: tuple[object, ...]) -> None:
        if event in {"socket.connect", "socket.getaddrinfo", "socket.__new__"}:
            raise AssertionError("network is outside installed acceptance")

    sys.addaudithook(no_network)
    baseline = decide()
    assert field(baseline, "mi_use") is None
    assert set(cast(dict[str, object], method(machine, "selection_envelope")(baseline))) == {
        "schema_version",
        "decision",
    }
    if mode == "bootstrap":
        try:
            _ = distribution("model-intelligence")
        except PackageNotFoundError:
            pass
        else:
            raise AssertionError("MI unexpectedly installed in base-only environment")
        print(
            json.dumps(
                {"result": "PASS", "mi_installed": False, "router_origin": str(origin), "decision": dto(baseline)}
            )
        )
        return
    assert mode == "acceptance"
    import model_intelligence
    from model_intelligence.acquisition import Capture
    from model_intelligence.contract import NATIVE_PAYLOAD_SCHEMA, PublicEvidence, encode_public_evidence
    from model_intelligence.evidence import Model, ModelClaim, NativeLimit
    from model_intelligence.operator import snapshot as inspect
    from model_intelligence.producer import publish, retained
    from model_intelligence.publication import CutReference
    from model_intelligence.utilization import decode_decision_utilization
    from model_intelligence.zai import SCOPE, normalize

    mi_origin = Path(model_intelligence.__file__ or "").resolve()
    assert Path(sys.prefix).resolve() in mi_origin.parents and "site-packages" in mi_origin.parts
    installed_sources: dict[str, object] = {}
    for name, source_root, package in (
        ("model-intelligence", root / "mi" / "src", "model_intelligence"),
        ("scarcity-router", root / "router", "scarcity_router"),
    ):
        info = distribution(name)
        direct = json.loads(info.read_text("direct_url.json") or "null")
        (wheel,) = (root / ("mi-dist" if name == "model-intelligence" else "router-dist")).glob("*.whl")
        assert direct["url"] == wheel.as_uri()
        # uv's local-wheel direct_url has archive_info={}; do not invent a hash
        # there. The installer enforces our digest and all wheel files match.
        with zipfile.ZipFile(wheel) as archive:
            for filename in archive.namelist():
                if not filename.endswith(("/", "/RECORD")):
                    assert Path(str(info.locate_file(filename))).read_bytes() == archive.read(filename)
        checked = 0
        for member in info.files or ():
            if member.parts[0] == package and member.suffix == ".py":
                assert Path(str(info.locate_file(member))).read_bytes() == (source_root / member).read_bytes()
                checked += 1
        assert checked > 0
        installed_sources[name] = {
            "direct_url": direct,
            "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
            "source_modules_verified": checked,
        }
    consumer_module = importlib.import_module("scarcity_router.mi_consumer")
    fixture = importlib.import_module("router_component_cases")
    # Explicit reviewed synthetic association reuses Router's maintained fixture;
    # it declares no real physical identity and never derives effort from variant.
    public = cast(PublicEvidence, method(fixture, "public")())
    binding = field(fixture, "BINDING")
    subject = cast(Model, field(fixture, "SUBJECT"))
    assert field(binding, "identity") == field(entry, "identity")
    assert dict(subject.configuration or ())["reasoning_effort"] == field(entry, "reasoning_effort")
    assert subject.physical_model_id is None
    store = root / "publication"
    store.mkdir()
    data, expected = encode_public_evidence(
        public, produced_at=at - timedelta(seconds=1), payload_schema=NATIVE_PAYLOAD_SCHEMA
    )
    # Expected digest/reference recorded independently of publish's returned value.
    _ = (root / "expected-cut.json").write_bytes(
        canonical({"format_version": 1, "payload_schema": NATIVE_PAYLOAD_SCHEMA, "sha256": expected.sha256})
    )
    reference = publish(
        store, public, expected=public.applicability, produced_at=at - timedelta(seconds=1), max_bytes=bound
    )
    assert reference == expected and hashlib.sha256(data).hexdigest() == expected.sha256
    path = store / f"{reference.sha256}.json"
    assert path.read_bytes() == data
    assert retained(store, max_bytes=bound) == (data, expected, public)
    view_a = inspect(store, instance="installed-synthetic", at=at, max_bytes=bound)
    assert cast(dict[str, object], view_a["publication"])["artifact"] == data.decode()
    _ = (root / "operator-a.json").write_bytes(canonical(view_a))
    owner = method(consumer_module, "MIConsumer")(
        expected_scope=public.applicability, bindings=(binding,), max_bytes=bound
    )
    method(owner, "load")(path, expected)
    # Observe the real selector boundary, rather than annotating its result.
    selector = field(app, "select_model")
    evaluated: list[bytes] = []

    def observe_selector(**kwargs: object) -> object:
        evaluated.append(canonical(method(kwargs["catalog"], "to_dict")()))
        assert b"public input 4096 tokens" in evaluated[-1]
        return cast(Callable[..., object], selector)(**kwargs)

    with patch.object(app, "select_model", side_effect=observe_selector):
        decision_a = decide(owner)
    assert len(evaluated) == 1 and "public input 4096 tokens" in label(decision_a)
    use_a = field(decision_a, "mi_use")
    assert use_a is not None

    def verify(decision: object, expected_cut: CutReference | None, name: str) -> dict[str, str]:
        use = field(decision, "mi_use")
        assert use is not None
        response = canonical(method(machine, "selection_envelope")(decision))
        decision_bytes = cast(bytes, field(use, "decision"))
        context = cast(bytes, field(use, "context"))
        manifest = cast(bytes, field(use, "utilization"))
        verified = decode_decision_utilization(
            manifest,
            response=response,
            expected_cut=expected_cut,
            evaluated_at=cast(datetime, field(use, "evaluated_at")),
            decision=decision_bytes,
            context=context,
            max_bytes=bound,
        )
        assert verified.cut == expected_cut
        output = root / name
        output.mkdir()
        artifacts = {
            "decision.json": decision_bytes,
            "context.json": context,
            "manifest.json": manifest,
            "envelope.json": response,
        }
        cut = field(use, "cut")
        if cut is not None:
            artifacts["cut.json"] = cast(bytes, field(cut, "data"))
        for filename, content in artifacts.items():
            _ = (output / filename).write_bytes(content)
        return {filename: hashlib.sha256(content).hexdigest() for filename, content in artifacts.items()}

    a_hashes = verify(decision_a, expected, "decision-a")
    binding_refusals = 0
    response_a = canonical(method(machine, "selection_envelope")(decision_a))
    inputs: dict[str, object] = {
        "response": response_a,
        "expected_cut": expected,
        "evaluated_at": at,
        "decision": field(use_a, "decision"),
        "context": field(use_a, "context"),
        "max_bytes": bound,
    }
    manifest_a = cast(bytes, field(use_a, "utilization"))
    for change in (
        {"expected_cut": replace(expected, sha256="0" * 64)},
        {"evaluated_at": at + timedelta(microseconds=1)},
        {"decision": cast(bytes, inputs["decision"]) + b" "},
        {"context": cast(bytes, inputs["context"]) + b" "},
        {"response": canonical({"schema_version": 1, "decision": dto(decision_a), "mi_utilization": {}})},
    ):
        try:
            _ = cast(Callable[..., object], decode_decision_utilization)(manifest_a, **{**inputs, **change})
        except ValueError:
            binding_refusals += 1
        else:
            raise AssertionError("tampered utilization binding accepted")
    try:
        _ = cast(Callable[..., object], decode_decision_utilization)(manifest_a + b" ", **inputs)
    except ValueError:
        binding_refusals += 1
    else:
        raise AssertionError("tampered manifest accepted")
    context_a = cast(dict[str, object], json.loads(cast(bytes, field(use_a, "context"))))
    assert context_a["mode"] == "explanation-only/1"
    bootstrap_context = cast(dict[str, object], context_a["bootstrap_catalog"])
    explained_context = cast(dict[str, object], context_a["evaluated_catalog"])
    assert canonical(bootstrap_context) == canonical(method(catalog, "to_dict")())
    explained_entry = cast(dict[str, object], cast(list[object], explained_context["entries"])[0])
    bootstrap_entry = cast(dict[str, object], cast(list[object], bootstrap_context["entries"])[0])
    explained_entry["display_name"] = bootstrap_entry["display_name"]
    assert explained_context == bootstrap_context
    without_annotation = dto(decision_a)
    cast(dict[str, object], without_annotation["selected"])["display_name"] = cast(
        dict[str, object], dto(baseline)["selected"]
    )["display_name"]
    assert without_annotation == dto(baseline), "public evidence changed selection authority"
    empty = method(consumer_module, "MIConsumer")(
        expected_scope=public.applicability, bindings=(binding,), max_bytes=bound
    )
    empty_decision = decide(empty)
    assert dto(empty_decision) == dto(baseline)
    _ = verify(empty_decision, None, "empty-consumer")
    # A compatible B is published and loaded during collection AFTER capture A.
    old_claim = public.evidence.claims[0]
    assert isinstance(old_claim, ModelClaim) and isinstance(old_claim.payload, NativeLimit)
    from decimal import Decimal

    new_claim = replace(
        old_claim,
        claim_id="installed-successor",
        revises=old_claim.claim_id,
        effective_from=at,
        payload=replace(old_claim.payload, amount=Decimal(8192)),
    )
    newer = replace(public, evidence=public.evidence.extend(claims=(new_claim,)))
    expected_b_data, expected_b = encode_public_evidence(newer, produced_at=at, payload_schema=NATIVE_PAYLOAD_SCHEMA)

    def refresh(*, retrieved_at: str) -> object:
        actual = publish(store, newer, expected=public.applicability, produced_at=at, max_bytes=bound)
        assert actual == expected_b
        method(owner, "load")(store / f"{actual.sha256}.json", expected_b)
        return openai(retrieved_at=retrieved_at)

    mid = decide(owner, dependencies=changed(collectors, openai=refresh))
    assert "4096" in label(mid)
    assert verify(mid, expected, "mid-refresh") == a_hashes
    decision_b = decide(owner)
    assert "8192" in label(decision_b)
    b_hashes = verify(decision_b, expected_b, "decision-b")
    assert a_hashes != b_hashes
    assert (store / f"{expected_b.sha256}.json").read_bytes() == expected_b_data
    view_b = inspect(store, instance="installed-synthetic", at=at, max_bytes=bound, checkpoint=expected.sha256)
    assert cast(dict[str, object], view_b["history"])["relation"] == "extension"
    _ = (root / "operator-b.json").write_bytes(canonical(view_b))
    stable_slot = method(owner, "capture")()
    stable_store = {item.name: item.read_bytes() for item in store.iterdir()}
    refused = 0
    for invalid, trusted in (
        (data, replace(expected, sha256="0" * 64)),
        (data[:-1], expected),
        (data, replace(expected, format_version=2)),
        (data, replace(expected, payload_schema="unsupported")),
        (b"x" * (bound + 1), expected),
        (data, expected),
    ):
        try:
            method(owner, "adopt")(invalid, trusted)
        except ValueError:
            refused += 1
        else:
            raise AssertionError("invalid input or unsupported rollback accepted")
        assert method(owner, "capture")() == stable_slot
        assert stable_store == {item.name: item.read_bytes() for item in store.iterdir()}
    try:
        publish(store, public, expected=public.applicability, produced_at=at, max_bytes=bound)
    except ValueError:
        refused += 1
    else:
        raise AssertionError("publication history rollback accepted")
    assert stable_store == {item.name: item.read_bytes() for item in store.iterdir()}
    # An interrupted write and incomplete selected-source generation cannot update B.
    with patch("model_intelligence.producer.os.replace", side_effect=OSError("synthetic interruption")):
        try:
            publish(store, newer, expected=public.applicability, produced_at=at + day, max_bytes=bound)
        except OSError:
            refused += 1
        else:
            raise AssertionError("interrupted publication unexpectedly succeeded")
    assert stable_store == {item.name: item.read_bytes() for item in store.iterdir()}
    # Replays use the retained immutable A, not the current pointer or a new cut.
    replay = method(consumer_module, "MIConsumer")(
        expected_scope=public.applicability, bindings=(binding,), max_bytes=bound
    )
    method(replay, "load")(path, expected)
    assert verify(decide(replay), expected, "replay-a") == a_hashes
    assert verify(decision_a, expected, "retained-a-after-b") == a_hashes
    assert "MI stale" in label(decide(owner, when=at + day))
    # Selected #15 source path: original complete upstream-shaped captures, not
    # live data or curated channel/configuration/identity additions.
    source_fixture = importlib.import_module("test_zai_source")
    captures = method(source_fixture, "captures")(at=at)
    selected = normalize(cast(tuple[Capture, ...], captures))
    assert selected.applicability == SCOPE and SCOPE.channel is None
    selected_store = root / "selected-source"
    selected_store.mkdir()
    selected_ref = publish(selected_store, selected, expected=SCOPE, produced_at=at, max_bytes=bound)
    selected_owner = method(consumer_module, "MIConsumer")(expected_scope=SCOPE, bindings=(binding,), max_bytes=bound)
    method(selected_owner, "load")(selected_store / f"{selected_ref.sha256}.json", selected_ref)
    selected_decision = decide(selected_owner)
    assert "MI unsupported" in label(selected_decision)
    assert not method(binding, "matches")(entry, SCOPE)
    subjects = tuple(claim.subject for claim in selected.evidence.claims if isinstance(claim, ModelClaim))
    assert subjects and all(subject.configuration is None for subject in subjects)
    assert all(subject.physical_model_id is None for subject in subjects)
    # Even an existing matching bootstrap identity cannot repair a null scope.
    exact_source_identities = 0
    for subject in subjects:
        assert not (subject.channel is not None and subject.channel == SCOPE.channel)
        for candidate in entries:
            identity = field(candidate, "identity")
            if (
                field(identity, "provider") == subject.provider_id
                and field(identity, "model") == subject.provider_model_id
            ):
                exact_source_identities += 1
                associated = method(consumer_module, "ModelBinding")(
                    identity, subject, "owned.input", "input-allowance", "owned-basis"
                )
                assert not method(associated, "matches")(candidate, SCOPE)
    assert all(item.fresh_until is None for item in selected.evidence.observations)
    _ = verify(selected_decision, selected_ref, "selected-source-use")
    try:
        _ = normalize(())
    except ValueError:
        refused += 1
    else:
        raise AssertionError("incomplete generation accepted")
    report = {
        "result": "PASS",
        "mi_version": distribution("model-intelligence").version,
        "router_version": distribution("scarcity-router").version,
        "mi_origin": str(mi_origin),
        "router_origin": str(origin),
        "mi_metadata": {
            key: distribution("model-intelligence").metadata[key] for key in ("Name", "Version", "License-Expression")
        },
        "router_requirements": distribution("scarcity-router").requires,
        "positive_label": label(decision_a),
        "updated_label": label(decision_b),
        "selector_boundary_observations": len(evaluated),
        "explicit_refusals": refused,
        "binding_refusals": binding_refusals,
        "installed_sources": installed_sources,
        "selected_source_existing_identity_matches": exact_source_identities,
        "a": a_hashes,
        "b": b_hashes,
        "selected_source_positive": False,
        "selected_source_limitations": [
            "nullable applicability channel",
            "no native per-model configuration/effort",
            "unknown physical identity retained",
            "unreviewed association and freshness cannot be invented",
        ],
        "live_acceptance": False,
        "product_go": False,
    }
    _ = (root / "integration.json").write_bytes(canonical(report))
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
