# PMBOT Operator Review Pack v1

- schema_version: operator_review_pack.v1
- generated_by: pm_bot/workbench/export_operator_review_pack.py
- generated_at_policy: deterministic_static_snapshot_no_current_time
- product_direction: operator_workbench_review_pack_v1
- paper_orders_created: 0
- commands_executed: 0
- network_calls: 0

## Quality Warning Summary

- quality_report_status: health_passed
- total_warnings: 0
- blocking_warnings: 0
- action_required_warnings: 0
- review_needed_warnings: 0
- informational_warnings: 0
- blocking_warning_detected: false
- operator_summary: No quality warnings detected.
- recommended_manual_action: Continue manual review with no quality warning follow-up required.

## Quality Warning Interpretation

- blocking: blocking means stop and repair before relying on the package.
- action_required: action_required means review before relying on the package.
- review_needed: review_needed means inspect but not necessarily block.
- informational: informational means low-priority context.

## Top Quality Warning Categories

- none

## Quality Warnings By Owner

- code: 0
- fixture: 0
- schema: 0
- data: 0
- unknown: 0

## Quality Warnings By Action Type

- fix_required: 0
- review_required: 0
- ignore_allowed: 0

## Top Quality Action Items

- none

## Artifact Inventory

- total_artifacts: 25
- present_artifacts: 25
- missing_artifacts: 0
- required_missing_artifacts: 0

- product_001_result: docs/PMBOT_PRODUCT_001_RESULT.json (present=true, required=true, parse_status=parsed)
- integration_008_result: docs/PMBOT_INTEGRATION_008_RESULT.json (present=true, required=true, parse_status=parsed)
- paper_017_result: docs/PMBOT_PAPER_017_RESULT.json (present=true, required=false, parse_status=parsed)
- paper_018_result: docs/PMBOT_PAPER_018_RESULT.json (present=true, required=true, parse_status=parsed)
- paper_019_result: docs/PMBOT_PAPER_019_RESULT.json (present=true, required=false, parse_status=parsed)
- paper_019_multi_market_run_series: pm_bot/paper/multi_market_paper_run_series.v1.json (present=true, required=false, parse_status=parsed)
- paper_020_result: docs/PMBOT_PAPER_020_RESULT.json (present=true, required=false, parse_status=parsed)
- paper_020_paper_run_series_postmortem: pm_bot/paper/paper_run_series_postmortem.v1.json (present=true, required=false, parse_status=parsed)
- dashboard_002_result: docs/PMBOT_DASHBOARD_002_RESULT.json (present=true, required=true, parse_status=parsed)
- operator_002_result: docs/PMBOT_OPERATOR_002_RESULT.json (present=true, required=true, parse_status=parsed)
- infra_009_result: docs/PMBOT_INFRA_009_RESULT.json (present=true, required=false, parse_status=parsed)
- infra_009_report: docs/PMBOT_INFRA_009_ABC_ROUND003_WORKTREE_MATERIALIZATION.md (present=true, required=false, parse_status=not_applicable)
- paper_accounting_reconciliation_audit: pm_bot/paper/paper_accounting_reconciliation_audit.v1.json (present=true, required=true, parse_status=parsed)
- paper_accounting_batch_audit: pm_bot/paper/paper_accounting_batch_audit.v1.json (present=true, required=true, parse_status=parsed)
- paper_accounting_ledger: pm_bot/paper/paper_accounting_ledger.v1.json (present=true, required=true, parse_status=parsed)
- paper_accounting_pnl_preview: pm_bot/paper/paper_accounting_pnl_preview.v1.json (present=true, required=true, parse_status=parsed)
- paper_portfolio_snapshot: pm_bot/paper/paper_portfolio_snapshot.v1.json (present=true, required=true, parse_status=parsed)
- paper_metrics_report: pm_bot/paper/paper_metrics_report.v1.json (present=true, required=true, parse_status=parsed)
- portfolio_audit_state_preview: pm_bot/dashboard/portfolio_audit_state_preview.v1.json (present=true, required=true, parse_status=parsed)
- manual_command_inbox_review: pm_bot/operator/manual_command_inbox_review.v1.json (present=true, required=true, parse_status=parsed)
- manual_llm_review: pm_bot/llm/manual_llm_paste_in_review.v1.json (present=true, required=false, parse_status=parsed)
- manual_llm_review_quality_gate: pm_bot/llm/manual_llm_review_quality_gate.v1.json (present=true, required=false, parse_status=parsed)
- manual_llm_review_queue: pm_bot/llm/manual_llm_review_queue.v1.json (present=true, required=false, parse_status=parsed)
- actual_manual_llm_response_trial: pm_bot/llm/actual_manual_llm_response_trial.v1.json (present=true, required=false, parse_status=parsed)
- openrouter_passive_surface: pm_bot/workbench/openrouter_passive_surface_pointer.v1.json (present=true, required=false, parse_status=parsed)

## Paper Audits

- reconciliation_audit_status: reconciliation_passed
- reconciliation_checks_passed: 14
- batch_audit_status: batch_audit_passed
- batch_records_audited: 3
- batch_checks_passed: 13
- audit_warnings_count: 0
- audit_mismatches_count: 0

## PAPER-019 Multi-Market Run Series

- section_id: paper_019_multi_market_run_series
- artifact_status: present
- artifact_pointer: pm_bot/paper/multi_market_paper_run_series.v1.json
- artifact_parse_status: parsed
- series_status: series_run_passed
- markets_seen: 5
- records_seen: 5
- records_processed: 4

## PAPER-019 Records By Status

- accepted_accounting_record: 3
- blocked_fixture_record: 1
- manual_review_only: 1

## PAPER-019 Accounting-Only Summary

- paper_accounting_total_records: 4
- paper_accounting_settled_count: 3
- paper_accounting_open_count: 1
- paper_accounting_win_count: 1
- paper_accounting_loss_count: 1
- paper_accounting_flat_count: 1
- paper_accounting_total_cost_basis: 24.00
- paper_accounting_settled_cost_basis: 19.00
- paper_accounting_open_cost_basis: 5.00
- paper_accounting_total_settlement_value: 18.00
- paper_accounting_cumulative_pnl: -1.00
- paper_accounting_average_settled_pnl: -0.33
- paper_accounting_gross_profit: 6.00
- paper_accounting_gross_loss: -7.00
- paper_accounting_max_gain: 6.00
- paper_accounting_max_loss: -7.00

## PAPER-019 Blocked Or Manual Review Summary

- blocked_fixture_record_count: 1
- manual_review_only_count: 1
- blocked_or_rejected_records: 1
- manual_review_only_records: 1
- paper-run-series-record-004: market_id=paper-series-market-open-manual-004, processing_status=manual_review_only, lifecycle_state=open, accounting_included=true
- paper-run-series-record-005: market_id=paper-series-market-blocked-005, processing_status=blocked_fixture_record, lifecycle_state=blocked, accounting_included=false

## PAPER-019 Interpretation Warning

- PAPER-019 values are deterministic fixture/accounting-only outputs and are not strategy profitability, recommendation, EV, edge, probability, or market decision evidence.

## PAPER-019 Safety Counters

- real_orders_created: 0
- autonomous_paper_orders: 0
- network_calls: 0
- commands_executed: 0
- autonomous_decisions: 0

## PAPER-020 Paper Run Series Postmortem

- section_id: paper_020_paper_run_series_postmortem
- artifact_status: present
- artifact_pointer: pm_bot/paper/paper_run_series_postmortem.v1.json
- artifact_parse_status: parsed
- postmortem_status: postmortem_completed
- source_paper_019_found: true
- source_paper_019_series_status: series_run_passed
- markets_seen: 5
- records_seen: 5
- records_processed: 4

## PAPER-020 Accounting-Only PnL Warning

- cumulative_pnl: -1.00
- accounting_only_warning_present: true
- PAPER-019 PnL is accounting-only fixture output, not strategy profitability; it is not a recommendation, edge, EV, probability estimate, market score, or market truth evidence.

## PAPER-020 Record Status Summary

- accepted_accounting_record: count=3, operator_meaning=Record was accepted from the local fixture for accounting summary only.
- manual_review_only: count=1, operator_meaning=Record remains an open manual-review fixture item; it is inert and does not create orders.
- blocked_fixture_record: count=1, operator_meaning=Record was retained as blocked fixture context and excluded from accounting.

## PAPER-020 Fixture Limitations

- The series has five local fixture records and is not statistically representative.
- All accounting values are explicit fixture values; no live settlement truth is inferred.
- Only one open manual-review record and one blocked record are represented.
- No fees, liquidity, orderbook state, slippage, fill uncertainty, or timing variance are modeled.
- The fixture does not validate market discovery, live data handling, wallet access, or execution behavior.

## PAPER-020 Recommended Next Fixture Expansions

- Add more settled fixture records covering additional cost and settlement combinations.
- Add more open manual-review fixture records that remain inert until explicit fixture settlement values exist.
- Add blocked fixture variants for malformed accounting values and unsafe lineage flags.
- Add boundary accounting examples for zero cost, zero settlement, and unusually large fixture values.

## PAPER-020 Safety Counters

- real_orders_created: 0
- autonomous_paper_orders: 0
- network_calls: 0
- commands_executed: 0
- autonomous_decisions: 0

## PAPER-020 Next Safe Action

- PMBOT-WORKBENCH-006-SURFACE-PAPER-020-POSTMORTEM or PMBOT-PRODUCT-002-NEXT-MVP-GATE-REVIEW

## Portfolio Accounting

- summary_status: portfolio_accounting_state_ready
- accepted_accounting_market_ids: 824952
- paper_accounting_cumulative_pnl: 6.00
- batch_accounting_cumulative_pnl: -1.00
- accounting_boundary_warning: Paper accounting PnL is fixture/manual accounting only and is not strategy profitability.

## Dashboard State

- present: true
- schema_version: portfolio_audit_state_preview.v1
- dashboard_state_export_version: v2
- known_market_ids: 824952, series_btc_above_90000_2026_05_31
- current_known_portfolio_audit_status: paper_017_reconciliation_available_with_dashboard_002_static_export

## Operator Inbox

- records_seen: 7
- accepted_count: 3
- rejected_count: 3
- needs_human_review_count: 1
- execution_authority: false
- commands_executed: 0
- network_calls: 0

## Manual LLM Review

- section_id: manual_llm_review
- artifact_status: present
- artifact_pointer: pm_bot/llm/manual_llm_paste_in_review.v1.json
- artifact_parse_status: parsed
- validation_status: accepted
- errors_count: 0
- warnings_count: 0
- forbidden_content_detected: detected=false, findings_count=0
- next_safe_operator_action: Compare the accepted sections with local source artifacts and manually record unresolved evidence gaps.
- analysis_only_warning: Manual LLM review is analysis-only and not trading advice; it does not authorize orders, paper orders, market decisions, side selection, probability estimates, EV, edge, or scoring.
- llm_text_generated: false
- llm_api_calls_added: false
- browser_automation_added: false
- runtime_integration_added: false

## Manual LLM Accepted Sections

- concise_market_summary
- key_uncertainties
- missing_evidence
- contradiction_checks
- risk_notes
- operator_review_checklist
- suggested_research_questions
- citation_or_source_gap_notes
- safety_acknowledgement

## Manual LLM Missing Sections

- none

## Manual LLM Safe Error Summary

- none

## Manual LLM Review Quality Gate

- section_id: manual_llm_review_quality_gate
- artifact_status: present
- artifact_pointer: pm_bot/llm/manual_llm_review_quality_gate.v1.json
- artifact_parse_status: parsed
- validation_status: quality_passed
- base_validator_status: accepted
- checks_total: 11
- checks_passed: 11
- checks_with_warnings: 0
- checks_failed: 0
- errors_count: 0
- warnings_count: 0
- next_safe_operator_action: Use the response only as manual review context and verify unresolved source gaps against local artifacts.
- deterministic_quality_gate_warning: Manual LLM review quality gate is a deterministic offline quality gate only; it is not truth evaluation, probability, EV, edge, side, or trading advice.
- llm_text_generated: false
- llm_api_calls_added: false
- browser_automation_added: false
- runtime_integration_added: false

## Manual LLM Quality Gate Check Summaries

- required_sections_check: status=passed, required_sections_count=9, present_sections_count=9, missing_sections_count=0, empty_sections_count=0, errors_count=0, warnings_count=0
- minimum_content_check: status=passed, errors_count=0, warnings_count=0
- generic_or_placeholder_text_check: status=passed, placeholder_findings_count=0, repeated_cannot_determine_paths_count=0, errors_count=0, warnings_count=0
- unsafe_certainty_check: status=passed, unsafe_certainty_detected=false, findings_count=0, errors_count=0, warnings_count=0
- forbidden_content_check: status=passed, forbidden_content_detected=false, findings_count=0, errors_count=0, warnings_count=0

## Manual LLM Quality Gate Safe Error Summary

- none

## Manual LLM Review Queue

- section_id: manual_llm_review_queue
- artifact_status: present
- artifact_pointer: pm_bot/llm/manual_llm_review_queue.v1.json
- parse_status: parsed
- queue_items_total: 15
- additional_ready_candidates_found: 14
- errors_count: 0
- warnings_count: 0
- offline_manual_only: true
- not_truth_source: true
- not_trading_advice: true
- not_execution_authority: true
- offline_review_warning: Manual LLM review queue is an offline local index only; it is not truth, not trading advice, and not execution authority.
- llm_api_calls_added: false
- browser_automation_added: false
- runtime_integration_added: false

## Manual LLM Review Queue Status Counts

- ready_for_manual_packet_export: 0
- ready_for_manual_prompt_export: 0
- waiting_for_operator_pasted_response: 14
- response_accepted_for_operator_review: 1
- response_rejected_needs_operator_fix: 0
- blocked_missing_packet: 0
- blocked_invalid_artifact: 0
- blocked_missing_source_artifact: 0

## Manual LLM Review Queue Items

- market_id=563650, status=waiting_for_operator_pasted_response, response_present=false, validation_status=not_run, quality_gate_status=not_run, operator_surface_review_status=not_available
- market_id=569332, status=waiting_for_operator_pasted_response, response_present=false, validation_status=not_run, quality_gate_status=not_run, operator_surface_review_status=not_available
- market_id=569333, status=waiting_for_operator_pasted_response, response_present=false, validation_status=not_run, quality_gate_status=not_run, operator_surface_review_status=not_available
- market_id=569334, status=waiting_for_operator_pasted_response, response_present=false, validation_status=not_run, quality_gate_status=not_run, operator_surface_review_status=not_available
- market_id=569343, status=waiting_for_operator_pasted_response, response_present=false, validation_status=not_run, quality_gate_status=not_run, operator_surface_review_status=not_available
- market_id=569344, status=waiting_for_operator_pasted_response, response_present=false, validation_status=not_run, quality_gate_status=not_run, operator_surface_review_status=not_available
- market_id=569366, status=waiting_for_operator_pasted_response, response_present=false, validation_status=not_run, quality_gate_status=not_run, operator_surface_review_status=not_available
- market_id=569368, status=waiting_for_operator_pasted_response, response_present=false, validation_status=not_run, quality_gate_status=not_run, operator_surface_review_status=not_available
- market_id=569373, status=waiting_for_operator_pasted_response, response_present=false, validation_status=not_run, quality_gate_status=not_run, operator_surface_review_status=not_available
- market_id=573656, status=waiting_for_operator_pasted_response, response_present=false, validation_status=not_run, quality_gate_status=not_run, operator_surface_review_status=not_available
- market_id=597964, status=waiting_for_operator_pasted_response, response_present=false, validation_status=not_run, quality_gate_status=not_run, operator_surface_review_status=not_available
- market_id=598936, status=waiting_for_operator_pasted_response, response_present=false, validation_status=not_run, quality_gate_status=not_run, operator_surface_review_status=not_available
- market_id=691547, status=waiting_for_operator_pasted_response, response_present=false, validation_status=not_run, quality_gate_status=not_run, operator_surface_review_status=not_available
- market_id=692258, status=waiting_for_operator_pasted_response, response_present=false, validation_status=not_run, quality_gate_status=not_run, operator_surface_review_status=not_available
- market_id=824952, status=response_accepted_for_operator_review, response_present=true, validation_status=accepted, quality_gate_status=quality_passed, operator_surface_review_status=operator_surface_review_passed

## Manual LLM Review Queue Safe Error Summary

- none

## Actual Manual LLM Response Trial

- section_id: actual_manual_llm_response_trial
- artifact_status: present
- artifact_path: pm_bot/llm/actual_manual_llm_response_trial.v1.json
- artifact_present: true
- parse_status: parsed
- operator_response_path: pm_bot/llm/real_local_market_llm_trial_response_operator.v1.json
- operator_response_present: true
- trial_artifact_operator_response_present: true
- response_source_type: actual_operator_pasted_response
- market_id: 824952
- source_artifact_path: pm_bot/research/selected_ingest_final_dossier_drafts.v1.json
- trial_packet_source_type: real_local_market_artifact
- run_status: actual_response_accepted
- acceptance_status: accepted_for_operator_review
- response_validation_status: accepted
- manual_review_status: accepted
- quality_gate_status: quality_passed
- errors_count: 0
- warnings_count: 0
- next_safe_operator_action: Review the accepted local artifacts as offline operator context only; do not execute or automate anything.
- offline_review_context_only: true
- not_truth_source: true
- not_trading_advice: true
- not_execution_authority: true
- explicit_warning: This surface is offline review context only. It is not a truth source, not trading advice, and not execution authority.

## Actual Manual LLM Response Trial Safety Flags

- autonomous_paper_orders: false
- browser_automation: false
- credentials_or_wallet: false
- deterministic: true
- llm_api: false
- local_file_reads_only: true
- market_decision_logic: false
- network_api: false
- not_execution_authority: true
- not_trading_advice: true
- not_truth_source: true
- offline_review_context_only: true
- probability_ev_scoring_or_edge: false
- prompt_automation: false
- real_orders_or_live_trading: false
- runtime_wiring: false
- side_recommendations: false
- surface_only: true
- truth_evaluation: false

## OpenRouter Passive Surface

- section_id: openrouter_passive_surface
- artifact_status: present
- artifact_pointer: pm_bot/workbench/openrouter_passive_surface_pointer.v1.json
- artifact_markdown_pointer: pm_bot/workbench/openrouter_passive_surface_pointer.v1.md
- artifact_parse_status: parsed
- source_batch_task: PMBOT-OPENROUTER-046
- source_baseline_task: PMBOT-OPENROUTER-047
- source_surface_task: PMBOT-OPENROUTER-048
- source_048_status: completed_pushed
- surfaced_market_ids: 569333, 569334, 569343
- model: anthropic/claude-sonnet-4.5
- total_calls: 3
- prompt_tokens: 12859
- completion_tokens: 5827
- total_tokens: 18686
- total_cost: 0.125982
- average_cost_per_market: 0.041994
- fenced_response_count: 3
- normalized_response_count: 3
- clean_raw_json_response_count: 0
- accepted_for_operator_review_count: 3
- blocked_count: 0
- offline_review_warning: OpenRouter passive surface is read-only operator context; it creates no queue item, runtime hook, API call, wallet/order access, or authority.

## OpenRouter Passive Surface Safety Flags

- operator_review_only: true
- passive_context_only: true
- no_trading_authority: true
- no_queue_authority: true
- no_runtime_authority: true
- no_dispatcher_authority: true
- no_wallet_or_order_authority: true
- acceptance_is_not_trading_approval: true
- analysis_only: true
- manual_review_only: true

## OpenRouter Passive Surface Artifact Pointers

- workbench_pointer_json: pm_bot/workbench/openrouter_passive_surface_pointer.v1.json (generated_workbench_pointer)
- workbench_pointer_markdown: pm_bot/workbench/openrouter_passive_surface_pointer.v1.md (generated_workbench_pointer)
- source_surface_json: pm_bot/llm/operator_openrouter_batch_surface_046.v1.json (read_only_passive_source)
- source_surface_markdown: pm_bot/llm/operator_openrouter_batch_surface_046.v1.md (read_only_passive_source)
- source_048_result: docs/PMBOT_OPENROUTER_048_RESULT.json (read_only_source_result)
- source_048_report: docs/PMBOT_OPENROUTER_048_PASSIVE_OPERATOR_SURFACE_046_BATCH.md (read_only_source_report)

## Missing Artifacts

- none

## Warnings

- accounting_only_interpretation: Paper accounting PnL is fixture/manual accounting only and is not strategy profitability.
- audit_status_not_truth_inference: Audit pass/fail state reflects deterministic local artifact consistency only, not truth inference.
- no_recommendations_or_decisions: This operator review pack does not recommend markets, sides, prices, sizes, orders, trades, paper orders, or decisions.
- local_artifacts_only: This pack reads local artifacts only and contains no live prices, live fetch results, or API results.

## Safety Flags

- acceptance_is_not_trading_approval: true
- analysis_only: true
- autonomous_paper_orders: false
- command_execution: false
- credentials: false
- deterministic_output: true
- dispatcher_run_codex_changes: false
- live_trading: false
- local_file_reads_only: true
- manual_review_only: true
- market_decisions: false
- network_api: false
- no_dispatcher_authority: true
- no_queue_authority: true
- no_runtime_authority: true
- no_trading_authority: true
- no_wallet_or_order_authority: true
- offline_only: true
- operator_review_only: true
- passive_context_only: true
- real_orders: false
- recommendations: false
- runtime_wiring: false
- scoring_probability_ev_edge: false
- trading: false
- truth_inference: false
- wallet: false

## Next Safe Manual Actions

- review_pack_inventory_and_warnings: Review artifact_inventory, missing_artifacts, and warnings in this local pack.
- review_paper_accounting_audit_artifacts: Inspect the existing paper reconciliation and batch audit artifacts for local consistency status.
- review_operator_inbox_queue: Review accepted, rejected, and needs-human-review inbox records without executing commands.
- review_manual_llm_review_queue: Review manual LLM queue status for local packet and response readiness.
- review_actual_manual_llm_response_trial_surface: Review actual manual LLM response trial status as offline local context only.
- review_openrouter_passive_surface_pointer: Review OpenRouter batch surface pointer as read-only local context.
- integration_review_only: Use this pack as a static input for human integration review only.

- This operator review pack does not recommend markets, sides, prices, sizes, orders, trades, paper orders, or decisions.
