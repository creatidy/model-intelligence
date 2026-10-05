# Model Intelligence Architecture

## Authority and Status

This document records the owner-selected [alignment task #11][alignment], not a
new implementation mandate. Requirements come from *Creatidy - shared system
architecture*, v1.0, 2026-10-04, filename
`Creatidy_architektura_systemu_2026-10-04.md`, owner-supplied SHA-256
`4e64121599ac30896afb77574b2fd16cddfc3420afde37108611715c24b56e92`.
The full file was not located in the available workspace or `/tmp/kilo`; the MI
brief is the available source. Applicable source sections supplied by the owner
are 1-5, 7-10 and 12-18. We do not invent finer section mappings or claim to have
computed the file hash. [ROADMAP.md](ROADMAP.md) maps the brief's requirements to
evidence and registered work.

| Status | Meaning |
| --- | --- |
| Agreed | Binding owner direction, including the shared roles and boundaries below. |
| Verified | Source/test/platform observation at a named revision; recheck before calling it current. |
| Proposed Clarification | Recommendation with rationale, requiring owner acceptance through the selected issue/PR workflow. |
| To Prove | Unanswered evidence/contract question with a bounded Forgejo task; not a fictional implementation specification. |

Verified MI baseline: canonical `develop`
`fb7299810fdc4612d4e0559465faef571662c6ef`, owner merge of [PR #10][r2-pr] at
2026-10-04 22:14:43 UTC. The historical `6edd31d491a41a92e73ebfc6d9ee81c284129f8a`
had only bootstrap/workflow; the advance integrates synthetic R2, not a deployed
service. Forgejo owns issue/PR/integration state; GitHub is a read-only mirror.
No live-source publication, MI consumer integration or product inference was
verified by this documentation work.

## Mission and Ownership

Agreed mission: an open, local-first, observable system for individuals and small
teams optimizing the path to an accepted result across money, subscription quota,
time, corrections, review and owner attention. A cheap token is not the objective.
MI's value must be demonstrated beyond existing sources, not asserted by building
another manually maintained catalog. Professional completion means delivering the
accepted evidence scope correctly, not collecting all data in the world.

| Owner | Responsibility | Not MI responsibility |
| --- | --- | --- |
| Kernel | Intent, TaskSpec/WorkUnit/Attempt, authority, workspace, durable lifecycle, harness control, verification, review/remediation and outcome evidence. | Task controller, review loop, sandbox, scheduler or workspace cache. |
| Scarcity Router | Execution sources/accounts/capacity pools, private telemetry, channel compatibility, cost/selection policy, admission, gateway and provider calls. | Private remaining quota, held resets, inference or final task routing. |
| Model Intelligence | External model/interface/benchmark/public-term evidence, provenance, applicability, conflicts, versioned knowledge publication and semantic change. | Account entitlement, live inventory/admission, runtime authentication or task permission. |
| Console | Cross-product views and delegation of authorized commands to the feature owner. | Independent scheduler/ranker, permissions database or direct access to another owner's state database. |

Harness is an existing agent running the model-tools-result loop. Kernel controls
it through a documented adapter, not IDE clicking or an unproved new agent.
Target paths are Kernel -> harness adapter -> harness -> workspace, and harness
inference -> Router gateway -> permitted source. MI publishes knowledge for Router;
Kernel normally receives its reference indirectly through Router-backed evidence.
All producers serve their own state/events to CLI/Console. These are target paths,
not claims of delivered integration. No repository or public identifier is renamed.

Public modules may depend on each other. They must not require private
creatidy-onprem. Separate product ownership does not require four resident
services, a shared database, message broker or Kubernetes. Existing public
contracts must be inspected before proposing new interfaces.

## Verified Temporal Proof

The integrated [R2 issue #9][r2] and [tests](tests/test_separated_proof.py) use
synthetic identities, `example.invalid` references and synthetic licenses. Their
coverage is semantic evidence, not verified manufacturer facts, redistribution
rights or a product GO. The original [A/B/C contract #1][abc] remains the real-source
value/rights and unbiased STOP/GO gate; [#12][value] supplies the missing research.

| Existing implementation | Delivered meaning and representative proof |
| --- | --- |
| [`Observation`, `Evidence.extend`](src/model_intelligence/evidence.py) | Explicit source/reference and observation identities; independent acquisition/freshness. Semantic rewrites and invented lineage rejected. `test_retrieval_only_silent_stale_stays_stale_pr4`. |
| [`knowledge`](src/model_intelligence/evidence.py) | Retained history, latest-known heads, future claims and stale observations in the supplied evidence set. `test_required_future_baseline_no_unknown_gap`. |
| [`effective_at`](src/model_intelligence/projection.py) | Arrived explicit version boundaries replace ancestors independently of knowledge heads; durable baselines, bounded campaign terms, zoned conditions/windows and explicit withdrawal. `test_shortening_extension_term_change_and_no_resurrection`. |
| `Conflict`, `OfferView` | Alternatives within one campaign, composition across independent campaigns, no source/authority/recency winner or implicit multiplier. Baseline disagreement survives masking. `test_sibling_omissions_are_alternatives_not_composable_campaigns`. |
| [`evidence_delta`](src/model_intelligence/deltas.py) | New IDs/explicit links, including batched/future revisions; missing history is rejected, not cessation. `test_missing_rows_never_cessation_pr4`. |
| `projection_delta` | Effective endpoint participants/terms/conflicts, not reconstruction of hidden intermediate causes. `test_batch_revisions_evidence_not_intermediate_projection_pr8`. |
| `Benchmark`, `SurfaceEvidence` | Contextual original measurements; advertised/observed/selectable/enforceable remain separate nullable assertions. `test_model_context_and_future_revisions`, `test_surface_dimensions_unknown_false_and_future_revision`. |

Preserve these accepted invariants. Future-known versions do not prematurely remove
current predecessors. Explicit corrections/withdrawals retain history. A campaign
revision permanently replaces its predecessor once effective; expiry cannot
resurrect it. Omitted override fields inherit; unknown baseline fields are not
zeros. Public quota terms are not private balance. Equal values or missing rows
never supply identity, revision, cessation or an authority winner.

Important limits: `knowledge(evidence, at)` does not filter evidence by when it was
learned; it is not a historical "what was known at T" query. Replay needs a frozen
input evidence set/reference. `effective_at()` does not enforce freshness policy;
`fresh_until=None` means no stale flag, not affirmative freshness. `Observation`
license/distribution strings are declarations, not an enforced publication gate.
There is no integrated snapshot serializer/version/manifest, persisted-history
contract, publisher, source client, MI CLI or consumer loader. [#13][publication]
must settle evidence-cut/validity semantics; [#15][acquisition] delivers the
permitted-source producer, not this documentation task.

## Agreed Evidence Requirements

Identity must distinguish model, alias/lineage, version, provider, serving channel
and parameter configuration. The same model can have different channel conditions;
plan-managed execution may not reveal a physical model. An opaque variant does not
prove reasoning effort. Unknown is distinct from zero, false and literal `none`.
R2's supplied `Model`/`Surface` identities are not a complete mapping contract.
Public capability/limit evidence, including context/output/interface limits when
available, must retain native units and channel/configuration applicability.
R2's nullable boolean `Capability` does not establish this broader contract;
[#14][semantics]/[#15][acquisition] cover missing/incompatible/conflicting limits
without treating unknown as unlimited or weakening consumer requirements.

Each material observation needs source and revision/reference, subject, acquisition
time and applicability conditions/time. Public known/unknown/stale/conflicting/
withdrawn meanings must be explicit in [#13][publication]; no new status enum is
approved here. Correction/revocation cannot erase earlier evidence. Source failure
or disappearance cannot extend promotion validity or turn missing price into free
access. Promotions may depend on dates, timezone, plan, model, access channel and
harness; applicable conflict, missing data, changed terms and expiry stay distinct.

Benchmarks retain original metric, unit, date, method/version, configuration and
provenance. Manufacturer declarations do not prove local harness capability.
No single intelligence score proves all usefulness, and a benchmark does not
automatically imply `coding=5`. Kernel supplies task requirements; Router matches
them. MI does not classify private tasks or establish entitlement.

## Integration Contracts

Agreed primary output is recognizable versioned knowledge with provenance,
validity, conflicts and meaningful change. MI need not be synchronous on every
inference call. Router owns acceptance/freshness/offline policy and private
telemetry; an MI outage alone must not stop an ongoing authorized Attempt. New use
depends on consumer policy, with critical withdrawal distinct from a missing new
price. MI must expose those meanings, not impose a universal undocumented TTL.

The read-only planning audit examined the Router's local artifact/calibration seam,
but external checkout reads are outside the native reviewer's permissions. This
PR therefore does not publish those sibling-code assertions as independently
Verified contracts. Existing Router task records and the new [consumer #176][router-mi]
define obligations to inspect against frozen producer/consumer source in
[#13][publication]/[#14][semantics]: admitted offline evidence, explicit identity
and effort, reviewed calibration, provenance, compatibility and safe migration.
Issue records are contract evidence, not substitute source/test/live evidence or
permission to redistribute curated data. The MI consumer contract is still To Prove.

| Contract | Producer / consumer owner | Required receipt | Registered work |
| --- | --- | --- | --- |
| Knowledge publication/adoption/reference | MI / Router / Kernel | Complete recognizable artifact; evidence-cut, compatibility, corruption/partial-update rejection, provenance and immutable utilized reference. | [MI #13][publication], production [#15][acquisition], [Router #176][router-mi], [Kernel #55][kernel-knowledge] |
| Capability identity/calibration | MI raw evidence / Router mapping and matching / Kernel requirements | Small versioned language with negative/unknown cases; no automatic transfer of existing calibration or third scale. | [MI #14][semantics], [Router #175][router-requirements], [Kernel #49][kernel-intake]/[#51][kernel-requirements] |
| Operator state/events | Each producer / CLI and Console | Consistent facts, correlation/version, reconnect/dedup position and explicit history gaps; no direct foreign DB edits. | [MI #16][operator], separate [Kernel #57][kernel-events]/[Router #183][router-events] producers |
| Optional operational evidence | Kernel/Router local export / MI only after separate approval | Consent/minimization/provenance and cautious inference; denial/withdrawal leaves core operation intact. | [MI #17][feedback], local [Kernel #58][kernel-outcomes]/[Router #177][router-feedback] |
| Installation/updates and composed receipt | MI public artifact / Router, indirect Kernel evidence | Installed compatible versions, migrations/recovery, outage and operator acceptance. | [MI #18][distribution]/[#19][acceptance], [Kernel #62][kernel-migration]/[#60][kernel-acceptance] |

Review caught incomplete discovery during concurrent task registration. The
corrected registry links the actual Kernel children above, rather than leaving
known reference/export/state/migration consumers only under planning parent
[#46][kernel]. These are planned work, not integrated contracts. A Console consumer
counterpart was not identified; [MI #16][operator] records its expected owner/contract
without designing Console. [ROADMAP.md](ROADMAP.md) gives the complete received
requirements/gateway/budget/concurrency/compatibility matches and their scope.

No endpoint, payload, CLI flag, protocol version, global ontology, PKI or broker is
approved by this table. [#13][publication] and [#14][semantics] are bounded contract
research/conformance tasks. Their proposed choices require owner acceptance and
producer-consumer tests before a separately selected functional delivery. Optional
Kernel queries for versioned harness/interface evidence cannot create a second
ranker or replace adapter tests. Router ZCode support is not Kernel ZCode runtime.

## Privacy, Security and Reuse

MI does not store provider credentials, private remaining quota/subscriptions,
held reset credits/cards, authenticated runtime state, private GPU/workspace,
preferences/policies or current routing decisions. Public plans/promotions are
evidence of conditions; Router determines their applicability to an account/channel.
MI grants neither account entitlement nor Kernel authority.

Kernel outcomes/tests/APPROVE have limited scope and confounding from task
difficulty, harness, prompt and reviewer. Local export/analysis belongs first to
Kernel/Router. Any MI sharing is separately approved opt-in, with minimization,
consent scope, provenance and metadata identifiability analysis in [#17][feedback].
There is no mandatory central feedback API or automatic training requirement.

Reuse order is ADOPT -> VENDOR/COPY -> PORT -> ADAPT -> BUILD. Consider existing
models.dev, AI Model Watch, Model Price Watch, pydantic/genai-prices, codingplan,
producer sources and benchmarks including Artificial Analysis. Reuse includes
data, mappings, parsers, algorithms, fixtures and tests, not just dependencies.
Earlier source-shape investigations in [#3][first] are evidence to revisit, not
current approval. No material is newly copied by this alignment. Exact source
revision/files, semantic fit, negative tests, safety, dependencies/maintenance and
separate code/data/API/attribution/redistribution/commercial rights must be verified
in [#12][value] before material use. Unknown rights block publication; public read
is not blanket permission. Record NOTICE/provenance when material first lands.

Imported data/text is untrusted content, never executable instructions or a
permission change. [#15][acquisition] must prove safe retrieval/parsing and recovery
for the admitted sources; no vulnerability is claimed in a nonexistent fetcher.
Use existing scheduling/notification mechanisms when sufficient, not a generic
scheduler. Console delegates only commands MI actually exposes and authorizes;
the frontend does not resolve source disagreements or swap knowledge by itself.

## Decision History and Open Questions

No standalone ADR files existed in the audited baseline. This record preserves
the decisions in their canonical issues/PRs rather than rewriting them.

| Record | Preserved outcome / superseded assumption |
| --- | --- |
| [#1][abc], merged bootstrap PR #2 | Foundation delivered; future real-source A/B/C and unbiased STOP/GO remain binding. Bootstrap-only status is superseded by merged R2, not by a GO decision. |
| [#3][first] / [PR #4][first-pr] | Unmerged STOP_REVISE at `303f5fe118a592f3cf5e7ea47c5955625850ea28`; payload/time/row heuristics did not establish revision/cessation. No restart or implicit projection-code reuse. |
| [#5][workflow], merged PR #6 | Native fresh whole-PR review in one normal checkout supersedes old worktree/external-controller/onprem review assumptions. |
| [#7][second] / [PR #8][second-pr] | Unmerged STOP_REVISE at `c70bbd380a0728bad04112f1c02f076fb94ee1e4`; latest-known heads and effective applicability plus causal deltas required separation. Budget/history retained. |
| [#9][r2], merged [PR #10][r2-pr] | R2 separation delivered; final native APPROVE at `177471b7bc083e796d03096382740d1b2d80d676` is synthetic-proof approval, not live accuracy or final GO. |
| [#11][alignment], current owner direction | Shared target and full known professional scope replace a bootstrap-only prohibition on public-module dependencies. Private onprem dependence remains disallowed. Registered gaps do not authorize feature implementation. |

Proposed Clarification: use frozen evidence-cut references and explicit per-class
validity diagnostics rather than treating an effective-time query as historical
acquisition replay. Rationale: current R2 deliberately separates supplied knowledge
from applicability. Approve the actual contract through [#13][publication], not
by silently changing the proof API in this documentation PR.

To Prove/decide: lawful added value and owner STOP/GO ([#12][value]); precise
publication/update/completeness mechanism and consumer policies ([#13][publication]);
raw-evidence versus derived-calibration ownership if contested ([#14][semantics]);
optional feedback benefit/privacy approval or explicit return criterion
([#17][feedback]). No invented numeric cost/quality/time threshold settles these.
Routine documentation defects are not architecture decisions. A documentation
APPROVE leaves the [functional roadmap](ROADMAP.md) open and is never
`READY_FOR_LIVE_TASK`.

[alignment]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/11
[abc]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/1
[first]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/3
[first-pr]: https://forgejo.creatidy.com/Creatidy/model-intelligence/pulls/4
[workflow]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/5
[second]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/7
[second-pr]: https://forgejo.creatidy.com/Creatidy/model-intelligence/pulls/8
[r2]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/9
[r2-pr]: https://forgejo.creatidy.com/Creatidy/model-intelligence/pulls/10
[value]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/12
[publication]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/13
[semantics]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/14
[acquisition]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/15
[operator]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/16
[feedback]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/17
[distribution]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/18
[acceptance]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/19
[router]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/173
[kernel]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/46
[router-mi]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/176
[router-requirements]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/175
[router-feedback]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/177
[router-events]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/183
[kernel-intake]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/49
[kernel-requirements]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/51
[kernel-knowledge]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/55
[kernel-events]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/57
[kernel-outcomes]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/58
[kernel-acceptance]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/60
[kernel-migration]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/62
