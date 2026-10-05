# Single-Issue Workflow

- Start implementation only when Adrian explicitly selects one Forgejo issue by
  number, URL or unambiguous title. Fetch the actual issue via MCP before planning
  or editing. If the selection is ambiguous, clarify; never infer work from order,
  age, labels, milestones, Projects, branches, documentation queues or memory.
- The one-time issue #1 bootstrap creation/selection exception has expired. Do not
  create more issues without explicit authorization. No Program Execution Mode,
  controller, execution graph, autonomous issue selection or planning framework.
  An explicit owner documentation/planning mandate can authorize deduplicated
  registration of its main/gap issues; it does not authorize implementing the
  registered features. Record the actual mandate and use returned Forgejo IDs.
- Verify the canonical remote, fetch current `develop`, record its exact SHA and
  inspect files/status/branches. Demonstrate access by successful operations.
  Use one normal checkout, never `git worktree` or alternate checkout management
  unless Adrian explicitly re-enables it. Preserve unrelated changes/branches;
  never stash/reset others' work. If unrelated changes prevent safe switching,
  stop with a precise blocker.
- Create an ordinary branch named `issue-<number>-<short-topic>` from that recorded
  fetched SHA in this checkout. Use normal Git transport. Never implement
  directly on `develop`; never target, modify, merge into or promote `main`.
- Confirm accepted scope, implement the smallest coherent change, run checks,
  inspect status/full base delta, commit only intended files, push to canonical
  Forgejo, create one PR to `develop` via MCP and post a concise issue update.
- Never merge, auto-merge, bypass the human merge gate, release, promote or deploy
  as part of implementation/review. Keep the issue open at handoff; use `Refs #N`,
  not automatic closing keywords. Report issue/PR, base/head SHAs, validation and
  genuine blockers; READY_FOR_REVIEW means implemented and verified, not approved.
- `/finish-pr` selects an existing PR and authorizes only its linked issue's
  accepted-scope remediation. Use a fresh foreground `pr-reviewer` native `task`
  for each frozen whole-PR review; consume its result without owner relaying.
  At most three remediation rounds per invocation; never reset the count by
  restarting a session. Current APPROVE yields READY_TO_MERGE, never a merge.
  At the bound return STOP_REVISE with new defects versus incomplete fixes and
  recurring architectural/semantic patterns. Material scope/architecture decisions
  yield OWNER_DECISION_NEEDED; unavailable tools yield a precise finite BLOCKED.
