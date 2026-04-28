# PM Bot Stage Summary V14

Status: `crypto_numeric_review_table_ready_for_review`

`PMBOT-BRAIN-002-CRYPTO-NUMERIC-REVIEW-TABLE` adds a paper-only operator review table for deterministic crypto numeric scorer outputs.

Run JSON:

```powershell
python pm_bot\scoring\crypto_numeric_review_table.py pm_bot\scoring\expected_crypto_numeric_score_report.v1.json
```

Run Markdown:

```powershell
python pm_bot\scoring\crypto_numeric_review_table.py pm_bot\scoring\expected_crypto_numeric_score_report.v1.json --markdown
```

## Review Scope

- reads the offline scorer report
- emits per-market probabilities, buffered edge, liquidity/spread/risk gates, decision, and short reason
- includes grouped decision counts
- marks output as operator review only

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
- `python pm_bot\scoring\crypto_numeric_review_table.py pm_bot\scoring\expected_crypto_numeric_score_report.v1.json`
- `python pm_bot\scoring\crypto_numeric_review_table.py pm_bot\scoring\expected_crypto_numeric_score_report.v1.json --markdown`

## Next Step

`PMBOT-BRAIN-003-CRYPTO-NUMERIC-REASON-CODES`: add stable machine-readable reason codes for scorer and review-table outputs while preserving offline-only and no-runtime-wiring boundaries.
