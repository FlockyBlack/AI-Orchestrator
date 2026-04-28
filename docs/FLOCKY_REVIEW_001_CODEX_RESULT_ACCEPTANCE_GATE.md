# FLOCKY-REVIEW-001 Codex Result Acceptance Gate

## Scope

This gate is a compact, reference-only operator review aid for deciding whether a Codex task result should be:
- `ACCEPTED`
- `ACCEPTED_WITH_WARNINGS`
- `NEEDS_PATCH`
- `REJECTED`
- `BLOCKED`

Flocky/OpenClaw reviews evidence only.
It does not execute, dispatch, mutate runtime state, or become a second source of truth.

## Non-Goals

This gate does not:
- run Codex
- run tests from AI-Orchestrator
- modify PMBOT files
- change `dispatcher.py`
- change `run_codex.py`
- change runtime behavior
- add background execution
- enable Telegram
- install external skills
- authorize execution automatically

## Input Assumptions

- A Codex result arrives as a compact result envelope or task report.
- The operator manually supplies any relevant AI-Orchestrator artifact path.
- Flocky reviews the evidence and records a verdict.
- The review is reference-only and must not become runtime state.

## Minimum Codex Result Envelope

A result should include at least:
- `task_id`
- `status`
- `summary`
- `files_created`
- `files_modified`
- `tests_run`
- `blockers`
- `warnings`
- `safety_flags`
- `recommended_next_action`

Practical minimum meaning:
- the task can be identified
- the claimed result is understandable
- file touch scope is reviewable
- validation evidence is visible
- safety posture is explicit
- the next action is safe and specific

## Acceptance Verdicts

Use exactly:
- `ACCEPTED`
- `ACCEPTED_WITH_WARNINGS`
- `NEEDS_PATCH`
- `REJECTED`
- `BLOCKED`

## Operator Review Checklist

Check the following:

1. `task_id` matches the requested task.
2. `status` is coherent with the summary, warnings, blockers, and next action.
3. Work stayed inside the approved task scope.
4. `files_created` and `files_modified` are listed and plausible.
5. Forbidden files were not touched.
6. `tests_run` or checks are listed honestly, including when none were run.
7. Warnings are separated clearly from blockers.
8. Safety flags are explicit rather than implied.
9. No runtime or source-of-truth boundary was crossed.
10. `recommended_next_action` is safe, specific, and operator-usable.

## Safety Blockers

Block acceptance if any of these happened without prior approval:
- PMBOT live trading, order, wallet, or live API behavior was added
- `dispatcher.py` was changed
- `run_codex.py` was changed
- runtime behavior was changed
- background execution was added
- Telegram was enabled
- external skills were installed
- a second source of truth was created
- OpenClaw/Flocky was turned into an executor instead of a governance/review layer

If any of the above is present or cannot be ruled out safely, the verdict is `BLOCKED`.

## Verdict Rules

### ACCEPTED
Use when:
- output is complete enough for the requested task
- scope stayed approved
- evidence is coherent
- listed checks are adequate for the change size
- no material warnings remain
- no safety boundary was crossed

### ACCEPTED_WITH_WARNINGS
Use when:
- result is usable
- remaining issues are non-blocking
- warnings are explicit and bounded
- no safety boundary was crossed
- operator can proceed safely while remembering the caveats

### NEEDS_PATCH
Use when:
- result is mostly correct
- scope is still acceptable
- a limited correction is clearly needed
- rework is smaller than a full rejection
- evidence is good enough to request a targeted patch

### REJECTED
Use when:
- task scope was wrong
- evidence is too weak or misleading
- output is broken, incomplete, or implausible
- the implementation is not acceptable even without a safety blocker
- the safest next step is to send the task back rather than patch around it

### BLOCKED
Use when:
- safety, runtime, or source-of-truth boundary was crossed
- forbidden files were touched without approval
- live/trading/wallet/API behavior appeared without approval
- the result cannot be safely reviewed from the available evidence
- operator clarification or explicit human approval is required before any further step

## Review Record Template

Reference-only template:

```json
{
  "review_id": "manual-review-id",
  "reviewed_task_id": "task-id",
  "source_result_path": "path/to/codex-result.json",
  "verdict": "ACCEPTED | ACCEPTED_WITH_WARNINGS | NEEDS_PATCH | REJECTED | BLOCKED",
  "reason": "short plain-language review reason",
  "accepted_warnings": [],
  "required_patch": [],
  "blockers": [],
  "safety_flags": {
    "pmbot_live_behavior_added": false,
    "dispatcher_touched": false,
    "run_codex_touched": false,
    "runtime_changed": false,
    "background_execution_added": false,
    "telegram_enabled": false,
    "external_skills_installed": false,
    "second_source_of_truth_created": false,
    "openclaw_executor_role_added": false
  },
  "operator_next_action": "safe specific next step",
  "reviewed_at_manual": "YYYY-MM-DD HH:MM local"
}
```

Markdown-friendly shape:

```markdown
- review_id:
- reviewed_task_id:
- source_result_path:
- verdict:
- reason:
- accepted_warnings:
- required_patch:
- blockers:
- safety_flags:
- operator_next_action:
- reviewed_at_manual:
```

## PMBOT-Specific Overlay

For PMBOT-related Codex tasks, the default stance is **offline / local / paper-only** unless the operator explicitly approved otherwise.

Any of the following is blocking by default:
- live API use
- wallet handling
- private key handling
- real order placement
- trading execution
- runtime dispatcher change

## Recommended Use

Use this gate after a Codex result arrives and before any operator accepts it as a usable outcome.

Suggested flow:
1. inspect the result envelope
2. compare claimed scope vs approved task
3. check touched files and safety flags
4. choose one verdict only
5. write a short review record
6. keep the review record reference-only

## Source-of-Truth Boundary

AI-Orchestrator remains the only source of truth and runtime workspace.

This gate is only a review aid.
It must not:
- become execution authority
- replace canonical task artifacts
- mutate runtime state
- normalize unsafe boundary crossings through wording alone
