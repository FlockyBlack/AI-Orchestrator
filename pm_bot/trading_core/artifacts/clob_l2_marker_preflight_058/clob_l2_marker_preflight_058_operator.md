# PMBOT CLOB Base URL and Redacted L2 Marker Preflight 058

- Status: `clob_l2_marker_preflight_fail_closed`
- Market: `BTC`
- Mode: `preflight / review-only`
- execution_mode: `preflight`
- review_only: `true`
- preflight_only: `true`

## CLOB Base URL

- Configured: `false`
- Status: `missing`
- Valid: `false`
- Production URL: `false`

## Redacted L2 Markers

- Marker status: `missing`
- Marker set complete: `false`
- Configured markers: `0`
- Missing markers: `3`
- Unsafe raw marker detected: `false`
- Marker values stored: `false`
- Marker value hashes stored: `false`

## No-Order Boundary

- Plan status: `blocked`
- Auth boundary mock checked: `false`
- No-order auth plan ready: `false`
- Authenticated request performed: `false`
- Authenticated request skipped by default: `true`
- Allowed methods in plan: `GET`
- Blocked methods in plan: `POST, PUT, PATCH, DELETE`

## Safety

- order submission blocked
- order cancellation blocked
- signing blocked
- signed payload generation blocked
- wallet connection blocked
- balances blocked
- positions blocked
- live execution blocked
- authenticated_polymarket_enabled: `false`
- live_connector_enabled: `false`
- allowed_for_live: `false`
- resolved_blocker_count: `0`

## Blockers

- CLOB base URL is missing.
- All L2 marker variables are missing.
- missing_l2_marker:PMBOT_POLYMARKET_L2_API_KEY_PRESENT
- missing_l2_marker:PMBOT_POLYMARKET_L2_API_SECRET_PRESENT
- missing_l2_marker:PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT
- No-order authenticated GET boundary is not ready with safe URL and redacted markers.
- Authenticated request is skipped by default in task 058.
- Order submission remains blocked.
- Order cancellation remains blocked.
- Signing and signed payload generation remain blocked.
- Wallet connection and private-key reads remain blocked.
- Balance reads remain blocked.
- Position reads remain blocked.
- Live execution remains blocked and allowed_for_live remains false.

## Latest Status

- Latest status path: `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/latest_clob_l2_marker_preflight_status_058.json`
