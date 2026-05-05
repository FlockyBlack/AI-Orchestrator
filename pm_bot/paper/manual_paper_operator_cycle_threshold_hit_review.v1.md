# Manual Paper Operator Cycle

- Run ID: manual-paper-operator-cycle-fixture-v1
- Source: <REPO_ROOT>\pm_bot\paper\manual_snapshot_import_source
- Workspace: <REPO_ROOT>\pm_bot\paper\manual_paper_workspace
- Inbox: <REPO_ROOT>\pm_bot\paper\manual_paper_workspace\inbox
- Write inbox: false
- Manifest written: false
- Run artifacts written: false
- State committed: false
- Workspace note: Importable snapshots were previewed but not added to the workspace inbox because --write-inbox was not provided.

## Import Phase

- Inputs discovered: 7
- Importable snapshots: 2
- Imported snapshots: 0
- Skipped/quarantined inputs: 5
- Reason counts: {"already_present_in_workspace_inbox": 1, "duplicate_snapshot_id_in_source_batch": 1, "ignored_non_json_file": 1, "malformed_json": 1, "unsupported_snapshot_shape": 1}

## Workspace Phase

- Input files discovered: 3
- Valid snapshots discovered: 3
- Snapshots discovered: 3
- Snapshots processed: 2
- Snapshots skipped already processed: 1
- Quarantine records: 1
- Quarantine reason counts: {"already_processed_snapshot": 1}
- New paper orders created: 0
- Duplicate orders blocked: 1
- Risk-limit orders blocked: 1
- Before exposure: 100.00
- After exposure: 0.00
- Realized paper PnL delta: 72.41
- Final realized paper PnL: 72.41

## Output Artifacts

- None written

## Threshold-Hit Review

- threshold_hit_review_included: true
- threshold_hit_source_path: <REPO_ROOT>\pm_bot\paper\fixtures\polymarket_markets_active_threshold_hit.fixture.json
- threshold_hit_reference_context_used: true
- threshold_hit_decision_policy_used: true
- threshold_hit_decision_policy_version: threshold_hit_decision_policy.v1
- threshold_hit_candidates: 3
- threshold_hit_watchlist_count: 1
- threshold_hit_policy_blocked_count: 2
- threshold_hit_paper_candidate_count: 0
- threshold_hit_paper_orders_created: 0
- threshold_hit_artifact_paths: {}
- threshold_hit_candidate_rows: [{"asset": "BTC", "market_id": "fixture_bitcoin_hit_1m_before_event", "market_type": "threshold_hit_before_event", "reason_codes": ["before_event_requires_event_model", "paper_candidates_disabled_by_policy", "target_distance_above_watchlist_limit", "yes_price_above_conservative_limit"], "review_decision": "policy_blocked", "target": "$1m"}, {"asset": "BTC", "market_id": "fixture_btc_hit_150k_by_date", "market_type": "threshold_hit_by_date", "reason_codes": ["paper_candidates_disabled_by_policy"], "review_decision": "watchlist", "target": "$150k"}, {"asset": "ETH", "market_id": "fixture_eth_reach_5000_by_date", "market_type": "threshold_hit_by_date", "reason_codes": ["paper_candidates_disabled_by_policy", "target_distance_above_watchlist_limit", "yes_price_above_conservative_limit"], "review_decision": "policy_blocked", "target": "$5,000"}]

## Safety

- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; dispatcher_touched=false; prompt_automation_added=false
