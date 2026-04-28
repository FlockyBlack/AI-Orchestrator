import argparse
import json
import re
import sys
from pathlib import Path


CONTRACT_PATH = Path(__file__).with_name("manual_command_contract.v1.json")

SECRET_PATTERNS = (
    ("credential_block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.IGNORECASE)),
    ("telegram_bot_token_shape", re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b")),
    ("url_shape", re.compile(r"\b(?:https?|wss?)://", re.IGNORECASE)),
    ("bearer_token_shape", re.compile(r"\bbearer\s+[A-Za-z0-9._-]{20,}\b", re.IGNORECASE)),
)

SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,80}$")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_contract(path: Path = CONTRACT_PATH):
    return load_json(path)


def _string_field(record, field, errors):
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"string_field_required:{field}")
    return value


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
    if path == ("execution_authority",):
        return False
    if path and path[0] == "safety_flags":
        return False
    normalized_key = _normalized_text(key)
    for fragment in contract["forbidden_field_name_fragments"]:
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


def _validate_payload(command_type, payload, contract, errors):
    if not isinstance(payload, dict):
        errors.append("payload_must_be_object")
        return

    payload_contracts = contract["payload_contract_by_command_type"]
    if command_type not in payload_contracts:
        return

    payload_contract = payload_contracts[command_type]
    required = set(payload_contract["required_fields"])
    allowed = set(payload_contract["allowed_fields"])

    for field in sorted(required - set(payload)):
        errors.append(f"missing_payload_field:{field}")
    for field in sorted(set(payload) - allowed):
        errors.append(f"unexpected_payload_field:{field}")

    for field, value in payload.items():
        if isinstance(value, str):
            if not value.strip():
                errors.append(f"payload_string_must_be_non_empty:{field}")
        elif isinstance(value, list):
            if not value:
                errors.append(f"payload_list_must_be_non_empty:{field}")
            for index, item in enumerate(value):
                if not isinstance(item, str) or not item.strip():
                    errors.append(f"payload_list_item_must_be_non_empty_string:{field}[{index}]")
        else:
            errors.append(f"payload_value_must_be_string_or_string_list:{field}")


def validate_command(record, contract=None):
    contract = contract or load_contract()
    errors = []

    if not isinstance(record, dict):
        return ["command_record_must_be_object"]

    required = set(contract["required_top_level_fields"])
    allowed = set(contract["allowed_top_level_fields"])

    for field in sorted(required - set(record)):
        errors.append(f"missing_required_field:{field}")
    for field in sorted(set(record) - allowed):
        errors.append(f"unexpected_top_level_field:{field}")

    if record.get("schema_version") != contract["command_schema_version"]:
        errors.append("schema_version_must_match_contract")

    command_id = _string_field(record, "command_id", errors)
    if isinstance(command_id, str) and not SAFE_ID_RE.match(command_id):
        errors.append("command_id_has_invalid_shape")

    command_type = _string_field(record, "command_type", errors)
    if command_type not in contract["allowed_command_types"]:
        errors.append(f"invalid_command_type:{command_type}")

    source_type = _string_field(record, "source_type", errors)
    if source_type not in contract["allowed_source_types"]:
        errors.append(f"invalid_source_type:{source_type}")
    if source_type in contract["forbidden_source_types"]:
        errors.append(f"forbidden_source_type:{source_type}")

    _string_field(record, "source_label", errors)

    created_by_policy = _string_field(record, "created_by_policy", errors)
    if created_by_policy not in contract["allowed_created_by_policy"]:
        errors.append(f"invalid_created_by_policy:{created_by_policy}")

    if "market_id" in record and not isinstance(record["market_id"], str):
        errors.append("optional_string_field_must_be_string:market_id")
    if "artifact_pointer" in record and not isinstance(record["artifact_pointer"], str):
        errors.append("optional_string_field_must_be_string:artifact_pointer")

    if record.get("execution_authority") is not False:
        errors.append("execution_authority_must_be_false")
    if record.get("requires_human_review") is not True:
        errors.append("requires_human_review_must_be_true")

    allowed_next_action = _string_field(record, "allowed_next_action", errors)
    if allowed_next_action not in contract["allowed_next_actions"]:
        errors.append(f"invalid_allowed_next_action:{allowed_next_action}")

    safety_flags = record.get("safety_flags")
    if not isinstance(safety_flags, dict):
        errors.append("safety_flags_must_be_object")
    else:
        required_flags = set(contract["required_safety_flags_false"])
        for flag in sorted(required_flags - set(safety_flags)):
            errors.append(f"missing_safety_flag:{flag}")
        for flag in sorted(set(safety_flags) - required_flags):
            errors.append(f"unexpected_safety_flag:{flag}")
        for flag in sorted(required_flags & set(safety_flags)):
            if safety_flags[flag] is not False:
                errors.append(f"safety_flag_must_be_false:{flag}")

    _validate_payload(command_type, record.get("payload"), contract, errors)
    errors.extend(_scan_forbidden(record, contract))

    return list(dict.fromkeys(errors))


def validate_examples_document(document, contract=None):
    contract = contract or load_contract()
    errors = []
    valid_commands = document.get("valid_commands", [])
    invalid_commands = document.get("invalid_commands", [])

    if not isinstance(valid_commands, list):
        errors.append("valid_commands_must_be_array")
        valid_commands = []
    if not isinstance(invalid_commands, list):
        errors.append("invalid_commands_must_be_array")
        invalid_commands = []

    for index, command in enumerate(valid_commands):
        command_errors = validate_command(command, contract)
        if command_errors:
            errors.append(f"valid_example_failed:{index}:{','.join(command_errors)}")

    for index, wrapper in enumerate(invalid_commands):
        command = wrapper.get("command") if isinstance(wrapper, dict) else None
        expected = wrapper.get("expected_reject_reasons", []) if isinstance(wrapper, dict) else []
        command_errors = validate_command(command, contract)
        if not command_errors:
            errors.append(f"invalid_example_accepted:{index}")
            continue
        for expected_reason in expected:
            if not any(error == expected_reason or error.startswith(f"{expected_reason}:") for error in command_errors):
                errors.append(f"invalid_example_missing_expected_reason:{index}:{expected_reason}")

    return {
        "schema_version": "manual_command_validation_result.v1",
        "valid_examples_checked": len(valid_commands),
        "invalid_examples_checked": len(invalid_commands),
        "errors": errors,
        "status": "passed" if not errors else "failed"
    }


def _parse_args():
    parser = argparse.ArgumentParser(description="Validate inert PMBOT manual command records.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--examples", action="store_true", help="Validate manual_command_examples.v1.json fixtures.")
    return parser.parse_args()


def main():
    args = _parse_args()
    data = load_json(args.path)
    contract = load_contract()

    if args.examples:
        result = validate_examples_document(data, contract)
    else:
        errors = validate_command(data, contract)
        result = {
            "schema_version": "manual_command_validation_result.v1",
            "command_path": str(args.path),
            "errors": errors,
            "status": "passed" if not errors else "failed"
        }

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
