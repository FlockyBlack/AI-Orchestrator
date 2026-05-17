# ORCH-PMBOT-RUNTIME-078C CLOB SDK Detection And Read-Only Balance Probe

## Scope

This task improves PMBOT 070C live-account read-only diagnostics and Telegram balance display for Polymarket CLOB SDK availability.

## Implemented

- 070C now imports and reports candidate SDK modules: `py_clob_client`, `py_clob_client.client`, and `py_clob_client_v2`.
- SDK diagnostics now include candidate installed/missing status, import error type, selected module, expected module, expected install command, Python executable, and safe pip package visibility.
- Missing L2 credentials still block account probing, but import-only SDK diagnostics are recorded before any credential object or client creation.
- Telegram Balance now displays SDK unavailable diagnostics, safe install guidance, and the Python executable when the local 070C artifact reports SDK unavailability.
- Tests cover SDK missing, v1 present, v2 present, import error redaction, missing credentials with SDK diagnostics, and no fake balance emission.

## Safety

- No live trading was added.
- No submit/cancel/write endpoint code was added.
- No signer is instantiated by SDK detection.
- No private key or wallet-connect UI is used.
- No raw secrets, fake balances, fake PnL, fake orders, or fake positions are emitted.
- `allowed_for_live` and `trading_requested` remain false.

## Validation

- `python -m pytest pm_bot/tests/test_clob_sdk_detection_078c.py` passed.
- `python -m pytest pm_bot/tests/test_live_account_readonly_state_probe_070c.py` passed.
- `python -m pytest pm_bot/tests/test_telegram_balance_readonly_account_077f.py` passed.
- `python -m pytest pm_bot/tests/test_artifact_dir_consistency_078a.py` passed.
- `python -m pytest pm_bot/tests/test_static_safety_invariant_report_060q.py` passed.
- `python -B -m pytest pm_bot/tests` passed: 2301 tests.
- `python -m compileall -q pm_bot` passed.
- `python -m compileall -q ai_orchestrator` passed.
- `python -m pm_bot.operator_runner.live_account_readonly_state_probe --market BTC --strategy tiny-momentum --dry-run` passed with credential env vars cleared for safety.
- `python -m pm_bot.operator_runner.telegram_runtime_smoke --json` passed with credential env vars cleared for safety.
- `python -m pm_bot.operator_runner.static_safety_invariant_report --scope pm_bot --dry-run` passed with 0 critical findings.

