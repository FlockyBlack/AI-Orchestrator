# Autopilot V1 Dry Run Flow

## Purpose
`codex_auto/autopilot/run_dry_run_flow.py` builds a deterministic, dry-run-only report for the Autopilot V1 handoff path:

AI-Orchestrator task/run references -> preview handoff builder -> preview handoff validator -> dry-run flow report -> advisory next action.

## Dry-run-only semantics
This reporter is intentionally non-executing.

It does:
- read authoritative task and run references
- build an inline preview handoff using the existing builder
- validate that preview handoff using the existing validator
- emit a deterministic JSON dry-run report
- recommend the next gated action

It does not:
- perform runtime wiring
- mutate any queue
- approve execution
- claim final acceptance
- transfer source-of-truth ownership
- write by default

## Source-of-truth boundaries
AI-Orchestrator remains the owner of runtime status and final acceptance status.

`codex_auto` owns the preview handoff artifact.

`codex_auto/autopilot validator` owns preview validation status.

`codex_auto/autopilot dry-run reporter` owns dry-run status.

Flocky remains the next required read-only validation gate.

Codex execution status is only a result envelope owner after approved execution. This dry-run flow never authorizes that execution.

## Sequence
1. Resolve authoritative task and run references.
2. Call `build_preview_handoff.py` functionality.
3. Call `validate_preview_handoff.py` functionality.
4. Assemble the dry-run-only flow report.
5. Recommend one of: `ready_for_flocky_review`, `repair_needed`, `blocked`, `approval_required`.

## CLI usage
Stdout-first, no-write default:

```bash
python codex_auto/autopilot/run_dry_run_flow.py \
  --task-path codex_auto/autopilot/fixtures/valid_runtime_task.json \
  --run-path codex_auto/autopilot/fixtures/valid_runtime_result.json \
  --source-task-id ORCH-AUTOPILOT-SAMPLE \
  --out -
```

Optional write to an allowlisted dry-run output area:

```bash
python codex_auto/autopilot/run_dry_run_flow.py \
  --task-path codex_auto/autopilot/fixtures/valid_runtime_task.json \
  --run-path codex_auto/autopilot/fixtures/valid_runtime_result.json \
  --source-task-id ORCH-AUTOPILOT-SAMPLE \
  --out codex_auto/autopilot/tests/output/dry_run_report.json
```

## Test commands
```bash
python -m pytest -q codex_auto/autopilot/tests
python codex_auto/autopilot/run_dry_run_flow.py --task-path codex_auto/autopilot/fixtures/valid_runtime_task.json --run-path codex_auto/autopilot/fixtures/valid_runtime_result.json --source-task-id ORCH-AUTOPILOT-SAMPLE --out -
python -m pytest -q codex_auto
```

## Manual work that remains
After the dry-run report is generated, the remaining work is still manual and gated:
- Flocky read-only validation
- human approval before any future execution step
- any future runtime wiring outside this isolated dry-run scope
- any future final acceptance decision by AI-Orchestrator

## Next gated step
The next required step after a valid dry-run report is:

`ORCH-AUTOPILOT-006-DRY-RUN-REPORTER-V Flocky read-only validation`
