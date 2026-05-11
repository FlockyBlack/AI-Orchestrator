# ORCH-CODEX-AUTOMATION-028: AGENTS.md, Subagents, Memory Bank, Maintenance

## Что изменилось после 027

После успешного short-lived app-server dry-run в 027 добавлен durable governance layer для длинных supervised Codex/PMBOT runs:

- корневой `AGENTS.md` как проектный контракт
- профили ролей в `agent_tasks/agents/`
- контекстный `memory-bank/`
- phase memory в `.codex-agent/`
- Goal Maker-style board и receipt template
- maintenance automation prompt
- contract schemas
- idempotency foundation
- subagent metadata в Codex execution packets
- легкая интеграция статусов в operator panel/dashboard

## Как используется AGENTS.md

`AGENTS.md` фиксирует миссию проекта, PMBOT paper-only режим, safety boundaries, git discipline, Codex automation rules, роли и required output.
Execution prompt теперь явно говорит Codex читать `AGENTS.md` до изменений и агрегировать работу в один result JSON.

## Как используются subagent roles

Профили ролей не создают самостоятельный scheduler или background worker. Это bounded working modes:

- Scout - read-only discovery
- Planner - decomposition and blocker detection
- Builder - bounded implementation
- Tester - targeted tests and validation
- Reviewer - diff/safety/git review
- Docs - operator docs/result JSON
- Integrator - gate decision and selective staging plan

028 сохраняет эти роли как repo artifacts и packet metadata. Реальная маршрутизация по worktree lanes отложена на 029.

## Как работает memory-bank

`memory-bank/` хранит компактный контекст, который future Codex runs могут читать без повторного восстановления всей истории:

- `projectbrief.md`
- `productContext.md`
- `techContext.md`
- `activeContext.md`
- `progress.md`
- `pmbotSafety.md`
- `pmbotMarkets.md`
- `codexAutomation.md`

Tracked PMBOT markets остаются unresolved, `feedback_ready_count = 0`, outcomes не изобретались.

## Как работает .codex-agent phase memory

`.codex-agent/phase-card.md` описывает фазы DISCOVERY, PLANNING, APPROVAL, EXECUTION, VERIFICATION, HANDOFF.
`.codex-agent/ultra-context.md` хранит самый плотный high-value context.
`.codex-agent/context-bundle.md` указывает планы, artifacts, result docs и команды.
`.codex-agent/approval-snapshot.json` фиксирует approved scope 028, allowed paths, required tests и baseline safety.

## Как работают receipts

`docs/goals/pmbot-paper-mvp/` содержит goal board для milestone range 022-050.
Receipt template требует `task_id`, `status`, `head_before`, `head_after`, `files_changed`, `tests_run`, `artifacts`, `safety`, `blockers`, `next_recommended_task`.

Цель receipts - сделать каждый milestone проверяемым и пригодным для восстановления после context loss.

## Как работает maintenance automation

`agent_tasks/automations/codex_maintenance_prompt.md` - report-only prompt.
Он проверяет stale runs, old worktrees, large logs/artifacts, old Codex sessions, freshness `memory-bank/` и `.codex-agent/`.
Он не удаляет, не изменяет файлы и не создает daemon/scheduler/background worker.

## Как это улучшает PMBOT automation

028 снижает риск:

- потери контекста между long supervised runs
- смешивания discovery/build/test/review responsibilities
- небезопасных PMBOT решений
- broad git staging
- fake success claims
- неаудируемых retry/restart действий

Execution packets теперь несут `subagent_plan`, `role_assignments`, expected outputs, aggregation policy, memory context paths и `agents_md_path`.

## Current Limitations

- Subagent routing пока metadata/template based.
- Idempotency foundation не подключена к базе или runtime lock manager.
- Contract schemas валидируются как JSON artifacts; full schema enforcement может быть добавлен позже.
- Result JSON внутри коммита не может содержать собственный final commit hash без отдельной follow-up мутации; final response содержит verified `head_after`.
- Real trading, wallet/signing, orders, authenticated endpoints, browser automation, OpenRouter и Polymarket API остаются запрещены.

## Next Milestone

`ORCH-CODEX-AUTOMATION-029-WORKTREE-LANE-REAL-EXECUTION-AND-SUBAGENT-ROUTING`
