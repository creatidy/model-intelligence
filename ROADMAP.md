# Evidence and Delivery Roadmap

This is the working requirements/evidence/task matrix for [alignment #11][alignment].
Read [ARCHITECTURE.md](ARCHITECTURE.md) for source/hash availability, status meanings,
ownership and preserved decisions. All source references below use the supplied
MI section bundle 1-5, 7-10, 12-18 of v1.0 (2026-10-04); brief section references
identify available requirements, not fabricated headings in the unavailable file.
No issue is selected for functional implementation by appearing in this roadmap.

## Baseline and Deduplication

Verified MI base: `fb7299810fdc4612d4e0559465faef571662c6ef` (owner-merged PR #10).
The historical `6edd31d491a41a92e73ebfc6d9ee81c284129f8a` predates the integrated
R2 proof. Its tests are synthetic and network-free. No deployed intelligence
service or installed MI-Router path is evidenced. Open issue state is not absence
of implementation: [#9][r2] is delivered; [#5][workflow] is integrated workflow.
[Closed #1][abc] completed bootstrap, not the future real-source value gate.
[PR #4][first-pr] and [PR #8][second-pr] remain unmerged STOP_REVISE, not features
to patch or restart. Existing architectural/adversarial/source research is reused
as evidence, not as license permission or implicitly accepted implementation.

The actual cross-product planning parents are [Router #173][router] and
[Kernel #46][kernel]. Existing Kernel [#11][allocator] delivered a recommendation-only
allocator and explicitly excludes gateway/feedback learning. Router [#146][harness]
records harness/transport boundaries, [#140][router-ux] administrator UX,
[#139][router-tls] TLS and [#141][router-acceptance] install/client acceptance.
None proves MI publication/adoption. Router's existing effort/calibration work
[#57][effort], [#79][calibration], [#107][binding] and [#126][tracks] is not a shared MI
calibration contract and must not be reimplemented under a different owner.

Read-only counterpart refresh, corrected after independent review of concurrent
registration, found the following actual registered children.
The matching criteria, not merely similar titles, justify these links. They are
open plans; no producer-consumer implementation or live receipt is inferred.
MI #12-#19 have been supplemented with their applicable links in Forgejo.

| Contract/dependency | Actual counterpart and acceptance match |
| --- | --- |
| G01/G04 harness/gateway | [Router #174][router-pin] executable recommendation/admission/exact pin; [Kernel #47][kernel-harness] feasibility proof, [#53][kernel-runtime] conditional lifecycle delivery and [#52][kernel-routing] Attempt-bound decision/identity consumption. [Router #178][router-narrowing] library-core narrowing is not a public gateway proof. |
| G02/G05 approved requirements | [Kernel #49][kernel-intake] ordinary-issue specification, [#51][kernel-requirements] hard requirements without L0 fallback; [Router #175][router-requirements] monotone eligibility. MI [#14][semantics] owns evidence, not task classification. |
| G03 product review | [Kernel #54][kernel-review] durable candidate-bound bounded remediation, exact-subject checks/fresh independent verdict and findings lineage. Not MI's local developer workflow. |
| G06/G13 MI publication/adoption/reference | [Router #176][router-mi] complete admitted snapshots/provenance/atomic migration/offline expiry; [Kernel #55][kernel-knowledge] immutable utilized reference. Completed MI [#13][publication] supplies the minimum contract; remaining [#15][acquisition] producer/[#19][acceptance] installed receipt. |
| G07 local outcome evidence | [Kernel #58][kernel-outcomes] private versioned full-cost/verdict export, local-by-default with scoped consent; [Router #177][router-feedback] correlation/dedup/incomplete-history and cautious calibration. MI [#17][feedback] owner REJECT current operational intake; future reconsideration is separately gated. |
| G08 state/events | Separate [Kernel #57][kernel-events], [Router #183][router-events] and MI [#16][operator] owner-authorized reconnectable producers; Router [#182][router-cli] CLI preserving JSON/pipes. Console consumer counterpart not identified. |
| G09 workspace authority | [Kernel #50][kernel-isolation] isolation/trusted-check preconditions and [Router #180][router-workspace] backend-native agent/workspace boundary; neither replaces MI parser safety [#15][acquisition]. |
| G10 identity/protocol | [Router #179][router-identity] opaque variant versus effort/requested/resolved/dispatched/observed identity; [#181][router-protocol] versioned harness/protocol; [Kernel #52][kernel-routing] sticky execution identity after [#47][kernel-harness] feasibility. |
| G11 concurrency/source ownership | [Kernel #59][kernel-concurrency] controller/workspace/manual-edit reconciliation; [#61][kernel-cache] host-qualified cache/locking/dispatch/migration. MI owns artifact completeness, not Kernel scheduling/cache. |
| G12 private economics | [Router #184][router-economics] account/access-mode/quota-pool/call-cost boundaries; [Kernel #56][kernel-budget] whole-task budgets across Attempts/tools/review, unknown/dedup/recovery. [#48][kernel-lifetime] lifetime is a separate prerequisite. MI owns only public terms. |
| G13 compatibility and installed receipt | [Kernel #62][kernel-migration] public installation/contract/state migration and [#60][kernel-acceptance] controlled-task receipt; [Router #185][router-migration] contract/artifact upgrades and [#186][router-distribution] public distribution/platform gates. MI [#18][distribution]/[#19][acceptance] own its artifacts and receipt, not other-product deployment. |

Kernel [#46][kernel] remains the planning parent, not a substitute for these known
children. #47 and #49 are not superseded: #53/#52 receive the harness proof and
#51 translates authorized intake requirements. These are distinct receipt
boundaries. Discovery corrections preserve history and never duplicate producer
work in MI or turn issue contracts into verified source/live implementation.

## G01-G13 Matrix

G identifiers are analysis IDs, not issue numbers. Non-MI rows are explicit
dependencies, not local implementation authorizations. Contract owners remain
responsible even where a consumer link has not yet been identified.

| Gap | Owner of this part | Current evidence and disposition | Actual work / why no MI implementation issue |
| --- | --- | --- | --- |
| G01 Harness adapters | Kernel; harness owns agent loop | MI `SurfaceEvidence` is public assertion evidence, not runtime adapter control. Kernel adapter scope is planned. | [Kernel #47][kernel-harness] proof/[#53][kernel-runtime] delivery; MI [#14][semantics] evidence slice, no MI controller. |
| G02 Ordinary task intake | Kernel | No task intake in MI source inventory; it is outside its ownership. | [Kernel #49][kernel-intake]; no MI issue because MI must not accept/classify private tasks. |
| G03 Review/remediation | Kernel product; MI development workflow locally | [#5][workflow]/merged PR #6 deliver native fresh frozen-PR review with three-round bound, not Kernel runtime review orchestration. | Local development fulfilled; product [Kernel #54][kernel-review], no duplicate MI review service. |
| G04 Gateway integration | Router producer; Kernel/harness consumer | [Kernel #11][allocator] is recommendation-only; neither MI proof nor Router harness architecture [#146][harness] proves gateway integration. | [Router #174][router-pin]/[#178][router-narrowing], [Kernel #52][kernel-routing] after #47 proof; no MI gateway task. |
| G05 Task requirements / semantic boundary | Kernel requirements, Router matching/calibration, MI raw evidence | Completed #14/merged PR #31 retain ownership and versioned offline mapping/negative fixtures; no third scale or production mapping approval. | Preserve [#14][semantics]; separately accepted production mapping and [Router #175][router-requirements]/[Kernel #51][kernel-requirements] after #49 intake remain. |
| G06 MI and integration | MI publication, Router consumption, Kernel utilized reference | #9/#10 temporal proof, closed #12/#23 ADAPT analysis and completed #13/merged PR #26 minimum decision-bound contract/conformance. Not full A/B/C or installed acceptance. | Remaining [#15][acquisition]/[#19][acceptance], [Router #176][router-mi], [Kernel #55][kernel-knowledge]; no reopening #12/#13 or another temporal proof. |
| G07 Outcome feedback | Kernel/Router local export/analysis; no current MI intake | #17 owner REJECT: no demonstrated incremental need over public evidence/reproduction/local analysis; scoped outcomes are confounded, not quality ground truth. | Preserve [#17][feedback] [reconsideration criteria](OPERATIONAL_SHARING_REVIEW.md#reconsideration-and-compatibility); no receiving API/format/collection/automatic calibration. |
| G08 Observability | MI own state/events; Console views; others own theirs | `evidence_delta`/`projection_delta` compare evidence/endpoints, not a reconnectable event feed. No MI status/inspect/Console export delivered. | [#16][operator]; separate [Kernel #57][kernel-events]/[Router #183][router-events]. Console counterpart not identified. |
| G09 Isolation | Kernel workspace/harness; Router call execution | MI has no sandbox. Its separate acquisition/parser threat model is prospective, not evidence of an existing fetch vulnerability. | [Kernel #50][kernel-isolation]/[Router #180][router-workspace]; MI retrieval safety combined in [#15][acquisition], not a sandbox duplicate. |
| G10 Identity/protocol evidence | MI public evidence; Router live inventory/admission; Kernel runtime identity | R2 identities, completed #13 native payload/context and #14/PR #31 bounded alias/channel/configuration negatives exist; production mapping/installed compatibility remain incomplete. | Remaining [#15][acquisition] accepted producer/mapping, [Kernel #52][kernel-routing]/[Router #179][router-identity]/[#181][router-protocol]; no entitlement attestation. |
| G11 Multiple tasks/concurrency | Kernel task scheduling; Router admission | No MI task scheduler; completed #13 contract/fixture rejects incomplete mixed updates, not a production publisher. | [Kernel #59][kernel-concurrency]/[#61][kernel-cache]; remaining MI [#15][acquisition], no task concurrency machinery. |
| G12 End-to-end budget / public conditions | MI public rules; Router private accounting; Kernel whole-task budget | R2 terms/expiry, closed #12 economics analysis and completed #13 native payload/reference proof; no account balance or guaranteed task cost. | Remaining MI [#15][acquisition]; [Router #184][router-economics]/[Kernel #56][kernel-budget] own accounting; #48 is lifetime only. |
| G13 Versioning/distribution | Each producer/consumer owns its lifecycle | Typed wheel and accepted minimum #13 frame/payload/version/rejection/migration obligations exist; no permanent ABI, production updates/migration or installed receipt. | Remaining [#18][distribution]/[#19][acceptance], [Router #185][router-migration]/[#186][router-distribution], [Kernel #62][kernel-migration]/[#60][kernel-acceptance]; no private onprem. |

## Requirement Coverage

All observations here are scoped to the audited revision. A fulfilled proof slice
does not mark its broader G gap complete.

| Available requirement | Evidence / missing outcome | Documents corrected | Disposition |
| --- | --- | --- | --- |
| Brief 1-2: source statuses, roles, local-first target, public dependencies | Earlier README/rules lacked shared boundaries; no independent public MI service claimed. | README, ARCHITECTURE, AGENTS, discipline/task rules | Documentation [#11][alignment]; known product gaps below remain open. |
| Brief 3-5: real value, source/reuse/license proof and A/B/C | Closed #12/merged PR #23 provide accepted ADAPT source comparison; synthetic tests and #1 are not full real-source proof. | Architecture proof/reuse/history, this roadmap | Preserve completed [#12][value], #1 and delivered #9; future implementation/receipts stay in the backlog. |
| Brief 4: lineage, applicability, withdrawal, conflicts, expiry | `Evidence.extend`, `knowledge`, `effective_at`; future baseline, branch, zoned lifecycle and predecessor regression tests. | README proof, architecture verified semantics | Already fulfilled synthetic slice by [#9][r2]; producer meaning/conformance in [#13][publication]/[#15][acquisition]. |
| Brief 4: identity, public capabilities/limits, benchmark context and calibration ownership | Completed #14 research retains ownership; owner decision15692 accepts minimum #15 production representation through new `/2`, never a third scale or `/1` reinterpretation. | Architecture producer extension | Preserve completed [#14][semantics]; #15 actual selected-source/rights/validation/review gates and Router-only mapping/admission remain. |
| Brief 4: recognizable snapshot, validity/conflicts/change, complete publication | Completed #13/merged PR #26 supplies framing/payload/cut/evaluation/decision manifest and offline conformance, not production publisher; `knowledge` remains supplied-cut classification. | Architecture integration/limits | Preserve completed [#13][publication]; remaining [#15][acquisition] producer/[#18][distribution] updates. |
| Brief 4: failure, freshness, critical revocation, offline consumer policy | Completed #13 defines public semantics and retained-input failure conformance; `effective_at` does not exclude stale and absent freshness is not affirmative validity. | Architecture limits/outage | Remaining [#15][acquisition]/[#19][acceptance]; Router owns actual fallback/TTL/admission and Kernel authority. |
| Brief 4-5: public plans/prices/promotions and untrusted source normalization | Closed #12 independently reviewed public-source analysis; no production fetch/parser or installed receipt. | Architecture security/reuse | Remaining [#15][acquisition]: actual source-use/copying rights, unknown terms and failure safety; no new public-fact legal gate or reopening [#12][value]. |
| Brief 4-5: opt-in feedback with minimization/consent and confounding | #17 explicit owner REJECT current operational intake; no sharing contract or unbiased ground truth from operational results. | Architecture privacy and [decision packet](OPERATIONAL_SHARING_REVIEW.md) | Preserved reconsideration/rights/consent/negative conformance and separate approval; no central API/training. |
| Brief 4-5: operator CLI/status/inspect, semantic vs transport change, Console export | Owner correction15780 accepts MI-first offline read-only contract over actual #13/#15 facts; deltas still not history feed. | Architecture operator contract | [#16][operator] independent portable consumer receipt; no existing Console/browser prerequisite or deferred live-gate waiver. |
| Brief 5-6: professional security, migrations, public install/maintenance and receipt | Python foundation exists, not data update/recovery or installed producer-consumer acceptance. | Architecture security, roadmap gates | New [#15][acquisition]/[#18][distribution]/[#19][acceptance], dependencies recorded rather than requirements omitted. |
| Brief 7-8: no feature implementation/inference/effects; independent bounded review | Existing native workflow/Makefile; exact branch gates still required for this delivery. | AGENTS/task rules; this roadmap | [#11][alignment] focused documentation PR; #5 covers reused workflow, not another controller. |

## Registered Deliveries

Priorities are risk/dependency ordering, not authorization or invented budgets.
P1 settles lawful value/meaning before building distribution; P2 records required
professional delivery after those gates. Each linked issue includes negative
scenarios, reuse obligations, diagnostics/security/compatibility and future access
requirements. Dependency comments complement its acceptance body.

| Issue | Priority and independent result | Dependencies / receipt boundary |
| --- | --- | --- |
| [#12: Product-value analysis][value] | Completed/closed through merged PR #23: accepted ADAPT to a thin upstream-backed public-evidence and selected-history layer. | Reuses #1/#9 and pinned source research; not product GO, full A/B/C proof or installed MI-Router acceptance. |
| [#13: Snapshot publication contract][publication] | Completed/closed through merged PR #26: accepted minimum payload/framing/reference/source-critical semantics and verifiable decision-bound pinned-code conformance. | Not permanent ABI, private policy, product GO or installed acceptance; remaining production mapping, #15 producer and actual consumers. |
| [#14: Capability identity/calibration boundary][semantics] | Completed/closed through merged PR #31: small versioned ownership/semantic research record and negative fixtures, no third scale. | Existing Router assessments/effort and narrow Kernel reference trace; not production mapping approval or rich requirements/installed acceptance. |
| [#15: Permitted-source acquisition/refresh][acquisition] | Completed/closed via merged PR #34: owner minimum15692 `/2`, selected upstream-backed source producer, retained publication/health, lifecycle/safety/rights receipts. | Integrated147 validation/exact review6; no installed adoption, live execution or GO. |
| [#16: MI operator status/Console events][operator] | P2: governing owner correction15780, traceable to original AC1/3/4. MI-first versioned offline read-only status/inspect/export with independent portable consumer conformance. | Delivered #13/#15; Console semantic requirements input, NOT wire ownership/Console6/browser/receiver prerequisite. Empty effectful commands; no endpoints/replay/globalcursors/auth/service/secondstore. Actual Console/browser/transport/installed/product gates remain separate. |
| [#17: Optional outcome sharing decision][feedback] | Explicit owner decision recorded: REJECT current operational intake, with rationale and concrete reconsideration criteria in [PR #33](https://forgejo.creatidy.com/Creatidy/model-intelligence/pulls/33). Delivery integration follows validation/fresh review. | Kernel/Router local analysis remains primary. Not permanent prohibition, sharing permission, product GO or a prerequisite forcing optional sharing into the core. |
| [#18: Public install/update/migrations][distribution] | P2: installed public package/artifact compatibility, update/rollback and recovery without history loss. | #12-#16; only actual existing config/data formats require migration, no guessed backward-compatibility layer. |
| [#19: Installed evidence-path acceptance][acceptance] | P2: frozen installed producer/consumer revisions with complete/update/outage/unknown/withdrawal and operator receipt. | #12-#16/#18 plus Router consumer, Kernel reference if available; explicitly record missing downstream acceptance. |

## First-Priority Deviations

Issue #12 is completed/closed through [merged PR #23][value-pr]. Its independently
reviewed [product-value analysis](SOURCE_VALUE_REVIEW.md) has the accepted outcome
ADAPT to a thin upstream-backed public-evidence/applicability and selected-history
layer, not a replacement catalog, calculator or resident service. Direct upstream
use plus Router-local adapters is an explicit STOP alternative. The owner's
clarification treats unknown campaign boundaries and conflicts as normal states,
not research failures; an artificial benchmark/price conflict is not a viability
gate. Dataset-copying rights apply to an actual copying route, not to ordinary
public-fact citations. No owner GO, full A/B/C proof, installed MI-Router acceptance
or functional selection follows from accepted ADAPT. Future implementation and
receipts belong to the remaining backlog, not to reopening #12.

These are current limits or incomplete target contracts, not hidden by a possible
documentation APPROVE. No routine temporal proof defect is asserted here.

| Verified fact | User/integration consequence and urgency | Closure condition |
| --- | --- | --- |
| R2 remains synthetic; closed #12/merged PR #23 establish accepted ADAPT, #13 minimum publication and #14 bounded semantic research are integrated. | Most catalog/pricing/history data stays upstream; scale and installed benefit are not proved by these receipts. | Remaining [#15][acquisition]-[#19][acceptance], separately accepted production mapping and actual copying/installed receipts; do not repeat completed #12/#13/#14. |
| Accepted #13 framing/payload/utilization artifacts and offline negative conformance exist; no production publisher or installed receipt. | Router at the inspected pin does not emit/admit the accepted MI binding; compatibility is not installed use. | Remaining [#15][acquisition] production/[#19][acceptance] actual consumption with Router #176/Kernel #55; preserve completed #13. |
| `knowledge` has no acquisition cutoff; absent freshness yields no stale flag; effective projection does not enforce freshness. | Supplied knowledge must not be mistaken for historical acquisition or automatic new-use freshness approval. | Completed [#13][publication] frozen-input/evaluation/reference semantics and negative tests; actual Router owns freshness policy. Preserve #9 API. |
| Completed #14 retains ownership; later owner15692 accepts minimum #15 versioned production assertions, not MI consumer policy. | Automatic benchmark-to-rating, variant-to-effort or cross-channel assumptions remain forbidden. | Preserve [#14][semantics]; actual Router/Kernel adoption, adapter and installed receipts before corresponding operational claims. |

Required subsequent backlog, not immediate proof defects: secure permitted-source
operations (#15), usable operator/event diagnostics (#16), compatible public
maintenance (#18), installed composed receipt (#19). #17's current-intake REJECT
is settled; future return follows its preserved criteria and separate owner approval.
Missing an implementation solution is not a reason to erase known work.

## Receipt Sequence and Decisions

1. Preserve the integrated R2 proof and its completed review; do not reopen stopped
   experiments or reset any prior remediation budget.
2. Preserve completed/closed #12 and merged PR #23 with accepted thin-layer ADAPT.
   Preserve completed/closed #13 and merged PR #26 with accepted minimum contract;
   Preserve completed/closed #14 and merged PR #31 bounded research; production
   mapping remains separately gated. This does not deploy a product or claim full A/B/C or installed acceptance.
3. Accept producer/consumer semantics and conformance; Router owns adoption, Kernel
   owns reference retention/authority. Then separately select #15 production work.
4. Deliver #16 operator facts and #18 public install/update/migration. Event/history,
   CLI/export consistency, partial update and rollback are receipts, not prose alone.
   #16's owner correction accepts portable independently implemented offline
   conformance before actual Console adoption; never claim deferred live criteria passed.
5. Exercise #19 against frozen installed producer/consumer revisions; distinguish
   source integration, deployment and actually observed scenarios. No inference or
   effectful task occurs without separate permission. #17 rejects current intake;
   reconsideration is separately gated, not mandatory telemetry collection.

The ADAPT outcome for #12 and minimum contract acceptance for #13 are settled;
completed #14 retains agreed ownership without a third scale. Owner-reserved
decisions concern new production mapping, future contested ownership changes and
any future #17 reconsideration after the current-intake REJECT. Paid/service/data,
inference or effect access is separately authorized when a future receipt needs it.
No numerical quality/cost/time threshold is invented here. Routine documentation
findings are remediated by the existing bounded workflow, not escalated as owner
architecture decisions.

The documentation gate is `make check`, full-base scope/whitespace and link/index/
decision consistency inspection, followed by a fresh native whole-PR reviewer that
also reads this matrix and linked issue acceptance. Exact clean HEAD/base and
Forgejo currentness are required. That alignment delivery used the historical
maximum three remediation rounds; current development follows [AGENTS.md](AGENTS.md)
and its issue-delivery review bound. Native APPROVE is distinct from a formal
Forgejo review. Neither means product GO, `READY_FOR_LIVE_TASK` or completion of
these functional gaps; only explicit `/loop` adds verified develop integration.

[alignment]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/11
[abc]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/1
[workflow]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/5
[r2]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/9
[first-pr]: https://forgejo.creatidy.com/Creatidy/model-intelligence/pulls/4
[second-pr]: https://forgejo.creatidy.com/Creatidy/model-intelligence/pulls/8
[value]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/12
[value-pr]: https://forgejo.creatidy.com/Creatidy/model-intelligence/pulls/23
[publication]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/13
[semantics]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/14
[semantics-pr]: https://forgejo.creatidy.com/Creatidy/model-intelligence/pulls/31
[acquisition]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/15
[operator]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/16
[feedback]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/17
[distribution]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/18
[acceptance]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/19
[router]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/173
[kernel]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/46
[allocator]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/11
[harness]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/146
[effort]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/57
[calibration]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/79
[binding]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/107
[tracks]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/126
[router-ux]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/140
[router-tls]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/139
[router-acceptance]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/141
[router-pin]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/174
[router-requirements]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/175
[router-mi]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/176
[router-feedback]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/177
[router-narrowing]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/178
[router-identity]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/179
[router-workspace]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/180
[router-protocol]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/181
[router-cli]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/182
[router-events]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/183
[router-economics]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/184
[kernel-harness]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/47
[kernel-lifetime]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/48
[kernel-intake]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/49
[kernel-isolation]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/50
[kernel-requirements]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/51
[kernel-routing]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/52
[kernel-runtime]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/53
[kernel-review]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/54
[kernel-knowledge]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/55
[kernel-budget]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/56
[kernel-events]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/57
[kernel-outcomes]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/58
[kernel-concurrency]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/59
[kernel-acceptance]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/60
[kernel-cache]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/61
[kernel-migration]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/62
[router-migration]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/185
[router-distribution]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/186
