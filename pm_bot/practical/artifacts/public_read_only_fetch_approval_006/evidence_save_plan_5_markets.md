# PMBOT Public Fetch Evidence Save Plan

- Evidence save plan ID: `public-read-only-fetch-prep-005-5-markets.evidence_save_plan.006`
- Fetch plan ID: `public-read-only-fetch-prep-005-5-markets`
- Evidence directory: `pm_bot/practical/artifacts/public_read_only_fetch_execution_007/saved_public_evidence`
- Filename pattern: `{market_id}/{request_intent_id}.saved_public_evidence_packet.json`
- Overwrite policy: `no_overwrite`
- Replay before analysis update: `true`
- Validation required before use: `true`

## Required Metadata

- `evidence_packet_id`
- `captured_at`
- `capture_mode`
- `source_id`
- `source_name`
- `source_category`
- `source_reference`
- `market_ids`
- `hypothesis_ids`
- `raw_excerpt_or_summary`
- `normalized_claims`
- `freshness_status`
- `contradiction_candidates`
- `limitations`
- `capture_errors`
- `auth_used`
- `credentials_used`
- `wallet_or_private_key_access`
- `orders_or_trading_actions`
- `safe_for_replay`

## Capture Policy

- Raw capture required: `true`
- Normalized claims required: `true`
- Retention: retain_with_task_artifacts_until_operator_reviewed_cleanup
- Redaction: If credential, session, wallet, or private material appears unexpectedly, block use and require separate local review.

## Safety Flags

- `auth_used`: `false`
- `credentials_used`: `false`
- `wallet_or_private_key_access`: `false`
- `orders_or_trading_actions`: `false`
- `safe_for_replay`: `true`
- `capture_context_must_be_explicit`: `true`

## Safety Boundary

- Evidence must be saved before replay.
- Saved evidence must validate before use.
- This plan performs no public fetch.
