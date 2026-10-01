# Repository Guidance

Model Intelligence is a public/shared AI ecosystem intelligence project, currently
bootstrap/M0. Read README.md and the following rules before work; do not rely on
automatic discovery of nested rule files:

- `.kilo/rules/10-task-system.md`: owner selection, worktree and delivery gates.
- `.kilo/rules/20-forgejo-mcp.md`: repository authority and tool boundaries.
- `.kilo/rules/30-implementation-discipline.md`: product, reuse and scope limits.
- `.kilo/rules/40-local-search.md`: evidence and local working context.
- `.kilo/rules/validation.md`: repository-owned checks and handoff evidence.

Commands: `/implement-issue <number|URL|unambiguous title>` and
`/review-pr <Forgejo PR number|URL>`. A plain `Implement issue #N` follows the same
implementation workflow. These do not select additional work or authorize merging.
No Program Execution Mode exists. `/review-pr` orchestrates existing M5-B v2;
`creatidy-autonomy` owns independent reviewer routing/execution and formal publication.
No Kilo subagent or implementation self-review satisfies the formal review gate.

`.kilo/command/*` slash commands are discovered/loaded by the Kilo/VS Code workspace
runtime; availability is not dynamically guaranteed when files appear. After adding
or changing commands, a VS Code/Kilo workspace reload may be required. Open the
development worktree as the active VS Code workspace to load its repository-local
commands/rules. An unavailable command never permits inventing a different workflow.
