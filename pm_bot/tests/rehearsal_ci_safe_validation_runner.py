from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/tests/", "tests/")
EXPECTED_VALIDATION_COMMANDS = (
    "python -m compileall pm_bot tests",
    "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
)
FIXTURE_PATH = Path("pm_bot/tests/fixtures/rehearsal/pmbot_rehearsal_ci_safe_validation_runner.valid.json")
OPERATOR_REVIEW_STATUS = "pending_operator_review"
TRUE_SAFETY_BOUNDARIES = {
    "local_fixtures_only",
    "local_static_samples_only",
    "operator_review_required",
    "paper_mode_only",
}


def run_rehearsal_ci_safe_validation(repo_root: Path | str | None = None) -> dict[str, Any]:
    root = _repo_root(repo_root)
    fixture = _load_json(_resolve_allowed_reference(root, str(FIXTURE_PATH).replace("\\", "/")))

    local_reference_errors = _local_reference_errors(root, fixture)
    review_state_errors = _review_state_errors(root, fixture)
    command_errors = _validation_command_errors(fixture)
    boundary_errors = _boundary_errors(fixture)

    checks = [
        _check_record(
            "local_reference_resolution",
            not local_reference_errors,
            "All declared runner targets resolve under allowed local paths.",
        ),
        _check_record(
            "prior_artifact_operator_review_state",
            not review_state_errors,
            "Prior rehearsal fixtures remain pending operator review.",
        ),
        _check_record(
            "validation_command_record_consistency",
            not command_errors,
            "Required validation commands match fixed local command records.",
        ),
        _check_record(
            "closed_safety_boundary_confirmation",
            not boundary_errors,
            "Closed safety boundaries match the local runner contract.",
        ),
        _check_record(
            "human_review_boundary_confirmation",
            fixture["operator_review"] == {
                "reviewed_at": None,
                "reviewed_by": None,
                "status": OPERATOR_REVIEW_STATUS,
            },
            "Human operator review remains pending.",
        ),
    ]

    errors = [*local_reference_errors, *review_state_errors, *command_errors, *boundary_errors]
    errors.extend(f"failed_check:{check['check_id']}" for check in checks if check["status"] != "passed")

    return {
        "checks": checks,
        "contract_id": fixture["contract_id"],
        "contract_version": fixture["contract_version"],
        "errors": errors,
        "operator_review": fixture["operator_review"],
        "run_mode": fixture["run_mode"],
        "runner_id": fixture["runner_id"],
        "summary_counts": {
            "checks": len(checks),
            "checks_passed": sum(1 for check in checks if check["status"] == "passed"),
            "errors": len(errors),
            "runner_targets": len(fixture["runner_targets"]),
            "validation_command_records": len(fixture["validation_command_records"]),
            "warnings": len(fixture["warnings"]),
        },
        "task_id": fixture["task_id"],
        "warnings": list(fixture["warnings"]),
    }


def main() -> int:
    print(json.dumps(run_rehearsal_ci_safe_validation(), indent=2, sort_keys=True))
    return 0


def _repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is None:
        return Path(__file__).resolve().parents[2]
    return Path(repo_root)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_allowed_reference(repo_root: Path, local_reference: str) -> Path:
    normalized = local_reference.replace("\\", "/")
    if "://" in normalized:
        raise ValueError(f"not_local:{local_reference}")
    if normalized.startswith("/") or normalized.startswith("\\"):
        raise ValueError(f"not_relative:{local_reference}")
    if any(part in {"", ".."} for part in normalized.split("/")):
        raise ValueError(f"unsafe_path:{local_reference}")
    if not normalized.startswith(ALLOWED_LOCAL_PREFIXES):
        raise ValueError(f"not_allowed:{local_reference}")

    root = repo_root.resolve()
    resolved = (root / Path(*normalized.split("/"))).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"outside_root:{local_reference}") from exc
    return resolved


def _local_reference_errors(repo_root: Path, fixture: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for target in fixture["runner_targets"]:
        local_reference = target["local_reference"]
        try:
            path = _resolve_allowed_reference(repo_root, local_reference)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if not path.exists():
            errors.append(f"missing:{local_reference}")
    return errors


def _review_state_errors(repo_root: Path, fixture: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for target in fixture["runner_targets"]:
        if target["artifact_type"] != "json_fixture":
            continue
        if target["expected_state"] != OPERATOR_REVIEW_STATUS:
            continue

        local_reference = target["local_reference"]
        path = _resolve_allowed_reference(repo_root, local_reference)
        artifact = _load_json(path)
        if artifact.get("operator_review", {}).get("status") != OPERATOR_REVIEW_STATUS:
            errors.append(f"review_state:{local_reference}")
    return errors


def _validation_command_errors(fixture: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if tuple(fixture["required_validation_commands"]) != EXPECTED_VALIDATION_COMMANDS:
        errors.append("validation_commands")
    if [record["command_label"] for record in fixture["validation_command_records"]] != list(
        EXPECTED_VALIDATION_COMMANDS
    ):
        errors.append("validation_command_records")
    if any(record["status"] != "not_run_static_record" for record in fixture["validation_command_records"]):
        errors.append("validation_command_status")
    return errors


def _boundary_errors(fixture: dict[str, Any]) -> list[str]:
    boundaries = fixture["safety_boundaries"]
    errors = [f"boundary:{key}" for key in TRUE_SAFETY_BOUNDARIES if boundaries.get(key) is not True]
    errors.extend(f"boundary:{key}" for key, value in boundaries.items() if key.endswith("_allowed") and value is not False)
    return sorted(errors)


def _check_record(check_id: str, passed: bool, detail: str) -> dict[str, str]:
    return {
        "check_id": check_id,
        "detail": detail,
        "status": "passed" if passed else "failed",
    }


if __name__ == "__main__":
    raise SystemExit(main())
