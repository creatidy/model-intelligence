# Repository Guidance

Model Intelligence is a public/shared AI ecosystem intelligence project, currently
bootstrap/M0. Read README.md and the following rules before work; do not rely on
automatic discovery of nested rule files:

- `.kilo/rules/10-task-system.md`: owner selection, branch and delivery gates.
- `.kilo/rules/20-forgejo-mcp.md`: repository authority and tool boundaries.
- `.kilo/rules/30-implementation-discipline.md`: product, reuse and scope limits.
- `.kilo/rules/40-local-search.md`: evidence and local working context.
- `.kilo/rules/validation.md`: repository-owned checks and handoff evidence.

Commands: `/implement-issue <number|URL|unambiguous title>`,
`/finish-pr <Forgejo PR number|URL>` and `/review-pr <Forgejo PR number|URL>`.
A plain `Implement issue #N` follows the implementation workflow. `/finish-pr`
authorizes bounded in-scope remediation on the selected PR, not additional issues
or merging. It consumes native `task` results directly, with at most three
remediation rounds. `/review-pr` is standalone read-only review using the same
`.kilo/agents/pr-reviewer.md` agent. A newly spawned reviewer subagent's isolated
context satisfies independence; implementation self-review and resumed reviewers
do not. Every changed HEAD/base requires a fresh whole-PR review. Forgejo review
publication is optional, never orchestration state. No external controller exists.

Use one normal checkout and ordinary issue branches. Do not use `git worktree`
or alternate checkout management unless Adrian explicitly re-enables it. Review
the exact frozen Git objects/current clean PR branch read-only in this checkout;
the parent must not edit or switch branches while the reviewer task is running.
Never stash/reset unrelated changes to make branch switching possible.

`.kilo/command/*` and `.kilo/agents/*` are loaded by the Kilo workspace runtime;
availability is not dynamically guaranteed when files appear. After adding
or changing commands, a VS Code/Kilo workspace reload may be required. The current
repository checkout supplies its local commands/agents/rules. A missing native
agent/task is a finite tool blocker, not permission to substitute parent self-review
or external orchestration.
