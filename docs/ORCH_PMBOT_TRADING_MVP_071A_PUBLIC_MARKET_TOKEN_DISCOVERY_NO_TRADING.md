# ORCH PMBOT Trading MVP 071A: Public Market Token Discovery

## Purpose

Task 071A adds a public read-only adapter for discovering source-backed Polymarket BTC market candidates and outcome token IDs.

Run:

```powershell
python -m pm_bot.operator_runner.public_market_token_discovery --market BTC --strategy tiny-momentum --dry-run
```

The adapter is intended only as a future review input for a separately approved supervised tiny-order task. It does not trade.

## Boundary

The 071A path is public/read-only and dry-run only:

- no private key reads
- no wallet access
- no signing
- no order generation
- no submit or cancel path
- no authenticated trading request
- no browser automation
- no scheduler, daemon, or background loop
- `allowed_for_live=false`

If a public source is unavailable and no source-backed local artifact is usable, the adapter writes fail-closed artifacts with status `discovery_unavailable`.

## Sources

The adapter can use:

- public Gamma market/event metadata through the existing `PublicGammaMarketClient` GET-only client
- existing local artifacts only when they already carry public Gamma source backing

It refuses deterministic fallback fixture token IDs and does not synthesize token IDs. Outcome token candidates are emitted only when token IDs are present in source-backed public market metadata fields such as `clobTokenIds`.

## Output Artifacts

Artifacts are written under:

```text
pm_bot/trading_core/artifacts/public_market_token_discovery_071a/
```

Files:

- `public_market_token_discovery_071a_result.json`
- `latest_public_market_token_discovery_status_071a.json`
- `public_market_candidates_071a.json`
- `public_outcome_token_candidates_071a.json`
- `public_market_token_discovery_redaction_policy_071a.json`
- `public_market_token_discovery_operator_summary_071a.md`

## Status Semantics

- `source_backed_candidates_ready`: at least one source-backed outcome token candidate is available.
- `source_backed_markets_without_token_ids`: public/source-backed markets were found, but no acceptable source-backed token ID was present.
- `no_source_backed_candidates`: sources were readable but no BTC-related candidate passed filters.
- `discovery_unavailable`: no usable public network source or source-backed local artifact was available.

All statuses remain non-executable and `allowed_for_live=false`.

## Validation Focus

The focused tests cover:

- no private key/API secret reads
- no authenticated trading calls
- no submit/cancel/signing calls
- no fake token IDs
- fail-closed behavior when public discovery is unavailable
- source-backed candidate marking
- `allowed_for_live=false`
- runner artifact emission

## Safety Statement

Task 071A discovers public metadata only. It does not create orders, sign payloads, submit, cancel, authenticate trading, inspect wallets, read secrets, or provide actionable trading advice.
