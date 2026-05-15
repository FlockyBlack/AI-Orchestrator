# ORCH-PMBOT-TELEGRAM-063T Design Supervised Live Enablement Review Panel

## Purpose

This document is a design-only implementation plan for a future Telegram review panel for the 063 supervised tiny live enablement gate.

The panel is intended to mirror local 063 review artifacts for operator inspection. It must not become source of truth, mutate runtime state, or grant approval. Local artifacts remain authoritative.

This task adds documentation only. It does not modify Telegram runtime code, add buttons, add callbacks, add actions, add live execution, add order handling, add credential handling, or push `master`.

## Hard Boundary

The future panel must remain review-only and dry-run-only. This design forbids any Telegram control whose label, callback, command, action id, payload, or handler performs or implies:

- `approve-live`
- `send-order`
- `submit-order`
- `cancel-order`
- `sign`
- `signer`
- `wallet`
- `connect-wallet`
- `unlock-wallet`
- `live-enable`
- `live-execute`

The future implementation must also reject synonyms that would mutate live state, place or cancel an order, unlock credentials, approve execution, or request signing material.

## Expected Source Artifact Contract

The future panel should read only local JSON or Markdown artifacts produced by the 063 gate. On current `origin/master`, these artifacts may not exist yet; absence must render as blocked or unavailable, never as approval.

Expected 063 artifact paths:

- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/latest_supervised_tiny_live_enablement_status_063.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_operator_checklist_063.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_blockers_063.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_risk_limits_063.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_kill_switch_plan_063.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_cancel_plan_063.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_failure_plan_063.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_env_readiness_063.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_manual_approval_packet_063.json`
- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/supervised_tiny_live_enablement_gate_063_operator.md`

The reader should use schema-aware parsing where available. Malformed JSON, missing files, stale timestamps, unexpected true execution flags, or unexpected resolved blockers must render the panel as blocked.

## Panel Sections

### Supervised Live Enablement Status

Display a compact status card from `latest_supervised_tiny_live_enablement_status_063.json`:

- task id
- generated timestamp
- market and strategy
- mode and execution mode
- readiness status
- source artifact presence
- non-executable state
- unresolved blocker count
- `resolved_blocker_count`

The visual state must default to blocked. The only acceptable positive state is "review artifacts present"; it must not be phrased as live readiness or execution approval.

Required invariant display:

- `review_only=true`
- `dry_run_only=true`
- `preflight_only=true`
- `preparation_only=true`
- `gate_only=true`
- `non_executable=true`
- `allowed_for_live=false`
- `live_execution_approved=false`
- `operator_approved=false`
- `candidate_is_executable=false`
- `resolved_blocker_count=0`

Any deviation from those values is a panel-level safety failure.

### Operator Checklist

Display `supervised_tiny_live_operator_checklist_063.json` as a read-only checklist:

- item id
- operator-facing label
- current status
- evidence path or source path
- blocking reason
- owner or next review role if present

Checklist rows may use read-only states such as present, missing, blocked, or needs review. Telegram must not allow the operator to mark checklist rows complete from chat. Completion must remain a local artifact workflow in a separate approved implementation.

### Blocker Matrix

Display `supervised_tiny_live_blockers_063.json` as a blocker matrix:

- blocker id
- severity
- current blocking state
- reason
- required evidence
- related artifact

The matrix must preserve unresolved blocker semantics. A future panel may group blockers by category:

- operator approval boundary
- live task boundary
- credential boundary
- signing boundary
- order boundary
- cancellation boundary
- authenticated trading boundary
- account-runtime boundary
- candidate executability boundary

The matrix must not include a resolve, approve, bypass, dismiss, override, or retry-live control.

### Risk Limits

Display `supervised_tiny_live_risk_limits_063.json` as non-editable limits:

- max order notional
- max daily notional
- max orders per day
- max market count
- allowed market
- allowed strategy
- scope statement

Risk limits are preparation constraints only. Passing a limit check must not change the status card into an approval state. Missing, malformed, or out-of-policy limits must render blocked.

### Kill Switch Plan

Display `supervised_tiny_live_kill_switch_plan_063.json` as a plan summary:

- operator stop condition
- required blocked state
- expected local artifact proof
- communication or escalation note
- evidence to capture after a stop decision

The plan must be descriptive only. Telegram must not expose an execution stop control, runtime pause control, or live-path mutation from this panel.

### Cancel Plan

Display `supervised_tiny_live_cancel_plan_063.json` as future prerequisites:

- cancellation readiness status
- prerequisites that must exist before any later live task
- required evidence
- failure handling if cancellation readiness is absent

The panel must describe cancellation readiness as unavailable unless an explicit future task provides a safe, reviewed, non-ambiguous contract. It must not expose any cancellation action.

### Failure Plan

Display `supervised_tiny_live_failure_plan_063.json` as operator review guidance:

- failure class
- detection evidence
- safe fallback
- required artifact update
- escalation owner

Safe fallback should remain paper-only review, local artifact capture, and blocked status preservation. The panel must not attempt automatic recovery.

### Environment Readiness

Display `supervised_tiny_live_env_readiness_063.json` as redacted readiness metadata:

- marker count
- missing marker count
- marker labels
- presence-only booleans
- values redacted indicator
- raw values emitted indicator

The future reader must never print raw environment values, tokens, keys, mnemonics, secrets, account identifiers, order identifiers, transaction hashes, balances, positions, fills, or PnL.

Any missing readiness marker keeps the panel blocked. A complete readiness marker set only means "operator review data present"; it does not approve execution.

### Manual Approval Packet

Display `supervised_tiny_live_manual_approval_packet_063.json` as a non-executable packet:

- approval required
- approval scope
- operator approved value
- packet generated timestamp
- artifact path
- remaining blocker summary

The panel must make `operator_approved=false` visible. It must not offer an approval button or a chat command that changes approval state.

### Safe Dry-Run Action Only

A future implementation may expose at most one safe dry-run action for this panel, and only in a separately approved implementation task. This design task does not add it.

The future action must run only the 063 local gate in dry-run mode, with no credentials, no authenticated trading endpoint, no account runtime reads, and no live mutation:

```powershell
python -m pm_bot.operator_runner.supervised_tiny_live_enablement_gate --market BTC --strategy tiny-momentum --dry-run
```

The action must be hidden or disabled if the runner is unavailable, if `--dry-run` cannot be enforced, if any prohibited flag is present, or if safety invariants fail. Its output may refresh local review artifacts only if a future task explicitly approves that behavior.

## Telegram Layout

Recommended message order:

1. Title and blocked status summary.
2. Latest status and invariant summary.
3. Operator checklist summary.
4. Blocker matrix summary with top unresolved blockers.
5. Risk limits summary.
6. Kill switch, cancellation, and failure plan summaries.
7. Environment readiness summary with redaction state.
8. Manual approval packet summary.
9. Safe dry-run availability note.

Long sections should be paginated or summarized with artifact paths. Pagination must remain read-only.

## Missing Data And Failure States

The future panel must render blocked for:

- missing 063 artifacts
- malformed JSON
- unsupported contract version
- stale artifact timestamp
- `resolved_blocker_count` greater than zero
- any unexpected true value for an execution, signing, wallet, order, cancellation, authenticated trading, account runtime, browser automation, scheduler, daemon, or autonomous trading flag
- any environment artifact that exposes raw values
- any manual approval packet that claims approval inside Telegram-controlled state

Missing source artifacts should not crash the runtime. They should produce a clear unavailable state and point to the expected local path.

## Future Validation Plan

A later implementation task should include focused tests for:

- status rendering from complete 063 artifacts
- blocked rendering from missing artifacts
- blocked rendering from malformed artifacts
- blocked rendering from unexpected true safety flags
- prohibited Telegram labels, callbacks, action ids, commands, and payload fragments
- safe dry-run command construction with required `--dry-run`
- redacted environment readiness rendering
- no mutation of approval, blockers, runtime state, or artifacts unless separately approved

The static safety invariant report should remain clean, and Telegram runtime smoke must continue to report expected false safety flags.

## Non-Goals

This design does not:

- modify Telegram runtime code
- add buttons, callbacks, or actions
- add live execution
- add credential or account access
- add signing or order paths
- approve any live task
- mark blockers resolved
- push `master`
