# PMBOT Selected Token Verification Bridge 076A

- Status: `selected_token_verified_for_payload_dry_run`
- Market: `BTC`
- Strategy: `tiny-momentum`
- Mode: `selected token verification bridge / dry-run / no-live / no-submit`
- selected_token_payload_ready_for_submit: `false`
- allowed_for_live: `false`

## Verification

- selected_candidate_artifact_present: `true`
- selected_candidate_index: `0`
- selected_by_operator: `true`
- source_backed: `true`
- token_hash_match: `true`
- token_short_match: `true`
- market_match: `true`
- strategy_match: `true`
- market_title_match: `true`
- outcome_label_match: `true`
- selected_candidate_in_known_candidate_set: `true`
- selected_token_verified_for_payload_dry_run: `true`

## Matched Candidate

- candidate_index: `0`
- candidate_id: `operator-token-selection-candidate-073b-a289a2a3160e27ca`
- market_title: `MicroStrategy sells any Bitcoin by December 31, 2026?`
- outcome_label: `Yes`
- token_id_short: `111128...7287`
- token_id_hash: `d348e2a7d5d7c9f7084272c64ea704a8c5e82e183b04688937df777aef31e43a`

## Safety

- this bridge reads local JSON artifacts only
- it verifies the selected candidate against the known 073B source-backed candidate set
- it does not emit the full token ID
- it does not build an order payload, sign, submit, cancel, connect a wallet, read secrets, or call Polymarket

## Artifacts

- `pm_bot/trading_core/artifacts/selected_token_verification_bridge_076a/selected_token_verification_076a_result.json`
- `pm_bot/trading_core/artifacts/selected_token_verification_bridge_076a/latest_selected_token_verification_076a_status.json`
- `pm_bot/trading_core/artifacts/selected_token_verification_bridge_076a/selected_token_verification_076a_evidence.json`
- `pm_bot/trading_core/artifacts/selected_token_verification_bridge_076a/selected_token_verification_076a_operator_summary.md`

## Blockers

- 076A verification is only a payload dry-run bridge; allowed_for_live=false remains enforced.
- selected_token_payload_ready_for_submit=false; this bridge cannot authorize submit.
- Signing and signed payload generation remain blocked by default.
- Order submission and cancellation remain blocked.
