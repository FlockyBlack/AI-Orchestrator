# PMBOT Controlled Public Read-Only Fetch Prep

## Purpose

This document describes the PRACTICAL-005 preparation layer for future controlled public read-only refresh of PMBOT practical market packets.

PRACTICAL-004 proved that five saved real/local market packets can be normalized, analyzed, tracked as paper-only hypotheses, linked to outcome checks, and reviewed through local operator artifacts. PRACTICAL-005 does not fetch new data. It defines the contracts and gates needed before a future operator-approved public read-only request can be allowed.

## What Public Read-Only Fetch Means

Public read-only fetch means a future explicit operator command may retrieve public information that does not require authentication, credentials, browser session cookies, KYC, wallet access, signing, order paths, trading endpoints, schedulers, polling, or unattended automation.

This milestone only prepares that path:

- Source category registry
- Fetch plan contract
- Dry-run preview
- Saved evidence packet format
- Saved evidence replay adapter
- Pending operator approval record
- Readiness gate
- Operator card and safety scan

## Relation To PRACTICAL-004

The new artifacts attach to the PRACTICAL-004 queue at:

- `pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.market_queue.json`
- `pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.source_dependency_map.json`
- `pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.active_paper_hypotheses.result.json`
- `pm_bot/practical/artifacts/real_market_batch_004/real_market_batch_004.outcome_check_queue.result.json`

The tracked markets remain:

- `563650` SCOTUS accepts sports event contract case by July 31, 2026?
- `597964` Macron out by June 30, 2026?
- `598936` Will the next UK election be called by June 30, 2026?
- `691547` Kraken IPO by December 31, 2026?
- `692258` MicroStrategy sells any Bitcoin by June 30, 2026?

## Allowed Source Categories

Allowed categories are placeholders only until a separate approval task authorizes a controlled request:

- `public_market_metadata_endpoint_placeholder`
- `public_resolution_source_page_placeholder`
- `public_issuer_company_news_page_placeholder`
- `public_court_government_page_placeholder`
- `public_exchange_company_announcement_page_placeholder`
- `public_static_web_page_placeholder`
- `low_quality_forum_or_rumor_labeled_source`

## Blocked Source Categories

The registry blocks:

- `authenticated_endpoint`
- `trading_endpoint`
- `order_endpoint`
- `wallet_signing_endpoint`
- `private_api_key_endpoint`
- `browser_session_cookie_based_source`
- `forum_rumor_only_unlabeled_source`
- `source_requiring_kyc_or_login`
- `source_requiring_bypass_or_automation`

## Fetch Plan Structure

`pm_bot/practical/public_read_only_fetch_contract.py` defines `pmbot_public_read_only_fetch_plan.v1`.

The generated plan requires:

- `auth_required: false`
- `credentials_required: false`
- `wallet_required: false`
- `trading_endpoint_allowed: false`
- `order_endpoint_allowed: false`
- `evidence_save_required: true`
- `replay_required_before_analysis_update: true`
- `operator_approval_required: true`
- `operator_approval_granted: false`
- `live_fetch_performed: false`

The current five-market plan contains 10 planned source placeholders: one public market metadata placeholder and one domain-specific public evidence placeholder per market.

## Saved Evidence Packet Structure

`pm_bot/practical/saved_public_evidence_packet.py` defines `pmbot_saved_public_evidence_packet.v1`.

Saved evidence records capture source identity, category, market links, hypothesis links, normalized claims, freshness, contradictions, limitations, capture errors, and explicit safety flags. The local fixtures use `capture_mode: fixture` and `live_network_used: false`.

## Replay Adapter

`pm_bot/practical/saved_evidence_replay_adapter.py` maps saved evidence packets into a `source_packets`-like structure compatible with the existing one-market practical input flow.

Replay is local-only. It preserves source ID, source category, freshness status, limitations, and replay markers. It does not fetch network data or update any analysis by itself.

## Operator Approval Requirement

`pm_bot/practical/public_fetch_operator_approval.py` creates a pending approval record with:

- `operator_approval_required: true`
- `operator_approval_granted: false`
- `approved_by: null`
- `approved_at: null`
- `live_fetch_enabled_after_approval: false`

This task does not grant approval.

## Readiness Gate

`pm_bot/practical/public_fetch_readiness_gate.py` evaluates the fetch plan, approval record, dry-run preview, source registry, and optional safety scan.

The generated readiness gate returns `ready_for_controlled_public_fetch: false` because approval is pending and live fetch is not enabled.

## Why No Live Fetch Was Performed

No live fetch was performed because the task scope is preparation only. The correct sequence is:

1. Operator inspects the registry, plan, preview, evidence contract, replay adapter, and readiness blockers.
2. A separate task creates an approval packet for a first controlled public read-only dry run.
3. Any future request saves evidence before replay.
4. Any analysis update consumes saved evidence through replay first.

## Why This Is Still Not Trading

This layer does not create or evaluate trades, does not touch wallet or signing paths, does not call order or trading endpoints, does not create background polling, and does not produce executable market output. It is paper-only infrastructure for evidence capture and analysis-quality tracking.

## Remaining Work Before Real-Money Activity

Real-money activity remains blocked. Required future work includes resolved outcome feedback history, source quality evidence, explicit risk controls, audited execution design, wallet/key policy, and separate operator approval.

## Next Recommended Action

`ORCH-PMBOT-PRACTICAL-006-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-DRY-RUN-APPROVAL-PACKET`
