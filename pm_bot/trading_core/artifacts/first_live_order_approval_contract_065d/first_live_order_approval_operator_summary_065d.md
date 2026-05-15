# PMBOT First Live Order Approval Contract 065D

- Status: `approval_contract_defined_execution_blocked`
- Market: `BTC`
- Strategy: `tiny-momentum`
- Mode: `definition-only / no execution`
- approval_contract_executable: `false`
- allowed_for_live: `false`
- no approval means no execution

## Exact Required Approval Text

```text
STOP - REAL MONEY RISK. I, the operator, explicitly approve ONE FUTURE SUPERVISED TINY LIVE ORDER for BTC using strategy tiny-momentum only, capped at 1.00 USD notional, expiring 15 minutes after my approval, one-shot only with no repeats, no scheduler, no daemon, no background loop, and revocable by me before use. I understand no approval means no execution, and this 065D approval contract itself cannot execute, connect a wallet, instantiate a signer, sign payloads, generate signed orders, submit orders, cancel orders, make authenticated trading calls, read credentials, or create fills/PnL.
```

## Scope

- allowed_markets: `['BTC']`
- allowed_strategies: `['tiny-momentum']`
- scope_valid: `true`

## Limits

- max_notional_usd: `1.0`
- max_orders_per_day: `1`
- one_shot_only: `true`
- no scheduler, daemon, background loop, or autonomous repeat

## Timeout

- approval_expires: `true`
- approval_timeout_minutes: `15`
- expired_approval_blocks_future_use: `true`

## Revocation

- revocable_by_operator: `true`
- revocation_effect: `revoked approval blocks any later use of this approval text`

## Audit Template

- exact approval text copy
- operator approval timestamp
- revocation status checked before any separate future use
- BTC/tiny-momentum scope check
- 1.00 USD maximum notional check
- one-shot consumption note if a separate future task ever uses the approval
- timeout check no later than 15 minutes after approval

## Safety Boundary

- this contract records no operator approval
- this contract cannot perform a live action
- no wallet connection, signer instantiation, signed payload, order action, authenticated trading call, credential read, fill, or PnL is produced
