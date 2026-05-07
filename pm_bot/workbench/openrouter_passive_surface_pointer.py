import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-OPENROUTER-053-WORKBENCH-PASSIVE-SURFACE-MULTI-BATCH-INTEGRATION"
SCHEMA_VERSION = "openrouter_passive_surface_pointer.v1"
GENERATED_BY = "pm_bot/workbench/openrouter_passive_surface_pointer.py"
WORKBENCH_INTEGRATION_MODE = "read_only_passive_context_multi_batch"

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import openrouter_operator_review_artifacts_053 as artifacts_053  # noqa: E402

WORKBENCH_DIR = ROOT / "pm_bot" / "workbench"
DEFAULT_POINTER_JSON = WORKBENCH_DIR / "openrouter_passive_surface_pointer.v1.json"
DEFAULT_POINTER_MD = WORKBENCH_DIR / "openrouter_passive_surface_pointer.v1.md"

N3_SURFACE_JSON_PATH = "pm_bot/llm/operator_openrouter_batch_surface_046.v1.json"
N3_SURFACE_MD_PATH = "pm_bot/llm/operator_openrouter_batch_surface_046.v1.md"
N5_SURFACE_JSON_PATH = "pm_bot/llm/operator_openrouter_batch_surface_051.v1.json"
N5_SURFACE_MD_PATH = "pm_bot/llm/operator_openrouter_batch_surface_051.v1.md"
DASHBOARD_JSON_PATH = "pm_bot/workbench/operator_openrouter_review_dashboard.v1.json"
DASHBOARD_MD_PATH = "pm_bot/workbench/operator_openrouter_review_dashboard.v1.md"

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
        description="Export the PMBOT multi-batch OpenRouter passive surface pointer."
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


def _artifact_pointer(path, role):
    return {"path": path, "role": role}


def _normalization_summary(surface):
    if isinstance(surface.get("normalization_summary"), dict):
        return dict(surface["normalization_summary"])
    normalization = _safe_dict(surface.get("normalization"))
    return {
        "fenced_response_count": normalization.get("fenced_response_count", 0),
        "normalized_response_count": normalization.get("normalized_response_count", 0),
        "clean_raw_json_response_count": normalization.get("clean_raw_json_response_count", 0),
        "policy": normalization.get("policy") or "fenced_json_normalization.v1",
        "raw_response_preserved": normalization.get("raw_response_preserved", True),
        "semantic_repair_allowed": normalization.get("semantic_repair_allowed", False),
    }


def _quality_summary(surface):
    if isinstance(surface.get("quality_summary"), dict):
        return dict(surface["quality_summary"])
    quality = _safe_dict(surface.get("quality"))
    return {
        "accepted_for_operator_review_count": surface.get("accepted_for_operator_review_count", 0),
        "blocked_count": surface.get("blocked_count", 0),
        "schema_validation_accepted_count": quality.get("schema_validation_accepted_count", 0),
        "acceptance_gate_passed_count": quality.get("acceptance_gate_passed_count", 0),
        "prohibited_content_detected_count": quality.get("prohibited_content_detected_count", 0),
        "forbidden_phrase_detected_count": quality.get("forbidden_phrase_detected_count", 0),
        "baseline_suitable_for_future_controlled_expansion": quality.get(
            "baseline_suitable_for_future_controlled_expansion", False
        ),
    }


def _markets_for_surface(surface):
    source_summary = _safe_dict(surface.get("source_summary"))
    return (
        _safe_list(surface.get("surfaced_market_ids"))
        or _safe_list(source_summary.get("markets_included"))
    )


def _calls_for_surface(surface):
    source_summary = _safe_dict(surface.get("source_summary"))
    return surface.get("total_openrouter_calls_performed") or source_summary.get(
        "source_openrouter_calls_performed", 0
    )


def _required_flag_status(surface):
    safety = _safe_dict(surface.get("safety_summary"))
    return {
        flag: bool(surface.get(flag) is True and safety.get(flag) is True)
        for flag in REQUIRED_TRUE_FLAGS
    }


def _surface_history_entry(batch_label, surface, surface_load_status, surface_json, surface_md):
    markets = _markets_for_surface(surface)
    aggregate_usage = _safe_dict(surface.get("aggregate_usage"))
    aggregate_cost = _safe_dict(surface.get("aggregate_cost"))
    normalization = _normalization_summary(surface)
    quality = _quality_summary(surface)
    flags = _required_flag_status(surface)
    return {
        "batch_label": batch_label,
        "surface_load_status": surface_load_status,
        "surface_status": surface.get("status", "not_available"),
        "source_protocol_task": surface.get("source_protocol_task"),
        "source_batch_task": surface.get("source_batch_task"),
        "source_baseline_task": surface.get("source_baseline_task"),
        "source_surface_task": surface.get("surface_task_id") or surface.get("task_id"),
        "model": surface.get("model")
        or _safe_dict(surface.get("source_summary")).get("model")
        or artifacts_053.MODEL,
        "surfaced_market_ids": markets,
        "total_calls": _calls_for_surface(surface),
        "aggregate_usage": aggregate_usage,
        "aggregate_cost": aggregate_cost,
        "normalization_summary": normalization,
        "quality_summary": quality,
        "required_flag_status": flags,
        "artifact_paths": {
            "surface_json": surface_json,
            "surface_markdown": surface_md,
        },
    }


def _source_artifact_pointers(surface, prefix):
    pointers = {}
    for key, item in _safe_dict(surface.get("artifact_pointers")).items():
        path = _safe_dict(item).get("path")
        if path:
            pointers[f"{prefix}_{key}"] = _artifact_pointer(path, "read_only_source_summary")
    return pointers


def _combined_aggregate_usage(n3, n5):
    return {
        "total_openrouter_calls": n3["total_calls"] + n5["total_calls"],
        "prompt_tokens": n3["aggregate_usage"].get("prompt_tokens", 0)
        + n5["aggregate_usage"].get("prompt_tokens", 0),
        "completion_tokens": n3["aggregate_usage"].get("completion_tokens", 0)
        + n5["aggregate_usage"].get("completion_tokens", 0),
        "total_tokens": artifacts_053.COMBINED_OPENROUTER_CONTOUR_SUMMARY["combined_tokens"],
    }


def _combined_aggregate_cost():
    return {
        "total_cost": artifacts_053.COMBINED_OPENROUTER_CONTOUR_SUMMARY["combined_cost"],
        "average_cost_per_market": artifacts_053.COMBINED_OPENROUTER_CONTOUR_SUMMARY[
            "average_cost_per_market_combined"
        ],
    }


def _pointer_is_ready(n3, n5, n3_status, n5_status):
    return (
        n3_status == "parsed"
        and n5_status == "parsed"
        and n3.get("surface_status") == "passive_operator_surface_created"
        and n5.get("surface_status") == "passive_operator_surface_created"
        and all(n3.get("required_flag_status", {}).values())
        and all(n5.get("required_flag_status", {}).values())
    )


def build_openrouter_passive_surface_pointer(root=ROOT):
    n3_path = _resolve_path(N3_SURFACE_JSON_PATH, root=root)
    n5_path = _resolve_path(N5_SURFACE_JSON_PATH, root=root)
    n3_surface, n3_status = _load_optional_json(n3_path)
    n5_surface, n5_status = _load_optional_json(n5_path)
    n3_surface = _safe_dict(n3_surface)
    n5_surface = _safe_dict(n5_surface)

    n3 = _surface_history_entry("N=3", n3_surface, n3_status, N3_SURFACE_JSON_PATH, N3_SURFACE_MD_PATH)
    n5 = _surface_history_entry("N=5", n5_surface, n5_status, N5_SURFACE_JSON_PATH, N5_SURFACE_MD_PATH)
    ready = _pointer_is_ready(n3, n5, n3_status, n5_status)
    status = "passive_surface_pointer_ready" if ready else "passive_surface_pointer_source_incomplete"
    combined_summary = artifacts_053.COMBINED_OPENROUTER_CONTOUR_SUMMARY

    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "status": status,
        "workbench_integration_mode": WORKBENCH_INTEGRATION_MODE,
        "source_load_status": {
            "n3_surface_json": n3_status,
            "n5_surface_json": n5_status,
        },
        **SAFETY_TRUE_FLAGS,
        "latest_surface_source_batch_task": "PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL",
        "latest_surface_task": artifacts_053.SURFACE_TASK_ID,
        "source_batch_task": "PMBOT-OPENROUTER-051-CONTROLLED-N5-BATCH-LIVE-CALL",
        "source_baseline_task": "PMBOT-OPENROUTER-052-N5-BATCH-BASELINE-QUALITY-AND-OPERATOR-SUMMARY",
        "source_surface_task": artifacts_053.SURFACE_TASK_ID,
        "source_048_status": artifacts_053._status("docs/PMBOT_OPENROUTER_048_RESULT.json", root=root),
        "source_052_status": artifacts_053._status("docs/PMBOT_OPENROUTER_052_RESULT.json", root=root),
        "surfaced_market_ids": list(n5["surfaced_market_ids"]),
        "model": n5["model"],
        "total_calls": n5["total_calls"],
        "aggregate_usage": n5["aggregate_usage"],
        "aggregate_cost": n5["aggregate_cost"],
        "normalization_summary": n5["normalization_summary"],
        "quality_summary": n5["quality_summary"],
        "surface_history": [n3, n5],
        "n3_summary": n3,
        "n5_summary": n5,
        "latest_n5_summary": n5,
        "combined_openrouter_review_contour_summary": dict(combined_summary),
        "combined_aggregate_usage": _combined_aggregate_usage(n3, n5),
        "combined_aggregate_cost": _combined_aggregate_cost(),
        "required_flag_status": {
            flag: bool(
                n3["required_flag_status"].get(flag) is True
                and n5["required_flag_status"].get(flag) is True
            )
            for flag in REQUIRED_TRUE_FLAGS
        },
        "safety_summary": {
            **SAFETY_TRUE_FLAGS,
            **SAFETY_FALSE_FLAGS,
            "openrouter_calls_performed": 0,
            "polymarket_api_calls_performed": 0,
            "network_calls": 0,
            "orders_created": 0,
            "combined_source_openrouter_calls": combined_summary[
                "total_openrouter_calls_in_successful_batches"
            ],
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
            "operator_openrouter_review_dashboard_json": _artifact_pointer(
                DASHBOARD_JSON_PATH,
                "generated_static_dashboard",
            ),
            "operator_openrouter_review_dashboard_markdown": _artifact_pointer(
                DASHBOARD_MD_PATH,
                "generated_static_dashboard",
            ),
            "n3_surface_json": _artifact_pointer(N3_SURFACE_JSON_PATH, "read_only_passive_source"),
            "n3_surface_markdown": _artifact_pointer(N3_SURFACE_MD_PATH, "read_only_passive_source"),
            "n5_surface_json": _artifact_pointer(N5_SURFACE_JSON_PATH, "read_only_passive_source"),
            "n5_surface_markdown": _artifact_pointer(N5_SURFACE_MD_PATH, "read_only_passive_source"),
            "source_048_result": _artifact_pointer(
                "docs/PMBOT_OPENROUTER_048_RESULT.json",
                "read_only_source_result",
            ),
            "source_052_result": _artifact_pointer(
                "docs/PMBOT_OPENROUTER_052_RESULT.json",
                "read_only_source_result",
            ),
        },
        "source_artifact_pointers": {
            **_source_artifact_pointers(n3_surface, "n3"),
            **_source_artifact_pointers(n5_surface, "n5"),
        },
        "warnings": [
            "all successful batch responses required fenced JSON normalization",
            "no clean raw JSON responses observed",
        ],
        "future_readiness_note": {
            "options_documented_only": True,
            "future_live_calls_approved_by_this_task": False,
            "next_protocol_allowed_without_live_calls": "N=10 readiness protocol after inventory/UX review",
        },
    }


def render_markdown(pointer):
    combined = pointer["combined_openrouter_review_contour_summary"]
    lines = [
        "# PMBOT OpenRouter Passive Surface Pointer v1",
        "",
        f"- schema_version: {pointer['schema_version']}",
        f"- task_id: {pointer['task_id']}",
        f"- generated_by: {pointer['generated_by']}",
        f"- status: {pointer['status']}",
        f"- workbench_integration_mode: {pointer['workbench_integration_mode']}",
        f"- latest_surface_source_batch_task: {pointer['latest_surface_source_batch_task']}",
        f"- latest_surface_task: {pointer['latest_surface_task']}",
        "",
        "## Surface History",
        "",
    ]
    for entry in pointer["surface_history"]:
        lines.extend(
            [
                f"- {entry['batch_label']}",
                f"  source_batch_task: {entry['source_batch_task']}",
                f"  source_baseline_task: {entry['source_baseline_task']}",
                f"  source_surface_task: {entry['source_surface_task']}",
                f"  surfaced_market_ids: {', '.join(entry['surfaced_market_ids'])}",
                f"  calls: {entry['total_calls']}",
                f"  total_tokens: {entry['aggregate_usage'].get('total_tokens', 0)}",
                f"  total_cost: {entry['aggregate_cost'].get('total_cost', 0)}",
                f"  accepted_for_operator_review_count: {entry['quality_summary'].get('accepted_for_operator_review_count', 0)}",
                f"  blocked_count: {entry['quality_summary'].get('blocked_count', 0)}",
            ]
        )
    lines.extend(
        [
            "",
            "## Combined Summary",
            "",
            f"- total_markets_successfully_reviewed: {combined['total_markets_successfully_reviewed']}",
            f"- total_openrouter_calls_in_successful_batches: {combined['total_openrouter_calls_in_successful_batches']}",
            f"- combined_cost: {combined['combined_cost']}",
            f"- combined_tokens: {combined['combined_tokens']}",
            f"- total_blocked_in_successful_batches: {combined['total_blocked_in_successful_batches']}",
            "",
            "## Normalization Warnings",
            "",
        ]
    )
    for warning in pointer["warnings"]:
        lines.append(f"- {warning}")
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
    lines.append("")
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
        "latest_surface_source_batch_task": pointer["latest_surface_source_batch_task"],
        "latest_surface_task": pointer["latest_surface_task"],
        "surface_history_count": len(pointer["surface_history"]),
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
