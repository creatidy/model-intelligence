"""Deterministic A/B/C representation and semantic-change acceptance proof."""

import json
import unittest
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

from proof_fixtures import (
    BEFORE,
    DURING,
    END,
    LEARNED,
    START,
    disagreement,
    evidence,
    execution,
    model,
    promotion,
    proof_snapshots,
    surfaces,
)

from model_intelligence.domain import (
    Assertion,
    Authority,
    Benchmark,
    Capability,
    ChangeKind,
    DailyWindow,
    Distribution,
    IdentityMode,
    Price,
    Snapshot,
    State,
    Validity,
    semantic_changes,
    serialize_changes,
)


class TemporalProofTests(unittest.TestCase):
    def test_half_open_temporal_boundaries(self) -> None:
        interval = Validity(START, END)
        for at, expected in (
            (BEFORE, State.FUTURE),
            (START, State.CURRENT),
            (END - timedelta(microseconds=1), State.CURRENT),
            (END, State.EXPIRED),
            (END + timedelta(days=30), State.EXPIRED),
        ):
            with self.subTest(at=at):
                self.assertEqual(interval.state_at(at), expected)

    def test_invalid_intervals_and_naive_times(self) -> None:
        for end in (START, BEFORE):
            with self.assertRaises(ValueError):
                _ = Validity(START, end)
        with self.assertRaises(ValueError):
            _ = Validity(datetime(2026, 1, 1))
        with self.assertRaises(ValueError):
            _ = Validity(START).state_at(datetime(2026, 1, 1))

    def test_unbounded_and_observation_not_effective_time(self) -> None:
        fact = promotion()
        self.assertLess(fact.evidence.source.retrieved_at, fact.evidence.validity.start)
        self.assertEqual(fact.evidence.states_at(BEFORE), (State.FUTURE,))
        self.assertEqual(Validity(LEARNED).state_at(END + timedelta(days=1000)), State.CURRENT)

    def test_invalid_provenance_and_freshness(self) -> None:
        source = evidence().source
        with self.assertRaises(ValueError):
            _ = replace(source, observed_at=source.retrieved_at + timedelta(seconds=1))
        with self.assertRaises(ValueError):
            _ = replace(source, retrieved_at=datetime(2026, 1, 1))
        with self.assertRaises(ValueError):
            _ = replace(source, distribution=Distribution.OPEN_LICENSE)
        with self.assertRaises(ValueError):
            _ = replace(evidence(), fresh_until=datetime(2026, 1, 1))
        with self.assertRaises(ValueError):
            _ = replace(evidence(), superseded_at=datetime(2026, 1, 1))
        self.assertEqual(replace(source, authority=Authority.SECONDARY).authority, Authority.SECONDARY)
        self.assertEqual(replace(source, distribution=Distribution.OPEN_LICENSE, license_id="MIT").license_id, "MIT")

    def test_stale_is_not_false_and_does_not_extend_expiry(self) -> None:
        fact = replace(execution(), evidence=replace(evidence(), fresh_until=START))
        snapshot = Snapshot(1, DURING, (fact,))
        self.assertEqual(snapshot.states(fact), (State.CURRENT, State.STALE))
        self.assertTrue(fact.supported)
        self.assertTrue(snapshot.effective())
        offer = replace(promotion(), evidence=replace(promotion().evidence, fresh_until=START))
        self.assertIn(State.STALE, Snapshot(1, END, (offer,)).states(offer))
        self.assertIn(State.EXPIRED, Snapshot(1, END, (offer,)).states(offer))
        self.assertFalse(offer.window_active_at(END))

    def test_superseded_evidence_is_retained_not_effective(self) -> None:
        old = replace(model(), evidence=replace(evidence(), superseded_at=START))
        self.assertTrue(Snapshot(1, BEFORE, (old,)).effective())
        snapshot = Snapshot(2, START, (old, disagreement()))
        self.assertIn(old, snapshot.facts)
        self.assertIn(State.SUPERSEDED, snapshot.states(old))
        self.assertEqual(snapshot.conflicts(), ())

    def test_source_conflict_survives_normalization(self) -> None:
        first, second = model(), disagreement()
        snapshot = Snapshot(1, DURING, (first, second, first))
        self.assertEqual(len(snapshot.facts), 2)
        self.assertEqual(len(snapshot.conflicts()), 1)
        for fact in (first, second):
            self.assertIn(State.CONFLICTING, snapshot.states(fact))
        self.assertEqual(
            {f.evidence.source.source_id for f in snapshot.facts}, {"fixture-primary", "fixture-secondary"}
        )
        self.assertIn('"0.1"', snapshot.serialize())
        self.assertIn('"0.2"', snapshot.serialize())

    def test_stale_disagreement_remains_visible(self) -> None:
        stale = replace(disagreement(), evidence=replace(disagreement().evidence, fresh_until=START))
        snapshot = Snapshot(1, DURING, (model(), stale))
        self.assertIn(State.STALE, snapshot.states(stale))
        self.assertIn(State.CONFLICTING, snapshot.states(stale))

    def test_benchmark_contexts_are_not_universal_scores(self) -> None:
        first = model()
        second = replace(first, benchmark=replace(first.benchmark, configuration="temperature=1", score=Decimal("50")))
        snapshot = Snapshot(1, DURING, (first, second))
        self.assertEqual(snapshot.conflicts(), ())
        comparable = replace(first, benchmark=replace(first.benchmark, score=Decimal("50")), evidence=evidence("other"))
        self.assertEqual(len(Snapshot(1, DURING, (first, comparable)).conflicts()), 1)

    def test_benchmark_conflict_states_only_mark_comparable_participants(self) -> None:
        first = model()
        second = replace(first, benchmark=replace(first.benchmark, score=Decimal("50")), evidence=evidence("other"))
        unrelated = replace(
            first,
            benchmark=replace(first.benchmark, configuration="temperature=1", score=Decimal("90")),
            evidence=evidence("another-context"),
        )
        snapshot = Snapshot(1, DURING, (first, second, unrelated))
        self.assertEqual(len(snapshot.conflicts()), 1)
        self.assertIn(State.CONFLICTING, snapshot.states(first))
        self.assertIn(State.CONFLICTING, snapshot.states(second))
        self.assertNotIn(State.CONFLICTING, snapshot.states(unrelated))
        for disputed in (
            replace(unrelated, price=Price(Decimal("0.20"), Decimal("0.30"), "USD")),
            replace(unrelated, capabilities=("text",)),
        ):
            with self.subTest(disputed=disputed):
                self.assertIn(State.CONFLICTING, Snapshot(1, DURING, (first, second, disputed)).states(disputed))

    def test_daily_overnight_window_boundaries(self) -> None:
        offer = promotion()
        for hour, minute, active in ((22, 59, False), (23, 0, True), (0, 0, True), (8, 59, True), (9, 0, False)):
            at = datetime(2026, 9, 5, hour, minute, tzinfo=ZoneInfo("Asia/Singapore"))
            with self.subTest(at=at):
                self.assertEqual(offer.window_active_at(at), active)
        self.assertFalse(offer.window_active_at(BEFORE))
        self.assertTrue(offer.window_active_at(START))
        self.assertFalse(offer.window_active_at(END))
        self.assertFalse(offer.window_active_at(END + timedelta(hours=14)))

    def test_daytime_window_and_invalid_windows(self) -> None:
        window = DailyWindow("UTC", time(9), time(17))
        self.assertTrue(window.contains(datetime(2026, 1, 1, 9, tzinfo=UTC)))
        self.assertFalse(window.contains(datetime(2026, 1, 1, 17, tzinfo=UTC)))
        with self.assertRaises(ValueError):
            _ = DailyWindow("UTC", time(9), time(9))
        with self.assertRaises(ValueError):
            _ = DailyWindow("UTC", time(9, tzinfo=UTC), time(17))

    def test_dst_window_uses_local_wall_time(self) -> None:
        window = DailyWindow("America/New_York", time(1), time(2))
        # Both occurrences of 01:30 during the autumn fold are in the daily window.
        for hour in (5, 6):
            self.assertTrue(window.contains(datetime(2026, 11, 1, hour, 30, tzinfo=UTC)))
        self.assertFalse(window.contains(datetime(2026, 11, 1, 7, tzinfo=UTC)))

    def test_offer_terms_are_conditional_and_not_composed(self) -> None:
        offer = promotion()
        self.assertEqual(offer.generation, "fixture-credits-v3")
        self.assertEqual(offer.quota_multiplier, Decimal("2"))
        self.assertIn("baseline quota not exhausted", offer.conditions)
        self.assertEqual(offer.composable_with, ())
        self.assertIn("NOT API price", offer.quota_basis)
        with self.assertRaises(ValueError):
            _ = replace(offer, evidence=evidence())

    def test_execution_assertions_are_independent(self) -> None:
        snapshot = Snapshot(1, DURING, surfaces())
        self.assertEqual(snapshot.conflicts(), ())
        headless = [fact for fact in surfaces() if fact.capability == Capability.HEADLESS]
        self.assertEqual(
            {fact.assertion: fact.supported for fact in headless},
            {
                Assertion.ADVERTISED: True,
                Assertion.OBSERVED: False,
            },
        )
        selection = execution(Capability.MODEL_SELECTION, Assertion.SELECTABLE)
        enforced = execution(Capability.MODEL_SELECTION, Assertion.ENFORCEABLE, False)
        self.assertEqual(Snapshot(1, DURING, (selection, enforced)).conflicts(), ())
        observed = execution(Capability.MODEL_SELECTION, Assertion.OBSERVED, False)
        advertised = execution(Capability.MODEL_SELECTION, Assertion.ADVERTISED)
        self.assertEqual(len({f.assertion for f in (selection, enforced, observed, advertised)}), 4)

    def test_unknown_does_not_assert_false_or_conflict(self) -> None:
        unknown = execution(Capability.PHYSICAL_MODEL_OBSERVABILITY, Assertion.OBSERVED, None)
        negative = replace(unknown, supported=False, evidence=evidence("other"))
        snapshot = Snapshot(1, DURING, (unknown, negative))
        self.assertIn(State.UNKNOWN, snapshot.states(unknown))
        self.assertIsNone(unknown.supported)
        self.assertEqual(snapshot.conflicts(), ())

    def test_provider_managed_has_no_invented_physical_model(self) -> None:
        managed = execution(Capability.PHYSICAL_MODEL_ENFORCEABILITY, Assertion.ENFORCEABLE, False)
        self.assertIsNone(managed.physical_model_id)
        with self.assertRaises(ValueError):
            _ = replace(managed, physical_model_id="z-ai:glm-5.3-flash")
        with self.assertRaises(ValueError):
            _ = replace(managed, supported=True)
        with self.assertRaises(ValueError):
            _ = replace(managed, identity_mode=IdentityMode.PHYSICAL)
        physical = replace(managed, identity_mode=IdentityMode.PHYSICAL, physical_model_id="z-ai:glm-5.3-flash")
        self.assertEqual(physical.physical_model_id, "z-ai:glm-5.3-flash")

    def test_invalid_or_ambiguous_identity(self) -> None:
        for identifier in (
            "",
            "GLM-5.3-Flash",
            "z-ai:auto",
            "z-ai:latest",
            "z-ai:unknown",
            "z-ai:default",
            " z-ai:glm-5.3-flash",
        ):
            with self.subTest(identifier=identifier), self.assertRaises(ValueError):
                _ = replace(model(), model_id=identifier)
        with self.assertRaises(ValueError):
            _ = replace(model(), provider_model_id=" ")
        with self.assertRaises(ValueError):
            _ = replace(execution(), identity_mode=IdentityMode.PHYSICAL, physical_model_id="z-ai:auto")

    def test_numeric_validation(self) -> None:
        for value in (Decimal("-1"), Decimal("NaN"), Decimal("Infinity")):
            with self.assertRaises(ValueError):
                _ = Price(value, Decimal("1"), "USD")
            with self.assertRaises(ValueError):
                _ = replace(promotion(), quota_multiplier=value)
        with self.assertRaises(ValueError):
            _ = replace(promotion(), quota_multiplier=Decimal("0"))
        with self.assertRaises(ValueError):
            _ = replace(model().price, currency="usd")
        with self.assertRaises(ValueError):
            _ = Benchmark("b", "1", "", "c", Decimal("1"), "%")

    def test_snapshot_order_identity_serialization(self) -> None:
        _, snapshot, _ = proof_snapshots()
        reordered = Snapshot(snapshot.version, snapshot.at, tuple(reversed(snapshot.facts)))
        self.assertEqual(snapshot.snapshot_id, reordered.snapshot_id)
        self.assertEqual(snapshot.serialize(), reordered.serialize())
        self.assertEqual(len(snapshot.snapshot_id), 64)
        self.assertNotEqual(snapshot.snapshot_id, replace(snapshot, version=3).snapshot_id)
        self.assertNotEqual(snapshot.snapshot_id, replace(snapshot, at=END).snapshot_id)
        self.assertEqual(json.loads(snapshot.serialize())["schema_version"], 1)

    def test_canonical_decimal_timezone_and_set_order(self) -> None:
        original = model()
        alternate = replace(
            original,
            price=Price(Decimal("0.1000"), Decimal("0.3000"), "USD"),
            capabilities=("tool-use", "text", "text"),
        )
        shifted = DURING.astimezone(ZoneInfo("Asia/Singapore"))
        self.assertEqual(Snapshot(1, DURING, (original,)).snapshot_id, Snapshot(1, shifted, (alternate,)).snapshot_id)
        permuted = replace(promotion(), conditions=tuple(reversed(promotion().conditions)))
        self.assertEqual(Snapshot(1, DURING, (promotion(),)).serialize(), Snapshot(1, DURING, (permuted,)).serialize())

    def test_snapshot_and_values_are_immutable(self) -> None:
        snapshot = Snapshot(1, DURING, (model(),))
        attribute = "version"
        with self.assertRaises(FrozenInstanceError):
            setattr(snapshot, attribute, 2)
        attribute = "source_id"
        with self.assertRaises(FrozenInstanceError):
            setattr(snapshot.facts[0].evidence.source, attribute, "changed")

    def test_invalid_snapshot_and_comparison(self) -> None:
        with self.assertRaises(ValueError):
            _ = Snapshot(0, DURING, ())
        with self.assertRaises(ValueError):
            _ = Snapshot(1, LEARNED - timedelta(seconds=1), (model(),))
        with self.assertRaises(ValueError):
            _ = Snapshot(1, datetime(2026, 1, 1), ())
        snapshot = Snapshot(1, DURING, (model(),))
        with self.assertRaises(ValueError):
            _ = snapshot.states(disagreement())
        with self.assertRaises(ValueError):
            _ = semantic_changes(snapshot, snapshot)
        with self.assertRaises(ValueError):
            _ = semantic_changes(snapshot, Snapshot(2, BEFORE, (model(),)))

    def test_abc_semantic_proof_and_no_repeated_conflict_noise(self) -> None:
        before, during, expired = proof_snapshots()
        activation = semantic_changes(before, during)
        self.assertEqual(
            {change.kind for change in activation},
            {
                ChangeKind.PROMOTION_STARTED,
                ChangeKind.PRICE_CHANGED,
                ChangeKind.EVIDENCE_CONFLICT_DETECTED,
            },
        )
        ending = semantic_changes(during, expired)
        self.assertEqual(
            {change.kind for change in ending}, {ChangeKind.PROMOTION_ENDED, ChangeKind.EXECUTION_SURFACE_CHANGED}
        )
        self.assertEqual(len(ending), 2)
        self.assertEqual(len(expired.conflicts()), 1)
        self.assertIn(State.EXPIRED, expired.states(promotion()))

    def test_initial_model_and_surface_observed(self) -> None:
        empty = Snapshot(1, DURING, ())
        populated = Snapshot(2, DURING, (model(), execution()))
        self.assertEqual(
            {change.kind for change in semantic_changes(empty, populated)},
            {
                ChangeKind.MODEL_OBSERVED,
                ChangeKind.EXECUTION_SURFACE_CHANGED,
            },
        )

    def test_new_benchmark_is_not_a_new_release(self) -> None:
        first = model()
        benchmark = replace(first, benchmark=replace(first.benchmark, version="2"))
        events = semantic_changes(Snapshot(1, DURING, (first,)), Snapshot(2, DURING, (first, benchmark)))
        self.assertEqual({event.kind for event in events}, {ChangeKind.MODEL_EVIDENCE_CHANGED})

    def test_offer_terms_and_interval_change(self) -> None:
        first = promotion()
        for second in (
            replace(first, monthly_price=Decimal("19")),
            replace(first, evidence=replace(first.evidence, validity=Validity(START, END + timedelta(days=1)))),
        ):
            with self.subTest(second=second):
                events = semantic_changes(Snapshot(1, DURING, (first,)), Snapshot(2, DURING, (second,)))
                self.assertEqual({event.kind for event in events}, {ChangeKind.OFFER_CHANGED})

    def test_missing_offer_is_not_proof_of_expiry(self) -> None:
        events = semantic_changes(Snapshot(1, DURING, (promotion(),)), Snapshot(2, DURING, ()))
        self.assertEqual(events, ())

    def test_partial_source_removal_cannot_use_historical_offer_as_end_evidence(self) -> None:
        active = promotion()
        historical = replace(
            active, evidence=replace(evidence("historical", bounded=True), validity=Validity(LEARNED, START))
        )
        before = Snapshot(1, DURING, (active, historical))
        self.assertEqual(tuple(before.effective().values()), ((active,),))
        for at in (DURING + timedelta(seconds=1), END):
            with self.subTest(at=at):
                after = Snapshot(2, at, (historical,))
                self.assertIn(State.EXPIRED, after.states(historical))
                self.assertEqual(after.effective(), {})
                self.assertEqual(semantic_changes(before, after), ())

    def test_promotion_end_needs_evidence_for_every_previously_effective_assertion(self) -> None:
        early = promotion()
        later = replace(
            early, evidence=replace(evidence("later", bounded=True), validity=Validity(START, END + timedelta(days=1)))
        )
        before = Snapshot(1, DURING, (early, later))
        after = Snapshot(2, END, (early,))
        self.assertEqual(semantic_changes(before, after), ())

    def test_last_model_evidence_expiry_emits_semantic_change(self) -> None:
        fact = replace(model(), evidence=replace(evidence(), validity=Validity(LEARNED, END)))
        before = Snapshot(1, DURING, (fact,))
        after = Snapshot(2, END, (fact,))
        self.assertTrue(before.effective())
        self.assertEqual(after.effective(), {})
        self.assertIn(State.EXPIRED, after.states(fact))
        self.assertEqual([c.kind for c in semantic_changes(before, after)], [ChangeKind.MODEL_EVIDENCE_CHANGED])

    def test_last_model_evidence_supersession_emits_semantic_change(self) -> None:
        fact = replace(model(), evidence=replace(evidence(), superseded_at=END))
        before = Snapshot(1, DURING, (fact,))
        after = Snapshot(2, END, (fact,))
        self.assertTrue(before.effective())
        self.assertEqual(after.effective(), {})
        self.assertIn(State.SUPERSEDED, after.states(fact))
        self.assertEqual([c.kind for c in semantic_changes(before, after)], [ChangeKind.MODEL_EVIDENCE_CHANGED])

    def test_equivalent_model_replacement_is_semantically_silent(self) -> None:
        for prior_evidence in (
            replace(evidence(), validity=Validity(LEARNED, END)),
            replace(evidence(), superseded_at=END),
        ):
            with self.subTest(evidence=prior_evidence):
                prior = replace(model(), evidence=prior_evidence)
                replacement = replace(model(), evidence=replace(evidence("replacement"), validity=Validity(END)))
                before = Snapshot(1, DURING, (prior,))
                after = Snapshot(2, END, (prior, replacement))
                self.assertEqual(tuple(after.effective().values()), ((replacement,),))
                self.assertEqual(semantic_changes(before, after), ())

    def test_model_source_removal_is_not_evidence_of_expiry(self) -> None:
        fact = replace(model(), evidence=replace(evidence(), validity=Validity(LEARNED, END)))
        self.assertEqual(semantic_changes(Snapshot(1, DURING, (fact,)), Snapshot(2, END, ())), ())

    def test_offer_cessation_and_supplied_correction_are_distinct(self) -> None:
        prior = promotion()
        for supplied, expected in (
            (replace(prior, evidence=evidence("other", bounded=True)), []),
            (replace(prior, monthly_price=Decimal("19")), [ChangeKind.OFFER_CHANGED]),
            (
                replace(prior, evidence=replace(prior.evidence, validity=Validity(LEARNED, START))),
                [ChangeKind.OFFER_CHANGED],
            ),
        ):
            with self.subTest(supplied=supplied):
                before = Snapshot(1, DURING, (prior,))
                after = Snapshot(2, END, (supplied,))
                self.assertEqual(after.effective(), {})
                self.assertEqual([c.kind for c in semantic_changes(before, after)], expected)

    def test_retained_offer_retrieval_refresh_still_establishes_expiry(self) -> None:
        prior = promotion()
        refreshed = replace(
            prior,
            evidence=replace(
                prior.evidence,
                source=replace(prior.evidence.source, retrieved_at=DURING),
            ),
        )
        changes = semantic_changes(Snapshot(1, DURING, (prior,)), Snapshot(2, END, (refreshed,)))
        self.assertEqual([c.kind for c in changes], [ChangeKind.PROMOTION_ENDED])

    def test_supplied_offer_correction_to_earlier_end_emits_change_not_end(self) -> None:
        prior = promotion()
        at = DURING + timedelta(seconds=1)
        corrected = replace(prior, evidence=replace(prior.evidence, validity=Validity(START, at)))
        before = Snapshot(1, DURING, (prior,))
        after = Snapshot(2, at, (corrected,))
        self.assertEqual(after.effective(), {})
        self.assertIn(State.EXPIRED, after.states(corrected))
        self.assertEqual([c.kind for c in semantic_changes(before, after)], [ChangeKind.OFFER_CHANGED])

    def test_supplied_offer_correction_to_future_start_emits_change(self) -> None:
        prior = promotion()
        corrected = replace(prior, evidence=replace(prior.evidence, validity=Validity(DURING + timedelta(days=1), END)))
        before = Snapshot(1, DURING, (prior,))
        after = Snapshot(2, DURING + timedelta(seconds=1), (corrected,))
        self.assertEqual(after.effective(), {})
        self.assertIn(State.FUTURE, after.states(corrected))
        self.assertEqual([c.kind for c in semantic_changes(before, after)], [ChangeKind.OFFER_CHANGED])

    def test_supplied_offer_correction_takes_precedence_over_proven_cessation(self) -> None:
        prior = promotion()
        closed = replace(prior, evidence=replace(prior.evidence, superseded_at=END))
        corrected = replace(
            prior,
            evidence=replace(
                prior.evidence,
                validity=Validity(
                    END + timedelta(days=1),
                    END + timedelta(days=2),
                ),
            ),
        )
        before = Snapshot(1, DURING, (prior,))
        after = Snapshot(2, END, (closed, corrected))
        self.assertEqual(after.effective(), {})
        self.assertIn(State.EXPIRED, after.states(closed))
        self.assertIn(State.SUPERSEDED, after.states(closed))
        # Supplied changed claims are more precise than treating their correction as an end.
        self.assertEqual([c.kind for c in semantic_changes(before, after)], [ChangeKind.OFFER_CHANGED])

    def test_existing_same_source_history_is_not_a_supplied_correction(self) -> None:
        prior = promotion()
        historical = replace(prior, evidence=replace(prior.evidence, validity=Validity(LEARNED, START)))
        before = Snapshot(1, DURING, (prior, historical))
        after = Snapshot(2, DURING + timedelta(seconds=1), (historical,))
        self.assertEqual(semantic_changes(before, after), ())

    def test_supplied_correction_requires_same_offer_and_source(self) -> None:
        prior = promotion()
        at = DURING + timedelta(seconds=1)
        corrected = replace(prior, evidence=replace(prior.evidence, validity=Validity(START, at)))
        for unrelated in (
            replace(corrected, evidence=replace(corrected.evidence, source=evidence("other").source)),
            replace(corrected, promotion_id="another-promotion"),
        ):
            with self.subTest(unrelated=unrelated):
                self.assertEqual(semantic_changes(Snapshot(1, DURING, (prior,)), Snapshot(2, at, (unrelated,))), ())

    def test_reretrieved_stale_evidence_preserves_freshness_history(self) -> None:
        prior = replace(execution(), evidence=replace(evidence(), fresh_until=START))
        refreshed = replace(
            prior,
            evidence=replace(
                prior.evidence,
                source=replace(
                    prior.evidence.source,
                    retrieved_at=DURING,
                ),
            ),
        )
        before = Snapshot(1, DURING, (prior,))
        after = Snapshot(2, DURING, (refreshed,))
        self.assertEqual(refreshed.evidence.fresh_until, START)
        self.assertIn(State.STALE, after.states(refreshed))
        self.assertTrue(refreshed.supported)
        self.assertTrue(after.effective())
        same_version = replace(after, version=before.version)
        self.assertNotEqual(before.serialize(), same_version.serialize())
        self.assertNotEqual(before.snapshot_id, same_version.snapshot_id)
        self.assertEqual(semantic_changes(before, after), ())

    def test_reretrieved_superseded_evidence_does_not_reactivate(self) -> None:
        prior = replace(model(), evidence=replace(evidence(), superseded_at=START))
        refreshed = replace(
            prior,
            evidence=replace(
                prior.evidence,
                source=replace(
                    prior.evidence.source,
                    retrieved_at=DURING,
                ),
            ),
        )
        before = Snapshot(1, DURING, (prior,))
        after = Snapshot(2, DURING, (refreshed,))
        self.assertEqual(refreshed.evidence.superseded_at, START)
        self.assertIn(State.SUPERSEDED, after.states(refreshed))
        self.assertEqual(after.retained(), {})
        self.assertEqual(after.effective(), {})
        same_version = replace(after, version=before.version)
        self.assertNotEqual(before.serialize(), same_version.serialize())
        self.assertNotEqual(before.snapshot_id, same_version.snapshot_id)
        self.assertEqual(semantic_changes(before, after), ())

    def test_evidence_boundaries_are_independent_aware_and_canonical(self) -> None:
        boundary = (LEARNED - timedelta(seconds=1)).astimezone(ZoneInfo("Asia/Singapore"))
        historical = replace(evidence(), fresh_until=boundary, superseded_at=boundary)
        self.assertEqual(historical.fresh_until, boundary.astimezone(UTC))
        self.assertEqual(historical.superseded_at, boundary.astimezone(UTC))
        assert historical.fresh_until is not None
        assert historical.superseded_at is not None
        self.assertIs(historical.fresh_until.tzinfo, UTC)
        self.assertIs(historical.superseded_at.tzinfo, UTC)
        self.assertIn(State.STALE, historical.states_at(LEARNED))
        self.assertIn(State.SUPERSEDED, historical.states_at(LEARNED))

    def test_explicit_offer_supersession_establishes_end_of_applicability(self) -> None:
        prior = promotion()
        superseded = replace(prior, evidence=replace(prior.evidence, superseded_at=DURING))
        before = Snapshot(1, START, (prior,))
        after = Snapshot(2, DURING, (superseded,))
        self.assertIn(superseded, after.facts)
        self.assertEqual(after.retained(), {})
        self.assertEqual(after.effective(), {})
        self.assertEqual([c.kind for c in semantic_changes(before, after)], [ChangeKind.PROMOTION_ENDED])

    def test_present_retained_and_effective_are_distinct(self) -> None:
        current = model()
        future = promotion()
        expired = replace(
            future, evidence=replace(evidence("expired", bounded=True), validity=Validity(LEARNED, BEFORE))
        )
        superseded = replace(current, evidence=replace(evidence("superseded"), superseded_at=BEFORE))
        snapshot = Snapshot(1, BEFORE, (current, future, expired, superseded))
        retained = {f for facts in snapshot.retained().values() for f in facts}
        effective = {f for facts in snapshot.effective().values() for f in facts}
        self.assertEqual(set(snapshot.facts), {current, future, expired, superseded})
        self.assertEqual(retained, {current, future, expired})
        self.assertEqual(effective, {current})

    def test_unchanged_and_retrieval_only_changes_are_silent(self) -> None:
        fact = model()
        before = Snapshot(1, DURING, (fact,))
        refreshed = replace(
            fact,
            evidence=replace(
                fact.evidence,
                source=replace(
                    fact.evidence.source,
                    observed_at=START,
                    retrieved_at=START,
                ),
            ),
        )
        after = Snapshot(2, DURING + timedelta(seconds=1), (refreshed,))
        self.assertNotEqual(before.snapshot_id, after.snapshot_id)
        self.assertEqual(semantic_changes(before, after), ())
        self.assertEqual(semantic_changes(before, Snapshot(2, END, (fact,))), ())

    def test_semantic_output_is_deterministic(self) -> None:
        before, after, _ = proof_snapshots()
        changes = semantic_changes(before, after)
        reversed_before = replace(before, facts=tuple(reversed(before.facts)))
        reversed_after = replace(after, facts=tuple(reversed(after.facts)))
        self.assertEqual(changes, semantic_changes(reversed_before, reversed_after))
        self.assertEqual(serialize_changes(changes), serialize_changes(tuple(reversed(changes))))
        self.assertEqual(serialize_changes(changes), serialize_changes((*changes, *changes)))

    def test_all_fixtures_run_without_network(self) -> None:
        with patch("socket.socket", side_effect=AssertionError("network forbidden")):
            before, during, expired = proof_snapshots()
            self.assertTrue(semantic_changes(before, during))
            self.assertTrue(semantic_changes(during, expired))

    def test_signed_zero_is_canonical_and_not_a_conflict(self) -> None:
        positive = replace(model(), price=Price(Decimal("0"), Decimal("0.3"), "USD"))
        negative = replace(positive, price=Price(Decimal("-0.00"), Decimal("0.3"), "USD"))
        for facts in ((positive,), (negative,), (positive, negative), (negative, positive)):
            self.assertEqual(Snapshot(1, DURING, facts).snapshot_id, Snapshot(1, DURING, (positive,)).snapshot_id)
        other_source = replace(negative, evidence=evidence("other"))
        self.assertEqual(Snapshot(1, DURING, (positive, other_source)).conflicts(), ())

    def test_price_conflict_independent_of_benchmark_context(self) -> None:
        different_benchmark = replace(
            disagreement(), benchmark=replace(model().benchmark, configuration="temperature=1")
        )
        snapshot = Snapshot(2, DURING, (model(), different_benchmark))
        self.assertEqual(len(snapshot.conflicts()), 1)
        events = semantic_changes(Snapshot(1, DURING, (model(),)), snapshot)
        self.assertIn(ChangeKind.PRICE_CHANGED, {event.kind for event in events})

    def test_physical_model_contexts_are_distinct(self) -> None:
        first = replace(execution(), identity_mode=IdentityMode.PHYSICAL, physical_model_id="z-ai:glm-5.3-flash")
        second = replace(first, physical_model_id="other:model-1")
        self.assertEqual(Snapshot(1, DURING, (first, second)).conflicts(), ())
        contrary = replace(first, supported=False, evidence=evidence("other"))
        self.assertEqual(len(Snapshot(1, DURING, (first, contrary)).conflicts()), 1)

    def test_offer_expiry_disagreement_is_a_conflict(self) -> None:
        first = promotion()
        second = replace(
            first, evidence=replace(evidence("other", bounded=True), validity=Validity(START, END + timedelta(days=1)))
        )
        during = Snapshot(1, DURING, (first, second))
        self.assertEqual(len(during.conflicts()), 1)
        for at in (END, END + timedelta(microseconds=1), END + timedelta(hours=12)):
            with self.subTest(at=at):
                after = Snapshot(2, at, (first, second))
                # Retain the disagreement without making the earlier expired assertion effective.
                self.assertEqual(after.conflicts(), during.conflicts())
                self.assertIn(State.EXPIRED, after.states(first))
                self.assertIn(State.CONFLICTING, after.states(first))
                self.assertIn(State.CURRENT, after.states(second))
                self.assertIn(State.CONFLICTING, after.states(second))
                self.assertEqual(tuple(after.effective().values()), ((second,),))
                kinds = {c.kind for c in semantic_changes(during, after)}
                self.assertNotIn(ChangeKind.PROMOTION_ENDED, kinds)
                self.assertNotIn(ChangeKind.EVIDENCE_CONFLICT_DETECTED, kinds)
        expired = Snapshot(3, END + timedelta(days=1), (first, second))
        self.assertEqual(expired.effective(), {})
        self.assertEqual(expired.conflicts(), during.conflicts())
        self.assertEqual([c.kind for c in semantic_changes(during, expired)], [ChangeKind.PROMOTION_ENDED])
        superseded = replace(first, evidence=replace(first.evidence, superseded_at=END))
        resolved = Snapshot(3, END, (superseded, second))
        self.assertEqual(resolved.conflicts(), ())
        self.assertNotIn(State.CONFLICTING, resolved.states(superseded))

    def test_superseded_offer_history_does_not_hide_expiry(self) -> None:
        current = promotion()
        old = replace(
            current,
            evidence=replace(
                evidence("superseded", bounded=True),
                validity=Validity(START, END + timedelta(days=1)),
                superseded_at=START,
            ),
        )
        before = Snapshot(1, DURING, (current, old))
        after = Snapshot(2, END, (current, old))
        self.assertEqual({c.kind for c in semantic_changes(before, after)}, {ChangeKind.PROMOTION_ENDED})

    def test_fold_timestamps_are_instant_based(self) -> None:
        zone = ZoneInfo("America/New_York")
        early = datetime(2026, 11, 1, 1, 30, tzinfo=zone, fold=0)
        late = datetime(2026, 11, 1, 1, 30, tzinfo=zone, fold=1)
        self.assertEqual(Validity(late).state_at(early), State.FUTURE)
        self.assertEqual(Validity(early, late).state_at(late), State.EXPIRED)
        with self.assertRaises(ValueError):
            _ = Validity(late, early)
        with self.assertRaises(ValueError):
            _ = replace(evidence().source, observed_at=late, retrieved_at=early)
        later_source = replace(evidence().source, observed_at=early, retrieved_at=late)
        fact = replace(model(), evidence=replace(evidence(), source=later_source, fresh_until=late))
        with self.assertRaises(ValueError):
            _ = Snapshot(1, early, (fact,))
        self.assertNotEqual(Snapshot(1, early, ()).snapshot_id, Snapshot(1, late, ()).snapshot_id)
        self.assertEqual(semantic_changes(Snapshot(1, early, ()), Snapshot(2, late, ())), ())
        self.assertNotIn(State.STALE, fact.evidence.states_at(early))
        self.assertIn(State.STALE, fact.evidence.states_at(late))

    def test_historical_identity_is_not_a_new_model(self) -> None:
        old = replace(model(), evidence=replace(evidence(), superseded_at=START))
        before = Snapshot(1, DURING, (old,))
        after = Snapshot(2, DURING, (old, model()))
        self.assertEqual({c.kind for c in semantic_changes(before, after)}, {ChangeKind.MODEL_EVIDENCE_CHANGED})

    def test_unknown_does_not_participate_in_known_conflict(self) -> None:
        yes = execution()
        no = replace(yes, supported=False, evidence=evidence("other"))
        unknown = replace(yes, supported=None, evidence=evidence("unknown"))
        snapshot = Snapshot(1, DURING, (yes, no, unknown))
        self.assertIn(State.CONFLICTING, snapshot.states(yes))
        self.assertNotIn(State.CONFLICTING, snapshot.states(unknown))

    def test_same_source_historical_observation_cannot_certify_live_assertion_cessation(self) -> None:
        for original in (promotion(), model()):
            historic = replace(original, evidence=replace(original.evidence, superseded_at=BEFORE))
            current = replace(
                original,
                evidence=replace(
                    original.evidence,
                    source=replace(original.evidence.source, observed_at=START, retrieved_at=START),
                ),
            )
            before = Snapshot(1, DURING, (historic, current))
            after = Snapshot(2, DURING + timedelta(seconds=1), (historic,))
            with self.subTest(family=type(original).__name__):
                self.assertEqual(tuple(before.effective().values()), ((current,),))
                self.assertEqual(after.effective(), {})
                self.assertIn(State.CURRENT, current.evidence.states_at(after.at))
                self.assertEqual(semantic_changes(before, after), ())

    def test_newly_included_superseded_offer_history_is_not_a_correction(self) -> None:
        current = promotion()
        historic = replace(
            current,
            monthly_price=Decimal("9"),
            evidence=replace(current.evidence, validity=Validity(LEARNED, START), superseded_at=BEFORE),
        )
        before = Snapshot(1, DURING, (current,))
        for at, expected in (
            (DURING + timedelta(seconds=1), []),
            (END, [ChangeKind.PROMOTION_ENDED]),
        ):
            with self.subTest(at=at):
                after = Snapshot(2, at, (current, historic))
                without_history = Snapshot(2, at, (current,))
                self.assertEqual(after.effective(), without_history.effective())
                self.assertEqual(after.conflicts(), ())
                self.assertIn(State.SUPERSEDED, after.states(historic))
                self.assertEqual([c.kind for c in semantic_changes(before, after)], expected)

    def test_cessation_matches_reference_and_observation_not_retrieval(self) -> None:
        for prior in (promotion(), model()):
            for source, matches in (
                (replace(prior.evidence.source, retrieved_at=DURING), True),
                (replace(prior.evidence.source, observed_at=DURING, retrieved_at=DURING), False),
                (replace(prior.evidence.source, reference="fixture:another-observation"), False),
            ):
                closed = replace(prior, evidence=replace(prior.evidence, source=source, superseded_at=DURING))
                before = Snapshot(1, START, (prior,))
                after = Snapshot(2, DURING, (closed,))
                with self.subTest(family=type(prior).__name__, source=source):
                    self.assertEqual(bool(semantic_changes(before, after)), matches)

    def test_new_offer_observation_can_reintroduce_superseded_terms(self) -> None:
        prior = promotion()
        historical = replace(
            prior,
            monthly_price=Decimal("19"),
            evidence=replace(
                prior.evidence,
                validity=Validity(END + timedelta(days=1), END + timedelta(days=2)),
                superseded_at=BEFORE,
            ),
        )
        closed = replace(prior, evidence=replace(prior.evidence, superseded_at=END))
        supplied = replace(
            historical,
            evidence=replace(
                historical.evidence,
                source=replace(
                    historical.evidence.source,
                    reference="fixture:new-correction",
                    observed_at=DURING,
                    retrieved_at=DURING,
                ),
                superseded_at=None,
            ),
        )
        for old_facts in ((prior,), (prior, historical)):
            before = Snapshot(1, DURING, old_facts)
            after = Snapshot(2, END, (closed, supplied))
            with self.subTest(history=historical in old_facts):
                self.assertEqual(after.effective(), {})
                self.assertIn(State.FUTURE, after.states(supplied))
                self.assertEqual([c.kind for c in semantic_changes(before, after)], [ChangeKind.OFFER_CHANGED])
        refreshed_history = replace(
            historical,
            evidence=replace(historical.evidence, source=replace(historical.evidence.source, retrieved_at=DURING)),
        )
        before = Snapshot(1, DURING, (prior, historical))
        for old in (historical, refreshed_history):
            after = Snapshot(2, END, (closed, old))
            self.assertEqual([c.kind for c in semantic_changes(before, after)], [ChangeKind.PROMOTION_ENDED])

    def test_supplied_model_validity_correction_changes_evidence(self) -> None:
        prior = model()
        at = DURING + timedelta(seconds=1)
        before = Snapshot(1, DURING, (prior,))
        for validity in (Validity(LEARNED, at), Validity(at + timedelta(days=1))):
            corrected = replace(prior, evidence=replace(prior.evidence, validity=validity))
            after = Snapshot(2, at, (corrected,))
            with self.subTest(validity=validity):
                self.assertEqual(after.effective(), {})
                self.assertEqual([c.kind for c in semantic_changes(before, after)], [ChangeKind.MODEL_EVIDENCE_CHANGED])
        for source in (
            replace(prior.evidence.source, source_id="unrelated"),
            replace(prior.evidence.source, reference="fixture:unrelated"),
            replace(prior.evidence.source, observed_at=DURING, retrieved_at=DURING),
        ):
            unrelated = replace(prior, evidence=replace(prior.evidence, source=source, validity=Validity(LEARNED, at)))
            self.assertEqual(semantic_changes(before, Snapshot(2, at, (unrelated,))), ())
        refreshed = replace(
            prior, evidence=replace(prior.evidence, source=replace(prior.evidence.source, retrieved_at=DURING))
        )
        self.assertEqual(semantic_changes(before, Snapshot(2, at, (refreshed,))), ())

    def test_new_offer_observation_with_unchanged_terms_is_silent(self) -> None:
        prior = promotion()
        observed = replace(
            prior,
            evidence=replace(
                prior.evidence,
                source=replace(prior.evidence.source, observed_at=DURING, retrieved_at=DURING),
            ),
        )
        before = Snapshot(1, DURING, (prior,))
        after = Snapshot(2, DURING + timedelta(seconds=1), (observed,))
        self.assertEqual(semantic_changes(before, after), ())

    def test_delayed_older_offer_history_does_not_correct_newer_observation(self) -> None:
        original = promotion()
        current = replace(
            original,
            evidence=replace(
                original.evidence,
                source=replace(original.evidence.source, observed_at=START, retrieved_at=START),
            ),
        )
        before = Snapshot(1, DURING, (current,))
        for at, expected in (
            (DURING + timedelta(seconds=1), []),
            (END, [ChangeKind.PROMOTION_ENDED]),
        ):
            historical = replace(
                original,
                monthly_price=Decimal("9"),
                evidence=replace(
                    original.evidence,
                    source=replace(original.evidence.source, retrieved_at=at),
                    validity=Validity(LEARNED, START),
                ),
            )
            after = Snapshot(2, at, (current, historical))
            with self.subTest(at=at):
                self.assertIn(historical, after.facts)
                self.assertIn(State.EXPIRED, after.states(historical))
                self.assertNotIn(State.SUPERSEDED, after.states(historical))
                self.assertEqual(after.effective(), Snapshot(2, at, (current,)).effective())
                # Retained contradictory terms can still add a conflict summary, not a correction.
                kinds = [
                    c.kind for c in semantic_changes(before, after) if c.kind != ChangeKind.EVIDENCE_CONFLICT_DETECTED
                ]
                self.assertEqual(kinds, expected)
        newer = replace(
            historical,
            evidence=replace(
                historical.evidence,
                source=replace(historical.evidence.source, observed_at=DURING, retrieved_at=END),
            ),
        )
        kinds = {c.kind for c in semantic_changes(before, Snapshot(2, END, (current, newer)))}
        self.assertIn(ChangeKind.OFFER_CHANGED, kinds)
        self.assertNotIn(ChangeKind.PROMOTION_ENDED, kinds)
