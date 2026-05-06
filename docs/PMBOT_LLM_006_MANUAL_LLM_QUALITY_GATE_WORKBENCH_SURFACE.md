# PMBOT-LLM-006 Manual LLM Quality Gate Workbench Surface

Task ID: PMBOT-LLM-006-MANUAL-LLM-QUALITY-GATE-WORKBENCH-SURFACE

## Summary

PMBOT-LLM-006 passively surfaces the existing manual LLM review quality gate artifact in the local operator review pack and workbench-facing outputs.

This is surface-only integration. It reads `pm_bot/llm/manual_llm_review_quality_gate.v1.json` when present and exposes compact deterministic status fields. It does not call an LLM API, generate LLM text, run browser automation, fetch live data, create orders, score markets, estimate outcomes, choose sides, or evaluate truth.

## Operator Pack Surface

The operator review pack now includes `manual_llm_review_quality_gate`.

When the artifact is present and valid, the section exposes:

- `artifact_status: present`
- `validation_status`
- `base_validator_status`
- compact summaries for required sections, minimum content, generic placeholder text, unsafe certainty, and forbidden content checks
- warning and error counts
- `next_safe_operator_action`
- a deterministic offline quality gate warning stating that this is not truth evaluation, probability, EV, edge, side, or trading advice

When the artifact is missing, the section returns `artifact_status: missing` and `validation_status: not_available`.

When the artifact is malformed or does not match the expected compact surface contract, the section returns `artifact_status: invalid` and `validation_status: rejected_or_unreadable` with a safe error summary.

## Workbench Outputs

Updated artifacts:

- `pm_bot/workbench/operator_review_pack.v1.json`
- `pm_bot/workbench/operator_review_pack.v1.md`
- `pm_bot/workbench/expected_operator_review_pack.v1.json`
- `docs/PMBOT_WORKBENCH_001_RESULT.json`
- `docs/PMBOT_CODEX_A_ROUND003_RESULT.json`

The static dashboard summary/report were refreshed only because they display the operator review pack artifact inventory counts, which moved from 21 to 22 artifacts.

## Safety Boundary

- No LLM API calls.
- No browser automation.
- No prompt automation.
- No runtime wiring.
- No dispatcher or `run_codex` changes.
- No credentials, wallets, private keys, or signing.
- No real orders or live trading.
- No autonomous paper orders.
- No probability, EV, edge, scoring, side recommendation, market decision, or truth evaluation fields were added to the quality gate surface.

## Verification

- `python -m pytest pm_bot\llm -q`: 38 passed
- `python -m pytest pm_bot\workbench -q`: 29 passed
- `python -m pytest pm_bot\quality pm_bot\dashboard pm_bot\operator -q`: 93 passed, 48 subtests passed
- `python -m pytest pm_bot\paper -q`: 331 passed, 39 subtests passed
- `python pm_bot\workbench\run_operator_workbench_export.py`: required steps passed
- Focused workbench tests cover present, missing, and malformed quality gate artifact handling.
