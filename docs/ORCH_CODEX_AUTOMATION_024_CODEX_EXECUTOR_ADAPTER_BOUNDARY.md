# ORCH-CODEX-AUTOMATION-024: Codex Executor Adapter Boundary

## Что изменилось после 023

В 023 система уже умела создавать очередь из master plan, выполнять fake-задачи, продолжать и восстанавливать run state, экспортировать handoff prompt и показывать состояние в локальной operator panel.

В 024 добавлена безопасная граница Codex executor adapter:

- контракт `CodexExecutionPacket` для одной runnable-задачи;
- шаблон ожидаемого result JSON;
- генерация copy-friendly `prompt.md`;
- ручной ingestion результата через существующую acceptance policy;
- executor modes `codex_packet` и `codex_cli_dry_run`;
- stub для будущего operator-approved Codex CLI режима;
- panel controls для packet flow;
- fake integration artifact без реального вызова Codex.

## Что такое adapter boundary

Adapter boundary - это файловый контракт между plan-runner и будущим исполнителем Codex. Runner не запускает Codex сам. Он только пишет пакет:

```text
agent_tasks/generated/<plan_id>/<run_id>/codex_packets/<task_id>/
  packet.json
  prompt.md
  expected_result_template.json
  README.md
```

Пакет фиксирует:

- `run_id`, `plan_id`, `task_id`;
- точный `repo_root`, `branch`, `expected_head`;
- `state_path` и `queue_manifest_path`;
- allowed paths, forbidden actions, acceptance gates;
- adapter mode;
- safety boundaries и approval requirement.

## Почему реальная самоинвокация Codex не включена

024 намеренно не создает autonomous loop, daemon, scheduler или background worker. `codex_cli_dry_run` только пишет будущую команду в artifact. `codex_cli_operator_approved_stub` остается заглушкой и не вызывает внешний процесс без отдельной будущей задачи и явного approval marker.

Запрещено и проверяется:

- `git add .`, `git add -A`, `git add --all`;
- force push;
- wallet/private key/signing/orders/trading endpoints;
- OpenRouter и Polymarket API без отдельного approval;
- authenticated endpoints;
- browser automation;
- daemon/scheduler/background worker.

## Как создать packet

```powershell
python -m ai_orchestrator.codex_queue.operator_cli create-codex-packet --run-id <RUN_ID> --queue-root agent_tasks --adapter-mode manual_handoff
```

Для dry-run будущего Codex CLI:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli codex-adapter-dry-run --run-id <RUN_ID> --queue-root agent_tasks --adapter-mode codex_cli_dry_run
```

Через controller:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli continue-plan --run-id <RUN_ID> --queue-root agent_tasks --max-steps 1 --executor codex_packet --continue-until one_step
```

## Как вручную выполнить prompt

1. Откройте `prompt.md` из packet directory.
2. Скопируйте prompt в отдельный операторски одобренный Codex-сеанс.
3. Выполняйте только один `task_id`.
4. Верните только JSON по `expected_result_template.json`.
5. Не используйте unsafe git staging, force push, wallet/signing/orders/trading, OpenRouter, Polymarket API, browser automation, daemon/scheduler/background worker.

## Как ingest-ить результат

```powershell
python -m ai_orchestrator.codex_queue.operator_cli ingest-codex-result --packet-path <PACKET_JSON> --result-json <RESULT_JSON> --queue-root agent_tasks
```

Ingestion:

- проверяет packet/result envelope;
- сверяет `task_id`;
- сканирует unsafe claims;
- запускает `result_acceptance_policy`;
- только после acceptance обновляет state;
- пишет dashboard и `ingestion_report.json/.md`;
- не invent-ит success и не помечает done при validation failure.

## Panel support

Run detail page теперь показывает действия:

- Create Codex packet;
- Create Codex dry-run packet;
- Export expected result template;
- Ingest result JSON;
- Continue with fake;
- Continue with codex_packet.

Codex Handoff page показывает latest packet, prompt, expected result template, adapter mode, approval flag и ingestion status.

Artifacts page группирует `codex_packets`, включая `packet.json`, `prompt.md`, `expected_result_template.json` и ingestion reports.

## Как будущие Codex CLI/App automation подключатся

Следующий слой должен читать `packet.json`, выполнять ровно один task в worktree/workspace-write sandbox, возвращать result envelope и вызывать ingestion. Любое фактическое self-invocation должно быть добавлено отдельной задачей с явным operator approval, bounded execution и отдельными safety gates.

## Текущие ограничения

- Real Codex CLI не вызывается.
- Codex App automation profile только описан шаблоном.
- Нет daemon/scheduler/background worker.
- Нет network/auth/browser/wallet/order/trading endpoints.
- Result artifacts проверяются как заявленные пути, но не доказывают содержимое без task-specific validation.
- Старые failed fake integration попытки могут оставаться untracked локально; итоговый проход зафиксирован в `R24D`.

## Fake integration

Итоговый artifact:

```text
agent_tasks/generated/fake_integration/codex_adapter_024/final_integration_result.json
```

Он демонстрирует:

- загрузку `pmbot_master_plan_to_050.v1.json`;
- fake execution одного шага;
- создание Codex packet для следующей задачи;
- запись `packet.json`, `prompt.md`, `expected_result_template.json`;
- simulated accepted result JSON;
- ingestion через реальную policy;
- обновление state/dashboard;
- ingestion report;
- отсутствие claim о full 050 completion.

## Next task

Рекомендуемый следующий шаг: `ORCH-CODEX-AUTOMATION-025-WORKTREE-LANE-EXECUTION`.
