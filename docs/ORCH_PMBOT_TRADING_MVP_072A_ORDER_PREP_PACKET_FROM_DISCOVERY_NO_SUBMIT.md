# ORCH-PMBOT-TRADING-MVP-072A Order Prep Packet From Discovery No Submit

## Summary

072A adds a local, non-executable first-order preparation packet that combines the current discovery, token resolver, account, live read-only, signer diagnostic, approval, and signed-payload dry-run artifacts into one operator review surface.

The packet is intentionally blocked unless every readiness input is present and explicitly ready. It never submits orders, cancels orders, signs real order payloads by default, enables live trading, connects a wallet UI, or makes authenticated trading write calls.

## Operator Command

```powershell
python -m pm_bot.operator_runner.order_prep_packet --market BTC --strategy tiny-momentum --dry-run
```

Default output directory:

```text
pm_bot/trading_core/artifacts/order_prep_packet_072a/
```

## Generated Artifacts

- `order_prep_packet_072a_result.json`
- `latest_order_prep_packet_status_072a.json`
- `order_prep_packet_sources_072a.json`
- `order_prep_packet_operator_review_072a.json`
- `order_prep_packet_blockers_072a.json`
- `order_prep_packet_safety_snapshot_072a.json`
- `order_prep_packet_operator_summary_072a.md`

## Source Inputs

The builder reads local artifacts only from these directories when present:

- `public_market_token_discovery_071a`
- `discovery_to_token_resolver_bridge_071d`
- `first_order_market_token_resolver_070b`
- `live_account_readonly_state_probe_070c`
- `live_readonly_status_aggregator_071b`
- `guarded_signer_diagnostic_smoke_069a`
- `first_live_order_approval_contract_065d`
- `signed_order_payload_dry_run_070a`

Missing or unreadable inputs stay `missing` or `unreadable`; the packet does not fabricate balances, token IDs, approvals, signer status, payload status, orders, fills, PnL, order IDs, or transaction hashes.

## Blocking Rules

- Multiple source-backed token candidates set `operator_selection_required=true`.
- No selected token ID blocks the packet.
- Missing or failed 070C account probe blocks the packet.
- Missing or non-`diagnostic_ok` 069A signer diagnostic blocks the packet.
- Missing operator approval record blocks the packet.
- Missing or unready 070A signed-payload dry-run artifact blocks the packet.
- Any missing required local source artifact blocks the packet.

## Safety Snapshot

The packet always emits:

- `allowed_for_live=false`
- `order_prep_packet_executable=false`
- `order_submission_enabled=false`
- `order_cancellation_enabled=false`
- `signing_enabled=false`
- `wallet_connection_enabled=false`
- `authenticated_trading_call_performed=false`

The builder stores sanitized source summaries, readiness rows, blockers, and public token candidate metadata only. It does not embed full source payloads, raw private keys, API secrets, passphrases, full signed payloads, raw account values, raw order rows, fills, PnL, order IDs, or transaction hashes.

## Validation

The implementation was validated with the requested 072A focused test, adjacent component regressions, full `pm_bot/tests`, compile checks, operator runner commands, and diff checks. The default 072A runner currently emits a blocked packet because the checked-in local artifacts contain multiple source-backed token candidates and no selected token ID.
