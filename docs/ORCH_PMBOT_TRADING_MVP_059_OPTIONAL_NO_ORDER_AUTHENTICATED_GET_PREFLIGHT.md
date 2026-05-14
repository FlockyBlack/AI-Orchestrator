# ORCH PMBOT Trading MVP 059: Optional No-Order Authenticated GET Preflight

## Purpose

Task 059 adds a supervised preflight boundary for an optional no-order authenticated GET check. It remains review-only, preflight-only, and live-blocked.

This task does not add live trading, order submission, order cancellation, signing, HMAC generation, wallet access, private-key reads, balance reads, position reads, fills, trades, fake execution records, schedulers, daemons, background workers, or autonomous trading loops.

## Default Behavior

The default authenticated CLOB preflight remains safe and mocked:

```powershell
python -m pm_bot.operator_runner.authenticated_clob_preflight --market BTC --dry-run
```

Task 059 writes a skipped/latest status when the optional flag is not requested. No authenticated request is sent.

The optional mocked no-order GET boundary is enabled with:

```powershell
python -m pm_bot.operator_runner.authenticated_clob_preflight --market BTC --dry-run --no-order-auth-get
```

This produces:

- `No-order auth GET: mocked`
- request method `GET`
- mocked response evidence
- `real_authenticated_get_performed=false`
- `auth_used=false`
- `credentials_used=redacted_presence_only`
- all order/signing/wallet/live execution flags `false`

## Real Auth Read-Only Opt-In

Real authenticated GET mode can only be requested with both:

```powershell
python -m pm_bot.operator_runner.authenticated_clob_preflight --market BTC --dry-run --no-order-auth-get --real-auth-read-only
```

and:

```powershell
$env:PMBOT_ALLOW_REAL_NO_ORDER_AUTH_GET = "true"
```

If `--real-auth-read-only` is used without `--no-order-auth-get`, the task fails closed with:

- `real_auth_read_only_requires_no_order_auth_get`

If the env opt-in marker is missing, the task fails closed with:

- `real_no_order_auth_get_not_enabled`

The opt-in marker value is never written to artifacts.

## Safe Endpoint Selection Rule

Only `GET` is allowed. `POST`, `PUT`, `PATCH`, and `DELETE` are blocked.

The mock-only safe endpoint boundary is:

```text
/auth/no-order-boundary/mock-get
```

Real network mode has no allowlisted endpoint in this task. Current Polymarket CLOB documentation describes public CLOB read endpoints as no-auth and L2 authentication as used for trading/user-scope operations such as open orders, balances/allowances, and signed orders. Because no clearly safe no-order authenticated GET endpoint is available, real mode fails closed with:

- `no_clearly_safe_authenticated_get_endpoint`

Reference: [Polymarket CLOB authentication documentation](https://docs.polymarket.com/api-reference/authentication).

## Forbidden Endpoints

Task 059 blocks endpoint paths that match private, trading, account, wallet, or execution scopes, including:

- order creation
- order cancellation
- open orders when they require trading scope
- balances
- positions
- fills
- trades that imply user/private execution records
- wallet
- allowance
- approvals
- API key creation or derivation
- heartbeat

The denylist is enforced before any real request could be considered.

## Redaction Guarantees

Task 059 artifacts never store:

- raw API keys
- raw API secrets
- passphrases
- private keys
- mnemonics
- seed phrases
- auth tokens
- signed payloads
- signatures
- wallet material

The artifacts only record redacted presence and boundary state:

- `credentials_used=redacted_presence_only`
- `credentials_values_exposed=false`
- `private_key_read=false`
- `signing_attempted=false`
- `signed_payload_generated=false`
- `auth_used=false` unless a future clearly safe real GET is actually performed

## Why This Still Does Not Enable Live Trading

Task 059 cannot place or cancel orders because it never enables order methods, never generates payloads, and never exposes POST/PUT/PATCH/DELETE paths.

It cannot sign because it never reads private keys, never derives API keys, and never creates HMAC or wallet signatures.

It cannot inspect wallet/account execution state because balance, position, fill, trade, allowance, approval, and wallet endpoints are blocked.

It cannot run autonomously because no scheduler, daemon, background worker, or recursive trading loop is added.

## Artifacts

Task 059 writes:

- `pm_bot/trading_core/artifacts/no_order_auth_get_preflight_059/no_order_auth_get_preflight_059_result.json`
- `pm_bot/trading_core/artifacts/no_order_auth_get_preflight_059/no_order_auth_get_preflight_059_operator.md`
- `pm_bot/trading_core/artifacts/no_order_auth_get_preflight_059/latest_no_order_auth_get_preflight_status_059.json`
- `pm_bot/trading_core/artifacts/no_order_auth_get_preflight_059/no_order_auth_get_request_plan_059.json`
- `pm_bot/trading_core/artifacts/no_order_auth_get_preflight_059/no_order_auth_get_endpoint_validation_059.json`
- `pm_bot/trading_core/artifacts/no_order_auth_get_preflight_059/no_order_auth_get_response_evidence_059.json` when mocked evidence is generated
- `pm_bot/trading_core/artifacts/no_order_auth_get_preflight_059/no_order_auth_get_blockers_059.json`

## Remaining Blockers Before Signer, Order, or Tiny Canary

These blockers remain active:

- no clearly safe real no-order authenticated GET endpoint is allowlisted
- L1 private-key reads remain blocked
- L2 HMAC/signature generation remains blocked
- API key creation/derivation remains blocked
- order submission remains blocked
- order cancellation remains blocked
- wallet connection remains blocked
- balance and position reads remain blocked
- live execution remains blocked
- operator approval cannot enable live execution in this task

## Safety Invariants

Every 059 output preserves:

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
