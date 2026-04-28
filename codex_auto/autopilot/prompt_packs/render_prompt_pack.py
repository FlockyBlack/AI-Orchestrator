import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
PROMPT_PACK_ROOT = PROJECT_ROOT / "codex_auto" / "autopilot" / "prompt_packs"
MANIFEST_PATH = PROMPT_PACK_ROOT / "prompt_pack_manifest.v1.json"
REQUEST_SCHEMA_PATH = PROMPT_PACK_ROOT / "prompt_pack_render_request.schema.v1.json"
REPORT_SCHEMA_PATH = PROMPT_PACK_ROOT / "prompt_pack_render_report.schema.v1.json"

from codex_auto.autopilot.run_routing_preflight import build_routing_preflight_report  # noqa: E402

REPORT_TYPE = "AUTOPILOT_PROMPT_PACK_RENDER_REPORT"
REQUEST_SCHEMA_VERSION = "1.0"
GENERATED_BY = "codex_auto/autopilot/prompt_packs/render_prompt_pack.py"
OUTPUT_ALLOWLIST = [
    "codex_auto/autopilot/prompt_packs/output/",
    "codex_auto/autopilot/prompt_packs/tmp/",
    "codex_auto/autopilot/tests/output/",
]
FORBIDDEN_TEXT_CLAIMS = {
    "EXECUTE_NOW": "forbidden_claim:execute_now",
    "FINAL_ACCEPTED": "forbidden_claim:final_accepted",
    "RUNTIME_DONE": "forbidden_claim:runtime_done",
    "AUTO_APPROVE_EXECUTION": "forbidden_claim:auto_approve_execution",
    "AUTO_APPLY_RUNTIME_STATE": "forbidden_claim:auto_apply_runtime_state",
    "runtime_wiring_allowed=true": "forbidden_claim:runtime_wiring_allowed",
    "queue_mutation_allowed=true": "forbidden_claim:queue_mutation_allowed",
    "governance_mutation_allowed=true": "forbidden_claim:governance_mutation_allowed",
    "sessions_spawn_allowed=true": "forbidden_claim:sessions_spawn_allowed",
    "sessions_spawn_allowed_for_flocky: true": "forbidden_claim:sessions_spawn_allowed_for_flocky",
    "execution_approved=true": "forbidden_claim:execution_approved",
    "source_of_truth=codex_auto": "forbidden_claim:source_of_truth_codex_auto",
    "authoritative_runtime_owner=codex_auto": "forbidden_claim:authoritative_runtime_owner_codex_auto",
}
REQUIRED_REQUEST_FIELDS = [
    "schema_version",
    "template_name",
    "task_id",
    "task_title",
    "target_agent",
    "task_owner",
    "task_type",
    "context",
    "goal",
    "allowed_read_paths",
    "allowed_write_paths",
    "forbidden_write_paths",
    "forbidden_behavior",
    "validation_commands",
    "expected_final_json",
    "custom_sections",
    "preflight_receiver",
    "notes",
]
REQUIRED_REPORT_FIELDS = [
    "type",
    "schema_version",
    "render_only",
    "template_name",
    "target_agent",
    "task_owner",
    "task_type",
    "task_id",
    "rendered_prompt",
    "routing_header",
    "preflight_receiver",
    "preflight_report",
    "safe_to_send_to",
    "unsafe_to_send_to",
    "original_prompt_executed",
    "rendered_prompt_executed",
    "sessions_spawn_allowed",
    "runtime_wiring_allowed",
    "queue_mutation_allowed",
    "active_flocky_tool_integration",
    "single_runtime_source_rule_preserved",
    "warnings",
    "errors",
    "generated_by",
    "deterministic_render",
]


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_request_schema():
    return _load_json(REQUEST_SCHEMA_PATH)


def load_report_schema():
    return _load_json(REPORT_SCHEMA_PATH)


def _sorted_unique(items):
    return sorted(set(items))


def _normalize_path(value) -> str:
    return str(Path(str(value))).replace("\\", "/").lower()


def _resolve_project_path(path_str: str) -> Path:
    candidate = Path(path_str)
    if not candidate.is_absolute():
        candidate = (PROJECT_ROOT / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        candidate.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise ValueError(f"path_outside_project_root:{candidate}") from exc
    return candidate


def _to_project_ref(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def _is_under(base_ref: str, candidate_ref: str) -> bool:
    base = base_ref.rstrip("/")
    candidate = candidate_ref.rstrip("/")
    return candidate == base or candidate.startswith(base + "/")


def validate_output_path(path_str: str) -> Path:
    candidate = _resolve_project_path(path_str)
    candidate_ref = _to_project_ref(candidate)
    candidate_norm = _normalize_path(candidate_ref)
    forbidden_roots = [
        "tasks/",
        "runs/",
        "state/",
        "runtime/",
        "results/",
        "freeze/",
        "checkpoint/",
        "governance/",
        "scripts/",
        "pm_bot/",
        "codex_auto/tasks/",
        "codex_auto/queue/",
        "codex_auto/external_cli/",
    ]
    for forbidden in forbidden_roots:
        forbidden_norm = _normalize_path(forbidden).rstrip("/")
        if candidate_norm == forbidden_norm or candidate_norm.startswith(forbidden_norm + "/"):
            raise ValueError(f"output_path_forbidden:{candidate_ref}")
    for allowed_root in OUTPUT_ALLOWLIST:
        if _is_under(_normalize_path(allowed_root), candidate_norm):
            return candidate
    raise ValueError(f"output_path_not_in_allowed_render_area:{candidate_ref}")


def write_render_report(output_path: str, report):
    destination = validate_output_path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return destination


def _read_template_headers(text: str):
    headers = {}
    for raw_line in text.splitlines():
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key.isupper() or key == "SESSIONS_SPAWN_ALLOWED_FOR_FLOCKY":
            headers[key] = value
        if key == "Prompt Pack":
            break
    return headers


def _read_template_body(text: str):
    lines = text.splitlines()
    start = 0
    for idx, line in enumerate(lines):
        if line.startswith("Prompt Pack:"):
            start = idx
            break
    return "\n".join(lines[start:]).strip()


def _scan_forbidden_claims(value, errors):
    if isinstance(value, dict):
        for nested in value.values():
            _scan_forbidden_claims(nested, errors)
        return
    if isinstance(value, list):
        for item in value:
            _scan_forbidden_claims(item, errors)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for term, code in FORBIDDEN_TEXT_CLAIMS.items():
            if term.lower() in lowered:
                errors.append(code)


def _load_manifest():
    return _load_json(MANIFEST_PATH)


def _get_template_record(template_name: str):
    manifest = _load_manifest()
    for item in manifest["prompt_pack_templates"]:
        if item["template_name"] == template_name:
            return item
    return None


def _load_request(request_path: str):
    return _load_json(_resolve_project_path(request_path))


def _render_list_section(title: str, items):
    if not items:
        return f"{title}\n- none"
    return "\n".join([title] + [f"- {item}" for item in items])


def _render_json_section(title: str, payload):
    return "\n".join([title, json.dumps(payload, indent=2, ensure_ascii=False)])


def _build_routing_header(request, template_headers, template_record):
    header = {
        "TARGET_AGENT": request["target_agent"],
        "TASK_OWNER": request["task_owner"],
        "TASK_TYPE": request["task_type"],
        "CODE_CHANGES_ALLOWED_FOR_RECEIVER": "true" if template_record["code_changes_allowed"] else "false",
        "SESSIONS_SPAWN_ALLOWED": "false",
        "RUNTIME_MUTATION_ALLOWED": "false",
        "QUEUE_MUTATION_ALLOWED": "false",
        "GOVERNANCE_MUTATION_ALLOWED": "false",
        "APPROVAL_REQUIRED": "true" if template_record["approval_required"] else "false",
        "MISROUTE_BEHAVIOR": template_headers["MISROUTE_BEHAVIOR"],
    }
    if "SESSIONS_SPAWN_ALLOWED_FOR_FLOCKY" in template_headers:
        header["SESSIONS_SPAWN_ALLOWED_FOR_FLOCKY"] = template_headers["SESSIONS_SPAWN_ALLOWED_FOR_FLOCKY"]
    return header


def _render_prompt(request, template_record, template_text):
    template_headers = _read_template_headers(template_text)
    routing_header = _build_routing_header(request, template_headers, template_record)
    header_lines = [f"{key}: {value}" for key, value in routing_header.items()]
    body_sections = [
        f"Task ID:\n{request['task_id']}",
        f"Task Title:\n{request['task_title']}",
        f"Context:\n{request['context']}",
        f"Goal:\n{request['goal']}",
        _render_list_section("Allowed read paths:", request["allowed_read_paths"]),
    ]

    if request["allowed_write_paths"]:
        body_sections.append(_render_list_section("Allowed write paths:", request["allowed_write_paths"]))
    else:
        body_sections.append("Allowed write paths: none in project root")

    body_sections.extend(
        [
            _render_list_section("Forbidden write paths:", request["forbidden_write_paths"]),
            _render_list_section("Forbidden behavior:", request["forbidden_behavior"]),
        ]
    )
    if request["validation_commands"]:
        body_sections.append(_render_list_section("Required validation commands:", request["validation_commands"]))
    body_sections.append(_render_json_section("Expected final JSON:", request["expected_final_json"]))

    if request["notes"]:
        body_sections.append(_render_list_section("Notes:", request["notes"]))

    for section in request["custom_sections"]:
        body_sections.append(f"{section['title']}:\n{section['body']}")

    body_sections.append("Template Guidance:")
    body_sections.append(_read_template_body(template_text))
    rendered = "\n\n".join(["\n".join(header_lines)] + body_sections).strip() + "\n"
    return routing_header, rendered


def validate_render_request(data):
    errors = []
    warnings = []
    if not isinstance(data, dict):
        return {"valid": False, "errors": ["render_request_must_be_object"], "warnings": []}

    for field in REQUIRED_REQUEST_FIELDS:
        if field not in data:
            errors.append(f"missing:{field}")

    if data.get("schema_version") != REQUEST_SCHEMA_VERSION:
        errors.append(f"schema_version_must_be:{REQUEST_SCHEMA_VERSION}")

    for field in ["template_name", "task_id", "task_title", "target_agent", "task_owner", "task_type", "context", "goal", "preflight_receiver"]:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field}_must_be_non_empty")

    for field in ["allowed_read_paths", "allowed_write_paths", "forbidden_write_paths", "forbidden_behavior", "validation_commands", "notes"]:
        value = data.get(field)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            errors.append(f"{field}_must_be_list_of_strings")

    custom_sections = data.get("custom_sections")
    if not isinstance(custom_sections, list):
        errors.append("custom_sections_must_be_list")
    else:
        for section in custom_sections:
            if not isinstance(section, dict):
                errors.append("custom_section_must_be_object")
                continue
            if not isinstance(section.get("title"), str) or not section["title"].strip():
                errors.append("custom_section_title_must_be_non_empty")
            if not isinstance(section.get("body"), str) or not section["body"].strip():
                errors.append("custom_section_body_must_be_non_empty")

    if not isinstance(data.get("expected_final_json"), dict):
        errors.append("expected_final_json_must_be_object")

    template_record = _get_template_record(data.get("template_name", ""))
    if template_record is None:
        errors.append("unknown_template_name")
    else:
        if data.get("target_agent") != template_record["target_agent"]:
            errors.append("target_agent_template_mismatch")
        if data.get("task_owner") != template_record["target_agent"]:
            errors.append("task_owner_template_mismatch")
        if data.get("task_type") != template_record["task_type"]:
            errors.append("task_type_template_mismatch")

    _scan_forbidden_claims(data, errors)
    return {"valid": not errors, "errors": _sorted_unique(errors), "warnings": warnings}


def validate_render_report(data):
    errors = []
    warnings = []
    if not isinstance(data, dict):
        return {"valid": False, "errors": ["render_report_must_be_object"], "warnings": []}
    for field in REQUIRED_REPORT_FIELDS:
        if field not in data:
            errors.append(f"missing:{field}")
    if data.get("type") != REPORT_TYPE:
        errors.append(f"type_must_be:{REPORT_TYPE}")
    if data.get("schema_version") != REQUEST_SCHEMA_VERSION:
        errors.append(f"schema_version_must_be:{REQUEST_SCHEMA_VERSION}")
    if data.get("render_only") is not True:
        errors.append("render_only_must_be_true")
    if data.get("original_prompt_executed") is not False:
        errors.append("original_prompt_executed_must_be_false")
    if data.get("rendered_prompt_executed") is not False:
        errors.append("rendered_prompt_executed_must_be_false")
    if data.get("sessions_spawn_allowed") is not False:
        errors.append("sessions_spawn_allowed_must_be_false")
    if data.get("runtime_wiring_allowed") is not False:
        errors.append("runtime_wiring_allowed_must_be_false")
    if data.get("queue_mutation_allowed") is not False:
        errors.append("queue_mutation_allowed_must_be_false")
    if data.get("active_flocky_tool_integration") is not False:
        errors.append("active_flocky_tool_integration_must_be_false")
    if data.get("single_runtime_source_rule_preserved") is not True:
        errors.append("single_runtime_source_rule_preserved_must_be_true")
    if data.get("deterministic_render") is not True:
        errors.append("deterministic_render_must_be_true")
    if data.get("generated_by") != GENERATED_BY:
        errors.append(f"generated_by_must_be:{GENERATED_BY}")

    if not isinstance(data.get("routing_header"), dict):
        errors.append("routing_header_must_be_object")
    if not isinstance(data.get("preflight_report"), dict):
        errors.append("preflight_report_must_be_object")
    if not isinstance(data.get("safe_to_send_to"), list):
        errors.append("safe_to_send_to_must_be_list")
    if not isinstance(data.get("unsafe_to_send_to"), list):
        errors.append("unsafe_to_send_to_must_be_list")
    if not isinstance(data.get("warnings"), list) or not all(isinstance(item, str) for item in data.get("warnings", [])):
        errors.append("warnings_must_be_list_of_strings")
    if not isinstance(data.get("errors"), list) or not all(isinstance(item, str) for item in data.get("errors", [])):
        errors.append("errors_must_be_list_of_strings")

    rendered_prompt = data.get("rendered_prompt", "")
    if not isinstance(rendered_prompt, str) or not rendered_prompt.strip():
        errors.append("rendered_prompt_must_be_non_empty")
    else:
        _scan_forbidden_claims(rendered_prompt, errors)

    routing_header = data.get("routing_header") or {}
    if isinstance(routing_header, dict):
        if routing_header.get("SESSIONS_SPAWN_ALLOWED") != "false":
            errors.append("routing_header_sessions_spawn_allowed_must_be_false")
        if routing_header.get("RUNTIME_MUTATION_ALLOWED") != "false":
            errors.append("routing_header_runtime_mutation_allowed_must_be_false")
        if routing_header.get("QUEUE_MUTATION_ALLOWED") != "false":
            errors.append("routing_header_queue_mutation_allowed_must_be_false")
        if routing_header.get("GOVERNANCE_MUTATION_ALLOWED") != "false":
            errors.append("routing_header_governance_mutation_allowed_must_be_false")
        if routing_header.get("SESSIONS_SPAWN_ALLOWED_FOR_FLOCKY") == "true":
            errors.append("routing_header_sessions_spawn_allowed_for_flocky_must_be_false")

    preflight_report = data.get("preflight_report") or {}
    if isinstance(preflight_report, dict):
        if preflight_report.get("original_prompt_executed") is not False:
            errors.append("preflight_report_original_prompt_executed_must_be_false")

    return {"valid": not errors, "errors": _sorted_unique(errors), "warnings": warnings}


def build_render_report_from_request(request):
    request_validation = validate_render_request(request)
    if not request_validation["valid"]:
        raise ValueError(";".join(request_validation["errors"]))

    template_record = _get_template_record(request["template_name"])
    template_path = PROMPT_PACK_ROOT / "templates" / request["template_name"]
    template_text = template_path.read_text(encoding="utf-8")
    routing_header, rendered_prompt = _render_prompt(request, template_record, template_text)
    preflight_report = build_routing_preflight_report(
        receiver=request["preflight_receiver"],
        prompt_text=rendered_prompt,
        prompt_source=f"rendered:{request['template_name']}",
    )
    report = {
        "type": REPORT_TYPE,
        "schema_version": REQUEST_SCHEMA_VERSION,
        "render_only": True,
        "template_name": request["template_name"],
        "target_agent": request["target_agent"],
        "task_owner": request["task_owner"],
        "task_type": request["task_type"],
        "task_id": request["task_id"],
        "rendered_prompt": rendered_prompt,
        "routing_header": routing_header,
        "preflight_receiver": request["preflight_receiver"],
        "preflight_report": preflight_report,
        "safe_to_send_to": list(template_record["safe_to_send_to"]),
        "unsafe_to_send_to": list(template_record["unsafe_to_send_to"]),
        "original_prompt_executed": False,
        "rendered_prompt_executed": False,
        "sessions_spawn_allowed": False,
        "runtime_wiring_allowed": False,
        "queue_mutation_allowed": False,
        "active_flocky_tool_integration": False,
        "single_runtime_source_rule_preserved": True,
        "warnings": [],
        "errors": [],
        "generated_by": GENERATED_BY,
        "deterministic_render": True,
    }
    validation = validate_render_report(report)
    report["warnings"] = validation["warnings"]
    report["errors"] = validation["errors"]
    return report


def build_render_report_from_request_path(request_path: str):
    return build_render_report_from_request(_load_request(request_path))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render an Autopilot prompt pack request into a ready-to-send prompt and inline preflight report.")
    parser.add_argument("--request-path", required=True)
    parser.add_argument("--out", default="-")
    args = parser.parse_args(argv)
    try:
        report = build_render_report_from_request_path(args.request_path)
        if args.out != "-":
            write_render_report(args.out, report)
        print(json.dumps(report, indent=2))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "invalid", "errors": [str(exc)]}, separators=(",", ":")))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
