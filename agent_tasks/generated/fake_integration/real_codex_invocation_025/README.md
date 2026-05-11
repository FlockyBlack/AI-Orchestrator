# ORCH-CODEX-AUTOMATION-025 Fake Integration

This artifact demonstrates the no-manual-copy/paste path for the real `codex_cli` executor using `tests/fake_codex_command.py` instead of real Codex.

Commands run:

```powershell
python -m ai_orchestrator.codex_queue.operator_cli run-plan --plan-file agent_tasks/generated/fake_integration/real_codex_invocation_025/plan.json --queue-root agent_tasks/generated/fake_integration/real_codex_invocation_025/agent_tasks --run-id RUN025 --max-steps 0
python -m ai_orchestrator.codex_queue.operator_cli continue-plan --run-id RUN025 --queue-root agent_tasks/generated/fake_integration/real_codex_invocation_025/agent_tasks --executor codex_cli --max-steps 1 --auto-ingest --allow-real-codex-invocation --continue-until blocked_or_done
```

Observed result:

- Fake command wrote `codex_result.json`.
- `codex_result_ingestion.status` was `accepted`.
- Run status became `done`.
- State and dashboard files were updated under `agent_tasks/generated/fake_integration/real_codex_invocation_025/agent_tasks/generated/fake_real_codex_invocation_025/RUN025/`.
- No manual prompt copy/paste or manual result ingestion was used.
