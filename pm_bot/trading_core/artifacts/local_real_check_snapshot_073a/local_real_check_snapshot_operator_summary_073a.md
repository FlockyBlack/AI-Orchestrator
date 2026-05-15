# PMBOT Local Real-Check Snapshot 073A

- Status: `local_real_check_snapshot_recorded_live_blocked`
- Market: `BTC`
- Strategy: `tiny-momentum`
- execution_mode: `local_real_check_snapshot_073a`
- allowed_for_live: `false`
- snapshot_executable_for_live: `false`
- local artifact reads only
- no network calls, no environment secret reads, no subchecks run by default

## Normalized Status

- `l2_auth_status` = `blocked_missing_l2_credentials`
- `account_readonly_status` = `account_config_not_detected`
- `signer_diagnostic_status` = `diagnostic_not_requested`
- `public_discovery_status` = `source_backed_candidates_ready`
- `token_bridge_status` = `blocked_no_latest_discovery_artifact`
- `order_prep_packet_status` = `blocked_order_prep_packet_not_ready`
- `final_blocker_status` = `blocked_remaining_first_live_order_final_blockers`

## Sources

- `local_real_check_bundle_072c` exists=true parsed=true status=`local_real_check_bundle_completed_with_blockers_live_blocked` path=`pm_bot/trading_core/artifacts/local_real_check_bundle_072c/latest_local_real_check_bundle_status_072c.json`
- `clob_l2_auth_readonly_probe_067c` exists=true parsed=true status=`blocked_missing_l2_credentials` path=`pm_bot/trading_core/artifacts/clob_l2_auth_readonly_probe_067c/latest_clob_l2_auth_readonly_probe_status_067c.json`
- `live_account_readonly_state_probe_070c` exists=true parsed=true status=`blocked_missing_l2_credentials` path=`pm_bot/trading_core/artifacts/live_account_readonly_state_probe_070c/latest_live_account_readonly_state_status_070c.json`
- `guarded_signer_diagnostic_smoke_069a` exists=true parsed=true status=`blocked_diagnostic_not_requested` path=`pm_bot/trading_core/artifacts/guarded_signer_diagnostic_smoke_069a/latest_guarded_signer_diagnostic_status_069a.json`
- `public_market_token_discovery_071a` exists=true parsed=true status=`source_backed_candidates_ready` path=`pm_bot/trading_core/artifacts/public_market_token_discovery_071a/latest_public_market_token_discovery_status_071a.json`
- `discovery_to_token_resolver_bridge_071d` exists=true parsed=true status=`blocked_no_latest_discovery_artifact` path=`pm_bot/trading_core/artifacts/discovery_to_token_resolver_bridge_071d/latest_discovery_to_token_resolver_bridge_status_071d.json`
- `order_prep_packet_072a` exists=true parsed=true status=`blocked_order_prep_packet_not_ready` path=`pm_bot/trading_core/artifacts/order_prep_packet_072a/latest_order_prep_packet_status_072a.json`
- `first_live_order_final_blocker_reducer_072d` exists=true parsed=true status=`blocked_remaining_first_live_order_final_blockers` path=`pm_bot/trading_core/artifacts/first_live_order_final_blocker_reducer_072d/latest_first_live_order_final_blockers_072d.json`

## Next Actions

- `keep_live_execution_blocked` - use this snapshot as read-only ingestion input only; keep any live-capable action in a separate approved task

## Safety

- this snapshot is not an executable live packet
- missing evidence remains `missing`; unknown evidence remains `unknown`
- raw source payloads are not embedded
- address-like values are redacted to short form when status/path text is reported
- no order submission, cancellation, order payload signing, wallet connection, or trading write endpoint is available
- latest status artifact: `pm_bot/trading_core/artifacts/local_real_check_snapshot_073a/latest_local_real_check_snapshot_status_073a.json`
