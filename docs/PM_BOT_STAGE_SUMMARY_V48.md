# PM Bot Stage Summary V48

## Scope

PMBOT-BRAIN-036 added opt-in deterministic offline/paper conservative decision policy support for the crypto threshold-hit review table.

## Result

- Added `pm_bot/paper/threshold_hit_decision_policy.v1.json` with conservative thresholds and `allow_paper_candidates=false`.
- Added `--decision-policy <path>` to `pm_bot/paper/run_crypto_threshold_hit_review_table.py`.
- Preserved BRAIN-035 behavior when `--decision-policy` is omitted.
- Policy mode runs after triage and reference-context enrichment.
- Policy-mode rows include `decision_policy_version`, `policy_checks`, `passed_policy_checks`, `failed_policy_checks`, `reason_codes`, and `human_review_note`.
- Policy-mode summaries include `decision_policy_used`, `policy_blocked_count`, and `policy_reason_counts`.
- With the default policy and reference context, the real local snapshot produces 3 threshold-hit candidates: 2 watchlist rows, 1 policy-blocked before-event row, 0 paper candidates, and 0 paper orders.
- A test-only policy with `allow_paper_candidates=true` can label a passing fixture row as `paper_candidate` without creating paper orders.

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
- `python pm_bot\paper\run_crypto_threshold_hit_review_table.py --reference-context pm_bot\paper\threshold_hit_reference_context.v1.json --decision-policy pm_bot\paper\threshold_hit_decision_policy.v1.json`
- `python pm_bot\paper\run_crypto_threshold_hit_review_table.py --reference-context pm_bot\paper\threshold_hit_reference_context.v1.json --decision-policy pm_bot\paper\threshold_hit_decision_policy.v1.json --markdown`
- `python pm_bot\paper\run_crypto_threshold_hit_triage_report.py --source C:\Users\OpenC\Documents\AI-Orchestrator\local_snapshots\polymarket_markets_active_500_001.json --markdown`
- `PYTHONIOENCODING=utf-8 python pm_bot\paper\run_real_market_triage_report.py --source C:\Users\OpenC\Documents\AI-Orchestrator\local_snapshots\polymarket_markets_active_500_001.json --markdown`
- `python pm_bot\paper\run_manual_paper_operator_cycle.py`
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py`

All verification checks passed.
