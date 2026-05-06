import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import evaluate_real_manual_llm_trial_operator_acceptance as acceptance  # noqa: E402
from pm_bot.llm import validate_llm_analysis_artifacts as validator  # noqa: E402


TASK_ID = "PMBOT-LLM-010-ACTUAL-MANUAL-LLM-RESPONSE-TRIAL-RUN"
CONTRACT_VERSION = "actual_manual_llm_response_trial_contract.v1"
TRIAL_RUN_VERSION = "actual_manual_llm_response_trial.v1"
TRIAL_RUN_ID = "pmbot-llm-010-actual-manual-llm-response-trial-run"
DETERMINISTIC_GENERATED_AT = "deterministic-actual-manual-llm-response-trial.v1"

PENDING_OPERATOR_INPUT = "pending_operator_input"
ACTUAL_RESPONSE_ACCEPTED = "actual_response_accepted"
ACTUAL_RESPONSE_REJECTED = "actual_response_rejected"
ACTUAL_RESPONSE_BLOCKED = "actual_response_blocked"

DEFAULT_TRIAL_PATH = validator.LLM_DIR / "real_local_market_llm_trial.v1.json"
DEFAULT_PACKET_PATH = validator.LLM_DIR / "real_local_market_llm_trial_packet.v1.json"
DEFAULT_PROMPT_PATH = validator.LLM_DIR / "real_local_market_llm_trial_prompt.v1.md"
DEFAULT_OPERATOR_RESPONSE_PATH = validator.LLM_DIR / "real_local_market_llm_trial_response_operator.v1.json"
DEFAULT_OUT_JSON_PATH = validator.LLM_DIR / "actual_manual_llm_response_trial.v1.json"
DEFAULT_OUT_MD_PATH = validator.LLM_DIR / "actual_manual_llm_response_trial.v1.md"

NOT_RUN = "not_run"

SAFETY_FLAGS = {
    **acceptance.SAFETY_FLAGS,
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
    "dispatcher_or_run_codex_changed": False,
}

OPERATOR_REQUIRED_ACTIONS_PENDING = [
    "Open pm_bot/llm/real_local_market_llm_trial_prompt.v1.md.",
    "Paste into ChatGPT/Claude/Gemini manually.",
    "Request strict JSON only.",
    "Save the returned JSON to pm_bot/llm/real_local_market_llm_trial_response_operator.v1.json.",
    (
        "Rerun python pm_bot\\llm\\run_actual_manual_llm_response_trial.py --trial "
        "pm_bot\\llm\\real_local_market_llm_trial.v1.json --packet "
        "pm_bot\\llm\\real_local_market_llm_trial_packet.v1.json --prompt "
        "pm_bot\\llm\\real_local_market_llm_trial_prompt.v1.md --operator-response "
        "pm_bot\\llm\\real_local_market_llm_trial_response_operator.v1.json --out-json "
        "pm_bot\\llm\\actual_manual_llm_response_trial.v1.json --out-md "
        "pm_bot\\llm\\actual_manual_llm_response_trial.v1.md."
    ),
]

BOUNDARY_WARNING = (
    "no API, no automation, no trading advice, no truth/probability/EV/edge/side/trading execution"
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Run the deterministic offline PMBOT actual manual LLM response trial wrapper."
    )
    parser.add_argument("--trial", default=str(DEFAULT_TRIAL_PATH.relative_to(ROOT)))
    parser.add_argument("--packet", default=str(DEFAULT_PACKET_PATH.relative_to(ROOT)))
    parser.add_argument("--prompt", default=str(DEFAULT_PROMPT_PATH.relative_to(ROOT)))
    parser.add_argument("--operator-response", default=str(DEFAULT_OPERATOR_RESPONSE_PATH.relative_to(ROOT)))
    parser.add_argument("--out-json", default=str(DEFAULT_OUT_JSON_PATH.relative_to(ROOT)))
    parser.add_argument("--out-md", default=str(DEFAULT_OUT_MD_PATH.relative_to(ROOT)))
    return parser.parse_args(argv)


def _resolve_path(path):
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return ROOT / candidate


def _display_path(path):
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _issue(code, path, message):
    return {"code": code, "path": path, "message": message}


def _not_run_validation():
    return {"status": NOT_RUN, "errors": [], "warnings": []}


def _empty_trial_source():
    return {
        "trial_packet_source_type": "",
        "source_artifact_path": "",
        "market_id": "",
        "used_example_packet_fallback": None,
    }


def _prompt_presence_errors(prompt_path):
    if Path(prompt_path).exists():
        return []
    return [
        _issue(
            "prompt_file_missing",
            _display_path(prompt_path),
            "Prompt file is required for the manual operator paste flow.",
        )
    ]


def _verify_trial_and_packet(trial_path, packet_path, prompt_path):
    blocking_errors = []
    rejection_errors = []
    warnings = []
    trial_source = _empty_trial_source()
    packet_validation = _not_run_validation()

    trial_payload, trial_load_errors = acceptance._load_json_artifact(trial_path, "trial")
    if trial_load_errors:
        blocking_errors.extend(acceptance._stage_messages("trial_load", trial_load_errors))
    else:
        trial_summary = acceptance._trial_source_summary(trial_payload)
        trial_source = {
            "trial_packet_source_type": trial_summary["trial_packet_source_type"],
            "source_artifact_path": trial_summary["source_artifact_path"],
            "market_id": trial_summary["market_id"],
            "used_example_packet_fallback": trial_summary["used_example_packet_fallback"],
        }
        blocking_errors.extend(
            acceptance._stage_messages("trial_source_verification", trial_summary["blocking_errors"])
        )
        rejection_errors.extend(
            acceptance._stage_messages("trial_source_verification", trial_summary["rejection_errors"])
        )

    packet_payload, packet_load_errors = acceptance._load_json_artifact(packet_path, "packet")
    packet_schema, packet_schema_errors = acceptance._load_json_artifact(validator.PACKET_SCHEMA_PATH, "packet_schema")
    if packet_load_errors or packet_schema_errors:
        packet_validation = acceptance._validation_from_load_errors(packet_load_errors + packet_schema_errors)
        blocking_errors.extend(acceptance._stage_messages("packet_load", packet_validation["errors"]))
    else:
        packet_validation = validator.validate_packet_payload(packet_payload, packet_schema)
        if packet_validation["status"] != "accepted":
            blocking_errors.extend(acceptance._stage_messages("packet_validation", packet_validation["errors"]))
        packet_blocking, packet_rejection = acceptance._packet_source_verification(packet_payload, trial_source)
        blocking_errors.extend(acceptance._stage_messages("packet_source_verification", packet_blocking))
        rejection_errors.extend(acceptance._stage_messages("packet_source_verification", packet_rejection))

    blocking_errors.extend(acceptance._stage_messages("prompt_presence", _prompt_presence_errors(prompt_path)))
    warnings.extend(acceptance._stage_messages("packet_validation", packet_validation.get("warnings", [])))

    errors = []
    errors.extend(blocking_errors)
    errors.extend(rejection_errors)
    errors = sorted(
        errors,
        key=lambda item: (
            item.get("stage", ""),
            item.get("artifact", ""),
            item.get("check", ""),
            item.get("path", ""),
            item.get("code", ""),
            item.get("message", ""),
        ),
    )
    warnings = sorted(
        warnings,
        key=lambda item: (
            item.get("stage", ""),
            item.get("artifact", ""),
            item.get("check", ""),
            item.get("path", ""),
            item.get("code", ""),
            item.get("message", ""),
        ),
    )
    return {
        "trial_source": trial_source,
        "packet_validation": packet_validation,
        "blocking_errors": blocking_errors,
        "rejection_errors": rejection_errors,
        "errors": errors,
        "warnings": warnings,
    }


def _source_artifacts(trial_path, packet_path, prompt_path, operator_response_path, trial_source):
    return {
        "trial_result": _display_path(trial_path),
        "packet": _display_path(packet_path),
        "prompt": _display_path(prompt_path),
        "operator_response": _display_path(operator_response_path),
        "source_artifact_path": trial_source["source_artifact_path"],
        "market_id": trial_source["market_id"],
        "contract_artifacts": [
            _display_path(validator.PACKET_SCHEMA_PATH),
            _display_path(validator.RESPONSE_SCHEMA_PATH),
        ],
        "component_artifacts": {
            "base_validator": _display_path(validator.LLM_DIR / "validate_llm_analysis_artifacts.py"),
            "manual_review_flow": _display_path(validator.LLM_DIR / "validate_manual_llm_paste_in_review.py"),
            "quality_gate": _display_path(validator.LLM_DIR / "evaluate_manual_llm_review_quality_gate.py"),
            "operator_acceptance_gate": _display_path(
                validator.LLM_DIR / "evaluate_real_manual_llm_trial_operator_acceptance.py"
            ),
            "actual_manual_response_trial_runner": _display_path(Path(__file__).resolve()),
        },
    }


def _base_result(
    trial_path,
    packet_path,
    prompt_path,
    operator_response_path,
    operator_response_present,
    trial_source,
    run_status,
    acceptance_status,
    packet_validation_status,
    response_validation_status,
    manual_review_status,
    quality_gate_status,
    errors,
    warnings,
    operator_required_actions,
    next_safe_operator_action,
):
    return {
        "contract_version": CONTRACT_VERSION,
        "trial_run_version": TRIAL_RUN_VERSION,
        "trial_run_id": TRIAL_RUN_ID,
        "task_id": TASK_ID,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "trial_path": _display_path(trial_path),
        "packet_path": _display_path(packet_path),
        "prompt_path": _display_path(prompt_path),
        "operator_response_path": _display_path(operator_response_path),
        "operator_response_present": operator_response_present,
        "response_source_type": acceptance.ACTUAL_OPERATOR_PASTED_RESPONSE,
        "market_id": trial_source["market_id"],
        "source_artifact_path": trial_source["source_artifact_path"],
        "trial_packet_source_type": trial_source["trial_packet_source_type"],
        "used_example_packet_fallback": trial_source["used_example_packet_fallback"],
        "run_status": run_status,
        "acceptance_status": acceptance_status,
        "packet_validation_status": packet_validation_status,
        "response_validation_status": response_validation_status,
        "manual_review_status": manual_review_status,
        "quality_gate_status": quality_gate_status,
        "errors": errors,
        "warnings": warnings,
        "operator_required_actions": operator_required_actions,
        "next_safe_operator_action": next_safe_operator_action,
        "safety_flags": dict(SAFETY_FLAGS),
        "source_artifacts": _source_artifacts(
            trial_path, packet_path, prompt_path, operator_response_path, trial_source
        ),
    }


def _missing_response_result(trial_path, packet_path, prompt_path, operator_response_path, verification):
    trial_source = verification["trial_source"]
    warnings = list(verification["warnings"])
    operator_missing_warning = {
        "stage": "operator_response_presence",
        "code": "operator_response_file_missing",
        "path": _display_path(operator_response_path),
        "message": "Actual operator-pasted response file is missing; no fake response was created.",
    }

    if verification["blocking_errors"]:
        return _base_result(
            trial_path,
            packet_path,
            prompt_path,
            operator_response_path,
            False,
            trial_source,
            ACTUAL_RESPONSE_BLOCKED,
            acceptance.BLOCKED,
            verification["packet_validation"]["status"],
            NOT_RUN,
            NOT_RUN,
            NOT_RUN,
            verification["errors"],
            warnings + [operator_missing_warning],
            [
                "Fix missing, malformed, or unverifiable local trial, packet, and prompt artifacts.",
                "Rerun this wrapper before saving or accepting any operator response.",
            ],
            "fix_local_trial_packet_or_prompt_artifacts",
        )

    if verification["rejection_errors"]:
        return _base_result(
            trial_path,
            packet_path,
            prompt_path,
            operator_response_path,
            False,
            trial_source,
            ACTUAL_RESPONSE_REJECTED,
            acceptance.REJECTED,
            verification["packet_validation"]["status"],
            NOT_RUN,
            NOT_RUN,
            NOT_RUN,
            verification["errors"],
            warnings + [operator_missing_warning],
            [
                "Correct the non-real or fallback trial source selection before requesting operator response.",
                "Rerun this wrapper after the local trial proves real_local_market_artifact with no example fallback.",
            ],
            "fix_trial_source_selection",
        )

    return _base_result(
        trial_path,
        packet_path,
        prompt_path,
        operator_response_path,
        False,
        trial_source,
        PENDING_OPERATOR_INPUT,
        acceptance.PENDING,
        verification["packet_validation"]["status"],
        NOT_RUN,
        NOT_RUN,
        NOT_RUN,
        [],
        warnings + [operator_missing_warning],
        list(OPERATOR_REQUIRED_ACTIONS_PENDING),
        "save_actual_operator_pasted_response",
    )


def _map_acceptance_status(acceptance_status):
    if acceptance_status == acceptance.ACCEPTED:
        return ACTUAL_RESPONSE_ACCEPTED
    if acceptance_status == acceptance.REJECTED:
        return ACTUAL_RESPONSE_REJECTED
    return ACTUAL_RESPONSE_BLOCKED


def _actual_response_result(trial_path, packet_path, prompt_path, operator_response_path):
    acceptance_result = acceptance.build_acceptance(
        trial_path,
        packet_path,
        prompt_path,
        operator_response_path,
        acceptance.ACTUAL_OPERATOR_PASTED_RESPONSE,
    )
    trial_source = {
        "trial_packet_source_type": acceptance_result["trial_packet_source_type"],
        "source_artifact_path": acceptance_result["source_artifact_path"],
        "market_id": acceptance_result["market_id"],
        "used_example_packet_fallback": acceptance_result["used_example_packet_fallback"],
    }
    return _base_result(
        trial_path,
        packet_path,
        prompt_path,
        operator_response_path,
        True,
        trial_source,
        _map_acceptance_status(acceptance_result["acceptance_status"]),
        acceptance_result["acceptance_status"],
        acceptance_result["packet_validation_status"],
        acceptance_result["response_validation_status"],
        acceptance_result["manual_review_status"],
        acceptance_result["quality_gate_status"],
        acceptance_result["errors"],
        acceptance_result["warnings"],
        acceptance_result["operator_required_actions"],
        acceptance_result["next_safe_operator_action"],
    )


def build_actual_manual_llm_response_trial(
    trial_path=DEFAULT_TRIAL_PATH,
    packet_path=DEFAULT_PACKET_PATH,
    prompt_path=DEFAULT_PROMPT_PATH,
    operator_response_path=DEFAULT_OPERATOR_RESPONSE_PATH,
):
    trial_path = _resolve_path(trial_path)
    packet_path = _resolve_path(packet_path)
    prompt_path = _resolve_path(prompt_path)
    operator_response_path = _resolve_path(operator_response_path)

    verification = _verify_trial_and_packet(trial_path, packet_path, prompt_path)
    if not operator_response_path.exists():
        return _missing_response_result(trial_path, packet_path, prompt_path, operator_response_path, verification)

    return _actual_response_result(trial_path, packet_path, prompt_path, operator_response_path)


def _format_messages(messages):
    if not messages:
        return ["- none"]
    lines = []
    for message in messages:
        stage = f"[{message.get('stage', 'trial')}] "
        artifact = f"{message.get('artifact')}: " if message.get("artifact") else ""
        check = f"{message.get('check')}: " if message.get("check") else ""
        lines.append(
            f"- {stage}{artifact}{check}{message.get('path', '')}: "
            f"{message.get('code', 'message')} - {message.get('message', '')}"
        )
    return lines


def _format_list(items):
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]


def render_markdown_report(result):
    response_status_lines = []
    if result["operator_response_present"]:
        response_status_lines = [
            f"- Response validator status: {result['response_validation_status']}",
            f"- Manual review status: {result['manual_review_status']}",
            f"- Quality gate status: {result['quality_gate_status']}",
        ]
    else:
        response_status_lines = [
            "- Response validator status: not run because actual operator response file is missing",
            "- Manual review status: not run because actual operator response file is missing",
            "- Quality gate status: not run because actual operator response file is missing",
        ]

    lines = [
        "# PMBOT Actual Manual LLM Response Trial Run v1",
        "",
        f"- Run status: {result['run_status']}",
        f"- Actual operator response file exists: {result['operator_response_present']}",
        f"- Prompt path: {result['prompt_path']}",
        f"- Response path: {result['operator_response_path']}",
        f"- Market ID: {result['market_id'] or 'not available'}",
        f"- Source artifact path: {result['source_artifact_path'] or 'not available'}",
        f"- Acceptance status: {result['acceptance_status']}",
        f"- Packet validator status: {result['packet_validation_status']}",
        *response_status_lines,
        "",
        "## Next Action",
        result["next_safe_operator_action"],
        "",
        "## Operator Required Actions",
        *_format_list(result["operator_required_actions"]),
        "",
        "## Errors",
        *_format_messages(result["errors"]),
        "",
        "## Warnings",
        *_format_messages(result["warnings"]),
        "",
        "## Explicit Safety Warning",
        BOUNDARY_WARNING,
        "",
    ]
    return "\n".join(lines)


def export_actual_manual_llm_response_trial(
    trial_path=DEFAULT_TRIAL_PATH,
    packet_path=DEFAULT_PACKET_PATH,
    prompt_path=DEFAULT_PROMPT_PATH,
    operator_response_path=DEFAULT_OPERATOR_RESPONSE_PATH,
    out_json_path=DEFAULT_OUT_JSON_PATH,
    out_md_path=DEFAULT_OUT_MD_PATH,
):
    result = build_actual_manual_llm_response_trial(
        trial_path,
        packet_path,
        prompt_path,
        operator_response_path,
    )
    out_json_path = _resolve_path(out_json_path)
    out_md_path = _resolve_path(out_md_path)
    _write_json(out_json_path, result)
    _write_text(out_md_path, render_markdown_report(result))
    return result


def main(argv):
    args = _parse_args(argv)
    result = export_actual_manual_llm_response_trial(
        args.trial,
        args.packet,
        args.prompt,
        args.operator_response,
        args.out_json,
        args.out_md,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["run_status"] in {PENDING_OPERATOR_INPUT, ACTUAL_RESPONSE_ACCEPTED} else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
