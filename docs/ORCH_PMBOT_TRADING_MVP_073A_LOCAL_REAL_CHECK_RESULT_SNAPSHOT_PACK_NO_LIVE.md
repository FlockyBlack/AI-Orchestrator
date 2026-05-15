# ORCH PMBOT Trading MVP 073A Local Real-Check Result Snapshot Pack

Task ID: `ORCH-PMBOT-TRADING-MVP-073A-LOCAL-REAL-CHECK-RESULT-SNAPSHOT-PACK-NO-LIVE`

073A creates a local, redacted result snapshot for real operator checks already available after 072G-era work. It does not run the checks, call the network, read environment secrets, sign payloads, submit orders, cancel orders, connect wallets, or create live-capable output.

## Operator Command

```bash
python -m pm_bot.operator_runner.local_real_check_snapshot --market BTC --strategy tiny-momentum --dry-run
```

`--include-latest-artifacts` is enabled by default. Use `--no-include-latest-artifacts` only when the snapshot should ignore latest-status artifacts and read primary result artifacts where present.

## Inputs

The snapshot reads known local JSON artifacts only:

- `local_real_check_bundle_072c`
- `clob_l2_auth_readonly_probe_067c`
- `live_account_readonly_state_probe_070c`
- `guarded_signer_diagnostic_smoke_069a`
- `public_market_token_discovery_071a`
- `discovery_to_token_resolver_bridge_071d`
- `order_prep_packet_072a`
- `first_live_order_final_blocker_reducer_072d`

Missing artifacts stay `missing`; unreadable artifacts stay `unreadable`; absent status values stay `unknown`. No success is inferred from missing evidence.

## Outputs

The command writes:

- `pm_bot/trading_core/artifacts/local_real_check_snapshot_073a/local_real_check_snapshot_073a_result.json`
- `pm_bot/trading_core/artifacts/local_real_check_snapshot_073a/latest_local_real_check_snapshot_status_073a.json`
- `pm_bot/trading_core/artifacts/local_real_check_snapshot_073a/local_real_check_snapshot_sources_073a.json`
- `pm_bot/trading_core/artifacts/local_real_check_snapshot_073a/local_real_check_snapshot_normalized_status_073a.json`
- `pm_bot/trading_core/artifacts/local_real_check_snapshot_073a/local_real_check_snapshot_next_actions_073a.json`
- `pm_bot/trading_core/artifacts/local_real_check_snapshot_073a/local_real_check_snapshot_safety_snapshot_073a.json`
- `pm_bot/trading_core/artifacts/local_real_check_snapshot_073a/local_real_check_snapshot_operator_summary_073a.md`

## Normalized Status Fields

The ingestion pack exposes these normalized statuses:

- `l2_auth_status`
- `account_readonly_status`
- `signer_diagnostic_status`
- `public_discovery_status`
- `token_bridge_status`
- `order_prep_packet_status`
- `final_blocker_status`

Each status includes source metadata in the JSON output: source id, source path, parse status, candidate paths, and file modification timestamp when available. Raw source payloads are not embedded.

## Default Snapshot Summary

The default run in this worktree produced:

- `status=local_real_check_snapshot_recorded_live_blocked`
- `sources_present=8/8`
- `sources_missing=0`
- `sources_unreadable=0`
- `l2_auth_status=blocked_missing_l2_credentials`
- `account_readonly_status=account_config_not_detected`
- `signer_diagnostic_status=diagnostic_not_requested`
- `public_discovery_status=source_backed_candidates_ready`
- `token_bridge_status=blocked_no_latest_discovery_artifact`
- `order_prep_packet_status=blocked_order_prep_packet_not_ready`
- `final_blocker_status=blocked_remaining_first_live_order_final_blockers`
- `allowed_for_live=false`
- `snapshot_executable_for_live=false`

## Safety Statement

073A is a local artifact snapshot and ingestion pack only. It does not run subchecks by default, read raw secrets, call network services, submit orders, cancel orders, sign order payloads, connect wallets, use authenticated trading write endpoints, generate fake evidence, emit fake account/order/fill/PnL/token data, create browser automation, create schedulers, create daemons, or start background workers.
