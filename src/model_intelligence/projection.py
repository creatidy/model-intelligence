"""Effective projections and explainable changes over explicit historical evidence."""

from dataclasses import dataclass, fields, replace
from datetime import datetime
from enum import StrEnum

from model_intelligence.domain import (
    Benchmark,
    Capability,
    Evidence,
    ModelClaim,
    Money,
    OfferClaim,
    Override,
    Plan,
    Quota,
    SurfaceClaim,
    Terms,
    comparison_key,
    utc_instant,
)


@dataclass(frozen=True)
class Conflict:
    subject: tuple[str, ...]
    field: str
    claim_ids: tuple[str, ...]


@dataclass(frozen=True)
class OfferView:
    baselines: tuple[OfferClaim, ...]
    overrides: tuple[OfferClaim, ...]
    effective: Terms
    conflicts: tuple[Conflict, ...]


type FieldValue = Money | Quota | bool | tuple[str, ...] | None


def _field(terms: Terms, name: str) -> FieldValue:
    return getattr(terms, name)


def offer(
    evidence: Evidence,
    plan: Plan,
    at: datetime,
    *,
    conditions: frozenset[str] = frozenset(),
) -> OfferView:
    heads = tuple(claim for claim in evidence.heads() if isinstance(claim, OfferClaim) and claim.subject == plan)
    baselines = tuple(claim for claim in heads if isinstance(claim.payload, Terms) and claim.active(at))
    overrides = tuple(claim for claim in heads if isinstance(claim.payload, Override) and claim.active(at, conditions))
    conflicts: list[Conflict] = []
    disputed: set[str] = set()
    campaigns = {claim.payload.campaign_id for claim in heads if isinstance(claim.payload, Override)}
    for campaign in sorted(campaigns):
        participants = tuple(
            claim for claim in heads if isinstance(claim.payload, Override) and claim.payload.campaign_id == campaign
        )
        boundaries = {
            (claim.applicability, claim.payload.window, claim.payload.conditions, claim.payload.withdrawn)
            for claim in participants
            if isinstance(claim.payload, Override)
        }
        if len(boundaries) > 1:
            conflicts.append(
                Conflict(comparison_key(participants[0]), "applicability", tuple(c.claim_id for c in participants))
            )
            # Keep disputed boundary evidence visible, without applying expired terms.
            if any(claim.active(at, conditions) for claim in participants) and not all(
                claim.active(at, conditions) for claim in participants
            ):
                for claim in participants:
                    assert isinstance(claim.payload, Override)
                    disputed.update(
                        field.name for field in fields(Terms) if _field(claim.payload.terms, field.name) is not None
                    )
    effective = Terms()
    for field in fields(Terms):
        baseline_values = [
            (claim.claim_id, _field(claim.payload, field.name))
            for claim in baselines
            if isinstance(claim.payload, Terms)
        ]
        overlay_values = [
            (claim.claim_id, _field(claim.payload.terms, field.name))
            for claim in overrides
            if isinstance(claim.payload, Override) and _field(claim.payload.terms, field.name) is not None
        ]
        candidates = overlay_values or baseline_values
        values = {value for _, value in candidates if value is not None}
        if len(values) > 1:
            conflicts.append(
                Conflict(
                    ("offer", plan.plan_id, plan.provider_id, plan.generation),
                    field.name,
                    tuple(identity for identity, value in candidates if value is not None),
                )
            )
        value = next(iter(values)) if len(values) == 1 and field.name not in disputed else None
        effective = replace(effective, **{field.name: value})
    return OfferView(baselines, overrides, effective, tuple(conflicts))


def future_overrides(evidence: Evidence, plan: Plan, at: datetime) -> tuple[OfferClaim, ...]:
    return tuple(
        claim
        for claim in evidence.heads()
        if isinstance(claim, OfferClaim)
        and claim.subject == plan
        and isinstance(claim.payload, Override)
        and not claim.payload.withdrawn
        and claim.applicability.start > utc_instant(at)
    )


def current(evidence: Evidence, at: datetime) -> tuple[ModelClaim | SurfaceClaim, ...]:
    return tuple(
        claim
        for claim in evidence.heads()
        if isinstance(claim, ModelClaim | SurfaceClaim) and claim.applicability.contains(at)
    )


def conflicts(evidence: Evidence, at: datetime, *, conditions: frozenset[str] = frozenset()) -> tuple[Conflict, ...]:
    result: list[Conflict] = []
    groups: dict[tuple[str, ...], list[ModelClaim | SurfaceClaim]] = {}
    for claim in current(evidence, at):
        groups.setdefault(comparison_key(claim), []).append(claim)
    for key, claims in sorted(groups.items()):
        dimensions: dict[str, list[tuple[str, object]]] = {}
        for claim in claims:
            payload = claim.payload
            if isinstance(payload, Capability):
                values = {"supported": payload.supported}
            elif isinstance(payload, Benchmark):
                values = {"value": payload.value}
            elif isinstance(payload, Money):
                values = {"amount": payload.amount}
            else:
                values = {
                    field.name: getattr(payload, field.name) for field in fields(payload) if field.name != "capability"
                }
            for name, value in values.items():
                if value is not None:
                    dimensions.setdefault(name, []).append((claim.claim_id, value))
        for name, values in sorted(dimensions.items()):
            if len({value for _, value in values}) > 1:
                result.append(Conflict(key, name, tuple(identity for identity, _ in values)))
    plans = {claim.subject for claim in evidence.heads() if isinstance(claim, OfferClaim)}
    for plan in sorted(plans, key=lambda item: (item.plan_id, item.provider_id, item.generation)):
        result.extend(offer(evidence, plan, at, conditions=conditions).conflicts)
    return tuple(result)


class ChangeKind(StrEnum):
    MODEL_OBSERVED = "model observed"
    MODEL_EVIDENCE_REVISED = "model evidence revised"
    MODEL_EVIDENCE_ACTIVATED = "model evidence activated"
    MODEL_EVIDENCE_EXPIRED = "model evidence expired"
    PRICE_CHANGED = "price changed"
    OVERRIDE_ACTIVATED = "override activated"
    OVERRIDE_REVISED = "override revised"
    OVERRIDE_WITHDRAWN = "override withdrawn"
    OVERRIDE_EXPIRED = "override expired"
    OVERRIDE_INACTIVE = "override inactive"
    EFFECTIVE_OFFER_CHANGED = "effective offer changed"
    EXECUTION_SURFACE_CHANGED = "execution surface changed"
    CONFLICT_DETECTED = "conflict detected"
    CONFLICT_RESOLVED = "conflict resolved"


@dataclass(frozen=True)
class Change:
    kind: ChangeKind
    subject: tuple[str, ...]
    claim_ids: tuple[str, ...]


def changes(
    before: Evidence,
    after: Evidence,
    before_at: datetime,
    after_at: datetime,
    *,
    conditions: frozenset[str] = frozenset(),
) -> tuple[Change, ...]:
    """Require retained history. Absence is rejected, never translated into cessation.

    Output ordering is presentation only. Events cite explicit heads/links/boundaries;
    retrieval-only updates are silent, even if evidence remains stale or superseded.
    """
    if utc_instant(after_at) < utc_instant(before_at):
        raise ValueError("comparison time must not go backwards")
    expected = before.extend(observations=after.observations, claims=after.claims)
    if expected != after:
        raise ValueError("comparison must retain historical evidence; missing rows do not imply cessation")
    old = {claim.claim_id: claim for claim in before.claims}
    result: set[Change] = set()
    for claim in after.heads():
        key = comparison_key(claim)
        if isinstance(claim, ModelClaim | SurfaceClaim) and claim.claim_id in old and claim in before.heads():
            was_current = claim.applicability.contains(before_at)
            is_current = claim.applicability.contains(after_at)
            if was_current != is_current:
                kind = ChangeKind.EXECUTION_SURFACE_CHANGED
                if isinstance(claim, ModelClaim):
                    kind = ChangeKind.MODEL_EVIDENCE_ACTIVATED if is_current else ChangeKind.MODEL_EVIDENCE_EXPIRED
                result.add(Change(kind, key, (claim.claim_id,)))
        if claim.claim_id not in old:
            if isinstance(claim, ModelClaim):
                kind = ChangeKind.MODEL_EVIDENCE_REVISED if claim.revises else ChangeKind.MODEL_OBSERVED
                result.add(Change(kind, key, (claim.claim_id,)))
            elif isinstance(claim, SurfaceClaim):
                result.add(Change(ChangeKind.EXECUTION_SURFACE_CHANGED, key, (claim.claim_id,)))
            elif isinstance(claim.payload, Override) and claim.revises:
                kind = ChangeKind.OVERRIDE_WITHDRAWN if claim.payload.withdrawn else ChangeKind.OVERRIDE_REVISED
                result.add(Change(kind, key, (claim.revises, claim.claim_id)))
            if claim.revises:
                previous = next(item for item in after.claims if item.claim_id == claim.revises)
                old_price = (
                    previous.payload
                    if isinstance(previous.payload, Money)
                    else (previous.payload.price if isinstance(previous.payload, Terms) else None)
                )
                new_price = (
                    claim.payload
                    if isinstance(claim.payload, Money)
                    else (claim.payload.price if isinstance(claim.payload, Terms) else None)
                )
                if old_price != new_price:
                    result.add(Change(ChangeKind.PRICE_CHANGED, key, (claim.revises, claim.claim_id)))
        if isinstance(claim, OfferClaim) and isinstance(claim.payload, Override):
            was_active = (
                claim.claim_id in old and old[claim.claim_id] in before.heads() and claim.active(before_at, conditions)
            )
            active = claim.active(after_at, conditions)
            if active and not was_active:
                result.add(Change(ChangeKind.OVERRIDE_ACTIVATED, key, (claim.claim_id,)))
            elif was_active and not active:
                kind = (
                    ChangeKind.OVERRIDE_EXPIRED
                    if claim.applicability.end is not None and utc_instant(after_at) >= claim.applicability.end
                    else ChangeKind.OVERRIDE_INACTIVE
                )
                result.add(Change(kind, key, (claim.claim_id,)))
    plans = {claim.subject for claim in (*before.claims, *after.claims) if isinstance(claim, OfferClaim)}
    for plan in plans:
        previous = offer(before, plan, before_at, conditions=conditions)
        following = offer(after, plan, after_at, conditions=conditions)
        if previous.effective != following.effective:
            ids = tuple(
                sorted(
                    {
                        claim.claim_id
                        for claim in (
                            *previous.baselines,
                            *previous.overrides,
                            *following.baselines,
                            *following.overrides,
                        )
                    }
                )
            )
            result.add(
                Change(
                    ChangeKind.EFFECTIVE_OFFER_CHANGED, ("offer", plan.plan_id, plan.provider_id, plan.generation), ids
                )
            )
    old_conflicts = set(conflicts(before, before_at, conditions=conditions))
    new_conflicts = set(conflicts(after, after_at, conditions=conditions))
    for items, kind in (
        (new_conflicts - old_conflicts, ChangeKind.CONFLICT_DETECTED),
        (old_conflicts - new_conflicts, ChangeKind.CONFLICT_RESOLVED),
    ):
        for item in items:
            result.add(Change(kind, (*item.subject, item.field), item.claim_ids))
    return tuple(sorted(result, key=lambda item: (item.kind, item.subject, item.claim_ids)))
