import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

TASK_ID = "PMBOT-LLM-012-OPERATOR-REVIEW-ACTUAL-MANUAL-LLM-RESPONSE-SURFACE"
CONTRACT_VERSION = "actual_manual_llm_response_surface_operator_review_contract.v1"
REVIEW_VERSION = "actual_manual_llm_response_surface_operator_review.v1"
GENERATED_AT = "deterministic-actual-manual-llm-response-surface-operator-review.v1"
GENERATED_BY = "pm_bot/llm/evaluate_actual_manual_llm_response_surface_operator_review.py"

DEFAULT_REVIEW_PACK_JSON = "pm_bot/workbench/operator_review_pack.v1.json"
DEFAULT_REVIEW_PACK_MD = "pm_bot/workbench/operator_review_pack.v1.md"
DEFAULT_WORKBENCH_EXPORT_JSON = "pm_bot/workbench/operator_workbench_export_run.v1.json"
DEFAULT_WORKBENCH_EXPORT_MD = "pm_bot/workbench/operator_workbench_export_run.v1.md"
DEFAULT_OUT_JSON = "pm_bot/llm/actual_manual_llm_response_surface_operator_review.v1.json"
DEFAULT_OUT_MD = "pm_bot/llm/actual_manual_llm_response_surface_operator_review.v1.md"
DEFAULT_EXPECTED_JSON = "pm_bot/llm/expected_actual_manual_llm_response_surface_operator_review.v1.json"
DEFAULT_DOC_RESULT_JSON = "docs/PMBOT_LLM_012_RESULT.json"
DEFAULT_DOC_MD = "docs/PMBOT_LLM_012_OPERATOR_REVIEW_ACTUAL_MANUAL_LLM_RESPONSE_SURFACE.md"

EXPECTED_MARKET_ID = "824952"
EXPECTED_RESPONSE_SOURCE_TYPE = "actual_operator_pasted_response"
EXPECTED_STATUSES = {
    "artifact_present": True,
    "run_status": "actual_response_accepted",
    "acceptance_status": "accepted_for_operator_review",
    "response_validation_status": "accepted",
    "manual_review_status": "accepted",
    "quality_gate_status": "quality_passed",
}
EXPECTED_ZERO_COUNTS = {
    "errors_count": 0,
    "warnings_count": 0,
}
REQUIRED_SAFETY_PHRASES = (
    "offline review context only",
    "not a truth source",
    "not trading advice",
    "not execution authority",
)

FALSE_BOUNDARY_KEYS = {
    "autonomous_paper_orders",
    "browser_automation",
    "browser_automation_added",
    "credentials_or_wallet",
    "llm_api",
    "llm_api_calls_added",
    "market_decision_logic",
    "network_api",
    "probability_ev_scoring_or_edge",
    "real_orders_or_live_trading",
    "runtime_integration_added",
    "runtime_wiring",
    "side_recommendations",
    "truth_evaluation",
}
TRUE_BOUNDARY_KEYS = {
    "deterministic",
    "local_file_reads_only",
    "not_execution_authority",
    "not_trading_advice",
    "not_truth_source",
    "offline_review_context_only",
    "surface_only",
}
ALLOWED_BOUNDARY_PHRASES = (
    "offline review context only",
    "not a truth source",
    "not truth",
    "not trading advice",
    "not execution authority",
    "do not execute or automate anything",
)

FORBIDDEN_TOKEN_GROUPS = {
    "recommendation": ("recommend", "recommends", "recommended", "recommendation", "recommendations"),
    "probability": ("probability", "probabilities", "probabilistic"),
    "ev": ("ev",),
    "edge": ("edge",),
    "scoring": ("score", "scores", "scoring"),
    "side_selection": ("side",),
    "buy_sell_hold_enter_exit": ("buy", "sell", "hold", "enter", "exit"),
    "trading_order_wallet_instruction": ("trade", "trading", "order", "orders", "wallet", "signing"),
}
FORBIDDEN_PHRASES = {
    "side_selection": (
        ("side", "selection"),
        ("side", "recommendation"),
        ("side", "recommendations"),
        ("recommended", "side"),
        ("market", "side"),
    ),
    "market_decision": (
        ("market", "decision"),
        ("market", "decisions"),
        ("market", "selection"),
    ),
    "trading_order_wallet_instruction": (
        ("trading", "instruction"),
        ("order", "instruction"),
        ("wallet", "instruction"),
        ("place", "order"),
        ("submit", "order"),
        ("create", "order"),
    ),
}

SAFETY_FLAGS = {
    "offline_local_manual_only": True,
    "local_file_reads_only": True,
    "deterministic": True,
    "llm_api": False,
    "network_api": False,
    "browser_automation": False,
    "prompt_automation": False,
    "runtime_wiring": False,
    "dispatcher_run_codex_changes": False,
    "credentials_or_wallet": False,
    "real_orders_or_live_trading": False,
    "autonomous_paper_orders": False,
    "probability_ev_scoring_or_edge": False,
    "side_recommendations": False,
    "market_decision_logic": False,
    "truth_evaluation": False,
    "execution_authority": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Evaluate the local operator surface for the accepted actual manual LLM response."
    )
    parser.add_argument("--review-pack-json", default=DEFAULT_REVIEW_PACK_JSON)
    parser.add_argument("--review-pack-md", default=DEFAULT_REVIEW_PACK_MD)
    parser.add_argument("--workbench-export-json", default=DEFAULT_WORKBENCH_EXPORT_JSON)
    parser.add_argument("--workbench-export-md", default=DEFAULT_WORKBENCH_EXPORT_MD)
    parser.add_argument("--out-json", default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", default=DEFAULT_OUT_MD)
    parser.add_argument("--expected-json", default=DEFAULT_EXPECTED_JSON)
    parser.add_argument("--doc-result-json", default=DEFAULT_DOC_RESULT_JSON)
    parser.add_argument("--doc-md", default=DEFAULT_DOC_MD)
    return parser.parse_args(argv)


def _resolve_path(path, root=ROOT):
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return Path(root) / candidate


def _display_path(path, root=ROOT):
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(Path(root).resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def _write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_json(path, artifact_id, root=ROOT):
    path = _resolve_path(path, root)
    status = {
        "artifact_id": artifact_id,
        "path": _display_path(path, root),
        "artifact_present": path.exists(),
        "parse_status": "not_loaded",
    }
    if not path.exists():
        status["parse_status"] = "missing"
        return None, status, [
            _error(
                f"{artifact_id}_missing",
                status["path"],
                "Required generated JSON artifact is missing.",
                "artifact_load_check",
            )
        ]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        status["parse_status"] = "parse_failed"
        return None, status, [
            _error(
                f"{artifact_id}_json_malformed",
                status["path"],
                f"JSON parse failed at line {exc.lineno}, column {exc.colno}.",
                "artifact_load_check",
            )
        ]
    except OSError as exc:
        status["parse_status"] = "read_failed"
        return None, status, [
            _error(
                f"{artifact_id}_read_failed",
                status["path"],
                f"JSON artifact could not be read: {exc.__class__.__name__}.",
                "artifact_load_check",
            )
        ]
    if not isinstance(payload, dict):
        status["parse_status"] = "top_level_not_object"
        return None, status, [
            _error(
                f"{artifact_id}_top_level_not_object",
                status["path"],
                "Generated JSON artifact parsed but is not an object.",
                "artifact_load_check",
            )
        ]
    status["parse_status"] = "parsed"
    return payload, status, []


def _load_text(path, artifact_id, root=ROOT):
    path = _resolve_path(path, root)
    status = {
        "artifact_id": artifact_id,
        "path": _display_path(path, root),
        "artifact_present": path.exists(),
        "parse_status": "not_loaded",
    }
    if not path.exists():
        status["parse_status"] = "missing"
        return "", status, [
            _error(
                f"{artifact_id}_missing",
                status["path"],
                "Required generated Markdown artifact is missing.",
                "markdown_readability_check",
            )
        ]
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        status["parse_status"] = "read_failed"
        return "", status, [
            _error(
                f"{artifact_id}_read_failed",
                status["path"],
                f"Markdown artifact could not be read: {exc.__class__.__name__}.",
                "markdown_readability_check",
            )
        ]
    status["parse_status"] = "read"
    return text, status, []


def _error(code, path, message, check):
    return {"code": code, "path": path, "message": message, "check": check}


def _warning(code, path, message, check):
    return {"code": code, "path": path, "message": message, "check": check}


def _check(status_name, errors, warnings=None, **extra):
    warnings = warnings or []
    if errors:
        status = "failed"
    elif warnings:
        status = "warning"
    else:
        status = "passed"
    return {
        "check_name": status_name,
        "status": status,
        **extra,
        "errors": errors,
        "warnings": warnings,
    }


def _surface_from_payload(payload, artifact_id, source_path):
    if not isinstance(payload, dict):
        return None, [
            _error(
                f"{artifact_id}_surface_missing",
                source_path,
                "Generated artifact did not parse to an object with a surface section.",
                "surface_presence_check",
            )
        ]
    surface = payload.get("actual_manual_llm_response_trial")
    if not isinstance(surface, dict):
        return None, [
            _error(
                f"{artifact_id}_surface_missing",
                source_path,
                "actual_manual_llm_response_trial section is missing or not an object.",
                "surface_presence_check",
            )
        ]
    return surface, []


def _is_repo_relative_path(value):
    if not isinstance(value, str) or not value.strip():
        return False
    candidate = value.strip()
    return not (
        Path(candidate).is_absolute()
        or candidate.startswith("/")
        or candidate.startswith("\\")
        or "://" in candidate
        or ":" in Path(candidate).parts[0]
    )


def _status_errors(source_id, surface):
    errors = []
    for field, expected in EXPECTED_STATUSES.items():
        observed = surface.get(field)
        if observed != expected:
            errors.append(
                _error(
                    f"{source_id}_{field}_unexpected",
                    field,
                    f"{field} must be {expected!r}; observed {observed!r}.",
                    "accepted_status_check",
                )
            )
    for field, expected in EXPECTED_ZERO_COUNTS.items():
        observed = surface.get(field)
        if observed != expected:
            errors.append(
                _error(
                    f"{source_id}_{field}_nonzero",
                    field,
                    f"{field} must be {expected}; observed {observed!r}.",
                    "accepted_status_check",
                )
            )
    return errors


def _market_source_errors(source_id, surface):
    errors = []
    if str(surface.get("market_id") or "") != EXPECTED_MARKET_ID:
        errors.append(
            _error(
                f"{source_id}_market_id_unexpected",
                "market_id",
                f"market_id must be {EXPECTED_MARKET_ID}.",
                "market_source_check",
            )
        )
    if surface.get("response_source_type") != EXPECTED_RESPONSE_SOURCE_TYPE:
        errors.append(
            _error(
                f"{source_id}_response_source_type_unexpected",
                "response_source_type",
                f"response_source_type must be {EXPECTED_RESPONSE_SOURCE_TYPE}.",
                "market_source_check",
            )
        )
    pointer_candidates = (
        surface.get("source_artifact_path"),
        surface.get("artifact_pointer"),
        surface.get("artifact_path"),
    )
    if not any(_is_repo_relative_path(candidate) for candidate in pointer_candidates):
        errors.append(
            _error(
                f"{source_id}_source_pointer_missing",
                "source_artifact_path",
                "Surface must include source_artifact_path or an equivalent repo-relative pointer.",
                "market_source_check",
            )
        )
    return errors


def _string_values(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for nested in value.values():
            yield from _string_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _string_values(nested)


def _safety_language_errors(source_id, surface, markdown_sections):
    text = " ".join(_string_values(surface))
    text = " ".join([text, *markdown_sections]).lower()
    errors = []
    for phrase in REQUIRED_SAFETY_PHRASES:
        if phrase not in text:
            errors.append(
                _error(
                    f"{source_id}_safety_phrase_missing_{phrase.replace(' ', '_')}",
                    "explicit_operator_warning",
                    f"Surface must include safety phrase: {phrase}.",
                    "safety_language_check",
                )
            )
    for field in ("offline_review_context_only", "not_truth_source", "not_trading_advice", "not_execution_authority"):
        if surface.get(field) is not True:
            errors.append(
                _error(
                    f"{source_id}_{field}_not_true",
                    field,
                    f"{field} must be true.",
                    "safety_language_check",
                )
            )
    return errors


def _extract_actual_trial_markdown_section(text):
    if not text:
        return ""
    marker = "## Actual Manual LLM Response Trial"
    start = text.find(marker)
    if start == -1:
        return ""
    next_header = text.find("\n## ", start + len(marker))
    if next_header == -1:
        return text[start:]
    return text[start:next_header]


def _markdown_readability_errors(source_id, text):
    errors = []
    section = _extract_actual_trial_markdown_section(text)
    if not section:
        errors.append(
            _error(
                f"{source_id}_actual_trial_markdown_section_missing",
                "actual_manual_llm_response_trial",
                "Markdown must include an Actual Manual LLM Response Trial section.",
                "markdown_readability_check",
            )
        )
        return errors
    required_fragments = (
        "artifact_present: true",
        "response_source_type: actual_operator_pasted_response",
        "market_id: 824952",
        "run_status: actual_response_accepted",
        "acceptance_status: accepted_for_operator_review",
        "response_validation_status: accepted",
        "manual_review_status: accepted",
        "quality_gate_status: quality_passed",
        "errors_count: 0",
        "warnings_count: 0",
        "offline review context only",
        "not trading advice",
        "not execution authority",
    )
    lowered = section.lower()
    for fragment in required_fragments:
        if fragment not in lowered:
            errors.append(
                _error(
                    f"{source_id}_markdown_fragment_missing",
                    "actual_manual_llm_response_trial",
                    f"Markdown section must include {fragment!r}.",
                    "markdown_readability_check",
                )
            )
    return errors


def _tokens(text):
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in str(text))
    return cleaned.split()


def _contains_phrase(tokens, phrase):
    length = len(phrase)
    if length == 0 or len(tokens) < length:
        return False
    return any(tuple(tokens[index : index + length]) == phrase for index in range(len(tokens) - length + 1))


def _allowed_boundary_candidate(path, text, value):
    key = path.split(".")[-1]
    lowered = str(text).strip().lower()
    if key in FALSE_BOUNDARY_KEYS and value is False:
        return True
    if key in TRUE_BOUNDARY_KEYS and value is True:
        return True
    if lowered.startswith("- ") and lowered.endswith(": false"):
        key_text = lowered[2:].split(":", 1)[0].strip()
        if key_text in FALSE_BOUNDARY_KEYS:
            return True
    if lowered.startswith("- ") and lowered.endswith(": true"):
        key_text = lowered[2:].split(":", 1)[0].strip()
        if key_text in TRUE_BOUNDARY_KEYS:
            return True
    return any(phrase in lowered for phrase in ALLOWED_BOUNDARY_PHRASES)


def _forbidden_findings_for_text(source_id, path, text, value=None):
    if _allowed_boundary_candidate(path, text, value):
        return []
    tokens = _tokens(text)
    findings = []
    token_set = set(tokens)
    for code, group in FORBIDDEN_TOKEN_GROUPS.items():
        if token_set.intersection(group):
            findings.append(
                {
                    "code": f"forbidden_surface_text_{code}",
                    "source": source_id,
                    "path": path,
                    "text": str(text),
                }
            )
    for code, phrases in FORBIDDEN_PHRASES.items():
        for phrase in phrases:
            if _contains_phrase(tokens, phrase):
                findings.append(
                    {
                        "code": f"forbidden_surface_phrase_{code}",
                        "source": source_id,
                        "path": path,
                        "text": str(text),
                    }
                )
                break
    return findings


def _surface_forbidden_findings(source_id, value, path="surface"):
    findings = []
    if isinstance(value, dict):
        for key, nested in value.items():
            nested_path = f"{path}.{key}"
            if _allowed_boundary_candidate(nested_path, key, nested):
                continue
            findings.extend(_forbidden_findings_for_text(source_id, nested_path, key, nested))
            findings.extend(_surface_forbidden_findings(source_id, nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            findings.extend(_surface_forbidden_findings(source_id, nested, f"{path}[{index}]"))
    elif isinstance(value, str):
        findings.extend(_forbidden_findings_for_text(source_id, path, value, value))
    return findings


def _markdown_forbidden_findings(source_id, text):
    section = _extract_actual_trial_markdown_section(text)
    findings = []
    for index, line in enumerate(section.splitlines(), start=1):
        if not line.strip():
            continue
        findings.extend(
            _forbidden_findings_for_text(source_id, f"markdown_line_{index}", line, line)
        )
    return findings


def _forbidden_errors(findings):
    errors = []
    for finding in findings:
        errors.append(
            _error(
                finding["code"],
                f"{finding['source']}:{finding['path']}",
                "Surface contains forbidden operator behavior language.",
                "forbidden_behavior_check",
            )
        )
    return errors


def _surface_snapshot(surface):
    fields = (
        "artifact_present",
        "run_status",
        "acceptance_status",
        "response_validation_status",
        "manual_review_status",
        "quality_gate_status",
        "market_id",
        "response_source_type",
        "source_artifact_path",
        "artifact_path",
        "artifact_pointer",
        "errors_count",
        "warnings_count",
    )
    return {field: surface.get(field) for field in fields if field in surface}


def _review_status(errors, warnings):
    if errors:
        return "operator_surface_review_failed"
    if warnings:
        return "operator_surface_review_passed_with_warnings"
    return "operator_surface_review_passed"


def _operator_summary(status):
    if status == "operator_surface_review_passed":
        return (
            "Operator surface review passed: the generated workbench artifacts expose the accepted actual "
            "operator-pasted response with clear offline-only safety boundaries."
        )
    if status == "operator_surface_review_passed_with_warnings":
        return (
            "Operator surface review passed with warnings: the accepted response surface is usable, but the "
            "listed warnings should be reviewed before relying on the surface as local context."
        )
    return (
        "Operator surface review failed: the generated workbench artifacts need operator attention before "
        "this actual manual LLM response surface is treated as accepted local review context."
    )


def _count_checks(checks):
    statuses = [check["status"] for check in checks.values()]
    return {
        "checks_total": len(statuses),
        "checks_passed": statuses.count("passed"),
        "checks_with_warnings": statuses.count("warning"),
        "checks_failed": statuses.count("failed"),
    }


def evaluate_operator_surface_review(
    root=ROOT,
    review_pack_json=DEFAULT_REVIEW_PACK_JSON,
    review_pack_md=DEFAULT_REVIEW_PACK_MD,
    workbench_export_json=DEFAULT_WORKBENCH_EXPORT_JSON,
    workbench_export_md=DEFAULT_WORKBENCH_EXPORT_MD,
):
    root = Path(root)
    pack_payload, pack_status, pack_errors = _load_json(review_pack_json, "operator_review_pack_json", root)
    export_payload, export_status, export_errors = _load_json(
        workbench_export_json,
        "operator_workbench_export_json",
        root,
    )
    pack_md, pack_md_status, pack_md_errors = _load_text(review_pack_md, "operator_review_pack_markdown", root)
    export_md, export_md_status, export_md_errors = _load_text(
        workbench_export_md,
        "operator_workbench_export_markdown",
        root,
    )

    pack_surface, pack_surface_errors = _surface_from_payload(
        pack_payload,
        "operator_review_pack_json",
        pack_status["path"],
    )
    export_surface, export_surface_errors = _surface_from_payload(
        export_payload,
        "operator_workbench_export_json",
        export_status["path"],
    )

    surfaces = {
        "operator_review_pack": pack_surface or {},
        "operator_workbench_export": export_surface or {},
    }
    artifact_errors = pack_errors + export_errors + pack_md_errors + export_md_errors
    presence_errors = pack_surface_errors + export_surface_errors

    status_errors = []
    market_errors = []
    safety_errors = []
    markdown_errors = []
    forbidden_findings = []

    markdown_sections = {
        "operator_review_pack": _extract_actual_trial_markdown_section(pack_md),
        "operator_workbench_export": _extract_actual_trial_markdown_section(export_md),
    }
    for source_id, surface in surfaces.items():
        if not surface:
            continue
        status_errors.extend(_status_errors(source_id, surface))
        market_errors.extend(_market_source_errors(source_id, surface))
        safety_errors.extend(
            _safety_language_errors(source_id, surface, [markdown_sections[source_id]])
        )
        forbidden_findings.extend(_surface_forbidden_findings(source_id, surface))
    markdown_errors.extend(_markdown_readability_errors("operator_review_pack", pack_md))
    markdown_errors.extend(_markdown_readability_errors("operator_workbench_export", export_md))
    forbidden_findings.extend(_markdown_forbidden_findings("operator_review_pack", pack_md))
    forbidden_findings.extend(_markdown_forbidden_findings("operator_workbench_export", export_md))

    forbidden_errors = _forbidden_errors(forbidden_findings)
    checks = {
        "artifact_load_check": _check(
            "artifact_load_check",
            artifact_errors,
            observed_artifacts=[pack_status, export_status, pack_md_status, export_md_status],
        ),
        "surface_presence_check": _check("surface_presence_check", presence_errors),
        "accepted_status_check": _check("accepted_status_check", status_errors),
        "market_source_check": _check("market_source_check", market_errors),
        "safety_language_check": _check("safety_language_check", safety_errors),
        "markdown_readability_check": _check("markdown_readability_check", markdown_errors),
        "forbidden_behavior_check": _check(
            "forbidden_behavior_check",
            forbidden_errors,
            forbidden_findings=forbidden_findings,
        ),
    }
    errors = []
    warnings = []
    for check in checks.values():
        errors.extend(check["errors"])
        warnings.extend(check["warnings"])
    errors = sorted(errors, key=lambda item: (item["check"], item["path"], item["code"], item["message"]))
    warnings = sorted(warnings, key=lambda item: (item["check"], item["path"], item["code"], item["message"]))
    status = _review_status(errors, warnings)
    check_counts = _count_checks(checks)
    return {
        "contract_version": CONTRACT_VERSION,
        "review_version": REVIEW_VERSION,
        "task_id": TASK_ID,
        "generated_at": GENERATED_AT,
        "generated_by": GENERATED_BY,
        "operator_surface_review_status": status,
        "review_counts": {
            **check_counts,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
        },
        "source_artifacts": {
            "operator_review_pack_json": pack_status["path"],
            "operator_review_pack_markdown": pack_md_status["path"],
            "operator_workbench_export_json": export_status["path"],
            "operator_workbench_export_markdown": export_md_status["path"],
        },
        "surface_snapshots": {
            source_id: _surface_snapshot(surface) for source_id, surface in surfaces.items()
        },
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "safety_flags": dict(SAFETY_FLAGS),
        "operator_summary": _operator_summary(status),
        "next_safe_operator_action": (
            "Review the generated Markdown acceptance result and source workbench Markdown as "
            "offline local context only; do not execute or automate anything."
        ),
    }


def render_markdown(result):
    lines = [
        "# PMBOT LLM 012 Operator Surface Review",
        "",
        f"- task_id: {result['task_id']}",
        f"- operator_surface_review_status: {result['operator_surface_review_status']}",
        f"- errors_count: {result['review_counts']['errors_count']}",
        f"- warnings_count: {result['review_counts']['warnings_count']}",
        f"- operator_summary: {result['operator_summary']}",
        "",
        "## Source Artifacts",
        "",
    ]
    for key, value in result["source_artifacts"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Accepted Surface Status", ""])
    for source_id, snapshot in result["surface_snapshots"].items():
        lines.append(f"- {source_id}:")
        for field in (
            "artifact_present",
            "market_id",
            "response_source_type",
            "source_artifact_path",
            "run_status",
            "acceptance_status",
            "response_validation_status",
            "manual_review_status",
            "quality_gate_status",
            "errors_count",
            "warnings_count",
        ):
            if field in snapshot:
                lines.append(f"  - {field}: {snapshot[field]}")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- This review is offline review context only.",
            "- It is not a truth source.",
            "- It is not trading advice.",
            "- It is not execution authority.",
            "",
            "## Check Status",
            "",
        ]
    )
    for check in result["checks"].values():
        lines.append(f"- {check['check_name']}: {check['status']}")
    lines.extend(["", "## Errors", ""])
    if result["errors"]:
        for item in result["errors"]:
            lines.append(f"- {item['check']}: {item['path']}: {item['code']} - {item['message']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if result["warnings"]:
        for item in result["warnings"]:
            lines.append(f"- {item['check']}: {item['path']}: {item['code']} - {item['message']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Safety Flags", ""])
    for key in sorted(result["safety_flags"]):
        lines.append(f"- {key}: {str(result['safety_flags'][key]).lower()}")
    lines.extend(["", f"- next_safe_operator_action: {result['next_safe_operator_action']}", ""])
    return "\n".join(lines)


def build_doc_result(result):
    completed = result["operator_surface_review_status"] != "operator_surface_review_failed"
    return {
        "task_id": TASK_ID,
        "status": "completed_ready_for_review" if completed else "needs_operator_attention",
        "operator_surface_review_status": result["operator_surface_review_status"],
        "surface_review_artifact": DEFAULT_OUT_JSON,
        "surface_review_markdown": DEFAULT_OUT_MD,
        "doc_markdown": DEFAULT_DOC_MD,
        "source_artifacts": result["source_artifacts"],
        "review_counts": result["review_counts"],
        "safety_flags": dict(SAFETY_FLAGS),
        "warnings": result["warnings"],
        "blockers": result["errors"],
        "network_calls": 0,
        "llm_api_calls": 0,
        "browser_automation": False,
        "runtime_wiring": False,
        "orders_created": 0,
        "truth_inference": False,
        "next_recommended_task": "PMBOT-LLM-013-NEXT-MANUAL-ONLY-OPERATOR-REVIEW-STEP",
    }


def export_operator_surface_review(
    root=ROOT,
    review_pack_json=DEFAULT_REVIEW_PACK_JSON,
    review_pack_md=DEFAULT_REVIEW_PACK_MD,
    workbench_export_json=DEFAULT_WORKBENCH_EXPORT_JSON,
    workbench_export_md=DEFAULT_WORKBENCH_EXPORT_MD,
    out_json=DEFAULT_OUT_JSON,
    out_md=DEFAULT_OUT_MD,
    expected_json=DEFAULT_EXPECTED_JSON,
    doc_result_json=DEFAULT_DOC_RESULT_JSON,
    doc_md=DEFAULT_DOC_MD,
):
    result = evaluate_operator_surface_review(
        root=root,
        review_pack_json=review_pack_json,
        review_pack_md=review_pack_md,
        workbench_export_json=workbench_export_json,
        workbench_export_md=workbench_export_md,
    )
    markdown = render_markdown(result)
    doc_result = build_doc_result(result)
    _write_json(_resolve_path(out_json, root), result)
    _write_text(_resolve_path(out_md, root), markdown)
    _write_json(_resolve_path(expected_json, root), result)
    _write_json(_resolve_path(doc_result_json, root), doc_result)
    _write_text(_resolve_path(doc_md, root), markdown)
    return result


def main(argv):
    args = _parse_args(argv)
    result = export_operator_surface_review(
        review_pack_json=args.review_pack_json,
        review_pack_md=args.review_pack_md,
        workbench_export_json=args.workbench_export_json,
        workbench_export_md=args.workbench_export_md,
        out_json=args.out_json,
        out_md=args.out_md,
        expected_json=args.expected_json,
        doc_result_json=args.doc_result_json,
        doc_md=args.doc_md,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["operator_surface_review_status"] != "operator_surface_review_failed" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
