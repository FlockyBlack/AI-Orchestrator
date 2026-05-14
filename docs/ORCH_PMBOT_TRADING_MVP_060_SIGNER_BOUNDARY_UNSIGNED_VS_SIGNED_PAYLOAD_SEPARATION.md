# ORCH-PMBOT-TRADING-MVP-060 Signer Boundary and Unsigned Plan Separation

## Purpose

060 adds a review-only signer boundary preflight for PMBOT. It separates the existing paper intent flow from any future live-order machinery by introducing explicit, non-executable artifacts for:

- paper order intent
- live candidate order intent
- unsigned order payload plan
- signing boundary status
- signed payload availability
- order submission availability

This task does not enable live trading. It creates only local artifacts and passive UI/Telegram summaries. The command is:

```powershell
python -m pm_bot.operator_runner.signer_boundary_preflight --market BTC --strategy tiny-momentum --dry-run
```

## Why 060 Does Not Enable Live Trading

The 060 preflight is hard-coded to `execution_mode=preflight`, `review_only=true`, and `preflight_only=true`. It does not import wallet libraries, instantiate a signer, derive API credentials, perform authenticated requests, build a real signable CLOB payload, submit orders, cancel orders, read balances, or read positions.

All execution-enabling flags remain false, including:

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

## Artifact Separation

Paper intent is the existing paper-mode artifact from task 053 or 054. It is review-only and not a live order.

Live candidate intent is a non-executable review object derived from a paper intent. It copies only safe candidate fields such as market, strategy, outcome, side, limit price, size, and notional. It is not an execution identifier, not live approval, and not order submission.

Unsigned order payload plan is schema-only. It records which fields a future supervised boundary would need to review, but it does not materialize a real CLOB payload and is explicitly `unsigned_plan_is_executable=false`.

Signing boundary status is blocked. It records `signer_config_present=false`, `private_key_read=false`, `wallet_connection_attempted=false`, `signer_instantiated=false`, and `signing_attempted=false`.

Signed payload availability is unavailable. It records `signed_payload_generated=false` and `signed_payload_available=false`.

Order submission availability is blocked. It records `order_submission_attempted=false`, `order_submission_available=false`, `order_cancellation_attempted=false`, `balance_read_attempted=false`, and `position_read_attempted=false`.

## No-Key and No-Signer Guarantees

060 does not read private-key environment variables, seed phrases, mnemonics, wallet files, API secrets, passphrases, or auth tokens. It does not expose credential values in artifacts. It does not use wallet or signer libraries. It does not perform EIP-712 signing or any CLOB order-builder operation.

The generated artifacts intentionally contain no raw private keys, seed phrases, mnemonics, signatures, signed payload values, order IDs, transaction hashes, fills, balances, positions, or PnL.

## Artifacts

Default artifact directory:

```text
pm_bot/trading_core/artifacts/signer_boundary_preflight_060/
```

Required artifacts:

- `signer_boundary_preflight_060_result.json`
- `signer_boundary_preflight_060_operator.md`
- `latest_signer_boundary_preflight_status_060.json`
- `live_candidate_order_intent_060.json`
- `unsigned_order_payload_plan_060.json`
- `signing_boundary_status_060.json`
- `signed_payload_availability_060.json`
- `order_submission_availability_060.json`
- `signer_boundary_blockers_060.json`

## Remaining Blockers Before First Tiny Supervised Live Order

- A separate operator-approved task must define a safe signer configuration contract.
- Private-key and wallet handling remain completely absent.
- No signer can be instantiated.
- No signed payload generation path exists.
- No real CLOB order payload builder is enabled.
- No order submission or cancellation path exists.
- No balance or position read path exists.
- Live execution approval remains false.
- A future task must separately approve and validate any live-only boundary relaxation.

## Operator Next Steps

Review the signer boundary only. There is no live order available from 060.

The next useful operator action is to inspect:

- source paper intent path
- candidate intent summary
- unsigned schema-only plan
- signer blocked status
- signed payload unavailable status
- order submission blocked status
- blocker list

Do not treat any 060 artifact as live-trading advice, live approval, a signable payload, or an executable order.
