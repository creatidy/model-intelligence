---
description: Implement one Adrian-selected Forgejo issue through an unmerged develop PR
---

Implement the single owner-selected issue: $ARGUMENTS

Read AGENTS.md and its listed rules. Do not choose another issue. An explicit
number, URL or unambiguous title is required; resolve/fetch the actual issue via
Forgejo MCP before planning/editing. Confirm its goal, scope, acceptance and
constraints; seek only genuine decisions, not routine reversible choices.

1. Verify canonical remote/access and inspect local status/files/branches. Require
   a clean safe normal checkout. Never stash/reset unrelated changes; if they
   prevent safe switching, stop with a precise blocker. Fetch current canonical
   develop and record its exact SHA; switch/update local develop safely, with no
   guessed reconciliation of divergence.
2. Create an ordinary `issue-<number>-<short-topic>` branch from that exact SHA in
   the SAME checkout. Do not use git worktree or alternate checkout management.
3. Implement only accepted scope; use reuse-first and product-boundary rules.
   Track short local progress when needed, excluded through .git/info/exclude.
4. Run focused checks and final `make check`. Inspect intended diff/status/full
   base delta for scope, secrets and local state. Diagnose failures before retry.
5. Inspect recent commit style and stage explicit intended files. Make small,
   coherent, reviewable commits as needed, including remediation commits; commit
   count is not acceptance. Follow the history-safety rule in
   `.kilo/rules/30-implementation-discipline.md`. Push via normal Git.
6. Create one Forgejo MCP PR targeting develop with `Refs #N`, scope, acceptance
   evidence, exact base/head SHAs, checks/results and limitations. Keep issue open.
7. Post a concise issue update with PR and validation. Continue through the native
   `/finish-pr` workflow on that PR until its bounded terminal outcome; consume
   reviewer task results directly, with no owner relaying. The implementation
   context is not an independent reviewer. Never merge/auto-merge, touch main,
   release or deploy.
