# PMBOT Paper Decision Policy Spec v1

## Summary

- task_id: PMBOT-PAPER-004-PAPER-DECISION-POLICY-SPEC
- source_preview_path: pm_bot/paper/paper_decision_simulation_preview.v1.json
- source_policy_review_result_path: pm_bot/paper/paper_policy_review_result.v1.json
- source_final_dossier_drafts_path: pm_bot/research/selected_ingest_final_dossier_drafts.v1.json
- preview_records_read: 1
- policy_specs_written: 1
- markets_covered: 1
- paper_orders_created: 0
- market_ids:
  - 824952
- interpretation: PAPER-004 defines constraints only and does not authorize simulation, recommendations, execution, or orders.

## Future Simulation Contract

- accepted_simulation_preview_status:
  - ready_for_future_paper_decision_policy_design
- allowed_future_simulation_statuses:
  - paper_simulation_allowed
  - paper_watch_only
  - paper_blocked_needs_more_review
  - paper_blocked_by_policy
- required_future_simulation_inputs:
  - market_id
  - question/title
  - resolution_criteria_summary
  - evidence_inventory_summary
  - uncertainty_register_summary
  - missing_information_review
  - open_questions
  - current_yes_price
  - liquidity
  - volume
  - paper_readiness_status
  - paper_policy_status
- allowed_future_output_fields:
  - market_id
  - simulation_status
  - policy_findings
  - blocking_reasons
  - watch_only_reasons
  - required_manual_followup
  - simulation_notes
- always_forbidden_future_fields:
  - real_order
  - live_order
  - wallet
  - private_key
  - execution
  - trade_execution
  - authenticated_endpoint
- paper_004_forbidden_output_fields:
  - side
  - recommendation
  - probability
  - expected_value
  - ev
  - score
  - signal
  - stake
  - size
  - entry_price
  - limit_price
  - price_target
  - market_decision
  - buy
  - sell

## Policy Constraint Codes

- policy_blockers:
  - missing_resolution_criteria
  - missing_evidence_inventory
  - unresolved_critical_questions
  - prohibited_trading_language_present
  - probability_or_ev_present
  - side_or_recommendation_present
  - market_decision_present
  - order_or_trade_present
- watch_only_reasons:
  - insufficient_source_coverage
  - high_unresolved_uncertainty
  - stale_manual_review
  - ambiguous_resolution_criteria

## Policy Specs

### 824952
- accepted_preview_status: ready_for_future_paper_decision_policy_design
- policy_spec_status: paper_decision_policy_constraints_defined
- source_policy_record_present: True
- source_final_dossier_draft_present: True
- policy_boundaries:
  - PAPER-004 defines policy constraints only.
  - A later PAPER-005 module may use this contract for paper-only simulation.
  - This artifact does not run a simulation, choose an outcome direction, infer truth, score the market, calculate probability, calculate expected value, or create paper orders.

## Safety Boundary

- live_fetchers: false
- network_api_calls: false
- credentials: false
- wallet_private_keys: false
- authenticated_endpoints: false
- trading_endpoints: false
- real_orders: false
- live_trading: false
- paper_orders: false
- betting_recommendations: false
- truth_inference: false
- market_scoring: false
- probability_estimates: false
- expected_value_calculations: false
- side_recommendations: false
- market_decisions: false
- runtime_wiring: false

## Limitations

- Reads only local PAPER-003 preview, PAPER-002 policy-review result, and selected-ingest final dossier draft artifacts.
- PAPER-004 only defines policy constraints; it does not run a decision simulation.
- This specification does not choose YES or NO, recommend a trade, calculate probability, calculate expected value, score a market, infer truth, create paper orders, or create real orders.
