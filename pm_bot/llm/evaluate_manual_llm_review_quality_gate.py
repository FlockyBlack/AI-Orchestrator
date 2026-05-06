import argparse
import json
import re
import sys
from json import JSONDecodeError
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import validate_llm_analysis_artifacts as validator  # noqa: E402


CONTRACT_VERSION = "manual_llm_review_quality_gate_contract.v1"
QUALITY_GATE_VERSION = "manual_llm_review_quality_gate.v1"
DETERMINISTIC_GENERATED_AT = "deterministic-manual-llm-review-quality-gate.v1"

DEFAULT_PACKET_PATH = validator.DEFAULT_PACKET_PATH
DEFAULT_RESPONSE_PATH = validator.LLM_DIR / "manual_llm_paste_in_response_example_valid.v1.json"
DEFAULT_MANUAL_REVIEW_PATH = validator.LLM_DIR / "manual_llm_paste_in_review.v1.json"
DEFAULT_OUT_JSON_PATH = validator.LLM_DIR / "manual_llm_review_quality_gate.v1.json"
DEFAULT_OUT_MD_PATH = validator.LLM_DIR / "manual_llm_review_quality_gate.v1.md"

REQUIRED_SECTIONS = tuple(validator.ALLOWED_RESPONSE_SECTIONS)

MINIMUM_USEFUL_ITEMS = {
    "key_uncertainties": 2,
    "missing_evidence": 1,
    "risk_notes": 2,
    "operator_review_checklist": 3,
    "suggested_research_questions": 2,
}

PLACEHOLDER_EXACT_TEXT = {
    "",
    "n/a",
    "na",
    "none",
    "not applicable",
    "no issues",
    "looks good",
    "safe to proceed",
    "cannot determine",
}

GENERIC_PHRASES = (
    "n/a",
    "not applicable",
    "no issues",
    "looks good",
    "safe to proceed",
)

UNCERTAINTY_MARKERS = (
    "uncertain",
    "uncertainty",
    "unknown",
    "not ",
    "not_",
    "may ",
    "might ",
    "could ",
    "unresolved",
    "needs",
    "has not",
    "have not",
    "requires",
)

MISSING_EVIDENCE_MARKERS = (
    "missing",
    "evidence",
    "unconfirmed",
    "confirmation",
    "source",
    "artifact",
    "gap",
    "needs",
    "not ",
)

RISK_MARKERS = (
    "risk",
    "stale",
    "unresolved",
    "manual",
    "offline",
    "review aid",
    "unsupported",
    "contradict",
    "caution",
)

CHECKLIST_ACTION_MARKERS = (
    "open",
    "compare",
    "mark",
    "verify",
    "check",
    "review",
    "confirm",
    "record",
    "inspect",
)

SOURCE_GAP_MARKERS = (
    "source",
    "citation",
    "gap",
    "artifact",
    "path",
    "local",
    "live",
    "confirmation",
    "outside",
)

UNSAFE_CERTAINTY_PATTERNS = (
    ("unsafe_certainty:guaranteed", "guaranteed", re.compile(r"\bguaranteed\b", re.IGNORECASE)),
    ("unsafe_certainty:certain_outcome", "certain outcome", re.compile(r"\bcertain\s+outcome\b", re.IGNORECASE)),
    ("unsafe_certainty:will_definitely", "will definitely", re.compile(r"\bwill\s+definitely\b", re.IGNORECASE)),
    ("unsafe_certainty:lock", "lock", re.compile(r"\block\b", re.IGNORECASE)),
    ("unsafe_certainty:sure_bet", "sure bet", re.compile(r"\bsure\s+bet\b", re.IGNORECASE)),
    ("unsafe_certainty:cannot_lose", "cannot lose", re.compile(r"\bcannot\s+lose\b", re.IGNORECASE)),
    ("unsafe_certainty:risk_free", "risk-free", re.compile(r"\brisk[-\s]+free\b", re.IGNORECASE)),
    ("unsafe_certainty:obvious_winner", "obvious winner", re.compile(r"\bobvious\s+winner\b", re.IGNORECASE)),
)

SAFETY_FLAGS = {
    **validator.SAFETY_FLAGS,
    "browser_automation": False,
    "market_decision_logic": False,
    "truth_evaluation": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Evaluate manual LLM paste-in response quality after PMBOT-LLM-001 validation."
    )
    parser.add_argument("--packet", default=str(DEFAULT_PACKET_PATH.relative_to(ROOT)))
    parser.add_argument("--response", default=str(DEFAULT_RESPONSE_PATH.relative_to(ROOT)))
    parser.add_argument("--manual-review", default=str(DEFAULT_MANUAL_REVIEW_PATH.relative_to(ROOT)))
    parser.add_argument("--out-json", default=str(DEFAULT_OUT_JSON_PATH.relative_to(ROOT)))
    parser.add_argument("--out-md", default=str(DEFAULT_OUT_MD_PATH.relative_to(ROOT)))
    return parser.parse_args(argv)


def _resolve_path(path):
    if path is None:
        return None
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return ROOT / candidate


def _display_path(path):
    if path is None:
        return ""
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


def _load_optional_manual_review(path):
    if path is None:
        return {
            "status": "not_provided",
            "path": "",
            "validation_status": "not_available",
            "warnings": [],
        }
    if not Path(path).exists():
        return {
            "status": "not_available",
            "path": _display_path(path),
            "validation_status": "not_available",
            "warnings": [
                {
                    "code": "manual_review_not_available",
                    "path": _display_path(path),
                    "message": "Optional PMBOT-LLM-003 manual review artifact was not found.",
                }
            ],
        }
    payload, errors = _load_json_artifact(path, "manual_review")
    if errors:
        return {
            "status": "unreadable",
            "path": _display_path(path),
            "validation_status": "not_available",
            "warnings": [
                {
                    "code": error["code"],
                    "path": error["path"],
                    "message": error["message"],
                }
                for error in errors
            ],
        }
    return {
        "status": "loaded",
        "path": _display_path(path),
        "validation_status": payload.get("validation_status", "unknown") if isinstance(payload, dict) else "unknown",
        "warnings": [],
    }


def _base_validation_from_load_errors(errors):
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


def _aggregate_base_messages(packet_validation, response_validation):
    errors = []
    warnings = []
    for error in packet_validation["errors"]:
        errors.append({**error, "artifact": "packet", "check": "base_validator"})
    for error in response_validation["errors"]:
        errors.append({**error, "artifact": "response", "check": "base_validator"})
    for warning in packet_validation["warnings"]:
        warnings.append({**warning, "artifact": "packet", "check": "base_validator"})
    for warning in response_validation["warnings"]:
        warnings.append({**warning, "artifact": "response", "check": "base_validator"})
    errors = sorted(errors, key=lambda item: (item["artifact"], item["path"], item["code"], item["message"]))
    warnings = sorted(warnings, key=lambda item: (item["artifact"], item["path"], item["code"], item["message"]))
    return errors, warnings


def _error(code, path, message, check):
    return {"code": code, "path": path, "message": message, "check": check}


def _warning(code, path, message, check):
    return {"code": code, "path": path, "message": message, "check": check}


def _text_fragments(value, prefix=""):
    if isinstance(value, str):
        yield prefix, value
    elif isinstance(value, dict):
        for key, nested in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield from _text_fragments(nested, path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            yield from _text_fragments(item, path)


def _item_text(value):
    if isinstance(value, str):
        return value
    return " ".join(text for _path, text in _text_fragments(value))


def _word_count(text):
    return len(re.findall(r"[A-Za-z0-9]+", text))


def _normalize_placeholder_text(text):
    cleaned = re.sub(r"\s+", " ", str(text).strip().lower())
    cleaned = re.sub(r"[^a-z0-9/\s-]+", "", cleaned)
    cleaned = cleaned.replace("-", " ")
    return re.sub(r"\s+", " ", cleaned).strip()


def _is_placeholder_text(text):
    normalized = _normalize_placeholder_text(text)
    if normalized in PLACEHOLDER_EXACT_TEXT:
        return True
    if normalized.replace("/", "") == "na":
        return True
    return False


def _is_generic_text(text):
    lowered = str(text).strip().lower()
    if _is_placeholder_text(text):
        return True
    return any(phrase in lowered for phrase in GENERIC_PHRASES) and _word_count(lowered) <= 6


def _is_useful_item(item):
    text = _item_text(item).strip()
    return bool(text) and not _is_placeholder_text(text) and _word_count(text) >= 3


def _usable_item_count(value):
    if not isinstance(value, list):
        return 0
    return sum(1 for item in value if _is_useful_item(item))


def _has_marker(text, markers):
    lowered = f" {str(text).lower()} "
    return any(marker in lowered for marker in markers)


def _check_status(errors, warnings):
    if errors:
        return "failed"
    if warnings:
        return "warning"
    return "passed"


def _build_check(name, errors, warnings, **fields):
    return {
        "check_name": name,
        "status": _check_status(errors, warnings),
        **fields,
        "errors": errors,
        "warnings": warnings,
    }


def _required_sections_check(response_payload):
    present = []
    missing = []
    empty = []
    if isinstance(response_payload, dict):
        for section in REQUIRED_SECTIONS:
            if section not in response_payload:
                missing.append(section)
                continue
            present.append(section)
            value = response_payload[section]
            if isinstance(value, str) and not value.strip():
                empty.append(section)
            elif isinstance(value, list) and not value:
                empty.append(section)
            elif isinstance(value, dict) and not value:
                empty.append(section)
    else:
        missing = list(REQUIRED_SECTIONS)

    errors = []
    for section in missing:
        errors.append(
            _error(
                "required_section_missing",
                section,
                f"Required response section {section} is missing.",
                "required_sections_check",
            )
        )
    for section in empty:
        errors.append(
            _error(
                "required_section_empty",
                section,
                f"Required response section {section} is empty.",
                "required_sections_check",
            )
        )
    return _build_check(
        "required_sections_check",
        errors,
        [],
        required_sections=list(REQUIRED_SECTIONS),
        present_sections=present,
        missing_sections=missing,
        empty_sections=empty,
    )


def _minimum_content_check(response_payload):
    errors = []
    observed_counts = {}
    if not isinstance(response_payload, dict):
        response_payload = {}
    for section, minimum in MINIMUM_USEFUL_ITEMS.items():
        observed = _usable_item_count(response_payload.get(section))
        observed_counts[section] = observed
        if observed < minimum:
            errors.append(
                _error(
                    "minimum_useful_content_not_met",
                    section,
                    f"{section} requires at least {minimum} useful item(s); observed {observed}.",
                    "minimum_content_check",
                )
            )
    return _build_check(
        "minimum_content_check",
        errors,
        [],
        required_minimum_useful_items=dict(MINIMUM_USEFUL_ITEMS),
        observed_useful_items=observed_counts,
    )


def _generic_or_placeholder_text_check(response_payload):
    errors = []
    warnings = []
    placeholder_findings = []
    repeated_cannot_determine = []
    if not isinstance(response_payload, dict):
        response_payload = {}

    for section in REQUIRED_SECTIONS:
        value = response_payload.get(section)
        if isinstance(value, list):
            item_placeholder_paths = []
            for index, item in enumerate(value):
                text = _item_text(item)
                path = f"{section}[{index}]"
                if _is_placeholder_text(text):
                    item_placeholder_paths.append(path)
                    placeholder_findings.append({"path": path, "text": text})
                    errors.append(
                        _error(
                            "placeholder_text_found",
                            path,
                            f"{path} is placeholder-only text.",
                            "generic_or_placeholder_text_check",
                        )
                    )
                elif _is_generic_text(text):
                    placeholder_findings.append({"path": path, "text": text})
                    warnings.append(
                        _warning(
                            "generic_text_found",
                            path,
                            f"{path} contains generic text that may not help the operator.",
                            "generic_or_placeholder_text_check",
                        )
                    )
                normalized = _normalize_placeholder_text(text)
                if normalized.startswith("cannot determine") and _word_count(normalized) <= 4:
                    repeated_cannot_determine.append(path)
            if value and len(item_placeholder_paths) == len(value):
                errors.append(
                    _error(
                        "placeholder_only_array",
                        section,
                        f"{section} contains only placeholder items.",
                        "generic_or_placeholder_text_check",
                    )
                )
        elif isinstance(value, str):
            if _is_placeholder_text(value):
                placeholder_findings.append({"path": section, "text": value})
                errors.append(
                    _error(
                        "placeholder_text_found",
                        section,
                        f"{section} is placeholder-only text.",
                        "generic_or_placeholder_text_check",
                    )
                )
            elif _is_generic_text(value):
                placeholder_findings.append({"path": section, "text": value})
                warnings.append(
                    _warning(
                        "generic_text_found",
                        section,
                        f"{section} contains generic text that may not help the operator.",
                        "generic_or_placeholder_text_check",
                    )
                )

    if len(repeated_cannot_determine) >= 2:
        errors.append(
            _error(
                "repeated_cannot_determine_without_detail",
                "response",
                "The response repeats cannot-determine placeholders without detail.",
                "generic_or_placeholder_text_check",
            )
        )

    return _build_check(
        "generic_or_placeholder_text_check",
        errors,
        warnings,
        placeholder_findings=placeholder_findings,
        repeated_cannot_determine_paths=repeated_cannot_determine,
    )


def _uncertainty_check(response_payload):
    errors = []
    warnings = []
    items = response_payload.get("key_uncertainties") if isinstance(response_payload, dict) else None
    useful_items = []
    unmarked_paths = []
    if isinstance(items, list):
        for index, item in enumerate(items):
            text = _item_text(item)
            if _is_useful_item(item):
                useful_items.append(text)
                if not _has_marker(text, UNCERTAINTY_MARKERS):
                    unmarked_paths.append(f"key_uncertainties[{index}]")
    if len(useful_items) < MINIMUM_USEFUL_ITEMS["key_uncertainties"]:
        errors.append(
            _error(
                "uncertainty_items_insufficient",
                "key_uncertainties",
                "key_uncertainties must include at least two useful uncertainty notes.",
                "uncertainty_check",
            )
        )
    if useful_items and len(unmarked_paths) == len(useful_items):
        errors.append(
            _error(
                "uncertainty_markers_absent",
                "key_uncertainties",
                "key_uncertainties must explicitly mark uncertainty instead of sounding settled.",
                "uncertainty_check",
            )
        )
    elif unmarked_paths:
        warnings.append(
            _warning(
                "some_uncertainty_items_not_explicitly_marked",
                "key_uncertainties",
                "Some uncertainty items do not include explicit uncertainty markers.",
                "uncertainty_check",
            )
        )
    return _build_check(
        "uncertainty_check",
        errors,
        warnings,
        useful_items_count=len(useful_items),
        unmarked_uncertainty_paths=unmarked_paths,
    )


def _missing_evidence_check(response_payload):
    errors = []
    warnings = []
    items = response_payload.get("missing_evidence") if isinstance(response_payload, dict) else None
    useful_items = []
    marker_paths = []
    if isinstance(items, list):
        for index, item in enumerate(items):
            text = _item_text(item)
            if _is_useful_item(item):
                useful_items.append(text)
                if _has_marker(text, MISSING_EVIDENCE_MARKERS):
                    marker_paths.append(f"missing_evidence[{index}]")
    if not useful_items:
        errors.append(
            _error(
                "missing_evidence_items_absent",
                "missing_evidence",
                "missing_evidence must include at least one useful missing-evidence note.",
                "missing_evidence_check",
            )
        )
    if useful_items and not marker_paths:
        warnings.append(
            _warning(
                "missing_evidence_markers_absent",
                "missing_evidence",
                "missing_evidence is present but does not clearly mention evidence, source, or confirmation gaps.",
                "missing_evidence_check",
            )
        )
    return _build_check(
        "missing_evidence_check",
        errors,
        warnings,
        useful_items_count=len(useful_items),
        evidence_gap_marker_paths=marker_paths,
    )


def _risk_notes_check(response_payload):
    errors = []
    warnings = []
    items = response_payload.get("risk_notes") if isinstance(response_payload, dict) else None
    useful_items = []
    marker_paths = []
    if isinstance(items, list):
        for index, item in enumerate(items):
            text = _item_text(item)
            if _is_useful_item(item):
                useful_items.append(text)
                if _has_marker(text, RISK_MARKERS):
                    marker_paths.append(f"risk_notes[{index}]")
    if len(useful_items) < MINIMUM_USEFUL_ITEMS["risk_notes"]:
        errors.append(
            _error(
                "risk_notes_insufficient",
                "risk_notes",
                "risk_notes must include at least two useful notes.",
                "risk_notes_check",
            )
        )
    if useful_items and not marker_paths:
        warnings.append(
            _warning(
                "risk_note_markers_absent",
                "risk_notes",
                "risk_notes is present but does not clearly mark review risk or caution.",
                "risk_notes_check",
            )
        )
    return _build_check(
        "risk_notes_check",
        errors,
        warnings,
        useful_items_count=len(useful_items),
        risk_marker_paths=marker_paths,
    )


def _operator_checklist_check(response_payload):
    errors = []
    warnings = []
    items = response_payload.get("operator_review_checklist") if isinstance(response_payload, dict) else None
    useful_items = []
    action_paths = []
    if isinstance(items, list):
        for index, item in enumerate(items):
            text = _item_text(item)
            if _is_useful_item(item):
                useful_items.append(text)
                if _has_marker(text, CHECKLIST_ACTION_MARKERS):
                    action_paths.append(f"operator_review_checklist[{index}]")
    if len(useful_items) < MINIMUM_USEFUL_ITEMS["operator_review_checklist"]:
        errors.append(
            _error(
                "operator_checklist_insufficient",
                "operator_review_checklist",
                "operator_review_checklist must include at least three useful action items.",
                "operator_checklist_check",
            )
        )
    if useful_items and not action_paths:
        warnings.append(
            _warning(
                "operator_checklist_action_markers_absent",
                "operator_review_checklist",
                "operator checklist items should be concrete manual actions.",
                "operator_checklist_check",
            )
        )
    return _build_check(
        "operator_checklist_check",
        errors,
        warnings,
        useful_items_count=len(useful_items),
        action_marker_paths=action_paths,
    )


def _source_gap_notes_check(response_payload):
    errors = []
    warnings = []
    items = response_payload.get("citation_or_source_gap_notes") if isinstance(response_payload, dict) else None
    useful_items = []
    marker_paths = []
    if isinstance(items, list):
        for index, item in enumerate(items):
            text = _item_text(item)
            if _is_useful_item(item):
                useful_items.append(text)
                if _has_marker(text, SOURCE_GAP_MARKERS):
                    marker_paths.append(f"citation_or_source_gap_notes[{index}]")
    if not useful_items:
        errors.append(
            _error(
                "source_gap_notes_absent",
                "citation_or_source_gap_notes",
                "citation_or_source_gap_notes must include at least one useful source-gap note.",
                "source_gap_notes_check",
            )
        )
    if useful_items and not marker_paths:
        warnings.append(
            _warning(
                "source_gap_markers_absent",
                "citation_or_source_gap_notes",
                "citation_or_source_gap_notes is present but does not clearly mention source, citation, artifact, or gap context.",
                "source_gap_notes_check",
            )
        )
    return _build_check(
        "source_gap_notes_check",
        errors,
        warnings,
        useful_items_count=len(useful_items),
        source_gap_marker_paths=marker_paths,
    )


def _safety_acknowledgement_check(response_payload):
    errors = []
    acknowledgement = response_payload.get("safety_acknowledgement") if isinstance(response_payload, dict) else None
    required_true_fields = (
        "offline_only",
        "local_only",
        "manual_review_only",
        "no_recommendations",
        "no_outcome_estimates",
        "no_value_scoring",
        "no_trade_or_wallet_instructions",
        "no_autonomous_actions",
        "uncertain_claims_marked",
    )
    field_status = {}
    if not isinstance(acknowledgement, dict):
        acknowledgement = {}
    for field in required_true_fields:
        field_status[field] = acknowledgement.get(field) is True
        if not field_status[field]:
            errors.append(
                _error(
                    "safety_acknowledgement_missing_or_false",
                    f"safety_acknowledgement.{field}",
                    f"safety_acknowledgement.{field} must be true.",
                    "safety_acknowledgement_check",
                )
            )
    concept_status = {
        "analysis_only": field_status["offline_only"]
        and field_status["local_only"]
        and field_status["manual_review_only"],
        "not_trading_advice": field_status["no_recommendations"]
        and field_status["no_trade_or_wallet_instructions"]
        and field_status["no_autonomous_actions"],
        "no_estimates_value_metrics_or_directional_guidance": field_status["no_outcome_estimates"]
        and field_status["no_value_scoring"]
        and field_status["no_recommendations"],
    }
    for concept, passed in concept_status.items():
        if not passed:
            errors.append(
                _error(
                    "safety_acknowledgement_concept_missing",
                    f"safety_acknowledgement.{concept}",
                    f"Safety acknowledgement does not satisfy {concept}.",
                    "safety_acknowledgement_check",
                )
            )
    return _build_check(
        "safety_acknowledgement_check",
        errors,
        [],
        required_true_fields=list(required_true_fields),
        field_status=field_status,
        concept_status=concept_status,
    )


def _unsafe_certainty_check(response_payload, base_errors):
    errors = []
    findings = []
    for path, text in _text_fragments(response_payload):
        for code, display, pattern in UNSAFE_CERTAINTY_PATTERNS:
            if pattern.search(text):
                finding = {
                    "code": code,
                    "path": path,
                    "message": f"Unsafe certainty language found: {display}.",
                    "check": "unsafe_certainty_check",
                }
                findings.append(finding)
                errors.append(finding)

    for error in base_errors:
        if error["code"].startswith("forbidden_certainty"):
            finding = {
                "code": error["code"],
                "path": error["path"],
                "message": error["message"],
                "check": "unsafe_certainty_check",
                "artifact": error.get("artifact", "response"),
            }
            if finding not in findings:
                findings.append(finding)
                errors.append(finding)

    findings = sorted(findings, key=lambda item: (item["path"], item["code"], item["message"]))
    errors = sorted(errors, key=lambda item: (item["path"], item["code"], item["message"]))
    return _build_check(
        "unsafe_certainty_check",
        errors,
        [],
        unsafe_certainty_detected=bool(findings),
        findings=findings,
    )


def _forbidden_content_check(base_errors):
    forbidden_prefixes = (
        "forbidden_packet_field",
        "forbidden_response_field",
        "forbidden_phrase",
        "forbidden_certainty",
        "missing_required_forbidden_output",
    )
    findings = [
        error
        for error in base_errors
        if any(error["code"].startswith(prefix) for prefix in forbidden_prefixes)
    ]
    errors = [
        _error(
            "forbidden_content_detected",
            finding["path"],
            f"Base validator reported forbidden content: {finding['code']}.",
            "forbidden_content_check",
        )
        for finding in findings
    ]
    return _build_check(
        "forbidden_content_check",
        errors,
        [],
        forbidden_content_detected=bool(findings),
        findings=findings,
    )


def _all_quality_checks(response_payload, base_errors):
    checks = [
        _required_sections_check(response_payload),
        _minimum_content_check(response_payload),
        _generic_or_placeholder_text_check(response_payload),
        _uncertainty_check(response_payload),
        _missing_evidence_check(response_payload),
        _risk_notes_check(response_payload),
        _operator_checklist_check(response_payload),
        _source_gap_notes_check(response_payload),
        _safety_acknowledgement_check(response_payload),
        _unsafe_certainty_check(response_payload, base_errors),
        _forbidden_content_check(base_errors),
    ]
    return {check["check_name"]: check for check in checks}


def _quality_counts(checks, errors, warnings):
    statuses = [check["status"] for check in checks.values()]
    return {
        "checks_total": len(statuses),
        "checks_passed": statuses.count("passed"),
        "checks_with_warnings": statuses.count("warning"),
        "checks_failed": statuses.count("failed"),
        "errors_count": len(errors),
        "warnings_count": len(warnings),
    }


def _operator_summary(status, base_status):
    if status == "quality_passed":
        return (
            "Quality passed: the response passed PMBOT-LLM-001 validation and deterministic operator-usefulness "
            "checks. Treat it only as offline manual review context."
        )
    if status == "quality_passed_with_warnings":
        return (
            "Quality passed with warnings: the response passed PMBOT-LLM-001 validation and has no forbidden "
            "content, but the operator should review the listed quality warnings before relying on it as context."
        )
    if base_status != "accepted":
        return (
            "Quality failed: the packet or response failed PMBOT-LLM-001 validation. Do not accept this manual "
            "review response until the local artifact is corrected and revalidated."
        )
    return (
        "Quality failed: the response passed PMBOT-LLM-001 validation but failed deterministic usefulness or "
        "certainty checks. Do not show it as accepted operator context."
    )


def _next_safe_operator_action(status):
    if status == "quality_passed":
        return "Use the response only as manual review context and verify unresolved source gaps against local artifacts."
    if status == "quality_passed_with_warnings":
        return "Review the warnings, add missing detail to the local response JSON if needed, and rerun the quality gate."
    return "Revise or replace the local manual response JSON, then rerun PMBOT-LLM-001 validation and this quality gate."


def _source_artifacts(packet_payload, packet_path, response_path, manual_review_path):
    declared = []
    if isinstance(packet_payload, dict) and isinstance(packet_payload.get("source_artifacts"), list):
        declared = packet_payload["source_artifacts"]
    manual_artifacts = {
        "packet": _display_path(packet_path),
        "response": _display_path(response_path),
    }
    if manual_review_path is not None:
        manual_artifacts["manual_review"] = _display_path(manual_review_path)
    return {
        "packet_declared_source_artifacts": declared,
        "manual_artifacts": manual_artifacts,
        "contract_artifacts": [
            _display_path(validator.PACKET_SCHEMA_PATH),
            _display_path(validator.RESPONSE_SCHEMA_PATH),
            _display_path(validator.LLM_DIR / "validate_llm_analysis_artifacts.py"),
            _display_path(Path(__file__).resolve()),
        ],
    }


def build_quality_gate(
    packet_path=DEFAULT_PACKET_PATH,
    response_path=DEFAULT_RESPONSE_PATH,
    manual_review_path=DEFAULT_MANUAL_REVIEW_PATH,
):
    packet_path = _resolve_path(packet_path)
    response_path = _resolve_path(response_path)
    manual_review_path = _resolve_path(manual_review_path)

    packet_payload, packet_load_errors = _load_json_artifact(packet_path, "packet")
    response_payload, response_load_errors = _load_json_artifact(response_path, "response")
    packet_schema, packet_schema_errors = _load_json_artifact(validator.PACKET_SCHEMA_PATH, "packet_schema")
    response_schema, response_schema_errors = _load_json_artifact(validator.RESPONSE_SCHEMA_PATH, "response_schema")

    if packet_load_errors or packet_schema_errors:
        packet_result = _base_validation_from_load_errors(packet_load_errors + packet_schema_errors)
    else:
        packet_result = validator.validate_packet_payload(packet_payload, packet_schema)

    if response_load_errors or response_schema_errors:
        response_result = _base_validation_from_load_errors(response_load_errors + response_schema_errors)
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

    base_errors, base_warnings = _aggregate_base_messages(packet_validation, response_validation)
    base_status = "accepted" if packet_result["status"] == "accepted" and response_result["status"] == "accepted" else "rejected"

    quality_checks = _all_quality_checks(response_payload, base_errors)
    quality_errors = []
    quality_warnings = []
    for check in quality_checks.values():
        quality_errors.extend(check["errors"])
        quality_warnings.extend(check["warnings"])

    manual_review_check = _load_optional_manual_review(manual_review_path)
    manual_review_warnings = [
        {**warning, "check": "manual_review_input_check"} for warning in manual_review_check["warnings"]
    ]

    errors = list(base_errors)
    warnings = list(base_warnings) + quality_warnings + manual_review_warnings
    if base_status != "accepted":
        errors.append(
            _error(
                "base_validator_rejected",
                "base_validator_status",
                "PMBOT-LLM-001 packet/response validation must pass before quality can pass.",
                "base_validator",
            )
        )
    errors.extend(quality_errors)

    errors = sorted(errors, key=lambda item: (item.get("check", ""), item.get("path", ""), item["code"], item["message"]))
    warnings = sorted(
        warnings,
        key=lambda item: (item.get("check", ""), item.get("path", ""), item["code"], item["message"]),
    )

    material_quality_failure = any(check["status"] == "failed" for check in quality_checks.values())
    if base_status != "accepted" or material_quality_failure:
        validation_status = "quality_failed"
    elif warnings:
        validation_status = "quality_passed_with_warnings"
    else:
        validation_status = "quality_passed"

    counts = _quality_counts(quality_checks, errors, warnings)

    return {
        "contract_version": CONTRACT_VERSION,
        "quality_gate_version": QUALITY_GATE_VERSION,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "packet_path": _display_path(packet_path),
        "response_path": _display_path(response_path),
        "manual_review_path": _display_path(manual_review_path),
        "validation_status": validation_status,
        "base_validator_status": base_status,
        "base_validator": {
            "packet_validation": packet_validation,
            "response_validation": response_validation,
            "errors": base_errors,
            "warnings": base_warnings,
        },
        "quality_counts": counts,
        "required_sections_check": quality_checks["required_sections_check"],
        "minimum_content_check": quality_checks["minimum_content_check"],
        "generic_or_placeholder_text_check": quality_checks["generic_or_placeholder_text_check"],
        "uncertainty_check": quality_checks["uncertainty_check"],
        "missing_evidence_check": quality_checks["missing_evidence_check"],
        "risk_notes_check": quality_checks["risk_notes_check"],
        "operator_checklist_check": quality_checks["operator_checklist_check"],
        "source_gap_notes_check": quality_checks["source_gap_notes_check"],
        "safety_acknowledgement_check": quality_checks["safety_acknowledgement_check"],
        "unsafe_certainty_check": quality_checks["unsafe_certainty_check"],
        "forbidden_content_check": quality_checks["forbidden_content_check"],
        "manual_review_input_check": manual_review_check,
        "warnings": warnings,
        "errors": errors,
        "safety_flags": dict(SAFETY_FLAGS),
        "operator_summary": _operator_summary(validation_status, base_status),
        "next_safe_operator_action": _next_safe_operator_action(validation_status),
        "source_artifacts": _source_artifacts(packet_payload, packet_path, response_path, manual_review_path),
    }


def _format_messages(messages):
    if not messages:
        return ["- none"]
    lines = []
    for message in messages:
        artifact = f"[{message['artifact']}] " if "artifact" in message else ""
        check = f"{message.get('check', 'quality_gate')}: "
        lines.append(f"- {artifact}{check}{message['path']}: {message['code']} - {message['message']}")
    return lines


def _format_check_status(check):
    return f"- {check['check_name']}: {check['status']}"


def render_markdown_summary(result):
    missing_generic = (
        result["generic_or_placeholder_text_check"]["errors"]
        + result["generic_or_placeholder_text_check"]["warnings"]
        + result["minimum_content_check"]["errors"]
    )
    lines = [
        "# PMBOT Manual LLM Review Quality Gate v1",
        "",
        f"- Quality gate status: {result['validation_status']}",
        f"- Base validator status: {result['base_validator_status']}",
        f"- Packet path: {result['packet_path']}",
        f"- Response path: {result['response_path']}",
        f"- Manual review path: {result['manual_review_path']}",
        "",
        "## Required Sections Status",
        _format_check_status(result["required_sections_check"]),
        _format_check_status(result["minimum_content_check"]),
        _format_check_status(result["uncertainty_check"]),
        _format_check_status(result["missing_evidence_check"]),
        _format_check_status(result["risk_notes_check"]),
        _format_check_status(result["operator_checklist_check"]),
        _format_check_status(result["source_gap_notes_check"]),
        _format_check_status(result["safety_acknowledgement_check"]),
        "",
        "## Warnings",
        *_format_messages(result["warnings"]),
        "",
        "## Errors",
        *_format_messages(result["errors"]),
        "",
        "## Unsafe Certainty Findings",
        *_format_messages(result["unsafe_certainty_check"]["findings"]),
        "",
        "## Missing Or Generic Content Findings",
        *_format_messages(missing_generic),
        "",
        "## Next Safe Operator Action",
        result["next_safe_operator_action"],
        "",
        "## Boundary Notice",
        (
            "This is a deterministic offline quality gate. It does not evaluate truth, probability, EV, edge, "
            "side, or trade execution."
        ),
        (
            "It adds no LLM API calls, browser automation, prompt automation, runtime integration, orders, "
            "autonomous paper orders, wallet handling, or market decision logic."
        ),
        "",
    ]
    return "\n".join(lines)


def export_quality_gate(
    packet_path=DEFAULT_PACKET_PATH,
    response_path=DEFAULT_RESPONSE_PATH,
    manual_review_path=DEFAULT_MANUAL_REVIEW_PATH,
    out_json_path=DEFAULT_OUT_JSON_PATH,
    out_md_path=DEFAULT_OUT_MD_PATH,
):
    result = build_quality_gate(packet_path, response_path, manual_review_path)
    out_json_path = _resolve_path(out_json_path)
    out_md_path = _resolve_path(out_md_path)
    out_json_path.parent.mkdir(parents=True, exist_ok=True)
    out_md_path.parent.mkdir(parents=True, exist_ok=True)
    out_json_path.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    out_md_path.write_text(render_markdown_summary(result), encoding="utf-8")
    return result


def main(argv):
    args = _parse_args(argv)
    result = export_quality_gate(
        args.packet,
        args.response,
        args.manual_review,
        args.out_json,
        args.out_md,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["validation_status"] != "quality_failed" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
