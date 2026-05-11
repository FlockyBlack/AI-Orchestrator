# ORCH-CODEX-AUTOMATION-026: Codex app-server и Symphony-style workspaces

## Статус

В этой вехе добавлен локальный адаптерный слой, который переводит задачи AI-Orchestrator в Symphony-style task/workspace/session/result контракты и строит render-only boundary для Codex `app-server`.

Реальный `codex app-server` не запускался. Worktree не создавался. Daemon, scheduler и background worker не добавлялись.

## Почему Elixir Symphony сейчас не запускается

Локальная Symphony reference implementation находится в `C:/Users/OpenC/.openclaw/external_research/openai_symphony`, но для нее нужны Elixir, `mix` и `mise`; в текущей среде они отсутствуют.

Стратегически это не blocker: Symphony используется как архитектурный reference, а не как runtime dependency. Для AI-Orchestrator безопаснее сейчас взять модели orchestration из `SPEC.md` и провести execution boundary напрямую через локальные Codex app-server schemas.

## Что Symphony дает архитектурно

Из локальных `README.md`, `SPEC.md` и `elixir/` извлечены основные модели:

- task/issue model: нормализованная работа с id, title, description, dependencies/blockers, attempts и retry state.
- workspace model: deterministic per-issue/per-task workspace path, workspace root boundary, cwd должен быть workspace path.
- Codex session model: `initialize`, `thread/start`, `turn/start`, session metadata, turn events, token/status notifications.
- result/review/proof model: proof of work через CI/validation/review/artifacts; успешный run может завершиться handoff/review state, а не auto-done.
- retry/recovery model: retry entries с attempt, due time, error; exponential backoff; restart recovery не восстанавливает live sessions.

Для этой вехи эти идеи сведены к локальным JSON artifact plans, а не к long-running service.

## Как это сопоставлено с AI-Orchestrator

Добавлен пакет `ai_orchestrator/symphony_adapter/`:

- `symphony_task_contract.py` описывает `SymphonyTask`, source/status, acceptance policy и proof requirements.
- `symphony_workspace_plan.py` строит worktree-style план без destructive git commands, без force operations и без auto-merge.
- `symphony_session_plan.py` строит Codex app-server session plan: cwd, approval policy, sandbox policy, allowed/forbidden tools и result contract.
- `symphony_mapping.py` переводит `PlanTaskSpec`/queue task в `SymphonyTask` и render-only Codex packet preview.
- `symphony_result_bridge.py` валидирует result envelope и отвергает unsafe claims: real trading/orders, wallet/signing/private keys, trading endpoints, real money, OpenRouter, Polymarket API, authenticated endpoints, browser automation, unsafe git staging, force push, daemon/scheduler/background worker и invented outcomes.
- `codex_app_server_protocol.py` индексирует локальные generated schemas.
- `app_server_adapter_boundary.py` строит render-only `codex app-server --listen ...` plan.

## Codex app-server schemas

Локальная schema reference директория:

`C:/Users/OpenC/.openclaw/external_research/codex_app_server_schema`

Она уже была сгенерирована через `codex app-server generate-json-schema` и `generate-ts`. В этой вехе схемы только читаются.

Индексируются:

- client requests: `initialize`, `thread/start`, `turn/start`, `thread/read`, `review/start`, `command/exec`, `config/read`, etc.
- server requests: `item/commandExecution/requestApproval`, `item/fileChange/requestApproval`, `item/permissions/requestApproval`, legacy `applyPatchApproval`, `execCommandApproval`.
- server notifications: `thread/started`, `thread/status/changed`, `turn/started`, `turn/completed`, `turn/diff/updated`, `turn/plan/updated`, file/command output notifications, warnings.
- auth/status related shapes: `account/*`, login/auth token refresh and rate limit notifications.
- git/review related shapes: `review/start`, `GitDiffToRemote*`, `TurnDiffUpdatedNotification`, `ReviewDecision`.

## Отличие от 025 Codex CLI executor

Веха 025 подготовила реальный Codex CLI invocation path с operator approval и auto-ingestion.

Веха 026 не заменяет этот executor. Она добавляет следующий boundary:

- 025: one-shot CLI executor packet and result ingestion.
- 026: Symphony-style orchestration plan around task/workspace/session/result, plus app-server protocol schema index.

Иными словами, 026 готовит структуру для будущей app-server session, но не создает автономный loop и не запускает server.

## Новая CLI-команда

```powershell
python -m ai_orchestrator.codex_queue.operator_cli create-symphony-task-plan --run-id <RUN_ID> --queue-root agent_tasks --workspace-root agent_tasks/workspaces
```

Команда:

- находит следующий runnable task в generated run;
- строит `symphony_task.json`;
- строит `workspace_plan.json`;
- строит `session_plan.json`;
- строит `app_server_adapter_plan.json`;
- пишет README под `agent_tasks/generated/<plan_id>/<run_id>/symphony_tasks/<task_id>/`;
- не запускает Codex app-server;
- не создает worktree.

## Fake integration

Создан bundle:

`agent_tasks/generated/fake_integration/symphony_style_app_server_026/`

Он демонстрирует:

- загрузку `agent_tasks/plans/pmbot_master_plan_to_050.v1.json`;
- тестовый generated run `SYMPHONY_STYLE_APP_SERVER_026`;
- выбор next runnable task;
- mapping в `SymphonyTask`;
- workspace/session/app-server adapter планирование;
- schema index через локальную generated schema directory;
- JSON artifacts и `integration_result.json`.

Полное выполнение 050 не заявляется.

## Что осталось до реального app-server execution

Следующая веха должна добавить short-lived dry-run session:

- выбрать безопасный local stdio app-server mode;
- запустить server только в bounded test scope;
- выполнить `initialize` + `thread/start` + controlled `turn/start`;
- обработать approval requests как reject/operator-required по умолчанию;
- записать transcript/result envelope;
- не переходить к daemon/scheduler/autonomous execution.

Рекомендуемая следующая задача:

`ORCH-CODEX-AUTOMATION-027-ACTUAL-APP-SERVER-SESSION-DRY-RUN`
