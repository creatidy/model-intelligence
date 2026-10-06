# Optional Operational Evidence Decision Packet

Research revision 2, 2026-10-06, selected [MI #17][issue].
**Owner decision: REJECT current operational intake.** Adrian supplied this explicit
decision on 2026-10-06T14:23:48Z; [canonical transcription][decision] records the
instruction, rationale and reconsideration gates. Revision 1's pending decision
and initial review remain in Git/issue history; the delivery and review counter
continue, not restart.
This is an assessment and synthetic examples, not an intake API, consent/redaction
implementation, new wire format, privacy certification or collection permission.
No private records were inspected or exported. No new representation or dependency
is proposed: reuse origin-local evidence before any separately accepted optional
contract. MI remains public/shared evidence; Kernel/Router retain local outcomes,
analysis, consent enforcement, task meaning, calibration, economics and routing.

## Owner Decision And Rationale

**REJECT current operational intake.** Do not implement a Model Intelligence
receiver, private operational-data collection path, production sharing format,
automatic calibration, or centralized ingestion of existing Kernel/Router private
outcome exports/audits. Keep core operation independent of optional sharing.

The governing owner rationale is:

- MI's core public-evidence role does not currently require private operational intake.
- No material incremental product benefit has been demonstrated over public-source
  evidence, reproducible public/synthetic cases and origin-local analysis.
- Task outcomes are materially confounded by workload, prompt, harness, reviewer,
  retries/remediation, selection policy and incomplete cost/usage coverage.
- Centralizing these records would add privacy/linkage/lifecycle obligations without
  a demonstrated need.

Public/synthetic, independently reproducible ecosystem corrections can instead be
considered under the existing public-source boundary and actual source rights;
this does not authorize a new receiver or bypass #15's production contract gate.

This explicit decision supplies #17 AC5's owner outcome, not an unexplained DEFER
or a decision inferred from loop authority, review or Git authorship. It is not
a permanent prohibition on future opt-in sharing. Reconsideration retains all
criteria below and requires separate owner approval before implementation.
Closure follows required validation, fresh exact-HEAD independent review and
verified integration. Neither the decision nor closure grants product GO, private
sharing, installed acceptance or implementation authority for #15/#16/#18/#19
without their own gates. No collection implementation task is selected or registered.

## Actual Local Evidence And Reuse

Fresh canonical source cuts inspected read-only on 2026-10-06:
Kernel `9dfa20931a46931d1e97d1f0efddcf2692afb7a7`,
Router `1dae1948f372e0f1739896655bb7db97d6b08460`.
Kernel paths below are under `src/creatidy_kernel/`; Router paths under
`scarcity_router/`. Inspected tests are source evidence, not executed foreign tests.

| Existing artifact | Useful origin-local behavior | Why not a public feed |
| --- | --- | --- |
| Kernel `core/outcomes.py:22-264`, `creatidy-local-outcomes-v1` | Attempt/spec/allocation/context identities, requested/resolved/observed identity, unknown usage, explicit receipt corrections and remediation ancestry. | No application call site at this cut. Duplicate observations/receipts are rejected; correction order matters, not an idempotent arbitrary-order importer. Remediation ancestors are not every solver/reviewer/helper expense. Strings can contain private content. |
| Kernel `adapters/reference.py:332-411` | Durable identity, verification/rejection records, cancellations, explicit unavailable token usage and historical PR receipts. | Full private subjects/references; not complete cost capture or current remote PR state. Unknown observed identity stays unknown. |
| Kernel `adapters/task_execution.py:1121-1165`, `ports/application.py:305-354` | Thin task/Attempt/operation/allocation/candidate/acceptance export; richer verification manifests retained locally. | Thin export omits full observed identity, consumption, checks/remediation/cancellation journey. Neither missing exported fields nor stored manifests prove an agreed sharing contract. |
| Kernel `core/execution.py:128-191`, `core/verification.py:2-5,120-196,248-304` | Candidate/Accepted/Rejected results, exact subject/provenance and independence/freshness checks. | Binding validation does not prove evidence truth. PASS/APPROVE is conditional on task/spec/check/reviewer, not universal quality or entitlement. No invented `WorkResult` type. |
| Router `gateway_audit.py:78-286`, `control_api.py:254-290`, `server_store.py:599-640` | Actual `AuditRecord`: request/client/decision/profile/resource/adapter/time, dispatch identity and call usage. Both memory trail and durable SQLite sink exist. | Request completion is not task acceptance; dispatch can identify only a plan-managed lane. Retention permits gaps; append is not correction-aware dedup. Stable identities/times/rare configurations can identify private activity. |
| Router `gateway_contracts.py:202-303`, `gateway_coordinator.py:2122-2157` | Reported/estimated/unavailable call quantities remain distinct. | Totals sum available facts without a missing-call coverage flag. Not a whole-task ledger, private quota attribution, exclusive pool spend or hidden-helper accounting. |

Actual counterparts are [Kernel #58][kernel] (producer) and [Router #177][router]
(authorized local consumer; comment 14349 corrects the registration-time missing
producer). Their planned whole-journey/correlation acceptance is not delivered
behavior at these pins. Completion is unnecessary for this assessment, but actual
bytes/conformance and completeness are required before stronger intake claims.
No foreign producer, importer, cost collector or consent machinery is implemented
in MI. #13 publication and completed #14 research are not optional outcome formats.

Both exact-pin source licenses are Apache-2.0; Kernel has a NOTICE. These concern
code, not rights to disclose user/provider/task records. No foreign code, fixtures,
data, library or telemetry backend is copied/adopted here. Public availability,
code licenses, local authorization and a redaction-policy digest do not authorize
redistribution. `core/context.py:17-92` retains selected content; history export at
`adapters/sqlite_store.py:882-908` includes actors and command/fact snapshots.

## Minimum Benefit And Measurement

Best candidate: a public/synthetic reproduction of one interface incompatibility
or contradicted support assertion. Necessary evidence is public adapter/build,
provider/channel/model or explicit unknown, relevant configuration, public inputs,
observed behavior, date/method/provenance and source-specific rights. It raises an
ecosystem hypothesis until independently reproduced; no private journey is needed.

Private outcome counts/latency/cost/pass rates have no demonstrated incremental MI
benefit over origin-local analysis and public reproduction. Comparisons require
the original declared workload, prompts/configuration, harness/version, verification
criteria/reviewer, retries/remediation/owner intervention, selection mechanism,
denominators, coverage and metric/unit/basis. MI must not classify private tasks to
invent those fields. If minimization removes necessary comparison context, withhold
the comparison; do not fill it with universal ratings, zeros or inferred identity.
Token rate is not full accepted-result cost or subscription quota consumption.

Original toy example, not benchmark data or a model scale: within two controlled
public/synthetic settings A has rates 4/5 and 19/20, B has 7/10 and 9/10. A wins in
each setting, but A's 9:1 mixture gives 163/200 while B's 1:9 gives 22/25. Comparing
those aggregates reverses the apparent ordering. This illustrates confounding, not
causal inference, calibration or empirical utility. [The Benchmark Lottery][lottery],
arXiv:2107.07002v1 (14 July 2021), abstract, separately reports that task choice can
change apparent relative performance; its experiments were not reproduced here.
Citation only: no paper dataset/code or redistribution-license assumption.

## Threats, Consent And Lifecycle

[RFC 6973][privacy], July 2013, Informational, provides analytical questions, not
certification or a prescribed balancing formula. Sections 5.2.1-5.2.5 cover
correlation, identification, secondary use, disclosure and exclusion; 6.1 covers
collection/use/disclosure/storage minimization; 6.1.1-6.1.2 make anonymity
observer-relative and distinguish pseudonyms; 6.2 and 7.2 cover user participation;
6.3 and 7.3 cover security; 7.1 and 7.4 address retention and protective defaults.
Persistent hashes, exact timing, rare configuration/usage combinations and external
public information can enable linkage. Removing prompts or hashing IDs is not
anonymization. Our owned dictionary example demonstrates one possible hash link,
not general hash reversibility and not a privacy guarantee. Aggregation/small-cell thresholds
and differential privacy are not adopted or asserted sufficient here.

Future consent must be voluntary, explicit at origin, attributable and destination,
purpose, field scope and time specific, including permitted secondary use. No opt-in
by silence, reused local approval or inferred consent from a successful task.
Denial/absence/expiry/withdrawal cannot degrade basic operation. Withdrawal must stop
future exports; already received copies, onward sharing, derived records and backups
need a separately enforceable lifecycle. Do not promise deletion merely from local
retention or consent expiry. Specify minimization, access, retention/deletion and
withdrawal receipts before adoption; no arbitrary TTL or anonymity threshold.

Diagnostics must be fixed classes without echoing input values, IDs, paths or
tokens. Consent alone does not cure unsafe content, uncertain provenance, source
restrictions, misleading comparisons or unapproved receiving authority. There is
no secret scanner/redactor/intake validator in this research packet.

RFC copyright is IETF Trust/authors, subject to BCP 78/publication-date legal
provisions. This is citation-only analysis, not code/format copying or adoption;
incorporated reuse terms were not independently verified. No GDPR/compliance claim.

## Synthetic Decision Examples

These original policy examples specify expected behavior for a future separately
agreed path; they are not accepted transport fields or executed privacy enforcement.
Today all operational sharing remains disabled, including the positive proposal.
Only current MI public-artifact independence, mathematical confounding and the
owned hash example are executable in `tests/test_operational_sharing_review.py`.

| Case | Owned synthetic condition | Expected diagnostic / disposition |
| --- | --- | --- |
| EX01 | Local public-evidence operation, sharing consent absent. | `LOCAL_ONLY` |
| EX02 | Named destination/purpose, scoped active consent, allowed public/synthetic reproduction, known provenance/rights; hypothetical recipient/lifecycle approved. | `PROPOSAL_ONLY` |
| EX03 | Consent absent or implied by PASS. | `CONSENT_ABSENT` |
| EX04 | Consent expires at evaluation; no future sharing. | `CONSENT_EXPIRED` |
| EX05 | Consent withdrawn; retain local operation, no promise of recipient-copy deletion. | `CONSENT_WITHDRAWN` |
| EX06 | Valid consent for a different destination, purpose, field scope or secondary use. | `CONSENT_SCOPE_MISMATCH` |
| EX07 | Unexplained/misbound source, identity, correction link, units or history coverage. Explicit model unknown may remain a scoped unknown, never a fabricated comparison. | `PROVENANCE_UNKNOWN` |
| EX08 | Free text contains owned fake `SECRET-MARKER` or `/owned-private/project`; prompt removed but stable IDs/time remain. | `PRIVATE_CONTENT_OR_LINKAGE` |
| EX09 | Different workload/harness/prompt/reviewer/selection mixtures or partial costs are compared as universal quality. | `COMPARISON_UNSUPPORTED` |
| EX10 | Unsupported future format, restricted-source evidence or no agreed retention/withdrawal receipts. | `CONTRACT_OR_RIGHTS_UNACCEPTED` |

## Reconsideration And Compatibility

The owner preserves this path; future return is not approved now. It requires:

- A specific named public-evidence/product problem.
- Demonstrated improvement over public sources/reproduction and origin-local analysis.
- Evidence that the proposed shared fields are necessary.
- Explicit producer/consumer contract and lifecycle.
- Voluntary scoped consent where private records are involved.
- Source/user rights and negative conformance.
- Separate owner approval before implementation.

A conditional return requires a named public user problem and measured improvement
over public sources/reproduction plus origin-local analysis: record the prevented
incorrect public assertion/compatibility conclusion, curation effort and maintenance
cost under the same declared acceptance case. Establish necessity of each proposed
field and why safer public reproduction cannot supply it. Synthetic consistency
alone does not establish benefit; no numerical utility/privacy threshold is invented.

Also require actual version-pinned origin export/consumer agreement, honest whole-
journey/correction/unknown coverage, voluntary scoped consent and negative conformance,
recipient retention/withdrawal/secondary-use enforcement and source/user rights.
Publish a privacy threat assessment for auxiliary information/linkage, not just
field-name checks. Owner approves purpose and measurable criteria before separately
selecting implementation; no new implementation issue is registered here.

If a future optional format is adopted, define explicit versions and migration or
rejection, preserve original receipts/corrections/unknowns, distinguish export order
from idempotent import and detect incomplete history. Current local exports are
not an MI wire API; no backwards compatibility bridge or second outcomes framework
is built. Transport hashes prove integrity, not truth, consent or anonymity.

[issue]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/17
[decision]: https://forgejo.creatidy.com/Creatidy/model-intelligence/issues/17#issuecomment-15400
[kernel]: https://forgejo.creatidy.com/Creatidy/creatidy-kernel/issues/58
[router]: https://forgejo.creatidy.com/BioMedical-IT/scarcity-router/issues/177
[privacy]: https://www.rfc-editor.org/rfc/rfc6973.html
[lottery]: https://arxiv.org/abs/2107.07002v1
