import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

CONTRACT_VERSION = "actual_manual_llm_response_workbench_surface.v1"
GENERATED_BY = "pm_bot/llm/summarize_actual_manual_llm_response_trial.py"
DEFAULT_TRIAL_ARTIFACT_PATH = "pm_bot/llm/actual_manual_llm_response_trial.v1.json"
DEFAULT_OPERATOR_RESPONSE_PATH = "pm_bot/llm/real_local_market_llm_trial_response_operator.v1.json"

OFFLINE_REVIEW_WARNING = (
    "This surface is offline review context only. It is not a truth source, not trading "
    "advice, and not execution authority."
)

NOT_AVAILABLE = "not_available"

SAFETY_FLAGS = {
    "offline_review_context_only": True,
    "not_truth_source": True,
    "not_trading_advice": True,
    "not_execution_authority": True,
    "surface_only": True,
    "local_file_reads_only": True,
    "deterministic": True,
    "runtime_wiring": False,
    "network_api": False,
    "llm_api": False,
    "browser_automation": False,
    "prompt_automation": False,
    "credentials_or_wallet": False,
    "real_orders_or_live_trading": False,
    "autonomous_paper_orders": False,
    "probability_ev_scoring_or_edge": False,
    "side_recommendations": False,
    "market_decision_logic": False,
    "truth_evaluation": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Summarize the deterministic local actual manual LLM response trial artifact."
    )
    parser.add_argument("--artifact", default=DEFAULT_TRIAL_ARTIFACT_PATH)
    parser.add_argument("--operator-response", default=None)
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv)


def _resolve_path(path, root):
    value = Path(path)
    if value.is_absolute():
        return value
    return Path(root) / value


def _display_path(path, root):
    resolved = Path(path).resolve()
    try:
        value = resolved.relative_to(Path(root).resolve())
    except ValueError:
        value = resolved
    return str(value).replace("\\", "/")


def _safe_dict(value):
    if isinstance(value, dict):
        return value
    return {}


def _safe_list(value):
    if isinstance(value, list):
        return value
    return []


def _operator_response_path_from_payload(payload, root, override_path=None):
    if override_path:
        return _resolve_path(override_path, root)
    payload_path = _safe_dict(payload).get("operator_response_path")
    if isinstance(payload_path, str) and payload_path:
        return _resolve_path(payload_path, root)
    return _resolve_path(DEFAULT_OPERATOR_RESPONSE_PATH, root)


def _base_summary(artifact_path, operator_response_path, artifact_present, parse_status, root):
    return {
        "contract_version": CONTRACT_VERSION,
        "generated_by": GENERATED_BY,
        "artifact_path": _display_path(artifact_path, root),
        "artifact_present": artifact_present,
        "artifact_status": "present" if artifact_present else "missing",
        "parse_status": parse_status,
        "operator_response_path": _display_path(operator_response_path, root),
        "operator_response_present": operator_response_path.exists(),
        "trial_artifact_operator_response_present": None,
        "market_id": "",
        "source_artifact_path": "",
        "response_source_type": "",
        "trial_packet_source_type": "",
        "run_status": NOT_AVAILABLE,
        "acceptance_status": NOT_AVAILABLE,
        "packet_validation_status": NOT_AVAILABLE,
        "response_validation_status": NOT_AVAILABLE,
        "manual_review_status": NOT_AVAILABLE,
        "quality_gate_status": NOT_AVAILABLE,
        "errors_count": 0,
        "warnings_count": 0,
        "next_safe_operator_action": "Review local artifact availability only; do not execute or automate anything.",
        "safe_error_summary": [],
        "safety_flags": dict(SAFETY_FLAGS),
        "offline_review_context_only": True,
        "not_truth_source": True,
        "not_trading_advice": True,
        "not_execution_authority": True,
        "explicit_operator_warning": OFFLINE_REVIEW_WARNING,
        "surface_only": True,
        "llm_text_generated": False,
        "llm_api_calls_added": False,
        "browser_automation_added": False,
        "runtime_integration_added": False,
    }


def _status_field(payload, field):
    value = payload.get(field)
    return value if isinstance(value, str) and value else NOT_AVAILABLE


def summarize_actual_manual_llm_response_trial(
    artifact_path=DEFAULT_TRIAL_ARTIFACT_PATH,
    operator_response_path=None,
    root=ROOT,
):
    root = Path(root)
    artifact = _resolve_path(artifact_path, root)
    default_operator_response = _operator_response_path_from_payload({}, root, operator_response_path)
    if not artifact.exists():
        summary = _base_summary(artifact, default_operator_response, False, "missing", root)
        summary["safe_error_summary"] = [
            "Actual manual LLM response trial artifact is not available locally."
        ]
        return summary

    try:
        payload = json.loads(artifact.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        summary = _base_summary(artifact, default_operator_response, True, "parse_failed", root)
        summary["artifact_status"] = "invalid"
        summary["safe_error_summary"] = [
            f"Actual manual LLM response trial artifact could not be read safely: {type(exc).__name__}."
        ]
        return summary

    if not isinstance(payload, dict):
        summary = _base_summary(artifact, default_operator_response, True, "top_level_not_object", root)
        summary["artifact_status"] = "invalid"
        summary["safe_error_summary"] = [
            "Actual manual LLM response trial artifact parsed but is not a JSON object."
        ]
        return summary

    operator_response = _operator_response_path_from_payload(payload, root, operator_response_path)
    summary = _base_summary(artifact, operator_response, True, "parsed", root)
    summary.update(
        {
            "trial_artifact_operator_response_present": bool(
                payload.get("operator_response_present", False)
            ),
            "market_id": str(payload.get("market_id") or ""),
            "source_artifact_path": str(payload.get("source_artifact_path") or ""),
            "response_source_type": str(payload.get("response_source_type") or ""),
            "trial_packet_source_type": str(payload.get("trial_packet_source_type") or ""),
            "run_status": _status_field(payload, "run_status"),
            "acceptance_status": _status_field(payload, "acceptance_status"),
            "packet_validation_status": _status_field(payload, "packet_validation_status"),
            "response_validation_status": _status_field(payload, "response_validation_status"),
            "manual_review_status": _status_field(payload, "manual_review_status"),
            "quality_gate_status": _status_field(payload, "quality_gate_status"),
            "errors_count": len(_safe_list(payload.get("errors"))),
            "warnings_count": len(_safe_list(payload.get("warnings"))),
            "next_safe_operator_action": str(
                payload.get("next_safe_operator_action")
                or "Review the local trial artifact as offline operator context only."
            ),
        }
    )
    return summary


def render_markdown(summary):
    lines = [
        "# PMBOT Actual Manual LLM Response Workbench Surface v1",
        "",
        f"- contract_version: {summary['contract_version']}",
        f"- artifact_path: {summary['artifact_path']}",
        f"- artifact_present: {str(summary['artifact_present']).lower()}",
        f"- artifact_status: {summary['artifact_status']}",
        f"- parse_status: {summary['parse_status']}",
        f"- operator_response_path: {summary['operator_response_path']}",
        f"- operator_response_present: {str(summary['operator_response_present']).lower()}",
        "- trial_artifact_operator_response_present: "
        f"{str(summary['trial_artifact_operator_response_present']).lower()}",
        f"- market_id: {summary['market_id'] or 'not_available'}",
        f"- source_artifact_path: {summary['source_artifact_path'] or 'not_available'}",
        f"- response_source_type: {summary['response_source_type'] or 'not_available'}",
        f"- trial_packet_source_type: {summary['trial_packet_source_type'] or 'not_available'}",
        f"- run_status: {summary['run_status']}",
        f"- acceptance_status: {summary['acceptance_status']}",
        f"- response_validation_status: {summary['response_validation_status']}",
        f"- manual_review_status: {summary['manual_review_status']}",
        f"- quality_gate_status: {summary['quality_gate_status']}",
        f"- errors_count: {summary['errors_count']}",
        f"- warnings_count: {summary['warnings_count']}",
        f"- next_safe_operator_action: {summary['next_safe_operator_action']}",
        "",
        "## Safety Flags",
        "",
    ]
    for key in sorted(summary["safety_flags"]):
        lines.append(f"- {key}: {str(summary['safety_flags'][key]).lower()}")
    lines.extend(["", "## Explicit Warning", "", f"- {summary['explicit_operator_warning']}", ""])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    summary = summarize_actual_manual_llm_response_trial(
        artifact_path=args.artifact,
        operator_response_path=args.operator_response,
        root=ROOT,
    )
    if args.markdown:
        print(render_markdown(summary), end="")
    else:
        print(json.dumps(summary, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
