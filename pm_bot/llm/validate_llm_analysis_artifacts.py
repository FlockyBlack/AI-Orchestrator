import argparse
import ast
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LLM_DIR = ROOT / "pm_bot" / "llm"

PACKET_SCHEMA_PATH = LLM_DIR / "llm_analysis_packet_schema.v1.json"
RESPONSE_SCHEMA_PATH = LLM_DIR / "llm_analysis_response_schema.v1.json"
DEFAULT_PACKET_PATH = LLM_DIR / "example_llm_analysis_packet.v1.json"
DEFAULT_RESPONSE_PATH = LLM_DIR / "example_llm_analysis_response_valid.v1.json"

SCHEMA_VERSION = "llm_analysis_artifact_validation.v1"

ALLOWED_RESPONSE_SECTIONS = (
    "concise_market_summary",
    "key_uncertainties",
    "missing_evidence",
    "contradiction_checks",
    "risk_notes",
    "operator_review_checklist",
    "suggested_research_questions",
    "citation_or_source_gap_notes",
    "safety_acknowledgement",
)

REQUIRED_FORBIDDEN_OUTPUTS = (
    "recommended_side",
    "bet_yes_or_no",
    "order_size",
    "price_target",
    "probability",
    "implied_probability",
    "fair_value",
    "ev",
    "edge",
    "expected_return",
    "kelly_sizing",
    "execution_instruction",
    "auto_trade_instruction",
    "wallet_instruction",
    "market_outcome_certainty_claim",
)

FORBIDDEN_PACKET_FIELD_NAMES = {
    "api_key",
    "api_secret",
    "authorization_header",
    "autonomous_action_request",
    "bet_yes_or_no",
    "credentials",
    "edge",
    "ev",
    "expected_return",
    "fair_value",
    "implied_probability",
    "kelly_sizing",
    "order",
    "order_placement",
    "order_size",
    "orders",
    "place_order",
    "price_target",
    "private_key",
    "probability",
    "probability_target",
    "recommended_side",
    "seed_phrase",
    "side_recommendation_request",
    "signer",
    "submit_order",
    "trade",
    "trading_endpoint",
    "wallet",
    "wallet_address",
}

FORBIDDEN_RESPONSE_FIELD_NAMES = {
    "auto_trade_instruction",
    "bet_yes_or_no",
    "edge",
    "ev",
    "execution_instruction",
    "expected_return",
    "fair_value",
    "implied_probability",
    "kelly_sizing",
    "order_size",
    "price_target",
    "probability",
    "recommended_side",
    "wallet_instruction",
}

FORBIDDEN_LANGUAGE_PATTERNS = (
    ("forbidden_phrase:recommended_side", "recommended side", re.compile(r"\brecommended\s+side\b", re.IGNORECASE)),
    ("forbidden_phrase:bet_on", "bet on", re.compile(r"\bbet\s+on\b", re.IGNORECASE)),
    ("forbidden_phrase:place_order", "place order", re.compile(r"\bplace\s+order\b", re.IGNORECASE)),
    ("forbidden_phrase:buy_yes", "buy YES", re.compile(r"\bbuy\s+yes\b", re.IGNORECASE)),
    ("forbidden_phrase:buy_no", "buy NO", re.compile(r"\bbuy\s+no\b", re.IGNORECASE)),
    ("forbidden_phrase:sell_yes", "sell YES", re.compile(r"\bsell\s+yes\b", re.IGNORECASE)),
    ("forbidden_phrase:sell_no", "sell NO", re.compile(r"\bsell\s+no\b", re.IGNORECASE)),
    ("forbidden_phrase:ev", "EV", re.compile(r"\bev\b", re.IGNORECASE)),
    ("forbidden_phrase:edge", "edge", re.compile(r"\bedge\b", re.IGNORECASE)),
    ("forbidden_phrase:kelly", "Kelly", re.compile(r"\bkelly\b", re.IGNORECASE)),
    ("forbidden_phrase:fair_probability", "fair probability", re.compile(r"\bfair\s+probability\b", re.IGNORECASE)),
    ("forbidden_phrase:my_probability", "my probability", re.compile(r"\bmy\s+probability\b", re.IGNORECASE)),
    ("forbidden_phrase:autotrade", "autotrade", re.compile(r"\bauto\s*trade\b", re.IGNORECASE)),
    ("forbidden_phrase:execute_trade", "execute trade", re.compile(r"\bexecute\s+trade\b", re.IGNORECASE)),
)

FORBIDDEN_LANGUAGE_CATEGORIES = {
    "forbidden_phrase:recommended_side": "side_selection_language",
    "forbidden_phrase:bet_on": "market_action_language",
    "forbidden_phrase:place_order": "order_instruction_language",
    "forbidden_phrase:buy_yes": "market_action_language",
    "forbidden_phrase:buy_no": "market_action_language",
    "forbidden_phrase:sell_yes": "market_action_language",
    "forbidden_phrase:sell_no": "market_action_language",
    "forbidden_phrase:ev": "value_scoring_language",
    "forbidden_phrase:edge": "value_scoring_language",
    "forbidden_phrase:kelly": "value_scoring_language",
    "forbidden_phrase:fair_probability": "probability_language",
    "forbidden_phrase:my_probability": "probability_language",
    "forbidden_phrase:autotrade": "autonomous_action_language",
    "forbidden_phrase:execute_trade": "trade_execution_language",
}

SNIPPET_REDACTION_RE = re.compile(
    r"\b("
    r"buy|buying|sell|selling|hold|holding|enter|entering|entry|exit|exiting|"
    r"trade|trading|order|orders|side|yes|no|probability|probabilities|ev|edge|"
    r"score|scoring|confidence|kelly|wallet|private\s+key|seed\s+phrase|"
    r"credential|credentials|recommend|recommends|recommended|recommending|"
    r"recommendation|recommendations"
    r")\b",
    re.IGNORECASE,
)

CERTAINTY_LANGUAGE_PATTERNS = (
    ("forbidden_certainty:market_outcome_is_certain", "market outcome is certain", re.compile(r"\bmarket\s+outcome\s+is\s+certain\b", re.IGNORECASE)),
    ("forbidden_certainty:outcome_is_certain", "outcome is certain", re.compile(r"\boutcome\s+is\s+certain\b", re.IGNORECASE)),
    ("forbidden_certainty:will_definitely", "will definitely", re.compile(r"\bwill\s+definitely\b", re.IGNORECASE)),
    ("forbidden_certainty:guaranteed_outcome", "guaranteed outcome", re.compile(r"\bguaranteed\s+outcome\b", re.IGNORECASE)),
)

PACKET_REQUEST_SCAN_FIELDS = {
    "operator_questions",
    "required_response_sections",
}

SAFETY_FLAGS = {
    "runtime_wiring": False,
    "network_api": False,
    "llm_api": False,
    "credentials_or_wallet": False,
    "real_orders_or_live_trading": False,
    "autonomous_paper_orders": False,
    "probability_ev_scoring_or_edge": False,
    "side_recommendations": False,
    "dispatcher_or_run_codex_changed": False,
    "prompt_automation": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Validate local PMBOT LLM analysis packet and response artifacts.")
    parser.add_argument("--packet", default=str(DEFAULT_PACKET_PATH.relative_to(ROOT)))
    parser.add_argument("--response", default=str(DEFAULT_RESPONSE_PATH.relative_to(ROOT)))
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


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _error(code, path, message, **extra):
    error = {"code": code, "path": path, "message": message}
    error.update(extra)
    return error


def _append(errors, code, path, message, **extra):
    errors.append(_error(code, path, message, **extra))


def _normalize_key(key):
    return re.sub(r"[^a-z0-9]+", "_", str(key).lower()).strip("_")


def _iter_key_paths(value, prefix=""):
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            yield path, _normalize_key(key_text)
            yield from _iter_key_paths(nested, path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _iter_key_paths(item, f"{prefix}[{index}]")


def _iter_strings(value, prefix=""):
    if isinstance(value, str):
        yield prefix, value
    elif isinstance(value, dict):
        for key, nested in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield from _iter_strings(nested, path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            yield from _iter_strings(item, path)


def _safe_redacted_snippet(value, match=None, max_chars=180):
    text = str(value)
    if match is None:
        snippet = text[:max_chars]
        if len(text) > max_chars:
            snippet += "..."
    else:
        radius = max(20, (max_chars - len(match.group(0))) // 2)
        start = max(0, match.start() - radius)
        end = min(len(text), match.end() + radius)
        snippet = text[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(text):
            snippet += "..."
    snippet = SNIPPET_REDACTION_RE.sub("[redacted:safety-term]", snippet)
    return " ".join(snippet.split())


def _language_diagnostic_classification(code, text):
    if code == "forbidden_phrase:edge" and re.search(r"\bedge\s+cases?\b", str(text), re.IGNORECASE):
        return "false_positive_contextual_phrase", "neutral_edge_case_phrase_preserve_block"
    return "true_positive_model_forbidden_phrase", "direct_policy_phrase"


def _type_matches(value, expected_type):
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "boolean":
        return isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "null":
        return value is None
    return False


def _validate_type(value, expected_type):
    if isinstance(expected_type, list):
        return any(_type_matches(value, item) for item in expected_type)
    return _type_matches(value, expected_type)


def _validate_against_schema(value, schema, path, errors):
    if "type" in schema and not _validate_type(value, schema["type"]):
        _append(errors, "schema_type_mismatch", path, f"{path or '$'} must be {schema['type']}.")
        return

    if "const" in schema and value != schema["const"]:
        _append(errors, "schema_const_mismatch", path, f"{path or '$'} must equal {schema['const']!r}.")

    if "enum" in schema and value not in schema["enum"]:
        _append(errors, "schema_enum_mismatch", path, f"{path or '$'} is not in the allowed enum set.")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            _append(errors, "schema_string_too_short", path, f"{path or '$'} must not be empty.")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            _append(errors, "schema_pattern_mismatch", path, f"{path or '$'} does not match the required pattern.")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            _append(errors, "schema_array_too_short", path, f"{path or '$'} must contain at least {schema['minItems']} items.")
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                _validate_against_schema(item, item_schema, f"{path}[{index}]" if path else f"[{index}]", errors)

    if isinstance(value, dict):
        required = schema.get("required", [])
        for field in required:
            if field not in value:
                _append(errors, "schema_missing_required", f"{path}.{field}" if path else field, f"{field} is required.")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for field in sorted(set(value) - set(properties)):
                _append(errors, "schema_unexpected_field", f"{path}.{field}" if path else field, f"{field} is not allowed.")

        for field in sorted(set(value) & set(properties)):
            child_path = f"{path}.{field}" if path else field
            _validate_against_schema(value[field], properties[field], child_path, errors)


def _schema_errors(payload, schema):
    errors = []
    _validate_against_schema(payload, schema, "", errors)
    return sorted(errors, key=lambda item: (item["path"], item["code"], item["message"]))


def _forbidden_field_errors(payload, forbidden_names, base_code, gate_id):
    errors = []
    for path, normalized_key in _iter_key_paths(payload):
        if normalized_key in forbidden_names:
            _append(
                errors,
                f"{base_code}:{normalized_key}",
                path,
                f"{path} uses forbidden field name {normalized_key}.",
                gate_id=gate_id,
                detector_rule_id=f"{base_code}:{normalized_key}",
                forbidden_phrase=normalized_key,
                field_path=path,
                safe_redacted_excerpt="field:[redacted:safety-term]",
                safe_redacted_snippet="field:[redacted:safety-term]",
                diagnostic_classification="true_positive_model_forbidden_phrase",
                diagnostic_reason_code="prohibited_schema_field",
                checked_content_source="parsed_payload",
                violation_category="prohibited_field",
            )
    return sorted(errors, key=lambda item: (item["path"], item["code"], item["message"]))


def _language_pattern_errors(
    value,
    path_prefix,
    include_certainty_patterns,
    gate_id,
    checked_content_source,
):
    errors = []
    patterns = FORBIDDEN_LANGUAGE_PATTERNS
    if include_certainty_patterns:
        patterns = patterns + CERTAINTY_LANGUAGE_PATTERNS
    for path, text in _iter_strings(value, path_prefix):
        for code, display, pattern in patterns:
            match = pattern.search(text)
            if match:
                diagnostic_classification, reason_code = _language_diagnostic_classification(code, text)
                category = FORBIDDEN_LANGUAGE_CATEGORIES.get(code, "certainty_language")
                _append(
                    errors,
                    code,
                    path,
                    f"Forbidden deterministic language pattern found: {display}.",
                    gate_id=gate_id,
                    detector_rule_id=code,
                    forbidden_phrase=display,
                    field_path=path,
                    safe_redacted_excerpt=_safe_redacted_snippet(text, match),
                    safe_redacted_snippet=_safe_redacted_snippet(text, match),
                    diagnostic_classification=diagnostic_classification,
                    diagnostic_reason_code=reason_code,
                    checked_content_source=checked_content_source,
                    violation_category=category,
                )
    return sorted(errors, key=lambda item: (item["path"], item["code"], item["message"]))


def _packet_request_language_errors(packet):
    errors = []
    if not isinstance(packet, dict):
        return errors
    for field in sorted(PACKET_REQUEST_SCAN_FIELDS):
        if field in packet:
            errors.extend(
                _language_pattern_errors(
                    packet[field],
                    field,
                    include_certainty_patterns=True,
                    gate_id="packet_request",
                    checked_content_source="parsed_packet_payload",
                )
            )
    return sorted(errors, key=lambda item: (item["path"], item["code"], item["message"]))


def _packet_forbidden_outputs_errors(packet):
    errors = []
    if not isinstance(packet, dict):
        return errors
    raw_values = packet.get("forbidden_outputs")
    if not isinstance(raw_values, list):
        return errors
    normalized = {_normalize_key(item) for item in raw_values if isinstance(item, str)}
    missing = [item for item in REQUIRED_FORBIDDEN_OUTPUTS if item not in normalized]
    for item in missing:
        _append(
            errors,
            f"missing_required_forbidden_output:{item}",
            "forbidden_outputs",
            f"forbidden_outputs must explicitly ban {item}.",
        )
    return errors


def validate_packet_payload(packet, schema=None):
    schema = schema or _load_json(PACKET_SCHEMA_PATH)
    errors = []
    warnings = []
    errors.extend(_schema_errors(packet, schema))
    errors.extend(
        _forbidden_field_errors(
            packet,
            FORBIDDEN_PACKET_FIELD_NAMES,
            "forbidden_packet_field",
            gate_id="packet_schema",
        )
    )
    errors.extend(_packet_request_language_errors(packet))
    errors.extend(_packet_forbidden_outputs_errors(packet))
    return {
        "status": "accepted" if not errors else "rejected",
        "errors": sorted(errors, key=lambda item: (item["path"], item["code"], item["message"])),
        "warnings": warnings,
    }


def validate_response_payload(response, schema=None):
    schema = schema or _load_json(RESPONSE_SCHEMA_PATH)
    errors = []
    warnings = []
    errors.extend(_schema_errors(response, schema))
    errors.extend(
        _forbidden_field_errors(
            response,
            FORBIDDEN_RESPONSE_FIELD_NAMES,
            "forbidden_response_field",
            gate_id="response_schema",
        )
    )
    errors.extend(
        _language_pattern_errors(
            response,
            "",
            include_certainty_patterns=True,
            gate_id="response_schema",
            checked_content_source="parsed_response_payload",
        )
    )
    return {
        "status": "accepted" if not errors else "rejected",
        "errors": sorted(errors, key=lambda item: (item["path"], item["code"], item["message"])),
        "warnings": warnings,
    }


def validate_packet_file(packet_path=DEFAULT_PACKET_PATH):
    packet_path = _resolve_path(packet_path)
    packet = _load_json(packet_path)
    result = validate_packet_payload(packet, _load_json(PACKET_SCHEMA_PATH))
    result["artifact_paths"] = {
        "packet": _display_path(packet_path),
        "packet_schema": _display_path(PACKET_SCHEMA_PATH),
    }
    result["safety_flags"] = dict(SAFETY_FLAGS)
    return result


def validate_response_file(response_path=DEFAULT_RESPONSE_PATH):
    response_path = _resolve_path(response_path)
    response = _load_json(response_path)
    result = validate_response_payload(response, _load_json(RESPONSE_SCHEMA_PATH))
    result["artifact_paths"] = {
        "response": _display_path(response_path),
        "response_schema": _display_path(RESPONSE_SCHEMA_PATH),
    }
    result["safety_flags"] = dict(SAFETY_FLAGS)
    return result


def validate_standard_library_only():
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return imports <= {"argparse", "ast", "json", "re", "sys", "pathlib"}


def validate_artifacts(packet_path=DEFAULT_PACKET_PATH, response_path=DEFAULT_RESPONSE_PATH):
    packet_path = _resolve_path(packet_path)
    response_path = _resolve_path(response_path)

    packet_schema = _load_json(PACKET_SCHEMA_PATH)
    response_schema = _load_json(RESPONSE_SCHEMA_PATH)
    packet = _load_json(packet_path)
    response = _load_json(response_path)

    packet_result = validate_packet_payload(packet, packet_schema)
    response_result = validate_response_payload(response, response_schema)

    errors = []
    warnings = []
    for error in packet_result["errors"]:
        errors.append({**error, "artifact": "packet"})
    for error in response_result["errors"]:
        errors.append({**error, "artifact": "response"})
    warnings.extend({**warning, "artifact": "packet"} for warning in packet_result["warnings"])
    warnings.extend({**warning, "artifact": "response"} for warning in response_result["warnings"])

    standard_library_only = validate_standard_library_only()
    if not standard_library_only:
        errors.append(
            _error(
                "validator_imports_non_standard_library",
                "pm_bot/llm/validate_llm_analysis_artifacts.py",
                "Validator must remain standard-library only.",
            )
        )

    errors = sorted(errors, key=lambda item: (item.get("artifact", ""), item["path"], item["code"], item["message"]))
    status = "accepted" if not errors else "rejected"

    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "safety_flags": dict(SAFETY_FLAGS),
        "artifact_paths": {
            "packet": _display_path(packet_path),
            "response": _display_path(response_path),
            "packet_schema": _display_path(PACKET_SCHEMA_PATH),
            "response_schema": _display_path(RESPONSE_SCHEMA_PATH),
        },
        "checks": {
            "packet_schema_valid": packet_result["status"] == "accepted",
            "response_schema_valid": response_result["status"] == "accepted",
            "forbidden_response_fields_absent": not any(
                error["code"].startswith("forbidden_response_field") for error in response_result["errors"]
            ),
            "forbidden_response_language_absent": not any(
                error["code"].startswith("forbidden_phrase") or error["code"].startswith("forbidden_certainty")
                for error in response_result["errors"]
            ),
            "forbidden_packet_requests_absent": not any(
                error["code"].startswith("forbidden_phrase") or error["code"].startswith("forbidden_certainty")
                for error in packet_result["errors"]
            ),
            "required_forbidden_outputs_present": not any(
                error["code"].startswith("missing_required_forbidden_output") for error in packet_result["errors"]
            ),
            "standard_library_only": standard_library_only,
            "local_only_validator": True,
            "llm_api_calls": False,
            "network_api_calls": False,
            "runtime_wiring": False,
        },
    }


def main(argv):
    args = _parse_args(argv)
    report = validate_artifacts(args.packet, args.response)
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0 if report["status"] == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
