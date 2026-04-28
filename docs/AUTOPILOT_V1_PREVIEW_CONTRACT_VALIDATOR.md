# AUTOPILOT V1 Preview Contract Validator

## Purpose

This validator independently checks preview handoff artifacts against the Autopilot V1 contract. Its job is to harden review of preview artifacts after they are produced, without trusting the builder to be the only enforcement point.

## Builder Versus Validator

The builder creates a deterministic preview envelope from task and run references. The validator consumes an existing preview artifact and produces a deterministic validation report with blocking `errors` and non-blocking `warnings`.

## Why This Is Still Preview-Only

The validator requires the preview-only contract flags to remain fixed:

- `preview_only=true`
- `runtime_authority=false`
- `final_acceptance_authority=false`
- `approval_required=true`
- `flocky_validation_required=true`
- `execution_allowed_now=false`
- `runtime_wiring_allowed=false`
- `single_runtime_source_rule_preserved=true`
- `deterministic_preview=true`

If any of these drift, validation fails.

## Why This Is Not Runtime Wiring

The validator only reads JSON and emits a validation report. It does not wire runtime flows, mutate queues, change dispatcher behavior, touch `run_codex`, or write into runtime/state/result surfaces.

## Source-Of-Truth Boundaries

- AI-Orchestrator remains the only authoritative runtime source.
- `codex_auto` owns only preview handoff artifacts.
- Codex is only the future execution result envelope owner.
- Flocky remains validation-only.
- Final acceptance remains AI-Orchestrator-owned.

The validator rejects authority drift claims such as `source_of_truth=codex_auto`, `final_accepted=true`, `runtime_truth_transferred=true`, or ownership drift in `status_ownership`.

## Tests

Focused tests:

```powershell
python -m pytest -q codex_auto/autopilot/tests
```

Validator CLI against the expected fixture:

```powershell
python codex_auto/autopilot/validate_preview_handoff.py --preview-path codex_auto/autopilot/fixtures/expected_preview_handoff.v1.json
```

Builder stdout into validator stdin:

```powershell
python codex_auto/autopilot/build_preview_handoff.py --task-path codex_auto/autopilot/fixtures/valid_runtime_task.json --run-path codex_auto/autopilot/fixtures/valid_runtime_result.json --source-task-id ORCH-AUTOPILOT-SAMPLE --out - | python codex_auto/autopilot/validate_preview_handoff.py --preview-path -
```

## Future Dry-Run Preparation

This validator prepares a future dry-run flow by allowing preview handoff artifacts to be reviewed independently of the builder. That gives Flocky and later gates a stable read-only contract check before any separate approval or execution step is discussed.

## What Remains Manual

- Reviewing warnings for fixture/example references
- Flocky read-only validation
- Any later approval decision
- Any future dry-run or execution design, which remains out of scope here
