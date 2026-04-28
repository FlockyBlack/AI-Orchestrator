# PM Bot Stage Summary V47

## Scope

PMBOT-BRAIN-035 added deterministic offline/local reference price context support for the crypto threshold-hit review table.

## Result

- Added `pm_bot/paper/threshold_hit_reference_context.v1.json` with manual BTC and ETH fixture prices.
- Added `--reference-context <path>` to `pm_bot/paper/run_crypto_threshold_hit_review_table.py`.
- Default behavior without `--reference-context` remains conservative: missing reference prices remain, paper candidates remain zero, and paper orders remain zero.
- With reference context, matching assets populate `current_reference_price`, `reference_price_captured_at`, and `reference_price_source`.
- With reference context, rows compute `distance_to_target_pct`, `target_multiple`, and by-date `time_to_deadline_days`.
- By-date rows with reference prices become `reviewable` watchlist rows, not paper candidates.
- Before-event rows remain gated by `before_event_requires_event_model`.

## Safety

- Offline fixture reads only.
- No live price fetching.
- No network or API calls.
- No credentials, wallet, private key, signing, real order, or live trading path.
- No dispatcher, runtime wiring, prompt automation, or paper order creation changes.
- Threshold-hit rows remain separate from the existing above/below crypto numeric scorer.

## Verification

- `python -m pytest pm_bot\scoring\tests pm_bot\paper\tests -q`
- `python pm_bot\paper\run_crypto_threshold_hit_review_table.py`
- `python pm_bot\paper\run_crypto_threshold_hit_review_table.py --markdown`
- `python pm_bot\paper\run_crypto_threshold_hit_review_table.py --reference-context pm_bot\paper\threshold_hit_reference_context.v1.json`
- `python pm_bot\paper\run_crypto_threshold_hit_review_table.py --reference-context pm_bot\paper\threshold_hit_reference_context.v1.json --markdown`
- `python pm_bot\paper\run_crypto_threshold_hit_triage_report.py --source C:\Users\OpenC\Documents\AI-Orchestrator\local_snapshots\polymarket_markets_active_500_001.json --markdown`
- `PYTHONIOENCODING=utf-8 python pm_bot\paper\run_real_market_triage_report.py --source C:\Users\OpenC\Documents\AI-Orchestrator\local_snapshots\polymarket_markets_active_500_001.json --markdown`
- `python pm_bot\paper\run_manual_paper_operator_cycle.py`
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py`

All verification checks passed.
