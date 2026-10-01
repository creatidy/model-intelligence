---
description: Independently review an exact Forgejo PR snapshot in a fresh interactive context
---

Review the exact Forgejo PR: $ARGUMENTS

Run in a fresh Kilo session/context distinct from the implementation session.
Implementation self-review does not satisfy independent review. A different
model/provider may be used when useful; no specific provider or routing
infrastructure is required. Do not automatically launch a reviewer subtask.

1. Require an exact PR number/URL. Fetch actual PR metadata and the linked issue
   through `forgejo-mcp`; if acceptance context is missing, report that limitation
   rather than inventing requirements. Require an open, unmerged PR to `develop`.
   Freeze and report exact HEAD SHA, base SHA, base branch and merge-base-to-HEAD
   diff boundary. Fetch the exact Git objects through normal canonical Git transport.
2. Read repository `AGENTS.md` and its applicable rules at the frozen snapshot.
   Inspect the entire current PR and full diff, not only the latest commit, along
   with relevant source/tests and the issue's scope and acceptance criteria.
   Verify claimed evidence; assess correctness, regressions, missing tests,
   architecture, security/privacy and provenance/licenses when relevant. Preserve
   the M0 A/B/C and STOP/GO contract; commit count is not acceptance.
3. Operate read-only. Never edit, format, fix, commit, push or modify the reviewed
   branch. Use a separate detached review worktree at frozen HEAD when local
   inspection/checks need a checkout; preserve existing changes/worktrees. Run
   only safe non-mutating local checks when useful, with generated artifacts kept
   local/ignored in that separate checkout. Do not run untrusted code as a trusted
   action, access private credentials, or mutate external services.
4. Return severity-ordered actionable findings with concrete file/line evidence
   and consequences. State explicitly if none. Report acceptance coverage, exact
   frozen HEAD/base, executed checks/results, testing gaps and limitations;
   distinguish reproduced evidence from unverified claims.
5. Re-fetch PR metadata through MCP before reporting or optionally posting the
   result. Changed HEAD/base invalidates the snapshot: return `COMMENT` identifying
   the stale review, never a current approval. Every changed HEAD requires a fresh
   independent review of the entire PR; a changed base also requires a fresh review.
6. Return exactly one verdict: `APPROVE` when acceptance is sufficiently verified
   and no blocking findings remain; `REQUEST_CHANGES` for actionable blocking
   findings; `COMMENT` for an incomplete/stale review or informational assessment
   that cannot support approval. Approval never authorizes integration.

The result may remain in chat. Posting a formal Forgejo review through
`forgejo-mcp` is optional and is not an acceptance gate. A posting/access failure
does not invalidate a current independent chat review; report it truthfully.
Never merge/auto-merge, retarget or modify the reviewed branch, promote `main`,
release or deploy.
