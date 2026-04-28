# PMBOT Paper Policy Review Contract v1

## Summary

- task_id: PMBOT-PAPER-002-PAPER-POLICY-REVIEW-CONTRACT
- source_readiness_result_path: pm_bot/paper final dossier paper-readiness result artifact
- source_final_dossier_drafts_path: pm_bot/research selected-ingest final dossier drafts artifact
- source_policy_records_path: pm_bot/paper paper-policy-review records fixture
- policy_records_read: 4
- policy_records_accepted: 1
- policy_records_rejected: 3
- eligible_for_future_paper_decision_simulation: 1
- watch_only_policy_review: 0
- needs_more_manual_review: 1
- blocked_by_policy: 2
- paper_orders_created: 0
- market_ids:
  - 824952
- interpretation: eligible_for_future_paper_decision_simulation allows only a later paper-only decision-review simulation and does not authorize paper orders.

## Policy Records

### policy-review-824952-valid
- market_id: 824952
- readiness_status: eligible_for_future_paper_policy_review
- declared_future_policy_status: eligible_for_future_paper_decision_simulation
- future_policy_status: eligible_for_future_paper_decision_simulation
- record_validation_status: accepted
- source_readiness_record_found: True
- source_final_dossier_draft_found: True
- failure_codes:
  - none
- blocking_paths:
  - none

#### Checks

- dossier_readiness_confirmed: pass
- no_prohibited_trading_language: pass
- no_probability_or_ev_present: pass
- no_side_recommendation_present: pass
- no_market_decision_present: pass
- unresolved_questions_reviewed: pass
- uncertainty_register_present: pass
- evidence_inventory_present: pass

### policy-review-824952-incomplete
- market_id: 824952
- readiness_status: eligible_for_future_paper_policy_review
- declared_future_policy_status: eligible_for_future_paper_decision_simulation
- future_policy_status: needs_more_manual_review
- record_validation_status: rejected
- source_readiness_record_found: True
- source_final_dossier_draft_found: True
- failure_codes:
  - missing_policy_check:evidence_inventory_present
- blocking_paths:
  - policy_checks

#### Checks

- dossier_readiness_confirmed: pass
- no_prohibited_trading_language: pass
- no_probability_or_ev_present: pass
- no_side_recommendation_present: pass
- no_market_decision_present: pass
- unresolved_questions_reviewed: pass
- uncertainty_register_present: pass
- evidence_inventory_present: fail (missing_policy_check:evidence_inventory_present)

### policy-review-824952-prohibited-field
- market_id: 824952
- readiness_status: eligible_for_future_paper_policy_review
- declared_future_policy_status: eligible_for_future_paper_decision_simulation
- future_policy_status: blocked_by_policy
- record_validation_status: rejected
- source_readiness_record_found: True
- source_final_dossier_draft_found: True
- failure_codes:
  - prohibited_field:no_probability_or_ev_present
- blocking_paths:
  - policy_payload.probability

#### Checks

- dossier_readiness_confirmed: pass
- no_prohibited_trading_language: pass
- no_probability_or_ev_present: fail (prohibited_field:no_probability_or_ev_present)
- no_side_recommendation_present: pass
- no_market_decision_present: pass
- unresolved_questions_reviewed: pass
- uncertainty_register_present: pass
- evidence_inventory_present: pass

### policy-review-unknown-market
- market_id: 999999
- readiness_status: eligible_for_future_paper_policy_review
- declared_future_policy_status: watch_only_policy_review
- future_policy_status: blocked_by_policy
- record_validation_status: rejected
- source_readiness_record_found: False
- source_final_dossier_draft_found: False
- failure_codes:
  - missing_evidence_inventory
  - missing_uncertainty_register
  - missing_unresolved_questions_review
  - unknown_market_id
- blocking_paths:
  - market_id

#### Checks

- dossier_readiness_confirmed: fail (unknown_market_id)
- no_prohibited_trading_language: pass
- no_probability_or_ev_present: pass
- no_side_recommendation_present: pass
- no_market_decision_present: pass
- unresolved_questions_reviewed: fail (missing_unresolved_questions_review)
- uncertainty_register_present: fail (missing_uncertainty_register)
- evidence_inventory_present: fail (missing_evidence_inventory)

## Safety Boundary

- authenticated_endpoints: false
- betting_recommendations: false
- codex_copy_roots: false
- completed_dossiers: false
- credentials: false
- dispatcher_run_codex_touched: false
- expected_value_calculations: false
- live_fetchers: false
- live_trading: false
- market_decisions: false
- market_scoring: false
- network_api_calls: false
- paper_orders: false
- probability_estimates: false
- prompt_automation: false
- real_orders: false
- runtime_wiring: false
- side_recommendations: false
- trading_endpoints: false
- truth_inference: false
- wallet_private_keys: false

## Limitations

- Reads only local paper-readiness, selected-ingest final draft, and paper-policy-review fixture artifacts.
- eligible_for_future_paper_decision_simulation only means a later module may run a paper-only decision review simulation.
- This contract does not approve a paper order, choose a side, infer truth, recommend a trade, score a market, calculate probability, calculate expected value, or create paper orders.
