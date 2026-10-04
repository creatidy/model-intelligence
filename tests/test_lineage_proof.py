"""Synthetic M0-01R proof, not live model, Z.ai plan or ZCode assertions.

Predecessor scenarios come from PR #4 at 303f5fe, not its inferred matching code.
Every identity/link in these fixtures is deliberately supplied by the evidence author.
"""

import socket
import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

from model_intelligence.domain import (
    Benchmark,
    Capability,
    DailyWindow,
    Evidence,
    EvidenceClaim,
    Model,
    ModelClaim,
    Money,
    Observation,
    OfferClaim,
    Override,
    Period,
    Plan,
    Quota,
    Surface,
    SurfaceClaim,
    SurfaceEvidence,
    Terms,
)
from model_intelligence.projection import ChangeKind, changes, conflicts, current, future_overrides, offer

T0 = datetime(2026, 1, 1, tzinfo=UTC)
T1 = T0 + timedelta(days=1)
T2 = T0 + timedelta(days=2)
T3 = T0 + timedelta(days=3)
T4 = T0 + timedelta(days=4)
MODEL = Model("synthetic/glm-flash", "synthetic-zai", "glm-flash-fixture")
PLAN = Plan("synthetic/coding-pro", "synthetic-zai", "2026-fixture")
SURFACE = Surface("synthetic/zcode", "synthetic-zai", "fixture-1")
PRICE = Money(Decimal("20"), "USD", "month")
QUOTA = Quota(Decimal("100"), "public-request-units", "5 hours")
NORMAL = Terms(PRICE, QUOTA, True, ("public fair-use policy",))
SALE = Terms(price=Money(Decimal("10"), "USD", "month"))


def observation(identity: str, source: str = "a") -> Observation:
    return Observation(
        identity,
        source,
        "official" if source == "a" else "secondary",
        "documentation",
        f"https://example.invalid/{source}/{identity}",
        T0,
        "public",
        "synthetic, not redistributed",
        observed_at=T0,
        published_at=T0,
        fresh_until=T2,
    )


def baseline(identity: str = "base", *, revises: str | None = None, terms: Terms = NORMAL) -> OfferClaim:
    return OfferClaim(
        PLAN, terms, claim_id=identity, observation_id=identity, applicability=Period(T0), revises=revises
    )


def promotion(
    identity: str = "promo",
    *,
    start: datetime = T1,
    end: datetime = T3,
    revises: str | None = None,
    terms: Terms = SALE,
    campaign: str = "campaign-1",
    withdrawn: bool = False,
    window: DailyWindow | None = None,
    conditions: frozenset[str] = frozenset(),
) -> OfferClaim:
    return OfferClaim(
        PLAN,
        Override(campaign, terms, window, conditions, withdrawn),
        claim_id=identity,
        observation_id=identity,
        applicability=Period(start, end),
        revises=revises,
    )


def model_claim(identity: str, payload: Capability | Benchmark | Money, *, revises: str | None = None) -> ModelClaim:
    return ModelClaim(
        MODEL, payload, claim_id=identity, observation_id=identity, applicability=Period(T0), revises=revises
    )


def surface_claim(identity: str, payload: SurfaceEvidence, *, revises: str | None = None) -> SurfaceClaim:
    return SurfaceClaim(
        SURFACE, payload, claim_id=identity, observation_id=identity, applicability=Period(T0), revises=revises
    )


def evidence(*claims: EvidenceClaim) -> Evidence:
    return Evidence(
        tuple(observation(claim.observation_id, "b" if claim.claim_id.startswith("b-") else "a") for claim in claims),
        claims,
    )


def kinds(before: Evidence, after: Evidence, start: datetime = T1, end: datetime = T1) -> set[ChangeKind]:
    return {item.kind for item in changes(before, after, start, end)}


class LineageTests(unittest.TestCase):
    def test_explicit_identity_not_payload_equality(self) -> None:
        a = model_claim("a-price", Money(Decimal("1"), "USD", "million input tokens"))
        b = model_claim("b-price", a.payload)
        data = evidence(a, b)
        self.assertEqual(data.heads(), (a, b))
        self.assertEqual(len(data.observations), 2)
        self.assertEqual(conflicts(data, T1), ())
        self.assertIsNone(b.revises)

    def test_explicit_revision_preserves_history(self) -> None:
        a = promotion()
        revision = promotion("r", revises="promo", end=T2)
        data = evidence(a, revision)
        self.assertEqual(data.heads(), (revision,))
        self.assertEqual(data.status("promo", T1), "superseded")
        self.assertEqual(data.claims, (a, revision))

    def test_same_source_newer_different_values_not_revision(self) -> None:
        a = model_claim("a-price", Money(Decimal("1"), "USD", "million input tokens"))
        b = model_claim("a-newer", Money(Decimal("2"), "USD", "million input tokens"))
        newer = replace(observation("a-newer"), observed_at=T3, retrieved_at=T4)
        data = Evidence((observation("a-price"), newer), (a, b))
        self.assertEqual(len(data.heads()), 2)
        self.assertEqual(len(conflicts(data, T1)), 1)

    def test_revision_does_not_need_newer_timestamp_or_changed_value(self) -> None:
        a = model_claim("a", Capability("tools", True))
        r = model_claim("r", a.payload, revises="a")
        before = evidence(a)
        after = before.extend(
            observations=(replace(observation("r"), observed_at=T0 - timedelta(days=1)),), claims=(r,)
        )
        self.assertEqual(after.heads(), (r,))
        self.assertIn(ChangeKind.MODEL_EVIDENCE_REVISED, kinds(before, after))

    def test_self_reference_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "itself"):
            promotion(revises="promo")

    def test_missing_reference_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "historical"):
            evidence(promotion("r", revises="missing"))

    def test_cycles_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "cyclic"):
            evidence(promotion("a", revises="b"), promotion("b", revises="a"))

    def test_cross_family_subject_dimension_revision_rejected(self) -> None:
        base = baseline()
        bad = promotion(revises="base")
        other = replace(baseline("other", revises="base"), subject=replace(PLAN, generation="other"))
        cap = model_claim("cap", Capability("tools", True))
        price = model_claim("price", Money(Decimal("1"), "USD", "token"), revises="cap")
        collision = promotion("collision", campaign="baseline", revises="base")
        for claims in ((base, bad), (base, other), (cap, price), (base, collision)):
            with self.subTest(claims=claims), self.assertRaisesRegex(ValueError, "comparable"):
                evidence(*claims)

    def test_branching_lineage_does_not_choose_a_head(self) -> None:
        data = evidence(
            promotion(),
            promotion("x", revises="promo", terms=Terms(available=False)),
            promotion("y", revises="promo", terms=Terms(available=True)),
        )
        self.assertEqual({item.claim_id for item in data.heads()}, {"x", "y"})
        self.assertIsNone(offer(data, PLAN, T1).effective.available)
        self.assertEqual(offer(data, PLAN, T1).conflicts[0].field, "available")

    def test_identity_redefinition_and_duplicate_ids_rejected(self) -> None:
        data = evidence(baseline())
        with self.assertRaisesRegex(ValueError, "rewritten"):
            data.extend(claims=(baseline(terms=SALE),))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            Evidence(data.observations, (baseline(), baseline()))
        with self.assertRaisesRegex(ValueError, "observation"):
            Evidence((), (baseline(),))


class LifecycleTests(unittest.TestCase):
    def test_baseline_only(self) -> None:
        view = offer(evidence(baseline()), PLAN, T1)
        self.assertEqual(view.effective, NORMAL)
        self.assertEqual(view.overrides, ())
        self.assertEqual(len(view.baselines), 1)

    def test_future_promotion_is_queryable_but_inactive(self) -> None:
        data = evidence(baseline(), promotion())
        self.assertEqual(offer(data, PLAN, T0).effective, NORMAL)
        self.assertEqual(offer(data, PLAN, T0).overrides, ())
        self.assertEqual(future_overrides(data, PLAN, T0), (promotion(),))
        self.assertEqual(data.status("promo", T0), "future")

    def test_activation_declared_field_inheritance(self) -> None:
        data = evidence(baseline(), promotion())
        view = offer(data, PLAN, T1)
        self.assertEqual(view.effective, replace(NORMAL, price=SALE.price))
        self.assertEqual(view.overrides, (promotion(),))
        self.assertEqual(future_overrides(data, PLAN, T1), ())
        self.assertIn(ChangeKind.OVERRIDE_ACTIVATED, kinds(data, data, T0, T1))
        self.assertIn(ChangeKind.EFFECTIVE_OFFER_CHANGED, kinds(data, data, T0, T1))

    def test_expiry_automatically_falls_back_and_preserves_history(self) -> None:
        data = evidence(baseline(), promotion())
        self.assertEqual(offer(data, PLAN, T3).effective, NORMAL)
        self.assertEqual(offer(data, PLAN, T3).overrides, ())
        self.assertEqual(data.status("promo", T3), "expired")
        self.assertIn(promotion(), data.claims)
        self.assertIn(ChangeKind.OVERRIDE_EXPIRED, kinds(data, data, T2, T3))
        self.assertEqual(changes(data, data, T3, T4), ())

    def test_active_revision_shortens_end(self) -> None:
        before = evidence(baseline(), promotion())
        after = before.extend(
            observations=(observation("short"),), claims=(promotion("short", end=T2, revises="promo"),)
        )
        self.assertEqual(offer(after, PLAN, T1).overrides[0].claim_id, "short")
        self.assertEqual(offer(after, PLAN, T2).effective, NORMAL)
        self.assertIn(ChangeKind.OVERRIDE_REVISED, kinds(before, after))
        self.assertIn(ChangeKind.OVERRIDE_EXPIRED, kinds(after, after, T1, T2))

    def test_shortening_to_past_is_revision_not_inferred_expiry(self) -> None:
        before = evidence(baseline(), promotion())
        r = promotion("short", end=T1 + timedelta(hours=1), revises="promo")
        after = before.extend(observations=(observation("short"),), claims=(r,))
        events = kinds(before, after, T2, T2)
        self.assertIn(ChangeKind.OVERRIDE_REVISED, events)
        self.assertNotIn(ChangeKind.OVERRIDE_EXPIRED, events)
        self.assertEqual(offer(after, PLAN, T2).effective, NORMAL)

    def test_extension_and_term_change(self) -> None:
        before = evidence(baseline(), promotion())
        r = promotion("extended", end=T4, terms=Terms(price=Money(Decimal("8"), "USD", "month")), revises="promo")
        after = before.extend(observations=(observation("extended"),), claims=(r,))
        self.assertEqual(offer(after, PLAN, T3).effective.price, Money(Decimal("8"), "USD", "month"))
        self.assertEqual(offer(after, PLAN, T3).effective.quota, QUOTA)
        self.assertEqual(offer(after, PLAN, T4).effective, NORMAL)
        self.assertIn(ChangeKind.OVERRIDE_REVISED, kinds(before, after))
        self.assertIn(ChangeKind.EFFECTIVE_OFFER_CHANGED, kinds(before, after))

    def test_withdrawal_before_original_expiry(self) -> None:
        before = evidence(baseline(), promotion())
        r = promotion("withdrawn", revises="promo", withdrawn=True)
        after = before.extend(observations=(observation("withdrawn"),), claims=(r,))
        view = offer(after, PLAN, T2)
        self.assertEqual(view.effective, NORMAL)
        self.assertEqual(view.overrides, ())
        self.assertEqual(after.status("withdrawn", T2), "withdrawn")
        self.assertIn(ChangeKind.OVERRIDE_WITHDRAWN, kinds(before, after, T2, T2))
        self.assertNotIn(ChangeKind.OVERRIDE_EXPIRED, kinds(before, after, T2, T2))
        self.assertEqual(len(after.claims), 3)

    def test_later_independent_promotion_activates(self) -> None:
        data = evidence(
            baseline(),
            promotion(),
            promotion("ended", revises="promo", withdrawn=True),
            promotion("next", start=T3, end=T4, campaign="campaign-2"),
        )
        self.assertEqual(offer(data, PLAN, T2).effective, NORMAL)
        self.assertEqual([claim.claim_id for claim in offer(data, PLAN, T3).overrides], ["next"])
        self.assertIn(ChangeKind.OVERRIDE_ACTIVATED, kinds(data, data, T2, T3))

    def test_baseline_revision_independent_of_override(self) -> None:
        before = evidence(baseline(), promotion())
        revised = baseline(
            "new-base", revises="base", terms=replace(NORMAL, quota=Quota(Decimal("200"), "units", "day"))
        )
        after = before.extend(observations=(observation("new-base"),), claims=(revised,))
        self.assertEqual(offer(after, PLAN, T1).effective.price, SALE.price)
        assert isinstance(revised.payload, Terms)
        self.assertEqual(offer(after, PLAN, T1).effective.quota, revised.payload.quota)
        self.assertEqual(offer(after, PLAN, T3).baselines, (revised,))

    def test_no_baseline_does_not_invent_default_terms(self) -> None:
        self.assertEqual(offer(evidence(promotion()), PLAN, T0).effective, Terms())
        self.assertEqual(offer(evidence(promotion()), PLAN, T1).effective, SALE)

    def test_conditions_are_explicit_not_assumed(self) -> None:
        promo = promotion(conditions=frozenset({"public eligibility confirmed"}))
        data = evidence(baseline(), promo)
        self.assertEqual(offer(data, PLAN, T1).effective, NORMAL)
        self.assertEqual(
            offer(data, PLAN, T1, conditions=frozenset({"public eligibility confirmed"})).effective.price, SALE.price
        )

    def test_zoned_window_and_overnight_boundaries(self) -> None:
        window = DailyWindow("Asia/Shanghai", time(22), time(2))
        data = evidence(baseline(), promotion(window=window))
        self.assertEqual(offer(data, PLAN, T1 + timedelta(hours=14)).effective.price, SALE.price)
        self.assertEqual(offer(data, PLAN, T1 + timedelta(hours=18)).effective, NORMAL)
        self.assertIn(
            ChangeKind.OVERRIDE_INACTIVE, kinds(data, data, T1 + timedelta(hours=14), T1 + timedelta(hours=18))
        )


class ConflictTests(unittest.TestCase):
    def test_independent_disjoint_fields_compose(self) -> None:
        restricted = promotion("restriction", campaign="restriction", terms=Terms(available=False))
        data = evidence(baseline(), promotion(), restricted)
        view = offer(data, PLAN, T1)
        self.assertEqual(view.effective, replace(NORMAL, price=SALE.price, available=False))
        self.assertEqual(view.conflicts, ())

    def test_same_field_conflicts_no_arbitrary_winner(self) -> None:
        other = promotion("b-promo", campaign="other", terms=Terms(price=Money(Decimal("7"), "USD", "month")))
        data = evidence(baseline(), promotion(), other)
        view = offer(data, PLAN, T1)
        self.assertIsNone(view.effective.price)
        self.assertEqual(view.effective.quota, QUOTA)
        self.assertEqual(view.conflicts[0].field, "price")
        self.assertEqual(set(view.conflicts[0].claim_ids), {"promo", "b-promo"})
        refreshed = data.extend(observations=(replace(observation("b-promo", "b"), retrieved_at=T4),))
        self.assertEqual(offer(refreshed, PLAN, T1), view)

    def test_equal_independent_overrides_keep_identity_without_multiplication(self) -> None:
        data = evidence(baseline(), promotion(), promotion("b-equal", campaign="different"))
        view = offer(data, PLAN, T1)
        self.assertEqual(view.effective.price, SALE.price)
        self.assertEqual(len(view.overrides), 2)
        self.assertEqual(view.conflicts, ())

    def test_quota_overrides_are_replacements_not_composed_multipliers(self) -> None:
        a = promotion(terms=Terms(quota=Quota(Decimal("200"), "units", "5 hours")))
        b = promotion("other", campaign="other", terms=Terms(quota=Quota(Decimal("300"), "units", "5 hours")))
        view = offer(evidence(baseline(), a, b), PLAN, T1)
        self.assertIsNone(view.effective.quota)
        self.assertEqual(view.effective.price, PRICE)
        self.assertEqual(view.conflicts[0].field, "quota")

    def test_boundary_disagreement_visible_after_one_and_both_expire(self) -> None:
        data = evidence(baseline(), promotion(end=T2), promotion("b-boundary", end=T3))
        for at in (T1, T2, T3, T4):
            with self.subTest(at=at):
                self.assertEqual(offer(data, PLAN, at).conflicts[0].field, "applicability")
        view = offer(data, PLAN, T2)
        self.assertIsNone(view.effective.price)
        self.assertEqual([item.claim_id for item in view.overrides], ["b-boundary"])
        self.assertEqual(offer(data, PLAN, T3).overrides, ())
        self.assertEqual(offer(data, PLAN, T3).effective, NORMAL)

    def test_explicit_revision_resolves_boundary_disagreement(self) -> None:
        before = evidence(baseline(), promotion(end=T2), promotion("b-boundary", end=T3))
        r = promotion("r", end=T3, revises="promo")
        after = before.extend(observations=(observation("r"),), claims=(r,))
        self.assertEqual(offer(after, PLAN, T2).conflicts, ())
        self.assertIn(ChangeKind.CONFLICT_RESOLVED, kinds(before, after, T2, T2))
        self.assertIn(ChangeKind.OVERRIDE_REVISED, kinds(before, after, T2, T2))

    def test_conflicting_baselines_have_no_winner(self) -> None:
        data = evidence(
            baseline(), baseline("b-base", terms=replace(NORMAL, price=Money(Decimal("30"), "USD", "month")))
        )
        self.assertIsNone(offer(data, PLAN, T1).effective.price)
        self.assertEqual(len(offer(data, PLAN, T1).baselines), 2)

    def test_override_does_not_resolve_baseline_conflict(self) -> None:
        data = evidence(
            baseline(),
            baseline("b-base", terms=replace(NORMAL, price=Money(Decimal("30"), "USD", "month"))),
            promotion(),
        )
        baseline_conflicts = offer(data, PLAN, T0).conflicts
        self.assertEqual(len(baseline_conflicts), 1)
        self.assertEqual(baseline_conflicts[0].claim_ids, ("b-base", "base"))
        for at, price in ((T0, None), (T1, SALE.price), (T3, None)):
            with self.subTest(at=at):
                view = offer(data, PLAN, at)
                self.assertEqual(view.effective, replace(NORMAL, price=price))
                self.assertEqual(view.conflicts, baseline_conflicts)
                self.assertEqual(conflicts(data, at), baseline_conflicts)
        for start, end in ((T0, T1), (T2, T3)):
            with self.subTest(start=start, end=end):
                events = kinds(data, data, start, end)
                self.assertIn(ChangeKind.EFFECTIVE_OFFER_CHANGED, events)
                self.assertNotIn(ChangeKind.CONFLICT_RESOLVED, events)
                self.assertNotIn(ChangeKind.CONFLICT_DETECTED, events)

    def test_baseline_and_override_conflicts_remain_separate(self) -> None:
        data = evidence(
            baseline(),
            baseline("b-base", terms=replace(NORMAL, price=Money(Decimal("30"), "USD", "month"))),
            promotion(),
            promotion("b-promo", campaign="other", terms=Terms(price=Money(Decimal("7"), "USD", "month"))),
        )
        view = offer(data, PLAN, T1)
        self.assertIsNone(view.effective.price)
        self.assertEqual([item.claim_ids for item in view.conflicts], [("b-base", "base"), ("b-promo", "promo")])
        self.assertEqual(conflicts(data, T1), view.conflicts)

    def test_unknown_does_not_conflict_with_false(self) -> None:
        a = model_claim("unknown", Capability("tools", None))
        b = model_claim("b-false", Capability("tools", False))
        self.assertEqual(conflicts(evidence(a, b), T1), ())
        assert isinstance(a.payload, Capability) and isinstance(b.payload, Capability)
        self.assertIsNone(a.payload.supported)
        self.assertFalse(b.payload.supported)

    def test_conflict_events_not_repeated_when_unchanged(self) -> None:
        before = evidence(baseline(), promotion())
        other = promotion("b", campaign="other", terms=Terms(price=Money(Decimal("1"), "USD", "month")))
        after = before.extend(observations=(observation("b"),), claims=(other,))
        self.assertIn(ChangeKind.CONFLICT_DETECTED, kinds(before, after))
        self.assertEqual(changes(after, after, T1, T2), ())


class ABCProofTests(unittest.TestCase):
    def test_a_model_capability_price_and_contextual_benchmarks(self) -> None:
        benchmark = Benchmark("synthetic-code", "v1", "fixed tasks", "no tools", Decimal("70"), "percent")
        a = model_claim("a-bench", benchmark)
        b = model_claim("b-bench", replace(benchmark, value=Decimal("65")))
        different = model_claim("other-config", replace(benchmark, configuration="tools", value=Decimal("80")))
        price = model_claim("a-price", Money(Decimal("1"), "USD", "million input tokens"))
        data = evidence(a, b, different, price, model_claim("tools", Capability("tools", True)))
        self.assertEqual(
            {claim.subject.model_id for claim in current(data, T1) if isinstance(claim, ModelClaim)}, {MODEL.model_id}
        )
        self.assertEqual(
            {claim.subject.provider_model_id for claim in current(data, T1) if isinstance(claim, ModelClaim)},
            {MODEL.provider_model_id},
        )
        self.assertEqual(conflicts(data, T1)[0].claim_ids, ("a-bench", "b-bench"))
        self.assertEqual(len(conflicts(data, T1)), 1)
        self.assertEqual(len(data.heads()), 5)
        revised = model_claim("a-price-r", Money(Decimal("2"), "USD", "million input tokens"), revises="a-price")
        after = data.extend(observations=(observation("a-price-r"),), claims=(revised,))
        self.assertIn(ChangeKind.PRICE_CHANGED, kinds(data, after))
        self.assertIn(ChangeKind.MODEL_EVIDENCE_REVISED, kinds(data, after))

    def test_b_generation_baseline_and_bounded_rules(self) -> None:
        data = evidence(baseline(), promotion())
        self.assertEqual(offer(data, replace(PLAN, generation="2025"), T1).effective, Terms())
        self.assertEqual(offer(data, PLAN, T1).effective.rules, NORMAL.rules)
        self.assertEqual(offer(data, PLAN, T3).effective, NORMAL)

    def test_c_execution_dimensions_and_provider_managed_identity(self) -> None:
        capabilities = (
            "headless",
            "structured-output",
            "workspace-editing",
            "model-selection",
            "physical-model-observability",
            "physical-model-enforceability",
        )
        payloads = (
            SurfaceEvidence("headless", advertised=True, observed=True),
            SurfaceEvidence("structured-output", advertised=True, observed=None),
            SurfaceEvidence("workspace-editing", observed=True),
            SurfaceEvidence("model-selection", advertised=True, selectable=True, enforceable=False),
            SurfaceEvidence("physical-model-observability", advertised=False, observed=False),
            SurfaceEvidence("physical-model-enforceability", enforceable=False),
        )
        data = evidence(*(surface_claim(name, payload) for name, payload in zip(capabilities, payloads, strict=True)))
        self.assertEqual(len(current(data, T1)), 6)
        self.assertTrue(all(item.physical_model_id is None for item in payloads))
        self.assertIsNone(payloads[1].observed)
        self.assertEqual(conflicts(data, T1), ())
        r = surface_claim(
            "selected-r",
            SurfaceEvidence("model-selection", selectable=True, enforceable=True),
            revises="model-selection",
        )
        after = data.extend(observations=(observation("selected-r"),), claims=(r,))
        self.assertIn(ChangeKind.EXECUTION_SURFACE_CHANGED, kinds(data, after))

    def test_c_assertion_modes_do_not_conflict_across_dimensions(self) -> None:
        a = surface_claim("a", SurfaceEvidence("headless", advertised=True))
        b = surface_claim("b", SurfaceEvidence("headless", observed=False))
        c = surface_claim("c", SurfaceEvidence("headless", advertised=False))
        self.assertEqual(conflicts(evidence(a, b), T1), ())
        self.assertEqual(conflicts(evidence(a, b, c), T1)[0].claim_ids, ("a", "c"))

    def test_combined_abc_is_network_free_and_deterministic(self) -> None:
        claims = (
            baseline(),
            promotion(),
            model_claim("model", Capability("tools", True)),
            surface_claim("surface", SurfaceEvidence("headless", observed=True)),
        )
        with patch.object(socket, "socket", side_effect=AssertionError("network forbidden")):
            data = evidence(*claims)
            reverse = Evidence(tuple(reversed(data.observations)), tuple(reversed(data.claims)))
            self.assertEqual(data, reverse)
            self.assertEqual(changes(data, data, T0, T1), changes(reverse, reverse, T0, T1))
            self.assertEqual(offer(data, PLAN, T1).effective, replace(NORMAL, price=SALE.price))
            self.assertEqual(len(current(data, T1)), 2)


class PredecessorAdversarialTests(unittest.TestCase):
    def test_batched_price_revisions_preserve_explicit_changes(self) -> None:
        assert SALE.price is not None
        for family in ("model", "baseline"):
            with self.subTest(family=family):
                original = model_claim("a", PRICE) if family == "model" else baseline("a", terms=Terms(price=PRICE))
                middle = (
                    model_claim("b", SALE.price, revises="a")
                    if family == "model"
                    else baseline("b", terms=SALE, revises="a")
                )
                terminal = replace(middle, claim_id="c", observation_id="c", revises="b")
                before = evidence(original)
                intermediate = before.extend(observations=(observation("b"),), claims=(middle,))
                after = intermediate.extend(observations=(observation("c"),), claims=(terminal,))
                batched = before.extend(observations=(observation("b"), observation("c")), claims=(middle, terminal))
                self.assertEqual(after, batched)
                expected = tuple(
                    item for item in changes(before, intermediate, T1, T1) if item.kind == ChangeKind.PRICE_CHANGED
                )
                self.assertEqual(len(expected), 1)
                self.assertEqual(expected[0].claim_ids, ("a", "b"))
                self.assertEqual(
                    tuple(item for item in changes(before, batched, T1, T1) if item.kind == ChangeKind.PRICE_CHANGED),
                    expected,
                )
                self.assertNotIn(ChangeKind.PRICE_CHANGED, kinds(intermediate, after))
                self.assertEqual(changes(after, after, T1, T1), ())

    def test_model_activation_and_expiry_come_from_own_applicability(self) -> None:
        claim = replace(model_claim("model", Capability("tools", True)), applicability=Period(T1, T2))
        data = evidence(claim)
        self.assertEqual(current(data, T0), ())
        self.assertEqual(current(data, T1), (claim,))
        self.assertEqual(current(data, T2), ())
        self.assertIn(ChangeKind.MODEL_EVIDENCE_ACTIVATED, kinds(data, data, T0, T1))
        self.assertIn(ChangeKind.MODEL_EVIDENCE_EXPIRED, kinds(data, data, T1, T2))
        self.assertIn(claim, data.claims)

    def test_surface_expiry_changes_projection_without_deleting_evidence(self) -> None:
        claim = replace(
            surface_claim("surface", SurfaceEvidence("headless", observed=True)), applicability=Period(T0, T2)
        )
        data = evidence(claim)
        self.assertIn(ChangeKind.EXECUTION_SURFACE_CHANGED, kinds(data, data, T1, T2))
        self.assertIn(claim, data.claims)
        self.assertEqual(current(data, T2), ())

    def test_missing_row_is_not_cessation(self) -> None:
        data = evidence(baseline(), promotion())
        with self.assertRaisesRegex(ValueError, "missing rows"):
            changes(data, evidence(baseline()), T1, T2)
        self.assertEqual(len(data.claims), 2)

    def test_missing_model_row_is_not_cessation(self) -> None:
        data = evidence(model_claim("model", Capability("tools", True)))
        with self.assertRaisesRegex(ValueError, "missing rows"):
            changes(data, Evidence(), T1, T2)

    def test_older_same_source_history_cannot_close_newer_claim(self) -> None:
        before = evidence(baseline(), promotion())
        old = promotion("old", start=T0 - timedelta(days=2), end=T0, campaign="old-independent")
        after = before.extend(
            observations=(replace(observation("old"), observed_at=T0 - timedelta(days=2)),), claims=(old,)
        )
        self.assertEqual(offer(after, PLAN, T1).overrides, (promotion(),))
        self.assertEqual(changes(before, after, T1, T1), ())

    def test_matching_other_source_cannot_suppress_explicit_override_revision(self) -> None:
        before = evidence(baseline(), promotion(), promotion("b-short", end=T2))
        r = promotion("a-short", end=T2, revises="promo")
        after = before.extend(observations=(observation("a-short"),), claims=(r,))
        self.assertIn(ChangeKind.OVERRIDE_REVISED, kinds(before, after))
        self.assertEqual({claim.claim_id for claim in offer(after, PLAN, T1).overrides}, {"a-short", "b-short"})

    def test_matching_other_source_cannot_suppress_explicit_price_revision(self) -> None:
        rate = Money(Decimal("1"), "USD", "million input tokens")
        a = model_claim("a", rate)
        b = model_claim("b", replace(rate, amount=Decimal("2")))
        r = model_claim("r", b.payload, revises="a")
        before = evidence(a, b)
        after = before.extend(observations=(observation("r"),), claims=(r,))
        self.assertIn(ChangeKind.PRICE_CHANGED, kinds(before, after))
        self.assertEqual(after.heads(), (b, r))

    def test_superseded_history_does_not_become_current_correction(self) -> None:
        before = evidence(baseline(), promotion())
        old = promotion("old", end=T2, campaign="historical")
        closed = promotion("closed", end=T2, revises="old", campaign="historical", withdrawn=True)
        after = before.extend(observations=(observation("old"), observation("closed")), claims=(old, closed))
        events = changes(before, after, T1, T1)
        self.assertFalse(
            any("old" in event.claim_ids and event.kind == ChangeKind.OVERRIDE_REVISED for event in events)
        )
        self.assertEqual(offer(after, PLAN, T1).overrides, (promotion(),))

    def test_retrieval_only_silent_stale_stays_stale(self) -> None:
        data = evidence(baseline(), promotion())
        refreshed = data.extend(observations=tuple(replace(item, retrieved_at=T4) for item in data.observations))
        self.assertEqual(changes(data, refreshed, T2, T2), ())
        self.assertTrue(all(item.stale(T2) for item in refreshed.observations))
        self.assertEqual(offer(data, PLAN, T2), offer(refreshed, PLAN, T2))
        self.assertIn(ChangeKind.OVERRIDE_EXPIRED, kinds(data, refreshed, T2, T3))

    def test_superseded_remains_superseded_after_retrieval(self) -> None:
        data = evidence(baseline(), promotion(), promotion("r", revises="promo", end=T2))
        refreshed = data.extend(observations=(replace(observation("promo"), retrieved_at=T4),))
        self.assertEqual(refreshed.status("promo", T1), "superseded")
        self.assertEqual(changes(data, refreshed, T1, T1), ())
        self.assertEqual(offer(refreshed, PLAN, T2).overrides, ())

    def test_retrieval_cannot_rewrite_observation_or_claim_semantics(self) -> None:
        data = evidence(baseline())
        with self.assertRaisesRegex(ValueError, "observation identity"):
            data.extend(observations=(replace(observation("base"), fresh_until=T4),))

    def test_new_independent_promotion_does_not_resurrect_old_one(self) -> None:
        before = evidence(baseline(), promotion(), promotion("r", revises="promo", withdrawn=True))
        p = promotion("next", start=T3, end=T4, campaign="independent")
        after = before.extend(observations=(observation("next"),), claims=(p,))
        self.assertEqual(offer(after, PLAN, T3).overrides, (p,))
        self.assertEqual(after.status("promo", T3), "superseded")
        self.assertEqual(after.status("r", T3), "withdrawn")


class ValidationTests(unittest.TestCase):
    def test_half_open_period_and_aware_time_validation(self) -> None:
        period = Period(T1, T2)
        self.assertFalse(period.contains(T0))
        self.assertTrue(period.contains(T1))
        self.assertFalse(period.contains(T2))
        for end in (T0, T1):
            with self.assertRaises(ValueError):
                Period(T1, end)
        with self.assertRaises(ValueError):
            Period(datetime(2026, 1, 1))

    def test_temporary_override_bounded_and_withdrawal_linked(self) -> None:
        with self.assertRaisesRegex(ValueError, "bounded"):
            replace(promotion(), applicability=Period(T1))
        with self.assertRaisesRegex(ValueError, "explicitly"):
            promotion(withdrawn=True)
        with self.assertRaisesRegex(ValueError, "declare"):
            Override("empty", Terms())

    def test_dst_fold_uses_instants_and_window_uses_wall_time(self) -> None:
        zone = ZoneInfo("America/New_York")
        first = datetime(2026, 11, 1, 1, 30, tzinfo=zone, fold=0)
        second = datetime(2026, 11, 1, 1, 30, tzinfo=zone, fold=1)
        period = Period(first, second)
        self.assertTrue(period.contains(first))
        self.assertFalse(period.contains(second))
        window = DailyWindow("America/New_York", time(1), time(2))
        self.assertTrue(window.contains(first))
        self.assertTrue(window.contains(second))
        with self.assertRaises(ValueError):
            DailyWindow("UTC", time(1), time(1))

    def test_numeric_validation_and_signed_zero(self) -> None:
        for value in ("-1", "NaN", "Infinity"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Money(Decimal(value), "USD", "token")
        self.assertEqual(Money(Decimal("-0"), "USD", "token"), Money(Decimal("0"), "USD", "token"))

    def test_immutable_and_empty_identity_rejected(self) -> None:
        with self.assertRaises(FrozenInstanceError):
            attribute = "claim_id"
            setattr(baseline(), attribute, "rewritten")
        with self.assertRaises(ValueError):
            observation("")

    def test_historical_comparison_rejects_time_reversal(self) -> None:
        with self.assertRaisesRegex(ValueError, "backwards"):
            changes(Evidence(), Evidence(), T2, T1)
