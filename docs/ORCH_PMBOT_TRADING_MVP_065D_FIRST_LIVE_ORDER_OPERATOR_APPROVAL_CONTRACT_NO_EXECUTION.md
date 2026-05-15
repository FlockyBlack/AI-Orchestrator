# ORCH-PMBOT-TRADING-MVP-065D First Live Order Operator Approval Contract No Execution

## Purpose

This task defines the non-executable operator approval contract for a possible future first supervised tiny live order. It does not record an approval and it cannot execute anything.

The contract is safe to generate with:

```text
python -m pm_bot.operator_runner.first_live_order_approval_contract --market BTC --strategy tiny-momentum --dry-run
```

## Exact Required Approval Text

Any separate future task that seeks operator approval must require this exact text, unchanged:

```text
STOP - REAL MONEY RISK. I, the operator, explicitly approve ONE FUTURE SUPERVISED TINY LIVE ORDER for BTC using strategy tiny-momentum only, capped at 1.00 USD notional, expiring 15 minutes after my approval, one-shot only with no repeats, no scheduler, no daemon, no background loop, and revocable by me before use. I understand no approval means no execution, and this 065D approval contract itself cannot execute, connect a wallet, instantiate a signer, sign payloads, generate signed orders, submit orders, cancel orders, make authenticated trading calls, read credentials, or create fills/PnL.
```

## Scope And Limits

- Default and allowed market: `BTC`
- Default and allowed strategy: `tiny-momentum`
- Maximum notional: `1.00` USD
- Maximum orders per day: `1`
- Approval timeout: `15` minutes after approval
- One-shot only: `true`
- Reuse allowed: `false`
- Autonomous repeat allowed: `false`
- Scheduler, daemon, background loop: forbidden
- Operator revocation before use or expiry: allowed

## Safety Boundary

The implementation is intentionally definition-only:

- `approval_contract_executable=false`
- `allowed_for_live=false`
- `live_execution_approved=false`
- `operator_approval_recorded=false`
- `contract_can_execute=false`
- no approval means no execution
- no credential values are read or serialized
- no wallet connection, signer instantiation, signed payload generation, order submission, order cancellation, authenticated trading call, fill, or PnL is produced
- no scheduler, daemon, background worker, or autonomous loop is added

This task only creates a contract. A separate future operator-approved task would be required before any live action could even be considered.

## Artifacts

Default artifact directory:

```text
pm_bot/trading_core/artifacts/first_live_order_approval_contract_065d/
```

Generated artifacts:

- `first_live_order_approval_contract_065d_result.json`
- `latest_first_live_order_approval_contract_status_065d.json`
- `first_live_order_required_approval_text_065d.json`
- `first_live_order_approval_scope_065d.json`
- `first_live_order_approval_limits_065d.json`
- `first_live_order_approval_revocation_policy_065d.json`
- `first_live_order_approval_timeout_policy_065d.json`
- `first_live_order_approval_audit_record_template_065d.json`
- `first_live_order_approval_operator_summary_065d.md`

## Audit Template

The audit template requires future operator artifacts without inventing execution data:

- exact approval text copy
- operator approval timestamp
- revocation status checked before any separate future use
- BTC/tiny-momentum scope check
- 1.00 USD maximum notional check
- one-shot consumption note if a separate future task ever uses the approval
- timeout check no later than 15 minutes after approval

The 065D artifacts intentionally contain no fake execution IDs, fills, balances, positions, or PnL.

## Validation

Focused validation:

```text
python -m pytest pm_bot/tests/test_first_live_order_approval_contract_065d.py
```

Full task validation also runs the 064 readiness gate tests, 060Q static safety tests, all PMBOT tests, compile checks, the 065D CLI dry run, the static safety invariant dry run, and Git whitespace checks.
