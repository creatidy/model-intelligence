"""Synthetic producer/consumer framing proof, not installed Router acceptance."""

import hashlib
import json
import unittest
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import cast

from model_intelligence.deltas import evidence_delta, projection_delta
from model_intelligence.evidence import (
    BaselineClaim,
    Evidence,
    Money,
    Observation,
    OverrideClaim,
    Period,
    Plan,
    Quota,
    Terms,
    knowledge,
)
from model_intelligence.projection import EffectiveView, effective_at
from model_intelligence.publication import CutReference, Publication, SourceRevision, decode_cut, encode_cut

T = datetime(2026, 1, 1, tzinfo=UTC)
DAY = timedelta(days=1)
PLAN = Plan("synthetic/pro", "synthetic-provider", "fixture-generation")
NORMAL_PRICE = Money(Decimal("20"), "USD", "month")
SCHEMA = "synthetic-r2-offers/1"
SCOPE = "synthetic/pro:fixture-api:unknown-effort"
BOUND = 64 * 1024


def record(value: object, keys: set[str] | None = None) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("fixture-object")
    result = cast(dict[str, object], value)
    if keys is not None and set(result) != keys:
        raise ValueError("fixture-record-shape")
    return result


def text(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("fixture-text")
    return value


def rows(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("fixture-list")
    return cast(list[object], value)


def default(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, frozenset):
        return sorted(cast(frozenset[str], value))
    raise ValueError("fixture-value")


def dump(value: object) -> bytes:
    return json.dumps(value, default=default, sort_keys=True, allow_nan=False).encode()


def timestamp(value: object) -> datetime:
    return datetime.fromisoformat(text(value))


def money(value: object) -> Money | None:
    if value is None:
        return None
    item = record(value, {"amount", "currency", "unit"})
    return Money(Decimal(text(item["amount"])), text(item["currency"]), text(item["unit"]))


def terms(value: object) -> Terms:
    item = record(value, {"price", "quota", "available", "rules"})
    available = item["available"]
    if available is not None and type(available) is not bool:
        raise ValueError("fixture-availability")
    quota, rules = item["quota"], item["rules"]
    q = record(quota, {"amount", "unit", "period"}) if quota is not None else None
    return Terms(
        money(item["price"]),
        None if q is None else Quota(Decimal(text(q["amount"])), text(q["unit"]), text(q["period"])),
        available,
        None if rules is None else tuple(text(rule) for rule in rows(rules)),
    )


def decode_fixture(publication: Publication) -> Evidence:
    """This offer-only proof codec is NOT the proposed permanent evidence wire API."""
    if publication.scope != SCOPE:
        raise ValueError("fixture-scope")
    payload = record(json.loads(publication.payload, parse_float=Decimal))
    if set(payload) != {"plan", "observations", "claims"}:
        raise ValueError("fixture-payload-shape")
    if record(payload["plan"], {"plan_id", "provider_id", "generation"}) != asdict(PLAN):
        raise ValueError("fixture-subject")
    observations: list[Observation] = []
    for raw in rows(payload["observations"]):
        item = record(
            raw,
            {
                "observation_id",
                "source_id",
                "authority",
                "source_type",
                "reference",
                "retrieved_at",
                "distribution",
                "license",
                "observed_at",
                "published_at",
                "fresh_until",
            },
        )
        # The owned fixture codec deliberately fixes these provenance classifications.
        if (item["authority"], item["source_type"], item["distribution"], item["license"]) != (
            "official",
            "documentation",
            "public",
            "synthetic",
        ):
            raise ValueError("fixture-provenance")
        observations.append(
            Observation(
                text(item["observation_id"]),
                text(item["source_id"]),
                "official",
                "documentation",
                text(item["reference"]),
                timestamp(item["retrieved_at"]),
                "public",
                "synthetic",
                observed_at=None if item["observed_at"] is None else timestamp(item["observed_at"]),
                published_at=None if item["published_at"] is None else timestamp(item["published_at"]),
                fresh_until=None if item["fresh_until"] is None else timestamp(item["fresh_until"]),
            )
        )
    claims: list[BaselineClaim | OverrideClaim] = []
    for raw in rows(payload["claims"]):
        entry = record(raw, {"kind", "value"})
        fields = {"subject", "terms", "claim_id", "observation_id", "effective_from", "revises"}
        if entry["kind"] == "override":
            fields.update({"campaign_id", "period", "conditions", "window"})
        elif entry["kind"] != "baseline":
            raise ValueError("unsupported-fixture-payload")
        item = record(entry["value"], fields)
        claim_id = text(item["claim_id"])
        observation_id = text(item["observation_id"])
        effective_from = timestamp(item["effective_from"])
        revises = None if item["revises"] is None else text(item["revises"])
        if record(item["subject"], {"plan_id", "provider_id", "generation"}) != asdict(PLAN):
            raise ValueError("fixture-subject")
        if entry["kind"] == "baseline":
            claims.append(
                BaselineClaim(
                    PLAN,
                    terms(item["terms"]),
                    claim_id=claim_id,
                    observation_id=observation_id,
                    effective_from=effective_from,
                    revises=revises,
                )
            )
        elif entry["kind"] == "override" and item["window"] is None:
            period = None if item["period"] is None else record(item["period"], {"start", "end"})
            claims.append(
                OverrideClaim(
                    PLAN,
                    text(item["campaign_id"]),
                    None if item["terms"] is None else terms(item["terms"]),
                    None if period is None else Period(timestamp(period["start"]), timestamp(period["end"])),
                    frozenset(text(condition) for condition in rows(item["conditions"])),
                    claim_id=claim_id,
                    observation_id=observation_id,
                    effective_from=effective_from,
                    revises=revises,
                )
            )
        else:
            raise ValueError("unsupported-fixture-payload")
    evidence = Evidence(tuple(observations), tuple(claims))
    expected_members = {*(f"o:{o.observation_id}" for o in observations), *(f"c:{c.claim_id}" for c in claims)}
    if set(publication.members) != expected_members:
        raise ValueError("incomplete-cut")
    actual_sources = {(o.source_id, o.reference) for o in observations}
    if {(s.source_id, s.reference) for s in publication.sources} != actual_sources:
        raise ValueError("source-membership")
    return evidence


def observation(identity: str, *, fresh_until: datetime | None = T + DAY) -> Observation:
    return Observation(
        identity,
        "fixture-source",
        "official",
        "documentation",
        f"https://example.invalid/{identity}",
        T,
        "public",
        "synthetic",
        published_at=T - DAY,
        fresh_until=fresh_until,
    )


def baseline(identity: str = "base", *, price: Money | None = NORMAL_PRICE) -> BaselineClaim:
    return BaselineClaim(PLAN, Terms(price=price), claim_id=identity, observation_id=identity, effective_from=T - DAY)


BASE = Evidence((observation("base"),), (baseline(),))
PROMO = OverrideClaim(
    PLAN,
    "fixture-campaign",
    Terms(price=Money(Decimal("10"), "USD", "month")),
    Period(T, T + 2 * DAY),
    frozenset({"fixture-client"}),
    claim_id="sale",
    observation_id="sale",
    effective_from=T,
)


def publish(evidence: Evidence, *, produced_at: datetime = T) -> tuple[bytes, CutReference]:
    if any(not isinstance(claim, BaselineClaim | OverrideClaim) for claim in evidence.claims):
        raise ValueError("unsupported-fixture-payload")
    payload = dump(
        {
            "plan": asdict(PLAN),
            "observations": [asdict(o) for o in evidence.observations],
            "claims": [
                {"kind": "baseline" if isinstance(c, BaselineClaim) else "override", "value": asdict(c)}
                for c in evidence.claims
            ],
        }
    )
    return encode_cut(
        payload,
        payload_schema=SCHEMA,
        produced_at=produced_at,
        scope=SCOPE,
        members=tuple(
            [f"o:{o.observation_id}" for o in evidence.observations] + [f"c:{c.claim_id}" for c in evidence.claims]
        ),
        sources=tuple(
            SourceRevision(o.source_id, o.reference, f"fixture-revision:{o.observation_id}")
            for o in evidence.observations
        ),
    )


def read(data: bytes, reference: CutReference) -> Evidence:
    return decode_fixture(decode_cut(data, reference, supported_payload_schemas=frozenset({SCHEMA}), max_bytes=BOUND))


@dataclass(frozen=True)
class PinnedEvaluation:
    data: bytes
    reference: CutReference
    at: datetime
    conditions: frozenset[str]

    def replay(self) -> EffectiveView:
        return effective_at(read(self.data, self.reference), self.at, conditions=self.conditions)


class ConsumerFixture:
    """A local contract harness; no Router selection, admission or Attempt engine."""

    def __init__(self) -> None:
        self.admitted: tuple[bytes, CutReference] | None = None

    def adopt(self, data: bytes, reference: CutReference, *, rollback: bool = False) -> None:
        candidate = read(data, reference)
        if self.admitted is not None and not rollback:
            previous = read(*self.admitted)
            # Reject history loss or identity rewriting, rather than quietly repairing a partial cut.
            evidence_delta(previous, candidate)
        self.admitted = data, reference

    def pin(self, at: datetime, conditions: frozenset[str] = frozenset()) -> PinnedEvaluation:
        if self.admitted is None:
            raise ValueError("no-admitted-cut")
        return PinnedEvaluation(*self.admitted, at, conditions)


class PublicationContractTests(unittest.TestCase):
    def test_framing_preserves_exact_decimal_payload_bytes(self) -> None:
        payload = b'{"limit":9007199254740993.0,"fraction":0.12345678901234567890,"tiny":1e-400}'
        data, reference = encode_cut(
            payload, payload_schema="precision/1", produced_at=T, scope="synthetic", members=(), sources=()
        )
        cut = decode_cut(data, reference, supported_payload_schemas=frozenset({"precision/1"}), max_bytes=BOUND)
        self.assertEqual(cut.payload, payload)
        self.assertEqual(record(json.loads(cut.payload, parse_float=Decimal))["limit"], Decimal("9007199254740993.0"))
        self.assertEqual(record(json.loads(cut.payload, parse_float=Decimal))["tiny"], Decimal("1e-400"))

    def test_object_payload_is_not_silently_normalized_by_decoder(self) -> None:
        data, _ = publish(BASE)
        frame = record(json.loads(data))
        frame["payload"] = {"limit": 0.1}
        raw = dump(frame)
        with self.assertRaises(ValueError):
            decode_cut(
                raw,
                CutReference(1, SCHEMA, hashlib.sha256(raw).hexdigest()),
                supported_payload_schemas=frozenset({SCHEMA}),
                max_bytes=BOUND,
            )

    def test_nested_unknown_and_missing_fields_reject_without_activation(self) -> None:
        rich = BASE.extend(
            observations=(observation("sale"),),
            claims=(
                replace(
                    PROMO,
                    terms=Terms(
                        PROMO.terms.price if PROMO.terms else None,
                        Quota(Decimal("10"), "public-unit", "day"),
                        True,
                        ("public rule",),
                    ),
                ),
            ),
        )
        original = publish(rich)
        consumer = ConsumerFixture()
        consumer.adopt(*original)
        paths: tuple[tuple[str | int, ...], ...] = (
            ("observations", 0),
            ("claims", 0),
            ("claims", 0, "value"),
            ("claims", 0, "value", "subject"),
            ("claims", 0, "value", "terms"),
            ("claims", 0, "value", "terms", "price"),
            ("claims", 1, "value"),
            ("claims", 1, "value", "terms", "quota"),
            ("claims", 1, "value", "period"),
        )
        for path in paths:
            for mutation in ("unknown", "missing"):
                frame = record(json.loads(original[0]))
                payload = record(json.loads(text(frame["payload"])))
                node: object = payload
                for part in path:
                    node = record(node)[part] if isinstance(part, str) else rows(node)[part]
                item = record(node)
                if mutation == "unknown":
                    item["critical_revocation"] = {"notice": "synthetic"}
                else:
                    del item[next(iter(item))]
                frame["payload"] = dump(payload).decode()
                raw = dump(frame)
                with (
                    self.subTest(path=path, mutation=mutation),
                    self.assertRaisesRegex(ValueError, "fixture-record-shape"),
                ):
                    consumer.adopt(raw, CutReference(1, SCHEMA, hashlib.sha256(raw).hexdigest()))
                self.assertEqual(consumer.admitted, original)

    def test_complete_cut_and_reference_are_deterministic(self) -> None:
        data, reference = publish(BASE)
        self.assertEqual(publish(BASE), (data, reference))
        self.assertEqual(read(data, reference), BASE)
        self.assertEqual(reference.sha256, hashlib.sha256(data).hexdigest())
        cut = decode_cut(data, reference, supported_payload_schemas=frozenset({SCHEMA}), max_bytes=BOUND)
        self.assertEqual(cut.sources[0].revision, "fixture-revision:base")

    def test_unknown_source_revision_and_invalid_metadata_remain_distinct(self) -> None:
        data, _ = publish(BASE)
        frame = record(json.loads(data))
        record(rows(frame["sources"])[0])["revision"] = None
        unknown = dump(frame)
        reference = CutReference(1, SCHEMA, hashlib.sha256(unknown).hexdigest())
        cut = decode_cut(unknown, reference, supported_payload_schemas=frozenset({SCHEMA}), max_bytes=BOUND)
        self.assertIsNone(cut.sources[0].revision)
        for field, value in (
            ("format_version", True),
            ("produced_at", "2026-01-01"),
            ("members", ["o:base", "o:base"]),
        ):
            bad = dump({**frame, field: value})
            with self.subTest(field=field), self.assertRaises(ValueError):
                decode_cut(
                    bad,
                    CutReference(1, SCHEMA, hashlib.sha256(bad).hexdigest()),
                    supported_payload_schemas=frozenset({SCHEMA}),
                    max_bytes=BOUND,
                )

    def test_unrecognized_critical_notice_is_not_a_missing_price(self) -> None:
        consumer = ConsumerFixture()
        original = publish(BASE)
        consumer.adopt(*original)
        frame = record(json.loads(original[0]))
        payload = record(json.loads(text(frame["payload"])))
        payload["critical_revocation"] = {"source_notice": "synthetic-critical-notice"}
        frame["payload"] = dump(payload).decode()
        candidate = dump(frame)
        with self.assertRaisesRegex(ValueError, "fixture-payload-shape"):
            consumer.adopt(candidate, CutReference(1, SCHEMA, hashlib.sha256(candidate).hexdigest()))
        self.assertEqual(consumer.admitted, original)
        missing_price = Evidence((observation("base"),), (baseline(price=None),))
        self.assertIsNone(effective_at(read(*publish(missing_price)), T).offers[0].terms.price)

    def test_rejection_keeps_previous_artifact(self) -> None:
        consumer = ConsumerFixture()
        original = publish(BASE)
        consumer.adopt(*original)
        payload = record(json.loads(original[0]))
        payload["members"] = ["o:base"]
        incomplete = dump(payload)
        malformed = b'{"format_version":1,"format_version":1}'
        invalid_utf8 = b"\xff"
        nonfinite = b'{"payload":NaN}'
        extra = dump({**record(json.loads(original[0])), "unexpected": True})
        candidates = [
            (original[0][:-5], original[1]),
            (original[0] + b" ", original[1]),
            (original[0], replace(original[1], format_version=2)),
            (original[0], replace(original[1], payload_schema="future/1")),
            (b"x" * (BOUND + 1), original[1]),
        ]
        candidates.extend(
            (raw, CutReference(1, SCHEMA, hashlib.sha256(raw).hexdigest()))
            for raw in (incomplete, malformed, invalid_utf8, nonfinite, extra)
        )
        for candidate in candidates:
            with self.subTest(candidate=candidate[1]), self.assertRaises(ValueError):
                consumer.adopt(*candidate)
            self.assertEqual(consumer.admitted, original)

    def test_two_cuts_at_same_time_do_not_invent_acquisition_history(self) -> None:
        late = replace(baseline("late"), effective_from=T - 2 * DAY)
        newer = BASE.extend(observations=(observation("late"),), claims=(late,))
        consumer = ConsumerFixture()
        consumer.adopt(*publish(BASE))
        pinned = consumer.pin(T)
        consumer.adopt(*publish(newer, produced_at=T + DAY))
        self.assertNotEqual(pinned.reference, consumer.pin(T).reference)
        self.assertFalse(pinned.replay().conflicts)
        self.assertTrue(evidence_delta(BASE, newer).claims)
        self.assertEqual(len(knowledge(newer, T - 3 * DAY).history), 2)

    def test_future_revision_withdrawal_and_offline_expiry(self) -> None:
        sale = BASE.extend(observations=(observation("sale"),), claims=(PROMO,))
        withdrawal = OverrideClaim(
            PLAN,
            "fixture-campaign",
            None,
            None,
            claim_id="withdrawal",
            observation_id="withdrawal",
            effective_from=T + DAY,
            revises="sale",
        )
        newer = sale.extend(observations=(observation("withdrawal"),), claims=(withdrawal,))
        consumer = ConsumerFixture()
        consumer.adopt(*publish(newer))
        before = consumer.pin(T, frozenset({"fixture-client"}))
        self.assertEqual(before.replay().offers[0].terms.price, PROMO.terms.price if PROMO.terms else None)
        self.assertEqual(
            consumer.pin(T + DAY, before.conditions).replay().offers[0].terms.price, baseline().terms.price
        )
        self.assertTrue(knowledge(read(*publish(newer)), T).future)
        consumer.adopt(*publish(sale), rollback=True)
        self.assertEqual(
            consumer.pin(T + 2 * DAY, before.conditions).replay().offers[0].terms.price, baseline().terms.price
        )
        self.assertEqual(before.replay().offers[0].terms.price, PROMO.terms.price if PROMO.terms else None)

    def test_unknown_stale_missing_and_conflict_are_not_false_or_free(self) -> None:
        unknown = Evidence((observation("base", fresh_until=None),), (baseline(price=None),))
        cut = read(*publish(unknown))
        self.assertIsNone(cut.observations[0].fresh_until)
        self.assertFalse(knowledge(cut, T + 100 * DAY).stale_observations)
        self.assertIsNone(effective_at(cut, T).offers[0].terms.price)
        stale = read(*publish(BASE))
        self.assertTrue(knowledge(stale, T + DAY).stale_observations)
        self.assertIsNotNone(effective_at(stale, T + DAY).offers[0].terms.price)
        other = replace(baseline("other"), terms=Terms(price=Money(Decimal("99"), "USD", "month")))
        conflict = BASE.extend(observations=(observation("other"),), claims=(other,))
        view = effective_at(read(*publish(conflict)), T)
        self.assertTrue(view.conflicts)
        self.assertIsNone(view.offers[0].terms.price)

    def test_missing_history_and_refresh_failure_do_not_change_pinned_use(self) -> None:
        consumer = ConsumerFixture()
        consumer.adopt(*publish(BASE))
        pinned = consumer.pin(T)
        with self.assertRaises(ValueError):
            consumer.adopt(*publish(Evidence()))
        with self.assertRaises(ValueError):
            consumer.adopt(b"interrupted", publish(BASE)[1])
        self.assertEqual(consumer.pin(T), pinned)
        self.assertEqual(pinned.replay(), effective_at(BASE, T))

    def test_retrieval_refresh_changes_reference_not_freshness_or_evidence(self) -> None:
        refreshed = BASE.extend(observations=(replace(BASE.observations[0], retrieved_at=T + 2 * DAY),))
        old, new = read(*publish(BASE)), read(*publish(refreshed, produced_at=T + 2 * DAY))
        self.assertNotEqual(publish(BASE)[1], publish(refreshed)[1])
        self.assertEqual(evidence_delta(old, new).claims, ())
        self.assertEqual(projection_delta(effective_at(old, T), effective_at(new, T)).offers, ())
        self.assertTrue(knowledge(new, T + DAY).stale_observations)


if __name__ == "__main__":
    unittest.main()
