# Autopilot V1 Rendered Prompt Handoff Runbook

## Purpose

This runbook defines the current manual handoff process for a rendered prompt and its local preflight report.

The goal is to keep rendered-prompt work reviewable and bounded while AI-Orchestrator remains the only authoritative runtime and source of truth.

## Current-stage boundaries

- AI-Orchestrator remains the only authoritative runtime and source of truth.
- Flocky remains validation-only and governance-only.
- Codex remains approved code execution only after manual review and approval.
- `codex_auto` remains preview, dry-run, adapter, guardrail, simulator, prompt-pack, and renderer only.
- The renderer produces a rendered prompt and a local report. It does not execute or send prompts.
- No runtime wiring is implemented.
- No active Flocky integration is implemented.
- No dispatcher or `run_codex` integration is implemented.
- No queue bridge is implemented.
- No final acceptance authority is assigned to this runbook or to `codex_auto`.

## Manual handoff flow

1. Choose the prompt-pack template that matches the intended receiver and task type.
2. Create the render request JSON inside an approved local area.
3. Run the renderer to produce a rendered prompt and inline preflight report.
4. Review the render request before using the rendered prompt.
5. Review the render report and confirm the renderer stayed render-only.
6. Interpret the preflight report and stop if the receiver, behavior, or scope is wrong.
7. If the report remains safe and approved, manually send the rendered prompt to the correct agent.
8. Copy the resulting agent output back into the operator record without changing runtime state.
9. Require Flocky read-only validation after any Codex output.
10. If Flocky finds issues, run the repair loop with a new bounded prompt.
11. If a wrong-agent execution or unsafe action occurs, start incident containment and stop normal flow.

## Template selection rules

- Use `codex_code_changing.template.txt` only for approved code-changing work with explicit write scope and approval.
- Use `codex_focused_repair.template.txt` only for repair work with explicit write scope and approval.
- Use `flocky_read_only_validation.template.txt` only for read-only validation tasks.
- Use `flocky_governance_design.template.txt` only for governance or policy review tasks.
- Use `chatgpt_planning.template.txt` only for planning work that must not change project files.
- Do not reuse a template when the target agent, task owner, or task type do not match the manifest contract.
- Stop if the template would imply runtime wiring, dispatcher integration, `run_codex` integration, or queue bridging.

## Render request review checklist

- Confirm `TARGET_AGENT`, `TASK_OWNER`, and `TASK_TYPE` match the intended receiver.
- Confirm allowed write paths are explicit, minimal, and approved for the chosen template.
- Confirm forbidden write paths include runtime, queue, state, result, freeze, checkpoint, governance, dispatcher, and `run_codex` surfaces when relevant.
- Confirm forbidden behavior blocks prompt sending by automation, runtime wiring, queue mutation, session spawning, and active tool integration.
- Confirm validation commands are review-only commands and not execution approvals.
- Stop if the request implies `codex_auto` is runtime authority or source of truth.

## Render report review checklist

- Confirm `render_only` is true.
- Confirm `original_prompt_executed` is false.
- Confirm `rendered_prompt_executed` is false.
- Confirm `sessions_spawn_allowed` is false.
- Confirm `runtime_wiring_allowed` is false.
- Confirm `queue_mutation_allowed` is false.
- Confirm `active_flocky_tool_integration` is false.
- Confirm `single_runtime_source_rule_preserved` is true.
- Stop if the report claims approval to execute, approval to apply runtime state, runtime done, or final accepted.

## Preflight interpretation rules

- Treat `PROCEED_READ_ONLY_VALIDATION` as safe only for Flocky read-only validation.
- Treat `PROCEED_GOVERNANCE_DESIGN` as safe only for Flocky governance design review.
- Treat `MISROUTED_CODEX_PROMPT_DETECTED` as a hard stop for Flocky execution or tool use.
- Treat `RETURN_ROUTING_MISMATCH` as a hard stop until the prompt is clarified or resent to the correct agent.
- Treat `BLOCK_UNSAFE_OR_APPROVAL_REQUIRED` as a hard stop until the prompt is rewritten or a human explicitly re-approves the task.
- Stop if preflight says the receiver is unsafe, ambiguous, misrouted, or approval-gated.

## Send/no-send decision rules

- Send only when the template matches the intended agent, the render report stayed render-only, and preflight remains safe for the receiver.
- Do not send when approval is missing for Codex code-changing or repair work.
- Do not send when the rendered prompt implies runtime wiring, dispatcher integration, `run_codex` integration, or queue bridging.
- Do not send when the prompt asks for autonomous continuation, session spawning, external execution, or runtime mutation.
- Stop on any unsafe, blocked, ambiguous, or misrouted preflight outcome.

## Result copy-back rules

- Copy back the rendered prompt report, the agent response, and the operator notes into approved documentation or review artifacts only.
- Preserve the original rendered prompt and preflight report with the copied result so later reviewers can reconstruct the decision path.
- Do not treat a copied result as runtime state.
- Do not write copied results into queue, state, result, freeze, checkpoint, dispatcher, or `run_codex` surfaces.
- Stop if copy-back would mutate authoritative runtime records.

## Flocky validation requirement after Codex output

- Any Codex output produced from this manual handoff must be followed by Flocky read-only validation before the task is treated as ready for acceptance review.
- The Flocky validation step reviews the bounded Codex output, the rendered prompt, the preflight report, and the claimed write scope.
- Codex output alone is not final acceptance.
- Stop if Flocky validation is skipped after Codex output.

## Repair loop rules

- Start a repair loop when Flocky validation finds a contract gap, safety issue, scope drift, or missing evidence.
- Create a new bounded render request for the repair task instead of editing runtime state directly.
- Re-run the renderer and re-check preflight for the repair prompt.
- Require Flocky read-only validation again after the repair output.
- Stop if the repair loop expands scope beyond the approved write paths or tries to bypass validation.

## Misroute handling

- If a Codex task is reviewed by Flocky preflight and marked `MISROUTED_CODEX_PROMPT_DETECTED`, do not continue with Flocky tool use.
- If a Flocky-only task is sent to Codex, stop and resend it to Flocky as a read-only task.
- If receiver ownership is mixed or unclear, classify it as routing mismatch and stop until clarified.
- If wrong-agent execution occurs, treat it as an incident and move to containment immediately.

## Incident containment trigger

- Trigger containment if a wrong agent executes a prompt.
- Trigger containment if any prompt is sent after a blocked or mismatched preflight result.
- Trigger containment if any step implies runtime mutation, queue mutation, dispatcher integration, `run_codex` integration, or active Flocky tool integration.
- Trigger containment if an operator cannot prove which rendered prompt produced the result being reviewed.
- Containment means stop normal flow, preserve artifacts, record the mismatch, and require human review before any new handoff.

## Acceptance rules

- Acceptance review can begin only after manual handoff evidence exists, Codex output is copied back, and Flocky read-only validation has completed.
- Acceptance review still belongs outside this runbook.
- This runbook does not grant final acceptance authority.
- This runbook does not grant execution approval.
- This runbook does not claim runtime done.

## What remains manual

- Template choice remains manual.
- Render request authoring remains manual.
- The renderer command is run manually by the operator.
- Preflight interpretation remains manual.
- Prompt sending remains manual.
- Result copy-back remains manual.
- Flocky validation after Codex remains manual.
- Human approval and acceptance review remain manual.

## What is not implemented

- Runtime wiring is not implemented.
- Active Flocky integration is not implemented.
- Dispatcher integration is not implemented.
- `run_codex` integration is not implemented.
- Queue bridging is not implemented.
- Automatic prompt sending is not implemented.
- Automatic result write-back is not implemented.
- Session spawning is not implemented for this flow.
- Final acceptance automation is not implemented.
