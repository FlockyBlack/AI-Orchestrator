# PMBOT Signer Smoke Contract 068A

- Status: `blocked_contract_only_no_signer_smoke_execution`
- Market: `BTC`
- Strategy: `tiny-momentum`
- Mode: `signer smoke contract / contract-only / dry-run`
- execution_mode: `preflight`
- contract_only: `true`
- signer_smoke_executable: `false`
- allowed_for_live: `false`
- private_key_read: `false`
- polymarket_private_key_read: `false`
- address_derivation_performed: `false`
- diagnostic_challenge_signing_attempted: `false`
- order_payload_signing_enabled: `false`
- order_submission_enabled: `false`
- order_cancellation_enabled: `false`
- authenticated_trading_enabled: `false`
- wallet_connection_enabled: `false`

## Future Contract Scope

- a separate future task may define opt-in address derivation
- a separate future task may define opt-in non-order diagnostic challenge signing
- future mode must remain redacted and explicit
- future mode must not sign order payloads
- future mode must not submit or cancel orders
- future mode must not log raw key material

## Artifacts

- `pm_bot/trading_core/artifacts/signer_smoke_contract_068a/signer_smoke_contract_068a_result.json`
- `pm_bot/trading_core/artifacts/signer_smoke_contract_068a/latest_signer_smoke_contract_status_068a.json`
- `pm_bot/trading_core/artifacts/signer_smoke_contract_068a/signer_smoke_safety_contract_068a.json`
- `pm_bot/trading_core/artifacts/signer_smoke_contract_068a/signer_smoke_redaction_policy_068a.json`
- `pm_bot/trading_core/artifacts/signer_smoke_contract_068a/signer_smoke_operator_summary_068a.md`

## Required False Flags

- `allowed_for_live=false`
- `signer_smoke_executable=false`
- `signer_smoke_execution_enabled=false`
- `signer_smoke_executed=false`
- `signer_smoke_live_mode_enabled=false`
- `private_key_read=false`
- `polymarket_private_key_read=false`
- `seed_phrase_read=false`
- `mnemonic_read=false`
- `api_secret_read=false`
- `auth_token_read=false`
- `credential_value_read=false`
- `credential_values_read=false`
- `credential_value_serialized=false`
- `credential_values_serialized=false`
- `credential_value_printed=false`
- `credential_values_printed=false`
- `credential_value_stored=false`
- `credential_values_stored=false`
- `credential_value_hashed=false`
- `credential_values_hashed=false`
- `credential_value_transformed=false`
- `credential_values_transformed=false`
- `environment_values_read=false`
- `secret_files_read=false`
- `raw_key_material_logged=false`
- `raw_key_material_emitted=false`
- `redacted_key_material_emitted=false`
- `address_derivation_enabled=false`
- `address_derivation_performed=false`
- `derived_address_emitted=false`
- `diagnostic_challenge_signing_enabled=false`
- `diagnostic_challenge_signing_attempted=false`
- `diagnostic_challenge_signed=false`
- `diagnostic_challenge_output_emitted=false`
- `order_payload_signing_enabled=false`
- `order_payload_signing_attempted=false`
- `order_payload_signed=false`
- `order_payload_generated=false`
- `signed_payload_generated=false`
- `signed_order_payload_generated=false`
- `signed_order_generation_enabled=false`
- `signed_order_generation_attempted=false`
- `order_submission_enabled=false`
- `order_submission_attempted=false`
- `order_submission_performed=false`
- `order_cancellation_enabled=false`
- `order_cancellation_attempted=false`
- `order_cancellation_performed=false`
- `authenticated_trading_enabled=false`
- `authenticated_endpoint_enabled=false`
- `authenticated_request_performed=false`
- `wallet_connection_enabled=false`
- `wallet_connection_attempted=false`
- `wallet_enabled=false`
- `wallet_used=false`
- `wallet_signing_enabled=false`
- `wallet_signing_attempted=false`
- `cryptographic_signing_enabled=false`
- `cryptographic_signing_performed=false`
- `live_execution_approved=false`
- `live_execution_allowed=false`
- `live_execution_performed=false`
- `real_execution_available=false`
- `real_order_submitted=false`
- `order_submitted=false`
- `real_order_cancelled=false`
- `scheduler_or_daemon_added=false`
- `background_worker_added=false`
- `autonomous_live_trading_added=false`
