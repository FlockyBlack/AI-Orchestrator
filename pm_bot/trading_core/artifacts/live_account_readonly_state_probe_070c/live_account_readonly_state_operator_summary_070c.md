# PMBOT Live Account Read-Only State Probe 070C

- Status: `blocked_missing_l2_credentials`
- Market: `BTC`
- Strategy: `tiny-momentum`
- execution_mode: `live_account_readonly_state_probe`
- probe_is_readonly: `true`
- allowed_for_live: `false`
- private_key_read: `false`
- signer_instantiated: `false`

## Credential Boundary

- L2 credential presence status: `missing`
- Configured L2 env count: `0`
- Missing L2 env count: `3`
- Env vars used for auth: `POLYMARKET_API_KEY`, `POLYMARKET_API_SECRET`, `POLYMARKET_API_PASSPHRASE`
- Wallet, signature type, and funder are presence/redaction diagnostics only
- Private key and wallet private-key env vars read: `false`
- Raw credential values emitted: `false`

## Redacted Account Status

- Wallet address: `missing`
- Signature type: `missing`
- Funder address: `missing`

## SDK Account State Probe

- SDK status: `not_checked_missing_credentials`
- Selected SDK: `not_available`
- Read-only probe attempted: `false`
- Read-only probe performed: `false`
- Open orders status: `not_available`
- Open order count: `not_available`
- Balance/allowance status: `not_available`
- Balance/allowance availability: `not_available`

## Attempts

- none

## Safety

- no order submission
- no order cancellation
- no order signing
- no signer instantiation
- no private-key read
- no wallet connection
- no POST/PUT/PATCH/DELETE trading call from PMBOT code
- SDK responses are summarized and redacted
- allowed_for_live remains `false`

## Blockers

- `missing_l2_api_credentials` - One or more required L2 API credential env vars are missing; private key fallback is forbidden.
