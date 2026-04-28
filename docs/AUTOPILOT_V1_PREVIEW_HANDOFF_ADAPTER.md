# AUTOPILOT V1 Preview Handoff Adapter

## Purpose

This adapter builds a deterministic preview-only handoff envelope from an AI-Orchestrator task reference and run reference. It exists to describe a future Codex handoff boundary without performing execution, queue updates, runtime wiring, or acceptance transitions.

## Why This Is Preview-Only

The generated envelope hard-codes the Autopilot V1 safety contract:

- `preview_only=true`
- `runtime_authority=false`
- `final_acceptance_authority=false`
- `approval_required=true`
- `flocky_validation_required=true`
- `execution_allowed_now=false`
- `runtime_wiring_allowed=false`
- `single_runtime_source_rule_preserved=true`

Validation fails if any envelope claims runtime authority, final acceptance authority, execution permission now, runtime wiring permission, or source-of-truth transfer.

## Why This Is Not Runtime Wiring

The adapter reads input JSON and returns a preview envelope. It does not mutate:

- `tasks/`
- `runs/`
- `state/`
- `runtime/`
- `results/`
- `freeze/`
- `checkpoint/`
- `scripts/dispatcher.py`
- `scripts/run_codex.py`

CLI output defaults to stdout. File output is restricted to preview test/output locations under `codex_auto/autopilot/`.

## Source-Of-Truth Boundaries

- AI-Orchestrator remains the only authoritative runtime source.
- `codex_auto` owns only the preview handoff envelope.
- Codex is represented only as a future result-envelope executor.
- Flocky remains validation-only.
- Final acceptance remains AI-Orchestrator-side after separate validation.

## Tests

Run the focused adapter tests:

```powershell
python -m pytest -q codex_auto/autopilot/tests
```

Run the broader `codex_auto` test suite when feasible:

```powershell
python -m pytest -q codex_auto
```

## Next Gated Step Preparation

This adapter prepares the next gated step by producing a deterministic handoff envelope that can be inspected by Flocky without implying runtime ownership changes or execution authorization.

## What Is Still Manual

- Reviewing the preview envelope
- Running Flocky read-only validation
- Any future approval decision
- Any runtime wiring or execution work, which remains out of scope for this adapter
