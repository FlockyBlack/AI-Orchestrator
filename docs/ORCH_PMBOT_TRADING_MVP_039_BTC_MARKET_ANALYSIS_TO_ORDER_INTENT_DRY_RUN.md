# ORCH-PMBOT-TRADING-MVP-039 BTC Market Analysis To Order Intent Dry-Run

## Purpose

This task adds the dry-run-only bridge between the 038 BTC read-only market snapshot and the 037 risk limit control plane. It lets PMBOT consume a static/read-only `PolymarketBTCMarketSnapshot`, evaluate deterministic market-data conditions, build a non-executable `RiskLimitOrderIntent` candidate, and run that candidate through risk limits for dry-run review.

This is not live trading, not wallet integration, not signing, and not order submission.

## Why This Follows The 038 Connector

Task 038 established a BTC market snapshot contract with:

- read-only snapshot construction
- network disabled by default
- no authenticated endpoint support
- market freshness/status fields for risk control
- BTC UI market summary fields

Task 039 uses that snapshot as input and adds the next passive layer: analysis to dry-run intent to risk decision. It does not change the connector into an executable path.

## Analysis Schema

`pm_bot/trading_core/btc_market_analysis_order_intent.py` defines:

- `BTCMarketAnalysisConfig`
- `BTCMarketAnalysisInput`
- `BTCMarketSignalObservation`
- `BTCMarketAnalysisWarning`
- `BTCMarketAnalysisResult`
- `BTCDryRunOrderIntentPlan`
- `BTCOrderIntentDryRunResult`
- `BTCAnalysisRiskDecisionSummary`

The default config is conservative:

- `mode`: `dry_run_order_intent`
- `dry_run_only`: `true`
- `default_dry_run_notional_usd`: `1.0`
- `max_spread`: `0.05`
- `min_liquidity_usd`: `100.0`
- requires BTC/Bitcoin relation
- requires open, unresolved, fresh market data
- keeps `analysis_is_not_live_recommendation` true
- keeps `order_intent_is_not_order_submission` true

Analysis statuses are deterministic:

- `analysis_ready_for_dry_run_intent`
- `blocked_stale_market_data`
- `blocked_closed_or_resolved_market`
- `blocked_not_btc_market`
- `blocked_missing_required_prices`
- `blocked_spread_too_wide`
- `blocked_liquidity_too_low`
- `insufficient_data_for_intent`

## Dry-Run Order Intent Schema

For a valid fresh BTC fixture snapshot, the module builds a `RiskLimitOrderIntent`-compatible mapping with:

- `intent_source`: `btc_market_analysis_dry_run`
- `market_tag`: `BTC`
- deterministic side label: `track_primary_outcome`
- `notional_usd`: `1.0`
- `limit_price`: snapshot best ask when available
- `dry_run_only`: `true`
- `btc_market_snapshot_reference`
- `operator_intent_reference`
- `readiness_evidence_reference`
- `audit_replay_reference`

The intent remains an intent artifact only. It contains no signed order, transaction payload, auth header, API key, CLOB credentials, wallet data, or submission payload.

## Risk Control Integration

`evaluate_btc_analysis_to_order_intent(...)` runs the dry-run intent through `evaluate_risk_limits_for_order_intent(...)`.

Expected fixture behavior:

- valid fresh BTC snapshot: `ALLOW_DRY_RUN`
- stale BTC snapshot: `HALT`
- closed/resolved BTC snapshot: `HALT`
- non-BTC snapshot: `BLOCK`
- over-limit notional under policy: `BLOCK`

All live execution fields remain false:

- `allowed_for_live`
- `canary_executable_now`
- `live_execution_approved`
- `real_execution_available`
- `live_connector_enabled`

## Operator UI Integration

`pm_bot/operator_runner/operator_ui_panel_v1.py` now includes a BTC analysis/order intent section:

- `btc_market_analysis_status`
- `btc_intent_candidate_status`
- `dry_run_order_intent_status`
- `intent_market_id`
- `intent_market_slug`
- `intent_notional_usd`
- `intent_limit_price`
- `risk_decision_status`
- `allowed_for_dry_run`
- `allowed_for_live`
- `analysis_is_not_live_recommendation`
- `order_intent_is_not_order_submission`
- latest BTC analysis/order-intent/risk-decision artifact paths

The UI is review-only. It exposes no order placement control.

## Paper Daily Loop Integration

`pm_bot/operator_runner/paper_daily_loop.py` passively writes:

- `btc_market_analysis_039.json`
- `btc_order_intent_dry_run_039.json`
- `btc_risk_decision_039.json`

The daily dashboard also includes:

- `btc_market_analysis_summary`
- `btc_order_intent_dry_run_summary`
- `btc_risk_decision_summary`
- `btc_analysis_order_intent_summary`
- `btc_analysis_order_intent_section_feed`

No paper simulator fills or PnL are altered by this layer.

## Evidence And Blockers

The readiness evidence bundle now includes:

- `btc_market_analysis_to_order_intent_dry_run`

The item records whether analysis is ready, order intent dry-run is ready, risk decision is linked, and live execution is still disabled.

The live blocker matrix still keeps all critical blockers unresolved, including:

- `btc_analysis_order_intent_dry_run_only`
- `btc_order_intent_not_order_submission`
- `btc_order_intent_live_execution_still_disabled`
- `live_credentials_not_configured`
- `authenticated_order_connector_still_disabled`
- `real_order_submission_still_disabled`

## Fixture And Test Strategy

Tests use only static fixture payloads and deterministic in-memory mutations:

- valid fresh BTC snapshot
- stale BTC snapshot
- closed BTC snapshot
- resolved BTC snapshot
- non-BTC snapshot
- missing price fields
- wide spread
- low liquidity
- over-limit policy notional

Tests do not call external APIs and do not read environment secrets.

## Safety Wording

User-facing summaries avoid live trading advice wording. The module describes candidates as dry-run intent candidates or risk-checked dry-run intents, not as live recommendations.

The required safety flags remain explicit:

- `analysis_is_not_live_recommendation`: `true`
- `order_intent_is_not_order_submission`: `true`
- `allowed_for_live`: `false`

## Why Live Remains False

This task only proves deterministic local analysis and dry-run risk evaluation. Live remains false because there is still no approved credentials boundary, authenticated order connector, wallet access, signing adapter, live approval flow, or real order submission path.

## Next Step

Recommended next task:

`ORCH-PMBOT-TRADING-MVP-040-LIVE-CREDENTIALS-AUTH-BOUNDARY-FOR-TINY-CANARY`
