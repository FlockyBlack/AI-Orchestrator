# PMBOT Guarded Signer Diagnostic Smoke 069A

- Status: `blocked_missing_private_key`
- Diagnostic status: `missing_private_key`
- Market: `BTC`
- Strategy: `tiny-momentum`
- Default mode reads private key: `false`
- Diagnostic requested: `true`
- Private key read: `true`
- Private key present: `false`
- Private key format valid: `false`
- Wallet address present: `false`
- Derived wallet match: `unknown`
- Diagnostic challenge signed: `false`
- Order payload signing: `blocked`
- Signed order generation: `blocked`
- Order submission: `blocked`
- Order cancellation: `blocked`
- Authenticated trading: `blocked`
- Live trading: `blocked`
- Allowed for live: `false`
- Private key value emitted: `false`
- Raw secret values emitted: `false`
- Full diagnostic signature emitted: `false`

## Diagnostic Scope

- the explicit diagnostic flag is required before reading `POLYMARKET_PRIVATE_KEY`
- the diagnostic challenge is fixed and not an order payload
- address values are redacted to prefix and suffix only
- diagnostic signature output is limited to a redacted fingerprint and length
- no order payload is signed, generated, submitted, or canceled
- no authenticated trading endpoint is called

## Artifacts

- `pm_bot/trading_core/artifacts/guarded_signer_diagnostic_smoke_069a/guarded_signer_diagnostic_smoke_069a_result.json`
- `pm_bot/trading_core/artifacts/guarded_signer_diagnostic_smoke_069a/latest_guarded_signer_diagnostic_status_069a.json`
- `pm_bot/trading_core/artifacts/guarded_signer_diagnostic_smoke_069a/guarded_signer_diagnostic_redaction_policy_069a.json`
- `pm_bot/trading_core/artifacts/guarded_signer_diagnostic_smoke_069a/guarded_signer_diagnostic_safety_contract_069a.json`
- `pm_bot/trading_core/artifacts/guarded_signer_diagnostic_smoke_069a/guarded_signer_diagnostic_operator_summary_069a.md`

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
