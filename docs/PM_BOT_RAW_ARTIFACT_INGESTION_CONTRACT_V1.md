# PM Bot Raw Artifact Ingestion Contract V1

## Purpose

The raw artifact ingestion gate is a deterministic offline validation layer for local raw market snapshot artifacts. It exists before any live fetcher implementation so PMBOT can define what a future read-only capture artifact must look like and what must be quarantined before normalization or replay can ever see it.

This stage does not implement a fetcher, client, network integration, or runtime wiring. It only validates local JSON fixtures.

## Allowed source types

- `fixture`
- `manual_snapshot`
- `future_readonly_fetcher_output`

These labels are descriptive only. In this stage, only local fixture files are accepted by the validator.

## Raw artifact shape

Top-level required fields:

- `contract_version`
- `artifact_id`
- `source_type`
- `source_name`
- `captured_at`
- `market`
- `outcomes`
- `provenance`
- `safety`

Contract rules:

- `contract_version` must equal `raw_market_artifact.v1`
- `artifact_id` must be a deterministic non-empty string
- `captured_at` must be ISO-like and is checked against a deterministic reference time
- `market.market_id`, `market.title`, and `market.status` are required
- `outcomes` must be a non-empty list
- each outcome requires `name`, `side`, and `price`
- prices must be numeric and inside `[0, 1]`
- outcome names and sides must not conflict
- `provenance` must identify collector, collection method, and source reference
- `safety` must explicitly encode offline-safe intent

Required safety flags:

- `network_used: false`
- `api_credentials_used: false`
- `wallet_used: false`
- `order_capable: false`
- `trading_capable: false`
- `readonly_intended: true`

## Validation and quarantine model

The validator inspects local JSON files under `pm_bot/raw_artifacts/fixtures/`.

- files under `valid/` are expected to pass
- files under `invalid/` are expected to fail for deterministic reasons
- malformed, stale, conflicting, or unsafe artifacts produce quarantine findings
- an invalid fixture that passes is an `unexpected_pass`
- a valid fixture that fails is an `unexpected_failure`
- the full suite passes only when valid fixtures pass and invalid fixtures fail as intended

## Future fetcher constraint

If a future read-only fetcher is separately approved, it must produce artifacts that satisfy this contract before any normalization or replay step is allowed to consume them. The future fetcher must remain read-only and must not bypass quarantine.

## Still forbidden

- no live fetcher implementation in this batch
- no network or API calls
- no live Polymarket client imports
- no credentials
- no wallet or private key handling
- no order creation
- no trading logic
- no runtime wiring
- no dispatcher or `run_codex` integration
