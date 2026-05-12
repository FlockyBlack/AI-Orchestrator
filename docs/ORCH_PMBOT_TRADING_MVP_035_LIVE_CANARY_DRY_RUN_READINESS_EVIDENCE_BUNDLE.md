# ORCH-PMBOT-TRADING-MVP-035 Live Canary Dry-Run Readiness Evidence Bundle

## Purpose

This task adds a deterministic, pure-data readiness evidence bundle for the future tiny live canary review path. The bundle links existing PMBOT live-prep artifacts so an operator can review whether the dry-run readiness chain is complete enough for discussion.

The bundle is review evidence only. It does not enable real wallet access, signing, order placement, authenticated endpoint usage, live canary execution, or live approval.

## Review-Only Scope

The readiness evidence bundle can report:

- `readiness_evidence_bundle_ready: true`
- `evidence_bundle_review_ready: true`
- `readiness_chain_complete_for_dry_run_review: true`

The bundle must always report:

- `live_execution_approved: false`
- `canary_executable_now: false`
- `real_execution_available: false`
- `live_connector_enabled: false`
- `readiness_evidence_bundle_is_not_live_approval: true`

Review readiness means the artifact chain is present and internally consistent. It does not mean the operator approved live trading.

## Artifact Chain

The 035 bundle links the prior live-prep chain:

- 030: Canary replay acceptance and live connector blocker matrix.
- 031: Disabled real wallet connector adapter and static secret boundary.
- 032: Live connector audit replay and operator review packet.
- 033: Tiny live canary preflight contract and manual runbook.
- 034: Dry-run operator intent packet with human acknowledgement only.
- 034B: Merge artifact carrying the 034 chain into master.

The required evidence item types are:

- `disabled_connector_adapter_status`
- `secret_boundary_validation_summary`
- `live_canary_readiness_packet`
- `canary_replay_acceptance`
- `live_connector_audit_replay`
- `operator_live_approval_packet`
- `tiny_live_canary_preflight_contract`
- `tiny_live_canary_manual_runbook`
- `dry_run_operator_intent_packet`
- `live_connector_blocker_matrix`
- `kill_switch_requirements`
- `abort_conditions`
- `evidence_capture_checklist`
- `risk_review`

Optional evidence item types may link dry-run receipts and result artifacts when available.

## Evidence Item Schema

Every item includes:

- `evidence_id`
- `evidence_type`
- `source_component`
- `reference_path_or_id`
- `status`
- `required_for_future_live_canary_review`
- `present`
- `review_ready`
- `execution_enabling`
- `notes`

Every review item has `execution_enabling: false`.

## Validation Flow

`validate_live_canary_readiness_evidence_bundle` checks:

- required evidence item types are present and review-ready;
- unresolved live blockers are present and non-empty;
- disabled connector evidence exists;
- secret boundary evidence exists;
- audit replay evidence exists;
- operator packet evidence exists;
- preflight contract evidence exists;
- manual runbook evidence exists;
- operator intent evidence exists;
- kill-switch requirements evidence exists;
- required non-execution statements are present;
- forbidden secret, signing, transaction, auth, and order fields are absent;
- live execution flags remain false.

Passing validation returns `evidence_bundle_valid_for_dry_run_review`. A passing result is still review-only.

## Manifest

`build_live_canary_readiness_evidence_manifest` produces a JSON-compatible manifest with:

- task and version metadata;
- `generated_for_review_only: true`;
- current execution posture;
- artifact chain;
- blocker summary;
- safety summary;
- evidence items;
- missing evidence;
- warnings;
- next required gates;
- validation summary.

The manifest is passive data and does not write files by itself.

## Blocker Handling

The blocker matrix remains unresolved. 035 adds review-bundle blocker categories without resolving or lowering any existing critical blocker:

- `readiness_evidence_bundle_review_only`
- `readiness_evidence_bundle_not_live_approval`
- `readiness_evidence_bundle_not_operator_executed`
- `evidence_bundle_does_not_resolve_live_blockers`
- `live_canary_execution_still_disabled`
- `live_canary_real_funding_still_not_configured`
- `live_canary_order_adapter_still_disabled`

The bundle may increase blocker visibility. It must not decrease blocker severity or mark live execution as available.

## Kill-Switch Evidence

The bundle links kill-switch requirements from the tiny canary preflight contract. The status remains requirements-defined and not live-verified.

`kill_switch_verified_for_live` remains false. A future task would need to verify a kill switch against any future live adapter boundary before execution could be considered.

## Secret Boundary Rules

The static secret boundary was extended for readiness bundle, item, manifest, reference, and blocker summary payloads.

The boundary rejects fields such as:

- `private_key`
- `mnemonic`
- `seed_phrase`
- `signature`
- `signed_order`
- `signed_payload`
- `raw_transaction`
- `auth_header`
- `bearer_token`
- `api_key`
- `access_token`
- `order_submission_payload`
- `transaction_payload`

The policy does not read environment variables, inspect real secrets, persist secrets, or print secrets. Human acknowledgement wording from the 034 operator intent packet remains non-cryptographic.

## Still Blocked

The following remain unavailable:

- real wallet connection;
- private key or mnemonic handling;
- cryptographic, wallet, transaction, or order signing;
- real order placement;
- authenticated Polymarket endpoint integration;
- real live canary execution;
- autonomous live trading;
- scheduler, daemon, or background live execution path;
- market recommendation as real trading advice;
- probability, EV, edge, confidence, or side selection as a live trading signal.

## Future Gated Task

Before any real canary could be proposed, a separate future operator-approved task would be required to define live connector boundaries, credential handling, kill-switch verification, dual-control live approval, funding and reconciliation, and a disabled-first order adapter design.

This 035 bundle is only an evidence review artifact for dry-run readiness.
