# Publication Framing Candidate

## Status and Boundaries

This is the bounded [issue #13][issue] artifact/conformance proposal after the
accepted thin-layer ADAPT outcome in closed #12/merged PR #23. It is not an approved
cross-product wire contract, a production publisher, installed Router consumption,
Kernel acceptance or product GO. Producer/consumer acceptance is explicitly reserved
by #13; executable local conformance does not invent that agreement.

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
| [Router #176][router] | `6c337a400b4cdc28ded543d2ae8ccf3749d79cb7` | `selection_app.py:107-151` strict JSON loading; `selection_types.py:244-274` closed shapes, `958-1004` evidence references, `1458-1523` catalog version/date; `selector.py:1515-1555` decision metadata. These are not MI adoption or a complete utilized-reference digest. |
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
| Critical revocation | Not synonymous with campaign withdrawal, stale price or parser failure. R2 has no general criticality classifier. Classification/authority and effects on new use or active Attempts require the relevant producer/consumer acceptance; no cancellation policy is invented by the frame. |

Uncertain campaign ends remain uncertain annotations in a future approved payload,
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
other fact families. They do not prove an agreed production mapping or critical
revocation policy; those receipts are not claimed by green tests.

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

Owner acceptance outstanding under #13 is the precise public framing/reference/
completeness/compatibility contract and associated payload/admission boundaries,
not permission to choose ordinary JSON, hashing or test mechanics. Criticality,
publisher authenticity, consumer migration and installed behavior are not silently
settled. This proposal plus executable local proof is evidence for that agreement,
not authority to invent it or close #13 as completed.

[issue]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/13
[router]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/176
[kernel]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/55
