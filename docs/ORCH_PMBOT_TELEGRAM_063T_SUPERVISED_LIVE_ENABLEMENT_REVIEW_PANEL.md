# ORCH-PMBOT-TELEGRAM-063T Supervised Live Enablement Review Panel

## Scope

This task extends the Telegram operator console with a review-only panel for the accepted 063 supervised tiny live enablement gate. The panel surfaces local 063 artifacts for operator inspection and exposes exactly one safe dry-run action.

Source artifact directory:

- `pm_bot/trading_core/artifacts/supervised_tiny_live_enablement_gate_063/`

Displayed source artifacts:

- `latest_supervised_tiny_live_enablement_status_063.json`
- `supervised_tiny_live_operator_checklist_063.json`
- `supervised_tiny_live_blockers_063.json`
- `supervised_tiny_live_risk_limits_063.json`
- `supervised_tiny_live_kill_switch_plan_063.json`
- `supervised_tiny_live_cancel_plan_063.json`
- `supervised_tiny_live_failure_plan_063.json`
- `supervised_tiny_live_env_readiness_063.json`
- `supervised_tiny_live_manual_approval_packet_063.json`
- `supervised_tiny_live_enablement_gate_063_operator.md`

## Telegram Surface

The status registry now includes `supervised_tiny_live_enablement_gate_063` as a first-class safe status item:

- EN: `Supervised live enablement gate`
- RU: `Гейт supervised live enablement`
- mode: review-only / dry-run-only visibility

The panel adds `/supervised_live_review` and the passive status callback `pmbot:supervised_live_review`.

The only new run control is `Run Supervised Gate 063 Dry-Run`, mapped to:

```powershell
python -m pm_bot.operator_runner.supervised_tiny_live_enablement_gate --market BTC --strategy tiny-momentum --dry-run
```

The callback/action identifiers are dry-run scoped:

- `run_supervised_tiny_gate_063_review_dry_run`
- `pmbot:run:supervised_tiny_gate_063_review_dry_run`

## Review Sections

The Telegram review text summarizes:

- supervised live enablement status
- operator checklist
- blocker matrix
- risk limits
- kill switch plan
- cancel plan
- failure plan
- environment readiness as presence-only and redacted
- manual approval packet

RU/EN labels include:

- `Review only` / `Только просмотр`
- `Dry-run only` / `Только dry-run`
- `Not executable` / `Не исполняется`
- `Operator approval required` / `Требуется подтверждение оператора`

## Safety State

063T does not add approve-live, send-order, submit-order, cancel-order, sign, signer, wallet, connect-wallet, unlock-wallet, live-enable, or live-execute controls.

The registry, Telegram responses, and 063T artifacts preserve:

- `live_execution_approved=false`
- `canary_executable_now=false`
- `real_execution_available=false`
- `order_submission_enabled=false`
- `order_cancel_enabled=false`
- `wallet_signing_enabled=false`
- `signing_enabled=false`
- `signed_payload_generation_enabled=false`
- `signed_order_generation_enabled=false`
- `authenticated_polymarket_enabled=false`
- `live_connector_enabled=false`
- `allowed_for_live=false`
- `operator_approved=false`
- `candidate_is_executable=false`
- `resolved_blocker_count=0`

Environment readiness is rendered from redacted presence metadata only. Telegram does not print raw environment values, private keys, mnemonics, seed phrases, API secrets, auth tokens, account runtime values, order IDs, transaction hashes, balances, positions, fills, or PnL.

## Artifacts

063T writes:

- `pm_bot/trading_core/artifacts/telegram_supervised_live_enablement_review_063t/telegram_supervised_live_enablement_review_063t_result.json`
- `pm_bot/trading_core/artifacts/telegram_supervised_live_enablement_review_063t/latest_telegram_supervised_live_enablement_review_status_063t.json`
- `pm_bot/trading_core/artifacts/telegram_supervised_live_enablement_review_063t/telegram_supervised_live_enablement_review_controls_063t.json`
- `pm_bot/trading_core/artifacts/telegram_supervised_live_enablement_review_063t/telegram_supervised_live_enablement_review_registry_snapshot_063t.json`

## Validation

Focused validation:

```powershell
python -m pytest pm_bot/tests/test_telegram_supervised_live_enablement_review_063t.py
python -m pytest pm_bot/tests/test_supervised_tiny_live_enablement_gate_063.py
python -m pytest pm_bot/tests/test_telegram_pre_live_gate_review_062t.py
python -m pytest pm_bot/tests/test_pre_live_tiny_order_gate_062p.py
python -m pytest pm_bot/tests/test_telegram_tiny_order_review_061t.py
python -m pytest pm_bot/tests/test_tiny_order_scaffold_061.py
python -m pytest pm_bot/tests/test_telegram_operator_console_060t.py
python -m pytest pm_bot/tests/test_static_safety_invariant_report_060q.py
python -m pm_bot.operator_runner.telegram_runtime_smoke
python -m pm_bot.operator_runner.static_safety_invariant_report --scope pm_bot --dry-run
```

Full validation is recorded in `docs/ORCH_PMBOT_TELEGRAM_063T_SUPERVISED_LIVE_ENABLEMENT_REVIEW_PANEL_RESULT.json`.
