# ORCH-CODEX-AUTOMATION-022: операторская панель и plan-runner

## Что создано

Этот этап добавляет первый исполняемый локальный контур управления Codex-задачами:

- контракт master plan с валидацией безопасности;
- декомпозицию задач и материализацию очереди в `agent_tasks/generated/`;
- состояние run-а, lock-файл, recovery report и dashboard;
- fake/noop/handoff executors;
- генерацию durable Codex handoff prompt без вызова Codex;
- локальную web-панель на `127.0.0.1`;
- CLI-команды для `run-plan`, `continue-plan`, `recover-plan`, `export-next-codex-prompt`;
- selective staging planner и dry-run commit/push boundary.

Это не daemon, не scheduler и не автономный worker. Все действия запускаются оператором явно.

## Запуск панели

```powershell
python -m ai_orchestrator.operator_panel.panel_app --repo-root C:/Users/OpenC/.openclaw/workspace --queue-root agent_tasks --host 127.0.0.1 --port 8765
```

После запуска открыть локально:

```text
http://127.0.0.1:8765
```

Панель показывает repo root, queue root, текущую ветку/head, найденные планы, run-ы, counts, blocked/failed tasks, artifact paths и последний handoff prompt.

## Работа с планом

Готовый master plan лежит здесь:

```text
agent_tasks/plans/pmbot_master_plan_to_050.v1.json
```

Проверка плана:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli inspect-plan --plan-file agent_tasks/plans/pmbot_master_plan_to_050.v1.json --queue-root agent_tasks
```

Материализация очереди:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli plan-to-queue --plan-file agent_tasks/plans/pmbot_master_plan_to_050.v1.json --queue-root agent_tasks
```

Панель также умеет сохранять pasted JSON в `agent_tasks/plans/`, валидировать его и создавать очередь.

## Fake run

Безопасный локальный прогон:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli run-plan --plan-file agent_tasks/plans/pmbot_master_plan_to_050.v1.json --queue-root agent_tasks --mode long_supervised --max-steps 50 --executor fake --continue-until blocked_or_done
```

Продолжение существующего run-а:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli continue-plan --run-id <RUN_ID> --queue-root agent_tasks --max-steps 50 --continue-until blocked_or_done
```

Recovery:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli recover-plan --run-id <RUN_ID> --queue-root agent_tasks
```

Экспорт следующего Codex prompt:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli export-next-codex-prompt --run-id <RUN_ID> --queue-root agent_tasks
```

`handoff` executor пишет prompt в:

```text
agent_tasks/generated/<plan_id>/<run_id>/handoff/<task_id>_codex_prompt.md
```

Он не вызывает Codex напрямую.

## Как это уменьшает ручной roundtrip

Раньше цикл был таким: ChatGPT пишет большой prompt, оператор вставляет его в Codex, Codex делает одну задачу, оператор копирует JSON обратно.

Теперь локальный runner хранит master plan, очередь, state, dashboard, artifacts и следующий handoff prompt. Оператор видит состояние в панели, может продолжать run, восстанавливаться после блокера и экспортировать следующий Codex prompt без ручной сборки контекста с нуля.

## Что пока не автоматизировано

- Реальный Codex CLI/App executor пока не включен; есть только boundary stubs и handoff prompt.
- Нет scheduler-а, daemon-а или фонового worker-а.
- Нет browser automation.
- Нет OpenRouter/Polymarket API.
- Нет wallet/signing/orders/trading endpoints.
- Selective commit/push helper есть, но operator gate остается обязательным.

## Следующие milestones

- `ORCH-CODEX-AUTOMATION-023-QUEUE-STATE-RESUME-AND-PANEL-HARDENING`
- `ORCH-CODEX-AUTOMATION-024-CODEX-EXECUTOR-ADAPTER-BOUNDARY`
- `ORCH-CODEX-AUTOMATION-025-WORKTREE-LANE-MANAGER`
