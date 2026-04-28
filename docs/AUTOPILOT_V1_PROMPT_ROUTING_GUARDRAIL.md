# AUTOPILOT V1 Prompt Routing Guardrail

## Purpose

This guardrail classifies incoming prompts before any receiver-specific tool execution is considered. It is a local deterministic classifier only. It does not execute prompts, mutate runtime state, route tasks into queues, or integrate with Flocky tools.

## Why ORCH-006 Misroute Happened

During ORCH-AUTOPILOT-006, a Codex implementation prompt was accidentally received by Flocky. The prompt lacked a strong local receiver-side routing stop before tool use, and Flocky spawned a code-changing subagent. The resulting artifacts were safe, but the provenance was abnormal because the wrong receiver acted first.

## Why Flocky Must Classify Before Tools

Flocky is validation-only and governance-only in the accepted architecture. That means Flocky must first determine whether a prompt is:

- genuinely a Flocky validation task
- genuinely a Flocky governance/design task
- actually a Codex code-changing or repair task
- ambiguous or misrouted
- unsafe or approval-gated

If the prompt is a Codex implementation task, Flocky must stop before tool execution and return a misroute decision.

## Why Flocky Must Not Spawn Sessions By Default

The guardrail hard-codes `sessions_spawn_allowed=false` for Flocky routing decisions. This prevents the specific abnormal provenance seen in ORCH-006, where the wrong receiver delegated code-changing work instead of rejecting the prompt.

## Routing Taxonomy

- `FLOCKY_VALIDATION_TASK`
- `FLOCKY_GOVERNANCE_TASK`
- `CODEX_CODE_CHANGING_TASK`
- `CODEX_REPAIR_TASK`
- `CHATGPT_PLANNING_TASK`
- `AMBIGUOUS_OR_MISROUTED_TASK`
- `UNSAFE_OR_APPROVAL_REQUIRED_TASK`

## Misroute Behavior

If receiver `Flocky` receives a Codex code-changing or repair prompt, the classifier returns:

- `misroute_detected=true`
- `safe_for_receiver_to_execute=false`
- `sessions_spawn_allowed=false`
- `code_changes_allowed_for_receiver=false`
- `required_behavior=MISROUTED_CODEX_PROMPT_DETECTED`

The decision also includes blocking reasons and an explicit `original_prompt_not_executed` warning.

## What Is Still Not Implemented

- no runtime wiring
- no dispatcher integration
- no `run_codex` integration
- no queue mutation
- no active Flocky tool integration
- no automatic retry or reroute transport
- no subagent spawning

The current implementation only classifies and reports.
