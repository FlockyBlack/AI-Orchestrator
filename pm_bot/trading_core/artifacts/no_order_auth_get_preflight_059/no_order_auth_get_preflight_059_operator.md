# PMBOT Optional No-Order Authenticated GET Preflight 059

- Status: `no_order_auth_get_preflight_mocked_live_blocked`
- Market: `BTC`
- Mode: `preflight / review-only`
- execution_mode: `preflight`
- review_only: `true`
- preflight_only: `true`

## Request Boundary

- No-order auth GET status: `mocked`
- No-order auth GET requested: `true`
- Real auth read-only requested: `false`
- Real auth opt-in present: `false`
- Request method: `GET`
- Endpoint path sanitized: `/auth/no-order-boundary/mock-get`
- Endpoint safe for no-order check: `true`
- Endpoint blocked reason: ``
- Opt-in blocker reason: ``
- Allowed method: `GET`
- Blocked methods: `POST, PUT, PATCH, DELETE`

## Evidence

- Real authenticated GET performed: `false`
- Status code: `None`
- Auth used: `false`
- Credentials used: `redacted_presence_only`
- Credential values exposed: `false`
- Header values stored: `false`
- Signed payload generated: `false`

## Safety

- order submission blocked
- order cancellation blocked
- signing blocked
- wallet connection blocked
- balances blocked
- positions blocked
- live execution blocked
- private_key_read: `false`
- signing_attempted: `false`
- signed_payload_generated: `false`
- order_submission_attempted: `false`
- order_cancellation_attempted: `false`
- balance_read_attempted: `false`
- position_read_attempted: `false`
- wallet_connection_attempted: `false`
- live_execution_approved: `false`
- allowed_for_live: `false`
- resolved_blocker_count: `0`

## Blockers

- Order submission remains blocked.
- Order cancellation remains blocked.
- Signing, HMAC generation, and signed payload generation remain blocked.
- Wallet connection and private-key reads remain blocked.
- Balance reads remain blocked.
- Position reads remain blocked.
- Live execution remains blocked and allowed_for_live remains false.

## Latest Status

- Latest status path: `pm_bot/trading_core/artifacts/no_order_auth_get_preflight_059/latest_no_order_auth_get_preflight_status_059.json`
