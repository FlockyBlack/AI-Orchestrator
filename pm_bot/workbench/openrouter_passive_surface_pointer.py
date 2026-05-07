import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-OPENROUTER-049-WORKBENCH-PASSIVE-SURFACE-INTEGRATION"
SCHEMA_VERSION = "openrouter_passive_surface_pointer.v1"
GENERATED_BY = "pm_bot/workbench/openrouter_passive_surface_pointer.py"

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

WORKBENCH_DIR = ROOT / "pm_bot" / "workbench"

DEFAULT_POINTER_JSON = WORKBENCH_DIR / "openrouter_passive_surface_pointer.v1.json"
DEFAULT_POINTER_MD = WORKBENCH_DIR / "openrouter_passive_surface_pointer.v1.md"

SOURCE_SURFACE_JSON_PATH = "pm_bot/llm/operator_openrouter_batch_surface_046.v1.json"
SOURCE_SURFACE_MD_PATH = "pm_bot/llm/operator_openrouter_batch_surface_046.v1.md"
SOURCE_048_RESULT_PATH = "docs/PMBOT_OPENROUTER_048_RESULT.json"
SOURCE_048_REPORT_PATH = "docs/PMBOT_OPENROUTER_048_PASSIVE_OPERATOR_SURFACE_046_BATCH.md"

REQUIRED_TRUE_FLAGS = (
    "operator_review_only",
    "passive_context_only",
    "no_trading_authority",
    "no_queue_authority",
    "no_runtime_authority",
    "no_dispatcher_authority",
    "no_wallet_or_order_authority",
    "acceptance_is_not_trading_approval",
    "analysis_only",
    "manual_review_only",
)

SAFETY_TRUE_FLAGS = {
    "operator_review_only": True,
    "passive_context_only": True,
    "no_trading_authority": True,
    "no_queue_authority": True,
    "no_runtime_authority": True,
    "no_dispatcher_authority": True,
    "no_wallet_or_order_authority": True,
    "acceptance_is_not_trading_approval": True,
    "analysis_only": True,
    "manual_review_only": True,
}

SAFETY_FALSE_FLAGS = {
    "raw_model_responses_included": False,
    "per_market_response_text_included": False,
    "openrouter_calls_performed_by_this_task": False,
    "polymarket_api_calls_performed_by_this_task": False,
    "runtime_wiring_added": False,
    "dispatcher_changes_added": False,
    "background_workers_added": False,
    "queue_items_created": False,
    "queue_state_mutated": False,
    "browser_automation_added": False,
    "wallet_or_order_access_added": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export the PMBOT OpenRouter passive surface pointer for local workbench review."
    )
    parser.add_argument("--markdown", action="store_true", help="Print Markdown instead of JSON.")
    parser.add_argument("--write", action="store_true", help="Write pointer JSON and Markdown artifacts.")
    return parser.parse_args(argv)


def _resolve_path(path, root=ROOT):
    value = Path(path)
    if value.is_absolute():
        return value
    return Path(root) / value


def _display_path(path, root=ROOT):
    resolved = Path(path).resolve()
    try:
        value = resolved.relative_to(Path(root).resolve())
    except ValueError:
        value = resolved
    return str(value).replace("\\", "/")


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_optional_json(path):
    value = Path(path)
    if not value.exists():
        return None, "missing"
    try:
        payload = _load_json(value)
    except (OSError, json.JSONDecodeError) as exc:
        return None, type(exc).__name__
    if not isinstance(payload, dict):
        return None, "top_level_not_object"
    return payload, "parsed"


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _safe_dict(value):
    return value if isinstance(value, dict) else {}


def _safe_list(value):
    return value if isinstance(value, list) else []


def _required_flag_status(surface):
    return {
        flag: bool(surface.get(flag) is True and _safe_dict(surface.get("safety_summary")).get(flag) is True)
        for flag in REQUIRED_TRUE_FLAGS
    }


def _surface_is_ready(surface, source_048, surface_load_status, source_048_load_status):
    if surface_load_status != "parsed" or source_048_load_status != "parsed":
        return False
    flags = _required_flag_status(surface)
    return (
        surface.get("status") == "passive_operator_surface_created"
        and source_048.get("status") == "completed_pushed"
        and all(flags.values())
    )


def _artifact_pointer(path, role):
    return {"path": path, "role": role}


def _source_artifact_pointers(surface):
    pointers = {}
    for key, item in _safe_dict(surface.get("artifact_pointers")).items():
        path = _safe_dict(item).get("path")
        if not path:
            continue
        pointers[key] = _artifact_pointer(path, "read_only_source_summary")
    return pointers


def _summary_values(surface, source_048):
    source_summary = _safe_dict(surface.get("source_summary"))
    return {
        "source_batch_task": surface.get("source_batch_task") or "PMBOT-OPENROUTER-046",
        "source_baseline_task": surface.get("source_baseline_task") or "PMBOT-OPENROUTER-047",
        "source_surface_task": "PMBOT-OPENROUTER-048",
        "source_surface_status": surface.get("status") or "not_available",
        "source_048_status": source_048.get("status") or "not_available",
        "surfaced_market_ids": _safe_list(source_summary.get("markets_included"))
        or _safe_list(source_048.get("surfaced_market_ids")),
        "model": source_summary.get("model") or "not_available",
        "total_calls": source_summary.get("source_openrouter_calls_performed", 0),
    }


def build_openrouter_passive_surface_pointer(root=ROOT):
    surface_path = _resolve_path(SOURCE_SURFACE_JSON_PATH, root=root)
    source_048_path = _resolve_path(SOURCE_048_RESULT_PATH, root=root)
    surface, surface_load_status = _load_optional_json(surface_path)
    source_048, source_048_load_status = _load_optional_json(source_048_path)
    surface = _safe_dict(surface)
    source_048 = _safe_dict(source_048)

    source_values = _summary_values(surface, source_048)
    required_flags = _required_flag_status(surface)
    ready = _surface_is_ready(surface, source_048, surface_load_status, source_048_load_status)
    status = "passive_surface_pointer_ready" if ready else "passive_surface_pointer_source_incomplete"

    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "status": status,
        "workbench_integration_mode": "read_only_passive_context",
        "source_load_status": {
            "surface_json": surface_load_status,
            "source_048_result": source_048_load_status,
        },
        **SAFETY_TRUE_FLAGS,
        **source_values,
        "aggregate_usage": _safe_dict(surface.get("aggregate_usage")),
        "aggregate_cost": _safe_dict(surface.get("aggregate_cost")),
        "normalization_summary": _safe_dict(surface.get("normalization_summary")),
        "quality_summary": _safe_dict(surface.get("quality_summary")),
        "required_flag_status": required_flags,
        "safety_summary": {
            **SAFETY_TRUE_FLAGS,
            **SAFETY_FALSE_FLAGS,
            "openrouter_calls_performed": 0,
            "polymarket_api_calls_performed": 0,
            "network_calls": 0,
            "orders_created": 0,
        },
        "artifact_pointers": {
            "workbench_pointer_json": _artifact_pointer(
                "pm_bot/workbench/openrouter_passive_surface_pointer.v1.json",
                "generated_workbench_pointer",
            ),
            "workbench_pointer_markdown": _artifact_pointer(
                "pm_bot/workbench/openrouter_passive_surface_pointer.v1.md",
                "generated_workbench_pointer",
            ),
            "source_surface_json": _artifact_pointer(SOURCE_SURFACE_JSON_PATH, "read_only_passive_source"),
            "source_surface_markdown": _artifact_pointer(SOURCE_SURFACE_MD_PATH, "read_only_passive_source"),
            "source_048_result": _artifact_pointer(SOURCE_048_RESULT_PATH, "read_only_source_result"),
            "source_048_report": _artifact_pointer(SOURCE_048_REPORT_PATH, "read_only_source_report"),
        },
        "source_artifact_pointers": _source_artifact_pointers(surface),
        "warnings": [
            "all_3_source_responses_required_fenced_json_normalization",
            "no_clean_raw_json_responses_observed_in_046",
        ],
        "future_readiness_note": {
            "options_documented_only": True,
            "option_a": {
                "task_id": "PMBOT-OPENROUTER-050-CONTROLLED-N5-BATCH-READINESS-PROTOCOL",
                "purpose": "Protocol-only readiness for a future 5-market controlled batch, no live calls.",
                "run_or_approved_by_049": False,
            },
            "option_b": {
                "task_id": "PMBOT-OPENROUTER-050-OPERATOR-WORKBENCH-OPENROUTER-UX-REFINEMENT",
                "purpose": "Improve local presentation of passive OpenRouter review data in workbench artifacts, no live calls.",
                "run_or_approved_by_049": False,
            },
        },
    }


def render_markdown(pointer):
    lines = [
        "# PMBOT OpenRouter Passive Surface Pointer v1",
        "",
        f"- schema_version: {pointer['schema_version']}",
        f"- task_id: {pointer['task_id']}",
        f"- generated_by: {pointer['generated_by']}",
        f"- status: {pointer['status']}",
        f"- workbench_integration_mode: {pointer['workbench_integration_mode']}",
        f"- source_batch_task: {pointer['source_batch_task']}",
        f"- source_baseline_task: {pointer['source_baseline_task']}",
        f"- source_surface_task: {pointer['source_surface_task']}",
        f"- source_048_status: {pointer['source_048_status']}",
        f"- surfaced_market_ids: {', '.join(pointer['surfaced_market_ids'])}",
        f"- model: {pointer['model']}",
        f"- total_calls: {pointer['total_calls']}",
        "",
        "## Aggregate Usage",
        "",
    ]
    for key, value in pointer["aggregate_usage"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Aggregate Cost", ""])
    for key, value in pointer["aggregate_cost"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Normalization Summary", ""])
    for key, value in pointer["normalization_summary"].items():
        lines.append(f"- {key}: {str(value).lower() if isinstance(value, bool) else value}")
    lines.extend(["", "## Quality Summary", ""])
    for key, value in pointer["quality_summary"].items():
        lines.append(f"- {key}: {str(value).lower() if isinstance(value, bool) else value}")
    lines.extend(["", "## Safety No-Authority Flags", ""])
    for key in REQUIRED_TRUE_FLAGS:
        lines.append(f"- {key}: {str(pointer[key]).lower()}")
    lines.extend(
        [
            f"- raw_model_responses_included: {str(pointer['safety_summary']['raw_model_responses_included']).lower()}",
            "- per_market_response_text_included: "
            f"{str(pointer['safety_summary']['per_market_response_text_included']).lower()}",
            f"- network_calls: {pointer['safety_summary']['network_calls']}",
            f"- orders_created: {pointer['safety_summary']['orders_created']}",
            "",
            "## Artifact Pointers",
            "",
        ]
    )
    for key, item in pointer["artifact_pointers"].items():
        lines.append(f"- {key}: {item['path']} ({item['role']})")
    lines.extend(["", "## Source Artifact Pointers", ""])
    if pointer["source_artifact_pointers"]:
        for key, item in pointer["source_artifact_pointers"].items():
            lines.append(f"- {key}: {item['path']} ({item['role']})")
    else:
        lines.append("- none")
    lines.extend(["", "## Known Warnings", ""])
    for warning in pointer["warnings"]:
        lines.append(f"- {warning}")
    note = pointer["future_readiness_note"]
    lines.extend(
        [
            "",
            "## Future Readiness Note",
            "",
            f"- options_documented_only: {str(note['options_documented_only']).lower()}",
            f"- option_a: {note['option_a']['task_id']} - {note['option_a']['purpose']}",
            f"- option_b: {note['option_b']['task_id']} - {note['option_b']['purpose']}",
            "",
        ]
    )
    return "\n".join(lines)


def write_openrouter_passive_surface_pointer_artifacts(root=ROOT):
    pointer = build_openrouter_passive_surface_pointer(root=root)
    pointer_json = Path(root) / "pm_bot" / "workbench" / "openrouter_passive_surface_pointer.v1.json"
    pointer_md = Path(root) / "pm_bot" / "workbench" / "openrouter_passive_surface_pointer.v1.md"
    _write_json(pointer_json, pointer)
    _write_text(pointer_md, render_markdown(pointer))
    return {
        "task_id": TASK_ID,
        "status": pointer["status"],
        "files_written": [
            _display_path(pointer_json, root=root),
            _display_path(pointer_md, root=root),
        ],
        "source_048_status": pointer["source_048_status"],
        "surfaced_market_ids": pointer["surfaced_market_ids"],
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "network_calls": 0,
        "orders_created": 0,
        "queue_items_created": 0,
    }


def main(argv):
    args = _parse_args(argv)
    if args.write:
        payload = write_openrouter_passive_surface_pointer_artifacts(ROOT)
        print(json.dumps(payload, indent=2, ensure_ascii=True))
        return 0
    pointer = build_openrouter_passive_surface_pointer(ROOT)
    if args.markdown:
        print(render_markdown(pointer), end="")
    else:
        print(json.dumps(pointer, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
