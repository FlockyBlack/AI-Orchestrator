# Autopilot V1 Routing Preflight

## Why preflight exists

`codex_auto/autopilot/run_routing_preflight.py` is a deterministic local simulator that runs the existing prompt-routing classifier before any receiver-specific work is considered.

Its job is narrow:
- read a prompt from a file or stdin
- classify the prompt for a declared receiver
- convert that decision into a preflight-only report
- validate that the report does not imply execution, runtime wiring, queue mutation, or ownership transfer

It does not execute the original prompt.
It does not integrate with Flocky tools.
It does not wire anything into dispatcher or `run_codex`.
It does not mutate runtime state, task queues, governance state, or checkpoints.

## What ORCH-006 taught us

ORCH-AUTOPILOT-006 showed that a Codex implementation prompt can be misrouted to Flocky before a strong local stop happens. The abnormal part was not the content of the task. The abnormal part was that the wrong receiver acted first.

That means the routing check must happen before any receiver-specific tool use, session spawning, shell execution, or project writes. The preflight simulator makes that requirement explicit and testable.

## Why classifier must run before tools

The accepted architecture is still:
- AI-Orchestrator is the only authoritative runtime and source of truth.
- Flocky is validation-only and governance-only.
- Codex is approved-code-execution-only.
- `codex_auto` is preview, dry-run, adapter, and guardrail only.

Because of that boundary, Flocky must first determine whether a prompt is:
- a real Flocky validation task
- a real Flocky governance/design task
- a misrouted Codex code-changing or repair task
- ambiguous
- unsafe or approval-gated

If that decision is not made first, the receiver can cross its scope before any human sees the mismatch.

## Why this is not active Flocky integration

The simulator is local and isolated:
- it wraps `codex_auto/autopilot/classify_prompt_route.py`
- it emits JSON only
- it writes nowhere by default
- optional writes are restricted to `codex_auto/autopilot/tests/output/`, `codex_auto/autopilot/fixtures/output/`, or `codex_auto/autopilot/tmp/`

There is no tool bridge, no task handoff transport, no auto-resend, no queue bridge, and no active receiver execution step.

## Why this is not runtime wiring

The simulator never:
- edits `scripts/dispatcher.py`
- edits `scripts/run_codex.py`
- changes runtime ledgers or checkpoints
- mutates `tasks/`, `runs/`, `state/`, `runtime/`, `results/`, `freeze/`, or `checkpoint/`

Its report explicitly enforces:
- `runtime_wiring_allowed=false`
- `dispatcher_integration_allowed=false`
- `run_codex_integration_allowed=false`
- `single_runtime_source_rule_preserved=true`

## Why this is not queue mutation

The simulator does not move work between queues and does not mark task state.

It explicitly blocks any report that implies:
- `queue_mutation_allowed=true`
- `queue_bridge_active=true`
- runtime/source-of-truth transfer to `codex_auto`

## Allowed receiver behavior

For receiver `Flocky`, the simulator allows only two continue cases:
- `FLOCKY_VALIDATION_TASK`
  Result:
  `preflight_passed=true`, `safe_for_receiver_to_continue=true`, `required_behavior=PROCEED_READ_ONLY_VALIDATION`, `allowed_tool_scope=read_only_validation_only`
- `FLOCKY_GOVERNANCE_TASK`
  Result:
  `preflight_passed=true`, `safe_for_receiver_to_continue=true`, `required_behavior=PROCEED_GOVERNANCE_DESIGN`, `allowed_tool_scope=read_only_governance_design_only`

For misrouted Codex tasks received by Flocky:
- `CODEX_CODE_CHANGING_TASK`
- `CODEX_REPAIR_TASK`

Result:
- `preflight_passed=false`
- `safe_for_receiver_to_continue=false`
- `required_behavior=MISROUTED_CODEX_PROMPT_DETECTED`
- `next_action=RESEND_TO_CODEX`

For ambiguous prompts:
- `required_behavior=RETURN_ROUTING_MISMATCH`
- `next_action=CLARIFY_OR_RESEND_TO_CORRECT_AGENT`

For unsafe or approval-required prompts:
- `required_behavior=BLOCK_UNSAFE_OR_APPROVAL_REQUIRED`
- `next_action=REQUIRE_HUMAN_APPROVAL_OR_REWRITE_PROMPT`

## Misroute JSON behavior

The preflight report is a deterministic JSON envelope with these guarantees:
- `preflight_only=true`
- `original_prompt_executed=false`
- `sessions_spawn_allowed=false`
- `active_flocky_tool_integration=false`
- `runtime_wiring_allowed=false`
- `dispatcher_integration_allowed=false`
- `run_codex_integration_allowed=false`
- `deterministic_preflight=true`

It also includes a required `forbidden_before_preflight` list so the stop conditions are visible inside the report itself.

## CLI usage

Prompt file mode:

```bash
python codex_auto/autopilot/run_routing_preflight.py \
  --receiver Flocky \
  --prompt-path codex_auto/autopilot/fixtures/prompt_codex_code_changing_task.txt \
  --out -
```

Validation prompt example:

```bash
python codex_auto/autopilot/run_routing_preflight.py \
  --receiver Flocky \
  --prompt-path codex_auto/autopilot/fixtures/prompt_flocky_validation_task.txt \
  --out -
```

Optional stdin mode:

```bash
type codex_auto/autopilot/fixtures/prompt_codex_code_changing_task.txt | python codex_auto/autopilot/run_routing_preflight.py --receiver Flocky --prompt-path - --out -
```

Optional safe write:

```bash
python codex_auto/autopilot/run_routing_preflight.py \
  --receiver Flocky \
  --prompt-path codex_auto/autopilot/fixtures/prompt_flocky_validation_task.txt \
  --out codex_auto/autopilot/tests/output/routing_preflight_report.json
```

## Test commands

```bash
python -m pytest -q codex_auto/autopilot/tests
python codex_auto/autopilot/run_routing_preflight.py --receiver Flocky --prompt-path codex_auto/autopilot/fixtures/prompt_codex_code_changing_task.txt --out -
python codex_auto/autopilot/run_routing_preflight.py --receiver Flocky --prompt-path codex_auto/autopilot/fixtures/prompt_flocky_validation_task.txt --out -
python -m pytest -q codex_auto
```

## What remains manual

This simulator does not decide acceptance and does not perform the next transport step.

Manual and gated work still remains:
- Flocky read-only validation of this implementation
- any later approval decision by a human
- any future transport or runtime wiring work in a separately gated task
- any future queue or dispatcher integration in a separately gated task

## Next gated step after Flocky validation

After Flocky validates this simulator read-only, the next gated step is a separate approval-controlled task to decide whether any receiver-side integration should exist at all. That is outside ORCH-010.
