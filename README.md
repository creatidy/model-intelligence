# Model Intelligence / Creatidy Intelligence

Intended as a public/shared intelligence layer about the external AI ecosystem:
model identity, capability evidence, public pricing/plans/promotions, execution
surfaces, provenance, freshness, disagreement and semantic snapshot changes.

Currently at M0: [M0-01R](https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/7)
is a deterministic, synthetic A/B/C architecture proof, not a service or live market
claim. It replaces the failed, unmerged [PR #4](https://forgejo.creatidy.com/Creatidy/model-intelligence/pulls/4)
experiment; none of that domain implementation was carried forward. The
[frozen proof contract](https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/1)
still does not establish a product GO decision. STOP remains a valid outcome.

`domain.py` holds explicit observation/claim IDs, provenance, typed model/offer/
execution evidence and supplied `revises` links. `Evidence.extend()` retains history
and permits re-retrieval without revising claims or renewing freshness. Heads are
exactly claims not referenced by revision links; a supplied revision replaces its
predecessor immediately in that knowledge set, even if the replacement is future
or expired. Earlier `Evidence` values preserve what was known before the revision.
Missing history is rejected by semantic comparison, never interpreted as cessation.

`projection.py` projects baseline heads plus active bounded override heads at T.
Only declared fields replace baseline fields. Conditions require explicitly supplied
public applicability context; zoned daily windows use local wall time. Quotas are
absolute public rules, not private balances or implicitly multiplied bonuses.
Unknown/conflicted fields remain `None`; conflicts identify the disagreeing claims.
No source authority, timestamp or sorting order selects a winner. Future overrides
are queried separately; expired/superseded ones remain only in history. Unresolved
campaign-boundary disputes remain diagnostics, even after expiry, without applying
expired terms. Typed A/C projections retain independent evidence, benchmark context
and advertised/observed/selectable/enforceable distinctions. Provider-managed
surfaces need not assert a physical model ID.

Reuse candidates remain [models.dev](https://models.dev), AI Model Watch, Model Price
Watch, [genai-prices](https://github.com/pydantic/genai-prices) and
[codingplan](https://github.com/wmpeng/codingplan): catalogs/pricing are upstream
concerns, not recreated datasets. models.dev's public catalog and genai-prices'
documented historic/daily pricing informed the boundary, not the implementation.
No third-party code/data is copied or redistributed; all proof values and URLs are
synthetic. No upstream license or official-source accuracy is asserted here.

This project does not own credentials, private subscriptions or remaining quota,
held reset credits/cards, authenticated runtime state, private workspaces, local
GPUs, preferences or task-specific final routing decisions. It is not a downstream
decision engine. Reuse existing open components only where semantics and licenses
permit; do not construct another generic model catalog.

[Forgejo](https://forgejo.creatidy.com/Creatidy/model-intelligence) is canonical for
source, issues, PRs, reviews and integration history.
[GitHub](https://github.com/creatidy/model-intelligence) is a read-only public mirror.

## Local Development

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/) and Make.

```sh
uv sync --locked --group dev
make check
uv build
```

`make check` owns locked synchronization, Ruff lint/format, basedpyright, local
standard-library tests and Git whitespace checks. Tests use no live services.
Development starts from an explicitly Adrian-selected Forgejo issue; see
[AGENTS.md](AGENTS.md). PRs target `develop`; merge, `main` promotion and releases
remain human-controlled. Licensed under [Apache-2.0](LICENSE).
