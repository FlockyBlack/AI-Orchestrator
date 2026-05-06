import argparse
import json
import sys
from json import JSONDecodeError
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import validate_llm_analysis_artifacts as validator  # noqa: E402


CONTRACT_VERSION = "manual_llm_paste_in_review_contract.v1"
MANUAL_REVIEW_VERSION = "manual_llm_paste_in_review.v1"
DETERMINISTIC_GENERATED_AT = "deterministic-manual-llm-paste-in-review.v1"

DEFAULT_PACKET_PATH = validator.DEFAULT_PACKET_PATH
DEFAULT_RESPONSE_PATH = validator.LLM_DIR / "manual_llm_paste_in_response_example_valid.v1.json"
DEFAULT_PROMPT_PATH = validator.LLM_DIR / "manual_llm_prompt.v1.md"
DEFAULT_OUT_JSON_PATH = validator.LLM_DIR / "manual_llm_paste_in_review.v1.json"
DEFAULT_OUT_MD_PATH = validator.LLM_DIR / "manual_llm_paste_in_review.v1.md"


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Validate a manually saved LLM response JSON against the PMBOT offline LLM contract."
    )
    parser.add_argument("--packet", default=str(DEFAULT_PACKET_PATH.relative_to(ROOT)))
    parser.add_argument("--response", default=str(DEFAULT_RESPONSE_PATH.relative_to(ROOT)))
    parser.add_argument("--out-json", default=str(DEFAULT_OUT_JSON_PATH.relative_to(ROOT)))
    parser.add_argument("--out-md", default=str(DEFAULT_OUT_MD_PATH.relative_to(ROOT)))
    parser.add_argument("--prompt", default=str(DEFAULT_PROMPT_PATH.relative_to(ROOT)))
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


def _load_json_artifact(path, artifact):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), []
    except FileNotFoundError:
        return None, [
            {
                "code": f"{artifact}_file_missing",
                "path": _display_path(path),
                "message": f"{artifact} JSON file was not found.",
            }
        ]
    except JSONDecodeError as exc:
        return None, [
            {
                "code": f"{artifact}_json_malformed",
                "path": _display_path(path),
                "message": f"{artifact} JSON is malformed at line {exc.lineno}, column {exc.colno}.",
            }
        ]
    except OSError as exc:
        return None, [
            {
                "code": f"{artifact}_load_error",
                "path": _display_path(path),
                "message": f"{artifact} JSON could not be loaded: {exc.__class__.__name__}.",
            }
        ]


def _load_schema(path, artifact):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), []
    except (OSError, JSONDecodeError) as exc:
        return None, [
            {
                "code": f"{artifact}_schema_load_error",
                "path": _display_path(path),
                "message": f"{artifact} schema could not be loaded: {exc.__class__.__name__}.",
            }
        ]


def _validation_from_load_errors(errors):
    return {
        "status": "rejected",
        "errors": errors,
        "warnings": [],
    }


def _with_artifact_paths(result, artifact_paths):
    return {
        "status": result["status"],
        "errors": result["errors"],
        "warnings": result["warnings"],
        "artifact_paths": artifact_paths,
    }


def _aggregate_messages(packet_validation, response_validation):
    errors = []
    warnings = []
    for error in packet_validation["errors"]:
        errors.append({**error, "artifact": "packet"})
    for error in response_validation["errors"]:
        errors.append({**error, "artifact": "response"})
    for warning in packet_validation["warnings"]:
        warnings.append({**warning, "artifact": "packet"})
    for warning in response_validation["warnings"]:
        warnings.append({**warning, "artifact": "response"})
    errors = sorted(errors, key=lambda item: (item["artifact"], item["path"], item["code"], item["message"]))
    warnings = sorted(warnings, key=lambda item: (item["artifact"], item["path"], item["code"], item["message"]))
    return errors, warnings


def _accepted_sections(response_payload):
    if not isinstance(response_payload, dict):
        return []
    return [section for section in validator.ALLOWED_RESPONSE_SECTIONS if section in response_payload]


def _missing_sections(response_payload):
    if not isinstance(response_payload, dict):
        return list(validator.ALLOWED_RESPONSE_SECTIONS)
    return [section for section in validator.ALLOWED_RESPONSE_SECTIONS if section not in response_payload]


def _forbidden_content(errors):
    findings = [
        error
        for error in errors
        if error["code"].startswith("forbidden_response_field")
        or error["code"].startswith("forbidden_packet_field")
        or error["code"].startswith("forbidden_phrase")
        or error["code"].startswith("forbidden_certainty")
    ]
    return {
        "detected": bool(findings),
        "findings": findings,
    }


def _source_artifacts(packet_payload, packet_path, prompt_path, response_path):
    declared = []
    if isinstance(packet_payload, dict) and isinstance(packet_payload.get("source_artifacts"), list):
        declared = packet_payload["source_artifacts"]
    manual_artifacts = {
        "packet": _display_path(packet_path),
        "response": _display_path(response_path),
    }
    if prompt_path and Path(prompt_path).exists():
        manual_artifacts["prompt"] = _display_path(prompt_path)
    return {
        "packet_declared_source_artifacts": declared,
        "manual_artifacts": manual_artifacts,
        "contract_artifacts": [
            _display_path(validator.PACKET_SCHEMA_PATH),
            _display_path(validator.RESPONSE_SCHEMA_PATH),
            _display_path(Path(__file__).resolve().with_name("validate_llm_analysis_artifacts.py")),
        ],
    }


def _operator_summary(status):
    if status == "accepted":
        return (
            "Accepted: the packet and manually saved LLM response passed PMBOT-LLM-001 offline validation. "
            "Use the response only as a manual review aid; this is not trading advice and does not authorize "
            "autonomous action."
        )
    return (
        "Rejected: the packet or manually saved LLM response failed PMBOT-LLM-001 offline validation. "
        "Do not use the response downstream until local JSON artifacts are corrected and revalidated."
    )


def _next_safe_operator_action(status):
    if status == "accepted":
        return "Compare the accepted sections with local source artifacts and manually record unresolved evidence gaps."
    return "Inspect the listed validation errors, replace or edit only the local response JSON, and rerun this validator."


def _prompt_path_if_available(prompt_path):
    if not prompt_path:
        return ""
    resolved = _resolve_path(prompt_path)
    if resolved.exists():
        return _display_path(resolved)
    return ""


def build_manual_review(
    packet_path=DEFAULT_PACKET_PATH,
    response_path=DEFAULT_RESPONSE_PATH,
    prompt_path=DEFAULT_PROMPT_PATH,
):
    packet_path = _resolve_path(packet_path)
    response_path = _resolve_path(response_path)
    prompt_path = _resolve_path(prompt_path) if prompt_path else None

    packet_schema, packet_schema_errors = _load_schema(validator.PACKET_SCHEMA_PATH, "packet")
    response_schema, response_schema_errors = _load_schema(validator.RESPONSE_SCHEMA_PATH, "response")
    packet_payload, packet_load_errors = _load_json_artifact(packet_path, "packet")
    response_payload, response_load_errors = _load_json_artifact(response_path, "response")

    if packet_load_errors or packet_schema_errors:
        packet_result = _validation_from_load_errors(packet_load_errors + packet_schema_errors)
    else:
        packet_result = validator.validate_packet_payload(packet_payload, packet_schema)

    if response_load_errors or response_schema_errors:
        response_result = _validation_from_load_errors(response_load_errors + response_schema_errors)
    else:
        response_result = validator.validate_response_payload(response_payload, response_schema)

    packet_validation = _with_artifact_paths(
        packet_result,
        {
            "packet": _display_path(packet_path),
            "packet_schema": _display_path(validator.PACKET_SCHEMA_PATH),
        },
    )
    response_validation = _with_artifact_paths(
        response_result,
        {
            "response": _display_path(response_path),
            "response_schema": _display_path(validator.RESPONSE_SCHEMA_PATH),
        },
    )
    errors, warnings = _aggregate_messages(packet_validation, response_validation)
    status = "accepted" if packet_result["status"] == "accepted" and response_result["status"] == "accepted" else "rejected"

    return {
        "contract_version": CONTRACT_VERSION,
        "manual_review_version": MANUAL_REVIEW_VERSION,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "packet_path": _display_path(packet_path),
        "prompt_path": _prompt_path_if_available(prompt_path),
        "response_path": _display_path(response_path),
        "validation_status": status,
        "packet_validation": packet_validation,
        "response_validation": response_validation,
        "errors": errors,
        "warnings": warnings,
        "safety_flags": dict(validator.SAFETY_FLAGS),
        "accepted_sections": _accepted_sections(response_payload),
        "missing_sections": _missing_sections(response_payload),
        "forbidden_content_detected": _forbidden_content(errors),
        "operator_summary": _operator_summary(status),
        "next_safe_operator_action": _next_safe_operator_action(status),
        "source_artifacts": _source_artifacts(packet_payload, packet_path, prompt_path, response_path),
    }


def _format_messages(messages):
    if not messages:
        return ["- none"]
    return [
        f"- [{message['artifact']}] {message['path']}: {message['code']} - {message['message']}"
        for message in messages
    ]


def _format_section_list(items):
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]


def render_markdown_summary(result):
    forbidden_findings = result["forbidden_content_detected"]["findings"]
    prompt_path = result["prompt_path"] if result["prompt_path"] else "not available"
    lines = [
        "# PMBOT Manual LLM Paste-In Review v1",
        "",
        f"- Status: {result['validation_status']}",
        f"- Packet path: {result['packet_path']}",
        f"- Prompt path: {prompt_path}",
        f"- Response path: {result['response_path']}",
        f"- Accepted/rejected: {result['validation_status']}",
        "",
        "## Errors",
        *_format_messages(result["errors"]),
        "",
        "## Warnings",
        *_format_messages(result["warnings"]),
        "",
        "## Accepted Sections",
        *_format_section_list(result["accepted_sections"]),
        "",
        "## Missing Sections",
        *_format_section_list(result["missing_sections"]),
        "",
        "## Forbidden Findings",
        *_format_messages(forbidden_findings),
        "",
        "## Next Safe Operator Action",
        result["next_safe_operator_action"],
        "",
        "## Boundary Notice",
        (
            "Manual LLM paste-in only. This artifact is not trading advice and does not add API calls, "
            "LLM API calls, browser automation, prompt automation, runtime integration, orders, autonomous "
            "paper orders, probability estimates, value scoring, side selection, or market decision logic."
        ),
        "",
    ]
    return "\n".join(lines)


def export_manual_review(
    packet_path=DEFAULT_PACKET_PATH,
    response_path=DEFAULT_RESPONSE_PATH,
    out_json_path=DEFAULT_OUT_JSON_PATH,
    out_md_path=DEFAULT_OUT_MD_PATH,
    prompt_path=DEFAULT_PROMPT_PATH,
):
    result = build_manual_review(packet_path, response_path, prompt_path)
    out_json_path = _resolve_path(out_json_path)
    out_md_path = _resolve_path(out_md_path)
    out_json_path.parent.mkdir(parents=True, exist_ok=True)
    out_md_path.parent.mkdir(parents=True, exist_ok=True)
    out_json_path.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    out_md_path.write_text(render_markdown_summary(result), encoding="utf-8")
    return result


def main(argv):
    args = _parse_args(argv)
    result = export_manual_review(args.packet, args.response, args.out_json, args.out_md, args.prompt)
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["validation_status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
