# Model Intelligence / Creatidy Intelligence

Intended as a public/shared intelligence layer about the external AI ecosystem:
model identity, capability evidence, public pricing/plans/promotions, execution
surfaces, provenance, freshness, disagreement and semantic snapshot changes.

M0-01 implements a deterministic, synthetic
[A/B/C representation proof](https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/3)
of the [frozen contract](https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/1):
model/provider evidence with preserved disagreement, bounded zoned plan promotions,
and versioned execution surfaces with advertised/observed/selectable/enforceable
assertions. `model_intelligence.domain` supplies frozen values, half-open effective
intervals distinct from observation/retrieval, epistemic states, canonical snapshots
and a closed semantic-change vocabulary. Stale evidence is not false; cached
promotions do not extend their effective end. Unknown physical identity stays unknown.

Fixtures in `tests/proof_fixtures.py` are invented, not current market truth. They
provide exact campaign boundaries where official wording leaves precision unclear.
Offer conditions are recorded, not evaluated; multipliers are not combined.
Structured-output fixtures refer to CLI JSON events, not schema-constrained answers.
Conflicts compare complete assertions within explicit contexts; benchmark scores
require matching methodology/version/configuration, but prices compare per provider
identity. No authority winner or universal score is selected. Semantic events compare
effective endpoints (not intervening history); price changes mean changed price
evidence, not an adjudicated provider announcement. Retrieval-only changes are silent.

Reuse inspection covered [models.dev](https://models.dev),
[AI Model Watch](https://aimodelwatch.dev/api),
[Model Price Watch](https://modelpricewatch.com/about/),
[genai-prices](https://github.com/pydantic/genai-prices) and
[codingplan](https://github.com/wmpeng/codingplan). Catalogs, historical/conditional
pricing and subscription comparisons already exist upstream. No upstream code or
datasets are copied. Official Z.ai/ZCode shape references are linked in fixtures;
synthetic observation/assertion labels do not imply runtime verification.

Architecture result: **CONTINUE** for this small representation proof only. A/B/C
fit one shared temporal/provenance layer without provider-specific classes or a DSL.
This does not establish a product gap or decide the final product GO/NO-GO. Ingestion,
services, storage, scheduling, live verification and downstream integrations remain
unimplemented; STOP remains a valid later outcome. Runtime dependencies remain empty.

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
