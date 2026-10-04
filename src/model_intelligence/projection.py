"""Effective-at-T uses explicit applicable versions, not latest-known knowledge heads."""

from dataclasses import dataclass, fields, replace
from datetime import datetime

from model_intelligence.evidence import (
    BaselineClaim,
    Benchmark,
    Capability,
    Evidence,
    EvidenceClaim,
    ModelClaim,
    Money,
    OverrideClaim,
    Plan,
    SurfaceClaim,
    Terms,
    dimension,
    instant,
)


@dataclass(frozen=True)
class Conflict:
    subject: tuple[str, ...]
    field: str
    claim_ids: tuple[str, ...]


@dataclass(frozen=True)
class OfferView:
    plan: Plan
    baselines: tuple[BaselineClaim, ...]
    overrides: tuple[OverrideClaim, ...]
    terms: Terms
    conflicts: tuple[Conflict, ...]


@dataclass(frozen=True)
class EffectiveView:
    offers: tuple[OfferView, ...]
    models: tuple[ModelClaim, ...]
    surfaces: tuple[SurfaceClaim, ...]
    conflicts: tuple[Conflict, ...]


def effective_at(evidence: Evidence, at: datetime, *, conditions: frozenset[str] = frozenset()) -> EffectiveView:
    at = instant(at)
    # Version replacement is permanent from its explicit boundary. Expiry/conditions
    # control active terms afterward; they must not resurrect older versions.
    started = tuple(claim for claim in evidence.claims if claim.effective_from <= at)
    replaced = {claim.revises for claim in started}
    versions = tuple(claim for claim in started if claim.claim_id not in replaced)
    by_id = {claim.claim_id: claim for claim in evidence.claims}
    roots: dict[str, str] = {}
    for claim in versions:
        ancestor = claim
        while ancestor.revises is not None:
            ancestor = by_id[ancestor.revises]
        roots[claim.claim_id] = ancestor.claim_id
    all_conflicts: list[Conflict] = []
    groups: dict[tuple[str, ...], list[EvidenceClaim]] = {}
    for claim in versions:
        groups.setdefault(dimension(claim), []).append(claim)
    # Sibling revisions stay explicit even when their values happen to agree.
    for key, group in sorted(groups.items()):
        siblings: dict[str, list[str]] = {}
        for claim in group:
            siblings.setdefault(roots[claim.claim_id], []).append(claim.claim_id)
        for ids in siblings.values():
            if len(ids) > 1 and not isinstance(group[0], OverrideClaim):
                all_conflicts.append(Conflict(key, "lineage", tuple(ids)))
    models = tuple(claim for claim in versions if isinstance(claim, ModelClaim))
    surfaces = tuple(claim for claim in versions if isinstance(claim, SurfaceClaim))
    for key, group in sorted(groups.items()):
        values: dict[str, list[tuple[str, object]]] = {}
        for claim in group:
            if not isinstance(claim, ModelClaim | SurfaceClaim):
                continue
            payload = claim.payload
            if isinstance(payload, Capability):
                dimensions = {"supported": payload.supported}
            elif isinstance(payload, Benchmark):
                dimensions = {"value": payload.value}
            elif isinstance(payload, Money):
                dimensions = {"amount": payload.amount}
            else:
                dimensions = {
                    field.name: getattr(payload, field.name) for field in fields(payload) if field.name != "capability"
                }
            for name, value in dimensions.items():
                if value is not None:
                    values.setdefault(name, []).append((claim.claim_id, value))
        for name, candidates in sorted(values.items()):
            if len({value for _, value in candidates}) > 1:
                all_conflicts.append(Conflict(key, name, tuple(identity for identity, _ in candidates)))
    offers: list[OfferView] = []
    plans = {claim.subject for claim in versions if isinstance(claim, BaselineClaim | OverrideClaim)}
    for plan in sorted(plans, key=lambda item: (item.plan_id, item.provider_id, item.generation)):
        baselines = tuple(claim for claim in versions if isinstance(claim, BaselineClaim) and claim.subject == plan)
        campaigns = tuple(claim for claim in versions if isinstance(claim, OverrideClaim) and claim.subject == plan)
        active = tuple(claim for claim in campaigns if claim.active(at, conditions))
        diagnostics = [
            item
            for item in all_conflicts
            if item.subject == ("offer", plan.plan_id, plan.provider_id, plan.generation, "baseline")
        ]
        disputed: set[str] = set()
        for campaign_id in sorted({claim.campaign_id for claim in campaigns}):
            participants = tuple(claim for claim in campaigns if claim.campaign_id == campaign_id)
            if not any(claim in active for claim in participants):
                continue
            key = dimension(participants[0])
            boundaries = {(claim.period, claim.conditions, claim.window, claim.terms is None) for claim in participants}
            if len(boundaries) > 1:
                diagnostics.append(Conflict(key, "applicability", tuple(claim.claim_id for claim in participants)))
                if not all(claim in active for claim in participants):
                    disputed.update(
                        field.name
                        for claim in participants
                        if claim.terms is not None
                        for field in fields(Terms)
                        if getattr(claim.terms, field.name) is not None
                    )
            parents = {roots[claim.claim_id] for claim in participants}
            for parent in sorted(parents):
                ids = tuple(claim.claim_id for claim in participants if roots[claim.claim_id] == parent)
                if len(ids) > 1:
                    diagnostics.append(Conflict(key, "lineage", ids))
        terms = Terms()
        for field in fields(Terms):
            normal = [(claim.claim_id, getattr(claim.terms, field.name)) for claim in baselines]
            overlay = [
                (claim.claim_id, getattr(claim.terms, field.name))
                for claim in active
                if claim.terms is not None and getattr(claim.terms, field.name) is not None
            ]
            for label, candidates in (("baseline", normal), ("override", overlay)):
                if len({value for _, value in candidates if value is not None}) > 1:
                    diagnostics.append(
                        Conflict(
                            ("offer", plan.plan_id, plan.provider_id, plan.generation, label),
                            field.name,
                            tuple(identity for identity, value in candidates if value is not None),
                        )
                    )
            field_values = {value for _, value in overlay or normal if value is not None}
            value = next(iter(field_values)) if len(field_values) == 1 and field.name not in disputed else None
            terms = replace(terms, **{field.name: value})
        if baselines or active or diagnostics:
            offers.append(OfferView(plan, baselines, active, terms, tuple(diagnostics)))
            all_conflicts.extend(item for item in diagnostics if item not in all_conflicts)
    return EffectiveView(tuple(offers), models, surfaces, tuple(all_conflicts))
