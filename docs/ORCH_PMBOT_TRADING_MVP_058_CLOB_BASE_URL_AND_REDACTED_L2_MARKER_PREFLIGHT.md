# ORCH PMBOT Trading MVP 058: CLOB Base URL and Redacted L2 Marker Preflight

## Purpose

Task 058 adds a safe preflight surface for the Polymarket CLOB base URL and redacted L2 credential marker presence. It does not add live trading, authenticated network execution, wallet access, signing, balance reads, position reads, order submission, or order cancellation.

The preflight lets operators distinguish these states:

- CLOB base URL missing
- CLOB base URL configured and URL-shaped
- CLOB base URL invalid or unsafe-looking
- L2 marker variables missing
- L2 marker variables incomplete
- L2 marker variables present as redacted markers
- L2 marker values unsafe-looking and blocked
- no-order auth boundary mocked and still non-executable

## Safe Configuration Variables

The CLOB base URL is configured with:

```powershell
$env:PMBOT_POLYMARKET_CLOB_BASE_URL = "https://clob.polymarket.com"
```

The L2 marker variables are:

```powershell
$env:PMBOT_POLYMARKET_L2_API_KEY_PRESENT = "true"
$env:PMBOT_POLYMARKET_L2_API_SECRET_PRESENT = "true"
$env:PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT = "true"
```

Allowed marker values are:

- `true`
- `present`
- `1`

These marker variables are not API credentials. They only assert that an operator-side credential source exists outside PMBOT. PMBOT does not read, store, print, hash, derive, sign with, or use the raw API key, API secret, passphrase, private key, wallet, mnemonic, or seed phrase.

## Unsafe Marker Detection

If an L2 marker variable contains anything other than an allowed marker value, PMBOT treats it as unsafe raw credential material:

- `unsafe_raw_value_detected=true`
- the env var name is recorded
- the value is not printed
- the value is not stored
- no hash is stored
- no prefix or suffix is stored
- the no-order auth boundary remains blocked

## CLOB Base URL Validation

The production CLOB base URL is:

```text
https://clob.polymarket.com
```

Task 058 validates that the configured value is an HTTP or HTTPS URL with a host and no userinfo, query string, or fragment. A valid public URL may be emitted in artifacts because it is not a credential. Secret-looking CLOB URL values are blocked and not emitted.

## No-Order Boundary

The 058 no-order auth boundary remains a mocked plan by default. It uses marker presence only:

- method: `GET`
- POST/PUT/PATCH/DELETE: blocked
- authenticated request performed: `false`
- request headers materialized: `false`
- HMAC/signature generated: `false`
- order payload generated: `false`
- signed payload generated: `false`

## Remaining Blockers

Task 058 intentionally leaves these blockers active:

- authenticated request skipped by default
- order submission blocked
- order cancellation blocked
- signing blocked
- signed payload generation blocked
- wallet connection blocked
- private-key reads blocked
- balance reads blocked
- position reads blocked
- live execution blocked

## Safety Invariants

Every 058 output preserves:

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

## Commands

Default authenticated CLOB preflight:

```powershell
python -m pm_bot.operator_runner.authenticated_clob_preflight --market BTC --dry-run --mock-auth
```

Live connector preflight remains separate and review-only:

```powershell
python -m pm_bot.operator_runner.live_connector_preflight --market BTC --dry-run --network-check
```

Safe marker simulation without real secrets:

```powershell
$env:PMBOT_POLYMARKET_CLOB_BASE_URL="https://clob.polymarket.com"
$env:PMBOT_POLYMARKET_L2_API_KEY_PRESENT="true"
$env:PMBOT_POLYMARKET_L2_API_SECRET_PRESENT="true"
$env:PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT="true"
python -m pm_bot.operator_runner.authenticated_clob_preflight --market BTC --dry-run --mock-auth
Remove-Item Env:\PMBOT_POLYMARKET_CLOB_BASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:\PMBOT_POLYMARKET_L2_API_KEY_PRESENT -ErrorAction SilentlyContinue
Remove-Item Env:\PMBOT_POLYMARKET_L2_API_SECRET_PRESENT -ErrorAction SilentlyContinue
Remove-Item Env:\PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT -ErrorAction SilentlyContinue
```

## Artifacts

Task 058 writes:

- `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/clob_l2_marker_preflight_058_result.json`
- `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/clob_l2_marker_preflight_058_operator.md`
- `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/latest_clob_l2_marker_preflight_status_058.json`
- `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/clob_base_url_config_058.json`
- `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/redacted_l2_marker_presence_058.json`
- `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/unsafe_l2_marker_detection_058.json`
- `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/no_order_auth_boundary_plan_058.json`
- `pm_bot/trading_core/artifacts/clob_l2_marker_preflight_058/clob_l2_marker_blockers_058.json`

Artifacts must not contain raw API keys, raw secrets, passphrases, private keys, mnemonics, seed phrases, auth tokens, signed payloads, signatures, wallet credentials, fake order IDs, fake transaction hashes, fake fills, fake balances, fake PnL, or positions.
