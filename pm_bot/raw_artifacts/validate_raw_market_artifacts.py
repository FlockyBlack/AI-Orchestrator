import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURES_DIR = ROOT / "pm_bot" / "raw_artifacts" / "fixtures"
CONTRACT_PATH = ROOT / "pm_bot" / "raw_artifacts" / "raw_market_artifact_contract.v1.json"
EXPECTED_CONTRACT_VERSION = "raw_market_artifact.v1"
REFERENCE_TIME_TEXT = "2026-04-26T00:00:00Z"
REFERENCE_TIME = datetime(2026, 4, 26, 0, 0, 0, tzinfo=timezone.utc)
STALE_AFTER = timedelta(days=30)
SIDE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,31}$")
REQUIRED_TOP_LEVEL_FIELDS = (
    "contract_version",
    "artifact_id",
    "source_type",
    "source_name",
    "captured_at",
    "market",
    "outcomes",
    "provenance",
    "safety",
)
ALLOWED_SOURCE_TYPES = {
    "fixture",
    "manual_snapshot",
    "future_readonly_fetcher_output",
}
REQUIRED_MARKET_FIELDS = ("market_id", "title", "status")
OPTIONAL_MARKET_FIELDS = ("condition_id", "slug", "category", "end_date")
REQUIRED_PROVENANCE_FIELDS = ("collected_by", "collection_method", "source_reference")
OPTIONAL_PROVENANCE_FIELDS = ("notes",)
SAFETY_RULES = {
    "network_used": False,
    "api_credentials_used": False,
    "wallet_used": False,
    "order_capable": False,
    "trading_capable": False,
    "readonly_intended": True,
}


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_timestamp(value):
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _non_empty_text(value):
    return isinstance(value, str) and bool(value.strip())


def _finding(file_path, severity, code, message):
    return {
        "file": str(file_path).replace("\\", "/"),
        "severity": severity,
        "code": code,
        "message": message,
    }


def _append(findings, file_path, severity, code, message):
    findings.append(_finding(file_path, severity, code, message))


def validate_artifact(payload, file_path):
    findings = []

    if not isinstance(payload, dict):
        _append(findings, file_path, "blocking", "artifact_not_object", "Artifact root must be a JSON object.")
        return findings

    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in payload:
            _append(findings, file_path, "blocking", f"missing_required_field:{field}", f"Missing required top-level field '{field}'.")

    if payload.get("contract_version") != EXPECTED_CONTRACT_VERSION:
        _append(
            findings,
            file_path,
            "blocking",
            "bad_contract_version",
            f"contract_version must equal '{EXPECTED_CONTRACT_VERSION}'.",
        )

    if not _non_empty_text(payload.get("artifact_id")):
        _append(findings, file_path, "blocking", "empty_artifact_id", "artifact_id must be a non-empty string.")

    if payload.get("source_type") not in ALLOWED_SOURCE_TYPES:
        _append(findings, file_path, "blocking", "invalid_source_type", "source_type is not in the allowed source type set.")

    if not _non_empty_text(payload.get("source_name")):
        _append(findings, file_path, "blocking", "empty_source_name", "source_name must be a non-empty string.")

    captured_at = _parse_timestamp(payload.get("captured_at"))
    if captured_at is None:
        _append(findings, file_path, "blocking", "invalid_captured_at", "captured_at must be an ISO-like timestamp string.")
    elif captured_at < REFERENCE_TIME - STALE_AFTER:
        _append(
            findings,
            file_path,
            "warning",
            "stale_captured_at",
            f"captured_at is older than the deterministic reference window ending at {REFERENCE_TIME_TEXT}.",
        )

    market = payload.get("market")
    if not isinstance(market, dict):
        _append(findings, file_path, "blocking", "market_not_object", "market must be an object.")
        market = {}
    for field in REQUIRED_MARKET_FIELDS:
        if not _non_empty_text(market.get(field)):
            _append(findings, file_path, "blocking", f"invalid_market_field:{field}", f"market.{field} must be a non-empty string.")
    for field in OPTIONAL_MARKET_FIELDS:
        if field in market and market[field] is not None and not _non_empty_text(market[field]):
            _append(findings, file_path, "blocking", f"invalid_market_field:{field}", f"market.{field} must be a non-empty string when present.")
    if "end_date" in market and market.get("end_date") is not None and _parse_timestamp(market.get("end_date")) is None:
        _append(findings, file_path, "blocking", "invalid_market_end_date", "market.end_date must be an ISO-like timestamp string when present.")

    outcomes = payload.get("outcomes")
    if not isinstance(outcomes, list):
        _append(findings, file_path, "blocking", "outcomes_not_list", "outcomes must be a list.")
        outcomes = []
    elif not outcomes:
        _append(findings, file_path, "blocking", "outcomes_empty", "outcomes must contain at least one outcome.")

    seen_names = set()
    seen_sides = set()
    for index, outcome in enumerate(outcomes):
        prefix = f"outcomes[{index}]"
        if not isinstance(outcome, dict):
            _append(findings, file_path, "blocking", "malformed_outcome_entry", f"{prefix} must be an object.")
            continue
        name = outcome.get("name")
        side = outcome.get("side")
        price = outcome.get("price")
        if not _non_empty_text(name):
            _append(findings, file_path, "blocking", f"invalid_outcome_name:{index}", f"{prefix}.name must be a non-empty string.")
        else:
            key = name.strip().lower()
            if key in seen_names:
                _append(findings, file_path, "blocking", "duplicate_outcome_name", f"{prefix}.name duplicates a prior outcome name.")
            seen_names.add(key)
        if not _non_empty_text(side) or SIDE_PATTERN.fullmatch(side.strip()) is None:
            _append(findings, file_path, "blocking", f"invalid_outcome_side:{index}", f"{prefix}.side must match the lowercase side pattern.")
        else:
            key = side.strip().lower()
            if key in seen_sides:
                _append(findings, file_path, "blocking", "duplicate_outcome_side", f"{prefix}.side duplicates a prior outcome side.")
            seen_sides.add(key)
        if not isinstance(price, (int, float)):
            _append(findings, file_path, "blocking", f"invalid_outcome_price:{index}", f"{prefix}.price must be numeric.")
        elif price < 0 or price > 1:
            _append(findings, file_path, "blocking", "price_out_of_range", f"{prefix}.price must be between 0 and 1 inclusive.")
        for optional_field in ("liquidity", "volume"):
            if optional_field in outcome and outcome[optional_field] is not None and not isinstance(outcome[optional_field], (int, float)):
                _append(
                    findings,
                    file_path,
                    "blocking",
                    f"invalid_outcome_numeric:{optional_field}",
                    f"{prefix}.{optional_field} must be numeric when present.",
                )

    provenance = payload.get("provenance")
    if not isinstance(provenance, dict):
        _append(findings, file_path, "blocking", "provenance_not_object", "provenance must be an object.")
        provenance = {}
    for field in REQUIRED_PROVENANCE_FIELDS:
        if not _non_empty_text(provenance.get(field)):
            _append(findings, file_path, "blocking", f"invalid_provenance_field:{field}", f"provenance.{field} must be a non-empty string.")
    for field in OPTIONAL_PROVENANCE_FIELDS:
        if field in provenance and provenance[field] is not None and not _non_empty_text(provenance[field]):
            _append(findings, file_path, "blocking", f"invalid_provenance_field:{field}", f"provenance.{field} must be a non-empty string when present.")

    safety = payload.get("safety")
    if not isinstance(safety, dict):
        _append(findings, file_path, "blocking", "safety_not_object", "safety must be an object.")
        safety = {}
    for field, expected in SAFETY_RULES.items():
        if field not in safety:
            _append(findings, file_path, "blocking", f"missing_safety_flag:{field}", f"safety.{field} is required.")
            continue
        value = safety[field]
        if not isinstance(value, bool):
            _append(findings, file_path, "blocking", f"invalid_safety_flag:{field}", f"safety.{field} must be boolean.")
            continue
        if value != expected:
            _append(
                findings,
                file_path,
                "blocking",
                f"unsafe_safety_flag:{field}",
                f"safety.{field} must equal {str(expected).lower()}.",
            )

    findings.sort(key=lambda item: (item["file"], item["severity"], item["code"], item["message"]))
    return findings


def _relative_fixture_path(path, fixtures_dir):
    return str(path.resolve().relative_to(fixtures_dir.resolve())).replace("\\", "/")


def _expectation_for_path(relative_path):
    parts = tuple(relative_path.split("/"))
    if "valid" in parts:
        return "valid"
    if "invalid" in parts:
        return "invalid"
    return "unclassified"


def _iter_fixture_files(fixtures_dir):
    return sorted(path for path in fixtures_dir.rglob("*.json") if path.is_file())


def _normalize_fixtures_dir(fixtures_dir):
    resolved = fixtures_dir.resolve()
    try:
        relative = resolved.relative_to(ROOT.resolve())
    except ValueError:
        return str(resolved).replace("\\", "/")
    return str(relative).replace("\\", "/")


def build_validation_report(fixtures_dir):
    contract = _load_json(CONTRACT_PATH)
    fixtures_dir = fixtures_dir.resolve()
    fixtures_dir_display = _normalize_fixtures_dir(fixtures_dir)
    quarantine_findings = []
    unexpected_failures = []
    unexpected_passes = []
    checked_files_count = 0
    valid_files_count = 0
    invalid_files_count = 0
    safety_detected = {
        "network_used_detected": False,
        "api_credentials_detected": False,
        "wallet_detected": False,
        "order_or_trading_capability_detected": False,
        "runtime_wiring_detected": False,
    }
    unexpected_failures_internal = []

    if not fixtures_dir.exists():
        return {
            "validation_passed": False,
            "contract_version": contract["contract_version"],
            "fixtures_dir": fixtures_dir_display,
            "checked_files_count": 0,
            "valid_files_count": 0,
            "invalid_files_count": 0,
            "unexpected_failures": [],
            "unexpected_passes": [],
            "quarantine_findings": [
                _finding(
                    "fixtures",
                    "blocking",
                    "fixtures_dir_missing",
                    f"Fixtures directory does not exist: {str(fixtures_dir).replace(chr(92), '/')}",
                )
            ],
            "safety_summary": safety_detected,
        }

    for path in _iter_fixture_files(fixtures_dir):
        checked_files_count += 1
        relative_path = _relative_fixture_path(path, fixtures_dir)
        expectation = _expectation_for_path(relative_path)
        try:
            payload = _load_json(path)
            findings = validate_artifact(payload, relative_path)
        except Exception as exc:  # pragma: no cover - defensive path covered by tests via report field
            findings = [
                _finding(
                    relative_path,
                    "blocking",
                    "unexpected_exception",
                    f"{type(exc).__name__}: {exc}",
                )
            ]

        is_valid = not findings
        if is_valid and expectation == "valid":
            valid_files_count += 1
        elif not is_valid and expectation == "invalid":
            invalid_files_count += 1
            quarantine_findings.extend(findings)
        elif not is_valid and expectation == "valid":
            quarantine_findings.extend(findings)
            unexpected_failures.append(
                {
                    "file": relative_path,
                    "codes": [item["code"] for item in findings],
                }
            )
            unexpected_failures_internal.extend(findings)
        elif is_valid and expectation == "invalid":
            invalid_files_count += 1
            unexpected_passes.append(relative_path)
        else:
            quarantine_findings.extend(
                [
                    _finding(
                        relative_path,
                        "blocking",
                        "unclassified_fixture_path",
                        "Fixture path must include either a valid or invalid directory segment.",
                    )
                ]
            )
            unexpected_failures.append({"file": relative_path, "codes": ["unclassified_fixture_path"]})

    signal_map = {
        "unsafe_safety_flag:network_used": "network_used_detected",
        "unsafe_safety_flag:api_credentials_used": "api_credentials_detected",
        "unsafe_safety_flag:wallet_used": "wallet_detected",
        "unsafe_safety_flag:order_capable": "order_or_trading_capability_detected",
        "unsafe_safety_flag:trading_capable": "order_or_trading_capability_detected",
    }
    for finding in unexpected_failures_internal:
        if finding["code"] in signal_map:
            safety_detected[signal_map[finding["code"]]] = True

    quarantine_findings.sort(key=lambda item: (item["file"], item["severity"], item["code"], item["message"]))
    unexpected_failures.sort(key=lambda item: item["file"])
    unexpected_passes.sort()

    return {
        "validation_passed": not unexpected_failures and not unexpected_passes,
        "contract_version": contract["contract_version"],
        "fixtures_dir": fixtures_dir_display,
        "checked_files_count": checked_files_count,
        "valid_files_count": valid_files_count,
        "invalid_files_count": invalid_files_count,
        "unexpected_failures": unexpected_failures,
        "unexpected_passes": unexpected_passes,
        "quarantine_findings": quarantine_findings,
        "safety_summary": safety_detected,
    }


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Validate offline raw market artifact fixtures.")
    parser.add_argument("--fixtures-dir", default=str(DEFAULT_FIXTURES_DIR))
    parser.add_argument("--write-report")
    return parser.parse_args(argv)


def main(argv):
    args = _parse_args(argv)
    fixtures_dir = Path(args.fixtures_dir)
    if not fixtures_dir.is_absolute():
        fixtures_dir = (ROOT / fixtures_dir).resolve()
    report = build_validation_report(fixtures_dir)
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.write_report:
        output_path = Path(args.write_report)
        if not output_path.is_absolute():
            output_path = (ROOT / output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
