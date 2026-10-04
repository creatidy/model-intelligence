# Model Intelligence / Creatidy Intelligence

Intended as a public/shared intelligence layer about the external AI ecosystem:
model identity, capability evidence, public pricing/plans/promotions, execution
surfaces, provenance, freshness, disagreement and semantic snapshot changes.

Currently at M0: [M0-01R2](https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/9)
is a deterministic synthetic architecture proof, not a service or live market claim.
The unmerged [PR #4](https://forgejo.creatidy.com/Creatidy/model-intelligence/pulls/4)
and [PR #8](https://forgejo.creatidy.com/Creatidy/model-intelligence/pulls/8) ended
STOP_REVISE. Their behavioral evidence informs this fresh proof, not their projection
implementation. The [frozen A/B/C contract](https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/1)
still does not establish a product GO decision; STOP remains valid.

`evidence.py` retains explicit observations, typed claims and supplied revision links.
`knowledge()` exposes historical/latest-known/future versions and stale observations.
`effective_at()` independently selects versions whose explicit `effective_from` has
arrived, then excludes replaced ancestors. Revision boundaries cannot precede their
predecessors; equal boundaries permit explicit corrections. Baselines are durable,
without finite intervals. Overrides have separate version boundaries and bounded
active periods, conditions and zoned wall-time windows; withdrawal is an explicit
term-less revision. Future versions do not suppress current predecessors. An effective
override revision replaces its predecessor permanently, even after its terms expire.

Effective offers inherit omitted fields and retain current conflicts without choosing
authority/recency/order winners or multiplying quotas. Relevant campaign-boundary
diagnostics can cite inactive participants without applying their terms; irrelevant
expired/future campaigns do not clutter current results. Model benchmarks retain
context; execution evidence keeps advertised/observed/selectable/enforceable separate.
Unknown is not false and provider-managed execution need not assert a physical model.

`evidence_delta()` returns new observation/claim identities, including every supplied
revision/withdrawal announcement in a batch. Retrieval-only refresh is silent and
cannot renew freshness or rewrite semantics; missing history is rejected, not cessation.
`projection_delta()` compares only typed effective endpoint views, exposing before/after
terms, participants and conflicts. It does not reconstruct evidence events or invisible
causes. A future baseline revision is new knowledge now, but changes current projection
only at its effective boundary. Same-term version changes retain participant identities
without inventing a price change.

Reuse candidates remain models.dev, AI Model Watch, Model Price Watch, genai-prices
and codingplan: upstream catalogs/pricing are not recreated. No third-party code or
data is copied or redistributed; URLs and fixtures are synthetic. No upstream license
endorsement, official-source accuracy or product GO is asserted by this proof.

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
