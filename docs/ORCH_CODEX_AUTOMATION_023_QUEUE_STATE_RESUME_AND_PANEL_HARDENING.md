# ORCH-CODEX-AUTOMATION-023 - Queue state resume and panel hardening

## Что изменилось после 022

023 усиливает существующую реализацию 022, не заменяя ее:

- `PlanRunState` получил lifecycle statuses: `initialized`, `queued`, `running`, `paused`, `completed`, `blocked`, `failed`, `recovering`, `recovered`, `inconsistent`.
- State JSON теперь содержит `state_schema_version`, `created_by`, `last_updated_by`.
- `save_state` пишет атомарно через temp file, fsync где возможно и replace.
- Добавлены checkpoints: `create_checkpoint`, `list_checkpoints`, `get_last_checkpoint`, `restore_checkpoint`.
- Добавлена consistency validation: duplicate terminal statuses, unknown task IDs, invalid retry counts, missing/unknown current task, incomplete dependencies, completed run with pending tasks.
- Queue manifest расширен sha256 исходного плана, путями state/dashboard/handoff/recovery/lock и валидацией task files.
- Queue creation стала idempotent: тот же `plan_id/run_id/source_plan_sha256/task_ids` возвращает `exists`, конфликт manifest возвращает `blocked`.
- Controller перед продолжением проверяет manifest/state consistency и останавливает run до `recover-plan`, если state inconsistent.
- Fake executor поддерживает `fake_behavior`: `blocked`, `failed`, `needs_retry`, `requiring_operator_handoff`.
- Handoff executor пишет более читаемый prompt: compact state, previous completed tasks, только next task, exact expected result JSON, инструкция `Return only JSON`.
- Operator panel получил улучшенные dashboard/runs/run detail/plans/handoff/artifacts pages и действия continue/recover/export для выбранного run.
- CLI получил `inspect-run`, `list-runs`, `validate-state`, `checkpoint-run`.

## Как работает resume

`run-plan` создает queue и state, делает checkpoint `before_first_execution`, затем выполняет bounded fake/noop/handoff steps.

`continue-plan`:

1. Находит существующий `run_id` в `queue_root/generated/*/<run_id>/manifest.json`.
2. Валидирует manifest и task files.
3. Загружает state.
4. Валидирует consistency относительно исходного plan.
5. Продолжает только next runnable task.
6. Не запускает уже completed tasks повторно.
7. После каждого шага обновляет state и dashboard.

Пример:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli continue-plan --run-id <RUN_ID> --queue-root agent_tasks --max-steps 3 --executor fake --continue-until blocked_or_done
```

## Как работает recovery

`recover-plan` инспектирует manifest, state и lock:

- stale lock только сообщает как blocker без явного флага;
- с `--allow-stale-lock-clear` stale lock очищается;
- active lock не очищается;
- создается recovery checkpoint;
- пишется recovery report JSON/MD под `agent_tasks/generated/<plan_id>/<run_id>/recovery/`;
- state получает статус `recovered` или `blocked`.

Пример безопасной инспекции:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli recover-plan --run-id <RUN_ID> --queue-root agent_tasks
```

Пример явного разрешения очистки stale lock:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli recover-plan --run-id <RUN_ID> --queue-root agent_tasks --allow-stale-lock-clear
```

## Checkpoints

Checkpoint хранит snapshot:

- `checkpoint_id`
- `checkpoint_created_at`
- `checkpoint_reason`
- `task_id`
- completed/blocked/failed/skipped task IDs
- retry counts
- artifact paths
- latest handoff/recovery paths

Создать вручную:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli checkpoint-run --run-id <RUN_ID> --queue-root agent_tasks --reason manual_checkpoint
```

## Panel continue/recover

Старт panel:

```powershell
python -m ai_orchestrator.operator_panel.panel_app --repo-root C:/Users/OpenC/.openclaw/workspace --queue-root agent_tasks --host 127.0.0.1 --port 8765
```

На Dashboard видны branch/head, dirty status, active run, counts, current task, next runnable tasks, retry counts, latest checkpoint, latest artifacts, latest handoff prompt, latest recovery report и safety status.

На Run detail доступны:

- Continue 1 step
- Continue 3 steps
- Export handoff prompt
- Recover
- Refresh

POST actions возвращают visible result page и ссылку назад к run/artifacts/handoff.

## CLI команды

```powershell
python -m ai_orchestrator.codex_queue.operator_cli list-runs --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli inspect-run --run-id <RUN_ID> --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli validate-state --run-id <RUN_ID> --queue-root agent_tasks
python -m ai_orchestrator.codex_queue.operator_cli export-next-codex-prompt --run-id <RUN_ID> --queue-root agent_tasks
```

`validate-state` возвращает non-zero exit code, если state inconsistent.

## Fake integration artifact

Создан artifact:

`agent_tasks/generated/fake_integration/operator_panel_023_resume_recovery/`

Он демонстрирует:

- загрузку `pmbot_master_plan_to_050.v1.json`;
- создание run;
- 2 fake steps;
- продолжение того же run еще на 2 fake steps;
- checkpoint;
- stale-lock recovery без очистки и с явным allow flag;
- recovery reports;
- export next Codex handoff prompt;
- dashboard JSON/MD;
- финальный `fake_resume_recovery_integration_result.json`.

Это не заявляет full 050 completion.

## Текущие ограничения

- Нет daemon, scheduler или background worker.
- Нет real Codex self-invocation.
- Handoff prompt только экспортируется для ручного оператора.
- Recovery repair остается conservative: inconsistent state блокирует continue до recovery/manual repair.
- Full repo suite не запускался: collection показал 1843 теста из широких legacy/PMBOT/OpenRouter зон, не относящихся к 023. Запущен полный targeted suite из задания.

## Следующий milestone

`ORCH-CODEX-AUTOMATION-024-CODEX-EXECUTOR-ADAPTER-BOUNDARY`

Цель 024: определить границу будущего Codex executor adapter без реального self-invocation, без daemon/scheduler и без автономного исполнения.
