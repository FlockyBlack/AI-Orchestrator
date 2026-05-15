# PMBOT CLOB L2 Auth Read-Only Probe 067C

- Status: `blocked_missing_l2_credentials`
- Market: `BTC`
- Strategy: `tiny-momentum`
- execution_mode: `clob_l2_auth_readonly_probe`
- probe_is_readonly: `true`
- allowed_for_live: `false`
- private_key_read: `false`
- signer_instantiated: `false`

## Credential Boundary

- Credential presence status: `missing`
- Configured L2 env count: `0`
- Missing L2 env count: `3`
- Env vars read: `POLYMARKET_API_KEY`, `POLYMARKET_API_SECRET`, `POLYMARKET_API_PASSPHRASE`
- Private key, wallet, signature type, and funder env vars read: `false`
- Raw credential values emitted: `false`

## SDK Probe

- SDK status: `not_checked_missing_credentials`
- Selected SDK: `not_available`
- Auth verified: `false`
- Read-only probe attempted: `false`
- Read-only probe performed: `false`
- Open order count: `not_available`
- Balance allowance probe: `not_available`

## Attempts

- none

## Safety

- no order submission
- no order cancellation
- no order signing
- no signer instantiation
- no wallet connection
- no POST/PUT/PATCH/DELETE trading call from PMBOT code
- SDK responses are summarized and redacted
- allowed_for_live remains `false`

## Blockers

- `missing_l2_api_credentials` - One or more required L2 API credential env vars are missing; private key fallback is forbidden.
