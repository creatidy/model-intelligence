"""Synthetic R2 proof; predecessor behaviors, not predecessor projection code."""

import socket
import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from itertools import permutations
from unittest.mock import patch
from zoneinfo import ZoneInfo

from model_intelligence.deltas import EvidenceDelta, evidence_delta, projection_delta
from model_intelligence.evidence import (
    BaselineClaim,
    Benchmark,
    Capability,
    DailyWindow,
    Evidence,
    EvidenceClaim,
    Model,
    ModelClaim,
    Money,
    Observation,
    OverrideClaim,
    Period,
    Plan,
    Quota,
    Surface,
    SurfaceClaim,
    SurfaceEvidence,
    Terms,
    knowledge,
)
from model_intelligence.projection import OfferView, effective_at

JAN = datetime(2026, 1, 1, tzinfo=UTC)
OCT = datetime(2026, 10, 1, tzinfo=UTC)
NOW = datetime(2026, 10, 15, tzinfo=UTC)
NOV = datetime(2026, 11, 1, tzinfo=UTC)
DEC = datetime(2026, 12, 1, tzinfo=UTC)
PLAN = Plan("synthetic/pro", "synthetic-provider", "2026")
MODEL = Model("synthetic/model", "synthetic-provider", "fixture-id")
SURFACE = Surface("synthetic/editor", "synthetic-provider", "fixture-v1")
PRICE = Money(Decimal("20"), "USD", "month")
SALE = Money(Decimal("10"), "USD", "month")
NEXT = Money(Decimal("25"), "USD", "month")
NORMAL = Terms(PRICE, Quota(Decimal("100"), "public-units", "5 hours"), True, ("public fair use",))
SALE_TERMS = Terms(price=SALE)
EMPTY = effective_at(Evidence(), JAN)
NO_PROJECTION_DELTA = projection_delta(EMPTY, EMPTY)


def observation(identity: str, source: str = "official") -> Observation:
    return Observation(
        identity,
        source,
        "official" if source == "official" else "secondary",
        "documentation",
        f"https://example.invalid/{source}/{identity}",
        OCT,
        "public",
        "synthetic",
        observed_at=OCT,
        published_at=JAN,
        fresh_until=NOV,
    )


def base(identity: str = "a", price: Money = PRICE, start: datetime = JAN, revises: str | None = None) -> BaselineClaim:
    return BaselineClaim(
        PLAN,
        replace(NORMAL, price=price),
        claim_id=identity,
        observation_id=identity,
        effective_from=start,
        revises=revises,
    )


def promo(
    identity: str = "p",
    *,
    version: datetime = JAN,
    start: datetime = OCT,
    end: datetime = NOV,
    terms: Terms = SALE_TERMS,
    revises: str | None = None,
    campaign: str = "sale",
    conditions: frozenset[str] = frozenset(),
    window: DailyWindow | None = None,
) -> OverrideClaim:
    return OverrideClaim(
        PLAN,
        campaign,
        terms,
        Period(start, end),
        conditions,
        window,
        claim_id=identity,
        observation_id=identity,
        effective_from=version,
        revises=revises,
    )


def withdraw(identity: str = "w", *, at: datetime = NOV, revises: str = "p") -> OverrideClaim:
    return OverrideClaim(
        PLAN, "sale", None, None, claim_id=identity, observation_id=identity, effective_from=at, revises=revises
    )


def model(
    identity: str, payload: Capability | Benchmark | Money, *, at: datetime = JAN, revises: str | None = None
) -> ModelClaim:
    return ModelClaim(MODEL, payload, claim_id=identity, observation_id=identity, effective_from=at, revises=revises)


def surface(identity: str, payload: SurfaceEvidence, *, at: datetime = JAN, revises: str | None = None) -> SurfaceClaim:
    return SurfaceClaim(
        SURFACE, payload, claim_id=identity, observation_id=identity, effective_from=at, revises=revises
    )


def evidence(*claims: EvidenceClaim) -> Evidence:
    return Evidence(
        tuple(
            observation(claim.observation_id, "secondary" if claim.claim_id.startswith("b-") else "official")
            for claim in claims
        ),
        claims,
    )


def offer(data: Evidence, at: datetime = NOW, *, conditions: frozenset[str] = frozenset()) -> OfferView:
    return next(view for view in effective_at(data, at, conditions=conditions).offers if view.plan == PLAN)


class KnowledgeAndBaselineTests(unittest.TestCase):
    def test_observation_only_delta_and_explicit_identity(self) -> None:
        original = evidence(base())
        independent = replace(base(), claim_id="independent", observation_id="extra")
        acquired = original.extend(observations=(observation("extra", "secondary"),))
        self.assertEqual(evidence_delta(original, acquired).observations, (observation("extra", "secondary"),))
        self.assertEqual(evidence_delta(original, acquired).claims, ())
        self.assertEqual(effective_at(original, NOW), effective_at(acquired, NOW))
        after = acquired.extend(claims=(independent,))
        self.assertIsNone(independent.revises)
        self.assertEqual(len(knowledge(after, NOW).latest), 2)
        self.assertEqual(offer(after).terms, NORMAL)
        self.assertEqual(offer(after).conflicts, ())

    def test_required_future_baseline_no_unknown_gap(self) -> None:
        before = evidence(base())
        after = evidence(base(), base("b", NEXT, NOV, "a"))
        known = knowledge(after, NOW)
        self.assertEqual([claim.claim_id for claim in known.latest], ["b"])
        self.assertEqual(known.future, (base("b", NEXT, NOV, "a"),))
        self.assertEqual(offer(after).baselines, (base(),))
        self.assertEqual(offer(after).terms, NORMAL)
        delta = evidence_delta(before, after)
        self.assertEqual(delta.claims[0].claim_id, "b")
        self.assertEqual(delta.claims[0].revises, "a")
        self.assertEqual(projection_delta(effective_at(before, NOW), effective_at(after, NOW)), NO_PROJECTION_DELTA)
        changed = projection_delta(effective_at(after, NOW), effective_at(after, NOV)).offers[0]
        assert changed.before is not None and changed.after is not None
        self.assertEqual(changed.before.baselines, (base(),))
        self.assertEqual(changed.after.baselines, (base("b", NEXT, NOV, "a"),))
        self.assertEqual(changed.before.terms.price, PRICE)
        self.assertEqual(changed.after.terms.price, NEXT)
        self.assertEqual(evidence_delta(after, after), EvidenceDelta((), ()))

    def test_past_effective_revision_learned_today(self) -> None:
        before = evidence(base())
        after = evidence(base(), base("b", NEXT, OCT, "a"))
        self.assertEqual(offer(after).terms.price, NEXT)
        self.assertEqual(evidence_delta(before, after).claims[0].revises, "a")
        changed = projection_delta(effective_at(before, NOW), effective_at(after, NOW)).offers[0]
        assert changed.after is not None
        self.assertEqual(changed.after.baselines[0].claim_id, "b")

    def test_same_term_future_and_past_revisions_separate_knowledge(self) -> None:
        before = evidence(base())
        for start in (OCT, NOV):
            with self.subTest(start=start):
                revision = base("b", PRICE, start, "a")
                after = evidence(base(), revision)
                self.assertEqual(evidence_delta(before, after).claims, (revision,))
                self.assertEqual(offer(after).terms, NORMAL)
                self.assertEqual(offer(after).baselines[0].claim_id, "a" if start == NOV else "b")
                delta = projection_delta(effective_at(before, NOW), effective_at(after, NOW))
                self.assertEqual(delta == NO_PROJECTION_DELTA, start == NOV)

    def test_baseline_chain_boundaries_and_equal_start(self) -> None:
        data = evidence(base(), base("b", NEXT, OCT, "a"), base("c", SALE, NOV, "b"))
        for at, identity in ((JAN, "a"), (NOW, "b"), (NOV, "c"), (DEC, "c")):
            with self.subTest(at=at):
                self.assertEqual(offer(data, at).baselines[0].claim_id, identity)
                self.assertEqual(knowledge(data, at).latest[0].claim_id, "c")
        same_start = evidence(base(), base("b", NEXT, JAN, "a"))
        self.assertEqual(offer(same_start, JAN).terms.price, NEXT)

    def test_future_only_plan_does_not_contaminate_projection(self) -> None:
        data = evidence(base("future", start=NOV))
        self.assertEqual(effective_at(data, NOW), EMPTY)
        self.assertEqual(len(knowledge(data, NOW).latest), 1)

    def test_branches_nested_and_future_are_not_winners(self) -> None:
        data = evidence(base(), base("b", NEXT, OCT, "a"), base("c", SALE, NOV, "a"), base("d", NEXT, NOV, "b"))
        self.assertEqual([item.claim_id for item in knowledge(data, NOW).latest], ["c", "d"])
        self.assertEqual(offer(data, NOW).baselines[0].claim_id, "b")
        view = offer(data, NOV)
        self.assertEqual([item.claim_id for item in view.baselines], ["c", "d"])
        self.assertIsNone(view.terms.price)
        self.assertIn(("c", "d"), [item.claim_ids for item in view.conflicts if item.field == "lineage"])

    def test_equal_branch_values_retain_both_versions(self) -> None:
        data = evidence(base(), base("b", NEXT, OCT, "a"), base("c", NEXT, OCT, "a"))
        self.assertEqual(len(offer(data).baselines), 2)
        self.assertEqual(offer(data).terms.price, NEXT)
        self.assertEqual(offer(data).conflicts[0].field, "lineage")


class OverrideLifecycleTests(unittest.TestCase):
    def test_baseline_future_activation_inheritance_expiry(self) -> None:
        data = evidence(base(), promo())
        self.assertEqual(offer(data, JAN).terms, NORMAL)
        self.assertEqual(offer(data).terms, replace(NORMAL, price=SALE))
        self.assertEqual(offer(data).overrides, (promo(),))
        self.assertEqual(offer(data, NOV).terms, NORMAL)
        self.assertEqual(offer(data, NOV).overrides, ())
        self.assertIn(promo(), knowledge(data, NOV).history)
        self.assertIn(promo(), knowledge(data, JAN).future)

    def test_future_revision_does_not_disable_current_promotion(self) -> None:
        revision = promo("r", version=NOV, end=DEC, terms=Terms(price=NEXT), revises="p")
        before = evidence(base(), promo())
        after = evidence(base(), promo(), revision)
        self.assertIn(revision, knowledge(after, NOW).latest)
        self.assertEqual(offer(after).overrides, (promo(),))
        self.assertEqual(evidence_delta(before, after).claims, (revision,))
        self.assertEqual(projection_delta(effective_at(before, NOW), effective_at(after, NOW)), NO_PROJECTION_DELTA)
        self.assertEqual(offer(after, NOV).overrides, (revision,))
        self.assertEqual(offer(after, NOV).terms.price, NEXT)
        self.assertEqual(offer(after, DEC).terms, NORMAL)
        self.assertEqual(offer(after, DEC).overrides, ())

    def test_shortening_extension_term_change_and_no_resurrection(self) -> None:
        for end, terms in ((NOW, Terms(price=SALE)), (DEC, Terms(price=NEXT))):
            with self.subTest(end=end):
                revision = promo("r", version=NOW, end=end, terms=terms, revises="p")
                data = evidence(base(), promo(end=DEC), revision)
                self.assertEqual(offer(data, NOW - timedelta(seconds=1)).overrides[0].claim_id, "p")
                self.assertEqual(offer(data).terms.price, PRICE if end == NOW else NEXT)
                self.assertEqual(offer(data, end).terms, NORMAL)
                self.assertEqual(offer(data, end).overrides, ())

    def test_revision_of_window_has_separate_version_boundary(self) -> None:
        revision = promo("r", version=NOW, start=NOV, end=DEC, revises="p")
        data = evidence(base(), promo(), revision)
        self.assertEqual(offer(data, NOW - timedelta(seconds=1)).terms.price, SALE)
        self.assertEqual(offer(data).terms, NORMAL)
        self.assertEqual(offer(data, NOV).overrides, (revision,))

    def test_advance_withdrawal_and_later_independent_campaign(self) -> None:
        original = promo(end=DEC)
        withdrawal = withdraw(at=NOV)
        later = promo("later", version=NOV, start=NOV, end=DEC, campaign="later")
        data = evidence(base(), original, withdrawal)
        self.assertIn(withdrawal, knowledge(data, NOW).latest)
        self.assertEqual(offer(data).overrides, (original,))
        self.assertEqual(offer(data, NOV).terms, NORMAL)
        self.assertEqual(offer(data, DEC).overrides, ())
        self.assertEqual(evidence_delta(evidence(base(), original), data).claims, (withdrawal,))
        extended = data.extend(observations=(observation("later"),), claims=(later,))
        self.assertEqual(offer(extended, NOV).overrides, (later,))

    def test_baseline_revision_under_active_campaign_and_expiry(self) -> None:
        data = evidence(base(), base("b", NEXT, NOW, "a"), promo(end=DEC))
        self.assertEqual(offer(data).terms.price, SALE)
        self.assertEqual(offer(data, DEC).terms.price, NEXT)

    def test_conditions_and_zoned_overnight_windows(self) -> None:
        window = DailyWindow("Asia/Shanghai", time(22), time(2))
        claim = promo(conditions=frozenset({"public eligibility"}), window=window)
        data = evidence(base(), claim)
        at = NOW + timedelta(hours=14)
        self.assertEqual(offer(data, at).terms, NORMAL)
        context = frozenset({"public eligibility"})
        self.assertEqual(offer(data, at, conditions=context).terms.price, SALE)
        self.assertEqual(offer(data, NOW + timedelta(hours=18), conditions=context).terms, NORMAL)

    def test_disjoint_fields_and_absolute_quota_no_multipliers(self) -> None:
        quota = Quota(Decimal("200"), "public-units", "5 hours")
        data = evidence(
            base(),
            promo(),
            promo("q", campaign="quota", terms=Terms(quota=quota)),
            promo("s", campaign="restriction", terms=Terms(available=False)),
        )
        self.assertEqual(offer(data).terms, Terms(SALE, quota, False, NORMAL.rules))
        more = data.extend(
            observations=(observation("q2"),),
            claims=(promo("q2", campaign="other", terms=Terms(quota=replace(quota, amount=Decimal("300")))),),
        )
        self.assertIsNone(offer(more).terms.quota)

    def test_no_baseline_invented_or_history_noise(self) -> None:
        data = evidence(promo())
        self.assertEqual(effective_at(data, JAN), EMPTY)
        self.assertEqual(offer(data).terms, Terms(price=SALE))
        self.assertEqual(effective_at(data, NOV), EMPTY)


class ConflictAndPredecessorTests(unittest.TestCase):
    def test_sibling_omissions_are_alternatives_not_composable_campaigns(self) -> None:
        quota = Quota(Decimal("200"), "public-units", "5 hours")
        r = promo("r", version=OCT, revises="p", terms=Terms(price=SALE))
        s = promo("s", version=OCT, revises="p", terms=Terms(quota=quota))
        data = evidence(base(), promo(), r, s)
        view = offer(data)
        self.assertIsNone(view.terms.price)
        self.assertIsNone(view.terms.quota)
        self.assertEqual(view.terms.rules, NORMAL.rules)
        self.assertTrue(view.terms.available)
        self.assertEqual({item.field for item in view.conflicts}, {"lineage", "price", "quota"})
        shared = replace(s, terms=Terms(price=SALE, quota=quota))
        view = offer(evidence(base(), promo(), r, shared))
        self.assertEqual(view.terms.price, SALE)
        self.assertIsNone(view.terms.quota)

    def test_independent_campaign_can_mask_applicability_uncertainty(self) -> None:
        long = promo(end=DEC)
        short = promo("short", end=NOW)
        for price in (SALE, NEXT):
            with self.subTest(price=price):
                independent = promo("independent", campaign="independent", end=DEC, terms=Terms(price=price))
                data = evidence(base(), long, short, independent)
                view = offer(data)
                self.assertEqual(view.terms.price, SALE if price == SALE else None)
                self.assertIn("applicability", {item.field for item in view.conflicts})
                self.assertEqual({item.claim_id for item in view.overrides}, {"p", "independent"})
                before = evidence(base(), long, independent)
                changed = projection_delta(effective_at(before, NOW), effective_at(data, NOW)).offers[0]
                assert changed.before is not None and changed.after is not None
                self.assertEqual(changed.before.terms, changed.after.terms)

    def test_baseline_conflict_survives_override_masking_pr8(self) -> None:
        data = evidence(base(), base("b-base", NEXT), promo())
        diagnostic = offer(data, JAN).conflicts
        self.assertTrue(diagnostic)
        for at in (JAN, NOW, NOV):
            with self.subTest(at=at):
                self.assertEqual(offer(data, at).conflicts, diagnostic)
                self.assertEqual(offer(data, at).terms.price, SALE if at == NOW else None)
        delta = projection_delta(effective_at(data, JAN), effective_at(data, NOW))
        self.assertEqual(delta.conflicts_before, ())
        self.assertEqual(delta.conflicts_after, ())

    def test_boundary_disagreement_only_when_current_relevant_pr8(self) -> None:
        long = promo(end=DEC)
        short = promo("b-boundary", end=NOV)
        data = evidence(base(), long, short)
        self.assertEqual(offer(data, JAN).conflicts, ())
        self.assertEqual(offer(data).terms.price, SALE)
        self.assertEqual(offer(data).conflicts[0].field, "applicability")
        self.assertIsNone(offer(data, NOV).terms.price)
        self.assertEqual(offer(data, NOV).overrides, (long,))
        self.assertEqual(offer(data, DEC).conflicts, ())
        self.assertEqual(offer(data, DEC).terms, NORMAL)

    def test_inactive_boundary_addition_evidence_and_projection_pr8(self) -> None:
        before = evidence(base(), promo(end=DEC))
        boundary = promo("b-boundary", end=NOW)
        after = before.extend(observations=(observation("b-boundary", "secondary"),), claims=(boundary,))
        self.assertEqual(evidence_delta(before, after).claims, (boundary,))
        changed = projection_delta(effective_at(before, NOW), effective_at(after, NOW)).offers[0]
        assert changed.before is not None and changed.after is not None
        self.assertEqual(changed.before.terms.price, SALE)
        self.assertIsNone(changed.after.terms.price)
        self.assertNotIn(boundary, changed.after.overrides)
        self.assertIn("b-boundary", changed.after.conflicts[0].claim_ids)

    def test_independent_conflicts_no_source_order_timestamp_winner(self) -> None:
        data = evidence(base(), promo(), promo("b-price", campaign="other", terms=Terms(price=NEXT)))
        self.assertIsNone(offer(data).terms.price)
        self.assertEqual(offer(data).conflicts[0].claim_ids, ("b-price", "p"))
        equal = evidence(base(), promo(), promo("b-equal", campaign="other"))
        self.assertEqual(len(offer(equal).overrides), 2)
        self.assertEqual(offer(equal).conflicts, ())
        self.assertEqual(offer(equal).terms.price, SALE)

    def test_branch_withdrawal_conflicts_instead_of_winner(self) -> None:
        data = evidence(base(), promo(), withdraw("w", at=NOW), promo("r", version=NOW, revises="p", end=DEC))
        self.assertIsNone(offer(data).terms.price)
        self.assertEqual(offer(data).overrides[0].claim_id, "r")
        self.assertEqual({item.field for item in offer(data).conflicts}, {"lineage", "applicability", "price"})

    def test_cross_source_matches_do_not_suppress_explicit_revision_pr4(self) -> None:
        a = model("a", PRICE)
        other = model("b-price", NEXT)
        revision = model("r", NEXT, at=OCT, revises="a")
        before = evidence(a, other)
        after = evidence(a, other, revision)
        self.assertEqual(evidence_delta(before, after).claims, (revision,))
        self.assertEqual([item.claim_id for item in effective_at(after, NOW).models], ["b-price", "r"])

    def test_batch_revisions_evidence_not_intermediate_projection_pr8(self) -> None:
        for family in ("model", "baseline"):
            for final_price in (SALE, PRICE):
                with self.subTest(family=family, final_price=final_price):
                    a = model("a", PRICE) if family == "model" else base()
                    b = model("b", SALE, at=OCT, revises="a") if family == "model" else base("b", SALE, OCT, "a")
                    c = (
                        model("c", final_price, at=OCT, revises="b")
                        if family == "model"
                        else base("c", final_price, OCT, "b")
                    )
                    before = evidence(a)
                    after = evidence(a, b, c)
                    self.assertEqual(
                        [(item.claim_id, item.revises) for item in evidence_delta(before, after).claims],
                        [("b", "a"), ("c", "b")],
                    )
                    view = effective_at(after, NOW)
                    self.assertNotIn(b, view.models)
                    projected = projection_delta(effective_at(before, NOW), view)
                    if family == "baseline":
                        self.assertEqual(offer(after).baselines, (c,))
                        self.assertEqual(offer(after).terms.price, final_price)
                        endpoint = projected.offers[0]
                        assert endpoint.before is not None and endpoint.after is not None
                        self.assertEqual(endpoint.before.terms.price, PRICE)
                        self.assertEqual(endpoint.after.terms.price, final_price)
                        self.assertNotIn(b, endpoint.after.baselines)
                    else:
                        self.assertEqual(projected.models_before, (a,))
                        self.assertEqual(projected.models_after, (c,))

    def test_missing_rows_never_cessation_pr4(self) -> None:
        data = evidence(base(), promo())
        with self.assertRaisesRegex(ValueError, "retain history"):
            evidence_delta(data, evidence(base()))

    def test_old_history_not_correction_or_cessation_pr4(self) -> None:
        before = evidence(base(), promo())
        old = promo("old", end=OCT, start=JAN, campaign="historical")
        closed = withdraw("closed", at=OCT, revises="old")
        closed = replace(closed, campaign_id="historical")
        after = before.extend(observations=(observation("old"), observation("closed")), claims=(old, closed))
        self.assertEqual(projection_delta(effective_at(before, NOW), effective_at(after, NOW)), NO_PROJECTION_DELTA)
        self.assertEqual([item.claim_id for item in evidence_delta(before, after).claims], ["closed", "old"])

    def test_retrieval_only_silent_stale_stays_stale_pr4(self) -> None:
        data = evidence(base(), promo(), promo("r", version=NOW, revises="p", end=DEC))
        after = data.extend(observations=tuple(replace(item, retrieved_at=DEC) for item in data.observations))
        self.assertEqual(evidence_delta(data, after), EvidenceDelta((), ()))
        self.assertEqual(effective_at(data, NOW), effective_at(after, NOW))
        self.assertEqual(len(knowledge(after, DEC).stale_observations), 3)
        self.assertNotIn(promo(), knowledge(after, NOW).latest)


class ABCAndValidationTests(unittest.TestCase):
    def test_model_context_and_future_revisions(self) -> None:
        benchmark = Benchmark("synthetic-code", "v1", "fixed tasks", "no tools", Decimal("70"), "percent")
        claims = (
            model("price", PRICE),
            model("future", NEXT, at=NOV, revises="price"),
            model("cap", Capability("tools", True)),
            model("score", benchmark),
            model("b-score", replace(benchmark, value=Decimal("60"))),
            model("other-config", replace(benchmark, configuration="tools", value=Decimal("90"))),
        )
        data = evidence(*claims)
        view = effective_at(data, NOW)
        self.assertNotIn(claims[1], view.models)
        self.assertIn(claims[1], knowledge(data, NOW).latest)
        self.assertEqual(len(view.conflicts), 1)
        self.assertEqual(view.conflicts[0].claim_ids, ("b-score", "score"))
        self.assertIn(claims[1], effective_at(data, NOV).models)

    def test_surface_dimensions_unknown_false_and_future_revision(self) -> None:
        payloads = (
            SurfaceEvidence("headless", advertised=True, observed=True),
            SurfaceEvidence("structured-output", advertised=True),
            SurfaceEvidence("workspace-editing", observed=True),
            SurfaceEvidence("model-selection", selectable=True, enforceable=False),
            SurfaceEvidence("physical-model-observability", observed=False),
            SurfaceEvidence("physical-model-enforceability", enforceable=False),
        )
        claims = tuple(surface(str(index), payload) for index, payload in enumerate(payloads))
        revision = surface("r", replace(payloads[3], enforceable=True), at=NOV, revises="3")
        data = evidence(*claims, revision)
        self.assertEqual(effective_at(data, NOW).surfaces, claims)
        self.assertIn(revision, knowledge(data, NOW).latest)
        self.assertIsNone(payloads[1].observed)
        self.assertTrue(all(payload.physical_model_id is None for payload in payloads))
        changed = projection_delta(effective_at(data, NOW), effective_at(data, NOV))
        self.assertIn(revision, changed.surfaces_after)
        independent = evidence(
            surface("a", SurfaceEvidence("headless", advertised=True)),
            surface("b", SurfaceEvidence("headless", observed=False)),
        )
        self.assertEqual(effective_at(independent, NOW).conflicts, ())

    def test_permutation_and_network_free_combined_proof(self) -> None:
        claims = (
            base(),
            base("b", NEXT, NOV, "a"),
            promo(),
            model("m", Capability("tools", None)),
            surface("s", SurfaceEvidence("headless", observed=False)),
        )
        data = evidence(*claims)
        with patch.object(socket, "socket", side_effect=AssertionError("network forbidden")):
            expected = effective_at(data, NOW)
            for order in permutations(claims):
                shuffled = evidence(*order)
                self.assertEqual(shuffled, data)
                self.assertEqual(effective_at(shuffled, NOW), expected)
                self.assertEqual(knowledge(shuffled, NOW), knowledge(data, NOW))
        self.assertEqual(expected.offers[0].terms.price, SALE)

    def test_invalid_lineage_and_semantic_rewriting(self) -> None:
        for claims in (
            (base("a", revises="missing"),),
            (base(), model("m", PRICE, revises="a")),
            (base(), replace(base("b", revises="a"), subject=replace(PLAN, generation="other"))),
            (base(start=NOV), base("b", start=OCT, revises="a")),
            (base("a", revises="b"), base("b", revises="a")),
        ):
            with self.subTest(claims=claims), self.assertRaises(ValueError):
                evidence(*claims)
        with self.assertRaises(ValueError):
            base(revises="a")
        data = evidence(base())
        with self.assertRaisesRegex(ValueError, "identity"):
            data.extend(claims=(base(price=NEXT),))
        with self.assertRaisesRegex(ValueError, "semantics"):
            data.extend(observations=(replace(observation("a"), fresh_until=DEC),))
        with self.assertRaises(ValueError):
            Evidence((), (base(),))
        with self.assertRaises(ValueError):
            Evidence(data.observations, (base(), base()))

    def test_immutable_numeric_and_temporal_validation(self) -> None:
        with self.assertRaises(FrozenInstanceError):
            attribute = "claim_id"
            setattr(base(), attribute, "rewritten")
        for value in ("-1", "NaN", "Infinity"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                Money(Decimal(value), "USD", "month")
        self.assertEqual(Money(Decimal("-0"), "USD", "month"), Money(Decimal("0"), "USD", "month"))
        with self.assertRaises(ValueError):
            base(start=datetime(2026, 1, 1))
        with self.assertRaises(ValueError):
            Period(NOW, NOW)
        with self.assertRaises(ValueError):
            replace(promo(), period=None)
        with self.assertRaises(ValueError):
            replace(withdraw(), revises=None)

    def test_dst_fold_instants_wall_time_and_half_open(self) -> None:
        zone = ZoneInfo("America/New_York")
        first = datetime(2026, 11, 1, 1, 30, tzinfo=zone, fold=0)
        second = datetime(2026, 11, 1, 1, 30, tzinfo=zone, fold=1)
        period = Period(first, second)
        self.assertTrue(period.contains(first))
        self.assertFalse(period.contains(second))
        window = DailyWindow("America/New_York", time(1), time(2))
        self.assertTrue(window.contains(first))
        self.assertTrue(window.contains(second))
        data = evidence(base(), base("b", NEXT, second, "a"))
        self.assertEqual(offer(data, first).terms.price, PRICE)
        self.assertEqual(offer(data, second).terms.price, NEXT)
