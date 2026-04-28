import argparse
import json
import re
import sys
from pathlib import Path


CONTRACT_PATH = Path(__file__).with_name("review_pack_command_bridge_contract.v1.json")

SECRET_PATTERNS = (
    ("credential_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.IGNORECASE)),
    ("telegram_bot_token_shape", re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b")),
    ("url_shape", re.compile(r"\b(?:https?|wss?)://", re.IGNORECASE)),
    ("bearer_token_shape", re.compile(r"\bbearer\s+[A-Za-z0-9._-]{20,}\b", re.IGNORECASE)),
)

SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,96}$")
CONTROL_FIELDS = {"execution_authority", "can_trigger_runtime"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_contract(path: Path = CONTRACT_PATH):
    return load_json(path)


def _path_label(path):
    return ".".join(str(part) for part in path)


def _normalized_text(value):
    return f" {re.sub(r'[^a-z0-9]+', ' ', value.lower()).strip()} "


def _contains_forbidden_text(value, contract):
    normalized = _normalized_text(value)
    for fragment in contract["forbidden_text_fragments"]:
        if _normalized_text(fragment).strip() in normalized:
            return True
    return False


def _matches_secret_shape(value):
    return any(pattern.search(value) for _, pattern in SECRET_PATTERNS)


def _is_forbidden_key(path, key, contract):
    if path == ("safety_flags",) or (path and path[0] == "safety_flags"):
        return False
    if len(path) == 1 and key in CONTROL_FIELDS:
        return False

    normalized_key = _normalized_text(key)
    for fragment in contract["forbidden_fields"]:
        normalized_fragment = _normalized_text(fragment).strip()
        if f" {normalized_fragment} " in normalized_key:
            return True
    return False


def _scan_forbidden(value, contract, path=()):
    errors = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = path + (key,)
            if _is_forbidden_key(child_path, str(key), contract):
                errors.append(f"forbidden_field_name:{_path_label(child_path)}")
            errors.extend(_scan_forbidden(child, contract, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(_scan_forbidden(child, contract, path + (index,)))
    elif isinstance(value, str):
        if _contains_forbidden_text(value, contract):
            errors.append(f"forbidden_text_present:{_path_label(path)}")
        if _matches_secret_shape(value):
            errors.append(f"credential_shape_present:{_path_label(path)}")
    return errors


def _string_field(record, field, errors):
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"string_field_required:{field}")
    return value


def _optional_string_field(record, field, errors):
    if field in record and (not isinstance(record[field], str) or not record[field].strip()):
        errors.append(f"optional_string_field_must_be_non_empty_string:{field}")


def _mapping_set(contract):
    return {
        (item["command_type"], item["review_pack_section_id"], item["allowed_bridge_action"])
        for item in contract["bridge_mappings"]
    }


def _validate_safety_flags(record, contract, errors):
    safety_flags = record.get("safety_flags")
    if not isinstance(safety_flags, dict):
        errors.append("safety_flags_must_be_object")
        return

    required_flags = set(contract["required_safety_flags_false"])
    for flag in sorted(required_flags - set(safety_flags)):
        errors.append(f"missing_safety_flag:{flag}")
    for flag in sorted(set(safety_flags) - required_flags):
        errors.append(f"unexpected_safety_flag:{flag}")
    for flag in sorted(required_flags & set(safety_flags)):
        if safety_flags[flag] is not False:
            errors.append(f"safety_flag_must_be_false:{flag}")


def validate_bridge_record(record, contract=None):
    contract = contract or load_contract()
    errors = []

    if not isinstance(record, dict):
        return ["bridge_record_must_be_object"]

    required = set(contract["required_bridge_record_fields"])
    allowed = set(contract["allowed_bridge_record_fields"])

    for field in sorted(required - set(record)):
        errors.append(f"missing_required_field:{field}")
    for field in sorted(set(record) - allowed):
        errors.append(f"unexpected_top_level_field:{field}")

    if record.get("schema_version") != contract["bridge_record_schema_version"]:
        errors.append("schema_version_must_match_contract")

    bridge_id = _string_field(record, "bridge_id", errors)
    if isinstance(bridge_id, str) and not SAFE_ID_RE.match(bridge_id):
        errors.append("bridge_id_has_invalid_shape")

    command_type = _string_field(record, "command_type", errors)
    if command_type not in contract["allowed_command_types"]:
        errors.append(f"invalid_command_type:{command_type}")

    section_id = _string_field(record, "review_pack_section_id", errors)
    if section_id not in contract["review_pack_section_ids"]:
        errors.append(f"invalid_review_pack_section_id:{section_id}")

    bridge_action = _string_field(record, "allowed_bridge_action", errors)
    if bridge_action not in contract["allowed_bridge_actions"]:
        errors.append(f"invalid_allowed_bridge_action:{bridge_action}")

    if (command_type, section_id, bridge_action) not in _mapping_set(contract):
        errors.append("invalid_bridge_mapping")

    if record.get("requires_human_review") is not True:
        errors.append("requires_human_review_must_be_true")
    if record.get("execution_authority") is not False:
        errors.append("execution_authority_must_be_false")
    if record.get("can_trigger_runtime") is not False:
        errors.append("can_trigger_runtime_must_be_false")

    if record.get("source_command_schema_version", contract["source_command_schema_version"]) != contract["source_command_schema_version"]:
        errors.append("source_command_schema_version_must_match_manual_command_contract")

    _optional_string_field(record, "source_command_id", errors)
    _optional_string_field(record, "source_artifact_pointer_label", errors)
    _optional_string_field(record, "bridge_notes", errors)
    _validate_safety_flags(record, contract, errors)
    errors.extend(_scan_forbidden(record, contract))

    return list(dict.fromkeys(errors))


def validate_examples_document(document, contract=None):
    contract = contract or load_contract()
    errors = []
    valid_records = document.get("valid_bridge_records", [])
    invalid_records = document.get("invalid_bridge_records", [])

    if not isinstance(valid_records, list):
        errors.append("valid_bridge_records_must_be_array")
        valid_records = []
    if not isinstance(invalid_records, list):
        errors.append("invalid_bridge_records_must_be_array")
        invalid_records = []

    for index, record in enumerate(valid_records):
        record_errors = validate_bridge_record(record, contract)
        if record_errors:
            errors.append(f"valid_example_failed:{index}:{','.join(record_errors)}")

    for index, wrapper in enumerate(invalid_records):
        record = wrapper.get("record") if isinstance(wrapper, dict) else None
        expected = wrapper.get("expected_reject_reasons", []) if isinstance(wrapper, dict) else []
        record_errors = validate_bridge_record(record, contract)
        if not record_errors:
            errors.append(f"invalid_example_accepted:{index}")
            continue
        for expected_reason in expected:
            if not any(error == expected_reason or error.startswith(f"{expected_reason}:") for error in record_errors):
                errors.append(f"invalid_example_missing_expected_reason:{index}:{expected_reason}")

    return {
        "schema_version": "review_pack_command_bridge_validation_result.v1",
        "valid_examples_checked": len(valid_records),
        "invalid_examples_checked": len(invalid_records),
        "errors": errors,
        "status": "passed" if not errors else "failed",
    }


def _parse_args():
    parser = argparse.ArgumentParser(description="Validate inert PMBOT review pack command bridge records.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--examples", action="store_true", help="Validate review pack command bridge examples.")
    return parser.parse_args()


def main():
    args = _parse_args()
    data = load_json(args.path)
    contract = load_contract()

    if args.examples:
        result = validate_examples_document(data, contract)
    else:
        errors = validate_bridge_record(data, contract)
        result = {
            "schema_version": "review_pack_command_bridge_validation_result.v1",
            "bridge_record_path": str(args.path),
            "errors": errors,
            "status": "passed" if not errors else "failed",
        }

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
