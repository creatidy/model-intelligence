# Model Intelligence / Creatidy Intelligence

Intended as a public/shared intelligence layer about the external AI ecosystem:
model identity, capability evidence, public pricing/plans/promotions, execution
surfaces, provenance, freshness, disagreement and semantic snapshot changes.

At the audited `develop` revision `fb7299810fdc4612d4e0559465faef571662c6ef`,
[M0-01R2](https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/9) is
integrated through [PR #10](https://forgejo.creatidy.com/Creatidy/model-intelligence/pulls/10).
It is a deterministic synthetic architecture proof, not a service, real-source
value proof, published knowledge artifact or verified Router integration.
The full [frozen A/B/C proof](https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/1)
remains undelivered. [Issue #12](https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/12)
is completed/closed through [merged PR #23](https://forgejo.creatidy.com/Creatidy/model-intelligence/pulls/23).
The accepted outcome is ADAPT to a thin upstream-backed public-evidence and
selected-history layer, not product GO, full A/B/C proof or installed MI-Router
acceptance. Future implementation and receipts belong to the remaining backlog,
not to reopening #12.

The later owner-accepted #15 contract adds a bounded upstream-backed public source
producer and explicit native evidence grammar `/2`, preserving `/1`. This is not
installed Router adoption, a live intelligence service, private intake or product GO.

## Documentation

- [Architecture](ARCHITECTURE.md): shared ownership, delivered semantics, evidence
  limits, integration requirements, security/reuse and decision history.
- [Roadmap and gap matrix](ROADMAP.md): G01-G13, actual Forgejo tasks, priorities,
  cross-product dependencies and measurable acceptance sequence.
- [Product-value analysis](SOURCE_VALUE_REVIEW.md): issue #12 upstream/Router
  comparison, real cases and accepted narrow public-evidence ADAPT outcome; not product GO.
- [Minimum publication contract](PUBLICATION_CONTRACT.md): completed/closed #13,
  merged PR #26, accepted payload/reference/critical semantics and exact-pin
  decision-bound conformance; not a permanent ABI or installed consumer acceptance.
- [Native producer extension](PUBLICATION_CONTRACT.md#native-public-payload-extension):
  owner-accepted #15 `/2` representation, selected models.dev/Z.ai source adapter,
  atomic retained publication and source-health facts. No consumer admission,
  private calibration, installed adoption or product GO.
- [Capability boundary record](ARCHITECTURE.md#capability-boundary-record):
  completed/closed #14, merged PR #31, versioned ownership research and guarded
  offline mapping fixtures; not production mapping approval or installed acceptance.
- [Optional operational sharing packet](OPERATIONAL_SHARING_REVIEW.md): #17
  explicit owner **REJECT current operational intake**, rationale and preserved
  reconsideration criteria with original synthetic examples;
  no receiving format, collection, sharing authorization or automatic calibration.
- [Offline operator contract](OPERATOR_CONTRACT.md): #16 producer-owned first
  definition, read-only local CLI/status/inspection/export and independently
  implemented portable consumer conformance. Console requirements are inputs,
  not an existing-receiver prerequisite; live/browser/installed gates remain open.
- [Installation and maintenance](src/model_intelligence/INSTALLATION.md): #18
  offline source-build/wheel distribution, installed compatibility and recovery.
  This resource is included in the package; no registry release or deployment.
- [Agent guidance](AGENTS.md): owner-selected work, explicit `/loop` and native bounded PR review.

The target is a local-first, open and observable system optimizing accepted work,
including cost, quota, time, remediation, review and owner attention, not cheapest
tokens. MI supplies public evidence; Router chooses/adopts knowledge, Kernel owns
task authority and outcomes, and Console presents owner-served state. This is a
target architecture, not a claim that these integrations already work.

## Delivered Proof

`evidence.py` retains explicit observations, typed claims and supplied revision links.
`knowledge()` exposes retained/latest-known/future versions and stale observations
within its supplied evidence set, not a historical acquisition-time cutoff.
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
Versions of one campaign are alternatives, including omitted-field inheritance;
different campaigns compose. A guaranteed independent replacement can mask another
campaign's uncertain participation without hiding its boundary diagnostic.

`evidence_delta()` returns new observation/claim identities, including every supplied
revision/withdrawal announcement in a batch. Retrieval-only refresh is silent and
cannot renew freshness or rewrite semantics; missing history is rejected, not cessation.
`projection_delta()` compares only typed effective endpoint views, exposing before/after
terms, participants and conflicts. It does not reconstruct evidence events or invisible
causes. A future baseline revision is new knowledge now, but changes current projection
only at its effective boundary. Same-term version changes retain participant identities
without inventing a price change.

Reuse candidates remain models.dev, AI Model Watch, Model Price Watch, genai-prices
and codingplan, with producer/benchmark sources including Artificial Analysis:
upstream catalogs/pricing are not recreated. No third-party code or
data is copied or redistributed; URLs and fixtures are synthetic. No upstream license
endorsement, official-source accuracy or product GO is asserted by this proof.

This project does not own credentials, private subscriptions or remaining quota,
held reset credits/cards, authenticated runtime state, private workspaces, local
GPUs, preferences or task-specific final routing decisions. It is not a downstream
decision engine. Reuse existing open components only where semantics and licenses
permit; do not construct another generic model catalog.
Public module dependencies are allowed; private creatidy-onprem is not required.
Completed #16 supplies an offline read-only CLI and full-snapshot export,
not a live Console feed, endpoint, event replay or effectful command API.

[Forgejo](https://forgejo.creatidy.com/Creatidy/model-intelligence) is canonical for
source, issues, PRs, reviews and integration history.
[GitHub](https://github.com/creatidy/model-intelligence) is a read-only public mirror.

## Public Producer

The narrow adapter is `model_intelligence.zai`, not a catalog fork or service.
`SOURCES` fixes inspected public URI/pin, rights route and measured byte bounds;
`SCOPE` binds its configuration. Every declared source must parse before activation.
The caller supplies time, timeout and artifact byte policy; no global TTL, daemon
or private credentials are needed.

```python
from datetime import UTC, datetime
from pathlib import Path
from model_intelligence.zai import refresh

directory = Path("public-artifacts")  # Operator-owned local output, one mutator.
directory.mkdir(exist_ok=True)
result = refresh(directory, at=datetime.now(UTC), max_artifact_bytes=65536, timeout=30)
```

The sample artifact allowance is an example for the measured first selected cut,
not a global/ecosystem limit. History can grow; inspect and explicitly adjust policy
rather than dropping observations. Failure retains complete bytes, not freshness.
Raw official pages are not distributed. Read `NOTICE` and the [source limits](PUBLICATION_CONTRACT.md#bounded-production-source-slice)
before redistribution. Public evidence does not establish entitlement, account quota,
local execution support, universal quality or a routing decision.

## Local Development

Offline operator views (no source fetching, publication writes or commands):

```sh
mi-evidence status public-artifacts --instance public-demo --at 2026-10-08T20:00:00Z --max-bytes 65536
mi-evidence inspect public-artifacts --instance public-demo --at 2026-10-08T20:00:00Z --max-bytes 65536 --json
mi-evidence export public-artifacts --instance public-demo --at 2026-10-08T20:00:00Z --max-bytes 65536
```

All JSON forms use the same validated snapshot facts. Time and per-input byte
policy are explicit operator inputs, not a global TTL/limit. Optional `--checkpoint`
is a retained cut digest, not an event offset: missing history yields a gap, never
a fabricated timeline. Source health and active publication may disagree because
their files are separate; mismatch/unavailable is exposed rather than called current.
Snapshots retain unknown/stale/future/conflicting/withdrawn/expired classifications
without source-policy or admission decisions. Human inspection prints the same
projection, not new facts. Reads never refresh or modify an artifact.

The portable consumer is original code implemented independently from the producer
in a separate context, with no `model_intelligence` imports. Its strict shape/hash/
reference/version/namespace checks and immutable last-known state exercise malformed,
unsupported, duplicate/reordered, reconnect/resync and explicit missing-history
cases. This is not actual Console adoption, browser authorization, transport security,
installed integration, source authenticity or product acceptance. Effectful commands
are empty; #17 REJECT is unchanged. See the contract for compatibility limits.

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/) and Make.

```sh
uv sync --locked --group dev
make check
uv build
```

Repeatable outside-checkout installed lifecycle validation (prepared offline backend
cache required; use a new staging directory):

```sh
uv run --no-sync python tests/verify_distribution.py /tmp/kilo/mi-distribution-check --uv-cache /tmp/kilo/mi15-validation/cache/uv
```

The verifier uses an allowlisted synthetic environment, current and pinned #13/#15
wheels, exact wheel digests, sdist rebuild, real installed CLI, original installed
source/update/outage/legacy/rollback/refusal tests and packaged support/NOTICE.
It performs no live acquisition, publishing or consumer admission. See the installed
support resource for local installation, artifact copying, recovery and limitations.

`make check` owns locked synchronization, Ruff lint/format, basedpyright, local
standard-library tests and Git whitespace checks. Tests use no live services.
Standalone development starts from an explicitly Adrian-selected Forgejo issue;
see [AGENTS.md](AGENTS.md). Only an explicit owner `/loop` delegates successive
canonical issue selection, exact independently approved PR merge to `develop` and
verified completed-issue closure. Standalone finishing stops at READY_TO_MERGE;
`main` promotion, releases and deployment are not authorized by these commands.
Licensed under [Apache-2.0](LICENSE).
