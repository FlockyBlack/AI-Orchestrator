# PMBOT Signer Diagnostic Evidence Bridge 076C

- Status: `blocked_signer_diagnostic_failed`
- Market: `BTC`
- Strategy: `tiny-momentum`
- Mode: `signer diagnostic evidence bridge / local artifact read-only / no-live`
- signer_diagnostic_evidence_ok_for_payload_dry_run: `false`
- signer_ready_for_live: `false`
- order_submit_ready: `false`
- full_signed_payload_output: `false`
- allowed_for_live: `false`

## Source Evidence

- source_artifact_available: `true`
- source_status: `blocked_missing_private_key`
- source_diagnostic_status: `missing_private_key`
- safe_non_order_challenge_evidence: `not_signed_or_not_proven_safe`
- source_safety_flags_ok: `true`
- redacted_wallet_evidence_present: `true`

## Safety

- this bridge reads local JSON artifacts only
- it does not read environment variables, secret files, wallets, or browser profiles
- it does not instantiate a signer, sign payloads, generate orders, submit, cancel, or call authenticated endpoints
- it does not store raw private keys, API secrets, passphrases, full signatures, or signed payloads
- OK evidence is only for a future payload dry-run readiness gate, not for live execution

## Manual Diagnostic Command

- `python -m pm_bot.operator_runner.guarded_signer_diagnostic_smoke --market BTC --strategy tiny-momentum --dry-run --allow-private-key-diagnostic`

## Artifacts

- `pm_bot/trading_core/artifacts/signer_diagnostic_evidence_bridge_076c/signer_diagnostic_evidence_076c_result.json`
- `pm_bot/trading_core/artifacts/signer_diagnostic_evidence_bridge_076c/latest_signer_diagnostic_evidence_076c_status.json`
- `pm_bot/trading_core/artifacts/signer_diagnostic_evidence_bridge_076c/signer_diagnostic_evidence_076c_operator_summary.md`

## Blockers

- Guarded signer diagnostic evidence is present but not OK for payload dry-run: missing_private_key.
- 076C signer diagnostic evidence is only for payload dry-run readiness; allowed_for_live=false remains enforced.
- signer_ready_for_live=false; this bridge cannot authorize live signer use.
- order_submit_ready=false; this bridge cannot authorize order submission.

## Required False Flags

- `allowed_for_live=false`
- `order_payload_signing_enabled=false`
- `order_payload_signing_attempted=false`
- `order_payload_signed=false`
- `order_payload_generated=false`
- `signed_order_generation_enabled=false`
- `signed_order_generation_attempted=false`
- `signed_order_generated=false`
- `signed_order_payload_generated=false`
- `signed_payload_generated=false`
- `order_submission_enabled=false`
- `order_submission_attempted=false`
- `order_submission_performed=false`
- `order_submitted=false`
- `order_cancel_enabled=false`
- `order_cancel_attempted=false`
- `order_cancel_performed=false`
- `order_cancellation_enabled=false`
- `order_cancellation_attempted=false`
- `order_cancellation_performed=false`
- `authenticated_trading_enabled=false`
- `authenticated_endpoint_enabled=false`
- `authenticated_request_performed=false`
- `authenticated_trading_call_performed=false`
- `wallet_connection_enabled=false`
- `wallet_connection_attempted=false`
- `wallet_enabled=false`
- `wallet_used=false`
- `wallet_signing_enabled=false`
- `wallet_signing_attempted=false`
- `live_execution_approved=false`
- `live_execution_allowed=false`
- `live_execution_performed=false`
- `real_execution_available=false`
- `real_order_submitted=false`
- `real_order_cancelled=false`
- `private_key_value_emitted=false`
- `raw_private_key_emitted=false`
- `raw_secret_values_emitted=false`
- `full_diagnostic_signature_emitted=false`
- `raw_diagnostic_signature_emitted=false`
- `diagnostic_challenge_order_payload_fields_present=false`
- `scheduler_or_daemon_added=false`
- `background_worker_added=false`
- `autonomous_live_trading_added=false`
- `live=false`
- `selected_token_payload_ready_for_submit=false`
- `signing_by_default=false`
- `signer_ready_for_live=false`
- `order_submit_ready=false`
- `full_signed_payload_output=false`
- `operator_approved=false`
- `order_generation_enabled=false`
- `order_generation_attempted=false`
- `order_payload_executable=false`
- `signing_enabled=false`
- `signing_attempted=false`
- `signed_payload_generation_enabled=false`
- `signed_payload_generation_attempted=false`
- `signed_payload_fingerprint_stored=false`
- `full_signed_payload_emitted=false`
- `raw_signed_payload_emitted=false`
- `full_signed_order_emitted=false`
- `raw_signed_order_emitted=false`
- `signed_payload_submit_enabled=false`
- `signed_payload_submit_attempted=false`
- `signed_payload_submitted=false`
- `submit_call_performed=false`
- `cancel_call_performed=false`
- `authenticated_polymarket_enabled=false`
- `network_trading_call_performed=false`
- `trading_write_call_performed=false`
- `network_write_call_performed=false`
- `network_write_performed=false`
- `network_post_performed=false`
- `network_put_performed=false`
- `network_patch_performed=false`
- `network_delete_performed=false`
- `private_key_read=false`
- `seed_phrase_read=false`
- `mnemonic_read=false`
- `api_secret_read=false`
- `auth_token_read=false`
- `passphrase_read=false`
- `credential_value_read=false`
- `credential_values_read=false`
- `credential_values_printed=false`
- `credential_values_stored=false`
- `credential_values_serialized=false`
- `environment_values_read=false`
- `secret_files_read=false`
- `secrets_read=false`
- `secrets_printed=false`
- `secrets_persisted=false`
- `credential_value_serialized=false`
- `raw_values_emitted=false`
- `cryptographic_signing_enabled=false`
- `cryptographic_signing_performed=false`
- `local_payload_signing_attempted=false`
- `local_payload_signed=false`
- `browser_automation_added=false`
- `signer_instantiated=false`
- `signer_instantiation_attempted=false`
- `signer_diagnostic_executed_by_bridge=false`
