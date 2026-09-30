---
description: Independently review a frozen complete Forgejo PR without modifying it
subtask: true
---

Review the exact Forgejo PR: $ARGUMENTS

Read AGENTS.md and its listed rules. Require an exact PR number/URL; fetch its
actual metadata via Forgejo MCP and the linked issue when available. Freeze and
report exact head/base SHAs and the full merge-base-to-head diff boundary. Verify
the PR targets develop; never retarget it or modify main.

Use a fresh, distinct reviewer session/context with no implementation role for
this change. The implementation session or its self-review cannot satisfy this
gate. No concrete model choice is prescribed. Review is substantive and read-only:
never edit, format, commit, push or fix the reviewed branch. Use a separate detached
review worktree at the frozen head for local reads/non-mutating checks; preserve
existing worktrees and keep generated check artifacts local/ignored.

Review the **entire current PR**, not only its latest delta. Inspect authoritative
local sources, the selected issue acceptance criteria and relevant existing
behavior. Verify claimed tests/evidence and assess correctness, regressions,
missing tests, architecture, security/privacy, provenance/licenses and UX when
relevant. Separate reproduced evidence from unverified claims and testing gaps.

Present severity-ordered actionable findings with file/line and consequence;
state explicitly if none. Report acceptance coverage, exact frozen SHAs and
executed checks/results/limitations. Before publishing a Forgejo MCP review,
re-fetch metadata: if head/base changed, stop publication and report the stale
snapshot; a fresh full review is required. Publish COMMENT/REQUEST_CHANGES/APPROVED
only according to actual evidence. Approval is not authorization to integrate.
Never merge/auto-merge or bypass the human gate; never alter the reviewed branch.
