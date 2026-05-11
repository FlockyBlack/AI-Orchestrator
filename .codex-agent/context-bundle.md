# Context Bundle

## Plans

- Main plan: `agent_tasks/plans/pmbot_master_plan_to_050.v1.json`
- Queue root: `agent_tasks/`
- Generated run artifacts: `agent_tasks/generated/`

## Artifacts

- Codex packets: `agent_tasks/generated/*/*/codex_packets/*/`
- Dashboards: `agent_tasks/generated/*/*/dashboard/`
- Reports: `agent_tasks/reports/`
- Fake integrations: `agent_tasks/generated/fake_integration/`

## Result Docs

- Latest previous result: `docs/ORCH_CODEX_AUTOMATION_027_RESULT.json`
- Current result: `docs/ORCH_CODEX_AUTOMATION_028_RESULT.json`
- Current operator doc: `docs/ORCH_CODEX_AUTOMATION_028_AGENTS_MD_SUBAGENTS_MEMORY_BANK_AND_MAINTENANCE.md`

## Important Commands

- `git branch --show-current`
- `git rev-parse HEAD`
- `git status --short`
- `python -m compileall ai_orchestrator`
- `pytest tests/test_agents_md_contract.py tests/test_subagent_role_profiles.py tests/test_memory_bank.py tests/test_codex_agent_phase_memory.py tests/test_goal_receipts.py tests/test_contract_schemas.py tests/test_idempotency_keys.py tests/test_codex_packet_subagent_plan.py tests/test_maintenance_prompt.py`

## Expected Result JSON Pattern

Required top-level fields:

- `task_id`
- `status`
- `repo`
- `implemented`
- `safety`
- `validation`
- `operator_artifacts`
- `next_recommended_task`

Never report full roadmap completion from a single milestone result.
