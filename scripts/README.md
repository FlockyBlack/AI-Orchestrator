Scripts for the local execution path.

Available now:
- `run_codex.py` prepares dry-run prompt and run artifacts without launching `codex exec`.
- `validate_result.py` validates result JSON with stdlib-only checks against `schemas/codex-result.schema.json`.

Planned next:
- `dispatcher.py`
- `validate_result.py`

Dry-run usage:
- `python scripts/run_codex.py --task tasks/ready/AI-ORCH-SMOKE-001.task.json --dry-run`

Validation usage:
- `python scripts/validate_result.py --result runs/AI-ORCH-SMOKE-001/20260425T022119Z/result.placeholder.json`
