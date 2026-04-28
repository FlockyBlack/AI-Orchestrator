# PM Bot Stage Summary V15

Status: `crypto_numeric_paper_order_plan_ready_for_review`

`PMBOT-BRAIN-003-CRYPTO-NUMERIC-PAPER-ORDER-PLAN` adds a deterministic offline/paper order plan generator for crypto numeric review outputs.

Run JSON:

```powershell
python pm_bot\scoring\crypto_numeric_paper_order_plan.py pm_bot\scoring\expected_crypto_numeric_review_table.v1.json
```

Run Markdown:

```powershell
python pm_bot\scoring\crypto_numeric_paper_order_plan.py pm_bot\scoring\expected_crypto_numeric_review_table.v1.json --markdown
```

## Plan Scope

- reads the offline crypto numeric review table
- creates paper limit-order plan entries only for rows that clear deterministic paper limits
- creates no-action entries for watchlist and reject rows
- applies max per-market paper notional, max total paper notional, minimum edge, liquidity, spread, and risk gates

## Safety Boundary

- offline-only
- paper-only
- no network/API
- no credentials
- no wallet/private keys/signing
- no real orders
- no live trading
- no runtime wiring
- no dispatcher/run_codex
- no prompt automation

## Verification

- `python -m pytest pm_bot\scoring\tests -q`
- `python pm_bot\scoring\crypto_numeric_paper_order_plan.py pm_bot\scoring\expected_crypto_numeric_review_table.v1.json`
- `python pm_bot\scoring\crypto_numeric_paper_order_plan.py pm_bot\scoring\expected_crypto_numeric_review_table.v1.json --markdown`

## Next Step

`PMBOT-BRAIN-004-CRYPTO-NUMERIC-PAPER-PLAN-AUDIT`: add a deterministic paper-plan audit that validates generated plan entries against the risk limits and safety flags.
