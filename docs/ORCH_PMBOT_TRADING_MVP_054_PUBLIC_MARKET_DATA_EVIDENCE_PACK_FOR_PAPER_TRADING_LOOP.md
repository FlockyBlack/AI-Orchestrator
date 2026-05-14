# ORCH-PMBOT-TRADING-MVP-054 Public Market Data Evidence Pack For Paper Trading Loop

## Scope

054 adds a public/read-only Polymarket Gamma market data path for the accepted 053 paper trading loop.

The operator command is:

```text
python -m pm_bot.operator_runner.public_market_paper_loop --market BTC --strategy tiny-momentum --dry-run
```

Optional controls:

- `--query`
- `--slug`
- `--tag-id`
- `--limit`
- `--fixture-fallback`
- `--artifacts-dir`
- `--json`
- `--offline-fixture-only`

The flow remains paper/review-only. It does not enable live trading.

## Public Gamma Read-Only Boundary

Allowed in 054:

- HTTP `GET` only to public Gamma endpoints.
- Default base URL: `https://gamma-api.polymarket.com`.
- Configurable base URL: `PMBOT_GAMMA_BASE_URL`.
- Preferred active market discovery pattern: `/events?active=true&closed=false&limit=...`.
- Direct public market search via `/markets` when a slug/filter is supplied.
- Public event/market metadata parsing, including public token ids as market metadata only.

Not allowed in 054:

- authenticated CLOB endpoints
- private keys
- wallet connection
- signing
- signed payload creation
- live order submission or cancellation
- balances, positions, fills, transaction hashes, or PnL
- scheduler, daemon, background worker, or continuous polling

## Fixture Fallback Behavior

Default behavior tries public Gamma read-only fetch unless `--offline-fixture-only` is passed.

Fallback rules:

- `--offline-fixture-only` skips network and uses deterministic fixture fallback.
- `--fixture-fallback` permits deterministic fixture fallback when the public Gamma fetch or public normalization path fails.
- Without `--fixture-fallback`, a public fetch failure fails closed and writes `public_market_fetch_error_054.json`.
- The latest status always reports the source as either `public_gamma_live_read_only` or `fixture_fallback`.

The fixture fallback is intentionally deterministic so default tests pass offline.

## Evidence Pack Schema

054 writes:

- `public_gamma_request_evidence_054.json`
- `public_gamma_response_evidence_054.json`
- `public_market_evidence_pack_054.json`
- `normalized_public_market_snapshot_054.json`

The evidence pack includes:

- `source_name`
- `source_type`
- `base_url`
- `endpoint_path`
- `sanitized_query`
- `request_method=GET`
- `request_timestamp_utc`
- `response_timestamp_utc`
- `status_code` when network was used
- `network_used`
- `auth_used=false`
- `credentials_used=false`
- `wallet_used=false`
- `signing_used=false`
- `order_endpoint_used=false`
- `normalized_market_count`
- `selected_market_reason`
- `raw_response_hash`
- `response_snapshot_hash`
- `artifact_paths`

The evidence pack does not store API keys, tokens, cookies, credential values, private keys, wallet credentials, or signed payloads.

## Integration With 053 Paper Loop

Vertical flow:

```text
PublicGammaMarketDiscovery
-> PublicMarketEvidenceSnapshot
-> NormalizedPublicMarketSnapshot
-> 053 PaperTradingLoop
-> StrategySignal or NoSignal
-> PaperExecutionRisk
-> PaperOrderIntent only when paper risk passes
-> JSON/Markdown artifacts
-> LatestStatus
-> passive Operator UI / Telegram summaries
```

The 053 loop now accepts an optional supplied `MarketSnapshot`-compatible mapping. Existing 053 fixture behavior remains the default, so this command still works unchanged:

```text
python -m pm_bot.operator_runner.paper_trading_loop --market BTC --strategy tiny-momentum --dry-run
```

The 052 paper canary command also remains unchanged:

```text
python -m pm_bot.operator_runner.paper_canary_drill --market BTC --dry-run
```

## Generated Artifacts

Default artifact directory:

```text
pm_bot/trading_core/artifacts/public_market_paper_loop_054/
```

Required artifacts:

- `public_market_paper_loop_054_result.json`
- `public_market_paper_loop_054_operator.md`
- `latest_public_market_paper_status_054.json`
- `public_gamma_request_evidence_054.json`
- `public_gamma_response_evidence_054.json`
- `public_market_evidence_pack_054.json`
- `normalized_public_market_snapshot_054.json`
- `public_market_strategy_signal_054.json`
- `public_market_risk_054.json`
- `public_market_order_intent_054.json` only when risk passes
- `public_market_no_signal_054.json` only when no signal occurs
- `public_market_fetch_error_054.json` only when public fetch fails

The checked-in sample latest status records the source produced by the most recent safe operator command. `public_market_fetch_error_054.json` is present only when a public Gamma read-only fetch fails before fallback is used.

## Operator UI And Telegram

The passive operator UI and Telegram summaries expose latest public market paper status when supplied in dashboard/context data.

They show:

- source: `public_gamma_live_read_only` or `fixture_fallback`
- evidence pack path
- paper/review-only mode
- live execution blocked
- risk decision
- paper intent summary without implying execution

They do not add live approve buttons, wallet controls, signing controls, auth controls, order controls, or execution buttons.

## Safety Invariants

All 054 outputs preserve:

- `execution_mode=paper`
- `review_only=true`
- `live_execution_approved=false`
- `canary_executable_now=false`
- `real_execution_available=false`
- `order_submission_enabled=false`
- `wallet_signing_enabled=false`
- `signing_enabled=false`
- `signed_payload_generation_enabled=false`
- `signed_order_generation_enabled=false`
- `authenticated_polymarket_enabled=false`
- `live_connector_enabled=false`
- `allowed_for_live=false`
- `resolved_blocker_count=0`
- `auth_used=false`
- `credentials_used=false`
- `wallet_used=false`
- `signing_used=false`
- `order_endpoint_used=false`

Token ids may appear as public market metadata. They are never treated as order ids, transaction hashes, fill ids, or execution records.

## Forbidden Runtime Behavior

054 runtime modules do not introduce:

- `PRIVATE_KEY`
- `API_SECRET`
- `PASSPHRASE`
- `POLYMARKET_PK`
- `POLYMARKET_PRIVATE_KEY`
- `POLYGON_WALLET_PRIVATE_KEY`
- `Authorization`
- `Bearer`
- `Wallet(`
- `Signer`
- `OrderBuilder`
- `createAndPostOrder`
- `placeOrder`
- `postOrder`
- `cancelOrder`
- `sign_order`
- `signed_payload`
- `tx_hash`
- `fill_id`
- `filled_size`
- `fill_price`
- `balance`
- `pnl`
- private-key reads
- API secret reads
- raw credential reads
- wallet connection
- signing
- authenticated Polymarket calls
- order submission
- order cancellation
- fake execution identifiers
- fake fills
- fake financial state
- schedulers, daemons, background workers, or autonomous loops

The implementation is an operator-triggered one-shot review flow only.
