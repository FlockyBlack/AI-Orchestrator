import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


TASK_ID = "PMBOT-QUALITY-002-WARNING-HYGIENE-OWNER-ACTION-PATHS"
SCHEMA_VERSION = "warning_hygiene_owner_action_paths.v1"
GENERATED_BY = "pm_bot/quality/build_warning_hygiene_owner_action_paths.py"

ROOT = Path(__file__).resolve().parents[2]
QUALITY_DIR = ROOT / "pm_bot" / "quality"
DOCS_DIR = ROOT / "docs"

SOURCE_REPORT_JSON = QUALITY_DIR / "artifact_health_report.v1.json"
DEFAULT_REPORT_JSON = QUALITY_DIR / "warning_hygiene_owner_action_paths.v1.json"
DEFAULT_REPORT_MD = QUALITY_DIR / "warning_hygiene_owner_action_paths.v1.md"
DEFAULT_EXPECTED_REPORT_JSON = QUALITY_DIR / "expected_warning_hygiene_owner_action_paths.v1.json"
DEFAULT_RESULT = DOCS_DIR / "PMBOT_QUALITY_002_RESULT.json"

SEVERITIES = ("blocking", "action_required", "review_needed", "informational")
EXPECTED_STATUSES = ("current", "legacy", "stale", "expected_gap", "needs_cleanup", "needs_review")
SAFETY_RELEVANCE = (
    "none",
    "boundary_related",
    "execution_related",
    "data_integrity_related",
    "operator_usability_related",
)

CATEGORY_POLICY = {
    "missing_required_artifact": {
        "action_type": "inspect",
        "expected_status": "current",
        "safety_relevance": "operator_usability_related",
        "deferrable": False,
        "recommended_operator_action": "Stop review for this artifact and ask the maintainer to restore it.",
        "recommended_maintainer_action": "Restore or regenerate the missing required artifact.",
        "rationale": "A required artifact is absent, so the operator cannot verify that part of the package.",
    },
    "json_parse_failed": {
        "action_type": "inspect",
        "expected_status": "needs_cleanup",
        "safety_relevance": "data_integrity_related",
        "deferrable": False,
        "recommended_operator_action": "Do not rely on the malformed artifact until it is repaired or documented.",
        "recommended_maintainer_action": "Repair the JSON or document why the malformed fixture is intentional.",
        "rationale": "Malformed JSON blocks deterministic inspection unless it is an intentional fixture.",
    },
    "known_intentional_malformed_fixture_parse_failure": {
        "action_type": "document_exception",
        "expected_status": "expected_gap",
        "safety_relevance": "none",
        "deferrable": True,
        "recommended_operator_action": "No operator action is expected unless the fixture stops being intentional.",
        "recommended_maintainer_action": "Keep the intentional malformed fixture documented in tests.",
        "rationale": "The parse failure is a known fixture used to verify error handling.",
    },
    "fixture_alignment_actual_missing": {
        "action_type": "update_fixture",
        "expected_status": "needs_cleanup",
        "safety_relevance": "operator_usability_related",
        "deferrable": False,
        "recommended_operator_action": "Treat this as cleanup debt; local MVP usage is not blocked when no blocking warnings exist.",
        "recommended_maintainer_action": "Create or regenerate the missing actual artifact that corresponds to the expected fixture.",
        "rationale": "Expected fixtures without actual artifacts make review noisy and harder to route.",
    },
    "fixture_alignment_mismatch": {
        "action_type": "update_fixture",
        "expected_status": "needs_review",
        "safety_relevance": "data_integrity_related",
        "deferrable": False,
        "recommended_operator_action": "Ask the maintainer to confirm whether the expected fixture or actual artifact is authoritative.",
        "recommended_maintainer_action": "Regenerate the expected fixture or fix the actual artifact after review.",
        "rationale": "A mismatch can indicate stale expected data or an unintended artifact change.",
    },
    "expected_fixture_alignment_warning": {
        "action_type": "update_fixture",
        "expected_status": "needs_cleanup",
        "safety_relevance": "operator_usability_related",
        "deferrable": False,
        "recommended_operator_action": "Use as a cleanup queue; do not treat it as an MVP blocker when severity is not blocking.",
        "recommended_maintainer_action": "Align expected fixtures with current deterministic artifacts.",
        "rationale": "Fixture alignment warnings are maintainer-owned hygiene tasks, not hidden warning reductions.",
    },
    "schema_version_missing": {
        "action_type": "add_missing_metadata",
        "expected_status": "expected_gap",
        "safety_relevance": "operator_usability_related",
        "deferrable": False,
        "recommended_operator_action": "Route to the artifact owner; local MVP usage can continue if no blocking warnings exist.",
        "recommended_maintainer_action": "Add schema_version metadata or document why this artifact predates the convention.",
        "rationale": "Schema metadata lets operators compare artifacts and expected fixtures deterministically.",
    },
    "task_id_missing": {
        "action_type": "add_missing_metadata",
        "expected_status": "expected_gap",
        "safety_relevance": "operator_usability_related",
        "deferrable": False,
        "recommended_operator_action": "Route to the artifact owner for metadata cleanup.",
        "recommended_maintainer_action": "Add task_id metadata or document the legacy exception.",
        "rationale": "Task IDs make warning ownership and artifact lineage explicit.",
    },
    "status_fields_missing": {
        "action_type": "add_missing_metadata",
        "expected_status": "expected_gap",
        "safety_relevance": "operator_usability_related",
        "deferrable": False,
        "recommended_operator_action": "Ask the maintainer to add an operator-readable status field.",
        "recommended_maintainer_action": "Add status, report_status, acceptance_verdict, or an equivalent explicit status field.",
        "rationale": "Status metadata helps the operator understand whether an artifact is usable.",
    },
    "embedded_artifact_pointer_warning": {
        "action_type": "normalize_legacy_artifact",
        "expected_status": "stale",
        "safety_relevance": "operator_usability_related",
        "deferrable": True,
        "recommended_operator_action": "Defer for MVP use unless it repeats in a current decision path.",
        "recommended_maintainer_action": "Remove stale embedded artifact pointers or update them to current paths.",
        "rationale": "Stale embedded pointers create review noise but do not change execution behavior.",
    },
    "stale_reference_warning": {
        "action_type": "archive_or_mark_legacy",
        "expected_status": "stale",
        "safety_relevance": "operator_usability_related",
        "deferrable": True,
        "recommended_operator_action": "Defer if the referenced artifact is not part of the current MVP path.",
        "recommended_maintainer_action": "Archive, mark legacy, or update stale references.",
        "rationale": "Historical references should be visible without blocking current local review.",
    },
    "json_top_level_not_object": {
        "action_type": "document_exception",
        "expected_status": "needs_review",
        "safety_relevance": "data_integrity_related",
        "deferrable": True,
        "recommended_operator_action": "Inspect only if this artifact is needed for the current operator review.",
        "recommended_maintainer_action": "Document the non-object JSON shape or normalize the artifact.",
        "rationale": "Non-object JSON may be intentional, but it needs explicit review metadata.",
    },
    "missing_optional_artifact": {
        "action_type": "no_action_expected",
        "expected_status": "expected_gap",
        "safety_relevance": "none",
        "deferrable": True,
        "recommended_operator_action": "No action is expected for optional artifacts.",
        "recommended_maintainer_action": "Leave missing if optional, or update inventory if the artifact became required.",
        "rationale": "Optional missing artifacts are retained for traceability.",
    },
    "unclassified_warning": {
        "action_type": "escalate_if_repeated",
        "expected_status": "needs_review",
        "safety_relevance": "operator_usability_related",
        "deferrable": False,
        "recommended_operator_action": "Ask the maintainer to classify the warning before relying on it.",
        "recommended_maintainer_action": "Add a deterministic hygiene policy for the warning category.",
        "rationale": "Unclassified warnings should not remain ownerless.",
    },
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Build deterministic PMBOT warning hygiene owner/action paths.")
    parser.add_argument("--write", action="store_true", help="Write JSON, Markdown, expected fixture, and result docs.")
    parser.add_argument("--markdown", action="store_true", help="Print Markdown instead of JSON.")
    return parser.parse_args(argv)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_source_report(path=SOURCE_REPORT_JSON):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _source_path(warning):
    return warning.get("path") or "unknown"


def _source_artifact(source_path):
    if source_path == "unknown":
        return "unknown"
    return Path(source_path).name


def _owner_for_path(source_path):
    path = source_path.replace("\\", "/")
    name = Path(path).name
    if path.startswith("pm_bot/quality") or name.startswith(("artifact_health_report", "expected_artifact_health_report")):
        return "quality"
    if path.startswith("pm_bot/workbench") or "WORKBENCH" in name:
        return "workbench"
    if path.startswith("pm_bot/paper") or "PAPER" in name:
        return "paper"
    if path.startswith("pm_bot/dashboard") or "DASHBOARD" in name:
        return "dashboard"
    if path.startswith("pm_bot/operator") or "OPERATOR" in name:
        return "operator"
    if path.startswith("pm_bot/ingest") or "INGEST" in name:
        return "ingest"
    if path.startswith("pm_bot/research") or "RESEARCH" in name:
        return "research"
    if "PRODUCT" in name:
        return "product"
    if "INFRA" in name:
        return "infra"
    if path.startswith("docs/"):
        return "docs"
    return "unknown"


def _owner_type(category, source_path):
    if "fixture" in category:
        return "fixture_maintenance"
    if category in {"schema_version_missing", "task_id_missing", "status_fields_missing"}:
        return "artifact_metadata"
    if "stale" in category or "pointer" in category:
        return "legacy_reference_cleanup"
    if category.startswith("json_"):
        return "artifact_shape"
    if source_path.startswith("docs/"):
        return "docs_artifact_owner"
    return "artifact_owner"


def _action_path(source_path, action_type):
    return f"{action_type}:{source_path}"


def _bucket_id(owner, category, severity, action_type, expected_status, safety_relevance):
    return "|".join((owner, category, severity, action_type, expected_status, safety_relevance))


def _empty_summary():
    return {
        "owner": {},
        "category": {},
        "severity": {severity: 0 for severity in SEVERITIES},
        "expected_status": {status: 0 for status in EXPECTED_STATUSES},
        "action_type": {},
        "safety_relevance": {value: 0 for value in SAFETY_RELEVANCE},
        "deferrable": {"true": 0, "false": 0},
    }


def _increment_summary(summary, record):
    for key, value in (
        ("owner", record["owner"]),
        ("category", record["warning_category"]),
        ("severity", record["severity"]),
        ("expected_status", record["expected_status"]),
        ("action_type", record["action_type"]),
        ("safety_relevance", record["safety_relevance"]),
    ):
        summary[key][value] = summary[key].get(value, 0) + 1
    summary["deferrable"][str(record["deferrable"]).lower()] += 1


def _warning_record(index, warning):
    category = warning.get("category") or "unclassified_warning"
    policy = CATEGORY_POLICY.get(category, CATEGORY_POLICY["unclassified_warning"])
    source_path = _source_path(warning)
    severity = warning.get("severity") or "action_required"
    owner = _owner_for_path(source_path)
    owner_type = _owner_type(category, source_path)
    action_type = policy["action_type"]
    safety_relevance = policy["safety_relevance"]
    expected_status = policy["expected_status"]
    bucket_id = _bucket_id(owner, category, severity, action_type, expected_status, safety_relevance)
    warning_id = warning.get("warning_id") or f"warning_{index:03d}"
    return {
        "warning_id": warning_id,
        "bucket_id": bucket_id,
        "source_artifact": _source_artifact(source_path),
        "source_path": source_path,
        "warning_category": category,
        "severity": severity,
        "owner": owner,
        "owner_type": owner_type,
        "action_path": _action_path(source_path, action_type),
        "action_type": action_type,
        "deferrable": bool(policy["deferrable"]),
        "expected_status": expected_status,
        "safety_relevance": safety_relevance,
        "recommended_operator_action": policy["recommended_operator_action"],
        "recommended_maintainer_action": policy["recommended_maintainer_action"],
        "rationale": policy["rationale"],
        "source_warning_message": warning.get("message", ""),
        "source_warning_owner": warning.get("owner", "unknown"),
        "source_warning_action_type": warning.get("action_type", "unknown"),
    }


def _bucket_records(warning_records):
    grouped = {}
    source_paths_by_bucket = defaultdict(set)
    for record in warning_records:
        bucket = grouped.setdefault(
            record["bucket_id"],
            {
                "bucket_id": record["bucket_id"],
                "warning_category": record["warning_category"],
                "severity": record["severity"],
                "owner": record["owner"],
                "owner_type": record["owner_type"],
                "action_type": record["action_type"],
                "deferrable": record["deferrable"],
                "expected_status": record["expected_status"],
                "safety_relevance": record["safety_relevance"],
                "recommended_operator_action": record["recommended_operator_action"],
                "recommended_maintainer_action": record["recommended_maintainer_action"],
                "rationale": record["rationale"],
                "warning_count": 0,
                "warning_ids": [],
                "source_paths": [],
                "example_source_path": record["source_path"],
            },
        )
        bucket["warning_count"] += 1
        bucket["warning_ids"].append(record["warning_id"])
        source_paths_by_bucket[record["bucket_id"]].add(record["source_path"])
    for bucket_id, paths in source_paths_by_bucket.items():
        grouped[bucket_id]["source_paths"] = sorted(paths)
    return sorted(grouped.values(), key=lambda item: (-item["warning_count"], item["bucket_id"]))


def _top_owner_actions(warning_records):
    counter = Counter((record["owner"], record["action_type"]) for record in warning_records)
    return [
        {"owner": owner, "action_type": action_type, "warning_count": count}
        for (owner, action_type), count in sorted(counter.items(), key=lambda item: (-item[1], item[0][0], item[0][1]))[:5]
    ]


def _safe_documented_exception_count(source_report):
    summary = source_report.get("documented_exception_summary")
    if not isinstance(summary, dict):
        return 0
    value = summary.get("total_documented_exceptions")
    return value if isinstance(value, int) else 0


def build_warning_hygiene_report(source_report=None):
    if source_report is None:
        source_report = _load_source_report()

    warning_records = [
        _warning_record(index, warning)
        for index, warning in enumerate(source_report.get("warnings", []), start=1)
    ]
    summary = _empty_summary()
    for record in warning_records:
        _increment_summary(summary, record)

    buckets = _bucket_records(warning_records)
    non_deferrable_count = summary["deferrable"]["false"]
    safety_relevant_count = len([record for record in warning_records if record["safety_relevance"] != "none"])
    blocking_count = summary["severity"].get("blocking", 0)

    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_policy": {
            "wall_clock_time_used": False,
            "deterministic_source": "pm_bot/quality/artifact_health_report.v1.json",
        },
        "source_report": {
            "schema_version": source_report.get("schema_version"),
            "task_id": source_report.get("task_id"),
            "path": "pm_bot/quality/artifact_health_report.v1.json",
            "total_warnings": len(source_report.get("warnings", [])),
            "documented_exceptions": _safe_documented_exception_count(source_report),
            "report_status": source_report.get("report_status"),
        },
        "warning_detection_policy": {
            "warnings_hidden": False,
            "warnings_suppressed": False,
            "warnings_downgraded_silently": False,
            "blocking_relabel_allowed": False,
            "statement": "Warnings are grouped and routed for owner action; they are not hidden or downgraded silently.",
        },
        "summary_counts": summary,
        "warning_buckets": buckets,
        "warnings": warning_records,
        "operator_summary": {
            "local_mvp_blocked": bool(blocking_count),
            "non_deferrable_warning_count": non_deferrable_count,
            "safety_relevant_warning_count": safety_relevant_count,
            "top_owner_actions": _top_owner_actions(warning_records),
            "next_cleanup_actions": [
                bucket
                for bucket in buckets
                if bucket["expected_status"] in {"needs_cleanup", "needs_review", "expected_gap"}
            ][:5],
            "safe_to_defer_statement": (
                "Deferrable warnings may be postponed for local MVP use when blocking_count is zero; "
                "non-deferrable warnings remain visible as owner action queues."
            ),
            "not_mvp_blocking_statement": (
                "The current source report has no blocking warnings, so these hygiene warnings should not block local MVP usage."
                if not blocking_count
                else "Blocking warnings exist and must be repaired before local MVP usage."
            ),
        },
        "safety_flags": {
            "network_api_calls": False,
            "wallet_or_private_key_usage": False,
            "real_orders": False,
            "live_trading": False,
            "autonomous_decisions": False,
            "scoring_probability_ev_edge": False,
            "side_recommendations": False,
            "runtime_wiring": False,
            "command_execution": False,
        },
    }


def render_markdown(report):
    summary = report["summary_counts"]
    lines = [
        "# PMBOT Warning Hygiene Owner Action Paths v1",
        "",
        f"task_id: {report['task_id']}",
        f"schema_version: {report['schema_version']}",
        f"source_report: {report['source_report']['path']}",
        f"total_warnings_processed: {report['source_report']['total_warnings']}",
        f"documented_exceptions: {report['source_report']['documented_exceptions']}",
        "",
        "## Warning Policy",
        "",
        "- Warnings are not hidden.",
        "- Warnings are not suppressed.",
        "- Warnings are not downgraded silently.",
        "- Blocking warnings are not relabeled unless source evidence proves they are not blocking.",
        "",
        "## Operator Summary",
        "",
        f"- local_mvp_blocked: {str(report['operator_summary']['local_mvp_blocked']).lower()}",
        f"- non_deferrable_warning_count: {report['operator_summary']['non_deferrable_warning_count']}",
        f"- safety_relevant_warning_count: {report['operator_summary']['safety_relevant_warning_count']}",
        f"- what_should_not_block_local_mvp_usage: {report['operator_summary']['not_mvp_blocking_statement']}",
        f"- safe_to_defer: {report['operator_summary']['safe_to_defer_statement']}",
        "",
        "## Summary Counts",
        "",
        f"- severity: {json.dumps(summary['severity'], sort_keys=True)}",
        f"- owner: {json.dumps(summary['owner'], sort_keys=True)}",
        f"- category: {json.dumps(summary['category'], sort_keys=True)}",
        f"- expected_status: {json.dumps(summary['expected_status'], sort_keys=True)}",
        f"- action_type: {json.dumps(summary['action_type'], sort_keys=True)}",
        f"- safety_relevance: {json.dumps(summary['safety_relevance'], sort_keys=True)}",
        f"- deferrable: {json.dumps(summary['deferrable'], sort_keys=True)}",
        "",
        "## Top Warning Groups",
        "",
    ]
    for bucket in report["warning_buckets"][:10]:
        lines.append(
            "- "
            f"{bucket['warning_category']} | owner={bucket['owner']} | severity={bucket['severity']} | "
            f"count={bucket['warning_count']} | action={bucket['action_type']} | "
            f"status={bucket['expected_status']} | deferrable={str(bucket['deferrable']).lower()}"
        )
        lines.append(f"  operator_action: {bucket['recommended_operator_action']}")
        lines.append(f"  maintainer_action: {bucket['recommended_maintainer_action']}")
        lines.append(f"  example_path: {bucket['example_source_path']}")
    if not report["warning_buckets"]:
        lines.append("- none")
    lines.extend(["", "## Owner Action Queue", ""])
    for item in report["operator_summary"]["top_owner_actions"]:
        lines.append(f"- owner={item['owner']} action={item['action_type']} count={item['warning_count']}")
    if not report["operator_summary"]["top_owner_actions"]:
        lines.append("- none")
    lines.extend(["", "## Cleanup Soon", ""])
    for bucket in report["operator_summary"]["next_cleanup_actions"]:
        lines.append(
            "- "
            f"{bucket['warning_category']} owned_by={bucket['owner']} count={bucket['warning_count']} "
            f"maintainer_action={bucket['recommended_maintainer_action']}"
        )
    if not report["operator_summary"]["next_cleanup_actions"]:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def build_quality_result(report):
    return {
        "task_id": TASK_ID,
        "status": "completed_ready_for_review",
        "summary": "Deterministic warning hygiene metadata and owner/action routing were generated from the artifact health warning report without hiding or suppressing warnings.",
        "warning_hygiene_summary": {
            "total_warnings_processed": report["source_report"]["total_warnings"],
            "documented_exceptions": report["source_report"]["documented_exceptions"],
            "owners": report["summary_counts"]["owner"],
            "severity": report["summary_counts"]["severity"],
            "expected_status": report["summary_counts"]["expected_status"],
            "action_types": report["summary_counts"]["action_type"],
            "safety_relevance": report["summary_counts"]["safety_relevance"],
            "deferrable": report["summary_counts"]["deferrable"],
        },
        "operator_summary": report["operator_summary"],
        "safety_flags": report["safety_flags"],
        "forbidden_changes_detected": False,
        "warnings_hidden_or_suppressed": False,
    }


def write_outputs(report):
    markdown = render_markdown(report)
    _write_json(DEFAULT_REPORT_JSON, report)
    _write_json(DEFAULT_EXPECTED_REPORT_JSON, report)
    _write_text(DEFAULT_REPORT_MD, markdown)
    _write_json(DEFAULT_RESULT, build_quality_result(report))


def main(argv=None):
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    report = build_warning_hygiene_report()
    if args.write:
        write_outputs(report)
    if args.markdown:
        sys.stdout.write(render_markdown(report))
    else:
        sys.stdout.write(json.dumps(report, indent=2, ensure_ascii=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
