# Implementation Discipline

## Product and Reuse

- Own only public/shared external ecosystem intelligence. Never own credentials,
  private subscription/remaining quota, held reset credits/cards, authenticated
  runtime state, private workspaces, local GPUs/preferences or task-specific final
  routing. No downstream decision engine or dependency on other Creatidy products
  during bootstrap.
- Reuse-first, not blind copying or a new generic catalog: consider models.dev,
  AI Model Watch, Model Price Watch, pydantic/genai-prices and wmpeng/codingplan.
  Verify actual licenses before copying/substantial adaptation; preserve required
  notices/attribution and record materially reused code/data provenance in a
  concise reuse/NOTICE record when it first lands. Secondary sources are not
  authoritative by convenience. No dataset redistribution without permission or
  new paid SaaS dependency in the core.
- Issue #1 freezes the future A/B/C proof and unbiased STOP/GO contract; bootstrap
  does not implement or decide it. Preserve advertised/observed/selectable/
  enforceable distinctions and public rules vs private state in future work.

## Scope and Autonomy

- Commit count is not an acceptance criterion. Use as many small, coherent,
  reviewable commits as needed. Remediation commits are normal. Do not squash,
  amend, force-push, or rewrite published history merely to reduce commit count.
- Make the smallest coherent accepted change. No unrelated refactors, speculative
  abstractions, invented APIs/fields, empty future layers, silent vocabulary changes
  or excessive documentation. No ingestion/web/REST/MCP server/scheduler/storage
  layer until a selected implementation issue requires one. No premature generic
  EAV, event sourcing, PostgreSQL, rules engine, score/leaderboard or ML calibration.
- A selected issue authorizes ordinary safe/reversible scoped operations. State
  a safe assumption and proceed; diagnose ordinary bugs/test/tool failures without
  asking for routine permission. Ask only for genuine authority, security/privacy,
  architecture, material scope, incompatible acceptance, irreversible/destructive
  action, meaningful cost or external credential/access decisions.
- Every retry needs a diagnosis and changed hypothesis, input, state or strategy.
  Normally make one corrected retry. A new session, timeout or model alone is not
  diagnosis. If attempts add no durable state, stop that operation and report a
  finite blocker. Never weaken requirements or claim unobserved success.
- Report material new problems rather than expanding scope. Follow-ups must be
  durable, distinct, actionable and verifiable; do not create them automatically.
