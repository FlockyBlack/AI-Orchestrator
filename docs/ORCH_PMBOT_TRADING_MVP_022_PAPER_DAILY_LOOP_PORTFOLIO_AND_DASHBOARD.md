# ORCH-PMBOT-TRADING-MVP-022: ежедневный paper-only цикл

## Что добавлено

- Локальный ежедневный PMBOT paper-only loop: `python -m pm_bot.operator_runner.run_paper_daily_loop`.
- Конфиг запуска `PaperDailyLoopConfig` с жестким запретом network, OpenRouter, Polymarket API и real trading flags.
- Идемпотентный paper ledger: повторный запуск за ту же дату и тот же intent не создает дубли simulated fills.
- Guard для unresolved markets: все 6 tracked markets остаются `unresolved`, `feedback_ready_count` остается `0`.
- Paper portfolio report с подсчетом open paper positions, simulated fills и paper exposure.
- Dashboard, safety scan, audit, idempotency report и run result artifacts.

## Как работает daily loop

1. Загружает только локальные PMBOT fixtures/artifacts из practical/trading core.
2. Фильтрует tracked markets до `--max-markets`.
3. Проверяет локальные outcome records и блокирует resolved/ambiguous/void статус без evidence artifact.
4. Генерирует paper trade intents через существующий trading core generator.
5. Пропускает intents через существующий risk gate.
6. Создает simulated executions только через локальный deterministic simulator.
7. Обновляет ledger через idempotency key:
   `run_date + market_id + paper intent ID`.
8. Пересчитывает portfolio state и portfolio report.
9. Запускает post-execution audit и safety scan.
10. Пишет dashboard/report artifacts.

## Команда запуска

```powershell
python -m pm_bot.operator_runner.run_paper_daily_loop --max-markets 6 --output-dir pm_bot/operator_runner/artifacts/paper_daily_022
```

Для явной даты:

```powershell
python -m pm_bot.operator_runner.run_paper_daily_loop --run-date 2026-05-11 --max-markets 6 --output-dir pm_bot/operator_runner/artifacts/paper_daily_022
```

## Основные artifacts

- `pm_bot/operator_runner/artifacts/paper_daily_022/paper_daily_loop_result.json`
- `pm_bot/operator_runner/artifacts/paper_daily_022/paper_daily_dashboard.json`
- `pm_bot/operator_runner/artifacts/paper_daily_022/paper_daily_dashboard.md`
- `pm_bot/operator_runner/artifacts/paper_daily_022/paper_daily_portfolio_state.json`
- `pm_bot/operator_runner/artifacts/paper_daily_022/paper_daily_ledger.json`
- `pm_bot/operator_runner/artifacts/paper_daily_022/paper_daily_audit.json`
- `pm_bot/operator_runner/artifacts/paper_daily_022/paper_daily_safety_scan.json`
- `pm_bot/operator_runner/artifacts/paper_daily_022/paper_daily_idempotency_report.json`

## Safety boundaries

- No wallet/private keys/signing.
- No real orders.
- No trading endpoints.
- No real-money actions.
- No autonomous real trading.
- No authenticated endpoints.
- No browser automation.
- No OpenRouter usage.
- No Polymarket API usage.
- No invented outcomes.
- No market recommendation as real trading advice.
- No probability/EV/edge/confidence/side-selection as actionable real trading signal.

## Текущее состояние paper run

- Tracked markets: `6`
- Unresolved markets: `6`
- Feedback ready: `0`
- Paper intents: `6`
- Risk allowed: `6`
- Risk blocked: `0`
- Simulated executions: `6`
- Simulated fills: `2`
- Open paper positions: `2`
- Total paper exposure: `$50.0`

Повторный запуск за `2026-05-11` не создал дубликаты: idempotency report показывает `already_applied_count = 2` и `duplicate_fill_prevented_count = 2`.

## Ограничения

- Outcomes не обновляются автоматически.
- Feedback readiness остается `0`, пока нет explicit local resolved evidence artifact.
- Portfolio использует только paper exposure и fixture fills, без live prices и real PnL.
- Daily loop не является scheduler/daemon/background process; это один явный локальный command run.

## Следующий milestone

`ORCH-PMBOT-TRADING-MVP-023-PAPER-PORTFOLIO-ROLLFORWARD-AND-FEEDBACK-READINESS`
