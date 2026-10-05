# Repository Guidance

Model Intelligence is a public/shared AI ecosystem evidence project with an
integrated synthetic A/B/C architecture proof, not a live intelligence service.
Read README.md, ARCHITECTURE.md (ownership/decision authority), ROADMAP.md
(evidence and registered gaps), and the following rules before work; do not rely on
automatic discovery of nested rule files:

- `.kilo/rules/10-task-system.md`: owner selection, branch and delivery gates.
- `.kilo/rules/20-forgejo-mcp.md`: repository authority and tool boundaries.
- `.kilo/rules/30-implementation-discipline.md`: product, reuse and scope limits.
- `.kilo/rules/40-local-search.md`: evidence and local working context.
- `.kilo/rules/validation.md`: repository-owned checks and handoff evidence.

Commands: `/implement-issue <number|URL|unambiguous title>`,
`/finish-pr <Forgejo PR number|URL>`, `/review-pr <Forgejo PR number|URL>` and `/loop`.
A plain `Implement issue #N` follows the implementation workflow. `/finish-pr`
authorizes bounded in-scope remediation on the selected PR, not additional issues
or merging. It consumes native `task` results directly, with at most 10 whole-PR
review invocations per issue delivery, including initial/COMMENT/retries; its
excluded progress ledger preserves the count across finish/phase/session reentry.
`/review-pr` is standalone read-only review using the same
`.kilo/agents/pr-reviewer.md` agent. A newly spawned reviewer subagent's isolated
context satisfies independence; implementation self-review and resumed reviewers
do not. Every changed HEAD/base requires a fresh whole-PR review. Forgejo review
publication is optional, never orchestration state. No external controller exists.

Only an explicit owner `/loop` invocation delegates autonomous selection and
approved PR merge to develop/completed-issue closure. Its primary context is the
sole orchestrator, reusing implement-issue/finish-pr and the unchanged reviewer.
Read `.kilo/command/loop.md`: refresh all canonical open issues each cycle, exclude
exact invalid/wontfix/duplicate labels case-insensitively, verify explicit gates,
then order by explicit priority, required ordering and oldest registration.
Issues, not open PRs, are planning authority. Stop the entire invocation for
STOP_AND_ASK, STOP_REVISE or BLOCKED; no eligible issues yields QUEUE_EMPTY.
This does not authorize product GO, cross-repository mutation, Scarcity Router
operation, main, releases or deployments. Standalone implementation remains
owner-selected and unmerged; standalone review remains read-only.

An explicit owner documentation/planning mandate may authorize issue registration;
it does not select those functional issues for implementation. Preserve the frozen
A/B/C value gate and historical STOP_REVISE decisions. Documentation approval is
not product GO, verified consumer integration or READY_FOR_LIVE_TASK.

Use one normal checkout and ordinary issue branches. Do not use `git worktree`
or alternate checkout management. Only one context may mutate the checkout. Review
the exact frozen Git objects/current clean PR branch read-only in this checkout;
the parent must not edit or switch branches while the reviewer task is running.
Never stash/reset unrelated changes to make branch switching possible.

`.kilo/command/*` and `.kilo/agents/*` are loaded by the Kilo workspace runtime;
availability is not dynamically guaranteed when files appear. After adding
or changing commands, a VS Code/Kilo workspace reload may be required. The current
repository checkout supplies its local commands/agents/rules. A missing native
agent/task is a finite tool blocker, not permission to substitute parent self-review
or external orchestration.
