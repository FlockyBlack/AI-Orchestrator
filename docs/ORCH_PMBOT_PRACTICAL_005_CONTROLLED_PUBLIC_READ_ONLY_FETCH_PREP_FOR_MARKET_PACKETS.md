# ORCH-PMBOT-PRACTICAL-005 Controlled Public Read-Only Fetch Prep For Market Packets

## Summary

This task adds a local-only preparation layer for future controlled public read-only refresh of the five PRACTICAL-004 paper-tracked markets.

No public source was fetched. No OpenRouter call, Polymarket API call, authenticated endpoint, wallet/private-key access, signing, order path, trading action, runtime change, dispatcher change, scheduler, polling, watcher, daemon, or unattended automation was used.

## Generated Implementation

- `pm_bot/practical/public_read_only_fetch_contract.py`
- `pm_bot/practical/public_source_registry.py`
- `pm_bot/practical/public_fetch_plan_builder.py`
- `pm_bot/practical/public_fetch_dry_run_preview.py`
- `pm_bot/practical/saved_public_evidence_packet.py`
- `pm_bot/practical/saved_evidence_replay_adapter.py`
- `pm_bot/practical/public_fetch_operator_approval.py`
- `pm_bot/practical/public_fetch_readiness_gate.py`

## Generated Artifacts

Artifacts are under:

`pm_bot/practical/artifacts/public_read_only_fetch_prep_005/`

They include:

- Source registry snapshot
- Five-market fetch plan JSON/Markdown
- Dry-run preview JSON/Markdown
- Saved evidence fixture JSON/Markdown
- Saved evidence replay adapter sample JSON/Markdown
- Pending operator approval JSON/Markdown
- Public fetch readiness gate JSON/Markdown
- Fetch plan to active hypotheses link map JSON/Markdown
- Operator card JSON/Markdown
- Public fetch prep safety scan JSON/Markdown

## Source Registry

The registry separates allowed placeholder categories from blocked categories. Allowed categories are public read-only placeholders only. Blocked categories include authenticated endpoints, trading endpoints, order endpoints, wallet/signing endpoints, private API key endpoints, cookie/session sources, KYC/login sources, bypass/automation sources, and unlabeled rumor-only sources.

## Fetch Plan

The generated fetch plan covers the five active paper-only hypotheses from PRACTICAL-004:

- `563650`
- `597964`
- `598936`
- `691547`
- `692258`

The plan contains 10 future source placeholders. It records what would be fetched later, why it would matter, source category, allowed/blocked status, expected evidence type, linked market ID, linked hypothesis ID, and approval requirement.

The plan requires saved evidence and replay before any analysis update.

## Dry-Run Preview

The dry-run preview summarizes request count, affected markets, source categories, expected evidence, approval status, and blockers.

It explicitly returns:

- `live_fetch.allowed_now: false`
- `live_fetch_allowed_now: false`

Reason: operator approval is not granted and live fetch is not part of this task.

## Saved Evidence Packet

The evidence packet contract defines the future saved evidence format for fixture, replay, and future public read-only capture modes. The generated fixture is local-only and safe for replay.

The fixture and tests include:

- Valid saved evidence
- Stale saved evidence
- Contradictory saved evidence

## Replay Adapter

The replay adapter converts saved evidence packets into source-packet-like records for the existing practical one-market analysis flow. It preserves source identity, source category, freshness, limitations, claims, and replay markers.

It never fetches network data.

## Operator Approval

The generated approval record is pending:

- `operator_approval_required: true`
- `operator_approval_granted: false`
- `approved_by: null`
- `approved_at: null`
- `live_fetch_enabled_after_approval: false`

No approval is granted by this task.

## Readiness Gate

The readiness gate requires:

- Operator approval granted
- Allowed source categories only
- Request count within limit
- Evidence saving enabled
- Replay requirement enabled
- No auth, credentials, wallet, trading endpoint, or order endpoint
- No scheduler or background worker
- No live fetch already performed

The generated result is `ready_for_controlled_public_fetch: false`.

## Link Map

The link map connects planned source categories to active hypotheses, source dependencies, outcome check dependencies, expected evidence roles, and safety status for each market.

## Operator Card

The operator card explains what is ready, what is blocked, what approval is needed, what would be fetched later, what will not be fetched, why live fetch is not performed, and the next safe action.

## Safety Scan

The public fetch prep safety scan passed and confirms:

- `live_network_used: false`
- `openrouter_calls_performed: 0`
- `polymarket_api_calls_performed: 0`
- `authenticated_endpoints_used: false`
- `wallet_or_private_key_access: false`
- `orders_or_trading_actions: false`
- `runtime_or_dispatcher_changes: false`
- `market_recommendation_generated: false`
- `probability_ev_edge_or_side_selection_generated: false`
- `operator_approval_granted: false`
- `ready_for_controlled_public_fetch: false`

## Validation

Validation includes compileall, focused tests for each new module, the PRACTICAL-004 regression test, the practical safety scan test, JSON validation, and diff whitespace checks.

## Next Recommended Action

`ORCH-PMBOT-PRACTICAL-006-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-DRY-RUN-APPROVAL-PACKET`
