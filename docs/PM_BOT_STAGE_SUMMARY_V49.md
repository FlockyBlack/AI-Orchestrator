# PM Bot Stage Summary V49

## Scope

PMBOT-BRAIN-037 added deterministic offline/paper scenario coverage for crypto threshold-hit decision policy boundaries.

## Result

- Added `pm_bot/paper/threshold_hit_policy_scenarios.v1.json` with 12 local scenario cases.
- Added `pm_bot/paper/run_crypto_threshold_hit_policy_scenarios.py` with JSON output by default and Markdown output via `--markdown`.
- Added locked expected JSON and Markdown outputs for the scenario suite.
- Added tests proving deterministic JSON/Markdown, policy-reason coverage, expected-decision pass/fail status, zero paper orders, and existing regression commands.
- Scenario coverage exercises paper-candidate-disabled behavior, Yes price limit, distance limit, liquidity minimum, deadline boundaries, before-event missing model, missing reference price, missing Yes price, missing liquidity, missing deadline, non-future deadline, and unsupported threshold-hit rejection.
- The runner reuses existing threshold-hit triage, review, reference-context, and decision-policy logic.

## Scenario Summary

- Scenario count: 12
- Reviewed candidates: 11
- No action: 1
- Watchlist: 2
- Policy blocked: 8
- Paper candidates: 0
- Paper orders created: 0
- All expected decisions passed: true
- Policy reason counts: `{"before_event_requires_event_model": 1, "deadline_not_future": 1, "deadline_too_near": 1, "liquidity_below_conservative_minimum": 1, "missing_deadline": 1, "missing_liquidity": 1, "missing_reference_price": 1, "missing_yes_price": 1, "paper_candidates_disabled_by_policy": 11, "target_distance_above_watchlist_limit": 1, "target_distance_unavailable": 1, "yes_price_above_conservative_limit": 1}`

## Safety

- Offline fixture reads only.
- Paper mode only.
- No live price fetching.
- No network or API calls.
- No credentials, wallet, private key, signing, real order, or live trading path.
- No dispatcher, runtime wiring, prompt automation, paper order planning, or paper order creation changes.
- Threshold-hit rows remain separate from existing above/below crypto numeric scorer runtime behavior.

## Verification

- `python -m pytest pm_bot\paper\tests\test_run_crypto_threshold_hit_policy_scenarios.py -q`
- `python -m pytest pm_bot\scoring\tests pm_bot\paper\tests -q`
- `python pm_bot\paper\run_crypto_threshold_hit_policy_scenarios.py`
- `python pm_bot\paper\run_crypto_threshold_hit_policy_scenarios.py --markdown`
- `python pm_bot\paper\run_crypto_threshold_hit_review_table.py --reference-context pm_bot\paper\threshold_hit_reference_context.v1.json --decision-policy pm_bot\paper\threshold_hit_decision_policy.v1.json --markdown`
- `python pm_bot\paper\run_crypto_threshold_hit_triage_report.py --source C:\Users\OpenC\Documents\AI-Orchestrator\local_snapshots\polymarket_markets_active_500_001.json --markdown`
- `PYTHONIOENCODING=utf-8 python pm_bot\paper\run_real_market_triage_report.py --source C:\Users\OpenC\Documents\AI-Orchestrator\local_snapshots\polymarket_markets_active_500_001.json --markdown`
- `python pm_bot\paper\run_manual_paper_operator_cycle.py`
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py`

All verification checks passed.
