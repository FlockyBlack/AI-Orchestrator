# ORCH PMBOT Trading MVP 033 Tiny Live Canary Preflight Contract And Manual Runbook

## Purpose

This task adds a review-only preflight layer for a possible future tiny live canary. It defines the smallest acceptable future canary shape, the required evidence, manual operator checks, kill-switch requirements, blockers, stop conditions, and validation gates.

This is not live trading. It does not enable a wallet, signing, real order placement, authenticated endpoint calls, external API calls, browser automation, scheduler, daemon, or autonomous live execution.

## Current Build Status

- `preflight_contract_ready`: may be true when the static contract validates.
- `manual_runbook_ready`: may be true when the manual runbook validates.
- `future_canary_shape_defined`: may be true for review purposes only.
- `live_execution_approved`: always false.
- `real_execution_available`: always false.
- `live_connector_enabled`: always false.
- `canary_executable_now`: always false.

Operator review remains distinct from live approval. A review-ready packet is not authority to trade.

## Smallest Future Canary Shape

The only future shape defined by this task is:

- One manually reviewed market.
- One manually reviewed order-sized action.
- Tiny fixed placeholder notional and position limits.
- Review-only market status in this build.
- Required manual operator acknowledgement.
- Required disabled connector audit replay.
- Required operator review packet.
- Required static secret-boundary validation.
- Required blocker matrix review.
- Required manual runbook acknowledgement.
- Required kill-switch requirement validation.

The limits are placeholders for future review. They are not executable and do not authorize any order.

## Manual-Only Preflight Process

The manual runbook requires the operator to review:

- Purpose and scope.
- Explicit non-execution statement.
- Prerequisite artifacts.
- Operator identity and responsibility placeholder.
- Market selection review.
- Risk review.
- Secret boundary review.
- Disabled connector review.
- Audit replay review.
- Operator packet review.
- Kill-switch verification.
- Maximum exposure limits.
- Manual pause and abort conditions.
- Evidence capture checklist.
- Post-canary review requirements.
- Rollback and incident notes.
- Final non-authorization statement.

The runbook is pure data and text. It contains no live order workflow.

## Required Artifacts

Before any separate future canary proposal could be considered, the operator would need evidence for:

- Tiny live canary preflight contract validation.
- Manual runbook validation and acknowledgement.
- Operator review packet that explicitly does not approve live execution.
- Disabled connector audit replay.
- Static secret-boundary validation.
- Live connector blocker matrix with blockers unresolved.
- Kill-switch requirement packet.
- Evidence capture packet.

## Kill-Switch Requirements

The kill-switch model defines these future requirements:

- Operator-visible kill switch required.
- Dry-run kill-switch simulation required.
- Real connector must remain disabled in the current build.
- Live connector must not be enabled until a separate future gated task.
- Emergency stop instructions must be documented.
- No scheduler, daemon, or autonomous path may bypass the operator.

For this task:

- `requirements_defined`: true.
- `verified_for_live`: false.
- `blocks_live_execution`: true.

## Abort Conditions

Manual review must stop if:

- Any required artifact is missing, invalid, stale, or contradictory.
- Any artifact claims live execution approval or real execution availability.
- Any connector is enabled.
- Any workflow asks for wallet material, private keys, mnemonics, credentials, signing, authenticated endpoint use, or real order placement.
- Any scheduler, daemon, recursive loop, or autonomous path can bypass the operator.
- Any blocker matrix entry is treated as resolved without a separate gated task.
- Any output presents side selection, probability, EV, edge, or confidence as actionable real trading guidance.

## Unresolved Blockers

This task adds additional critical unresolved blocker categories:

- `tiny_live_canary_preflight_contract_review_only`
- `manual_runbook_not_operator_executed`
- `kill_switch_not_live_verified`
- `live_canary_manual_approval_not_collected`
- `live_canary_execution_adapter_disabled`
- `live_canary_funding_not_configured`
- `live_canary_market_selection_not_finalized`

Existing critical blockers remain unresolved. This task does not reduce severity, mark blockers resolved, or make live execution available.

## What Remains Impossible

This build still cannot:

- Access real wallets.
- Read private keys, mnemonics, seeds, credentials, or environment secrets.
- Sign payloads or transactions.
- Place real orders.
- Call authenticated Polymarket endpoints.
- Use browser automation.
- Run autonomous live execution.
- Run a scheduler, daemon, or uncontrolled recursive loop.
- Produce live trading advice or actionable real trading signals.

## Future Gated Task Required

Any real canary would require a separate future operator-approved task after all blockers are explicitly addressed. That future task would need to define and validate live credential handling, live connector boundaries, kill-switch wiring, live approval process, funding and exposure reconciliation, market selection finalization, post-action audit, and emergency stop procedures.

No part of this build grants that approval.
