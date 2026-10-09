# Offline Read-Only Operator Contract

Working contract `mi.operator-working/1`, MI #16. The owner decision of
2026-10-08T20:23:50Z ([canonical correction][decision]) assigns first definition,
semantics, fixtures and publication to MI. Console requirements from frozen
`6a254921a62b4a81c51dcc2c414692d5c22cf35c:docs/contracts.md:75-99` are inputs,
not a wire schema or a requirement for Console #6/browser implementation first.
Original #16 acceptance remains visible in its issue body with the governing AC
mapping. This contract does not change #13/#15 or #17's REJECT current intake.

## Scope And Operations

One full offline JSON snapshot, UTF-8, closed shapes, no duplicate keys/nonfinite
JSON numbers. The producer owns diagnosis/temporal semantics, not consumer routing.
CLI `status`, `inspect` and `export` are local read operations over the same
validated facts. Effectful command inventory is **empty**. There is no endpoint,
authentication, service, event replay, global cursor, notification, scheduler or
second event store. Reading does not fetch sources, mutate artifacts or refresh
freshness. Local filesystem authority belongs to the invoking operator.

## Envelope

The root has exactly `schema`, `product`, `instance`, `evaluated_at`, `capabilities`,
`publication`, `health`, `facts`, `history`. Product is `model-intelligence`;
instance is an explicit nonempty operator-supplied public namespace, never derived
from private paths/accounts. UTC evaluation time is explicit, not acquisition time.
Capabilities are exactly `reads=[status,inspect,export]`, `commands=[]`, `replay=false`.

Publication has exactly `state`, `reference`, `artifact`, `diagnostics`. State is
`available`, `empty`, `invalid` or `unsupported`. Only available supplies both the
full #13 cut reference and exact UTF-8 artifact string; SHA256 independently binds
those bytes. Frame version1 and payload `/1` or `/2` must be recognizable/complete.
Others supply nulls, constant diagnostic codes, no fabricated snapshot or empty-as-error.

Health has exactly `state`, `sha256`, `data`, `correlation`. State is `valid`,
`missing`, `invalid` or `unsupported`. Valid data is the complete existing
`mi.source-refresh-working/1` object, independently hashed over its canonical JSON.
Health correlation is `matched` only when its active digest equals the separately
validated available cut and adapter/source membership agrees. Otherwise `mismatch`
or `unavailable` is explicit; separate publication/health writes are not an atomic
transaction. Health time/publication time/source freshness remain different.
No arbitrary exception/body values are diagnosed or echoed.

Facts has exactly `latest`, `future`, `stale`, `unknown_freshness`, `notices`,
`uncertain_campaigns`, `conflicts`, `projection`. All except projection are arrays;
latest/future/stale/unknown_freshness are sorted unique namespaced evidence IDs.
Projection is an object with offers/models/surfaces/conflicts from the supplied
cut's explicit effective evaluation. Decimal values are exact strings, time/window
metadata stays explicit. Notices/uncertain campaigns reference public typed
records, conflicts are diagnostic records, not private cancellation or admission. Missing publication yields empty
diagnostic facts but never an available empty cut. Unknown freshness is not fresh;
effective selection alone does not enforce consumer freshness. No universal TTL,
free-price default, authority winner, universal quality or readiness claim.

Concrete nested shapes: facts `notices` and `uncertain_campaigns` are sorted unique
`notice:<id>` and `uncertain:<id>` references to the supplied artifact, not duplicated
wire records. Conflicts are objects with exactly `subject` (array of strings),
`field` (nonempty string), `claim_ids` (sorted unique `statement:<id>` array).
Projection has exactly `offers`, `models`, `surfaces`, `conflicts`; models/surfaces
are sorted unique `statement:<id>` arrays of the corresponding published claim
kind. Projection conflicts use the same conflict shape. Offers have exactly `plan`,
`baselines`, `overrides`, `terms`, `conflicts`: plan is `{plan_id,provider_id,generation}`
nonempty strings; baseline/override arrays are corresponding `statement:<id>`
references; conflicts use the above shape. Terms is `{price,quota,available,rules}`:
price null or `{amount,currency,unit}` exact finite nonnegative decimal string plus
nonempty currency/unit; quota null or `{amount,unit,period}` with the same exact
decimal constraint and nonempty unit/period; available null or boolean, rules null
(unreported) or nonempty-string arrays in their reported tuple order. Rule ordering
and duplicates are inherited evidence, not silently converted to a set; retained
#13/#15 bytes are unchanged. Missing publication still uses all four projection keys with empty
arrays, not a partial object. This is diagnostic producer evaluation, not eligibility.

Health agreement: `data.adapter` must equal payload `applicability.scope`;
the unique `data.sources[].source_id` set must equal payload `applicability.source_ids`;
`data.active` must equal the artifact reference digest. Only all three allow
`correlation=matched`. Health's canonical hash covers exactly its parsed object
with UTF-8 JSON sorted keys, separators comma/colon, non-ASCII unescaped; integer
and boolean types are exact. Valid schema1 health has exactly schema/adapter/
attempted_at/succeeded/diagnostic/phase/active/last_successful_publication_at/
freshness_policy/remediation/sources. Source rows have exactly source_id/reference/
retrieved/revision/bytes_received/diagnostic/remediation, unique nonempty IDs,
nonempty reference, boolean retrieved, nonnegative integer-or-null byte count,
nullable strings for revision/diagnostic/remediation. Attempt time aware ISO,
publication time aware ISO or null; phase retrieval/normalization/publication/complete;
active null or lowercase SHA256; adapter/freshness_policy nonempty strings,
diagnostic/remediation null or strings. Malformed structure is invalid, never matched.

Publication diagnostic allowlist: `retained-publication-invalid-or-unreadable`,
`publication-changed-during-read`, `retained-publication-unsupported` only. Available
and empty have an empty diagnostic array; invalid and unsupported require a
diagnostic. These are classes, never raw error/path/source text. The published
`/1`/`/2` payload root has exactly **five** keys: applicability, observations,
statements, notices, uncertain_campaigns; no sixth field is introduced.

## Checkpoint, Gaps And Consumer State

History has exactly `scope`, `replay`, `checkpoint`, `relation`, `evidence_added`,
`projection_changed`. Scope is `retained-publication-cuts-only`, replay is false.
Checkpoint is null or a previous **cut digest**, not an event offset/global cursor.
Relation is `initial`, `same`, `extension`, `gap` or `unavailable`. Extension is
claimed only after reading/validating that retained cut, identical applicability
and full evidence-history preservation against the active cut. Endpoint changes
are not reconstructed causes. Evidence additions are sorted namespaced IDs;
projection_changed is null when unavailable, otherwise a boolean endpoint change.
That endpoint comparison evaluates both retained cuts at this snapshot's explicit
evaluation time, as #9's `projection_delta` does. It is not a comparison against a
receiver's earlier evaluation time: time-only expiry can change the displayed
projection without new evidence or a reconstructed cause. The consumer validates
indicator type/history context but does not recalculate producer temporal semantics.
Only declared retained cuts are available history; missing checkpoint explicitly
gaps. No lossless acquisition-attempt/transport timeline or retention duration is
promised. Corrupt checkpoint yields gap, not heuristic ordering.
History additions cover all published member families: observations, statements,
notices and uncertain campaigns. Observation acquisition-time-only updates are
permitted by #13/#15 history; semantic/source-revision/freshness fields remain exact.
Embedded lineage requires matching kind/comparable subject and value dimension,
nondecreasing effective boundary and valid campaign period/withdrawal invariants,
independently from its byte hash. Projection change covers both before/after sides
and diagnostic conflicts, including the first effective model or surface assertion.
Daily windows independently require a valid named timezone and distinct naive
wall-time endpoints. Malformed retained/checkpoint windows diagnose invalid/gap,
never traceback or overwrite accepted state, including explicit resync.
Aware timestamps whose UTC normalization is outside the datetime range are rejected
at CLI input policy and diagnosed as invalid publication/health or checkpoint gap
at stored-data boundaries; the untrusted timestamp is never echoed in a traceback.
Notice replacement also preserves source ownership and targets. Uncertain campaign
terms must declare a field and keep at least one boundary unknown; both-known bounds
belong to a bounded override, not an uncertain record. These checks are independent
of producer validators and do not reinterpret or reorder retained evidence.

An independently implemented portable receiver validates the entire envelope,
hashes, versions and references without importing producer validators. Exact
duplicate snapshot bytes are a duplicate, not another history item. With retained
state, a new snapshot must cite the receiver's accepted cut checkpoint and report
same/extension; unrelated/reordered/unknown checkpoints preserve last-known state
and require explicit full-snapshot resync. Resync can accept a new validated full
snapshot while marking history unavailable; it does not fill a gap. No automatic
cross-instance merge, producer-version reinterpretation or effectful delegation.
Malformed/unsupported snapshots retain prior accepted state.

## Receipt Boundaries

Portable conformance is stronger than producer self-round-trip, but is explicitly
not actual Console adoption, browser authorization, transport security, installed
integration, authentication or product acceptance. Those remain separate owners'
gates. Console owns presentation/adoption/compatibility feedback, not MI state.
Legacy publication formats are inspected by declared version, not converted by
guessing. Unsupported operator/health/configuration versions reject or diagnose;
old immutable cuts remain unchanged. Installed packaging is not installed Console.

[decision]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/16#issuecomment-15780
