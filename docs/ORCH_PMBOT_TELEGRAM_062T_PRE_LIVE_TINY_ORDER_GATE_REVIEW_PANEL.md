# ORCH-PMBOT-TELEGRAM-062T Pre-Live Tiny Order Gate Review Panel

## Scope

This task extends the Telegram operator console with a review-only panel for the accepted 062P pre-live tiny order gate. The panel surfaces these 062P artifacts:

- `pm_bot/trading_core/artifacts/pre_live_tiny_order_gate_062p/latest_pre_live_tiny_order_gate_status_062p.json`
- `pm_bot/trading_core/artifacts/pre_live_tiny_order_gate_062p/pre_live_tiny_order_checklist_062p.json`
- `pm_bot/trading_core/artifacts/pre_live_tiny_order_gate_062p/pre_live_tiny_order_blockers_062p.json`
- `pm_bot/trading_core/artifacts/pre_live_tiny_order_gate_062p/pre_live_tiny_order_readiness_summary_062p.json`
- `pm_bot/trading_core/artifacts/pre_live_tiny_order_gate_062p/pre_live_tiny_order_gate_062p_operator.md`

## Telegram Surface

The status registry now includes `pre_live_tiny_order_gate_062p` as a first-class safe status item:

- EN: `Pre-live tiny order gate`
- RU: `Предлайв-гейт tiny order`
- mode: review-only / dry-run-only visibility

The panel adds `/pre_live_gate_review` and the safe status callback `pmbot:pre_live_gate_review`.

The only new run control is `Run Pre-live Gate 062P Dry-Run`, mapped to:

```powershell
python -m pm_bot.operator_runner.pre_live_tiny_order_gate --market BTC --strategy tiny-momentum --dry-run
```

The callback/action identifiers are explicitly review/dry-run scoped:

- `run_pre_live_tiny_order_gate_062p_review_dry_run`
- `pmbot:run:pre_live_tiny_order_gate_062p_review_dry_run`

## Safety State

062T does not add approve-live, send-order, submit-order, cancel-order, sign, wallet, connect-wallet, unlock-wallet, live-enable, or live-execute controls.

The registry, Telegram responses, and 062T artifacts preserve:

- `operator_approved=false`
- `candidate_is_executable=false`
- `signing_available=false`
- `signed_payload_available=false`
- `order_submission_available=false`
- `wallet_available=false`
- `live_execution_approved=false`
- `ready_for_future_live_enablement=false`
- `allowed_for_live=false`
- `resolved_blocker_count=0`

## Artifacts

062T writes:

- `pm_bot/trading_core/artifacts/telegram_pre_live_gate_review_062t/telegram_pre_live_gate_review_062t_result.json`
- `pm_bot/trading_core/artifacts/telegram_pre_live_gate_review_062t/latest_telegram_pre_live_gate_review_status_062t.json`
- `pm_bot/trading_core/artifacts/telegram_pre_live_gate_review_062t/telegram_pre_live_gate_review_registry_snapshot_062t.json`
- `pm_bot/trading_core/artifacts/telegram_pre_live_gate_review_062t/telegram_pre_live_gate_review_controls_062t.json`

## Validation

Focused validation:

```powershell
python -m pytest pm_bot/tests/test_telegram_pre_live_gate_review_062t.py
python -m pytest pm_bot/tests/test_pre_live_tiny_order_gate_062p.py
python -m pytest pm_bot/tests/test_telegram_tiny_order_review_061t.py
python -m pytest pm_bot/tests/test_tiny_order_scaffold_061.py
python -m pytest pm_bot/tests/test_telegram_operator_console_060t.py
```

Full validation is recorded in `docs/ORCH_PMBOT_TELEGRAM_062T_PRE_LIVE_TINY_ORDER_GATE_REVIEW_PANEL_RESULT.json`.
