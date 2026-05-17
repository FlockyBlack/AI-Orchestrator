# PMBOT Funder Wallet Context Diagnostic 077G

- Status: `blocked_missing_wallet_address`
- Statuses: `blocked_missing_wallet_address`
- Market: `BTC`
- Strategy: `tiny-momentum`
- Mode: `funder wallet context diagnostic / redacted env metadata / no-live`
- raw secret output: `false`
- funder_auto_inferred: `false`
- funder_auto_copied_from_wallet: `false`
- signer instantiated: `false`
- order submission enabled: `false`
- allowed_for_live: `false`

## Wallet Context

- wallet_address_present: `false`
- funder_address_present: `false`
- signature_type_present: `false`
- private_key_present: `false`
- wallet_context_visible: `false`
- funder_relationship_status: `unknown_not_compared`
- suggested_safe_action: `set POLYMARKET_WALLET_ADDRESS before evaluating funder context`

## Environment Variables

- POLYMARKET_WALLET_ADDRESS: present=false redaction=missing length=0 fingerprint=missing preview=missing
- POLYMARKET_FUNDER_ADDRESS: present=false redaction=missing length=0 fingerprint=missing preview=missing
- POLYMARKET_SIGNATURE_TYPE: present=false redaction=missing length=0 fingerprint=missing preview=missing
- POLYMARKET_PRIVATE_KEY: present=false redaction=missing presence_only=true

## Blockers

- `blocked_missing_wallet_address` - POLYMARKET_WALLET_ADDRESS is missing in this runtime process context.
- `blocked_missing_signature_type` - POLYMARKET_SIGNATURE_TYPE is missing in this runtime process context.

## Safety

- this diagnostic reads only the explicit environment variable allowlist
- it does not read dotenv files, wallet files, browser profiles, or credential stores
- it does not modify environment variables or copy wallet address into funder address
- it does not call Polymarket API, instantiate signers, sign payloads, submit orders, or cancel orders
- POLYMARKET_PRIVATE_KEY is reported as presence only

## Safe Next Command

- `python -m pm_bot.operator_runner.funder_wallet_context_diagnostic --market BTC --strategy tiny-momentum --dry-run`

## Artifacts

- `pm_bot/trading_core/artifacts/local_environment_self_test_078g/funder_wallet_context_077g/funder_wallet_context_077g_result.json`
- `pm_bot/trading_core/artifacts/local_environment_self_test_078g/funder_wallet_context_077g/latest_funder_wallet_context_077g_status.json`
- `pm_bot/trading_core/artifacts/local_environment_self_test_078g/funder_wallet_context_077g/funder_wallet_context_077g_operator_summary.md`
