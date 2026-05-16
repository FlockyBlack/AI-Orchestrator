# PMBOT Static Safety Invariant Report 060Q

- Status: `passed_with_warnings`
- Scope: `pm_bot`
- Mode: `static / review-only`
- Strict: `false`
- Artifacts included: `false`
- Scanned files: `372`
- Critical findings: `0`
- Warnings: `9`
- Allowed references: `0`

## Safety Invariants

- live execution blocked
- order submission blocked
- order cancellation blocked
- signing blocked
- signed payload generation blocked
- wallet usage blocked
- authenticated trading blocked
- resolved_blocker_count remains `0`

## Scanner Boundary

- repository worktree files only
- environment variables not read
- user home directories not read
- wallet files not read
- browser wallets not inspected
- network access not performed
- credential values not printed, hashed, stored, or transformed

## Findings

- `warning` `credential_name_reference` `pm_bot/llm/manual_packet_batch/692258_packet.v1.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/operator_runner/telegram_operator_control_bot.py`:740 - private key, API secret, passphrase, mnemonic, or seed variable name detected
- `warning` `credential_name_reference` `pm_bot/operator_runner/telegram_operator_control_bot.py`:753 - private key, API secret, passphrase, mnemonic, or seed variable name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/live_credentials_auth_boundary.py`:708 - private key, API secret, passphrase, mnemonic, or seed variable name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/live_credentials_auth_boundary.py`:710 - private key, API secret, passphrase, mnemonic, or seed variable name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/live_credentials_boundary.py`:556 - private key, API secret, passphrase, mnemonic, or seed variable name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/live_credentials_boundary.py`:558 - private key, API secret, passphrase, mnemonic, or seed variable name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/secret_boundary_policy.py`:1516 - private key, API secret, passphrase, mnemonic, or seed variable name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/secret_boundary_policy.py`:1518 - private key, API secret, passphrase, mnemonic, or seed variable name detected

## Operator Action

- review critical findings before any merge if `critical_count` is nonzero
- warning entries do not enable live/order/signing/wallet behavior
