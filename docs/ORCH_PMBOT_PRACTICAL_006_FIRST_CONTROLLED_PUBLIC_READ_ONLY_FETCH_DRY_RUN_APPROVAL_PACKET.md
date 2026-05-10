# ORCH-PMBOT-PRACTICAL-006 First Controlled Public Read-Only Fetch Dry-Run Approval Packet

## Purpose

This task creates the first controlled public read-only fetch dry-run approval packet for the five active PMBOT practical paper-tracked markets.

It is deliberately local-only. It prepares the approval packet, request manifest, operator checklist, evidence-save plan, replay-before-update plan, safety gate, blocker scenarios, and future execution boundary needed before a later explicitly approved public read-only fetch task.

## Inputs

The task reuses PRACTICAL-005 artifacts from:

`pm_bot/practical/artifacts/public_read_only_fetch_prep_005/`

Key inputs:

- `fetch_plan_5_markets.json`
- `fetch_dry_run_preview_5_markets.json`
- `operator_approval_pending.json`
- `public_fetch_readiness_gate.result.json`
- `fetch_plan_to_active_hypotheses_link_map.json`
- `source_registry_snapshot.json`

## Markets Covered

- `563650` SCOTUS accepts sports event contract case by July 31, 2026?
- `597964` Macron out by June 30, 2026?
- `598936` Will the next UK election be called by June 30, 2026?
- `691547` Kraken IPO by December 31, 2026?
- `692258` MicroStrategy sells any Bitcoin by June 30, 2026?

## Generated Modules

- `pm_bot/practical/public_fetch_approval_packet.py`
- `pm_bot/practical/public_fetch_request_manifest.py`
- `pm_bot/practical/public_fetch_evidence_save_plan.py`
- `pm_bot/practical/public_fetch_replay_before_update_plan.py`

These modules read local JSON artifacts and write local JSON/Markdown. They do not execute public fetches.

## Generated Approval Artifacts

Artifacts are written under:

`pm_bot/practical/artifacts/public_read_only_fetch_approval_006/`

The directory contains:

- `approval_packet_5_markets.json`
- `approval_packet_5_markets.md`
- `fetch_request_manifest_5_markets.json`
- `fetch_request_manifest_5_markets.md`
- `evidence_save_plan_5_markets.json`
- `evidence_save_plan_5_markets.md`
- `replay_before_update_plan_5_markets.json`
- `replay_before_update_plan_5_markets.md`
- `future_controlled_fetch_task_spec.json`
- `future_controlled_fetch_task_spec.md`
- `manual_operator_approval_template.json`
- `manual_operator_approval_template.md`
- `approval_blocker_scenarios.json`
- `approval_blocker_scenarios.md`
- `approval_packet_safety_scan.result.json`
- `approval_packet_safety_scan.md`
- `operator_public_fetch_approval_card.json`
- `operator_public_fetch_approval_card.md`

## Approval State

Approval remains pending:

- `operator_approval_required: true`
- `operator_approval_granted: false`
- `ready_for_controlled_public_fetch: false`
- `live_fetch_performed: false`
- `live_network_used: false`

The manual approval template is explicitly a non-approval artifact until a later separate operator action changes it.

## Safety Boundary

This task did not perform live public fetches, OpenRouter calls, Polymarket API calls, authenticated endpoint access, wallet/private-key/signing access, order or trading actions, scheduler/background fetches, browser automation changes, runtime/dispatcher changes, or autonomous polling.

It also did not generate market action recommendations or executable quantitative market output.

## Future Task Boundary

The only proposed next task after manual approval is:

`ORCH-PMBOT-PRACTICAL-007-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-EXECUTION-OPERATOR-APPROVED`

That future task would be limited to finite public read-only fetches for the listed markets and approved source categories, with evidence saved before use and replayed before any analysis update.

If manual approval is not granted, the safe path is to continue local paper tracking and outcome-feedback work.

## Validation

Validation covers:

- Compile check for `ai_orchestrator`, `pm_bot`, and `tests`
- New PRACTICAL-006 unit and E2E tests
- Existing PRACTICAL-005 prep tests
- Existing real market multi-packet batch test
- JSON validation for the generated result and approval artifacts
- `git diff --check`
- `git diff --cached --check`

## Remaining Gap Before Controlled Fetch

The approval packet is complete, but approval is still pending. The controlled public read-only fetch execution task remains blocked until manual operator approval is supplied in a separate explicit task.

## Remaining Gap Before Real-Money Trading

Real-money trading remains out of scope. This milestone does not add wallet, signing, order, custody, broker, or execution capability. Any such work would require separate design, review, validation, and explicit approval.
