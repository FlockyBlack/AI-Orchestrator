# ORCH-SYMPHONY-001 Local Queue Adapter Result

Task: `ORCH-SYMPHONY-001-ADAPT-SPEC-LOCAL-QUEUE`

Status: `completed`

## Why Symphony Was Adapted

Official OpenAI Symphony was treated as the reference architecture, not installed as a runtime. The prior spike found that the official implementation is useful but not a drop-in PMBOT orchestration layer because it is Linear-first, has no shipped GitHub Issues adapter, has no durable file-based queue adapter, requires Elixir/OTP for the reference implementation, and invokes Codex through Codex app-server.

This task therefore implements a local-only, dry-run-only queue adapter shaped around the useful Symphony concepts:

- task packet
- local queue
- validation
- safety gate
- workspace and handoff planning
- proof-of-work report
- human review

## Local Queue Created

The queue root is `agent_tasks/`.

It contains:

- `inbox/` for proposed tasks.
- `approved/` for manually approved task packets.
- `planned/` for generated non-executing plans and handoff prompts.
- `running/` reserved for future controlled execution, not used by this MVP.
- `review/` for completed task outputs awaiting human review.
- `done/` for manually accepted completed work.
- `blocked/` for rejected task packets.
- `templates/` for example task packets.
- `reports/` for dry-run reports.

The Python package is under `ai_orchestrator/codex_queue/` and contains schema constants, validation, deterministic safety classification, planning, report writing, and the CLI dry-run runner.

## Dry-Run Runner

The runner command is:

```powershell
python -m ai_orchestrator.codex_queue.dry_run_runner --queue-root agent_tasks --dry-run
```

It ensures queue directories exist, loads `*.json` packets from `agent_tasks/approved/`, validates packets, classifies safety, writes non-executing plans for allowed packets, writes handoff prompts for allowed packets, and writes latest JSON/Markdown reports.

It does not move packets, create branches, create worktrees, run tests, execute acceptance checks, invoke Codex, call Codex app-server, call network services, or start daemons/workers/schedulers.

## Handoff Prompt Generation

For each allowed approved task, the runner writes:

- `agent_tasks/planned/<TASK_ID>.plan.json`
- `agent_tasks/planned/<TASK_ID>.handoff_prompt.md`

The handoff prompt reduces manual Ctrl-C/Ctrl-V by rendering the task packet into a Codex-ready Markdown prompt with task id, title, summary, instructions, allowed paths, forbidden paths, safety boundaries, acceptance checks, required result JSON shape, and explicit safety statements.

The prompt still requires a human operator to inspect and manually execute Codex separately.

## Still Manual

- Creating task packets.
- Inspecting proposed packets.
- Moving packets from `inbox/` to `approved/`.
- Reviewing dry-run reports.
- Reviewing handoff prompts.
- Running Codex separately if approved.
- Moving outputs into `review/`.
- Accepting work into `done/`.

## Intentionally Not Automated

This MVP intentionally does not add:

- official Symphony runtime integration
- Linear integration
- GitHub Issues integration
- Codex app-server usage
- autonomous Codex execution
- background workers
- schedulers
- Windows Task Scheduler integration
- Telegram integration
- OpenClaw integration
- OpenRouter calls
- Polymarket API calls
- credential access
- wallet, trading, order, or payment behavior
- dispatcher, run_codex, or runtime execution changes

## Validation

Successful validation commands:

```powershell
python -m compileall ai_orchestrator tests
pytest tests/test_codex_queue_schema.py tests/test_codex_queue_validator.py tests/test_codex_queue_safety.py tests/test_codex_queue_planner.py tests/test_codex_queue_dry_run_runner.py
python -m ai_orchestrator.codex_queue.dry_run_runner --queue-root agent_tasks --dry-run
```

The focused pytest suite passed 25 tests. The live queue dry-run wrote latest reports under `agent_tasks/reports/`. The live queue had no approved packets, so no live handoff prompt was generated in `agent_tasks/planned/`; the handoff generation path is covered by the dry-run runner test using a temporary approved packet.

## Next Task

Recommended next task: `ORCH-SYMPHONY-002-FIRST-LOCAL-HANDOFF-DRY-RUN`.

