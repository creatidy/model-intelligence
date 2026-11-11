# Validation and Handoff

- Python 3.12+, uv, src layout and typed `model_intelligence`. Prefer standard
  library and minimal dependencies. Maintain uv.lock with intentional dependency
  changes; do not regenerate it to conceal a locked-sync failure.
- Final gate is `make check`. Makefile owns locked synchronization, Ruff lint,
  Ruff format check, basedpyright, deterministic local unittest discovery, and
  unstaged/staged `git diff --check`. Do not replace basedpyright with a weaker
  substitute or bypass any gate. Focused commands may diagnose before the gate.
- Tests use synthetic fixtures, controlled time and no live network/private
  accounts. Verify installed/built packaging when packaging changes.
- During development prefer checks focused on the change; the required final
  `make check` and command-specific validation still apply. Do not assume CI is
  an equivalent replacement: that requires an actual complete, accessible run
  bound to the exact candidate and a consistent change to the delivery rules.
- Define each scenario once where practical. Do not maintain manually copied
  scenario matrices or repeat the same scenario without a distinct evidentiary
  purpose. Consolidate only when all assertions and required boundaries survive;
  checkout, installed wheel, dependency-free runtime and sdist-rebuilt wheel can
  establish different facts and must not be treated as interchangeable.
- Build identical immutable artifacts once per run where their identity and
  provenance are verified. Different source revisions or build paths are distinct
  evidence. Share artifacts, not mutable test state: isolate working directories,
  databases, ports, process identifiers and fixtures unless sharing is under test.
- Parallelize only after verifying isolation, preferably in separate processes;
  serialize or truly isolate host-global state, fixed markers, shared containers
  and signals. Do not mask races by increasing timeouts or automatic retries.
  If suites are split into phases or shards, automatically verify a complete,
  disjoint union of case identities, including parameters, not just counts.
- Installed-artifact tests must verify import and executable provenance from the
  intended artifact, including workers and representative child processes where
  applicable. Preserve a separate proof without undeclared runtime dependencies.
- Bind successful validation to the actual checkout or explicit merge tree and
  exact candidate/base, required steps and results; a green badge alone is not
  sufficient. Independent review examines code, assertions and exact-run evidence;
  it may add focused checks for unresolved risks rather than repeat equivalent
  checks without a distinct purpose. Required command-specific gates remain binding.
- When optimizing validation, measure before and after: total wall-clock, major
  phases, executed and skipped case counts, and runner conditions. A single timing
  is an observation, not a future guarantee. Report unavailable or skipped required
  evidence as UNPROVED, never success, including native, security, external
  integration and failure-recovery evidence where applicable.
- Before commit inspect `git status`, intended diff, recent commit style and the
  complete delta against the recorded develop SHA. Stage explicit intended files;
  exclude secrets, credentials, runtime state, caches and scratch. After commit
  verify exact head, base ancestry and final delta/status. Never undo others' work.
- Handoff includes issue/PR URLs, exact base/head SHAs, substantive files, exact
  executed validation/results and genuine unresolved decisions/blockers. No claim
  of passing checks, push or PR creation without successful evidence.
- Parent uses the prepared delivery/review checkout on the exact clean PR HEAD and prepares
  its offline locked development environment before invoking a reviewer. Apply
  rule 50 for secret-safe validation and bounded environment failover; AGENTS.md
  defines conversational independence. The existing prepared environment may be
  shared; separate execution requires a concrete technical necessity. No
  candidate edits or branch switching during review. Reviewer verifies HEAD
  and clean status before/after checks and inspects frozen Git objects/full base
  delta. Ignored validation artifacts are allowed; tracked-file edits and
  Git/Forgejo mutations are not. Read checks before running them; permission
  allowlists do not make arbitrary repository code safe. Preserve unrelated work.
- `/finish-pr` records each reviewed HEAD/base/verdict, normal remediation commits,
  regression/check results and final currentness. Only an exact matching native
  reviewer result plus a final MCP currentness check can yield READY_TO_MERGE.
