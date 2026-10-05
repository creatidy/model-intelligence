"""Owned Router/Kernel-shaped fixtures, with separately executed pinned parser checks."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
import unittest
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import cast

from model_intelligence.contract import (
    Applicability,
    PublicEvidence,
    SourceNotice,
    UncertainCampaign,
    decode_public_evidence,
    encode_public_evidence,
)
from model_intelligence.evidence import (
    BaselineClaim,
    Benchmark,
    Capability,
    DailyWindow,
    Evidence,
    Model,
    ModelClaim,
    Money,
    Observation,
    OverrideClaim,
    Period,
    Plan,
    Surface,
    SurfaceClaim,
    SurfaceEvidence,
    Terms,
    knowledge,
)
from model_intelligence.projection import effective_at
from model_intelligence.publication import CutReference
from model_intelligence.utilization import decode_utilization, encode_utilization

T = datetime(2026, 1, 1, 12, 0, 0, 123456, tzinfo=UTC)
DAY = timedelta(days=1)
PLAN = Plan("owned-plan", "zai", "owned-generation")
SCOPE = Applicability(
    "owned-public-scope", "owned-api", (("effort", "none"), ("physical-model", None)), frozenset({"owned-source"})
)
PRICE = Money(Decimal("20.123456789012345678901"), "USD", "month")
BOUND = 256 * 1024


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def observation(identity: str, *, fresh_until: datetime | None = T + DAY) -> Observation:
    return Observation(
        identity,
        "owned-source",
        "official",
        "documentation",
        f"https://example.invalid/{identity}",
        T,
        "public",
        "owned-synthetic",
        observed_at=T - DAY,
        published_at=T - 2 * DAY,
        fresh_until=fresh_until,
    )


def base() -> PublicEvidence:
    claim = BaselineClaim(PLAN, Terms(price=PRICE), claim_id="base", observation_id="base", effective_from=T - 3 * DAY)
    return PublicEvidence(SCOPE, Evidence((observation("base"),), (claim,)), (("base", "owned-source-revision"),))


def augment(
    cut: PublicEvidence,
    *,
    observed: tuple[Observation, ...] = (),
    claims: tuple[BaselineClaim | OverrideClaim, ...] = (),
    notices: tuple[SourceNotice, ...] = (),
    uncertain: tuple[UncertainCampaign, ...] = (),
) -> PublicEvidence:
    return PublicEvidence(
        cut.applicability,
        cut.evidence.extend(observations=observed, claims=claims),
        (*cut.revisions, *((o.observation_id, f"owned-revision:{o.observation_id}") for o in observed)),
        (*cut.notices, *notices),
        (*cut.uncertain_campaigns, *uncertain),
    )


def requirement() -> dict[str, object]:
    return {"task_level": "L0", "capability_minima": {}, "hard_constraints": {}}


def router_decision(at: datetime, *, effort: str | None = "none") -> dict[str, object]:
    """Original fixture shaped like the pinned to_dict output, not a routing invocation."""
    evaluated = at.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    selected = {
        "identity": {"provider": "zai", "model": "owned-model", "variant": "owned-variant"},
        "display_name": "Owned conformance model",
        "eligible": True,
        "reasoning_effort": effort,
        "degraded": False,
        "capability_margin": 0,
    }
    return {
        "evaluated_at": evaluated,
        "requirement": requirement(),
        "catalog_version": 5,
        "catalog_updated_on": "2026-01-01",
        "selector_mode": "balanced",
        "resource_policy_version": 9,
        "selected": selected,
        "alternatives": [],
        "excluded": [],
        "closest_candidates": [],
        "recoverable_candidates": [],
        "degraded": False,
        "reason_codes": ["selected_balanced"],
        "preference_order": [],
    }


def evidence_ref(value: object) -> dict[str, str]:
    """Owned validation of the inspected EvidenceRef grammar; pinned parser verifies it too."""
    if not isinstance(value, dict):
        raise ValueError("evidence-reference-shape")
    raw = cast(dict[str, object], value)
    if not {"source", "identifier"} <= set(raw) or not set(raw) <= {"source", "identifier", "version", "date"}:
        raise ValueError("evidence-reference-shape")
    result: dict[str, str] = {}
    for key, limit in (("source", 64), ("identifier", 512), ("version", 128), ("date", 10)):
        item = raw.get(key)
        if item is None and key in {"version", "date"}:
            continue
        if not isinstance(item, str) or not item or len(item) > limit or item != item.strip():
            raise ValueError("evidence-reference-text")
        if any(unicodedata.category(character) == "Cc" for character in item):
            raise ValueError("evidence-reference-control")
        result[key] = item
    if re.fullmatch(r"[a-z0-9][a-z0-9._:-]{0,63}", result["source"]) is None:
        raise ValueError("evidence-reference-source")
    if "date" in result and date.fromisoformat(result["date"]).isoformat() != result["date"]:
        raise ValueError("evidence-reference-date")
    return result


@dataclass(frozen=True)
class AttemptFixture:
    """A retention/lifecycle trace; no actual Kernel authority or runtime side effect."""

    attempt_id: str
    allocation: bytes
    allocation_reference: str
    context: bytes
    context_reference: str
    intent: bytes
    cut_bytes: bytes
    cut_reference: CutReference
    utilization_bytes: bytes
    utilization_reference: tuple[tuple[str, str], ...]
    decision_bytes: bytes
    evaluated_at: datetime
    spec_bytes: bytes
    state: str = "authorized"

    def restore(self) -> None:
        if (
            "sha256:" + hashlib.sha256(self.allocation).hexdigest() != self.allocation_reference
            or "sha256:" + hashlib.sha256(self.context).hexdigest() != self.context_reference
        ):
            raise ValueError("attempt-input-corruption")
        intent = cast(dict[str, object], json.loads(self.intent))
        if intent["allocation"] != self.allocation.decode() or intent["context"] != self.context.decode():
            raise ValueError("attempt-intent-mismatch")
        if intent["attempt"] != hashlib.sha256(self.spec_bytes).hexdigest():
            raise ValueError("attempt-spec-mismatch")
        allocation = cast(dict[str, object], json.loads(self.allocation))["allocation"]
        provenance_text = cast(dict[str, object], allocation)["decision_provenance"]
        if not isinstance(provenance_text, str):
            raise ValueError("attempt-provenance-type")
        provenance = cast(dict[str, object], json.loads(provenance_text))
        if canonical(provenance["decision"]) != self.decision_bytes:
            raise ValueError("attempt-decision-mismatch")
        if provenance["mi_utilization"] != dict(self.utilization_reference):
            raise ValueError("attempt-utilization-mismatch")
        utilized = decode_utilization(
            self.utilization_bytes,
            dict(self.utilization_reference),
            evaluated_at=self.evaluated_at,
            decision=self.decision_bytes,
            context=self.context,
            max_bytes=BOUND,
        )
        if utilized.cut != self.cut_reference:
            raise ValueError("attempt-cut-mismatch")
        decode_public_evidence(self.cut_bytes, self.cut_reference, max_bytes=BOUND)


class RouterConsumerFixture:
    """Data validator and retained trace only: does not select, rank, admit or cancel."""

    def __init__(self, expected: Applicability = SCOPE) -> None:
        self.current: tuple[bytes, CutReference, PublicEvidence] | None = None
        self.attempts: list[AttemptFixture] = []
        self.expected = expected

    def adopt(self, data: bytes, reference: CutReference) -> None:
        candidate = decode_public_evidence(data, reference, max_bytes=BOUND)
        if candidate.applicability != self.expected:
            raise ValueError("unexpected-public-scope")
        if self.current is not None:
            self.current[2].check_update(candidate)
        self.current = data, reference, candidate

    def preserve_authorized(
        self, *, attempt_id: str, at: datetime, context: bytes, decision: dict[str, object]
    ) -> AttemptFixture:
        if self.current is None:
            raise ValueError("no-validated-public-cut")
        if at.tzinfo is None or at.utcoffset() is None:
            raise ValueError("decision-evaluation-time-mismatch")
        expected_time = at.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        if decision.get("evaluated_at") != expected_time:
            raise ValueError("decision-evaluation-time-mismatch")
        # The fixture receives an already authorized decision; it has no admission rule.
        decision_bytes = canonical(decision)
        manifest, manifest_ref = encode_utilization(
            self.current[1], evaluated_at=at, decision=decision_bytes, context=context
        )
        shaped_ref = evidence_ref(manifest_ref)
        response = {"schema_version": 1, "decision": decision, "mi_utilization": shaped_ref}
        # This explicit extension is a proposal, not an existing Router output field.
        provenance = canonical(response).decode()
        selected = cast(dict[str, object], decision["selected"])
        identity = cast(dict[str, str], selected["identity"])
        allocation = canonical(
            {
                "version": 1,
                "allocation": {
                    "runtime_id": "owned-runtime",
                    "provider_id": identity["provider"],
                    "model_id": identity["model"],
                    "capabilities": ["chat"],
                    "context_tokens": 4096,
                    "rationale": "Owned pre-authorized fixture",
                    "reasoning_effort": selected["reasoning_effort"],
                    "variant": identity["variant"],
                    "decision_provenance": provenance,
                },
            }
        )
        if context != canonical([]):
            raise ValueError("fixture-only-empty-effective-inputs")
        allocation_ref = "sha256:" + hashlib.sha256(allocation).hexdigest()
        context_ref = "sha256:" + hashlib.sha256(context).hexdigest()
        spec = canonical(
            {
                "attempt_id": attempt_id,
                "program_id": "owned-program",
                "work_unit_id": "owned-work-unit",
                "spec_revision": 1,
                "spec_digest": "owned-spec-digest",
                "effective_inputs": [],
                "allocation_reference": allocation_ref,
                "context_reference": context_ref,
                "agent_definition_reference": "owned-agent-definition",
                "workspace_reference": "owned-workspace",
            }
        )
        intent = canonical(
            {
                "version": 1,
                "attempt": hashlib.sha256(spec).hexdigest(),
                "workspace": "owned-workspace",
                "allocation": allocation.decode(),
                "context": context.decode(),
            }
        )
        attempt = AttemptFixture(
            attempt_id,
            allocation,
            allocation_ref,
            context,
            context_ref,
            intent,
            self.current[0],
            self.current[1],
            manifest,
            tuple(sorted(shaped_ref.items())),
            decision_bytes,
            at,
            spec,
        )
        attempt.restore()
        self.attempts.append(attempt)
        return attempt


class RouterConformanceTests(unittest.TestCase):
    def test_all_native_families_roundtrip_without_a_new_calibration_scale(self) -> None:
        model = Model("owned-model", "zai", "owned-request")
        surface = Surface("owned-surface", "zai", "owned-build")
        claims = (
            ModelClaim(model, Capability("tool-use", None), claim_id="cap", observation_id="base", effective_from=T),
            ModelClaim(
                model,
                Benchmark(
                    "owned-benchmark",
                    "owned-v",
                    "owned-method",
                    "owned-config",
                    Decimal("7.123456789012345678901"),
                    "points",
                ),
                claim_id="bench",
                observation_id="base",
                effective_from=T,
            ),
            ModelClaim(
                model,
                Money(Decimal("0.0000000000000000001"), "USD", "token"),
                claim_id="modelprice",
                observation_id="base",
                effective_from=T,
            ),
            SurfaceClaim(
                surface,
                SurfaceEvidence("model-selection", True, None, True, False, None),
                claim_id="surface",
                observation_id="base",
                effective_from=T,
            ),
        )
        source = base()
        cut = replace(source, evidence=source.evidence.extend(claims=claims))
        data, reference = encode_public_evidence(cut, produced_at=T)
        self.assertEqual(decode_public_evidence(data, reference, max_bytes=BOUND), cut)
        self.assertEqual(cut.applicability.configuration, (("effort", "none"), ("physical-model", None)))
        capability = next(
            claim.payload for claim in effective_at(cut.evidence, T).models if isinstance(claim.payload, Capability)
        )
        self.assertIsNone(capability.supported)

    def test_producer_rejects_unrepresentable_semantics_before_publishing(self) -> None:
        source = base()
        empty_rule = replace(source.evidence.claims[0], terms=Terms(price=PRICE, rules=("",)))
        invalid = replace(source, evidence=Evidence(source.evidence.observations, (empty_rule,)))
        with self.assertRaisesRegex(ValueError, "payload-text"):
            encode_public_evidence(invalid, produced_at=T)

    def test_unknown_campaign_end_is_retained_not_an_invented_period(self) -> None:
        unknown = UncertainCampaign("unknown-bound", "unknown", PLAN, "owned-campaign", Terms(price=PRICE), T, T, None)
        cut = augment(base(), observed=(observation("unknown", fresh_until=None),), uncertain=(unknown,))
        decoded = decode_public_evidence(*encode_public_evidence(cut, produced_at=T), max_bytes=BOUND)
        self.assertIsNone(decoded.uncertain_campaigns[0].end)
        self.assertEqual(decoded.evidence.claims, base().evidence.claims)
        stale_ids = {item.observation_id for item in knowledge(decoded.evidence, T + 100 * DAY).stale_observations}
        self.assertIn("base", stale_ids)
        self.assertNotIn("unknown", stale_ids)
        self.assertIsNone(next(o.fresh_until for o in decoded.evidence.observations if o.observation_id == "unknown"))

    def test_source_critical_notice_is_distinct_and_does_not_cancel_authorization(self) -> None:
        reader = RouterConsumerFixture()
        reader.adopt(*encode_public_evidence(base(), produced_at=T))
        attempt = reader.preserve_authorized(
            attempt_id="owned-attempt", at=T, context=canonical([]), decision=router_decision(T)
        )
        notice = SourceNotice("source-critical", "critical", frozenset({"statement:base"}), T + DAY, "revocation", True)
        cut = augment(base(), observed=(observation("critical"),), notices=(notice,))
        reader.adopt(*encode_public_evidence(cut, produced_at=T + DAY))
        self.assertEqual(reader.current[2].active_notices(T) if reader.current else (), ())
        self.assertEqual(cut.active_notices(T + DAY), (notice,))
        self.assertEqual(effective_at(cut.evidence, T + DAY).offers[0].terms.price, PRICE)
        self.assertEqual(attempt.state, "authorized")
        attempt.restore()
        retract = SourceNotice(
            "critical-retracted", "retract", notice.targets, T + 2 * DAY, "retraction", None, "source-critical"
        )
        resolved = augment(cut, observed=(observation("retract"),), notices=(retract,))
        self.assertEqual(resolved.active_notices(T + 2 * DAY), ())
        self.assertEqual(len(resolved.notices), 2)

    def test_interruption_later_cut_and_restore_retain_actual_shaped_bytes(self) -> None:
        reader = RouterConsumerFixture()
        data, reference = encode_public_evidence(base(), produced_at=T)
        reader.adopt(data, reference)
        attempt = reader.preserve_authorized(
            attempt_id="owned-attempt", at=T, context=canonical([]), decision=router_decision(T)
        )
        for invalid, ref in (
            (data[:-10], reference),
            (data + b" ", reference),
            (data, replace(reference, format_version=2)),
        ):
            with self.assertRaises(ValueError):
                reader.adopt(invalid, ref)
            self.assertEqual(reader.current, (data, reference, base()))
            attempt.restore()
        later = augment(
            base(),
            observed=(replace(observation("later"), retrieved_at=T + DAY),),
            claims=(
                BaselineClaim(
                    PLAN,
                    Terms(price=Money(Decimal("9"), "USD", "month")),
                    claim_id="later",
                    observation_id="later",
                    effective_from=T + DAY,
                    revises="base",
                ),
            ),
        )
        reader.adopt(*encode_public_evidence(later, produced_at=T + DAY))
        self.assertNotEqual(reader.current[1] if reader.current else None, reference)
        attempt.restore()
        self.assertEqual(attempt.cut_reference, reference)
        self.assertEqual(attempt.evaluated_at, T)

    def test_utilization_ref_conforms_without_timestamp_in_calendar_date(self) -> None:
        data, cut_ref = encode_public_evidence(base(), produced_at=T)
        decision, context = canonical(router_decision(T)), canonical({"owned": "context"})
        manifest, ref = encode_utilization(cut_ref, evaluated_at=T, decision=decision, context=context)
        self.assertEqual(evidence_ref(ref), ref)
        self.assertNotIn("date", ref)
        result = decode_utilization(
            manifest, dict(ref), evaluated_at=T, decision=decision, context=context, max_bytes=BOUND
        )
        self.assertEqual(result.cut, cut_ref)
        self.assertEqual(result.evaluated_at, T)
        with self.assertRaises(ValueError):
            decode_utilization(
                manifest,
                dict(ref),
                evaluated_at=T + timedelta(microseconds=1),
                decision=decision,
                context=context,
                max_bytes=BOUND,
            )
        self.assertEqual(router_decision(T), router_decision(T + timedelta(microseconds=1)))
        other_manifest, other_ref = encode_utilization(
            cut_ref, evaluated_at=T + timedelta(microseconds=1), decision=decision, context=context
        )
        self.assertNotEqual(ref, other_ref)
        self.assertNotEqual(manifest, other_manifest)
        self.assertEqual(decode_public_evidence(data, cut_ref, max_bytes=BOUND), base())

    def test_restore_rejects_corrupted_original_inputs_and_intent(self) -> None:
        consumer = RouterConsumerFixture()
        consumer.adopt(*encode_public_evidence(base(), produced_at=T))
        attempt = consumer.preserve_authorized(
            attempt_id="owned-attempt", at=T, context=canonical([]), decision=router_decision(T)
        )
        bad_intent = cast(dict[str, object], json.loads(attempt.intent))
        bad_intent["attempt"] = "different-spec-digest"
        for damaged in (
            replace(attempt, allocation=attempt.allocation + b" "),
            replace(attempt, context=b"corrupt"),
            replace(attempt, utilization_bytes=attempt.utilization_bytes + b" "),
            replace(attempt, intent=canonical(bad_intent)),
        ):
            with self.subTest(reference=damaged.allocation_reference), self.assertRaises(ValueError):
                damaged.restore()
        attempt.restore()

    def test_decision_binding_cannot_use_a_different_evaluation_day(self) -> None:
        consumer = RouterConsumerFixture()
        consumer.adopt(*encode_public_evidence(base(), produced_at=T))
        with self.assertRaisesRegex(ValueError, "decision-evaluation-time-mismatch"):
            consumer.preserve_authorized(
                attempt_id="owned-attempt", at=T + DAY, context=canonical([]), decision=router_decision(T)
            )
        self.assertEqual(consumer.attempts, [])

    def test_unknown_utilization_is_not_inferred_from_catalog_or_model(self) -> None:
        decision, context = canonical(router_decision(T)), canonical({"owned": "context"})
        manifest, ref = encode_utilization(None, evaluated_at=T, decision=decision, context=context)
        self.assertIsNone(
            decode_utilization(
                manifest, dict(ref), evaluated_at=T, decision=decision, context=context, max_bytes=BOUND
            ).cut
        )
        for bad in (
            {**ref, "date": T.isoformat()},
            {**ref, "evaluated_at": T.isoformat()},
            {**ref, "identifier": {"digest": "x"}},
        ):
            with self.assertRaises(ValueError):
                evidence_ref(bad)

    def test_future_withdrawal_expiry_stale_and_conflict_remain_separate(self) -> None:
        promotion = OverrideClaim(
            PLAN,
            "owned-campaign",
            Terms(price=Money(Decimal("10"), "USD", "month")),
            Period(T, T + 2 * DAY),
            frozenset({"owned-client"}),
            DailyWindow("UTC", datetime.min.time(), datetime.min.replace(hour=23).time()),
            claim_id="sale",
            observation_id="sale",
            effective_from=T,
        )
        sale = augment(base(), observed=(observation("sale"),), claims=(promotion,))
        decoded = decode_public_evidence(*encode_public_evidence(sale, produced_at=T), max_bytes=BOUND)
        self.assertEqual(decoded, sale)
        self.assertEqual(
            effective_at(decoded.evidence, T, conditions=frozenset({"owned-client"})).offers[0].terms.price,
            promotion.terms.price if promotion.terms else None,
        )
        self.assertEqual(
            effective_at(decoded.evidence, T + 2 * DAY, conditions=frozenset({"owned-client"})).offers[0].terms.price,
            PRICE,
        )
        self.assertTrue(knowledge(decoded.evidence, T + DAY).stale_observations)
        withdrawing = OverrideClaim(
            PLAN,
            "owned-campaign",
            None,
            None,
            claim_id="withdraw",
            observation_id="withdraw",
            effective_from=T + DAY,
            revises="sale",
        )
        known = augment(sale, observed=(observation("withdraw"),), claims=(withdrawing,))
        restored = decode_public_evidence(*encode_public_evidence(known, produced_at=T), max_bytes=BOUND)
        self.assertTrue(knowledge(restored.evidence, T).future)
        self.assertEqual(restored.active_notices(T + DAY), ())
        contradictory = BaselineClaim(
            PLAN,
            Terms(price=Money(Decimal("99"), "USD", "month")),
            claim_id="other",
            observation_id="other",
            effective_from=T - DAY,
        )
        conflict = augment(base(), observed=(observation("other"),), claims=(contradictory,))
        self.assertTrue(
            effective_at(
                decode_public_evidence(*encode_public_evidence(conflict, produced_at=T), max_bytes=BOUND).evidence, T
            ).conflicts
        )

    def test_scope_history_and_notice_lineage_cannot_be_silently_rewritten(self) -> None:
        previous = base()
        with self.assertRaises(ValueError):
            previous.check_update(replace(previous, applicability=replace(SCOPE, channel=None)))
        with self.assertRaises(ValueError):
            previous.check_update(replace(previous, revisions=(("base", "different-revision"),)))
        with self.assertRaises(ValueError):
            SourceNotice("retract", "base", frozenset({"statement:base"}), T, "retraction", None)
        with self.assertRaises(ValueError):
            replace(
                previous,
                notices=(SourceNotice("bad-target", "base", frozenset({"statement:missing"}), T, "revocation", True),),
            )

    def test_incomplete_refresh_and_self_shrunk_scope_cannot_activate(self) -> None:
        previous = base()
        with self.assertRaisesRegex(ValueError, "incomplete-declared-source-coverage"):
            replace(previous, applicability=replace(SCOPE, source_ids=frozenset({"owned-source", "missing-source"})))
        smaller = replace(previous, applicability=replace(SCOPE, channel=None))
        consumer = RouterConsumerFixture()
        with self.assertRaisesRegex(ValueError, "unexpected-public-scope"):
            consumer.adopt(*encode_public_evidence(smaller, produced_at=T))
        self.assertIsNone(consumer.current)

    def test_payload_and_source_manifest_mismatch_are_rejected_before_activation(self) -> None:
        data, reference = encode_public_evidence(base(), produced_at=T)
        consumer = RouterConsumerFixture()
        consumer.adopt(data, reference)
        for location in ("statement", "observation", "applicability", "terms", "money", "source", "members"):
            frame = cast(dict[str, object], json.loads(data))
            payload = cast(dict[str, object], json.loads(cast(str, frame["payload"])))
            if location == "members":
                frame["members"] = []
            elif location == "source":
                cast(list[dict[str, object]], frame["sources"])[0]["revision"] = "different-source-revision"
            else:
                item = cast(dict[str, object], payload["applicability"])
                if location == "observation":
                    item = cast(list[dict[str, object]], payload["observations"])[0]
                elif location in {"statement", "terms", "money"}:
                    item = cast(list[dict[str, object]], payload["statements"])[0]
                    if location in {"terms", "money"}:
                        item = cast(dict[str, object], item["value"])
                    if location == "money":
                        item = cast(dict[str, object], item["price"])
                item["critical_revocation"] = {"unregistered": True}
                frame["payload"] = canonical(payload).decode()
            candidate = canonical(frame)
            with self.subTest(location=location), self.assertRaises(ValueError):
                consumer.adopt(candidate, replace(reference, sha256=hashlib.sha256(candidate).hexdigest()))
            self.assertEqual(consumer.current, (data, reference, base()))

    def test_critical_false_unknown_and_conflicting_branches_are_preserved(self) -> None:
        targets = frozenset({"statement:base"})
        parent = SourceNotice("notice", "base", targets, T, "revocation", None)
        left = SourceNotice("left", "left", targets, T + DAY, "revocation", True, "notice")
        right = SourceNotice("right", "right", targets, T + DAY, "revocation", False, "notice")
        cut = augment(base(), observed=(observation("left"), observation("right")), notices=(parent, left, right))
        result = decode_public_evidence(*encode_public_evidence(cut, produced_at=T), max_bytes=BOUND)
        self.assertEqual(result.active_notices(T), (parent,))
        self.assertEqual(result.active_notices(T + DAY), (left, right))
        with self.assertRaises(ValueError):
            cut.check_update(replace(cut, notices=(parent, left)))

    def test_utilization_rejects_changed_context_decision_and_missing_reference(self) -> None:
        _, cut_ref = encode_public_evidence(base(), produced_at=T)
        decision, context = canonical(router_decision(T)), canonical({"owned": "context"})
        manifest, reference = encode_utilization(cut_ref, evaluated_at=T, decision=decision, context=context)
        for changed_decision, changed_context in ((decision + b" ", context), (decision, context + b" ")):
            with self.assertRaises(ValueError):
                decode_utilization(
                    manifest,
                    dict(reference),
                    evaluated_at=T,
                    decision=changed_decision,
                    context=changed_context,
                    max_bytes=BOUND,
                )
        with self.assertRaises(ValueError):
            decode_utilization(
                manifest,
                {"source": "model_intelligence", "identifier": "missing"},
                evaluated_at=T,
                decision=decision,
                context=context,
                max_bytes=BOUND,
            )

    def test_completely_retained_stale_source_is_not_a_fresh_refresh(self) -> None:
        previous = base()
        cut = replace(
            previous,
            evidence=previous.evidence.extend(
                observations=(replace(previous.evidence.observations[0], retrieved_at=T + 10 * DAY),)
            ),
        )
        previous.check_update(cut)
        parsed = decode_public_evidence(*encode_public_evidence(cut, produced_at=T + 10 * DAY), max_bytes=BOUND)
        self.assertEqual(parsed.evidence.observations[0].fresh_until, T + DAY)
        self.assertTrue(knowledge(parsed.evidence, T + 10 * DAY).stale_observations)
        self.assertEqual(parsed.evidence.claims, previous.evidence.claims)


if __name__ == "__main__":
    unittest.main()
