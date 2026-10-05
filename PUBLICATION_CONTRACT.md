# Publication Framing Candidate

## Status and Boundaries

This is the bounded [issue #13][issue] artifact/conformance work after the accepted
thin-layer ADAPT outcome in closed #12/merged PR #23. The owner accepted framing and
immutable reference mechanics as the working baseline on 2026-10-05 ([receipt][working]).
The expanded payload, source-critical semantics and versioned utilization/envelope
binding were then accepted as the minimum coordinated contract ([acceptance][accepted]).
Neither decision approves a permanent public wire ABI, production publisher,
private admission/cancellation, installed MI-Router acceptance, release or product GO.
All #13 criteria and downstream gates remain; incompatibilities require revision.

Issue #13 is completed/closed through [merged PR #26][delivery]. The [completion
receipt][completion] records exact independent approval, integrated acceptance and
conformance evidence. Remaining production/adoption/installed work stays in the
backlog; this does not grant product GO or permanent schema/ABI status.

The candidate uses original standard-library code and owned synthetic fixtures.
No upstream code/data/fixtures, private accounts, calibration ratings or consumer
product functions are copied or implemented. No source acquisition, service, CLI,
daemon, database, broker, signatures or PKI is added. #15/#18/#19 remain separate.

## Reused Evidence and Consumer Seams

MI R2 at `a8df6c4f3773e6bfa7644b3f5ce49128c3401c0e` supplies immutable `Evidence`,
explicit comparable lineage, `knowledge`, `effective_at`, `evidence_delta` and
`projection_delta`. None of those APIs or temporal semantics changes here.
`knowledge(evidence, T)` classifies the supplied cut, not historical acquisition
at T. `effective_at` does not perform freshness admission. An observation with
no `fresh_until` has unknown freshness, not a positive fresh guarantee.

Read-only actual consumer inspection used exact committed sources, not dirty
working files or an installed execution:

| Consumer | Frozen source | Actual mechanism and limit |
| --- | --- | --- |
| [Router #176][router] | `6c337a400b4cdc28ded543d2ae8ccf3749d79cb7` | `selection_types.py:958-1004` validates four-field `EvidenceRef`; `selector.py:1515-1758` serializes `SelectionDecision` without an MI reference/extension slot. `selection_app.py` is not imported: it probes artifact paths. These are not MI adoption or a complete utilized-reference digest. |
| Router calibration | Same committed pin | `CapabilityAssessment` requires reviewed evidence/confidence/date/rationale for ratings; unknown assessments cannot carry partial provenance. Raw MI uncertainty must not be forced into that calibration shape. Derived inventory projections can retain base catalog version/date, so those alone are not a complete utilized cut. |
| [Kernel #55][kernel] | `5048c5cef95e546377d5e20baeae16b99b1bd088` | `core/context.py` sources/digests, `ports/allocation.py` original allocation/context hash checks, `ports/application.py` preparation/restart, `adapters/sqlite_store.py:691-766` content-addressed immutable artifacts. These retain references but do not implement MI reference validation. |

The generic strict-parsing/integrity guarantees are independently implemented here,
not copied from these sources. Existing consumer private policy and calibrated
bootstrap remain untouched. Kernel normally receives utilized references through
Router decision provenance, without a mandatory live connection to MI.

## Candidate Frame and Reference

`encode_cut` produces UTF-8 JSON bytes. The exact supported frame has these seven
fields, no permissive extra fields:

| Field | Meaning |
| --- | --- |
| `format_version` | Integer `1`; distinct from the payload's semantic version and producer release. |
| `payload_schema` | Explicit separately registered payload grammar identifier. No unknown grammar is silently admitted. |
| `produced_at` | Time-aware UTC publication metadata, not claim effective time, source publication time or proof of freshness. |
| `scope` | Declared public interpretation scope; not ecosystem completeness, account applicability or a private task. |
| `members` | Unique explicit identities in this frozen cut, including retained historical membership. The payload validator must verify these against the actual content. |
| `sources` | Source ID, reference and supplied revision, including explicit unknown revision `null`. Pins identify evidence, not physical runtime or authority. |
| `payload` | Original UTF-8 JSON-object text carried in a JSON string. The reader returns those exact bytes to the registered payload validator, without number or whitespace normalization. No Python deserialization, executable instructions or automatic calibration. |

The external reference is `(format_version, payload_schema, SHA-256(exact bytes))`.
Readers require an independently supplied expected reference and supported payload
allowlist. A digest inside the same untrusted artifact cannot authenticate a
publisher. Local pinned references suffice for this offline integrity proof;
future release trust and distribution remain separately accepted scope.

## Working Public Payload

`mi.public-evidence-working/1` is a candidate grammar, not a permanent ABI or a
serialization of Python class names. `contract.py` names explicit JSON fields and
validates closed shapes throughout:

| Root | Contents and checked meaning |
| --- | --- |
| `applicability` | Scope ID, declared source roster, public channel and native configuration. `null` channel/configuration or parameter is unknown, never a wildcard. Known effort string `none` remains distinct from unknown/unconfigured. Scope/roster changes require consumer review. |
| `observations` | ID/source/authority/type/reference/revision, rights metadata and separate acquisition/observation/publication/freshness instants. Declared sources must be covered, revisions must cover every observation, and frame pins must match. No fixed TTL, authority winner or license grant inferred. |
| `statements` | Explicit subject and tagged model capability/benchmark/price, plan baseline/campaign, and surface assertions; source ID linkage, effective time and supplied comparable replacement. All current R2 families round-trip; decimal values have native unit/currency/method/configuration context and are not calibrated ratings. |
| `notices` | Attributed source revocation/retraction, affected member IDs, effective time, reported criticality (`true`/`false`/unknown) and explicit lineage. No synthetic admission/cancellation or producer-issued authority. |
| `uncertain_campaigns` | Retained reported terms and unknown start/end boundaries with source/context/conditions. They do not construct an invented R2 `Period` or an active discount; consumer-required uncertainty remains visible. |

Membership covers observations/statements/notices/uncertain annotations, not just
current effective values. Source-roster, history, nested field and identity failures
reject before activation. A producer cannot self-shrink a registered consumer scope
and call it compatible. Completeness means this explicit supplied scope, not all
ecosystem sources or a claim that every source was freshly fetched. Retained stale
records are complete-but-stale, never fresh merely because publication occurred.
Source metadata and public factual citations do not create a generalized legal gate;
actual copied/distributed payload rights are separately required when applicable.

R2 `Evidence`, temporal evaluation and deltas remain unchanged. Supplementary source
notices and uncertain campaigns are separate from that proof's payload classes.
Unsupported fields/kinds reject; this work does not invent numeric-limit/calibration
mapping belonging to #14 or promise active prices from unknown interval bounds.

Serialization sorts producer keys/membership/source references; it makes repeated
owned inputs deterministic, not a claim of a general cross-language canonical JSON
standard. Consumers hash received bytes before parsing, not their own reserialization.
The verified reference remains tied to the received artifact; the payload validator
receives the original payload bytes. Syntax validation parses fractional numbers
with exact Decimal handling and never serializes the parsed payload. Large or tiny
decimal values are preserved or explicitly rejected, never rounded through floats.
Earlier unmerged proposal frames with an object-valued payload are rejected; no
production consumer or approved wire ABI is migrated or given compatibility code.

`decode_cut` checks caller-chosen positive byte bounds, format/payload versions,
expected digest, strict UTF-8 JSON, duplicate keys/nonfinite values, closed frame
and source shapes, identity uniqueness and timezone-aware publication metadata.
It validates framing, **not** completeness or truth of an opaque payload. A producer
must validate the registered payload and declared cut before publishing; a consumer
must validate it before activation. No self-reported `complete=true` is treated as
proof. A declared empty cut means no supplied evidence, never withdrawal or free use.

## Frozen Input and Evaluation

A utilized reference retains the exact cut reference and evaluation instant plus
the applicable input context. The owned fixture uses a public synthetic client
condition; private inventory/account/calibration/admission inputs remain local to
Router/Kernel. MI does not receive them or own final new-use admission.

The actual `EvidenceRef` has `source`, `identifier`, optional `version` and optional
calendar `date`; it rejects extra keys and nested identifiers. A date is not an
evaluation instant. Actual `SelectionDecision.to_dict` rounds its timestamp to
milliseconds and has no metadata/provenance/evidence-reference extension field.
Catalog version/date and a selected identity cannot reconstruct a utilized MI cut.

`utilization.py` therefore binds a separate working utilization artifact: full cut
reference (or explicit unknown), exact UTC evaluation instant, hash of the exact
caller-retained decision bytes and context bytes. Its reference fits the inspected
EvidenceRef shape with a digest URI/version and no calendar date. The manifest and
any private context stay local to the consumer/Kernel, not a public MI feed. One
microsecond changes this reference even when Router's decision timestamp is equal.

The owned fixtures propose a `mi_utilization` reference beside `decision` in the
machine envelope, never extra fields inside the closed EvidenceRef or actual
decision. The pinned Kernel parser preserves that extra envelope member in its
opaque provenance, and allocation encoding preserves it. The minimum versioned
binding/envelope contract is accepted, but that permissive behavior is not installed
Router emission: Router at this pin does not emit it or validate the manifest.
Future #176/Kernel delivery must implement the accepted relationship and preserve
remaining admission, compatibility and installed-acceptance gates.

### Decision-Path Receipt

A consumer freezes the admitted cut bytes/reference and evaluation context BEFORE
invoking its evaluator. It emits the utilization manifest from those frozen inputs
and the evaluator's actual returned decision, never samples the latest cut after
the decision was created, and retains the envelope's MI reference with that same
decision. Evaluation context includes public conditions, applicable configuration,
requirement and local catalog/policy versions, separately from Kernel's resolved
input-list bytes; a context hash is not an admission policy or privacy guarantee.

`decode_decision_utilization` verifies the reference is present on that retained
decision envelope, checks the decision against exact retained decision bytes and
validates cut/time/evaluation-context hashes. A context-only link without the
decision-path reference rejects. Hashing primitives alone cannot attest arbitrary
consumer code behavior: the consumer adapter must implement this capture/evaluate/
emit path, and conformance must inspect and exercise it.

The owned fixture consumes the frozen public projection in its emitted decision's
display metadata while retaining a caller-preselected, pre-authorized identity;
it implements no selection/ranking/admission policy. The exact pinned Router
CandidateEvaluation/SelectionDecision constructors serialize that public input.
Changing the source value or applicable condition changes the actual emitted DTO
and utilization reference. A refresh within that callback cannot relabel the old
decision with the new cut. This is executable decision-path data-use conformance,
not evidence that current installed Router routing uses MI or that a callback can
be universally trusted without consumer review.

Two cuts at the same effective time can differ because a past-effective claim was
learned later. Replay uses the retained old cut, not today's store, so it cannot
invent historical acquisition lineage. An evidence addition may change reference
without changing an effective value; an expiry can change projection with no new
evidence. Retrieval-only changes never renew `fresh_until` or infer lineage.

## Semantic Dispositions

| Fact or diagnostic | Required distinction |
| --- | --- |
| Known / unknown value | Null is unknown, not false, zero, free or full; availability and evidence absence are separate. |
| Unknown freshness / stale | Missing freshness metadata is unknown; an explicit expired freshness boundary is stale. Stale is not a negated fact. Consumers choose admission, without a global arbitrary TTL here. |
| Conflict | Preserve comparable disagreeing claims and participants. No authority, source recency, retrieval time or lexical winner. Different economic bases are not automatically comparable. |
| Correction / future revision | Supplied links and effective boundary control replacement; source retrieval or equal values cannot infer correction. Known future evidence can be retained before becoming effective. |
| Expiry / withdrawal / disappearance | A bounded campaign expires at its supplied boundary offline; an explicit withdrawal references its predecessor. Missing rows or refresh failure do not erase history or withdraw facts. |
| Critical revocation | A source-reported critical assertion with targets, provenance and effective time, distinct from an ordinary source revocation, campaign withdrawal, stale price or parser failure. Unknown reported criticality is not false. Explicit same-source/target retraction preserves the original notice. Source assertion is not MI-issued admission denial or cancellation authority; consumer/Kernel policy owns effects. |

Known future notices stay inactive until their effective boundary. Explicit notice
lineage must retain comparable targets/source and monotone time, with no cycles or
inferred replacement. Independent or sibling notices remain visible: there is no
lexical/recency winner. Source freshness and reported criticality are orthogonal;
an expired freshness deadline cannot erase a critical report or turn it into a
missing price. Public views retain diagnostics; they do not resolve private policy.

Uncertain campaign ends remain uncertain annotations in this minimum contract,
not fabricated `Period` values or silent R2 changes. #14 coordinates actual
subject/channel/configuration/native-unit/assertion and mapping vocabulary; this
framing does not create another ontology or scale or block parallel #14 research.

## Executable Conformance and Its Limits

`tests/test_publication_contract.py` is a synthetic producer plus independently
authored local consumer fixture. Its offer-only `synthetic-r2-offers/1` codec is
explicitly NOT a permanent public payload or Router implementation. It fixes owned
provenance categories and includes a synthetic plan/serving/configuration scope,
observation acquisition/publication/freshness, claim effective intervals, native
money/quota units, public conditions and retained lineage. Unsupported fixture
features are rejected rather than projected or treated as compatible. Each fixture
record has a closed required shape, including observations, claim entries/values,
subjects, terms, money, quota and periods; unknown or missing nested fields cannot
be discarded before reconstruction or activation.

The fixture validates membership/source association and R2 invariants before one
admitted-reference assignment. Forward updates reject identity rewriting/history
loss; rollback explicitly reuses retained bytes, never makes old evidence fresh.
Malformed, incompatible, missing-member, corrupted, interrupted and oversized cuts
leave the previous artifact untouched. Pinned synthetic evaluations retain their
old immutable bytes through refresh failure or later adoption. This proves the
local reference mechanism, not actual Router/Kernel lifecycle behavior.

The proof also exercises unknown/stale price, conflict, future withdrawal, offline
expiry, two evidence cuts at one evaluation time, acquisition-only reference change
and separate evidence/projection deltas. Existing R2 tests cover daily windows and
other fact families. This original framing proof is not the sole conformance receipt.

`tests/test_router_conformance.py` adds original Router-shaped references and
SelectionDecision output, the working public payload, scoped source notices and
Kernel-shaped versioned allocation/original-input traces. Its caller-owned decision
callback consumes captured public inputs, without implementing selection/admission.
Its accepted-input receipt is retained instead of attaching a current cut post-hoc. Interrupted updates,
later evidence and critical reports do not rewrite retained cut/utilization/decision/
allocation/context bytes. Context fixtures use the actual empty resolved-input-list
shape; intent carries AttemptSpec digest, allocation/context references use `sha256:`.

`tests/verify_router_consumers.py` separately executes only inspected pure parsers,
constructors and serializers at the exact pins above. Git blob identity is checked
for all archived package files before import; sources are read-only, bytecode is
disabled, environment is empty/allowlisted, explicit source/runtime read roots and network/subprocess/write audit guards
apply after source verification. No selector, allocator, runtime, journal/database,
application advancement or provider operation is invoked. No foreign code/fixture
is vendored or made a product dependency; temporary exports retain LICENSE/NOTICE.

Supplemental reproduction after exporting the exact package objects with `git archive`
and retaining the licenses (no checkout of dirty sibling files):

```bash
env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp/kilo/mi13-check-home \
  PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -I -S -B tests/verify_router_consumers.py \
  <router-archive> <router-object-repo> <kernel-archive> <kernel-object-repo>
```

Use a deliberately synthetic writable HOME outside source trees. The script checks
the full archived package's Git blob IDs at the pins above before import. It requires
read-only Git access to those objects, not installed package dependencies. It is
supplemental to required `make check`, not a skip or substitute for that gate.

It checks owned results against actual EvidenceRef and SelectionDecision types,
Kernel response validation/canonical provenance/allocation encode-decode and
AttemptSpec reference/digest shapes, including known `none` versus unconfigured
`null`. Actual-shaped retained input bytes remain unchanged under MI failure.
This is exact-pin offline code conformance, not an installed consumer or execution
receipt. Its output explicitly marks installed acceptance and Router emission of
the proposed MI extension false. Green tests do not authorize critical-event policy.

## Acceptance, Migration and Operator Guidance

Before a new-use consumer activates a candidate: independently obtain the expected
reference, enforce its supported versions/bounds, validate the entire payload and
declared scope/history, then apply its local freshness/admission policy. Reject
with explicit diagnostics and retain old bytes/reference on failure. That old cut
is not automatically admissible for new use. An already pinned synthetic use keeps
its original reference solely across refresh failure; critical events are separate.

Persist reference/version and original bytes. Unsupported frame or payload changes
are rejected, not guessed migrations; explicit translators must preserve original
bytes/unknowns and be separately reviewed. Rollback chooses a retained version and
rechecks new-use policy. Do not remove Router bootstrap/catalog overrides before
producer-consumer parity and replacement acceptance. Preserve source provenance
and rights of any actual distributed payload; the owned synthetic codec needs no
third-party dataset copying and does not grant permission for future copies.

The expanded minimum producer-consumer contract is accepted. This does not grant
permanent schema/ABI status, publisher authenticity, private admission/cancellation,
product GO or installed behavior. Compatibility/migration and downstream gates
remain. Completion still requires all #13 conformance criteria and fresh independent
exact-candidate review, including the verifiable actual-use relationship; neither
the earlier MI-local offer fixture nor context-only provenance can replace it.

[issue]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/13
[router]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/176
[kernel]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/55
[working]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/13#issuecomment-14882
[accepted]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/13#issuecomment-15114
[delivery]: https://forgejo.creatidy.com/Creatidy/model-intelligence/pulls/26
[completion]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/13#issuecomment-15216
