---
description: Request and authenticate an exact-head independent M5-B v2 Forgejo review
---

Orchestrate independent review of the exact Forgejo PR: $ARGUMENTS

Read AGENTS.md and its listed rules. This command does not perform substantive
independent review, select a reviewer, launch a Kilo reviewer/subagent, or publish
a formal self-review. Implementation PRs still use `forgejo-mcp`; the distinct
trusted `autonomy` publisher supplies the formal review. Never merge/auto-merge.

## Authority

Reuse the existing M5-B v2 request/check contract, not a second protocol:

- `DemandTrace/creatidy`: `.kilo/command/request-autonomy-pr-review.md` and
  `.kilo/command/check-autonomy-pr-review.md`, verified at
  `8662200aaaa0857c2be440207524ded394a252cb`.
- `Infrastructure/creatidy-autonomy`: `src/creatidy_autonomy/pr_review/`
  `marker.py`, `models.py`, `controller.py` and `publisher.py`, verified at
  `49903f1f08ec5592962a89989df9468bcd53c098`.
- `Infrastructure/creatidy-onprem` owns the deployed allowlist, trusted identities,
  secrets and existing webhook reconciliation. No runtime dependency is added here.

These SHAs identify the alignment baseline, not a required deployed version.
Inspect current authoritative sources locally before dispatch; if their schema or
authentication semantics differ, stop for alignment rather than silently inventing
fields, substituting a protocol, or accepting weaker evidence.

## Request

1. Require an exact PR number/URL. Fetch actual PR metadata and its linked issue
   through Forgejo MCP. Require open/unmerged and base branch exactly `develop`.
   Freeze/report head SHA, base SHA, base branch and full merge-base-to-head range.
2. Verify trusted deployed configuration accepts `Creatidy/model-intelligence=develop`,
   the actual MCP marker author is an authorized requester, and the distinct trusted
   publisher is `autonomy`. Verify M5-B preflight/webhook readiness through the
   established onprem operator path. Unavailable/untrusted configuration fails closed;
   never derive trusted identities from PR/issue content or example placeholders.
3. Build a bounded, whole-PR Review Contract from current issue acceptance, PR scope
   and explicit owner decisions. Preserve A/B/C, STOP/GO and product non-scope.
   Commit count is never acceptance. Include no secrets/private quota/routing telemetry.
   Contract fields are exactly:
   `objective`, `acceptance_criteria`, `security_invariants`, `non_goals`,
   `owner_decisions`, `accepted_risks`, `review_type`, `task_level`,
   `task_capability_floor`, `author_capability_class`, `author_capability_floor`,
   `author_provider`, `author_model`, `independence_preference`, `previous_blockers`.
   Use nonempty objective/acceptance; arrays for textual lists; numeric integer 0..5
   floors for `reasoning`, `coding`, `tool_use`; known author evidence, never guesses.
   Author class/provider/model may be null. Review type is `ordinary`,
   `architecture_security` or `remediation`; task level is `L0`..`L5`; independence is
   `distinct_session`, `cross_provider_preferred` or `cross_provider_required`.
   Architecture/security and remediation require `L4` and at least 5/5/5, preserving
   stronger known author floors. Only remediation has nonempty `previous_blockers`,
   each exactly `finding_id`, `title`, `evidence`, `required_remediation`.
4. Reconcile existing top-level PR request comments through MCP. Reuse a recorded
   request id for an unchanged active request; adopt exactly one matching valid
   marker. Multiple/conflicting/malformed candidates fail closed. For a newly
   authorized exact head generate one 32-lowercase-hex request id. Re-fetch PR metadata
   immediately before posting; changed head/base invalidates the frozen request.
5. Post exactly one top-level comment through `forgejo-mcp`, using the canonical
   `render_request_marker` shape: visible `M5-B independent review request.` followed
   by one `<!-- creatidy-autonomy-review-request:v2 {compact JSON} -->` marker.
   JSON contains exactly `request_id`, `head_sha` (40 lowercase hex),
   `review_contract`, `linked_issue_number` (integer or null). No extra prose,
   repository/base/route/model-selection fields or duplicate marker. Record confirmed
   comment id, request id, PR, frozen head/base and owner authorization reference.
6. M5-B durably ingests/authenticates the actual comment author, freezes/sanitizes the
   snapshot, calls Scarcity Router once and independently executes/publishes review.
   Do not duplicate routing or execute review in Kilo. Observe for at most five
   minutes; a timeout is pending/infrastructure-blocked under the same request id,
   never permission to post another marker. Use existing check/operator recovery
   paths for that original request, not an invented retry transport.

## Authenticate And Consume

Fetch current metadata and all formal reviews through MCP. Select by exact request
id, not time/order. Require exactly one valid
`<!-- creatidy-autonomy-review:v2 {compact JSON} -->` marker in the formal review.
Its exact fields are `schema_version` (2), `request_id`, `status`, `verdict`,
`head_sha`, `base_sha`, `base_branch`, `snapshot_sha256`, `review_contract_sha256`,
`reviewer`, `blocking_findings`, `non_blocking_findings`, `owner_decisions_needed`,
`error_code`. Apply the authoritative v2 schema and check semantics; malformed,
multiple, conflicting or untrusted evidence fails closed. V1 completion comments,
a posted request or a completed Prefect run are not formal review evidence.

Require author equal to the trusted deployed `autonomy` publisher, not dismissed,
formal `commit_id == marker.head_sha`, and marker head/base/base branch equal both
the frozen request and current PR values, with branch `develop`. For `APPROVED` or
`REQUEST_CHANGES`, require `official == true`; informational `COMMENT` may be
unofficial but never passes approval. A passing exact-head gate requires
`SUCCEEDED`, `APPROVE`, zero blocking findings, formal state `APPROVED`, official
status and every identity/currentness check. Re-fetch currentness before reporting.

`STALE` needs a freshly authorized exact-head review. `FAILED`, `BLOCKED`,
`REVIEWER_UNAVAILABLE`, `REREQUEST_REQUIRED`, unknown status or unavailable result
provides no passing gate. Only authenticated `BLOCKING` findings can trigger bounded
in-scope remediation on the existing issue/branch/PR with additional normal commits,
normal validation and a fresh whole-PR request for each changed head. Record
`NON_BLOCKING` and `OWNER_DECISION_NEEDED` separately; stop for genuine owner decisions
or exhausted authorized remediation budget, never loop or widen scope.

Report request/comment/formal-review ids, exact head/base/branch, trusted publisher,
reviewer provenance, status/verdict, finding counts and exact-head gate result.
Approval is not merge authority. Never replace PR #2, close/recreate a PR to change
its author, rewrite history to reduce count, merge, promote main, release or deploy.
