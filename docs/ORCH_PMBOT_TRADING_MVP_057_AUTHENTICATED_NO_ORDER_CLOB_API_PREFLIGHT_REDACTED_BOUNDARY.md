# ORCH-PMBOT-TRADING-MVP-057 Authenticated No-Order CLOB API Preflight Redacted Boundary

## Scope

057 adds an authenticated no-order CLOB/API preflight boundary for PMBOT.

The operator command is:

```text
python -m pm_bot.operator_runner.authenticated_clob_preflight --market BTC --dry-run
```

Optional controls:

- `--mock-auth`
- `--auth-presence-only`
- `--no-order-auth-check`
- `--clob-base-url`
- `--artifacts-dir`
- `--json`

The command is dry-run, review-only, and preflight-only. It checks whether PMBOT can safely approach the Polymarket L2 auth layer while keeping live trading, signing, wallet use, balances, positions, and order endpoints blocked.

## Polymarket Auth Boundary

Polymarket CLOB auth has two separate layers:

- L1 private-key/EIP-712 auth can create or derive L2 API credentials.
- L2 API auth uses API key, secret, and passphrase material with HMAC-SHA256 style request authentication.
- Creating user orders still requires signed order payloads even when L2 headers are available.

057 does not cross the L1 boundary. It does not derive API keys, read private keys, connect wallets, sign EIP-712 messages, compute HMAC signatures, build signed order payloads, or post orders.

## Default Behavior

Default execution:

- checks redacted presence of L2 marker/config environment variables
- validates CLOB base URL shape without persisting the URL value
- builds a mocked no-order authenticated GET request plan
- verifies the plan allows only `GET`
- records `POST`, `PUT`, `PATCH`, and `DELETE` as blocked
- performs no real authenticated network request
- writes operator-safe artifacts
- exits successfully when missing configuration is an expected preflight blocker

Missing credentials, unsafe marker values, or missing/invalid CLOB base URL produce unresolved blockers. They do not crash the command unless there is a code error.

## Redacted L2 Credential Boundary

057 recognizes only these marker/config names:

- `PMBOT_POLYMARKET_CLOB_BASE_URL`
- `PMBOT_POLYMARKET_L2_API_KEY_PRESENT`
- `PMBOT_POLYMARKET_L2_API_SECRET_PRESENT`
- `PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT`

The L2 marker report may output only:

- `missing`
- `present_redacted`
- `unsafe_raw_value_detected=false`
- `unsafe_raw_value_detected=true`

It never prints, stores, hashes, truncates, or prefixes/suffixes raw API keys, secrets, passphrases, private keys, mnemonics, seed phrases, auth tokens, signatures, or signed payloads.

## No-Order / No-Signing Guarantees

057 preserves these hard boundaries:

- `execution_mode=preflight`
- `review_only=true`
- `preflight_only=true`
- `live_execution_approved=false`
- `canary_executable_now=false`
- `real_execution_available=false`
- `order_submission_enabled=false`
- `wallet_signing_enabled=false`
- `signing_enabled=false`
- `signed_payload_generation_enabled=false`
- `signed_order_generation_enabled=false`
- `authenticated_polymarket_enabled=false`
- `live_connector_enabled=false`
- `allowed_for_live=false`
- `resolved_blocker_count=0`

057 also records:

- `private_key_read=false`
- `l1_auth_attempted=false`
- `api_key_derivation_attempted=false`
- `wallet_connection_attempted=false`
- `signing_attempted=false`
- `signed_payload_generated=false`
- `order_submission_attempted=false`
- `order_cancellation_attempted=false`
- `balance_read_attempted=false`
- `position_read_attempted=false`
- `authenticated_request_performed=false`

## Generated Artifacts

Default artifact directory:

```text
pm_bot/trading_core/artifacts/authenticated_clob_preflight_057/
```

Generated artifacts:

- `authenticated_clob_preflight_057_result.json`
- `authenticated_clob_preflight_057_operator.md`
- `latest_authenticated_clob_preflight_status_057.json`
- `redacted_l2_credential_presence_057.json`
- `clob_base_url_validation_057.json`
- `auth_header_boundary_check_057.json`
- `no_order_authenticated_request_plan_057.json`
- `live_auth_readiness_blockers_057.json`

Artifacts must not contain raw API keys, raw secrets, passphrases, private keys, mnemonics, seed phrases, auth tokens, signed payloads, signatures, wallet credentials, fake order IDs, fake transaction hashes, fake fills, fake balances, fake PnL, or positions.

## Passive UI And Telegram

The passive Operator UI and Telegram summaries surface the latest authenticated CLOB preflight status when supplied in dashboard/context data.

They show:

- 057 status
- auth presence status
- CLOB base URL status
- blockers
- order submission blocked
- order cancellation blocked
- signing blocked
- wallet connection blocked
- balances blocked
- positions blocked
- live execution blocked

They do not add live approval buttons, order buttons, cancel buttons, wallet/signing controls, or credential displays.

## Remaining Blockers Before A First Live Tiny Order

057 does not make live order execution ready. Remaining blockers include:

- separate operator-approved task for any private-key or L1 auth handling
- separate operator-approved task for deriving or provisioning L2 credentials safely
- separate operator-approved task for real authenticated no-order GET, if needed
- separate operator-approved task for wallet connection and signer boundary review
- separate operator-approved task for signed order payload generation
- separate operator-approved task for order submission and cancellation boundaries
- balance and position read boundaries
- live approval and kill-switch verification
- final supervised tiny-order go/no-go gate

## Operator Setup Notes

Use marker/config environment variable names only. Do not paste secret values into Codex, ChatGPT, docs, issue comments, or artifacts.

Expected marker/config names:

- `PMBOT_POLYMARKET_CLOB_BASE_URL`
- `PMBOT_POLYMARKET_L2_API_KEY_PRESENT`
- `PMBOT_POLYMARKET_L2_API_SECRET_PRESENT`
- `PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT`

Safe marker values for the three L2 presence markers are simple booleans or marker words such as `true`, `present`, `configured`, or `present_redacted`. If a marker looks like raw credential material, 057 records `unsafe_raw_value_detected=true` without serializing the value and keeps live auth blocked.

The next operator action after 057 is:

```text
configure redacted L2 presence markers or review blockers; no live order available
```
