# PMBOT Operator Token Selection Packet 073B

- Status: `selection_required`
- Market: `BTC`
- Strategy: `tiny-momentum`
- Mode: `operator token selection packet / dry-run / no-trading`
- allowed_for_live: `false`
- token_selection_executable: `false`
- candidate_index_base: `0`

## Candidates

- index `0` token_id `111128191581505463501777127559667396812474366956707382672202929745167742497287` market `microstrategy-sells-any-bitcoin-by-december-31-2026` outcome `Yes` sources `public_market_token_discovery_071a`
- index `1` token_id `99807503632459517030616292055983105381849115736225256331133222076990620978808` market `microstrategy-sells-any-bitcoin-by-december-31-2026` outcome `No` sources `public_market_token_discovery_071a`

## Selection

- selected_token_id_present: `false`
- selected_token_source_backed: `false`
- operator_provided: `false`
- token_id_format_status: `missing_optional`

## Operator Commands

- Review the candidate list. To select a source-backed candidate, rerun this packet with:

```powershell
python -m pm_bot.operator_runner.operator_token_selection_packet --market BTC --strategy tiny-momentum --dry-run --candidate-index 0
```

- To validate a manually supplied token ID without claiming it is source-backed, rerun with:

```powershell
python -m pm_bot.operator_runner.operator_token_selection_packet --market BTC --strategy tiny-momentum --dry-run --token-id <TOKEN_ID>
```

## Safe Next CLI Path

- none

## Safety

- This packet is review-only and non-executable.
- It does not invent token IDs.
- It does not build an order payload.
- It does not sign, submit, cancel, connect a wallet, read secrets, or call authenticated trading endpoints.
- The selected token, if any, still requires separate supervised validation through 070B/072A before any future task can even be reviewed.
