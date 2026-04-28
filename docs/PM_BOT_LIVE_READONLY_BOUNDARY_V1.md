# PM Bot Live Read-Only Boundary V1

## Status

This document defines a future-only live/read-only fetcher boundary for PMBOT. PMBOT-BATCH-007 does not implement live fetching.

## Boundary Rules

- The future fetcher may only read public or separately approved market data.
- The future fetcher may not create orders, submit orders, or trigger execution.
- The future fetcher may not access any wallet, private key, signer, or execution credential.
- The future fetcher may not import execution modules.
- The future fetcher may not mutate runtime, state, results, freezes, or checkpoints.
- The future fetcher output must be a raw snapshot artifact only.
- The raw snapshot must be normalized and validated before any paper replay.
- Invalid, stale, malformed, or unsafe data must be quarantined.
- Live data cannot directly trigger execution.
- A watchlist cannot become an action.
- Any future live-data implementation requires separate human approval and Flocky validation.

## Allowed Future Output

The only allowed future fetcher output is a raw market snapshot that conforms to `pm_bot/contracts/raw_market_snapshot.schema.v1.json`.

## Required Future Flow

1. Read approved public market data.
2. Emit a raw snapshot artifact only.
3. Normalize the raw snapshot into the normalized contract.
4. Validate the normalized artifact.
5. Quarantine invalid artifacts.
6. Permit paper replay only after validation passes.

## Explicit Non-Scope For PMBOT-BATCH-007

- No live fetcher implementation
- No API calls
- No credentials
- No wallet access
- No private key access
- No signer access
- No order generation
- No trading logic
- No runtime wiring
- No dispatcher integration
- No `run_codex` integration
