# ORCH-PMBOT-TELEGRAM-061T Tiny Order Scaffold Review Panel

## Scope

This task extends the Telegram operator console with a review-only 061 tiny order scaffold panel. The console can display the latest tiny candidate, manual approval packet path, hard limits, and submission availability status from:

- `pm_bot/trading_core/artifacts/tiny_order_scaffold_061/latest_tiny_order_scaffold_status_061.json`
- `pm_bot/trading_core/artifacts/tiny_order_scaffold_061/manual_tiny_order_approval_packet_061.json`
- `pm_bot/trading_core/artifacts/tiny_order_scaffold_061/tiny_order_candidate_061.json`
- `pm_bot/trading_core/artifacts/tiny_order_scaffold_061/tiny_order_hard_limits_061.json`
- `pm_bot/trading_core/artifacts/tiny_order_scaffold_061/tiny_order_submission_availability_061.json`

## Telegram Surface

The panel adds a `Tiny Order Review` section with:

- `Tiny Candidate`
- `Approval Packet`
- `Hard Limits`
- `Submission Status`
- `Run Tiny Scaffold Dry-Run`

The only new run control is `Run Tiny Scaffold 061`, mapped to:

```powershell
python -m pm_bot.operator_runner.tiny_order_scaffold --market BTC --strategy tiny-momentum --dry-run
```

The Russian operator labels include:

- `Малый ордер`
- `Пакет ручного подтверждения`
- `Лимиты`
- `Оператор подтвердил: нет`
- `Кандидат не исполняемый`
- `Подписание заблокировано`
- `Отправка ордера заблокирована`
- `Live-торговля заблокирована`

## Safety State

061T remains review-only and paper-only. The registry and Telegram responses force these values:

- `live_execution_approved=false`
- `canary_executable_now=false`
- `real_execution_available=false`
- `order_submission_enabled=false`
- `wallet_signing_enabled=false`
- `signing_enabled=false`
- `signed_payload_generation_enabled=false`
- `signed_order_generation_enabled=false`
- `authenticated_polymarket_enabled=false`
- `live_connector_enabled=false`
- `allowed_for_live=false`
- `resolved_blocker_count=0`

The console does not add live submission, cancellation, signing, wallet, balance, position, fill, PnL, or autonomous execution controls.

## Artifacts

061T writes:

- `pm_bot/trading_core/artifacts/telegram_tiny_order_review_061t/telegram_tiny_order_review_061t_result.json`
- `pm_bot/trading_core/artifacts/telegram_tiny_order_review_061t/latest_telegram_tiny_order_review_status_061t.json`
- `pm_bot/trading_core/artifacts/telegram_tiny_order_review_061t/telegram_tiny_order_review_registry_snapshot_061t.json`

## Validation

Focused validation:

```powershell
python -m pytest pm_bot/tests/test_telegram_tiny_order_review_061t.py
python -m pytest pm_bot/tests/test_tiny_order_scaffold_061.py
python -m pytest pm_bot/tests/test_telegram_operator_console_060t.py
```

Full operator validation is recorded in `docs/ORCH_PMBOT_TELEGRAM_061T_TINY_ORDER_SCAFFOLD_REVIEW_PANEL_RESULT.json`.
