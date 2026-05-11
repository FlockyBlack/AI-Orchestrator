# AI-Orchestrator Codex Project Contract

This repository is the supervised automation home for AI-Orchestrator and PMBOT paper-mode development.
Operator-facing notes may be Russian, but code identifiers stay in English.

## 1. Project Mission

- AI-Orchestrator manages Codex and PMBOT plans, queues, execution packets, operator dashboards, and result ingestion.
- PMBOT is paper-only until explicit future approval in a separate task.
- Codex automation must remain supervised, auditable, resumable, and safe to inspect after interruptions.
- Every implementation task must leave a clear result artifact, validation record, and safety statement.

## 2. Current Hard Safety Boundaries

These boundaries are active for all tasks unless a separate future task explicitly changes them:

- no wallet/private keys/signing
- no real orders
- no trading endpoints
- no real-money actions
- no autonomous real trading
- no authenticated endpoints
- no browser automation
- no OpenRouter unless explicitly approved
- no Polymarket API unless explicitly approved
- no market recommendation as real trading advice
- no probability/EV/edge/confidence/side-selection as actionable real trading signal
- no git add .
- no git add -A
- no git add --all
- no force push
- selective staging only

If a task needs one of these boundaries relaxed, stop and require a separate operator-approved task.

## 3. Required Repo Discipline

- Inspect the current branch and HEAD before starting a task.
- Record `head_before` and `head_after` in the result JSON.
- Inspect relevant files before changing code.
- Make small, reviewable changes and preserve public interfaces unless the task requires a change.
- Run the smallest relevant tests first, then broader tests when the blast radius justifies it.
- Write a result JSON for each implementation task.
- Push only after validation passes.
- Verify remote HEAD after push.
- Use selective staging only; never use broad git staging.

## 4. PMBOT Rules

- Tracked markets remain unresolved unless evidence proves otherwise.
- Never invent outcomes.
- Paper-only simulation is allowed.
- Real trading is disabled.
- Source learning must be evidence-based.
- Unresolved market ambiguity must block, not guess.
- Market analysis artifacts must avoid actionable real trading signals.

## 5. Codex Automation Rules

- Prefer worktree/session isolation for long or risky execution.
- Preserve queue state, dashboard files, generated artifacts, and result envelopes.
- Use the auto-ingestion/result envelope path when Codex execution returns machine-readable JSON.
- Stop on safety failure, validation failure, schema mismatch, or blocked operator approval.
- App-server sessions must be short-lived unless explicitly approved.
- Do not create daemons, schedulers, background workers, or uncontrolled recursive Codex loops.
- Do not call external authenticated services from automation tasks.

## 6. Subagent Roles

Main Codex may use these roles as bounded working modes or delegated agents when the operator-approved environment supports it:

- Scout: read-only discovery, relevant file mapping, risk and dependency summary.
- Planner: scope decomposition, blockers, acceptance gates, and implementation plan.
- Builder: bounded code/docs implementation inside allowed paths.
- Tester: targeted tests, edge cases, fixtures, and validation report.
- Reviewer: diff review, safety scan, forbidden-action scan, and staging-rule scan.
- Docs: concise operator docs, result JSON, and artifact inventory without fake success claims.
- Integrator: aggregate role outputs, decide gate status, prepare selective staging plan, and commit/push only when allowed and safe.

Each role must stay inside its assignment. The main agent owns final aggregation and must report blockers honestly.

## 7. Required Output

Implementation tasks require:

- concise result JSON
- changed files list
- tests run and pass/fail status
- safety flags
- operator artifacts when useful
- docs only when useful for future operators
- remaining risks or blockers

Do not claim full roadmap completion unless the task explicitly completed that roadmap.
