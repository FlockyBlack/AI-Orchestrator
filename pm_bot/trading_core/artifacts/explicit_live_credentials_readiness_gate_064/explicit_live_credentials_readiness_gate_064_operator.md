# PMBOT Explicit Live Credentials Readiness Gate 064

- Status: `blocked`
- Market: `BTC`
- Strategy: `tiny-momentum`
- Mode: `redacted presence-only / review-only`
- execution_mode: `preflight`
- dry_run_only: `true`
- non_executable: `true`
- allowed_for_live: `false`
- live_ready: `false`
- resolved_blocker_count: `0`

## Marker Presence

- marker_count: `25`
- required_marker_count: `14`
- missing_required_marker_count: `14`
- present_execution_flag_count: `0`
- presence_only: `true`
- presence_booleans_only: `true`
- explicit_allowlist_only: `true`
- broad_environment_scan_performed: `false`
- environment_values_read: `false`
- raw_values_emitted: `false`

## Operator Approval Boundary

- operator_review_marker_present: `false`
- dual_control_review_marker_present: `false`
- operator_approved: `false`
- operator_review_does_not_enable_live: `true`
- separate_live_enabling_task_required: `true`

## Readiness Meaning

- redacted_presence_review_ready: `false`
- this is not live authorization
- no credential value validation was performed
- no wallet, signing, authenticated request, order submission, or cancellation path exists here

## Blockers

- `live_execution_not_approved` - Live execution approval remains false.
- `credentials_not_value_verified_by_pmbot` - PMBOT did not read, validate, fingerprint, or serialize credential values.
- `operator_review_does_not_enable_execution` - Operator marker presence is review evidence only and cannot enable live execution.
- `authenticated_polymarket_requests_blocked` - Authenticated Polymarket requests remain blocked.
- `wallet_connection_blocked` - Wallet connection remains blocked.
- `signer_instantiation_blocked` - Signer instantiation remains blocked.
- `private_key_reads_blocked` - Private key reads remain blocked.
- `api_secret_reads_blocked` - API secret reads remain blocked.
- `signed_payload_generation_blocked` - Signed payload generation remains blocked.
- `order_submission_blocked` - Order submission remains blocked.
- `order_cancellation_blocked` - Order cancellation remains blocked.
- `balance_reads_blocked` - Balance reads remain blocked.
- `position_reads_blocked` - Position reads remain blocked.
- `kill_switch_not_bound_to_live_adapter` - Kill-switch markers are not bound to any live adapter in this gate.
- `rollback_cancel_plan_not_implemented` - Rollback and cancellation implementation remains a later task.
- `first_live_order_task_not_present` - A separate first tiny live order task is still required.
- `missing_required_marker:PMBOT_LIVE_CREDENTIALS_READINESS_GATE_ENABLED` - Required marker `PMBOT_LIVE_CREDENTIALS_READINESS_GATE_ENABLED` is absent; only presence metadata was recorded.
- `missing_required_marker:PMBOT_POLYMARKET_AUTH_CONFIG_PRESENT` - Required marker `PMBOT_POLYMARKET_AUTH_CONFIG_PRESENT` is absent; only presence metadata was recorded.
- `missing_required_marker:PMBOT_POLYMARKET_CLOB_BASE_URL` - Required marker `PMBOT_POLYMARKET_CLOB_BASE_URL` is absent; only presence metadata was recorded.
- `missing_required_marker:PMBOT_POLYMARKET_L2_API_KEY_PRESENT` - Required marker `PMBOT_POLYMARKET_L2_API_KEY_PRESENT` is absent; only presence metadata was recorded.
- `missing_required_marker:PMBOT_POLYMARKET_L2_API_SECRET_PRESENT` - Required marker `PMBOT_POLYMARKET_L2_API_SECRET_PRESENT` is absent; only presence metadata was recorded.
- `missing_required_marker:PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT` - Required marker `PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT` is absent; only presence metadata was recorded.
- `missing_required_marker:PMBOT_POLYMARKET_FUNDER_ADDRESS_CONFIGURED` - Required marker `PMBOT_POLYMARKET_FUNDER_ADDRESS_CONFIGURED` is absent; only presence metadata was recorded.
- `missing_required_marker:PMBOT_WALLET_ADDRESS_CONFIGURED` - Required marker `PMBOT_WALLET_ADDRESS_CONFIGURED` is absent; only presence metadata was recorded.
- `missing_required_marker:PMBOT_SIGNING_PROVIDER_CONFIGURED` - Required marker `PMBOT_SIGNING_PROVIDER_CONFIGURED` is absent; only presence metadata was recorded.
- `missing_required_marker:PMBOT_SIGNING_DRY_RUN_ONLY` - Required marker `PMBOT_SIGNING_DRY_RUN_ONLY` is absent; only presence metadata was recorded.
- `missing_required_marker:PMBOT_REQUIRE_MANUAL_OPERATOR_APPROVAL` - Required marker `PMBOT_REQUIRE_MANUAL_OPERATOR_APPROVAL` is absent; only presence metadata was recorded.
- `missing_required_marker:PMBOT_REQUIRE_KILL_SWITCH_READY` - Required marker `PMBOT_REQUIRE_KILL_SWITCH_READY` is absent; only presence metadata was recorded.
- `missing_required_marker:PMBOT_LIVE_CREDENTIALS_OPERATOR_REVIEW_RECORD_PRESENT` - Required marker `PMBOT_LIVE_CREDENTIALS_OPERATOR_REVIEW_RECORD_PRESENT` is absent; only presence metadata was recorded.
- `missing_required_marker:PMBOT_LIVE_CREDENTIALS_DUAL_CONTROL_REVIEW_PRESENT` - Required marker `PMBOT_LIVE_CREDENTIALS_DUAL_CONTROL_REVIEW_PRESENT` is absent; only presence metadata was recorded.

## Required False Flags

- `allowed_for_live=false`
- `canary_executable_now=false`
- `live_execution_approved=false`
- `real_execution_available=false`
- `operator_approved=false`
- `candidate_is_executable=false`
- `order_submission_enabled=false`
- `order_cancel_enabled=false`
- `wallet_signing_enabled=false`
- `signing_enabled=false`
- `signed_payload_generation_enabled=false`
- `signed_order_generation_enabled=false`
- `authenticated_polymarket_enabled=false`
- `live_connector_enabled=false`
- `order_submission_available=false`
- `order_cancel_available=false`
- `wallet_available=false`
- `signer_available=false`
- `signed_payload_available=false`
- `signed_order_available=false`
- `live_execution_allowed=false`
- `live_execution_performed=false`
- `wallet_enabled=false`
- `wallet_used=false`
- `wallet_connection_attempted=false`
- `wallet_signing_performed=false`
- `signer_instantiated=false`
- `signing_attempted=false`
- `cryptographic_signing_enabled=false`
- `cryptographic_signing_performed=false`
- `signed_payload_generated=false`
- `signed_order_payload_generated=false`
- `order_payload_generated=false`
- `real_order_submitted=false`
- `order_submitted=false`
- `real_order_cancelled=false`
- `order_cancelled=false`
- `order_submission_attempted=false`
- `order_cancellation_attempted=false`
- `balance_read_attempted=false`
- `position_read_attempted=false`
- `fill_read_attempted=false`
- `pnl_read_attempted=false`
- `balance_read_enabled=false`
- `position_read_enabled=false`
- `fill_read_enabled=false`
- `pnl_read_enabled=false`
- `authenticated_endpoint_call_performed=false`
- `authenticated_request_performed=false`
- `real_authenticated_get_performed=false`
- `private_key_read=false`
- `seed_phrase_read=false`
- `mnemonic_read=false`
- `credential_values_read=false`
- `credentials_values_read=false`
- `credential_values_serialized=false`
- `credentials_values_serialized=false`
- `credential_values_printed=false`
- `credential_values_stored=false`
- `credential_values_hashed=false`
- `credential_values_transformed=false`
- `environment_values_read=false`
- `environment_values_serialized=false`
- `environment_values_printed=false`
- `environment_values_stored=false`
- `environment_secrets_read=false`
- `secrets_read=false`
- `secrets_printed=false`
- `secrets_persisted=false`
- `raw_values_emitted=false`
- `actual_secret_values_exposed=false`
- `credentials_values_exposed=false`
- `browser_automation_added=false`
- `scheduler_or_daemon_added=false`
- `background_worker_added=false`
- `autonomous_live_trading_added=false`
- `telegram_live_order_controls_added=false`
- `telegram_signing_controls_added=false`
- `telegram_wallet_controls_added=false`
- `live_trading_enabled=false`
