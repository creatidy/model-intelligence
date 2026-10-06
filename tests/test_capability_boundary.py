"""Original research fixtures, not an approved mapping schema or consumer product."""

from __future__ import annotations

import hashlib
import json
import unittest
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import cast

from test_router_conformance import DAY, T, canonical, observation

from model_intelligence.evidence import Benchmark, Model, Observation, Surface, SurfaceEvidence
from model_intelligence.publication import CutReference, SourceRevision, decode_cut, decode_json_object, encode_cut
from model_intelligence.utilization import decode_decision_utilization, encode_utilization

RESEARCH_VERSION = "owned-capability-boundary/1"


@dataclass(frozen=True)
class Subject:
    provider: str
    requested: str
    physical_model: str | None
    model_version: str | None
    channel: str | None
    configuration: tuple[tuple[str, str | None], ...]
    surface: Surface


SUBJECT = Subject(
    "zai",
    "owned-alias",
    "owned-model",
    "revision-a",
    "owned-api",
    (("effort", "none"), ("opaque-variant", "high-sounding-name")),
    Surface("owned-client", "zai", "1.0"),
)


@dataclass(frozen=True)
class Limit:
    identity: str
    subject: Subject
    dimension: str
    amount: Decimal | None
    unit: str
    observation: Observation


INPUT = Limit("input-a", SUBJECT, "input_context_tokens", Decimal("4096"), "tokens", observation("input-a"))


def project_limit(limits: tuple[Limit, ...], subject: Subject, dimension: str) -> int:
    """Research-only exact comparison proposal; never selects or approves a rating."""
    if dimension not in {"input_context_tokens", "output_tokens"}:
        raise ValueError("unsupported-dimension")
    if subject.channel is None or any(value is None for _, value in subject.configuration):
        raise ValueError("unknown-applicability")
    rows = tuple(item for item in limits if item.subject == subject and item.dimension == dimension)
    if not rows:
        raise ValueError("missing-compatible-evidence")
    if any(item.observation.fresh_until is None for item in rows):
        raise ValueError("unknown-freshness")
    if any(item.observation.stale(T) for item in rows):
        raise ValueError("stale-evidence")
    if any(item.unit != "tokens" for item in rows):
        raise ValueError("incompatible-unit")
    values = {item.amount for item in rows}
    if None in values:
        raise ValueError("unknown-limit")
    if len(values) != 1:
        raise ValueError("conflicting-evidence")
    value = next(iter(values))
    assert value is not None
    if not value.is_finite() or value <= 0 or value != value.to_integral_value():
        raise ValueError("unrepresentable-limit")
    return int(value)


def physical_binding(subjects: tuple[Subject, ...], requested: Subject) -> str:
    """Only explicit comparable assertions; no alias fallback or identity inference."""
    values = {
        item.physical_model for item in subjects if replace(item, physical_model=requested.physical_model) == requested
    }
    if not values or None in values:
        raise ValueError("unknown-physical-model")
    if len(values) != 1:
        raise ValueError("ambiguous-alias")
    return next(value for value in values if value is not None)


def framed_record(payload: dict[str, object]) -> tuple[bytes, CutReference]:
    """Reuse #13 framing; the payload is explicitly owned/non-normative research."""
    return encode_cut(
        canonical(payload),
        payload_schema=RESEARCH_VERSION,
        produced_at=T,
        scope="owned-capability-research",
        members=("owned-mapping",),
        sources=(SourceRevision("owned-source", "https://example.invalid/mapping", "owned-revision"),),
    )


def record_payload(subject: Subject = SUBJECT) -> dict[str, object]:
    return {
        "mapping_version": RESEARCH_VERSION,
        "identity": {
            "provider": subject.provider,
            "requested": subject.requested,
            "physical_model": subject.physical_model,
            "model_version": subject.model_version,
            "channel": subject.channel,
            "configuration": dict(subject.configuration),
            "surface": {"id": subject.surface.surface_id, "version": subject.surface.version},
        },
        "public_input_limit": {"amount": "4096", "unit": "tokens", "meaning": "input allowance"},
    }


def narrow_requirement(context_tokens: int = 128) -> dict[str, object]:
    """Original shape of current Kernel's reference subset, NOT rich task intake."""
    return {
        "task_level": "L0",
        "capability_minima": {},
        "hard_constraints": {"requires_tool_use": True, "minimum_input_context_tokens": context_tokens},
    }


def admitted_limit(data: bytes, reference: CutReference, subject: Subject = SUBJECT) -> Limit:
    frame = decode_cut(data, reference, supported_payload_schemas=frozenset({RESEARCH_VERSION}), max_bytes=65536)
    raw = decode_json_object(frame.payload)
    if set(raw) != {"mapping_version", "identity", "public_input_limit"} or raw["mapping_version"] != RESEARCH_VERSION:
        raise ValueError("unsupported-mapping-version-or-shape")
    if raw["identity"] != record_payload(subject)["identity"]:
        raise ValueError("incompatible-mapping-context")
    native = raw["public_input_limit"]
    if not isinstance(native, dict):
        raise ValueError("limit-shape")
    limit = cast(dict[str, object], native)
    if set(limit) != {"amount", "unit", "meaning"} or limit["meaning"] != "input allowance":
        raise ValueError("unsupported-limit-meaning")
    amount, unit = limit["amount"], limit["unit"]
    if not isinstance(amount, str) or not isinstance(unit, str):
        raise ValueError("limit-native-types")
    return replace(INPUT, subject=subject, amount=Decimal(amount), unit=unit)


class CapabilityBoundaryTests(unittest.TestCase):
    def test_explicit_identity_and_managed_unknown_are_separate(self) -> None:
        self.assertEqual(physical_binding((SUBJECT,), SUBJECT), "owned-model")
        managed = replace(SUBJECT, physical_model=None, model_version=None, channel="owned-plan")
        self.assertIsNone(cast(dict[str, object], record_payload(managed)["identity"])["physical_model"])
        with self.assertRaisesRegex(ValueError, "unknown-physical-model"):
            physical_binding((managed,), managed)
        self.assertEqual(Model("owned-model", "zai", "owned-alias").provider_model_id, SUBJECT.requested)

    def test_alias_ambiguity_has_no_source_order_winner(self) -> None:
        other = replace(SUBJECT, physical_model="different-model")
        for subjects in ((SUBJECT, other), (other, SUBJECT)):
            with self.assertRaisesRegex(ValueError, "ambiguous-alias"):
                physical_binding(subjects, SUBJECT)

    def test_same_model_other_channel_configuration_and_version_do_not_transfer(self) -> None:
        self.assertEqual(project_limit((INPUT,), SUBJECT, "input_context_tokens"), 4096)
        for changed in (
            replace(SUBJECT, provider="other-provider"),
            replace(SUBJECT, requested="changed-alias"),
            replace(SUBJECT, channel="owned-plan"),
            replace(SUBJECT, model_version="revision-b"),
            replace(SUBJECT, configuration=(("effort", "high"),)),
            replace(SUBJECT, surface=replace(SUBJECT.surface, version="2.0")),
        ):
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(ValueError, "missing-compatible-evidence"):
                    project_limit((INPUT,), changed, "input_context_tokens")
        plan = replace(SUBJECT, channel="owned-plan")
        plan_limit = replace(INPUT, identity="plan-limit", subject=plan, amount=Decimal("512"))
        self.assertEqual(project_limit((INPUT, plan_limit), plan, "input_context_tokens"), 512)
        self.assertEqual(INPUT.amount, Decimal("4096"))

    def test_unknown_effort_is_not_none_or_opaque_variant(self) -> None:
        unknown = replace(SUBJECT, configuration=(("effort", None), ("opaque-variant", "max")))
        self.assertNotEqual(record_payload(unknown), record_payload())
        with self.assertRaisesRegex(ValueError, "unknown-applicability"):
            project_limit((replace(INPUT, subject=unknown),), unknown, "input_context_tokens")
        self.assertEqual(dict(SUBJECT.configuration)["effort"], "none")
        self.assertEqual(dict(unknown.configuration)["effort"], None)

    def test_missing_unknown_conflict_and_stale_remain_distinct(self) -> None:
        cases = (
            ((), "missing-compatible-evidence"),
            ((replace(INPUT, amount=None),), "unknown-limit"),
            ((INPUT, replace(INPUT, identity="disagreement", amount=Decimal("512"))), "conflicting-evidence"),
            ((replace(INPUT, observation=replace(INPUT.observation, fresh_until=T)),), "stale-evidence"),
            ((replace(INPUT, observation=replace(INPUT.observation, fresh_until=None)),), "unknown-freshness"),
        )
        for rows, diagnostic in cases:
            with self.subTest(diagnostic=diagnostic), self.assertRaisesRegex(ValueError, diagnostic):
                project_limit(rows, SUBJECT, "input_context_tokens")
        self.assertEqual(INPUT.observation.reference, "https://example.invalid/input-a")

    def test_native_units_and_meaning_cannot_be_guessed_or_rounded(self) -> None:
        for unit in ("characters", "total-context-tokens", "bytes"):
            with self.subTest(unit=unit), self.assertRaisesRegex(ValueError, "incompatible-unit"):
                project_limit((replace(INPUT, unit=unit),), SUBJECT, "input_context_tokens")
        for amount in ("0", "-1", "1.5", "1e-400", "NaN", "Infinity"):
            with self.subTest(amount=amount), self.assertRaisesRegex(ValueError, "unrepresentable-limit"):
                project_limit((replace(INPUT, amount=Decimal(amount)),), SUBJECT, "input_context_tokens")
        with self.assertRaisesRegex(ValueError, "unsupported-dimension"):
            project_limit((INPUT,), SUBJECT, "enforceable_output")

    def test_original_benchmarks_do_not_generate_quality_or_private_task_minima(self) -> None:
        a = Benchmark("owned-bench", "1", "owned-method", "client1/effort:none", Decimal("78.25"), "percent")
        b = replace(a, version="2", configuration="client2/effort:high", value=Decimal("0.8"), unit="ratio")
        provenance = observation("benchmark", fresh_until=T + DAY)
        self.assertNotEqual(a, b)
        self.assertEqual(
            (a.value, a.unit, a.methodology, a.version), (Decimal("78.25"), "percent", "owned-method", "1")
        )
        self.assertEqual((provenance.source_id, provenance.observed_at), ("owned-source", T - DAY))
        self.assertEqual(narrow_requirement()["capability_minima"], {})
        self.assertNotIn("quality", record_payload())

    def test_public_surface_assertions_are_not_local_adapter_authority(self) -> None:
        advertised = SurfaceEvidence("workspace-editing", advertised=True)
        self.assertIsNone(advertised.observed)
        self.assertIsNone(advertised.selectable)
        self.assertIsNone(advertised.enforceable)
        self.assertIsNone(advertised.physical_model_id)
        with self.assertRaisesRegex(ValueError, "unsupported-dimension"):
            project_limit((INPUT,), SUBJECT, "kernel-zcode-runtime")

    def test_frozen_mapping_version_rejection_preserves_original_record(self) -> None:
        data, reference = framed_record(record_payload())
        original = data, reference
        incompatible, newer_ref = encode_cut(
            canonical({"mapping_version": "owned-capability-boundary/2"}),
            payload_schema="owned-capability-boundary/2",
            produced_at=T + DAY,
            scope="owned-capability-research",
            members=("owned-mapping",),
            sources=(),
        )
        with self.assertRaisesRegex(ValueError, "unsupported-version"):
            decode_cut(
                incompatible, newer_ref, supported_payload_schemas=frozenset({RESEARCH_VERSION}), max_bytes=65536
            )
        decoded = decode_cut(data, reference, supported_payload_schemas=frozenset({RESEARCH_VERSION}), max_bytes=65536)
        self.assertEqual(json.loads(decoded.payload), record_payload())
        self.assertEqual(original, (data, reference))
        self.assertNotEqual(reference.sha256, newer_ref.sha256)
        inner = record_payload()
        inner["mapping_version"] = "owned-capability-boundary/2"
        with self.assertRaisesRegex(ValueError, "unsupported-mapping-version"):
            admitted_limit(*framed_record(inner))
        with self.assertRaisesRegex(ValueError, "incompatible-mapping-context"):
            admitted_limit(*framed_record(record_payload(replace(SUBJECT, channel="other-channel"))))

    def test_mapping_requirement_calibration_and_decision_share_captured_reference(self) -> None:
        data, cut = framed_record(record_payload())
        consumed = admitted_limit(data, cut)
        requirement = narrow_requirement()
        context = canonical(
            {
                "mapping_version": RESEARCH_VERSION,
                "requirement": requirement,
                "consumer_calibration": "owned-reviewed-calibration",
                "consumer_configuration": "owned-runtime-binding",
            }
        )
        decision = canonical(
            {
                "requirement": requirement,
                "public_input_context": project_limit((consumed,), SUBJECT, "input_context_tokens"),
            }
        )
        manifest, reference = encode_utilization(cut, evaluated_at=T, decision=decision, context=context)
        envelope = canonical({"schema_version": 1, "decision": json.loads(decision), "mi_utilization": reference})
        self.assertEqual(
            decode_decision_utilization(
                manifest,
                response=envelope,
                expected_cut=cut,
                evaluated_at=T,
                decision=decision,
                context=context,
                max_bytes=65536,
            ).cut,
            cut,
        )
        changed, changed_cut = framed_record(record_payload(replace(SUBJECT, requested="later-alias")))
        self.assertNotEqual(data, changed)
        with self.assertRaisesRegex(ValueError, "cut"):
            decode_decision_utilization(
                manifest,
                response=envelope,
                expected_cut=changed_cut,
                evaluated_at=T,
                decision=decision,
                context=context,
                max_bytes=65536,
            )
        self.assertEqual(hashlib.sha256(data).hexdigest(), cut.sha256)


if __name__ == "__main__":
    unittest.main()
