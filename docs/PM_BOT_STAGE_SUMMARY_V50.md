# PM Bot Stage Summary V50

## Scope

PMBOT-BRAIN-038 added optional threshold-hit review artifact output to the manual paper operator cycle.

## Result

- Added `--include-threshold-hit-review` to `pm_bot/paper/run_manual_paper_operator_cycle.py`.
- Added `--threshold-reference-context <path>` and `--threshold-decision-policy <path>` for the optional review.
- Default unflagged JSON and Markdown output remains unchanged.
- Flagged runs reuse the existing threshold-hit review table logic against `local_snapshots/polymarket_markets_active_500_001.json`.
- When a run directory is created by `--write-run` or `--commit-state`, the operator cycle writes `threshold_hit_review.json` and `threshold_hit_review.md` alongside normal run artifacts.
- When no run directory is created, flagged stdout includes only the threshold-hit summary fields and compact candidate rows.
- Added locked expected JSON and Markdown outputs for the flagged operator-cycle path.
- Added tests for deterministic flagged stdout, Markdown, run artifact writing, state mutation avoidance, normal commit-state equivalence, lower-level threshold-hit review, policy scenarios, lifecycle gates, and canonical fixture workspace immutability.

## Threshold Summary

- threshold_hit_review_included: true when explicitly requested
- threshold_hit_candidates: 3
- threshold_hit_watchlist_count: 2
- threshold_hit_policy_blocked_count: 1
- threshold_hit_paper_candidate_count: 0
- threshold_hit_paper_orders_created: 0
- threshold_hit_artifact_paths: written only for run-directory executions

## Safety

- Offline local fixture reads only.
- Paper mode only.
- No live price fetching.
- No network or API calls.
- No credentials, wallet, private key, signing, real order, or live trading path.
- No dispatcher, runtime wiring, prompt automation, paper order planning, paper order creation, risk-limit behavior, or current_state decision behavior changes.
- Threshold-hit rows remain separate from the existing above/below crypto numeric scorer runtime behavior.

## Verification

- `python -m pytest pm_bot\paper\tests\test_run_manual_paper_operator_cycle.py -q`
- `python -m pytest pm_bot\scoring\tests pm_bot\paper\tests -q`
- `python pm_bot\paper\run_manual_paper_operator_cycle.py`
- `python pm_bot\paper\run_manual_paper_operator_cycle.py --markdown`
- `python pm_bot\paper\run_manual_paper_operator_cycle.py --include-threshold-hit-review --threshold-reference-context pm_bot\paper\threshold_hit_reference_context.v1.json --threshold-decision-policy pm_bot\paper\threshold_hit_decision_policy.v1.json`
- `python pm_bot\paper\run_manual_paper_operator_cycle.py --include-threshold-hit-review --threshold-reference-context pm_bot\paper\threshold_hit_reference_context.v1.json --threshold-decision-policy pm_bot\paper\threshold_hit_decision_policy.v1.json --markdown`
- `python pm_bot\paper\run_crypto_threshold_hit_review_table.py --reference-context pm_bot\paper\threshold_hit_reference_context.v1.json --decision-policy pm_bot\paper\threshold_hit_decision_policy.v1.json --markdown`
- `python pm_bot\paper\run_crypto_threshold_hit_policy_scenarios.py`
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py`

All verification checks passed.
