# ORCH-PMBOT-TELEGRAM-064T Design Credentials Readiness Review Panel

## Purpose

This document is a design-only implementation plan for a future Telegram review panel for the 064 explicit live credentials readiness gate.

The panel is intended to mirror local 064 review artifacts for operator inspection. It must not become source of truth, mutate runtime state, inspect credential values, or grant approval. Local 064 artifacts remain authoritative.

This task adds documentation only. It does not modify Telegram runtime code, add buttons, add callbacks, add actions, read credentials, connect wallets, sign payloads, submit orders, cancel orders, call authenticated endpoints, or push `master`.

## Hard Boundary

The future panel must remain review-only, dry-run-only, and presence-only. It may display marker names and booleans from safe local artifacts. It must not display, derive, validate, transform, or infer raw credential values.

The future panel must explicitly prohibit:

- printing environment values
- printing credential values
- broad environment enumeration
- `.env` file reads
- credential store reads
- browser profile or wallet profile reads
- validating credentials with authenticated network calls
- wallet connection
- signer instantiation
- signing
- signed payload generation
- order submission
- order cancellation
- balance, position, fill, or PnL reads
- Telegram controls for `approve-live`
- Telegram controls for `send-order`
- Telegram controls for `submit-order`
- Telegram controls for `cancel-order`
- Telegram controls for `sign`
- Telegram controls for `signer`
- Telegram controls for `wallet`
- Telegram controls for `connect-wallet`
- Telegram controls for `unlock-wallet`

The future implementation must also reject synonyms that would approve live execution, mutate live state, place or cancel an order, unlock credentials, connect a wallet, or request signing material.

## Expected Source Artifact Contract

The future panel should read only local JSON or Markdown artifacts produced by the 064 gate. It should not read environment variables directly. It should not enumerate environment keys. It should not call authenticated services to check whether credentials are correct.

Expected 064 artifact paths:

- `pm_bot/trading_core/artifacts/explicit_live_credentials_readiness_gate_064/latest_explicit_live_credentials_readiness_gate_status_064.json`
- `pm_bot/trading_core/artifacts/explicit_live_credentials_readiness_gate_064/redacted_marker_presence_064.json`
- `pm_bot/trading_core/artifacts/explicit_live_credentials_readiness_gate_064/live_credentials_readiness_blockers_064.json`
- `pm_bot/trading_core/artifacts/explicit_live_credentials_readiness_gate_064/explicit_live_credentials_operator_checklist_064.json`
- `pm_bot/trading_core/artifacts/explicit_live_credentials_readiness_gate_064/operator_approval_boundary_064.json`
- `pm_bot/trading_core/artifacts/explicit_live_credentials_readiness_gate_064/credential_safety_policy_validation_064.json`
- `pm_bot/trading_core/artifacts/explicit_live_credentials_readiness_gate_064/explicit_live_credentials_readiness_summary_064.json`
- `pm_bot/trading_core/artifacts/explicit_live_credentials_readiness_gate_064/explicit_live_credentials_readiness_gate_064_result.json`
- `pm_bot/trading_core/artifacts/explicit_live_credentials_readiness_gate_064/explicit_live_credentials_readiness_gate_064_operator.md`

The reader should use schema-aware parsing where available. Missing files, malformed JSON, unsupported contracts, stale timestamps, unexpected true execution flags, unexpected raw-value fields, exposed secret-looking strings, or `resolved_blocker_count` greater than zero must render the panel as blocked.

## Panel Sections

### Credentials Readiness Status

Display a compact status card from `latest_explicit_live_credentials_readiness_gate_status_064.json`:

- task id
- generated timestamp
- market and strategy
- status
- readiness status
- source artifact presence
- `redacted_presence_review_ready`
- `live_ready=false`
- `allowed_for_live=false`
- `resolved_blocker_count=0`
- missing required marker count
- present execution flag count
- blocker count

The visual state must default to blocked. The only acceptable positive state is "redacted presence review artifacts present"; it must not be phrased as live readiness, credential correctness, execution approval, or trading authorization.

Required invariant display:

- `review_only=true`
- `dry_run_only=true`
- `preflight_only=true`
- `preparation_only=true`
- `gate_only=true`
- `non_executable=true`
- `presence_only=true`
- `presence_booleans_only=true`
- `explicit_allowlist_only=true`
- `allowed_for_live=false`
- `live_execution_approved=false`
- `operator_approved=false`
- `candidate_is_executable=false`
- `resolved_blocker_count=0`

Any deviation from those values is a panel-level safety failure.

### Required Marker Presence

Display `redacted_marker_presence_064.json` as a read-only marker table. The table may show only:

- marker label
- marker group
- required or optional status
- present or absent boolean
- result category
- `value_redacted=true`
- `raw_value_emitted=false`

The panel must show required marker presence or absence only. It must never show marker values, raw credential values, hashes, prefixes, suffixes, lengths, masked previews, token previews, wallet previews, signatures, signed payloads, order identifiers, transaction identifiers, balances, positions, fills, or PnL.

Required credential-source marker labels:

- `PMBOT_LIVE_CREDENTIALS_READINESS_GATE_ENABLED`
- `PMBOT_POLYMARKET_AUTH_CONFIG_PRESENT`
- `PMBOT_POLYMARKET_CLOB_BASE_URL`
- `PMBOT_POLYMARKET_L2_API_KEY_PRESENT`
- `PMBOT_POLYMARKET_L2_API_SECRET_PRESENT`
- `PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT`
- `PMBOT_POLYMARKET_FUNDER_ADDRESS_CONFIGURED`
- `PMBOT_WALLET_ADDRESS_CONFIGURED`
- `PMBOT_SIGNING_PROVIDER_CONFIGURED`
- `PMBOT_SIGNING_DRY_RUN_ONLY`

Required manual-control marker labels:

- `PMBOT_REQUIRE_MANUAL_OPERATOR_APPROVAL`
- `PMBOT_REQUIRE_KILL_SWITCH_READY`
- `PMBOT_LIVE_CREDENTIALS_OPERATOR_REVIEW_RECORD_PRESENT`
- `PMBOT_LIVE_CREDENTIALS_DUAL_CONTROL_REVIEW_PRESENT`

Execution flag marker labels that must remain absent or blocked if present:

- `PMBOT_LIVE_MODE`
- `PMBOT_LIVE_CANARY_ENABLED`
- `PMBOT_AUTHENTICATED_POLYMARKET_ENABLED`
- `PMBOT_WALLET_SIGNING_ENABLED`
- `PMBOT_ORDER_SUBMISSION_ENABLED`

Optional non-secret context marker labels may be shown as optional labels only:

- `PMBOT_MAX_ORDER_NOTIONAL_USD`
- `PMBOT_DAILY_LOSS_CAP_USD`
- `PMBOT_TOTAL_EXPOSURE_CAP_USD`
- `PMBOT_MAX_LIVE_TRADES_PER_DAY`
- `PMBOT_ALLOWED_MARKET_SLUGS`
- `PMBOT_ALLOWED_MARKET_IDS`

### Redacted Labels Only

The future panel must render marker labels as redacted symbolic readiness labels. It must not treat labels as proof that a credential works. Labels indicate only that the gate saw explicit marker names.

Allowed marker display categories:

- `missing`
- `present_redacted`
- `conflicting_execution_flag_blocked`
- `not_checked`

Disallowed display categories:

- raw value
- masked value
- value hash
- value prefix
- value suffix
- value length
- credential preview
- bearer token preview
- wallet secret preview
- signature preview
- signed payload preview

### Missing Marker Blockers

Display `live_credentials_readiness_blockers_064.json` as a blocker matrix:

- blocker id
- blocker category
- severity
- resolution status
- reason
- live-blocking state

Any missing required marker should be shown as a blocker using the `missing_required_marker:<label>` pattern from the 064 gate. The blocker must remain unresolved. The panel must not include a resolve, approve, bypass, dismiss, override, retry-live, send-order, sign, or wallet control.

The matrix must preserve the required unresolved blocker set:

- `live_execution_not_approved`
- `credentials_not_value_verified_by_pmbot`
- `operator_review_does_not_enable_execution`
- `authenticated_polymarket_requests_blocked`
- `wallet_connection_blocked`
- `signer_instantiation_blocked`
- `private_key_reads_blocked`
- `api_secret_reads_blocked`
- `signed_payload_generation_blocked`
- `order_submission_blocked`
- `order_cancellation_blocked`
- `balance_reads_blocked`
- `position_reads_blocked`
- `kill_switch_not_bound_to_live_adapter`
- `rollback_cancel_plan_not_implemented`
- `first_live_order_task_not_present`

### Operator Approval Boundary

Display `operator_approval_boundary_064.json` as non-executable review metadata:

- operator review marker presence
- dual-control review marker presence
- `operator_approved=false`
- `allowed_for_live=false`
- separate live-enabling task required
- separate wallet/signing task required
- separate authenticated request task required
- separate order submission or cancellation task required

The panel must make it obvious that marker presence does not approve execution. Telegram must not offer an approval button or command that changes approval state.

### Safety Policy Validation

Display `credential_safety_policy_validation_064.json` as a safety summary:

- validation status
- presence check count
- forbidden field count
- explicit allowlist status
- presence-booleans-only status
- broad environment scan status
- credential-values-read status
- credential-values-printed status
- credential-values-stored status
- credential-values-hashed status
- credential-values-transformed status

The expected safe values are:

- `broad_environment_scan_performed=false`
- `credential_values_read=false`
- `credential_values_serialized=false`
- `credential_values_printed=false`
- `credential_values_stored=false`
- `credential_values_hashed=false`
- `credential_values_transformed=false`

Any nonzero forbidden field count or unexpected true value must render blocked.

### Presence-Only Warning

The panel must include a visible warning:

```text
Presence-only review cannot validate whether credential values are correct, usable, funded, authorized, or safe. It checks marker names only. Live execution remains blocked.
```

This warning should appear near the readiness status and again near any redacted marker table. A complete marker set can only mean `redacted_presence_review_ready_live_blocked`; it cannot mean live-ready.

### Safe Dry-Run Action Only

A future implementation may expose at most one safe dry-run action for this panel, and only in a separately approved implementation task. This design task does not add it.

The only permitted command is:

```powershell
python -m pm_bot.operator_runner.explicit_live_credentials_readiness_gate --market BTC --strategy tiny-momentum --dry-run
```

The command must not accept Telegram-provided live, auth, wallet, signing, order, cancellation, balance, position, fill, PnL, or environment-dump flags. The action must be hidden or disabled if the runner is unavailable, if `--dry-run` cannot be enforced, if any prohibited flag is present, or if safety invariants fail.

The future action may refresh local 064 review artifacts only if a separate implementation task explicitly approves that behavior. It must not read credential values, enumerate the environment, validate credentials with authenticated calls, connect a wallet, sign, submit orders, or cancel orders.

## Telegram Layout

Recommended message order:

1. Title and blocked status summary.
2. Presence-only warning.
3. Latest status and invariant summary.
4. Required marker presence table with labels and booleans only.
5. Missing marker blocker summary.
6. Operator approval boundary summary.
7. Safety policy validation summary.
8. Required unresolved blocker matrix summary.
9. Safe dry-run availability note.

Long sections should be paginated or summarized with artifact paths. Pagination must remain read-only.

## Missing Data And Failure States

The future panel must render blocked for:

- missing 064 artifacts
- malformed JSON
- unsupported contract version
- stale artifact timestamp
- missing required marker labels
- any present execution flag marker
- `allowed_for_live` not exactly false
- `resolved_blocker_count` not exactly zero
- any unexpected true value for execution, signing, wallet, order, cancellation, authenticated trading, account runtime, browser automation, scheduler, daemon, background worker, or autonomous trading flags
- any artifact that exposes raw values
- any artifact that includes forbidden fields such as `private_key`, `seed_phrase`, `mnemonic`, `api_secret`, `auth_token`, `passphrase`, `signature`, `signed_payload`, `order_id`, `tx_hash`, `balance`, `position`, `fill`, or `pnl`
- any manual approval artifact that claims Telegram-controlled approval

Missing source artifacts should not crash the runtime. They should produce a clear unavailable state and point to the expected local path.

## Future Implementation Plan

A later implementation task should remain small and reviewable:

1. Add a schema-aware 064 artifact reader that loads only the expected local files.
2. Add a read-only Telegram presenter for the credentials readiness status card.
3. Add a read-only marker table that renders labels and booleans only.
4. Add a blocker matrix summary that preserves unresolved blocker semantics.
5. Add a safety invariant guard that fails closed on unsafe fields or unexpected true flags.
6. Add prohibited-control scanning for Telegram labels, callbacks, action ids, commands, and payload fragments.
7. Optionally add the one safe dry-run command behind an explicit dry-run-only action gate in a separate approved implementation task.
8. Add focused tests before any runtime exposure.

The future implementation must not change the 064 gate contract, public interfaces, or source-of-truth artifacts without a separate reviewed task.

## Future Validation Plan

A later implementation task should include focused tests for:

- status rendering from complete 064 artifacts
- blocked rendering from missing artifacts
- blocked rendering from malformed artifacts
- blocked rendering from unsupported contracts
- blocked rendering from missing required markers
- blocked rendering from present execution flag markers
- blocked rendering from `allowed_for_live` not false
- blocked rendering from `resolved_blocker_count` not zero
- redacted marker rendering with labels and booleans only
- no environment value printing
- no broad environment enumeration
- no authenticated credential validation calls
- no wallet connection, signing, order submission, or cancellation behavior
- prohibited Telegram labels, callbacks, action ids, commands, and payload fragments
- safe dry-run command construction with required `--dry-run`
- no mutation of approval, blockers, runtime state, or artifacts unless separately approved

The static safety invariant report should remain clean, and existing PMBOT compile checks must continue to pass.

## Non-Goals

This design does not:

- modify Telegram runtime code
- add buttons, callbacks, commands, handlers, or actions
- read credential values
- inspect `.env` files
- enumerate broad environment state
- validate credential correctness
- call authenticated network endpoints
- connect wallets
- add signing
- add order submission or cancellation
- approve any live task
- mark blockers resolved
- push `master`
