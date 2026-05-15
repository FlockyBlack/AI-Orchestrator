# ORCH-PMBOT-TRADING-MVP-072C Local Real-Check Bundle No Live

## Purpose

This task adds a manual one-shot operator runner for the safe local real-check sequence:

```bash
python -m pm_bot.operator_runner.local_real_check_bundle --market BTC --strategy tiny-momentum --dry-run
```

Optional guarded signer diagnostic:

```bash
python -m pm_bot.operator_runner.local_real_check_bundle --market BTC --strategy tiny-momentum --dry-run --allow-private-key-diagnostic
```

The optional flag is passed only to `pm_bot.trading_core.guarded_signer_diagnostic_smoke.run_guarded_signer_diagnostic_smoke`.

## Sequence

The bundle executes these subchecks sequentially and records each status independently:

1. `clob_l2_auth_readonly_probe_067c`
2. `live_account_readonly_state_probe_070c`
3. `guarded_signer_diagnostic_smoke_069a`
4. `public_market_token_discovery_071a`
5. `discovery_to_token_resolver_bridge_071d`
6. `live_readonly_status_aggregator_071b`

If a subcheck blocks or fails, the bundle still writes its consolidated artifacts and marks the specific subcheck as blocked or failed. It does not infer success from later subchecks.

## Safety Contract

- `allowed_for_live=false` always
- `bundle_executable_for_live=false` always
- no order submission
- no order cancellation
- no order payload signing
- no trading write endpoints
- no live trading enablement
- no browser automation
- no scheduler, daemon, background worker, or autonomous loop
- bundle artifacts embed sanitized status summaries only, not raw subcheck payloads
- default mode does not request the private-key diagnostic

## Bundle Artifacts

Default artifact directory:

`pm_bot/trading_core/artifacts/local_real_check_bundle_072c/`

Files:

- `local_real_check_bundle_072c_result.json`
- `latest_local_real_check_bundle_status_072c.json`
- `local_real_check_bundle_subchecks_072c.json`
- `local_real_check_bundle_blockers_072c.json`
- `local_real_check_bundle_safety_snapshot_072c.json`
- `local_real_check_bundle_operator_summary_072c.md`

The default local run completed with blockers because L2 credentials were missing, the guarded signer diagnostic was not explicitly requested, and the discovery-to-token bridge required operator selection among multiple source-backed token candidates. This is expected and remains non-live.

## Operator Notes

The runner is designed for supervised local diagnostics only. A successful read-only probe or signer diagnostic does not change live readiness: live execution remains blocked, and a separate operator-approved task would still be required for any future live path.
