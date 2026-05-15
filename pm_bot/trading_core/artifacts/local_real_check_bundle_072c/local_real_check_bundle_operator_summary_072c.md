# PMBOT Local Real-Check Bundle 072C

- Status: `local_real_check_bundle_completed_with_blockers_live_blocked`
- Market: `BTC`
- Strategy: `tiny-momentum`
- Manual one-shot only: `true`
- Allowed for live: `false`
- Bundle executable for live: `false`
- Private key diagnostic requested: `false`
- Subchecks completed: `6/6`
- Subchecks failed: `0`
- Subchecks blocked: `4`
- Blockers: `11`

## Subchecks

- `clob_l2_auth_readonly_probe_067c` status=`blocked_missing_l2_credentials` classification=`blocked` artifact=`pm_bot/trading_core/artifacts/clob_l2_auth_readonly_probe_067c/clob_l2_auth_readonly_probe_067c_result.json`
- `live_account_readonly_state_probe_070c` status=`blocked_missing_l2_credentials` classification=`blocked` artifact=`pm_bot/trading_core/artifacts/live_account_readonly_state_probe_070c/live_account_readonly_state_probe_070c_result.json`
- `guarded_signer_diagnostic_smoke_069a` status=`blocked_diagnostic_not_requested` classification=`blocked` artifact=`pm_bot/trading_core/artifacts/guarded_signer_diagnostic_smoke_069a/guarded_signer_diagnostic_smoke_069a_result.json`
- `public_market_token_discovery_071a` status=`source_backed_candidates_ready` classification=`reported_success` artifact=`pm_bot/trading_core/artifacts/public_market_token_discovery_071a/public_market_token_discovery_071a_result.json`
- `discovery_to_token_resolver_bridge_071d` status=`operator_selection_required_multiple_source_backed_candidates` classification=`blocked` artifact=`pm_bot/trading_core/artifacts/discovery_to_token_resolver_bridge_071d/discovery_to_token_resolver_bridge_071d_result.json`
- `live_readonly_status_aggregator_071b` status=`live_readonly_status_aggregated` classification=`reported_success` artifact=`pm_bot/trading_core/artifacts/live_readonly_status_aggregator_071b/live_readonly_status_aggregator_071b_result.json`

## Consolidated Blockers

- `clob_l2_auth_readonly_probe_067c:missing_l2_api_credentials` `clob_l2_auth_readonly_probe_067c` - One or more required L2 API credential env vars are missing; private key fallback is forbidden.
- `live_account_readonly_state_probe_070c:missing_l2_api_credentials` `live_account_readonly_state_probe_070c` - One or more required L2 API credential env vars are missing; private key fallback is forbidden.
- `guarded_signer_diagnostic_smoke_069a:reported_blocked` `guarded_signer_diagnostic_smoke_069a` - Subcheck reported status blocked_diagnostic_not_requested; the bundle did not infer success.
- `discovery_to_token_resolver_bridge_071d:operator_selection_required` `discovery_to_token_resolver_bridge_071d` - Multiple source-backed token candidates are available; operator selection is required before producing a populated review contract.
- `discovery_to_token_resolver_bridge_071d:live_execution_blocked` `discovery_to_token_resolver_bridge_071d` - allowed_for_live=false and this task does not authorize live execution.
- `discovery_to_token_resolver_bridge_071d:order_generation_blocked` `discovery_to_token_resolver_bridge_071d` - Only a target candidate contract may be produced; no order payload is generated.
- `discovery_to_token_resolver_bridge_071d:signing_blocked` `discovery_to_token_resolver_bridge_071d` - Signing and signed payload generation remain blocked.
- `discovery_to_token_resolver_bridge_071d:submission_and_cancel_blocked` `discovery_to_token_resolver_bridge_071d` - Order submission and cancellation remain blocked.
- `discovery_to_token_resolver_bridge_071d:authenticated_trading_blocked` `discovery_to_token_resolver_bridge_071d` - Authenticated trading calls are not performed by this bridge.
- `local_real_check_bundle_allowed_for_live_false` `bundle` - The local real-check bundle is an operator diagnostic only and always sets allowed_for_live=false.
- `local_real_check_bundle_not_executable_for_live` `bundle` - The bundle output is not an executable live-trading packet.

## Safety

- no order submission or cancellation
- no order payload signing
- no trading write endpoint is called
- no live trading enablement is produced
- no raw secret value is written by the bundle
- subcheck failures remain visible in `local_real_check_bundle_subchecks_072c.json`
- `allowed_for_live=false` and `bundle_executable_for_live=false` are forced
