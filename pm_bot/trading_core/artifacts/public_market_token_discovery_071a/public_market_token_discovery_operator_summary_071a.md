# PMBOT Public Market Token Discovery 071A

- Status: `source_backed_candidates_ready`
- Market: `BTC`
- Strategy: `tiny-momentum`
- Market candidates: `1`
- Outcome token candidates: `2`
- Mode: `public read-only discovery`
- live execution blocked
- private_key_read=false
- wallet_connection_attempted=false
- signing_attempted=false
- order_submission_attempted=false
- order_cancellation_attempted=false
- authenticated_request_performed=false
- browser_automation_added=false
- scheduler_or_daemon_added=false
- allowed_for_live=false

## Source-Backed Markets

- `microstrategy-sells-any-bitcoin-by-december-31-2026` token candidates `2` source `public_local_artifact_read_only`

## Source-Backed Outcome Tokens

- `microstrategy-sells-any-bitcoin-by-december-31-2026` `Yes` token_id `111128191581505463501777127559667396812474366956707382672202929745167742497287` source_field `clobTokenIds`
- `microstrategy-sells-any-bitcoin-by-december-31-2026` `No` token_id `99807503632459517030616292055983105381849115736225256331133222076990620978808` source_field `clobTokenIds`

## Artifacts

- result: `pm_bot/trading_core/artifacts/public_market_token_discovery_071a/public_market_token_discovery_071a_result.json`
- latest_status: `pm_bot/trading_core/artifacts/public_market_token_discovery_071a/latest_public_market_token_discovery_status_071a.json`
- market_candidates: `pm_bot/trading_core/artifacts/public_market_token_discovery_071a/public_market_candidates_071a.json`
- outcome_token_candidates: `pm_bot/trading_core/artifacts/public_market_token_discovery_071a/public_outcome_token_candidates_071a.json`
- redaction_policy: `pm_bot/trading_core/artifacts/public_market_token_discovery_071a/public_market_token_discovery_redaction_policy_071a.json`
- operator_summary: `pm_bot/trading_core/artifacts/public_market_token_discovery_071a/public_market_token_discovery_operator_summary_071a.md`

## Operator Boundary

- This adapter discovers public metadata only.
- It does not create, sign, submit, or cancel anything.
- It does not use wallets, private keys, authenticated trading headers, browser automation, or background loops.
- Empty token candidates mean no source-backed token_id was available; nothing is invented.
