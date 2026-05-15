# PMBOT Live Read-Only Status Aggregator 071B

- Status: `live_readonly_status_aggregated`
- Market: `BTC`
- Strategy: `tiny-momentum`
- execution_mode: `live_readonly_status_aggregator`
- local_artifact_read_only: `true`
- allowed_for_live: `false`
- private_key_read: `false`
- network_access_performed: `false`

## Aggregated Status

- `l2_auth_status` = `blocked_missing_l2_credentials`
- `open_orders_status` = `not_available`
- `balance_status` = `not_available`
- `allowance_status` = `not_available`
- `wallet_address_status` = `missing`
- `funder_status` = `missing`
- `signature_type_status` = `missing`

## Sources

- `clob_l2_auth_readonly_probe_067c` available=`true` path=`pm_bot/trading_core/artifacts/clob_l2_auth_readonly_probe_067c/latest_clob_l2_auth_readonly_probe_status_067c.json`
- `live_account_readonly_state_probe_070c` available=`false` path=`none`
- `telegram_wallet_auth_status_067e` available=`true` path=`pm_bot/trading_core/artifacts/telegram_wallet_auth_status_067e/latest_telegram_wallet_auth_status_067e.json`

## Safety

- no network call is made by this aggregator
- no environment value is read
- no private key, wallet file, or credential store is read
- no order write, cancellation, signing, signer, or wallet connection path is added
- no fake balances, PnL, order rows, fills, or positions are created
- absent inputs remain `unknown`
