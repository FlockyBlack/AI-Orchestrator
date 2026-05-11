# Codex Agent Phase Card

## DISCOVERY

Purpose: understand task scope, current HEAD, existing files, safety boundaries, and likely blast radius.

Allowed actions:

- read repo files
- inspect git branch, HEAD, and status
- inspect relevant tests and docs
- produce Scout-style discovery notes

Forbidden actions:

- code changes
- staging/commit/push
- external service calls
- PMBOT outcome guesses

Required outputs:

- relevant files
- risks
- dependencies
- open questions or blockers

## PLANNING

Purpose: convert discovery into bounded implementation steps and validation gates.

Allowed actions:

- read `AGENTS.md` and relevant memory-bank files
- define allowed paths
- define tests and result artifacts
- identify blockers

Forbidden actions:

- unapproved scope expansion
- unrelated refactors
- fake acceptance criteria

Required outputs:

- implementation plan
- validation plan
- acceptance gates

## APPROVAL

Purpose: ensure operator approval exists for risky boundaries and execution modes.

Allowed actions:

- check task authorization
- check safety boundaries
- check allowed paths
- block when approval is missing

Forbidden actions:

- relaxing hard safety boundaries
- proceeding through missing approval
- starting long-lived sessions without approval

Required outputs:

- approval status
- blocked reason if approval is missing

## EXECUTION

Purpose: implement the approved bounded task.

Allowed actions:

- edit assigned files
- create required docs, tests, schemas, and artifacts
- use existing project patterns

Forbidden actions:

- unrelated rewrites
- new production dependencies without approval
- real PMBOT execution paths
- broad git staging

Required outputs:

- files changed
- implementation notes
- generated artifacts

## VERIFICATION

Purpose: prove the implementation is safe and behavior is preserved.

Allowed actions:

- run targeted tests
- run compile checks
- inspect diff
- validate JSON/schema artifacts

Forbidden actions:

- ignoring failing tests
- claiming success without validation
- hiding safety failures

Required outputs:

- commands run
- pass/fail status
- safety status
- residual risk

## HANDOFF

Purpose: leave concise operator-readable state for the next task.

Allowed actions:

- write result JSON
- update docs
- prepare selective staging plan
- commit/push only when explicitly allowed and safe

Forbidden actions:

- fake success claims
- force push
- broad staging
- unresolved blockers marked complete

Required outputs:

- result JSON
- `head_before` and `head_after`
- artifacts
- next recommended task
