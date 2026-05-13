# ORCH-PMBOT-TRADING-MVP-051 Supervised Tiny Canary Runbook And Operator Approval Packet

## Purpose

This task adds a review-only supervised tiny canary runbook and operator approval packet for a future one-shot tiny supervised canary.

The packet consolidates the current dry-run-only live readiness stack into a deterministic human-review workflow. It is an approval packet for review discipline, not approval to execute.

## What It Does

- Builds a deterministic JSON approval packet with stable Markdown rendering.
- References the current live readiness stack:
  - live enablement config status
  - authenticated connector scaffold status
  - wallet/signing boundary status
  - signed order payload validation gate status
  - risk cap/readiness status
  - go/no-go status
  - evidence bundle status
  - replay acceptance status
  - Telegram operator controls status
  - Mini App review-only status
  - unresolved blockers
- Adds an operator checklist for manual review.
- Adds future-required actions for actual tiny live canary enablement, but marks each action as not executable and not implemented in this task.
- Integrates passively with readiness, evidence bundle, replay acceptance, operator UI, and the paper daily loop.
- Extends static secret-boundary validation for the approval packet, summary, and Markdown output.

## What It Does Not Do

- It does not enable live trading.
- It does not approve live execution.
- It does not submit orders.
- It does not call authenticated Polymarket endpoints.
- It does not make connector network calls.
- It does not connect a wallet.
- It does not read private keys, mnemonics, seed phrases, wallet files, browser wallets, API secrets, auth tokens, Telegram tokens, init data, raw operator IDs, or raw credentials.
- It does not perform signing.
- It does not generate signed payloads.
- It does not generate signed orders.
- It does not generate fake signatures, order IDs, transaction hashes, fills, balances, PnL, or execution results.
- It does not add browser automation, a scheduler, a daemon, a background worker, or an autonomous live trading loop.

## Required Review-Only Flags

The approval packet requires:

- `review_only: true`
- `live_execution_approved: false`
- `canary_executable_now: false`
- `real_execution_available: false`
- `execution_enabling: false`
- `order_submission_enabled: false`
- `wallet_signing_enabled: false`
- `signing_enabled: false`
- `signed_payload_generation_enabled: false`
- `signed_order_generation_enabled: false`
- `authenticated_polymarket_enabled: false`
- `live_connector_enabled: false`
- `allowed_for_live: false`
- `resolved_blocker_count: 0`

Any future change that flips one of these flags must be a separate operator-approved live-enabling task.

## Operator Checklist

The packet includes this checklist text for manual review:

- verify market selection
- verify max stake cap
- verify daily loss cap
- verify source/evidence freshness
- verify Telegram operator identity boundary
- verify no secret exposure
- verify canary is still blocked until a separate explicit live-enabling task

The checklist is review guidance only. It does not unlock execution and does not resolve blockers.

## Future Required Actions

The packet lists future actions that would be required before any actual tiny live canary could be considered:

- create a separate explicit live-enabling task
- define dual-control operator approval
- approve authenticated endpoint allowlist, audit logging, and redaction rules
- approve wallet custody and signing provider design without exposing private material
- implement any future order adapter as disabled-first with refusal tests before enablement
- verify a kill switch against every future live connector, signing, and order boundary
- define post-canary audit, balance, exposure, and reconciliation records
- resolve all live blockers in separate reviewed tasks

Each future action is explicitly marked:

- `executable_in_this_task: false`
- `implemented_in_this_task: false`
- `requires_separate_operator_approved_task: true`

## Refusal Rule

This packet is not live approval. If it is treated as authorization to connect a wallet, sign, generate signed payloads or signed orders, call authenticated Polymarket endpoints, submit an order, or perform real execution, the correct response is refusal and escalation to a separate explicit operator-approved live-enabling task.

## Generated Artifacts

The paper daily loop can emit:

- `supervised_tiny_canary_approval_packet_051.json`
- `supervised_tiny_canary_approval_packet_051.md`

The operator UI and dashboard also expose a passive summary section for the approval packet. Those views remain read-only and expose no executable action.

## Passive Integration Points

- `pm_bot/trading_core/supervised_tiny_canary_runbook.py` builds, validates, summarizes, and renders the packet.
- `pm_bot/trading_core/secret_boundary_policy.py` validates packet, summary, and Markdown outputs without raw credential access.
- `pm_bot/trading_core/live_canary_replay_acceptance.py` adds unresolved review-only blockers for the packet and missing future live-enabling task.
- `pm_bot/trading_core/live_canary_readiness.py` includes packet summary metadata in dashboard readiness.
- `pm_bot/trading_core/live_canary_readiness_evidence_bundle.py` includes packet evidence as review-only.
- `pm_bot/operator_runner/operator_ui_panel_v1.py` includes a read-only packet section with no executable action.
- `pm_bot/operator_runner/paper_daily_loop.py` emits deterministic JSON and Markdown packet artifacts.

## Windows Path-Length Validation Note

The required worktree path is long enough to trigger Windows path-length false negatives in tests that write deep fixture artifacts. Full PMBOT validation passed through a temporary `subst O:` alias. The automation smoke subset passed with pytest's built-in temp fixture and a short validation-only `--basetemp=C:/oc051tmp`. The alias and temporary directory are validation-only and are not committed.

## Live Trading Status

This task does not approve or enable live execution. PMBOT remains paper/dry-run only.
