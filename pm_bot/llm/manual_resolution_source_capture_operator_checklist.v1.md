# PMBOT Manual Resolution Source Capture Operator Checklist v1

- checklist_version: manual_resolution_source_capture_operator_checklist.v1
- task_id: PMBOT-SOURCE-004B-MANUAL-CAPTURE-OPERATOR-FILL-GUIDE
- source_capture_schema_path: pm_bot/llm/manual_resolution_source_capture_schema.v1.json
- capture_manifest_path: pm_bot/llm/manual_resolution_source_capture_manifest.v1.json
- validation_report_path: pm_bot/llm/manual_resolution_source_capture_validation.v1.json
- target_capture_directory: pm_bot/llm/manual_resolution_source_capture
- total_templates: 14
- validation_command: python -m pm_bot.llm.manual_resolution_source_capture_validator --write

## Status Flow

- not_started
- draft
- ready_for_local_review
- reviewed
- needs_revision

## Recommended Fill Order

1. full_market_resolution_criteria_text
2. full_resolution_rules
3. official_source_references
4. official_source_urls_or_rule_references
5. source_timestamps
6. source_reliability_review
7. reviewed_local_evidence_references
8. non_placeholder_evidence_notes

## Field Checklist

- full_market_resolution_criteria_text
  priority: 1
  meaning: The complete local text that defines how the market resolves.
  good_content: Generic example: exact local rule text or a faithful operator summary with source note.
  bad_content: A guess, prediction, paraphrase without source context, or placeholder.
  if_unknown: Leave blank in not_started/draft and add the unresolved question.
- full_resolution_rules
  priority: 2
  meaning: All rule clauses needed to understand valid resolution conditions.
  good_content: Generic example: local rule sections covering outcome definitions and tie/edge cases.
  bad_content: Only a headline, short excerpt, unsupported inference, or market opinion.
  if_unknown: Leave blank in not_started/draft and record which rule text is missing.
- official_source_references
  priority: 3
  meaning: Names of official sources or rule documents the operator manually checked.
  good_content: Generic example: official rules document name, filing title, or source system label.
  bad_content: Social posts, commentary, unverifiable claims, or invented references.
  if_unknown: Use an unresolved_source_questions entry instead of inventing a reference.
- official_source_urls_or_rule_references
  priority: 4
  meaning: Local source URL strings or rule identifiers already known to the operator.
  good_content: Generic example: manually verified URL or local rule reference identifier.
  bad_content: Unvisited links, guessed URLs, search results, or stale placeholders.
  if_unknown: Leave the array empty until the operator manually verifies a source.
- source_timestamps
  priority: 5
  meaning: When each source was checked or captured by the local operator.
  good_content: Generic example: local timestamp plus which source or rule reference was checked.
  bad_content: Missing timestamp, future timestamp, or timestamp copied from unrelated context.
  if_unknown: Add the timestamp when the operator checks the source.
- source_reliability_review
  priority: 6
  meaning: Operator note on whether the cited sources are official and complete.
  good_content: Generic example: source is official, complete, current, or has named gaps.
  bad_content: Outcome speculation, certainty claims, or unsupported trust statements.
  if_unknown: State that reliability remains unresolved and list the missing verification.
- reviewed_local_evidence_references
  priority: 7
  meaning: Local files, packet sections, or captured documents the operator reviewed.
  good_content: Generic example: repo-relative file path and section label.
  bad_content: External claims not present locally or broad notes like checked sources.
  if_unknown: Leave empty until local evidence is actually reviewed.
- non_placeholder_evidence_notes
  priority: 8
  meaning: Substantive notes about what the local evidence contains or lacks.
  good_content: Generic example: source confirms rule scope; one timestamp still missing.
  bad_content: TODO, placeholder, prediction, recommendation, or market decision text.
  if_unknown: Write a clear missing-data note in draft only after source review starts.

## Per Market Checklist

- market_id: 563650
  capture_json_path: pm_bot/llm/manual_resolution_source_capture/563650_resolution_source_capture.v1.json
  capture_markdown_path: pm_bot/llm/manual_resolution_source_capture/563650_resolution_source_capture.v1.md
  current_status: not_started
  validation_status: valid
  operator_next_step: Open the JSON and Markdown template, fill the recommended fields from manual local review, then set both status fields to draft.
  no_market_action_guidance: true
- market_id: 569332
  capture_json_path: pm_bot/llm/manual_resolution_source_capture/569332_resolution_source_capture.v1.json
  capture_markdown_path: pm_bot/llm/manual_resolution_source_capture/569332_resolution_source_capture.v1.md
  current_status: not_started
  validation_status: valid
  operator_next_step: Open the JSON and Markdown template, fill the recommended fields from manual local review, then set both status fields to draft.
  no_market_action_guidance: true
- market_id: 569333
  capture_json_path: pm_bot/llm/manual_resolution_source_capture/569333_resolution_source_capture.v1.json
  capture_markdown_path: pm_bot/llm/manual_resolution_source_capture/569333_resolution_source_capture.v1.md
  current_status: not_started
  validation_status: valid
  operator_next_step: Open the JSON and Markdown template, fill the recommended fields from manual local review, then set both status fields to draft.
  no_market_action_guidance: true
- market_id: 569334
  capture_json_path: pm_bot/llm/manual_resolution_source_capture/569334_resolution_source_capture.v1.json
  capture_markdown_path: pm_bot/llm/manual_resolution_source_capture/569334_resolution_source_capture.v1.md
  current_status: not_started
  validation_status: valid
  operator_next_step: Open the JSON and Markdown template, fill the recommended fields from manual local review, then set both status fields to draft.
  no_market_action_guidance: true
- market_id: 569343
  capture_json_path: pm_bot/llm/manual_resolution_source_capture/569343_resolution_source_capture.v1.json
  capture_markdown_path: pm_bot/llm/manual_resolution_source_capture/569343_resolution_source_capture.v1.md
  current_status: not_started
  validation_status: valid
  operator_next_step: Open the JSON and Markdown template, fill the recommended fields from manual local review, then set both status fields to draft.
  no_market_action_guidance: true
- market_id: 569344
  capture_json_path: pm_bot/llm/manual_resolution_source_capture/569344_resolution_source_capture.v1.json
  capture_markdown_path: pm_bot/llm/manual_resolution_source_capture/569344_resolution_source_capture.v1.md
  current_status: not_started
  validation_status: valid
  operator_next_step: Open the JSON and Markdown template, fill the recommended fields from manual local review, then set both status fields to draft.
  no_market_action_guidance: true
- market_id: 569366
  capture_json_path: pm_bot/llm/manual_resolution_source_capture/569366_resolution_source_capture.v1.json
  capture_markdown_path: pm_bot/llm/manual_resolution_source_capture/569366_resolution_source_capture.v1.md
  current_status: not_started
  validation_status: valid
  operator_next_step: Open the JSON and Markdown template, fill the recommended fields from manual local review, then set both status fields to draft.
  no_market_action_guidance: true
- market_id: 569368
  capture_json_path: pm_bot/llm/manual_resolution_source_capture/569368_resolution_source_capture.v1.json
  capture_markdown_path: pm_bot/llm/manual_resolution_source_capture/569368_resolution_source_capture.v1.md
  current_status: not_started
  validation_status: valid
  operator_next_step: Open the JSON and Markdown template, fill the recommended fields from manual local review, then set both status fields to draft.
  no_market_action_guidance: true
- market_id: 569373
  capture_json_path: pm_bot/llm/manual_resolution_source_capture/569373_resolution_source_capture.v1.json
  capture_markdown_path: pm_bot/llm/manual_resolution_source_capture/569373_resolution_source_capture.v1.md
  current_status: not_started
  validation_status: valid
  operator_next_step: Open the JSON and Markdown template, fill the recommended fields from manual local review, then set both status fields to draft.
  no_market_action_guidance: true
- market_id: 573656
  capture_json_path: pm_bot/llm/manual_resolution_source_capture/573656_resolution_source_capture.v1.json
  capture_markdown_path: pm_bot/llm/manual_resolution_source_capture/573656_resolution_source_capture.v1.md
  current_status: not_started
  validation_status: valid
  operator_next_step: Open the JSON and Markdown template, fill the recommended fields from manual local review, then set both status fields to draft.
  no_market_action_guidance: true
- market_id: 597964
  capture_json_path: pm_bot/llm/manual_resolution_source_capture/597964_resolution_source_capture.v1.json
  capture_markdown_path: pm_bot/llm/manual_resolution_source_capture/597964_resolution_source_capture.v1.md
  current_status: not_started
  validation_status: valid
  operator_next_step: Open the JSON and Markdown template, fill the recommended fields from manual local review, then set both status fields to draft.
  no_market_action_guidance: true
- market_id: 598936
  capture_json_path: pm_bot/llm/manual_resolution_source_capture/598936_resolution_source_capture.v1.json
  capture_markdown_path: pm_bot/llm/manual_resolution_source_capture/598936_resolution_source_capture.v1.md
  current_status: not_started
  validation_status: valid
  operator_next_step: Open the JSON and Markdown template, fill the recommended fields from manual local review, then set both status fields to draft.
  no_market_action_guidance: true
- market_id: 691547
  capture_json_path: pm_bot/llm/manual_resolution_source_capture/691547_resolution_source_capture.v1.json
  capture_markdown_path: pm_bot/llm/manual_resolution_source_capture/691547_resolution_source_capture.v1.md
  current_status: not_started
  validation_status: valid
  operator_next_step: Open the JSON and Markdown template, fill the recommended fields from manual local review, then set both status fields to draft.
  no_market_action_guidance: true
- market_id: 692258
  capture_json_path: pm_bot/llm/manual_resolution_source_capture/692258_resolution_source_capture.v1.json
  capture_markdown_path: pm_bot/llm/manual_resolution_source_capture/692258_resolution_source_capture.v1.md
  current_status: not_started
  validation_status: valid
  operator_next_step: Open the JSON and Markdown template, fill the recommended fields from manual local review, then set both status fields to draft.
  no_market_action_guidance: true

## Safety Do Not Include

- no predictions
- no trading recommendations
- no probability
- no EV
- no edge
- no confidence score
- no side selection
- no buy/sell/hold/enter/exit

## Ready For Local Review Requirements

- capture_status and source_capture_status are both ready_for_local_review
- full_market_resolution_criteria_text is filled from local operator review
- full_resolution_rules is filled from local operator review
- official_source_references has at least one manually verified item
- official_source_urls_or_rule_references has at least one manually verified item or rule reference
- source_timestamps records when the operator checked each source
- source_reliability_review states why the cited sources are suitable or what remains uncertain
- reviewed_local_evidence_references identifies local files or packet sections checked
- non_placeholder_evidence_notes contains substantive evidence notes or a clear missing-data note
- no-authority flags remain true
- validator passes with zero invalid templates

## Reviewed Requirements

- a separate local reviewer has inspected the ready_for_local_review template
- all ready_for_local_review requirements still hold
- manual_operator_notes records review-only acceptance or requested revision context
- reviewed status does not approve actions, queues, runtime behavior, wallets, orders, or market decisions

## No Authority Flags

- acceptance_is_not_trading_approval: true
- no_dispatcher_authority: true
- no_market_action_guidance: true
- no_queue_authority: true
- no_runtime_authority: true
- no_trading_authority: true
- no_wallet_or_order_authority: true
- operator_review_only: true
- passive_context_only: true
