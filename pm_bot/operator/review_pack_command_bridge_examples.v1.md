# PMBOT Review Pack Command Bridge Examples

Static examples for the OPERATOR-003 bridge contract. These examples only map inert manual command record types to future review pack section IDs. They do not execute commands, start Telegram, call APIs, create orders, score markets, infer truth, or recommend decisions.

## Valid Bridge Records

- `request_status_summary` -> `product_status` using `include_static_summary_reference`
- `request_dashboard_state_export` -> `dashboard_state_summary` using `include_dashboard_state_reference`
- `record_manual_review_note` -> `operator_inbox_summary` using `include_manual_review_note`
- `record_manual_paper_intent_reference` -> `paper_audit_summary` using `include_paper_audit_reference`
- `request_artifact_pointer` -> `artifact_inventory` using `include_static_artifact_pointer`
- `request_artifact_pointer` -> `missing_stale_artifact_warnings` using `emit_missing_stale_artifact_warning`
- `mark_needs_human_review` -> `next_safe_manual_actions` using `list_next_safe_manual_action`

Every valid bridge record sets `requires_human_review: true`, `execution_authority: false`, `can_trigger_runtime: false`, and all safety flags to `false`.

## Invalid Bridge Records

- `invalid-execution-authority`: rejects execution authority, missing human review, and command execution flags.
- `invalid-runtime-trigger`: rejects runtime trigger authority and runtime wiring flags.
- `invalid-telegram-runtime-field`: rejects Telegram bot token fields and token-shaped values.
- `invalid-network-api-field`: rejects API endpoint fields and URL-shaped values.
- `invalid-wallet-order-fields`: rejects wallet/private-key fields and credential-shaped values.
- `invalid-scoring-fields`: rejects probability, EV, edge, and score fields.
- `invalid-unmapped-section`: rejects a command-to-section/action combination not listed in the bridge contract.

## Boundary

The bridge is a static contract layer for future review pack composition. It has no runtime wiring and grants no authority to execute operator commands, create paper or real orders, call network APIs, read credentials, sign wallet operations, score markets, calculate probability/EV/edge, infer truth, or recommend a side.
