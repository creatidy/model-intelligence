---
description: Fresh read-only whole-PR review through the native pr-reviewer subagent
---

Review the exact Forgejo PR: $ARGUMENTS

Run in the primary context; do not require a separate owner-opened session.
Fetch actual PR metadata and its linked issue through `forgejo-mcp`. Require an
open, unmerged canonical Creatidy/model-intelligence PR targeting `develop`.
Read AGENTS.md and its rules, verify canonical remote, fetch current Git objects,
freeze exact HEAD/base/merge-base and inspect status/branches. Do not edit the PR.
Apply `.kilo/rules/50-technical-remediation.md`: technical environment repair is
allowed, PR remediation is not. Classify failures before returning control.

Use one delivery checkout by default: safely switch to the fetched PR branch if needed, creating
its local tracking branch at fetched HEAD only if absent. Require clean status and
exact frozen HEAD; refuse local divergence rather than rewriting a branch.
Never stash/reset unrelated changes;
if they prevent safe switching, attempt authorized isolation under rule 50 before
reporting a blocker. Bounded temporary exact-candidate review checkouts are allowed.
Prepare the sanitized offline locked
environment here; review frozen Git objects/current clean branch read-only. The
parent must not edit/switch while the reviewer is active. Locate `pr-reviewer`.
If native task/agent or required access is unavailable, diagnose and try bounded
environment repair or another available authorized independent native reviewer path
with the same contract; never self-review or broaden permissions instead.

Invoke `task` with `subagent_type: pr-reviewer`, `background: false`, no `task_id`
by default; rule 50 failover preserves the same independent result contract.
Pass only the PR number/URL, expected HEAD/base and fresh whole-PR review
instructions including the prepared checkout/environment and source pins/paths
when needed. Do not pass implementation
reasoning, previous findings or desired verdict. The agent definition owns the
JSON result contract and GPT-6.1 Sol High selection. Never resume a past reviewer.

Require JSON fields reviewed_head, reviewed_base, verdict, findings, limitations,
checks_run as defined in `.kilo/agents/pr-reviewer.md`. Validate their types and
exact frozen SHAs. Recheck local HEAD/clean status and MCP before reporting. A
changed HEAD/base, dirty checkout, malformed result or mismatch cannot support
approval. Diagnose class-A failures, change strategy and obtain fresh review within
rule 50's bound before reporting unresolved COMMENT with the precise limitation.
Every issue-delivery dispatch uses its shared 10-review ledger; standalone review
also records attempts and permits at most 10 whole-PR dispatches per invocation
without resetting any existing delivery counter. Present findings in severity
order and exactly one verdict.
Do not remediate, commit, push, publish a formal review, merge or modify Forgejo
state. The returned task result is the handoff, not an owner copy or PR comment.
