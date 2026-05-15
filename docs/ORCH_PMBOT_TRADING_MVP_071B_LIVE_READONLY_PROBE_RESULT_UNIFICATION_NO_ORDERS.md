# ORCH-PMBOT-TRADING-MVP-071B Live Read-Only Probe Result Unification

## Purpose

This task adds a local-only status model for read-only live readiness signals. It unifies the latest local artifacts from:

- 067C CLOB L2 auth read-only probe
- 070C live account read-only state probe, when present
- 067E Telegram wallet/auth status dashboard, when present

Command:

```bash
python -m pm_bot.operator_runner.live_readonly_status_aggregator --market BTC --strategy tiny-momentum --dry-run
```

## Behavior

The aggregator reads fixed JSON artifact filenames under `pm_bot/trading_core/artifacts` by default. It does not scan the filesystem recursively and does not read environment variables, wallet files, browser profiles, credential stores, or secret paths.

Aggregated fields:

- `l2_auth_status`
- `open_orders_status`
- `balance_status`
- `allowance_status`
- `wallet_address_status`
- `funder_status`
- `signature_type_status`

Missing source artifacts produce `unknown` fields unless another local source artifact provides a concrete redacted status. The aggregator does not fabricate balances, PnL, order rows, fills, positions, account values, wallet values, or probe success.

## Artifacts

Default artifact directory:

```text
pm_bot/trading_core/artifacts/live_readonly_status_aggregator_071b/
```

Files:

- `live_readonly_status_aggregator_071b_result.json`
- `latest_live_readonly_status_071b.json`
- `live_readonly_status_sources_071b.json`
- `live_readonly_status_safety_snapshot_071b.json`
- `live_readonly_status_operator_summary_071b.md`

Current generated status in this worktree:

- `l2_auth_status=blocked_missing_l2_credentials`
- `open_orders_status=not_available`
- `balance_status=not_available`
- `allowance_status=not_available`
- `wallet_address_status=missing`
- `funder_status=missing`
- `signature_type_status=missing`
- 067C source available: `true`
- 070C source available: `false`
- 067E source available: `true`

## Safety Statement

`allowed_for_live=false` remains hard-coded. This task does not add live trading, order submission, order cancellation, signing, signer instantiation, wallet connection, private-key reads, authenticated write calls, network calls, browser automation, schedulers, daemons, background workers, or autonomous trading.
