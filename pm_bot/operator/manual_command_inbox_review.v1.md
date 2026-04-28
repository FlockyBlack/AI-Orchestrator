# PMBOT Manual Command Inbox Review

Deterministic local-only review queue for inert manual operator command records.

- Task ID: PMBOT-OPERATOR-002-MANUAL-COMMAND-INBOX-REVIEW-QUEUE
- Source inbox: pm_bot/operator/manual_command_inbox_fixture.v1.json
- Records seen: 7
- Accepted: 3
- Rejected: 3
- Needs human review: 1
- Execution authority: false
- Commands executed: 0
- Orders created: 0
- Network calls: 0
- Next safe action: human_review_queue_only

## Accepted Records
- manual-inbox-status-001: queue_for_human_review_only; artifact: none
- manual-inbox-artifact-pointer-001: human_artifact_lookup_only; artifact: pm_bot/operator/expected_operator_review_bundle.v1.json
- manual-inbox-paper-intent-ref-001: record_for_audit_trail_only; artifact: pm_bot/paper/manual_paper_intent_ledger.v1.json

## Needs Human Review
- manual-inbox-human-review-001: needs_human_review_only; reasons: record_explicitly_marked_needs_human_review, requires_human_review_true

## Rejected Records
- manual-inbox-invalid-live-source: reject_do_not_route; reasons: invalid_source_type:telegram_live_bot, forbidden_source_type:telegram_live_bot
- manual-inbox-invalid-authority: reject_do_not_route; reasons: execution_authority_must_be_false, requires_human_review_must_be_true, safety_flag_must_be_false:command_execution
- manual-inbox-invalid-scoring: reject_do_not_route; reasons: unexpected_payload_field:edge, unexpected_payload_field:ev, unexpected_payload_field:probability, payload_value_must_be_string_or_string_list:probability, payload_value_must_be_string_or_string_list:ev, payload_value_must_be_string_or_string_list:edge, forbidden_field_name:payload.probability, forbidden_field_name:payload.ev, forbidden_field_name:payload.edge

This report is an inert queue artifact. It does not execute commands, create orders, call APIs, start Telegram, or authorize runtime wiring.
