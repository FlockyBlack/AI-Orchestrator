import argparse
import json
import re
import sys
from pathlib import Path


TASK_ID = "PMBOT-QUALITY-001-ARTIFACT-HEALTH-AND-STALENESS-CHECK"
SCHEMA_VERSION = "artifact_health_report.v1"
GENERATED_BY = "pm_bot/quality/export_artifact_health_report.py"

ROOT = Path(__file__).resolve().parents[2]
QUALITY_DIR = ROOT / "pm_bot" / "quality"
DOCS_DIR = ROOT / "docs"

DEFAULT_REPORT_JSON = QUALITY_DIR / "artifact_health_report.v1.json"
DEFAULT_REPORT_MD = QUALITY_DIR / "artifact_health_report.v1.md"
DEFAULT_EXPECTED_REPORT_JSON = QUALITY_DIR / "expected_artifact_health_report.v1.json"
DEFAULT_RESULT = DOCS_DIR / "PMBOT_QUALITY_001_RESULT.json"
DEFAULT_LANE_RESULT = DOCS_DIR / "PMBOT_CODEX_B_ROUND003_RESULT.json"

BASE_COMMIT = "21edc9af372e9d1736afb0eccd3c016f23f2c144"
INFRA_009_MAIN_COMMIT = "4ab06bc10bb92639a38875ed94552260d04c45a9"

REQUIRED_CONTEXT_DOCS = (
    "docs/PMBOT_PRODUCT_001_RESULT.json",
    "docs/PMBOT_INTEGRATION_008_RESULT.json",
    "docs/PMBOT_PAPER_018_RESULT.json",
    "docs/PMBOT_DASHBOARD_002_RESULT.json",
    "docs/PMBOT_OPERATOR_002_RESULT.json",
)
OPTIONAL_CONTEXT_DOCS = (
    "docs/PMBOT_INFRA_009_RESULT.json",
)
ARTIFACT_SCAN_DIRS = (
    "pm_bot/paper",
    "pm_bot/dashboard",
    "pm_bot/operator",
)
ARTIFACT_EXTENSIONS = {".json", ".md"}

KNOWN_INTENTIONAL_PARSE_FIXTURE_PATHS = {
    "pm_bot/paper/manual_snapshot_import_source/005_malformed.json",
}

SAFETY_FLAGS = {
    "runtime_wiring": False,
    "network_api": False,
    "wallet": False,
    "trading": False,
    "autonomous_paper_orders": False,
    "scoring_probability_ev_edge": False,
    "market_decisions": False,
    "command_execution": False,
}

WARNING_SEVERITIES = ("blocking", "action_required", "review_needed", "informational")
WARNING_SEVERITY_RANK = {severity: index for index, severity in enumerate(WARNING_SEVERITIES)}
WARNING_SEVERITY_MODEL = {
    "blocking": "Stop operator review and repair the artifact or safety issue first.",
    "action_required": "Review and resolve or explicitly accept before relying on the package.",
    "review_needed": "Inspect as artifact hygiene context; it does not necessarily block review.",
    "informational": "Low-priority context retained for traceability.",
}
WARNING_CATEGORY_MODEL = {
    "missing_required_artifact": {
        "severity": "blocking",
        "operator_bucket": "required artifact missing",
    },
    "json_parse_failed": {
        "severity": "blocking",
        "operator_bucket": "JSON parse failure",
    },
    "fixture_alignment_actual_missing": {
        "severity": "action_required",
        "operator_bucket": "expected fixture exists but actual artifact is missing",
    },
    "fixture_alignment_mismatch": {
        "severity": "action_required",
        "operator_bucket": "expected fixture differs from actual artifact",
    },
    "expected_fixture_alignment_warning": {
        "severity": "action_required",
        "operator_bucket": "artifact has an expected fixture alignment warning",
    },
    "schema_version_missing": {
        "severity": "action_required",
        "operator_bucket": "schema version metadata missing",
    },
    "task_id_missing": {
        "severity": "action_required",
        "operator_bucket": "task_id metadata missing",
    },
    "status_fields_missing": {
        "severity": "action_required",
        "operator_bucket": "expected status field missing",
    },
    "embedded_artifact_pointer_warning": {
        "severity": "review_needed",
        "operator_bucket": "embedded artifact pointer needs inspection",
    },
    "stale_reference_warning": {
        "severity": "review_needed",
        "operator_bucket": "historical or stale reference needs inspection",
    },
    "json_top_level_not_object": {
        "severity": "review_needed",
        "operator_bucket": "JSON artifact is intentionally or structurally non-object",
    },
    "missing_optional_artifact": {
        "severity": "informational",
        "operator_bucket": "optional artifact missing",
    },
    "known_intentional_malformed_fixture_parse_failure": {
        "severity": "informational",
        "operator_bucket": "known intentional malformed fixture",
    },
    "unclassified_warning": {
        "severity": "action_required",
        "operator_bucket": "unclassified warning requires manual review",
    },
}

ZERO_OR_FALSE_SAFETY_FIELDS = {
    "api_used",
    "authenticated_endpoints",
    "autonomous_actions_created",
    "autonomous_paper_orders",
    "autonomous_paper_orders_created",
    "browser_automation",
    "command_execution",
    "commands_executed",
    "credentials",
    "dispatcher_run_codex_changes",
    "edge_calculations",
    "ev_calculations",
    "execution_allowed",
    "execution_authority",
    "frontend",
    "live_order_created",
    "live_orders_created",
    "live_trading",
    "market_decisions",
    "network_api",
    "network_api_calls",
    "network_calls",
    "network_used",
    "orders_created",
    "probability_estimates",
    "real_order_created",
    "real_orders",
    "real_orders_created",
    "recommendations",
    "runtime_wiring",
    "scoring_probability_ev_edge",
    "server",
    "side_recommendations",
    "trading",
    "trading_allowed",
    "trading_endpoints",
    "truth_inference",
    "wallet",
    "wallet_private_keys",
    "wallet_used",
}

TRUE_SAFE_FIELDS = {
    "deterministic",
    "fixture_only",
    "inert_only",
    "local_file_reads_only",
    "local_only",
    "manual_review_only",
    "no_credential_or_endpoint_use",
    "no_live_execution",
    "no_real_execution",
    "offline_only",
    "operator_manual_source_lineage",
    "operator_review_only",
    "paper_accounting_only",
    "paper_only",
    "record_is_inert",
}

COMMIT_RE = re.compile(r"\b[0-9a-f]{40}\b")
ROUND_GENERATION_RE = re.compile(r"\bROUND00[12]\b")


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Build a deterministic local PMBOT artifact health and staleness report."
    )
    parser.add_argument("--write", action="store_true", help="Write JSON, Markdown, fixture, and result docs.")
    parser.add_argument("--markdown", action="store_true", help="Print Markdown instead of JSON.")
    return parser.parse_args(argv)


def _display_path(path, root=ROOT):
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(Path(root).resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def _repo_path(path_text):
    return str(path_text).replace("\\", "/")


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _artifact_inventory_paths(root=ROOT):
    root = Path(root)
    paths = [root / item for item in REQUIRED_CONTEXT_DOCS]
    paths.extend(root / item for item in OPTIONAL_CONTEXT_DOCS)
    for directory in ARTIFACT_SCAN_DIRS:
        base = root / directory
        if not base.exists():
            paths.append(base)
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in ARTIFACT_EXTENSIONS:
                paths.append(path)
    return sorted(set(paths), key=lambda item: _display_path(item, root=root))


def _is_required(path, root=ROOT):
    repo_path = _display_path(path, root=root)
    if repo_path in OPTIONAL_CONTEXT_DOCS:
        return False
    if repo_path in REQUIRED_CONTEXT_DOCS:
        return True
    if repo_path in KNOWN_INTENTIONAL_PARSE_FIXTURE_PATHS:
        return False
    return any(repo_path.startswith(f"{directory}/") for directory in ARTIFACT_SCAN_DIRS)


def _task_id_expected(path, root=ROOT):
    repo_path = _display_path(path, root=root)
    if repo_path.startswith("docs/PMBOT_") and repo_path.endswith("_RESULT.json"):
        return True
    return repo_path.endswith(("_audit.v1.json", "_review.v1.json", "_fixture.v1.json"))


def _status_expected(path, payload, root=ROOT):
    repo_path = _display_path(path, root=root)
    if repo_path.startswith("docs/PMBOT_") and repo_path.endswith("_RESULT.json"):
        return True
    if isinstance(payload, dict):
        return any("status" in key.lower() for key in payload)
    return False


def _status_fields(payload):
    if not isinstance(payload, dict):
        return {}
    return {
        key: payload[key]
        for key in sorted(payload)
        if "status" in key.lower() and isinstance(payload[key], (str, int, bool)) or key.endswith("_status")
    }


def _safe_status_fields(payload):
    if not isinstance(payload, dict):
        return {}
    fields = {}
    for key in sorted(payload):
        if "status" not in key.lower() and not key.endswith("_status"):
            continue
        value = payload[key]
        if isinstance(value, (str, int, bool)) or value is None:
            fields[key] = value
        elif isinstance(value, list):
            fields[key] = f"list[{len(value)}]"
        elif isinstance(value, dict):
            fields[key] = "dict"
        else:
            fields[key] = type(value).__name__
    return fields


def _walk_json(value, prefix=""):
    yield prefix, value
    if isinstance(value, dict):
        for key in sorted(value):
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from _walk_json(value[key], child_prefix)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            child_prefix = f"{prefix}[{index}]"
            yield from _walk_json(item, child_prefix)


def _is_pointer_candidate(field_path, value):
    if not isinstance(value, str):
        return False
    text = value.strip().strip("`")
    if not text or "://" in text:
        return False
    lower_field = field_path.lower()
    lower_text = text.lower().replace("\\", "/")
    has_artifact_extension = lower_text.endswith(".json") or lower_text.endswith(".md")
    looks_like_path_field = (
        "path" in lower_field
        or "pointer" in lower_field
        or "artifact" in lower_field
        or lower_text.startswith(("docs/", "pm_bot/", "local_snapshots/"))
    )
    return has_artifact_extension and looks_like_path_field


def _resolve_pointer_target(source_path, pointer_text, root=ROOT):
    raw = pointer_text.strip().strip("`")
    normalized = _repo_path(raw)
    value = Path(raw)
    is_absolute = value.is_absolute()
    if is_absolute:
        return value, normalized, True
    if normalized.startswith(("docs/", "pm_bot/", "local_snapshots/", "schemas/")):
        return Path(root) / normalized, normalized, False
    return Path(source_path).parent / raw, _display_path(Path(source_path).parent / raw, root=root), False


def _embedded_pointer_health(path, payload, root=ROOT):
    pointers = []
    seen = set()
    if payload is None:
        return {"checked_count": 0, "present_count": 0, "missing_count": 0, "absolute_count": 0, "pointers": []}
    for field_path, value in _walk_json(payload):
        if not _is_pointer_candidate(field_path, value):
            continue
        target_path, normalized, is_absolute = _resolve_pointer_target(path, value, root=root)
        key = (field_path, normalized)
        if key in seen:
            continue
        seen.add(key)
        exists = target_path.exists()
        pointers.append(
            {
                "field_path": field_path,
                "target": normalized,
                "exists": exists,
                "pointer_scope": "absolute" if is_absolute else "relative",
            }
        )
    pointers.sort(key=lambda item: (item["field_path"], item["target"]))
    return {
        "checked_count": len(pointers),
        "present_count": sum(1 for item in pointers if item["exists"]),
        "missing_count": sum(1 for item in pointers if not item["exists"]),
        "absolute_count": sum(1 for item in pointers if item["pointer_scope"] == "absolute"),
        "pointers": pointers,
    }


def _safety_fields(payload):
    fields = {}
    if not isinstance(payload, dict):
        return fields
    for key, value in payload.items():
        lower_key = key.lower()
        if lower_key in ZERO_OR_FALSE_SAFETY_FIELDS or lower_key in TRUE_SAFE_FIELDS:
            fields[key] = value
    nested = payload.get("safety_flags")
    if isinstance(nested, dict):
        for key in sorted(nested):
            lower_key = key.lower()
            if lower_key in ZERO_OR_FALSE_SAFETY_FIELDS or lower_key in TRUE_SAFE_FIELDS:
                fields[f"safety_flags.{key}"] = nested[key]
    elif isinstance(nested, list):
        fields["safety_flags"] = list(nested)
    safety = payload.get("safety")
    if isinstance(safety, dict):
        for key in sorted(safety):
            lower_key = key.lower()
            if lower_key in ZERO_OR_FALSE_SAFETY_FIELDS or lower_key in TRUE_SAFE_FIELDS:
                fields[f"safety.{key}"] = safety[key]
    return fields


def _safety_value_is_expected_false_or_zero(field, value):
    normalized_field = field.split(".")[-1].lower()
    if normalized_field in TRUE_SAFE_FIELDS:
        return value is True
    if value is False or value == 0:
        return True
    if value is None:
        return True
    if isinstance(value, list):
        return True
    return False


def _stale_references(path, payload, root=ROOT):
    references = []
    if payload is None:
        return references
    for field_path, value in _walk_json(payload):
        if isinstance(value, str):
            for commit in COMMIT_RE.findall(value):
                if commit not in {BASE_COMMIT, INFRA_009_MAIN_COMMIT}:
                    references.append(
                        {
                            "field_path": field_path,
                            "value": commit,
                            "classification": "historical_or_non_current_commit_reference",
                        }
                    )
            if ROUND_GENERATION_RE.search(value):
                references.append(
                    {
                        "field_path": field_path,
                        "value": value,
                        "classification": "historical_round_generation_reference",
                    }
                )
    references.sort(key=lambda item: (item["classification"], item["field_path"], item["value"]))
    return references


def _artifact_record(path, root=ROOT):
    path = Path(path)
    repo_path = _display_path(path, root=root)
    required = _is_required(path, root=root)
    record = {
        "path": repo_path,
        "artifact_type": path.suffix.lower().removeprefix(".") or "directory",
        "required": required,
        "exists": path.exists(),
        "json_parse_status": "not_json",
        "schema_version_present": False,
        "schema_version": None,
        "task_id_expected": False,
        "task_id_present": False,
        "task_id": None,
        "status_fields_expected": False,
        "status_fields_present": False,
        "status_fields": {},
        "embedded_artifact_pointer_health": {
            "checked_count": 0,
            "present_count": 0,
            "missing_count": 0,
            "absolute_count": 0,
        },
        "expected_fixture_alignment": "not_applicable",
        "safety_fields": {},
        "warnings": [],
    }
    payload = None
    if not path.exists():
        record["json_parse_status"] = "missing"
        record["warnings"].append("missing_required_artifact" if required else "missing_optional_artifact")
        return record, payload
    if path.suffix.lower() != ".json":
        return record, payload
    try:
        payload = _load_json(path)
        record["json_parse_status"] = "parsed"
    except json.JSONDecodeError as exc:
        record["json_parse_status"] = "parse_failed"
        record["json_parse_error"] = f"{exc.msg} at line {exc.lineno} column {exc.colno}"
        if repo_path in KNOWN_INTENTIONAL_PARSE_FIXTURE_PATHS:
            record["warnings"].append("known_intentional_malformed_fixture_parse_failure")
        else:
            record["warnings"].append("json_parse_failed")
        return record, None

    if isinstance(payload, dict):
        record["schema_version_present"] = "schema_version" in payload
        record["schema_version"] = payload.get("schema_version")
        record["task_id_expected"] = _task_id_expected(path, root=root)
        record["task_id_present"] = isinstance(payload.get("task_id"), str) and bool(payload.get("task_id"))
        record["task_id"] = payload.get("task_id")
        record["status_fields_expected"] = _status_expected(path, payload, root=root)
        record["status_fields"] = _safe_status_fields(payload)
        record["status_fields_present"] = bool(record["status_fields"])
        record["safety_fields"] = _safety_fields(payload)
        if not record["schema_version_present"]:
            record["warnings"].append("schema_version_missing")
        if record["task_id_expected"] and not record["task_id_present"]:
            record["warnings"].append("task_id_missing")
        if record["status_fields_expected"] and not record["status_fields_present"]:
            record["warnings"].append("status_fields_missing")
    else:
        record["warnings"].append("json_top_level_not_object")

    pointer_health = _embedded_pointer_health(path, payload, root=root)
    record["embedded_artifact_pointer_health"] = {
        "checked_count": pointer_health["checked_count"],
        "present_count": pointer_health["present_count"],
        "missing_count": pointer_health["missing_count"],
        "absolute_count": pointer_health["absolute_count"],
    }
    pointer_warnings = []
    for pointer in pointer_health["pointers"]:
        if not pointer["exists"]:
            pointer_warnings.append(
                {
                    "warning_type": "embedded_artifact_pointer_missing",
                    "field_path": pointer["field_path"],
                    "target": pointer["target"],
                }
            )
        if pointer["pointer_scope"] == "absolute":
            pointer_warnings.append(
                {
                    "warning_type": "embedded_artifact_pointer_absolute",
                    "field_path": pointer["field_path"],
                    "target": pointer["target"],
                }
            )
    if pointer_warnings:
        record["pointer_warnings"] = pointer_warnings
        record["warnings"].append("embedded_artifact_pointer_warning")

    stale = _stale_references(path, payload, root=root)
    if stale:
        record["stale_reference_warnings"] = stale
        record["warnings"].append("stale_reference_warning")
    return record, payload


def _expected_counterpart(path):
    path = Path(path)
    name = path.name
    if not name.startswith("expected_"):
        return None
    return path.with_name(name.removeprefix("expected_"))


def _fixture_alignment(paths, payloads, root=ROOT):
    checks = []
    path_set = {Path(path).resolve() for path in paths}
    for path in sorted(paths, key=lambda item: _display_path(item, root=root)):
        counterpart = _expected_counterpart(path)
        if counterpart is None or path.suffix.lower() not in {".json", ".md"}:
            continue
        repo_expected = _display_path(path, root=root)
        repo_actual = _display_path(counterpart, root=root)
        if counterpart.resolve() not in path_set and not counterpart.exists():
            checks.append(
                {
                    "expected_path": repo_expected,
                    "actual_path": repo_actual,
                    "artifact_type": path.suffix.lower().removeprefix("."),
                    "alignment_status": "actual_missing",
                }
            )
            continue
        if path.suffix.lower() == ".json":
            expected_payload = payloads.get(repo_expected)
            actual_payload = payloads.get(repo_actual)
            if expected_payload is None or actual_payload is None:
                status = "not_checked_parse_failed_or_non_object"
            else:
                status = "aligned" if expected_payload == actual_payload else "mismatch"
        else:
            try:
                status = "aligned" if Path(path).read_text(encoding="utf-8") == counterpart.read_text(encoding="utf-8") else "mismatch"
            except OSError:
                status = "not_checked_read_failed"
        checks.append(
            {
                "expected_path": repo_expected,
                "actual_path": repo_actual,
                "artifact_type": path.suffix.lower().removeprefix("."),
                "alignment_status": status,
            }
        )
    return checks


def _safety_flag_summary(artifact_records):
    observed = {}
    unexpected_values = []
    for record in artifact_records:
        for key, value in record.get("safety_fields", {}).items():
            entry = observed.setdefault(
                key,
                {
                    "present_count": 0,
                    "expected_false_or_zero_count": 0,
                    "unexpected_values": [],
                },
            )
            entry["present_count"] += 1
            if _safety_value_is_expected_false_or_zero(key, value):
                entry["expected_false_or_zero_count"] += 1
            else:
                unexpected = {
                    "path": record["path"],
                    "field": key,
                    "value": value,
                }
                entry["unexpected_values"].append(unexpected)
                unexpected_values.append(unexpected)
    return {
        "report_safety_flags": dict(SAFETY_FLAGS),
        "observed_artifact_safety_fields": dict(sorted(observed.items())),
        "unexpected_true_or_nonzero_values": unexpected_values,
    }


def _report_status(artifact_records, fixture_checks, safety_summary):
    blocking = []
    warnings = []
    for record in artifact_records:
        if record["required"] and not record["exists"]:
            blocking.append(f"missing required artifact: {record['path']}")
        if (
            record["required"]
            and record["json_parse_status"] == "parse_failed"
            and record["path"] not in KNOWN_INTENTIONAL_PARSE_FIXTURE_PATHS
        ):
            blocking.append(f"required JSON parse failed: {record['path']}")
        for warning in record["warnings"]:
            warnings.append(f"{record['path']}: {warning}")
    for check in fixture_checks:
        if check["alignment_status"] in {"mismatch", "actual_missing"}:
            warnings.append(
                f"{check['expected_path']} fixture alignment {check['alignment_status']} with {check['actual_path']}"
            )
    for item in safety_summary["unexpected_true_or_nonzero_values"]:
        blocking.append(f"unexpected safety value {item['path']} {item['field']}={item['value']}")
    if blocking:
        return "health_failed", blocking, warnings
    if warnings:
        return "health_passed_with_warnings", [], warnings
    return "health_passed", [], []


def _warning_path(warning):
    if " fixture alignment " in warning:
        return warning.split(" fixture alignment ", 1)[0]
    if ": " in warning:
        return warning.split(": ", 1)[0]
    return None


def _warning_category(warning):
    if " fixture alignment " in warning:
        if " actual_missing " in warning:
            return "fixture_alignment_actual_missing"
        if " mismatch " in warning:
            return "fixture_alignment_mismatch"
        return "expected_fixture_alignment_warning"
    tag = warning.rsplit(": ", 1)[-1]
    if tag in WARNING_CATEGORY_MODEL:
        return tag
    return "unclassified_warning"


def _warning_severity(category, path, required_by_path):
    model = WARNING_CATEGORY_MODEL.get(category, WARNING_CATEGORY_MODEL["unclassified_warning"])
    severity = model["severity"]
    required = bool(path and required_by_path.get(path))
    if category == "json_parse_failed" and not required:
        return "action_required"
    if category in {"schema_version_missing", "task_id_missing", "status_fields_missing"} and not required:
        return "review_needed"
    return severity


def _highest_severity(severity_counts):
    for severity in WARNING_SEVERITIES:
        if severity_counts.get(severity, 0):
            return severity
    return "informational"


def _warning_operator_summary(severity_counts, blockers):
    if severity_counts["blocking"] or blockers:
        return "Blocking quality warning detected; stop and repair blocking artifact or safety issues first."
    if severity_counts["action_required"]:
        return "No blocking warnings detected; review action_required categories before relying on the package."
    if severity_counts["review_needed"]:
        return "No blocking or action_required warnings detected; inspect review_needed categories as artifact hygiene context."
    if severity_counts["informational"]:
        return "Only informational warnings detected; keep details for traceability."
    return "No quality warnings detected."


def _recommended_manual_action(severity_counts, blockers):
    if severity_counts["blocking"] or blockers:
        return "Stop operator review and repair blocking warnings or blockers before continuing."
    if severity_counts["action_required"]:
        return "Review action_required warning categories first, then inspect review_needed and informational categories."
    if severity_counts["review_needed"]:
        return "Inspect review_needed warning categories and keep detailed warnings available for follow-up cleanup."
    if severity_counts["informational"]:
        return "Record informational context and continue manual review."
    return "Continue manual review with no quality warning follow-up required."


def _warning_severity_summary(warnings, artifact_records, blockers):
    required_by_path = {record["path"]: record["required"] for record in artifact_records}
    severity_counts = {severity: 0 for severity in WARNING_SEVERITIES}
    category_counts = {}
    category_severity_counts = {}

    for warning in warnings:
        path = _warning_path(warning)
        category = _warning_category(warning)
        severity = _warning_severity(category, path, required_by_path)
        severity_counts[severity] += 1
        category_counts[category] = category_counts.get(category, 0) + 1
        per_category = category_severity_counts.setdefault(
            category,
            {item: 0 for item in WARNING_SEVERITIES},
        )
        per_category[severity] += 1

    categories = []
    for category in sorted(category_counts):
        model = WARNING_CATEGORY_MODEL.get(category, WARNING_CATEGORY_MODEL["unclassified_warning"])
        per_category = category_severity_counts[category]
        categories.append(
            {
                "category": category,
                "severity": _highest_severity(per_category),
                "count": category_counts[category],
                "severity_counts": per_category,
                "operator_bucket": model["operator_bucket"],
            }
        )
    categories.sort(
        key=lambda item: (
            -item["count"],
            WARNING_SEVERITY_RANK[item["severity"]],
            item["category"],
        )
    )

    summary = {
        "total_warnings": len(warnings),
        "blocking_count": severity_counts["blocking"],
        "action_required_count": severity_counts["action_required"],
        "review_needed_count": severity_counts["review_needed"],
        "informational_count": severity_counts["informational"],
        "warning_categories": categories,
        "top_warning_categories": categories[:5],
        "blocking_warning_detected": bool(severity_counts["blocking"] or blockers),
        "operator_summary": _warning_operator_summary(severity_counts, blockers),
        "recommended_manual_action": _recommended_manual_action(severity_counts, blockers),
        "severity_model": WARNING_SEVERITY_MODEL,
    }
    return summary


def build_artifact_health_report(root=ROOT):
    root = Path(root)
    paths = _artifact_inventory_paths(root)
    artifact_records = []
    payloads = {}
    for path in paths:
        record, payload = _artifact_record(path, root=root)
        artifact_records.append(record)
        if payload is not None:
            payloads[record["path"]] = payload
    fixture_checks = _fixture_alignment(paths, payloads, root=root)
    fixture_by_expected = {check["expected_path"]: check for check in fixture_checks}
    for record in artifact_records:
        check = fixture_by_expected.get(record["path"])
        if check:
            record["expected_fixture_alignment"] = check["alignment_status"]
            if check["alignment_status"] in {"mismatch", "actual_missing"}:
                record["warnings"].append("expected_fixture_alignment_warning")

    safety_summary = _safety_flag_summary(artifact_records)
    status, blockers, warnings = _report_status(artifact_records, fixture_checks, safety_summary)
    warning_summary = _warning_severity_summary(warnings, artifact_records, blockers)
    parse_pass = sum(1 for record in artifact_records if record["json_parse_status"] == "parsed")
    parse_fail = sum(1 for record in artifact_records if record["json_parse_status"] == "parse_failed")
    stale_pointer_warnings = []
    for record in artifact_records:
        for warning in record.get("pointer_warnings", []):
            stale_pointer_warnings.append({"path": record["path"], **warning})
        for warning in record.get("stale_reference_warnings", []):
            stale_pointer_warnings.append({"path": record["path"], **warning})
    stale_pointer_warnings.sort(key=lambda item: (item["path"], item.get("warning_type", item.get("classification", "")), item["field_path"]))

    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_policy": {
            "wall_clock_time_used": False,
            "policy": "deterministic_static_local_inventory_no_current_time",
            "fixed_value": "not_emitted",
        },
        "base_commit": BASE_COMMIT,
        "known_post_base_infra_009_doc_commit": INFRA_009_MAIN_COMMIT,
        "inventory_scope": {
            "required_context_docs": list(REQUIRED_CONTEXT_DOCS),
            "optional_context_docs": list(OPTIONAL_CONTEXT_DOCS),
            "artifact_scan_dirs": list(ARTIFACT_SCAN_DIRS),
            "local_file_reads_only": True,
            "network_api": False,
            "runtime_wiring": False,
        },
        "artifacts_checked": len(artifact_records),
        "artifacts_present_count": sum(1 for record in artifact_records if record["exists"]),
        "artifacts_missing_count": sum(1 for record in artifact_records if not record["exists"]),
        "json_parse_pass_count": parse_pass,
        "json_parse_fail_count": parse_fail,
        "schema_version_missing_count": sum(
            1
            for record in artifact_records
            if record["json_parse_status"] == "parsed" and not record["schema_version_present"]
        ),
        "task_id_missing_where_expected_count": sum(
            1
            for record in artifact_records
            if record["json_parse_status"] == "parsed"
            and record["task_id_expected"]
            and not record["task_id_present"]
        ),
        "status_fields_missing_where_expected_count": sum(
            1
            for record in artifact_records
            if record["json_parse_status"] == "parsed"
            and record["status_fields_expected"]
            and not record["status_fields_present"]
        ),
        "embedded_artifact_pointer_summary": {
            "checked_count": sum(
                record["embedded_artifact_pointer_health"]["checked_count"] for record in artifact_records
            ),
            "present_count": sum(
                record["embedded_artifact_pointer_health"]["present_count"] for record in artifact_records
            ),
            "missing_count": sum(
                record["embedded_artifact_pointer_health"]["missing_count"] for record in artifact_records
            ),
            "absolute_count": sum(
                record["embedded_artifact_pointer_health"]["absolute_count"] for record in artifact_records
            ),
        },
        "expected_fixture_alignment_summary": {
            "checks_total": len(fixture_checks),
            "aligned_count": sum(1 for check in fixture_checks if check["alignment_status"] == "aligned"),
            "mismatch_count": sum(1 for check in fixture_checks if check["alignment_status"] == "mismatch"),
            "actual_missing_count": sum(1 for check in fixture_checks if check["alignment_status"] == "actual_missing"),
            "checks": fixture_checks,
        },
        "safety_flag_summary": safety_summary,
        "stale_pointer_warnings": stale_pointer_warnings,
        "warning_severity_summary": warning_summary,
        "warnings": warnings,
        "blockers": blockers,
        "report_status": status,
        "artifacts": artifact_records,
    }


def render_markdown(report):
    pointer_summary = report["embedded_artifact_pointer_summary"]
    fixture_summary = report["expected_fixture_alignment_summary"]
    safety = report["safety_flag_summary"]
    warning_summary = report["warning_severity_summary"]
    lines = [
        "# PMBOT Artifact Health Report v1",
        "",
        f"- task_id: {report['task_id']}",
        f"- schema_version: {report['schema_version']}",
        f"- generated_by: {report['generated_by']}",
        f"- report_status: {report['report_status']}",
        f"- artifacts_checked: {report['artifacts_checked']}",
        f"- artifacts_present_count: {report['artifacts_present_count']}",
        f"- artifacts_missing_count: {report['artifacts_missing_count']}",
        f"- json_parse_pass_count: {report['json_parse_pass_count']}",
        f"- json_parse_fail_count: {report['json_parse_fail_count']}",
        f"- schema_version_missing_count: {report['schema_version_missing_count']}",
        f"- task_id_missing_where_expected_count: {report['task_id_missing_where_expected_count']}",
        f"- status_fields_missing_where_expected_count: {report['status_fields_missing_where_expected_count']}",
        "",
        "## Warning Severity Summary",
        "",
        f"- total_warnings: {warning_summary['total_warnings']}",
        f"- blocking_count: {warning_summary['blocking_count']}",
        f"- action_required_count: {warning_summary['action_required_count']}",
        f"- review_needed_count: {warning_summary['review_needed_count']}",
        f"- informational_count: {warning_summary['informational_count']}",
        f"- blocking_warning_detected: {str(warning_summary['blocking_warning_detected']).lower()}",
        f"- operator_summary: {warning_summary['operator_summary']}",
        f"- recommended_manual_action: {warning_summary['recommended_manual_action']}",
        "",
        "## Top Warning Categories",
        "",
    ]
    if warning_summary["top_warning_categories"]:
        for item in warning_summary["top_warning_categories"]:
            lines.append(
                "- "
                f"{item['category']}: count={item['count']}, severity={item['severity']}, "
                f"bucket={item['operator_bucket']}"
            )
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Warning Severity Model",
            "",
        ]
    )
    for severity in WARNING_SEVERITIES:
        lines.append(f"- {severity}: {warning_summary['severity_model'][severity]}")
    lines.extend(
        [
            "",
            "## Embedded Pointer Health",
            "",
            f"- checked_count: {pointer_summary['checked_count']}",
            f"- present_count: {pointer_summary['present_count']}",
            f"- missing_count: {pointer_summary['missing_count']}",
            f"- absolute_count: {pointer_summary['absolute_count']}",
            "",
            "## Expected Fixture Alignment",
            "",
            f"- checks_total: {fixture_summary['checks_total']}",
            f"- aligned_count: {fixture_summary['aligned_count']}",
            f"- mismatch_count: {fixture_summary['mismatch_count']}",
            f"- actual_missing_count: {fixture_summary['actual_missing_count']}",
            "",
            "## Safety Flags",
            "",
        ]
    )
    for key in sorted(safety["report_safety_flags"]):
        lines.append(f"- {key}: {str(safety['report_safety_flags'][key]).lower()}")
    lines.extend(["", "## Warnings", ""])
    if report["warnings"]:
        lines.extend(f"- {warning}" for warning in report["warnings"])
    else:
        lines.append("- none")
    lines.extend(["", "## Artifacts", ""])
    for artifact in report["artifacts"]:
        lines.append(
            "- "
            f"{artifact['path']}: exists={str(artifact['exists']).lower()}, "
            f"json_parse_status={artifact['json_parse_status']}, "
            f"schema_version={artifact['schema_version']}, "
            f"warnings={len(artifact['warnings'])}"
        )
    lines.append("")
    return "\n".join(lines)


def _result_payload(report):
    completed = report["report_status"] != "health_failed"
    return {
        "task_id": TASK_ID,
        "codex_lane": "CODEX_B",
        "status": "completed_ready_for_review" if completed else "blocked",
        "summary": "Implemented deterministic local artifact health and staleness inventory check.",
        "branch": "codex/b-artifact-health-staleness-round003",
        "worktree_path": "C:\\Users\\OpenC\\Documents\\AI-Orchestrator-worktrees\\CODEX_B_round003_artifact_health",
        "base_commit": BASE_COMMIT,
        "head_commit": None,
        "files_created": [
            "pm_bot/quality/export_artifact_health_report.py",
            "pm_bot/quality/artifact_health_report.v1.json",
            "pm_bot/quality/artifact_health_report.v1.md",
            "pm_bot/quality/expected_artifact_health_report.v1.json",
            "pm_bot/quality/tests/test_artifact_health_report.py",
            "docs/PMBOT_QUALITY_001_RESULT.json",
            "docs/PMBOT_CODEX_B_ROUND003_RESULT.json",
        ],
        "files_modified": [],
        "tests": [],
        "artifact_health": {
            "report_status": report["report_status"],
            "artifacts_checked": report["artifacts_checked"],
            "warnings": len(report["warnings"]),
        },
        "safety_flags": dict(SAFETY_FLAGS),
        "forbidden_changes_detected": False,
        "pushed": "reported_in_task_final_response",
        "blockers": report["blockers"],
        "next_action": "ready_for_integration_review" if completed else "requires_quality_review",
    }


def write_artifact_health_report():
    report = build_artifact_health_report(ROOT)
    _write_json(DEFAULT_REPORT_JSON, report)
    _write_json(DEFAULT_EXPECTED_REPORT_JSON, report)
    _write_text(DEFAULT_REPORT_MD, render_markdown(report))
    result = _result_payload(report)
    _write_json(DEFAULT_RESULT, result)
    _write_json(DEFAULT_LANE_RESULT, result)
    return {
        "task_id": TASK_ID,
        "report_status": report["report_status"],
        "artifacts_checked": report["artifacts_checked"],
        "warnings": len(report["warnings"]),
        "blockers": report["blockers"],
        "result_path": _display_path(DEFAULT_RESULT),
    }


def main(argv):
    args = _parse_args(argv)
    if args.write:
        print(json.dumps(write_artifact_health_report(), indent=2, ensure_ascii=True))
        return 0
    report = build_artifact_health_report(ROOT)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0 if report["report_status"] != "health_failed" else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
