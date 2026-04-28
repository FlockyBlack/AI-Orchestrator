import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "codex-result.schema.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_result(result: dict, schema: dict) -> list[str]:
    errors: list[str] = []
    required = schema.get("required", [])
    properties = schema.get("properties", {})

    if not isinstance(result, dict):
        return ["result must be a JSON object"]

    missing = [field for field in required if field not in result]
    if missing:
        errors.append("missing required fields: " + ", ".join(missing))

    for field in result:
        if schema.get("additionalProperties") is False and field not in properties:
            errors.append(f"unexpected field: {field}")

    status = result.get("status")
    if status not in {"done", "failed", "needs_human"}:
        errors.append("status must be one of: done, failed, needs_human")

    summary = result.get("summary")
    if not isinstance(summary, str):
        errors.append("summary must be a string")
    elif len(summary) > 300:
        errors.append("summary length must be <= 300")

    files_changed = result.get("files_changed")
    if not isinstance(files_changed, list):
        errors.append("files_changed must be an array")

    commands_run = result.get("commands_run")
    if not isinstance(commands_run, list):
        errors.append("commands_run must be an array")

    tests = result.get("tests")
    if not isinstance(tests, dict):
        errors.append("tests must be an object")

    risks = result.get("risks")
    if not isinstance(risks, list):
        errors.append("risks must be an array")

    next_tasks = result.get("next_tasks")
    if not isinstance(next_tasks, list):
        errors.append("next_tasks must be an array")

    needs_human = result.get("needs_human")
    if not isinstance(needs_human, bool):
        errors.append("needs_human must be a boolean")

    handoff = result.get("handoff")
    if not isinstance(handoff, str):
        errors.append("handoff must be a string")
    elif len(handoff) > 1000:
        errors.append("handoff length must be <= 1000")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result", required=True)
    args = parser.parse_args()

    result_path = Path(args.result)
    if not result_path.is_absolute():
        result_path = (ROOT / result_path).resolve()

    schema = load_json(SCHEMA_PATH)
    result = load_json(result_path)
    errors = validate_result(result, schema)

    print(
        json.dumps(
            {
                "status": "valid" if not errors else "invalid",
                "result_path": str(result_path),
                "errors": errors,
            },
            separators=(",", ":"),
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
