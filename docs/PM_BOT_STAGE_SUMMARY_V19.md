# PM Bot Stage Summary V19

Status: `crypto_numeric_guardrail_coverage_ready_for_review`

`PMBOT-BRAIN-007-CRYPTO-NUMERIC-GUARDRAIL-COVERAGE` adds fixture-only coverage around the extension guard threshold.

Run JSON:

```powershell
python pm_bot\scoring\run_crypto_numeric_guardrail_coverage.py
```

Run Markdown:

```powershell
python pm_bot\scoring\run_crypto_numeric_guardrail_coverage.py --markdown
```

## Coverage Scope

- just below 5.5% distance and yes price below 0.60
- just above 5.5% distance and yes price below 0.60
- below 5.5% distance and yes price above 0.60
- above 5.5% distance and yes price above 0.60
- clear bad overextended rich-price case
- clear legitimate candidate that remains a paper candidate

## Expected Result

- coverage cases: 6
- guardrail triggered: 2
- paper candidates preserved: 4
- watchlist caps: 2
- unexpected blocks: 0
- unexpected allows: 0

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
- no new validation layer

## Verification

- `python -m pytest pm_bot\scoring\tests -q`
- `python pm_bot\scoring\run_crypto_numeric_guardrail_coverage.py`
- `python pm_bot\scoring\run_crypto_numeric_guardrail_coverage.py --markdown`
- `python pm_bot\scoring\run_crypto_numeric_paper_replay.py`

## Next Step

`PMBOT-BRAIN-008-CRYPTO-NUMERIC-MULTI-ASSET-COVERAGE`: add ETH-side fixture-only guardrail coverage if review needs cross-asset symmetry checks.
