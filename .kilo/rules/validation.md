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
- Before commit inspect `git status`, intended diff, recent commit style and the
  complete delta against the recorded develop SHA. Stage explicit intended files;
  exclude secrets, credentials, runtime state, caches and scratch. After commit
  verify exact head, base ancestry and final delta/status. Never undo others' work.
- Handoff includes issue/PR URLs, exact base/head SHAs, substantive files, exact
  executed validation/results and genuine unresolved decisions/blockers. No claim
  of passing checks, push or PR creation without successful evidence.
- Parent prepares a clean detached checkout at frozen HEAD and offline locked
  development environment for each reviewer. Reviewer reads checks before running
  them; generated ignored validation artifacts are allowed, tracked-file edits
  and Git/Forgejo mutations are not. Permission allowlists do not make arbitrary
  repository code safe. Preserve all unrelated checkouts and changes.
- `/finish-pr` records each reviewed HEAD/base/verdict, normal remediation commits,
  regression/check results and final currentness. Only an exact matching native
  reviewer result plus a final MCP currentness check can yield READY_TO_MERGE.
