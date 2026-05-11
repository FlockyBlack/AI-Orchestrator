# PMBOT One-Command Operator Runner

## Command

```bash
python -m pm_bot.operator_runner.run_operator_workflow_once --out-dir pm_bot/operator_runner/artifacts/night_020_021/run_001 --include-trading-core --no-live-fetch --no-real-trading
```

## Behavior

The runner:

- runs once
- exits
- writes a run result
- writes a final operator report
- writes safety scan results
- uses only local artifacts
- does not call live network services
- does not create scheduler, daemon, watcher, background worker, polling loop, or automatic repeat behavior

## Main outputs

- `pm_bot/operator_runner/artifacts/night_020_021/operator_workflow_config.json`
- `pm_bot/operator_runner/artifacts/night_020_021/operator_runner_dashboard.json`
- `pm_bot/operator_runner/artifacts/night_020_021/run_001/operator_workflow_run_result.json`
- `pm_bot/operator_runner/artifacts/night_020_021/run_001/final_operator_report.json`
- `pm_bot/operator_runner/artifacts/night_020_021/run_001/operator_workflow_safety_scan.result.json`
- `pm_bot/operator_runner/artifacts/night_020_021/run_001/trading_core/paper_trading_dashboard.json`

## Safety status

The completed run reports:

- `run_once: true`
- `repeat_count: 1`
- `steps_passed: 13`
- `steps_failed: 0`
- `safety_ok: true`
- live fetch false
- real trading false
- wallet false
- orders false
- scheduler false
- daemon false
- background worker false
