# ORCH-PMBOT-TRADING-MVP-038 Polymarket BTC Read-Only Market Connector

## Purpose

This task adds the first direct BTC/Bitcoin-related market data integration boundary for the one-market PMBOT live-demo path. It creates a read-only connector and deterministic market snapshot layer that can feed the Operator UI Panel, Risk Limit Control Plane, daily paper-loop artifacts, and future BTC market-analysis dry-run work.

This is not live trading. It does not add wallet access, private-key handling, signing, authenticated endpoints, or order submission.

## Read-Only Boundary

The connector is implemented in `pm_bot/trading_core/polymarket_btc_read_only_connector.py`.

Safe defaults:

- `mode`: `read_only`
- `read_only`: `true`
- `network_enabled`: `false`
- `authenticated`: `false`
- `order_submission_supported`: `false`
- `wallet_required`: `false`
- `allowed_for_live`: `false`
- `live_execution_approved`: `false`
- `canary_executable_now`: `false`
- `real_execution_available`: `false`
- `live_connector_enabled`: `false`

The optional public fetch boundary is GET-only and requires both `network_enabled == true` and an explicit `operator_read_only_network_allowed == true`. It rejects non-HTTPS endpoints and endpoint shapes that look like auth, wallet, CLOB, signing, trading, or order-submission boundaries. Tests do not call the network.

## Config Schema

`PolymarketBTCReadOnlyConfig` includes:

- `config_id`
- `mode`
- `market_id`
- `market_slug`
- `market_url`
- `allowed_market_tags`
- `public_endpoint_url`
- `network_enabled`
- `max_snapshot_age_seconds`
- `expected_outcome_count`
- `require_open_market`
- `require_not_resolved`
- `require_btc_tag`
- `allow_fixture_payloads`
- `source_label`
- static safety fields for read-only, auth, order, wallet, and live-execution posture

`validate_btc_read_only_config(...)` rejects non-BTC configs when BTC validation is required and rejects forbidden secret/auth/order fields through the static secret-boundary policy.

## Snapshot Schema

`PolymarketBTCMarketSnapshot` records:

- snapshot identity, market id/slug/title, normalized tags, and BTC-related detection
- market status: `open`, `closed`, `resolved`, or `unknown`
- `is_open`, `is_closed`, `is_resolved`
- observed/fetched timestamps, evaluated age, and stale flag
- outcome rows with optional price/probability/bid/ask/last/liquidity fields
- market-level bid/ask/last/spread/liquidity when present
- explicit `price_status` when price data is unavailable
- source label and payload hash
- `risk_control_market_data_status`
- UI summary

The connector does not invent prices, liquidity, outcomes, or resolutions. Missing price fields remain `null` and are marked `not_available`.

## Payload Normalization

The normalizer supports tolerant fixture-style payloads for market id, slug, title/question, tags, active/open/closed/resolved flags, outcomes, prices/probabilities, liquidity, and timestamps. Malformed payloads produce deterministic rejection errors.

## Fixture Strategy

The fixture at `pm_bot/tests/fixtures/trading_core/polymarket_btc_market_sample_038.json` represents one BTC-related unresolved market with two outcomes and sample price/liquidity fields. The daily paper loop uses a static fixture payload generated in-process. Validation is deterministic and performs no external API calls.

## Risk Control Integration

`pm_bot/trading_core/risk_limit_control_plane.py` now accepts BTC market snapshot fields in `RiskLimitState`. A fresh open BTC snapshot can support dry-run evaluation for a valid dry-run intent. Stale, closed, resolved, non-BTC, or mismatched snapshot data blocks or halts according to the policy. Live allowance remains forced false.

## Operator UI Integration

`pm_bot/operator_runner/operator_ui_panel_v1.py` adds a `btc_market_connector` section with:

- connector status
- market id/slug/title
- BTC-related flag
- market status, open/resolved flags, stale flag, and age
- best bid, best ask, last price, spread, liquidity, and price status when available
- risk-control market-data status
- read-only network status
- latest snapshot artifact path

The UI remains a static, non-execution panel and exposes no order buttons or live actions.

## Paper Daily Loop Integration

`pm_bot/operator_runner/paper_daily_loop.py` emits passive BTC connector outputs:

- `btc_market_snapshot_038.json`
- `btc_market_snapshot_summary`
- `btc_read_only_connector_summary`
- `btc_market_section_feed`
- market freshness fields in the risk-control feed

The loop does not alter paper simulator fills, PnL, outcomes, or execution behavior.

## Evidence And Blockers

`pm_bot/trading_core/live_canary_readiness_evidence_bundle.py` adds `btc_read_only_market_connector` as review evidence. The item is read-only, network-disabled by default, non-execution enabling, and not live approval.

The live blocker matrix adds unresolved critical categories for:

- `btc_read_only_connector_review_only`
- `btc_market_snapshot_not_live_trade_approval`
- `btc_market_analysis_not_yet_order_intent`
- `authenticated_live_order_connector_still_disabled`
- `real_order_submission_still_disabled`

Existing critical live blockers remain unresolved.

## Secret Boundary

`pm_bot/trading_core/secret_boundary_policy.py` extends BTC validation helpers and rejects private keys, mnemonics, seed phrases, signatures, signed orders/payloads, raw transactions, auth headers, bearer/API/access tokens, order payloads, transaction payloads, authorization/cookie fields, and CLOB credential fields.

The connector never reads environment variables or inspects real secrets.

## Next Step

The next recommended task is `ORCH-PMBOT-TRADING-MVP-038B-MERGE-POLYMARKET-BTC-READ-ONLY-MARKET-CONNECTOR-INTO-MASTER`, followed by BTC market analysis to order-intent dry-run work. Live execution remains disabled until separately approved future tasks add and validate the required credential, auth, order, wallet, signing, funding, audit, kill-switch, and operator-approval boundaries.
