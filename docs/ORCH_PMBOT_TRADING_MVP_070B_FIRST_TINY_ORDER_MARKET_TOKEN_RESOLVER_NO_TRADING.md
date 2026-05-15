# ORCH-PMBOT-TRADING-MVP-070B First Tiny Order Market Token Resolver

## Scope

070B adds a no-trading market/token resolver scaffold for the first supervised tiny Polymarket order preparation lane.

Allowed scope:

- market: `BTC`
- strategy: `tiny-momentum`
- mode: `dry-run`
- output: first-order market/token target contract only

The runner command is:

```bash
python -m pm_bot.operator_runner.first_order_market_token_resolver --market BTC --strategy tiny-momentum --dry-run
```

Optional operator-provided identifiers:

- `--market-slug`
- `--condition-id`
- `--token-id`
- `--outcome`

## Behavior

- `token_id` is validated as a positive decimal string when explicitly provided.
- `condition_id` is validated as a `0x`-prefixed 32-byte hex string when provided.
- `market_slug` is validated as lowercase letters, numbers, and hyphens when provided.
- If no explicit `token_id` is provided, status is `blocked_missing_token_id`.
- The resolver does not invent, infer, or fake a token ID.
- Local market discovery artifacts are reference-only and are not used to ingest token IDs.

## Artifacts

Artifacts are written to:

`pm_bot/trading_core/artifacts/first_order_market_token_resolver_070b/`

Required files:

- `first_order_market_token_resolver_070b_result.json`
- `latest_first_order_market_token_status_070b.json`
- `first_order_market_token_contract_070b.json`
- `first_order_market_token_validation_070b.json`
- `first_order_market_token_operator_summary_070b.md`

## Safety Statement

070B does not trade, sign, submit, cancel, authenticate trading calls, read credentials, use a wallet, generate order payloads, perform browser automation, create a scheduler or daemon, or run a background loop.

`allowed_for_live=false` is forced throughout the result, status, validation, and target contract artifacts.
