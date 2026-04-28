import ast
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_DIR = ROOT / "pm_bot" / "contracts"
FIXTURES_DIR = ROOT / "pm_bot" / "fixtures" / "live_boundary"

REQUIRED_FILES = {
    "fetcher_contract": CONTRACTS_DIR / "live_readonly_fetcher_contract.v1.json",
    "raw_schema": CONTRACTS_DIR / "raw_market_snapshot.schema.v1.json",
    "normalized_schema": CONTRACTS_DIR / "normalized_market_snapshot.schema.v1.json",
    "quarantine_schema": CONTRACTS_DIR / "snapshot_quarantine_record.schema.v1.json",
    "paper_replay_contract": CONTRACTS_DIR / "paper_replay_import_contract.v1.json",
    "valid_raw_fixture": FIXTURES_DIR / "raw_snapshot.valid.example.v1.json",
    "invalid_raw_fixture": FIXTURES_DIR / "raw_snapshot.invalid.example.v1.json",
    "valid_normalized_fixture": FIXTURES_DIR / "normalized_snapshot.valid.example.v1.json",
    "quarantine_fixture": FIXTURES_DIR / "quarantine_record.example.v1.json",
}

FORBIDDEN_FIELD_NAMES = {
    "api_key",
    "api_secret",
    "authorization_header",
    "wallet",
    "wallet_address",
    "private_key",
    "seed_phrase",
    "signer",
    "signature",
    "order_instruction",
    "submit_order",
    "place_order",
    "execute_trade",
    "runtime_action",
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def collect_key_paths(payload, prefix=""):
    key_paths = []
    if isinstance(payload, dict):
        for key, value in payload.items():
            current = f"{prefix}.{key}" if prefix else key
            key_paths.append(current)
            key_paths.extend(collect_key_paths(value, current))
    elif isinstance(payload, list):
        for index, value in enumerate(payload):
            current = f"{prefix}[{index}]"
            key_paths.extend(collect_key_paths(value, current))
    return key_paths


def validate_payload_against_schema(schema, payload):
    errors = []

    for field in schema.get("required_fields", []):
        if field not in payload:
            errors.append(f"missing_required_field:{field}")

    for field, values in schema.get("enum_fields", {}).items():
        if field in payload and payload[field] not in values:
            errors.append(f"invalid_enum:{field}")

    for field in schema.get("numeric_fields", []):
        if field in payload and not isinstance(payload[field], (int, float)):
            errors.append(f"invalid_numeric:{field}")

    for field in schema.get("boolean_fields", []):
        if field in payload and not isinstance(payload[field], bool):
            errors.append(f"invalid_boolean:{field}")

    for field, spec in schema.get("array_fields", {}).items():
        if field in payload:
            value = payload[field]
            if not isinstance(value, list):
                errors.append(f"invalid_array:{field}")
            elif len(value) < spec.get("min_items", 0):
                errors.append(f"array_too_short:{field}")

    prohibited_paths = []
    all_key_paths = collect_key_paths(payload)
    for path in all_key_paths:
        field_name = path.split(".")[-1]
        field_name = field_name.split("[")[0]
        if field_name in schema.get("prohibited_fields", []):
            prohibited_paths.append(path)
    if prohibited_paths:
        errors.append(f"prohibited_fields_present:{','.join(sorted(prohibited_paths))}")

    return {"valid": not errors, "errors": errors}


def validate_normalized_snapshot_rules(payload):
    errors = []
    if payload.get("paper_replay_eligible") and payload.get("validation_status") != "valid":
        errors.append("paper_replay_eligible_requires_validation_status_valid")
    return {"valid": not errors, "errors": errors}


def build_quarantine_record(raw_payload, validation_errors):
    joined = " ".join(validation_errors)
    if "prohibited_fields_present" in joined:
        reason = "prohibited_fields_present"
        severity = "critical"
        allowed_next_step = "reject"
    elif "missing_required_field" in joined:
        reason = "malformed_snapshot"
        severity = "high"
        allowed_next_step = "manual_review"
    else:
        reason = "stale_or_unsupported_snapshot"
        severity = "medium"
        allowed_next_step = "fixture_replay_only"

    return {
        "quarantine_reason": reason,
        "source_snapshot_id": raw_payload.get("market_id", "unknown_snapshot"),
        "detected_at": "2026-04-26T10:21:00Z",
        "severity": severity,
        "blocking": True,
        "allowed_next_step": allowed_next_step,
    }


def validate_required_files():
    missing = []
    for path in REQUIRED_FILES.values():
        if not path.exists():
            missing.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return missing


def build_live_boundary_validation_report(root: Path):
    del root
    missing_files = validate_required_files()
    if missing_files:
        return {
            "status": "invalid",
            "missing_files": missing_files,
        }

    fetcher_contract = load_json(REQUIRED_FILES["fetcher_contract"])
    raw_schema = load_json(REQUIRED_FILES["raw_schema"])
    normalized_schema = load_json(REQUIRED_FILES["normalized_schema"])
    quarantine_schema = load_json(REQUIRED_FILES["quarantine_schema"])
    paper_replay_contract = load_json(REQUIRED_FILES["paper_replay_contract"])

    valid_raw_fixture = load_json(REQUIRED_FILES["valid_raw_fixture"])
    invalid_raw_fixture = load_json(REQUIRED_FILES["invalid_raw_fixture"])
    valid_normalized_fixture = load_json(REQUIRED_FILES["valid_normalized_fixture"])
    quarantine_fixture = load_json(REQUIRED_FILES["quarantine_fixture"])

    valid_raw_result = validate_payload_against_schema(raw_schema, valid_raw_fixture)
    invalid_raw_result = validate_payload_against_schema(raw_schema, invalid_raw_fixture)
    normalized_result = validate_payload_against_schema(normalized_schema, valid_normalized_fixture)
    normalized_rule_result = validate_normalized_snapshot_rules(valid_normalized_fixture)
    quarantine_fixture_result = validate_payload_against_schema(quarantine_schema, quarantine_fixture)
    generated_quarantine = build_quarantine_record(invalid_raw_fixture, invalid_raw_result["errors"])
    generated_quarantine_result = validate_payload_against_schema(quarantine_schema, generated_quarantine)

    prohibited_keys_seen = sorted(
        {
            key_path.split(".")[-1].split("[")[0]
            for key_path in collect_key_paths(invalid_raw_fixture)
            if key_path.split(".")[-1].split("[")[0] in FORBIDDEN_FIELD_NAMES
        }
    )

    report = {
        "schema_version": "v1",
        "artifact_type": "live_boundary_validation_report",
        "design_only": True,
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "contracts_loaded": {
            "fetcher_contract": fetcher_contract["artifact_type"],
            "raw_schema": raw_schema["artifact_type"],
            "normalized_schema": normalized_schema["artifact_type"],
            "quarantine_schema": quarantine_schema["artifact_type"],
            "paper_replay_contract": paper_replay_contract["artifact_type"],
        },
        "checks": {
            "valid_raw_fixture_accepted": valid_raw_result["valid"],
            "invalid_raw_fixture_rejected": not invalid_raw_result["valid"],
            "invalid_raw_fixture_quarantined": generated_quarantine_result["valid"],
            "normalized_fixture_valid": normalized_result["valid"],
            "normalized_fixture_paper_replay_eligible_only_when_valid": normalized_rule_result["valid"],
            "quarantine_fixture_valid": quarantine_fixture_result["valid"],
            "no_execution_fields_exist": all(field not in prohibited_keys_seen for field in {"order_instruction", "submit_order", "place_order", "execute_trade"}),
            "no_wallet_private_key_fields_exist": all(field not in prohibited_keys_seen for field in {"wallet", "wallet_address", "private_key", "seed_phrase", "signer", "signature"}),
            "no_api_credential_fields_exist": all(field not in prohibited_keys_seen for field in {"api_key", "api_secret", "authorization_header"}),
        },
        "invalid_fixture_prohibited_keys": prohibited_keys_seen,
        "invalid_fixture_errors": invalid_raw_result["errors"],
        "generated_quarantine_record": generated_quarantine,
    }
    report["checks"]["no_order_fields_exist"] = report["checks"]["no_execution_fields_exist"]
    report["validation_passed"] = all(report["checks"].values())
    return report


def validate_standard_library_only():
    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return imports <= {"ast", "json", "sys", "pathlib"}


def main(argv):
    if len(argv) != 0:
        print(json.dumps({"status": "invalid", "error": "usage: validate_live_boundary_contracts.py"}, separators=(",", ":")))
        return 2
    report = build_live_boundary_validation_report(ROOT)
    report["checks"]["standard_library_only"] = validate_standard_library_only()
    report["validation_passed"] = report.get("validation_passed", False) and report["checks"]["standard_library_only"]
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report.get("validation_passed") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
