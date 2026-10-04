"""Evidence additions and effective-view transitions are different questions."""

from dataclasses import dataclass

from model_intelligence.evidence import Evidence, EvidenceClaim, ModelClaim, Observation, Plan, SurfaceClaim
from model_intelligence.projection import Conflict, EffectiveView, OfferView


@dataclass(frozen=True)
class EvidenceDelta:
    observations: tuple[Observation, ...]
    claims: tuple[EvidenceClaim, ...]


def evidence_delta(before: Evidence, after: Evidence) -> EvidenceDelta:
    """New identities/links, including every batched revision and future announcement."""
    if before.extend(observations=after.observations, claims=after.claims) != after:
        raise ValueError("evidence transition must retain history; missing rows do not imply cessation")
    known_observations = {item.observation_id for item in before.observations}
    known_claims = {item.claim_id for item in before.claims}
    return EvidenceDelta(
        tuple(item for item in after.observations if item.observation_id not in known_observations),
        tuple(item for item in after.claims if item.claim_id not in known_claims),
    )


@dataclass(frozen=True)
class OfferDelta:
    plan: Plan
    before: OfferView | None
    after: OfferView | None


@dataclass(frozen=True)
class ProjectionDelta:
    """Endpoint participants/terms/diagnostics, not a reconstruction of causal history."""

    offers: tuple[OfferDelta, ...]
    models_before: tuple[ModelClaim, ...]
    models_after: tuple[ModelClaim, ...]
    surfaces_before: tuple[SurfaceClaim, ...]
    surfaces_after: tuple[SurfaceClaim, ...]
    conflicts_before: tuple[Conflict, ...]
    conflicts_after: tuple[Conflict, ...]


def projection_delta(before: EffectiveView, after: EffectiveView) -> ProjectionDelta:
    old = {item.plan: item for item in before.offers}
    new = {item.plan: item for item in after.offers}
    offers = tuple(
        OfferDelta(plan, old.get(plan), new.get(plan))
        for plan in sorted(old.keys() | new.keys(), key=lambda item: (item.plan_id, item.provider_id, item.generation))
        if old.get(plan) != new.get(plan)
    )
    return ProjectionDelta(
        offers,
        before.models if before.models != after.models else (),
        after.models if before.models != after.models else (),
        before.surfaces if before.surfaces != after.surfaces else (),
        after.surfaces if before.surfaces != after.surfaces else (),
        before.conflicts if before.conflicts != after.conflicts else (),
        after.conflicts if before.conflicts != after.conflicts else (),
    )
