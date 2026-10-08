"""Production grammar tests with original subjects, values and source observations."""

import json
import unittest
from dataclasses import replace
from datetime import datetime
from decimal import Decimal

from test_router_conformance import DAY, T, base, canonical, observation

from model_intelligence.contract import (
    NATIVE_PAYLOAD_SCHEMA,
    PAYLOAD_SCHEMA,
    PublicEvidence,
    SourceNotice,
    decode_public_evidence,
    encode_public_evidence,
)
from model_intelligence.evidence import Model, ModelClaim, NativeLimit, dimension, knowledge
from model_intelligence.projection import effective_at
from model_intelligence.publication import decode_cut, encode_cut

SUBJECT = Model(
    "owned-id",
    "owned-provider",
    "owned-alias",
    None,
    "revision-a",
    "api",
    "owned-client",
    "owned-surface-provider",
    "1.0",
    (("reasoning_effort", "none"), ("variant", "opaque-max")),
)
LIMIT = NativeLimit(
    "owned.input",
    "input-allowance",
    Decimal("4096.00000000000000000001"),
    "tokens",
    "owned-declared-scope",
    "advertised",
)


def cut(*claims: ModelClaim) -> PublicEvidence:
    public = base()
    observations = tuple(observation(claim.observation_id) for claim in claims)
    return PublicEvidence(
        public.applicability,
        public.evidence.extend(observations=observations, claims=claims),
        (*public.revisions, *((item.observation_id, "owned-revision") for item in observations)),
    )


def claim(
    identity: str = "native",
    *,
    subject: Model = SUBJECT,
    limit: NativeLimit = LIMIT,
    effective: datetime = T,
    revises: str | None = None,
) -> ModelClaim:
    return ModelClaim(
        subject, limit, claim_id=identity, observation_id=identity, effective_from=effective, revises=revises
    )


class NativeEvidenceTests(unittest.TestCase):
    def test_new_grammar_is_explicit_and_old_grammar_is_unchanged(self) -> None:
        legacy = base()
        old, old_ref = encode_public_evidence(legacy, produced_at=T)
        self.assertEqual(old_ref.payload_schema, PAYLOAD_SCHEMA)
        self.assertEqual(decode_public_evidence(old, old_ref, max_bytes=65536), legacy)
        public = cut(claim())
        with self.assertRaisesRegex(ValueError, "needs-native-grammar"):
            encode_public_evidence(public, produced_at=T)
        data, ref = encode_public_evidence(public, produced_at=T, payload_schema=NATIVE_PAYLOAD_SCHEMA)
        self.assertEqual(decode_public_evidence(data, ref, max_bytes=65536), public)
        with self.assertRaisesRegex(ValueError, "unsupported-version"):
            decode_public_evidence(data, ref, max_bytes=65536, supported_payload_schemas=frozenset({PAYLOAD_SCHEMA}))
        self.assertIn(str(LIMIT.amount), data.decode())

    def test_every_subject_component_and_missing_null_effort_are_distinct(self) -> None:
        initial = claim()
        for subject in (
            replace(SUBJECT, provider_model_id="different-alias"),
            replace(SUBJECT, physical_model_id="observed-model"),
            replace(SUBJECT, revision="revision-b"),
            replace(SUBJECT, channel="plan-managed"),
            replace(SUBJECT, interface_id="different-surface"),
            replace(SUBJECT, interface_provider_id="other-provider"),
            replace(SUBJECT, interface_version="2.0"),
            replace(SUBJECT, configuration=None),
            replace(SUBJECT, configuration=()),
            replace(SUBJECT, configuration=(("reasoning_effort", None),)),
            replace(SUBJECT, configuration=(("reasoning_effort", "unsupported-native-value"),)),
        ):
            with self.subTest(subject=subject):
                changed = claim("changed", subject=subject)
                self.assertNotEqual(dimension(initial), dimension(changed))
                public = cut(initial, changed)
                data, ref = encode_public_evidence(public, produced_at=T, payload_schema=NATIVE_PAYLOAD_SCHEMA)
                self.assertEqual(decode_public_evidence(data, ref, max_bytes=65536), public)
                with self.assertRaisesRegex(ValueError, "comparable"):
                    cut(initial, replace(changed, revises=initial.claim_id))
        self.assertIsNone(SUBJECT.physical_model_id)
        self.assertEqual(dict(SUBJECT.configuration or ())["reasoning_effort"], "none")

    def test_native_meaning_unit_basis_and_unknown_are_not_conversions(self) -> None:
        original = claim()
        for limit in (
            replace(LIMIT, meaning="total-context"),
            replace(LIMIT, meaning="execution-ceiling"),
            replace(LIMIT, unit="characters"),
            replace(LIMIT, unit=None),
            replace(LIMIT, basis=None),
        ):
            self.assertNotEqual(dimension(original), dimension(claim("other", limit=limit)))
        unknown = claim("unknown", limit=replace(LIMIT, amount=None, assertion="unknown"))
        public = cut(unknown)
        data, ref = encode_public_evidence(public, produced_at=T, payload_schema=NATIVE_PAYLOAD_SCHEMA)
        self.assertEqual(decode_public_evidence(data, ref, max_bytes=65536), public)
        assert isinstance(unknown.payload, NativeLimit)
        self.assertIsNone(unknown.payload.amount)
        for amount in (Decimal("NaN"), Decimal("Infinity"), Decimal("-1")):
            with self.assertRaises(ValueError):
                replace(LIMIT, amount=amount)
        self.assertEqual(replace(LIMIT, amount=Decimal(0)).amount, Decimal(0))

    def test_native_revisions_conflict_and_critical_notice_retain_originals(self) -> None:
        original = claim()
        future = claim("future", effective=T + DAY, revises="native", limit=replace(LIMIT, amount=Decimal("2048")))
        disagree = claim("disagree", limit=replace(LIMIT, amount=Decimal("1024")))
        public = cut(original, future, disagree)
        self.assertEqual({row.claim_id for row in effective_at(public.evidence, T).models}, {"native", "disagree"})
        self.assertTrue(effective_at(public.evidence, T).conflicts)
        self.assertEqual(knowledge(public.evidence, T).future, (future,))
        public = replace(
            public,
            notices=(SourceNotice("revocation", "native", frozenset({"statement:native"}), T, "revocation", True),),
        )
        data, ref = encode_public_evidence(public, produced_at=T, payload_schema=NATIVE_PAYLOAD_SCHEMA)
        restored = decode_public_evidence(data, ref, max_bytes=65536)
        self.assertEqual(restored, public)
        self.assertEqual(restored.active_notices(T)[0].notice_id, "revocation")

    def test_strict_nested_validation_rejects_incomplete_version_two(self) -> None:
        public = cut(claim())
        data, ref = encode_public_evidence(public, produced_at=T, payload_schema=NATIVE_PAYLOAD_SCHEMA)
        frame = decode_cut(data, ref, supported_payload_schemas=frozenset({NATIVE_PAYLOAD_SCHEMA}), max_bytes=65536)
        for field in ("unit", "basis", "assertion", "meaning", "amount"):
            raw = json.loads(frame.payload)
            native = next(row["value"] for row in raw["statements"] if row["value"].get("kind") == "native-limit")
            del native[field]
            broken, broken_ref = encode_cut(
                canonical(raw),
                payload_schema=NATIVE_PAYLOAD_SCHEMA,
                produced_at=T,
                scope=frame.scope,
                members=frame.members,
                sources=frame.sources,
            )
            with self.assertRaisesRegex(ValueError, "payload-shape"):
                decode_public_evidence(broken, broken_ref, max_bytes=65536)
        with self.assertRaisesRegex(ValueError, "history"):
            public.check_update(base())


if __name__ == "__main__":
    unittest.main()
