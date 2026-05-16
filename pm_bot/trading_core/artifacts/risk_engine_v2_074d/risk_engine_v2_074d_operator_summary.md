# PMBOT Risk Engine v2 Review 074D

- Status: `blocked_risk_engine_v2_review`
- Market: `BTC`
- Strategy: `tiny-momentum`
- execution_mode: `risk_engine_v2_review`
- allowed_for_live: `false`
- risk_engine_v2_executable_for_live: `false`
- first_supervised_tiny_order_blocked: `true`
- unknown evidence blocks
- no submit, no cancel, no signing, no wallet, no network

## Gates

- `stale_data` passed=false status=`local_real_check_snapshot_recorded_live_blocked`
- `liquidity_evidence` passed=false status=`missing_evidence`
- `source_backed_token_candidate` passed=false status=`selection_required`
- `account_readonly_evidence` passed=false status=`blocked_first_supervised_tiny_order_not_ready`
- `signer_diagnostic_evidence` passed=false status=`blocked_first_supervised_tiny_order_not_ready`
- `selected_token_payload_readiness` passed=false status=`blocked_missing_selected_token`
- `exposure_cap` passed=false status=`unknown_evidence`
- `per_market_cap` passed=false status=`unknown_evidence`
- `daily_loss_cap` passed=false status=`unknown_evidence`
- `duplicate_attempt_guard` passed=false status=`unknown_evidence`
- `halt_states` passed=false status=`unknown_evidence`
- `unknown_means_block` passed=false status=`unknown_evidence`
- `operator_approval_required` passed=false status=`review_required`
- `explicit_live_authorization_missing` passed=false status=`authorization_missing`

## Blockers

- `risk_v2_stale_data_or_freshness_unknown` - Data freshness evidence is stale or not review-ready.
- `risk_v2_liquidity_evidence_missing_or_weak` - Liquidity evidence is missing; weak or unknown liquidity blocks the review.
- `risk_v2_source_backed_token_candidate_missing` - Token candidate evidence is present but not source-backed and verified.
- `risk_v2_account_readonly_evidence_missing` - Read-only account evidence is not review-ready.
- `risk_v2_signer_diagnostic_evidence_missing` - Signer diagnostic evidence is present but not diagnostic_ok.
- `risk_v2_selected_token_payload_readiness_missing` - Selected-token payload readiness is not review-ready.
- `risk_v2_total_exposure_cap_unknown_or_exceeded` - total exposure cannot be evaluated because requested/current/limit values are missing.
- `risk_v2_per_market_cap_unknown_or_exceeded` - per-market exposure cannot be evaluated because requested/current/limit values are missing.
- `risk_v2_daily_loss_cap_unknown_or_exceeded` - Daily loss cap cannot be evaluated because local review values are missing.
- `risk_v2_duplicate_attempt_guard_unknown_or_triggered` - Duplicate attempt guard cannot be evaluated because the attempt key or prior-attempt list is missing.
- `risk_v2_halt_state_unknown_or_active` - Halt state is unknown; unknown halt state blocks the review.
- `risk_v2_unknown_evidence_blocks` - One or more readiness gates are unknown; unknown means block.
- `risk_v2_operator_approval_required` - A separate operator approval record is required before any future live action.
- `risk_v2_explicit_live_authorization_missing` - Explicit live authorization is missing and cannot be consumed by this no-live scaffold.

## Artifacts

- `pm_bot/trading_core/artifacts/risk_engine_v2_074d/risk_engine_v2_074d_result.json`
- `pm_bot/trading_core/artifacts/risk_engine_v2_074d/latest_risk_engine_v2_074d_status.json`
- `pm_bot/trading_core/artifacts/risk_engine_v2_074d/risk_engine_v2_074d_blockers.json`
- `pm_bot/trading_core/artifacts/risk_engine_v2_074d/risk_engine_v2_074d_gate_evaluations.json`
- `pm_bot/trading_core/artifacts/risk_engine_v2_074d/risk_engine_v2_074d_safety_snapshot.json`
- `pm_bot/trading_core/artifacts/risk_engine_v2_074d/risk_engine_v2_074d_operator_summary.md`

## Source Context

- `local_real_check_snapshot_073a` present=true status=`local_real_check_snapshot_recorded_live_blocked`
- `operator_token_selection_packet_073b` present=true status=`selection_required`
- `selected_token_payload_readiness_gate_073c` present=true status=`blocked_missing_selected_token`
- `real_local_check_evidence_review_074a` present=true status=`blocked_first_supervised_tiny_order_not_ready`

## Safety Statement

074D is a local review scaffold only. It does not read private material, instantiate signers, prepare executable payloads, submit or cancel orders, call Polymarket APIs, create schedulers, create daemons, or run background workers.
