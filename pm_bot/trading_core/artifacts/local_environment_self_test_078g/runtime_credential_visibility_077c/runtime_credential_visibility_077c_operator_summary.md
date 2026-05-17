# PMBOT Runtime Credential Visibility Diagnostic 077C

- Status: `blocked_missing_private_key`
- Market: `BTC`
- Strategy: `tiny-momentum`
- Mode: `runtime environment visibility diagnostic / redacted metadata / no-live`
- raw secret output: `false`
- signer instantiated: `false`
- order submission enabled: `false`
- allowed_for_live: `false`

## Required Variables

- POLYMARKET_API_KEY: present=false length=0 fingerprint=missing
- POLYMARKET_API_SECRET: present=false length=0 fingerprint=missing
- POLYMARKET_API_PASSPHRASE: present=false length=0 fingerprint=missing
- POLYMARKET_PRIVATE_KEY: present=false length=0 fingerprint=missing
- POLYMARKET_WALLET_ADDRESS: present=false length=0 fingerprint=missing
- POLYMARKET_SIGNATURE_TYPE: present=false length=0 fingerprint=missing
- POLYMARKET_FUNDER_ADDRESS: present=false length=0 fingerprint=missing
- TELEGRAM_BOT_TOKEN: present=false length=0 fingerprint=missing
- TELEGRAM_ALLOWED_OPERATOR_IDS: present=false length=0 fingerprint=missing

## Telegram Runtime Aliases

- The Telegram runtime in this repo reads `PMBOT_TELEGRAM_BOT_TOKEN` and `PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS`.
- PMBOT_TELEGRAM_BOT_TOKEN: present=true length=46 fingerprint=sha256:ed3124edeb10
- PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS: present=true length=10 fingerprint=sha256:d712acf93039

## Group Summary

- polymarket_l2_visible: `false`
- private_key_visible: `false`
- wallet_context_visible: `false`
- telegram_credentials_visible: `true`

## Blockers

- `blocked_missing_private_key` - POLYMARKET_PRIVATE_KEY is missing in this runtime process context.
- `blocked_missing_polymarket_l2_credentials` - One or more Polymarket L2 credential variables are missing in this runtime process context.
- `blocked_missing_wallet_address` - Wallet address, signature type, or funder address context is missing in this runtime process context.
- `live_execution_still_blocked` - This diagnostic only reports redacted runtime visibility metadata and cannot enable live execution.

## Safe Next Commands

- `python -m pm_bot.operator_runner.runtime_credential_visibility_diagnostic --market BTC --strategy tiny-momentum --dry-run`
- `python -m pm_bot.operator_runner.signer_diagnostic_evidence_bridge --market BTC --strategy tiny-momentum --dry-run`
- `python -m pm_bot.operator_runner.first_supervised_tiny_order_readiness_packet --market BTC --strategy tiny-momentum --dry-run`

## Artifacts

- `pm_bot/trading_core/artifacts/local_environment_self_test_078g/runtime_credential_visibility_077c/runtime_credential_visibility_077c_result.json`
- `pm_bot/trading_core/artifacts/local_environment_self_test_078g/runtime_credential_visibility_077c/latest_runtime_credential_visibility_077c_status.json`
- `pm_bot/trading_core/artifacts/local_environment_self_test_078g/runtime_credential_visibility_077c/runtime_credential_visibility_077c_operator_summary.md`
