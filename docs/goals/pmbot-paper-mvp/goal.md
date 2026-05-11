# PMBOT Paper MVP Goal

## Project Goal

Довести AI-Orchestrator/Codex до безопасного supervised workflow для PMBOT paper MVP: long runs, role-bounded execution, result envelopes, receipts, evidence-first market handling и operator review.

## Current Milestone Range

- Active range: 022-050
- Completed: 022-027
- Current: 028
- Next automation foundation: 029-030
- PMBOT milestones: 031-050

## Completed Milestones

- 022: operator panel + plan-runner
- 023: queue/state resume + recovery
- 024: Codex execution packet + result ingestion
- 025: real Codex CLI invocation + auto-ingestion path
- 026: Symphony-style workspace/session model + app-server schema boundary
- 027: real short-lived Codex app-server dry-run succeeded

## Next Milestones

- 028: AGENTS.md, subagents, memory-bank, phase memory, receipts, maintenance
- 029: worktree lane real execution and subagent routing
- 030: automation acceptance gate

## PMBOT Milestones

- 031-040: evidence/source/outcome/paper simulation automation foundation
- 041-050: paper-only MVP release readiness and supervised checkpoint

## Safety Constraints

- PMBOT remains paper-only.
- No wallet/private keys/signing.
- No real orders.
- No trading endpoints.
- No real-money actions.
- No autonomous real trading.
- No authenticated endpoints.
- No browser automation.
- No OpenRouter unless explicitly approved.
- No Polymarket API unless explicitly approved.
- No actionable real trading signal.
- Selective staging only.

## Receipt Requirements

Every implementation task should leave a receipt with:

- task_id
- status
- head_before
- head_after
- files_changed
- tests_run
- artifacts
- safety
- blockers
- next_recommended_task
