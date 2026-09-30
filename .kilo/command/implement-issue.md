---
description: Implement one Adrian-selected Forgejo issue through an unmerged develop PR
---

Implement the single owner-selected issue: $ARGUMENTS

Read AGENTS.md and its listed rules. Do not choose another issue. An explicit
number, URL or unambiguous title is required; resolve/fetch the actual issue via
Forgejo MCP before planning/editing. Confirm its goal, scope, acceptance and
constraints; seek only genuine decisions, not routine reversible choices.

1. Verify canonical remote/access and inspect local status/files/worktrees. Fetch
   current canonical develop and record its exact SHA.
2. Create an isolated `issue-<number>-<short-topic>` branch and worktree from that
   exact SHA using Git; perform all implementation there. Preserve other work.
3. Implement only accepted scope; use reuse-first and product-boundary rules.
   Track short local progress when needed, excluded through .git/info/exclude.
4. Run focused checks and final `make check`. Inspect intended diff/status/full
   base delta for scope, secrets and local state. Diagnose failures before retry.
5. Inspect recent commit style, stage explicit intended files, commit the smallest
   coherent change and push the issue branch to canonical Forgejo via normal Git.
6. Create one Forgejo MCP PR targeting develop with `Refs #N`, scope, acceptance
   evidence, exact base/head SHAs, checks/results and limitations. Keep issue open.
7. Post a concise issue update with PR and validation. Report READY_FOR_REVIEW with
   links/SHAs or a precise finite blocker. The implementation session is not an
   independent reviewer. Never merge/auto-merge, touch main, release or deploy.
