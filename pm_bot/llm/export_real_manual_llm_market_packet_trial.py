import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import evaluate_manual_llm_review_quality_gate as quality_gate  # noqa: E402
from pm_bot.llm import export_manual_llm_prompt as prompt_exporter  # noqa: E402
from pm_bot.llm import validate_llm_analysis_artifacts as validator  # noqa: E402
from pm_bot.llm import validate_manual_llm_paste_in_review as manual_review  # noqa: E402


TASK_ID = "PMBOT-LLM-007-REAL-MANUAL-LLM-MARKET-PACKET-TRIAL"
CONTRACT_VERSION = "real_manual_llm_market_packet_trial_contract.v1"
TRIAL_VERSION = "real_manual_llm_market_packet_trial.v1"
TRIAL_ID = "pmbot-llm-007-real-manual-llm-market-packet-trial"
DETERMINISTIC_GENERATED_AT = "deterministic-real-manual-llm-market-packet-trial.v1"
PACKET_SOURCE_TYPE = "example_packet_trial_not_live_market"

DEFAULT_PACKET_PATH = validator.LLM_DIR / "real_manual_llm_market_packet_trial_packet.v1.json"
DEFAULT_RESPONSE_PATH = validator.LLM_DIR / "real_manual_llm_market_packet_trial_response_example.v1.json"
DEFAULT_OUT_JSON_PATH = validator.LLM_DIR / "real_manual_llm_market_packet_trial.v1.json"
DEFAULT_OUT_MD_PATH = validator.LLM_DIR / "real_manual_llm_market_packet_trial.v1.md"
DEFAULT_OUT_PROMPT_PATH = validator.LLM_DIR / "real_manual_llm_market_packet_trial_prompt.v1.md"

QUALITY_PASS_STATUSES = {"quality_passed", "quality_passed_with_warnings"}

SAFETY_FLAGS = {
    **quality_gate.SAFETY_FLAGS,
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

OPERATOR_TRIAL_STEPS = [
    "Open pm_bot/llm/real_manual_llm_market_packet_trial_prompt.v1.md.",
    "Paste the prompt into ChatGPT, Claude, or Gemini manually.",
    "Ask for strict JSON only, with no Markdown wrapper or extra prose.",
    "Save the response to a local JSON file matching llm_analysis_response_schema.v1.json.",
    (
        "Rerun python pm_bot/llm/export_real_manual_llm_market_packet_trial.py "
        "--response path/to/manual_response.json."
    ),
    "Review accepted/rejected and quality gate status in the JSON and Markdown trial outputs.",
]

BOUNDARY_NOTICE = (
    "No API calls, LLM API calls, browser automation, prompt automation, runtime integration, "
    "live trading, real orders, autonomous paper orders, trading advice, truth evaluation, "
    "outcome estimates, value scoring, advantage claims, side selection, or market decisions."
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export a deterministic offline/manual PMBOT LLM market packet trial."
    )
    parser.add_argument("--packet", default=str(DEFAULT_PACKET_PATH.relative_to(ROOT)))
    parser.add_argument("--response", default=str(DEFAULT_RESPONSE_PATH.relative_to(ROOT)))
    parser.add_argument("--out-json", default=str(DEFAULT_OUT_JSON_PATH.relative_to(ROOT)))
    parser.add_argument("--out-md", default=str(DEFAULT_OUT_MD_PATH.relative_to(ROOT)))
    parser.add_argument("--out-prompt", default=str(DEFAULT_OUT_PROMPT_PATH.relative_to(ROOT)))
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


def _stage_messages(stage, messages):
    staged = []
    for message in messages:
        item = {"stage": stage, **message}
        staged.append(item)
    return sorted(
        staged,
        key=lambda item: (
            item.get("stage", ""),
            item.get("artifact", ""),
            item.get("check", ""),
            item.get("path", ""),
            item.get("code", ""),
            item.get("message", ""),
        ),
    )


def _safe_prompt_export(packet_path, out_prompt_path):
    try:
        return prompt_exporter.export_manual_prompt(packet_path, out_prompt_path)
    except prompt_exporter.ManualPromptExportError as exc:
        return {
            "status": "rejected",
            "manual_prompt_version": prompt_exporter.MANUAL_PROMPT_VERSION,
            "generated_at": prompt_exporter.DETERMINISTIC_GENERATED_AT,
            "packet_path": _display_path(_resolve_path(packet_path)),
            "out_md_path": _display_path(_resolve_path(out_prompt_path)),
            "errors": exc.errors,
            "warnings": [],
            "safety_flags": dict(SAFETY_FLAGS),
        }


def _packet_validation_from(review_result):
    packet_validation = review_result.get("packet_validation")
    if isinstance(packet_validation, dict):
        return packet_validation
    return {"status": "rejected", "errors": [], "warnings": []}


def _response_validation_from(review_result):
    response_validation = review_result.get("response_validation")
    if isinstance(response_validation, dict):
        return response_validation
    return {"status": "rejected", "errors": [], "warnings": []}


def _quality_gate_summary(result):
    return {
        "validation_status": result["validation_status"],
        "base_validator_status": result["base_validator_status"],
        "quality_counts": result["quality_counts"],
        "required_sections_status": result["required_sections_check"]["status"],
        "minimum_content_status": result["minimum_content_check"]["status"],
        "generic_or_placeholder_text_status": result["generic_or_placeholder_text_check"]["status"],
        "unsafe_certainty_status": result["unsafe_certainty_check"]["status"],
        "forbidden_content_status": result["forbidden_content_check"]["status"],
        "manual_review_input_status": result["manual_review_input_check"]["status"],
        "next_safe_operator_action": result["next_safe_operator_action"],
    }


def _manual_review_summary(result):
    return {
        "validation_status": result["validation_status"],
        "accepted_sections": result["accepted_sections"],
        "missing_sections": result["missing_sections"],
        "forbidden_content_detected": result["forbidden_content_detected"],
        "next_safe_operator_action": result["next_safe_operator_action"],
    }


def _source_artifacts(packet_path, prompt_path, response_path, review_result, gate_result):
    declared = []
    review_source = review_result.get("source_artifacts")
    if isinstance(review_source, dict):
        declared = review_source.get("packet_declared_source_artifacts", [])
    return {
        "packet_source_type": PACKET_SOURCE_TYPE,
        "source_packet_template": _display_path(validator.LLM_DIR / "example_llm_analysis_packet.v1.json"),
        "packet_declared_source_artifacts": declared,
        "manual_artifacts": {
            "packet": _display_path(packet_path),
            "prompt": _display_path(prompt_path),
            "response": _display_path(response_path),
        },
        "component_artifacts": {
            "manual_review_flow": _display_path(validator.LLM_DIR / "validate_manual_llm_paste_in_review.py"),
            "quality_gate": _display_path(validator.LLM_DIR / "evaluate_manual_llm_review_quality_gate.py"),
        },
        "contract_artifacts": [
            _display_path(validator.PACKET_SCHEMA_PATH),
            _display_path(validator.RESPONSE_SCHEMA_PATH),
            _display_path(validator.LLM_DIR / "validate_llm_analysis_artifacts.py"),
        ],
        "quality_gate_source_artifacts": gate_result.get("source_artifacts", {}),
    }


def _next_safe_operator_action(validation_status, quality_status):
    if validation_status == "accepted" and quality_status in QUALITY_PASS_STATUSES:
        return (
            "Replace only the response path with a real manually saved JSON response when ready, "
            "then rerun the exporter and inspect the local result artifacts."
        )
    return (
        "Inspect the local validation and quality errors, edit only the local packet or response JSON, "
        "and rerun the exporter."
    )


def build_trial_result(
    packet_path=DEFAULT_PACKET_PATH,
    response_path=DEFAULT_RESPONSE_PATH,
    out_prompt_path=DEFAULT_OUT_PROMPT_PATH,
):
    packet_path = _resolve_path(packet_path)
    response_path = _resolve_path(response_path)
    out_prompt_path = _resolve_path(out_prompt_path)

    prompt_result = _safe_prompt_export(packet_path, out_prompt_path)
    review_result = manual_review.build_manual_review(packet_path, response_path, out_prompt_path)
    gate_result = quality_gate.build_quality_gate(packet_path, response_path, None)

    packet_validation = _packet_validation_from(review_result)
    response_validation = _response_validation_from(review_result)
    manual_review_status = review_result["validation_status"]
    quality_gate_status = gate_result["validation_status"]
    validation_status = (
        "accepted"
        if prompt_result["status"] == "accepted"
        and packet_validation["status"] == "accepted"
        and response_validation["status"] == "accepted"
        and manual_review_status == "accepted"
        and quality_gate_status in QUALITY_PASS_STATUSES
        else "rejected"
    )

    errors = []
    warnings = []
    errors.extend(_stage_messages("prompt_export", prompt_result.get("errors", [])))
    warnings.extend(_stage_messages("prompt_export", prompt_result.get("warnings", [])))
    errors.extend(_stage_messages("manual_review", review_result["errors"]))
    warnings.extend(_stage_messages("manual_review", review_result["warnings"]))
    errors.extend(_stage_messages("quality_gate", gate_result["errors"]))
    warnings.extend(_stage_messages("quality_gate", gate_result["warnings"]))
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
        "contract_version": CONTRACT_VERSION,
        "trial_version": TRIAL_VERSION,
        "trial_id": TRIAL_ID,
        "task_id": TASK_ID,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "packet_source_type": PACKET_SOURCE_TYPE,
        "packet_path": _display_path(packet_path),
        "prompt_path": _display_path(out_prompt_path),
        "response_path": _display_path(response_path),
        "manual_review_status": manual_review_status,
        "quality_gate_status": quality_gate_status,
        "validation_status": validation_status,
        "quality_status": quality_gate_status,
        "errors": errors,
        "warnings": warnings,
        "safety_flags": dict(SAFETY_FLAGS),
        "operator_trial_steps": list(OPERATOR_TRIAL_STEPS),
        "next_safe_operator_action": _next_safe_operator_action(validation_status, quality_gate_status),
        "source_artifacts": _source_artifacts(packet_path, out_prompt_path, response_path, review_result, gate_result),
        "prompt_export": {
            "status": prompt_result["status"],
            "manual_prompt_version": prompt_result["manual_prompt_version"],
            "generated_at": prompt_result["generated_at"],
            "out_md_path": prompt_result["out_md_path"],
        },
        "packet_validation": packet_validation,
        "response_validation": response_validation,
        "manual_review": _manual_review_summary(review_result),
        "quality_gate": _quality_gate_summary(gate_result),
        "safety_boundary": BOUNDARY_NOTICE,
    }


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


def render_markdown_report(result):
    prompt_path = result["prompt_path"]
    response_path = result["response_path"]
    lines = [
        "# PMBOT Real Manual LLM Market Packet Trial v1",
        "",
        f"- Trial status: {result['validation_status']}",
        f"- Packet source: {result['packet_source_type']}",
        f"- Packet path: {result['packet_path']}",
        f"- Prompt path: {prompt_path}",
        f"- Response path: {response_path}",
        f"- Manual review status: {result['manual_review_status']}",
        f"- Quality gate status: {result['quality_gate_status']}",
        "",
        "## Boundary",
        "",
        BOUNDARY_NOTICE,
        "",
        "## Errors",
        "",
        *_format_messages(result["errors"]),
        "",
        "## Warnings",
        "",
        *_format_messages(result["warnings"]),
        "",
        "## Manual Operator Steps For A Real Trial",
        "",
    ]
    for index, step in enumerate(OPERATOR_TRIAL_STEPS, start=1):
        lines.append(f"{index}. {step}")
    lines.extend(
        [
            "",
            "## Current Example Response Status",
            "",
            f"- Packet validation: {result['packet_validation']['status']}",
            f"- Response validation: {result['response_validation']['status']}",
            f"- Manual review: {result['manual_review_status']}",
            f"- Quality gate: {result['quality_gate_status']}",
            "",
            "## Next Safe Operator Action",
            "",
            result["next_safe_operator_action"],
            "",
            "## Source Notes",
            "",
            (
                "This trial uses the existing PMBOT-LLM safe example packet source and is labeled "
                "`example_packet_trial_not_live_market`. It does not transform live data or create a "
                "market decision artifact."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def export_trial(
    packet_path=DEFAULT_PACKET_PATH,
    response_path=DEFAULT_RESPONSE_PATH,
    out_json_path=DEFAULT_OUT_JSON_PATH,
    out_md_path=DEFAULT_OUT_MD_PATH,
    out_prompt_path=DEFAULT_OUT_PROMPT_PATH,
):
    result = build_trial_result(packet_path, response_path, out_prompt_path)
    out_json_path = _resolve_path(out_json_path)
    out_md_path = _resolve_path(out_md_path)
    _write_json(out_json_path, result)
    _write_text(out_md_path, render_markdown_report(result))
    return result


def main(argv):
    args = _parse_args(argv)
    result = export_trial(args.packet, args.response, args.out_json, args.out_md, args.out_prompt)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["validation_status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
