# PMBOT Static Safety Invariant Report 060Q

- Status: `passed_with_warnings`
- Scope: `pm_bot`
- Mode: `static / review-only`
- Strict: `false`
- Artifacts included: `true`
- Scanned files: `357`
- Critical findings: `0`
- Warnings: `58`
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
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/authenticated_clob_preflight_057/authenticated_clob_preflight_057_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/authenticated_clob_preflight_057/authenticated_clob_preflight_057_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/authenticated_clob_preflight_057/redacted_l2_credential_presence_057.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/authenticated_clob_preflight_057/redacted_l2_credential_presence_057.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/clob_base_url_config_058.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/clob_base_url_config_058.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/clob_l2_marker_preflight_058_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/clob_l2_marker_preflight_058_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/clob_l2_marker_preflight_058_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/clob_l2_marker_preflight_058_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/redacted_l2_marker_presence_058.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/redacted_l2_marker_presence_058.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_drill_052_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_drill_052_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_drill_052_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_drill_052_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_drill_052_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_drill_052_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_drill_052_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_drill_052_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_drill_052_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_drill_052_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_drill_052_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected
- `warning` `credential_name_reference` `pm_bot/trading_core/artifacts/paper_canary_drill_052/paper_canary_drill_052_result.json` - private key, API secret, passphrase, mnemonic, or seed field name detected

- 33 additional findings are in the JSON artifact.

## Operator Action

- review critical findings before any merge if `critical_count` is nonzero
- warning entries do not enable live/order/signing/wallet behavior
