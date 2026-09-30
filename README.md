# Model Intelligence / Creatidy Intelligence

Intended as a public/shared intelligence layer about the external AI ecosystem:
model identity, capability evidence, public pricing/plans/promotions, execution
surfaces, provenance, freshness, disagreement and semantic snapshot changes.

Currently at bootstrap/M0: only the Python foundation and development workflow
exist. The [frozen A/B/C proof contract](https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/1)
will test whether existing open upstreams plus a small temporal/provenance layer
justify a separate product. STOP is a valid outcome; the proof is not implemented.

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
