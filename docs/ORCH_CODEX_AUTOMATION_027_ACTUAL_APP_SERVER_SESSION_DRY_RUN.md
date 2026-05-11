# ORCH-CODEX-AUTOMATION-027: actual app-server session dry-run

## Что изменилось после 026

Milestone 026 построил Symphony-style границу: task/workspace/session plan, индекс сгенерированных Codex app-server схем и render-only adapter plan. Сервер тогда не запускался.

Milestone 027 добавляет отдельный, явно операторский dry-run слой:

- `ai_orchestrator/symphony_adapter/app_server_session_dry_run.py` управляет коротким процессом `codex app-server`, protocol probe, shutdown и артефактами.
- `codex_app_server_protocol.py` умеет находить `initialize`, строить минимальный безопасный request и делать легкую структурную проверку без новых зависимостей.
- `operator_cli.py` получил команды `app-server-schema-probe`, `create-app-server-session-plan`, `app-server-dry-run`.
- Operator Panel получил страницу `App Server` с explicit confirmation text для запуска.
- Unit tests используют fake app-server; реальный app-server не нужен для обычного test suite.

## Что такое app-server dry-run

Dry-run здесь означает один короткий локальный запуск app-server с timeout:

1. построить safe config;
2. проверить safety flags;
3. запустить `codex app-server --listen stdio://`;
4. отправить только минимальный `initialize`, если схема позволяет;
5. собрать stdout/stderr/result;
6. закрыть stdin/остановить процесс;
7. записать артефакты.

Это не daemon, не scheduler, не background worker и не механизм автономного выполнения задач.

## Safety boundaries

Dry-run validation блокирует:

- `allow_network=true`;
- `allow_auth=true`;
- `allow_browser=true`;
- `allow_real_task_execution=true`;
- `timeout_seconds > 120`;
- websocket host вне loopback;
- отсутствующий schema dir;
- отсутствующий executable при approved запуске.

Не добавлены OpenRouter, Polymarket API, wallet/private key/signing, реальные orders или trading endpoints.

## Schema probe

Команда только читает локальные schema files и не запускает app-server:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli app-server-schema-probe --schema-dir C:/Users/OpenC/.openclaw/external_research/codex_app_server_schema
```

Результат показывает:

- known client/server request/notification methods;
- найден ли `initialize`;
- можно ли построить minimal initialize request;
- lightweight validation result;
- auth/approval/session message classes для оператора.

## Render dry-run command

Без `--operator-approved` процесс не стартует. CLI только рендерит команду и возвращает `requires_operator_approval`:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli app-server-dry-run --repo-root C:/Users/OpenC/.openclaw/workspace --queue-root agent_tasks --schema-dir C:/Users/OpenC/.openclaw/external_research/codex_app_server_schema --listen-mode stdio --timeout-seconds 30
```

Ожидаемая команда:

```text
codex app-server --listen stdio://
```

## Run short-lived dry-run

Запуск требует явного флага:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli app-server-dry-run --repo-root C:/Users/OpenC/.openclaw/workspace --queue-root agent_tasks --schema-dir C:/Users/OpenC/.openclaw/external_research/codex_app_server_schema --listen-mode stdio --timeout-seconds 30 --operator-approved
```

Operator Panel требует точный текст:

```text
I approve short-lived Codex app-server dry-run
```

## Artifacts

CLI пишет:

```text
agent_tasks/generated/<plan_id>/<run_id>/app_server_dry_runs/<timestamp>/
  dry_run_config.json
  app_server_command.txt
  protocol_probe.json
  stdout.log
  stderr.log
  result.json
  README.md
```

Для ручного CLI dry-run используется `manual_app_server_dry_run` как plan id.

Integration artifact 027:

```text
agent_tasks/generated/fake_integration/app_server_session_dry_run_027/
```

Он содержит fake app-server pass и real app-server short-lived readiness/probe record.

## Как читать статусы

- `process_started`: локальный процесс был создан через `subprocess.Popen`.
- `protocol_probe_attempted`: dry-run отправил minimal initialize request.
- `protocol_probe_succeeded`: получен response с тем же request id и `result`.
- `schema_only`: full protocol probe не выполнялся, результат только по schema inspection.
- `process_stopped`: dry-run handle завершил процесс; это не утверждение о desktop-managed процессах Codex.
- `blocked`: запуск не выполнялся из-за safety/config/operator approval gate.

Не нужно трактовать `protocol_probe_succeeded=true` как разрешение на автономные sessions. Это только initialize-level diagnostics.

## Почему full autonomous session еще выключен

027 не стартует `thread/start`, `turn/start`, shell commands, fs writes, authenticated methods, browser automation или торговые интеграции. Реальное task execution остается disabled через `allow_real_task_execution=false` и отдельный future approval gate.

## Validation

Выполнено:

```powershell
python -m compileall ai_orchestrator
pytest tests/test_symphony_task_contract.py tests/test_symphony_workspace_plan.py tests/test_symphony_session_plan.py tests/test_symphony_mapping.py tests/test_symphony_result_bridge.py tests/test_codex_app_server_protocol_index.py tests/test_app_server_adapter_boundary.py tests/test_operator_cli_symphony_task_plan.py tests/test_app_server_session_dry_run_config.py tests/test_app_server_schema_probe.py tests/test_app_server_dry_run_fake_process.py tests/test_operator_cli_app_server_dry_run.py tests/test_operator_panel_app_server.py
pytest tests/test_operator_cli_codex_adapter.py tests/test_codex_execution_packet.py tests/test_codex_queue_operator_cli.py tests/test_operator_panel_codex_adapter.py
```

Real dry-run result:

- command: `codex app-server --listen stdio://`;
- process started: true;
- initialize probe succeeded: true;
- process stopped: true;
- no browser/OpenRouter/Polymarket/wallet/trading endpoints.

## Next milestone

`ORCH-CODEX-AUTOMATION-028-AGENTS-MD-SUBAGENTS-MEMORY-BANK-AND-MAINTENANCE`
