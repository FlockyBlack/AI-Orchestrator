# FLOCKY-LONGRUN-001 Timeout and Stall Policy

## Scope

This is a compact, reference-only operator policy for deciding what to do when a long-running Codex/Flocky/OpenClaw task:
- runs longer than expected
- produces partial output
- appears stalled
- asks for clarification
- hits a safety or scope boundary

It is a review and decision aid only.

## Non-Goals

This policy is not:
- a scheduler
- a runtime
- an autonomous execution loop
- a replacement for AI-Orchestrator state
- permission to run tasks while the operator is absent
- permission to ignore safety gates

## Source-of-Truth Boundary

AI-Orchestrator remains the only source of truth and runtime workspace.

Flocky/OpenClaw may observe progress, review artifacts, and record operator decisions, but must not become a second source of truth or an executor.

If the root task state becomes unclear, stop and escalate.

## Task Duration Classes

Use practical operator-facing classes:

- **SHORT**: expected to finish quickly and normally within one focused pass
- **MEDIUM**: may need several steps, checks, or small iterations
- **LONG**: expected to span multiple substantial work chunks
- **OVERNIGHT**: intentionally left to continue while operator is away, but still subject to safety and approval boundaries
- **STALLED**: progress appears stopped or circular
- **NEEDS_HUMAN**: task cannot continue safely without an operator decision or approval

These are decision classes, not hard runtime timers.

## Progress Signals

Treat a task as making progress when one or more of these are visible:
- new files or artifacts are produced
- existing artifacts are advancing meaningfully
- result envelope or partial report appears
- logs show new distinct phases rather than repetition
- a blocker is identified clearly with a safe next step
- validation evidence is accumulating
- the task narrows uncertainty without crossing scope

## Stall Signals

A task may be stalled if any of these appear:
- no new files or artifacts
- repeated same log line or repeated same phase
- no result envelope after reasonable elapsed time for the class
- command is waiting for input
- auth or session expired
- tool crashed or became unavailable
- task asks the operator for a decision
- unsafe boundary encountered
- output contradicts approved task scope

One signal may justify caution.
Multiple signals usually justify status change or escalation.

## Allowed Continuation Behavior

Continuation is acceptable when:
- the task is still making progress
- only soft blockers exist
- a next safe work item is available inside scope
- no safety boundary has been crossed
- source-of-truth ownership remains clear
- no unapproved runtime mutation is required

Stop continuation when:
- a safety boundary is hit
- source-of-truth boundary is unclear
- required operator approval is missing
- runtime mutation would be needed without approval
- the task shifts outside approved scope
- a PMBOT live/wallet/API/trading concern appears without explicit approval

## Retry Policy

### One retry is allowed when:
- the failure is narrow and plausibly transient
- the task stayed inside approved scope
- the environment is still trustworthy
- the retry does not require a new approval boundary
- the retry is likely cheaper than opening a new task

### Retry is forbidden when:
- a safety boundary was crossed
- source-of-truth drift appeared
- forbidden files or runtime surfaces were touched without approval
- PMBOT live behavior, wallet, private key, trading, order, or live API concerns appeared
- the same failure already repeated without new evidence

### Retry must be operator-approved when:
- auth or session expired
- the root cause is unclear
- the task may re-touch sensitive surfaces
- the prior run produced contradictory output
- the retry changes the requested approach materially

### Retry should be patch-only when:
- the result is mostly correct
- only a bounded fix is needed
- the correction can be described explicitly
- the operator can name the exact expected patch target

### Retry should be replaced by a new task when:
- scope must be reframed
- the output contract was wrong
- the original task mixed multiple goals
- the failure revealed that a smaller or cleaner task boundary is needed

## Escalation Policy

Escalate to the operator when any of these appear:
- safety boundary issue
- missing approval
- unclear root or source of truth
- auth or session expiration
- repeated failure
- tool or environment issue
- contradictory result
- potential PMBOT live behavior
- any wallet, API, trading, order, or private key concern

Escalation should say:
- what was observed
- why continuation is unsafe or unclear
- what action is allowed next
- what action is forbidden next

## Status Mapping

Use these statuses:

- **CONTINUE**: progress is visible and continuation remains safe
- **WAIT**: task may still be healthy, but more evidence or elapsed time is needed before changing course
- **RETRY_ALLOWED**: one bounded retry is reasonable and safe
- **NEEDS_PATCH**: task result is mostly correct but requires a targeted correction
- **NEEDS_OPERATOR_DECISION**: task cannot continue safely without explicit operator input
- **BLOCKED**: safety, source-of-truth, or approval boundary prevents continuation
- **ACCEPT_PARTIAL_WITH_WARNINGS**: partial useful output exists, but it is incomplete and must be carried with explicit caveats

## Operator Decision Record Template

Reference-only template:

```json
{
  "decision_id": "manual-decision-id",
  "task_id": "task-id",
  "observed_state": "short plain-language state summary",
  "elapsed_time_manual": "operator-observed duration",
  "last_progress_signal": "most recent meaningful progress sign",
  "stall_signals": [],
  "decision": "CONTINUE | WAIT | RETRY_ALLOWED | NEEDS_PATCH | NEEDS_OPERATOR_DECISION | BLOCKED | ACCEPT_PARTIAL_WITH_WARNINGS",
  "reason": "short explanation",
  "allowed_next_action": "safe specific next step",
  "forbidden_next_action": "unsafe or disallowed next step",
  "reviewed_at_manual": "YYYY-MM-DD HH:MM local"
}
```

Markdown-friendly shape:

```markdown
- decision_id:
- task_id:
- observed_state:
- elapsed_time_manual:
- last_progress_signal:
- stall_signals:
- decision:
- reason:
- allowed_next_action:
- forbidden_next_action:
- reviewed_at_manual:
```

## PMBOT-Specific Overlay

For PMBOT-related work:
- default is offline / local / paper-only
- no live API
- no wallet or private key handling
- no real order placement
- no trading execution
- no `dispatcher.py`, `run_codex.py`, or runtime change without explicit approval
- any violation becomes `BLOCKED`

## Recommended Use

Use this policy when a task is running long enough that the operator needs a decision rather than a guess.

Suggested flow:
1. classify the run roughly
2. check progress signals
3. check stall signals
4. decide whether safe continuation still exists
5. choose one status only
6. record the decision in a short reference-only note
7. escalate immediately if safety or source-of-truth boundaries become unclear
