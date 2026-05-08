import argparse
import json
import re
from collections import Counter
from pathlib import Path

from pm_bot.llm import manual_resolution_source_capture as capture


TASK_ID = "PMBOT-SOURCE-005-MANUAL-CAPTURE-INGEST-FROM-FILLED-TEMPLATES"
HEAD_BEFORE = "97e72f99a9202e5ea44b98a8df1dd2523fcef5c3"
RESULT_VERSION = "manual_resolution_source_capture_ingest_result.v1"
MANIFEST_VERSION = "manual_resolution_source_capture_ingest_manifest.v1"
OVERLAY_VERSION = "manual_resolution_source_capture_ingested_overlay.v1"
GENERATED_BY = "pm_bot/llm/ingest_manual_resolution_source_capture.py"

ROOT = Path(__file__).resolve().parents[2]

CAPTURE_DIR = "pm_bot/llm/manual_resolution_source_capture"
EXAMPLE_DIR = "pm_bot/llm/manual_resolution_source_capture_examples"

RESULT_JSON = "pm_bot/llm/manual_resolution_source_capture_ingest_result.v1.json"
RESULT_MD = "pm_bot/llm/manual_resolution_source_capture_ingest_result.v1.md"
MANIFEST_JSON = "pm_bot/llm/manual_resolution_source_capture_ingest_manifest.v1.json"
MANIFEST_MD = "pm_bot/llm/manual_resolution_source_capture_ingest_manifest.v1.md"
OVERLAY_JSON = "pm_bot/llm/manual_resolution_source_capture_ingested_overlay.v1.json"
OVERLAY_MD = "pm_bot/llm/manual_resolution_source_capture_ingested_overlay.v1.md"
DOC_RESULT_JSON = "docs/PMBOT_SOURCE_005_RESULT.json"
DOC_MD = "docs/PMBOT_SOURCE_005_MANUAL_CAPTURE_INGEST_FROM_FILLED_TEMPLATES.md"

FILLED_STATUSES = ("draft", "ready_for_local_review", "reviewed")
READY_STATUSES = ("ready_for_local_review", "reviewed")
REQUIRED_INGEST_FIELDS = (
    "full_market_resolution_criteria_text",
    "full_resolution_rules",
    "official_source_references",
    "official_source_urls_or_rule_references",
    "source_timestamps",
    "source_reliability_review",
    "reviewed_local_evidence_references",
    "non_placeholder_evidence_notes",
)

EXAMPLE_FLAGS = (
    "example_only",
    "sandbox_only",
    "not_real_market_data",
    "not_for_ingest_as_real_source",
)

PLACEHOLDER_PATTERNS = (
    re.compile(r"^\s*$", re.IGNORECASE),
    re.compile(r"\b(todo|tbd|placeholder|fill me|not started)\b", re.IGNORECASE),
    re.compile(r"\b(example only|sandbox only|not real market data)\b", re.IGNORECASE),
    re.compile(r"^\s*(n/a|none|null|unknown)\s*$", re.IGNORECASE),
)

SAFETY_SUMMARY = {
    **capture.SAFETY_SUMMARY,
    "operator_review_only": True,
    "analysis_only": True,
    "local_only": True,
    "manual_review_only": True,
    "no_market_action_guidance": True,
    "no_trading_authority": True,
    "no_queue_authority": True,
    "no_runtime_authority": True,
    "no_dispatcher_authority": True,
    "no_browser_automation": True,
    "no_wallet_or_order_authority": True,
    "openrouter_calls_performed": 0,
    "polymarket_api_calls_performed": 0,
    "external_network_calls_performed": 0,
    "network_calls_performed": 0,
    "api_key_accessed": False,
    "wallet_or_private_key_accessed": False,
    "orders_created": 0,
    "queue_state_mutated": False,
    "runtime_wiring_added": False,
    "dispatcher_changed": False,
    "background_workers_added": False,
    "browser_automation_used": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Ingest manually filled local PMBOT resolution/source capture templates."
    )
    parser.add_argument("--write", action="store_true", help="Write local ingest artifacts.")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate only; do not write artifacts.")
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print a concise ingest summary JSON.",
    )
    parser.add_argument(
        "--include-drafts",
        action="store_true",
        help="Allow fully filled draft templates to be included in the overlay.",
    )
    parser.add_argument(
        "--strict-ready",
        action="store_true",
        help="Only ingest ready_for_local_review or reviewed templates.",
    )
    return parser.parse_args(argv)


def _resolve(path, root=ROOT):
    value = Path(path)
    return value if value.is_absolute() else Path(root) / value


def _display_path(path, root=ROOT):
    resolved = Path(path).resolve()
    try:
        value = resolved.relative_to(Path(root).resolve())
    except ValueError:
        value = resolved
    return str(value).replace("\\", "/")


def _load_json(path, root=ROOT):
    with _resolve(path, root=root).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, payload, root=ROOT):
    resolved = _resolve(path, root=root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _ascii(value):
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def _write_text(path, text, root=ROOT):
    resolved = _resolve(path, root=root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(_ascii(text), encoding="utf-8")


def _json_paths(directory, root=ROOT):
    resolved = _resolve(directory, root=root)
    if not resolved.exists():
        return []
    return sorted(resolved.glob("*.json"))


def _capture_paths(root=ROOT):
    return sorted(_resolve(CAPTURE_DIR, root=root).glob("*_resolution_source_capture.v1.json"))


def _example_paths(root=ROOT):
    paths = []
    for path in _json_paths(EXAMPLE_DIR, root=root):
        payload = _load_json(path, root=root)
        if _is_example_payload(payload) and payload.get("market_id"):
            paths.append(path)
    return paths


def _is_empty(value):
    return value is None or value == "" or value == [] or value == {}


def _string_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _string_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _string_values(item)
    elif isinstance(value, str):
        yield value


def _contains_placeholder(value):
    if _is_empty(value):
        return True
    strings = list(_string_values(value))
    if not strings:
        return False
    return any(pattern.search(text) for text in strings for pattern in PLACEHOLDER_PATTERNS)


def _is_example_payload(payload):
    return any(payload.get(flag) is True for flag in EXAMPLE_FLAGS)


def _required_field_gaps(payload):
    missing = []
    placeholder = []
    for field in REQUIRED_INGEST_FIELDS:
        value = payload.get(field)
        if _is_empty(value):
            missing.append(field)
        elif _contains_placeholder(value):
            placeholder.append(field)
    return missing, placeholder


def _allowed_statuses(include_drafts=False, strict_ready=False):
    if strict_ready:
        return set(READY_STATUSES)
    if include_drafts:
        return set(FILLED_STATUSES)
    return set(READY_STATUSES)


def _status(payload):
    return payload.get("source_capture_status") or payload.get("capture_status") or "unknown"


def _statuses_match(payload):
    return payload.get("source_capture_status") == payload.get("capture_status")


def _is_real_filled(payload):
    if _is_example_payload(payload):
        return False
    if not payload.get("market_id"):
        return False
    if not _statuses_match(payload):
        return False
    if _status(payload) not in FILLED_STATUSES:
        return False
    missing, placeholder = _required_field_gaps(payload)
    return not missing and not placeholder


def evaluate_capture_template(path, payload, include_drafts=False, strict_ready=False, root=ROOT):
    display_path = _display_path(path, root=root)
    market_id = str(payload.get("market_id") or "unknown")
    status = _status(payload)
    result = {
        "path": display_path,
        "market_id": market_id,
        "source_capture_status": payload.get("source_capture_status"),
        "capture_status": payload.get("capture_status"),
        "eligible_for_ingest": False,
        "skip_reason": None,
        "missing_required_source_fields": [],
        "placeholder_required_source_fields": [],
    }
    if _is_example_payload(payload):
        result["skip_reason"] = "sandbox_or_example_template"
        return result
    if not payload.get("market_id"):
        result["skip_reason"] = "missing_market_id"
        return result
    if not _statuses_match(payload):
        result["skip_reason"] = "capture_status_mismatch"
        return result
    if status == "not_started":
        result["skip_reason"] = "not_started_or_empty_template"
        return result
    if status not in FILLED_STATUSES:
        result["skip_reason"] = "capture_status_not_ingestable"
        return result

    missing, placeholder = _required_field_gaps(payload)
    result["missing_required_source_fields"] = missing
    result["placeholder_required_source_fields"] = placeholder
    if missing or placeholder:
        result["skip_reason"] = "required_source_fields_empty_or_placeholder"
        return result
    if status not in _allowed_statuses(include_drafts=include_drafts, strict_ready=strict_ready):
        result["skip_reason"] = "status_not_allowed_by_current_cli_options"
        return result

    result["eligible_for_ingest"] = True
    return result


def _overlay_entry(path, payload, root=ROOT):
    return {
        "market_id": str(payload["market_id"]),
        "capture_path": _display_path(path, root=root),
        "source_capture_status": payload.get("source_capture_status"),
        "capture_status": payload.get("capture_status"),
        "market_title_or_question": payload.get("market_title_or_question"),
        "category": payload.get("category"),
        "ingested_fields": list(REQUIRED_INGEST_FIELDS),
        "full_market_resolution_criteria_text": payload.get(
            "full_market_resolution_criteria_text"
        ),
        "full_resolution_rules": payload.get("full_resolution_rules"),
        "official_source_references": payload.get("official_source_references"),
        "official_source_urls_or_rule_references": payload.get(
            "official_source_urls_or_rule_references"
        ),
        "source_timestamps": payload.get("source_timestamps"),
        "source_reliability_review": payload.get("source_reliability_review"),
        "reviewed_local_evidence_references": payload.get("reviewed_local_evidence_references"),
        "non_placeholder_evidence_notes": payload.get("non_placeholder_evidence_notes"),
        "jurisdiction": payload.get("jurisdiction"),
        "candidate_or_party_if_applicable": payload.get("candidate_or_party_if_applicable"),
        "source_capture_author_or_operator": payload.get("source_capture_author_or_operator"),
        "source_capture_timestamp_local": payload.get("source_capture_timestamp_local"),
        "source_capture_provenance": payload.get("source_capture_provenance"),
        "operator_review_only": True,
        "analysis_only": True,
        "no_market_action_guidance": True,
        "no_trading_authority": True,
        "no_queue_authority": True,
        "no_runtime_authority": True,
        "no_wallet_or_order_authority": True,
    }


def _build_overlay(entries):
    return {
        "schema_version": OVERLAY_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "status": "real_templates_ingested" if entries else "no_real_ingested_templates",
        "overlay_scope": "local_manual_source_capture_overlay_only",
        "canonical_packets_mutated": False,
        "real_ingested_template_count": len(entries),
        "markets": entries,
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_ingest_report(root=ROOT, include_drafts=False, strict_ready=False, dry_run=True):
    template_results = []
    overlay_entries = []
    status_counts = Counter()
    real_filled_template_count = 0
    skipped_empty_count = 0
    skipped_placeholder_count = 0
    skipped_example_count = 0

    for path in _capture_paths(root=root):
        payload = _load_json(path, root=root)
        if _is_example_payload(payload):
            skipped_example_count += 1
        status_counts[_status(payload)] += 1
        if _is_real_filled(payload):
            real_filled_template_count += 1
        result = evaluate_capture_template(
            path,
            payload,
            include_drafts=include_drafts,
            strict_ready=strict_ready,
            root=root,
        )
        if result["skip_reason"] == "not_started_or_empty_template":
            skipped_empty_count += 1
        if result["skip_reason"] == "required_source_fields_empty_or_placeholder":
            skipped_placeholder_count += 1
        if result["skip_reason"] == "sandbox_or_example_template":
            skipped_example_count += 1
        if result["eligible_for_ingest"]:
            overlay_entries.append(_overlay_entry(path, payload, root=root))
        template_results.append(result)

    example_paths = _example_paths(root=root)
    skipped_example_count += len(example_paths)
    sandbox_examples = [_display_path(path, root=root) for path in example_paths]
    overlay = _build_overlay(overlay_entries)
    real_ingested_template_count = len(overlay_entries)
    ingest_status = (
        "real_templates_ingested"
        if real_ingested_template_count
        else "pending_manual_operator_filled_template"
    )
    status = "completed" if real_ingested_template_count else "blocked_or_pending"
    reason = None
    if not real_ingested_template_count:
        reason = "no eligible real filled manual capture templates"

    manifest = {
        "schema_version": MANIFEST_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "status": "manual_capture_ingest_manifest_created",
        "capture_dir": CAPTURE_DIR,
        "example_dir": EXAMPLE_DIR,
        "total_real_template_count": len(template_results),
        "real_filled_template_count": real_filled_template_count,
        "real_ingested_template_count": real_ingested_template_count,
        "sandbox_example_count": len(example_paths),
        "skipped_empty_count": skipped_empty_count,
        "skipped_placeholder_count": skipped_placeholder_count,
        "skipped_example_count": skipped_example_count,
        "capture_status_counts": {
            status_name: status_counts.get(status_name, 0)
            for status_name in capture.CAPTURE_STATUS_VALUES
        },
        "allowed_statuses": sorted(
            _allowed_statuses(include_drafts=include_drafts, strict_ready=strict_ready)
        ),
        "include_drafts": include_drafts,
        "strict_ready": strict_ready,
        "required_ingest_fields": list(REQUIRED_INGEST_FIELDS),
        "eligible_market_ids": [entry["market_id"] for entry in overlay_entries],
        "skipped_templates": [item for item in template_results if not item["eligible_for_ingest"]],
        "sandbox_example_paths": sandbox_examples,
        "overlay_path": OVERLAY_JSON,
        "canonical_packets_mutated": False,
        "safety_summary": dict(SAFETY_SUMMARY),
    }
    report = {
        "schema_version": RESULT_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "status": status,
        "ingest_status": ingest_status,
        "reason": reason,
        "dry_run": dry_run,
        "include_drafts": include_drafts,
        "strict_ready": strict_ready,
        "real_filled_template_count": real_filled_template_count,
        "real_ingested_template_count": real_ingested_template_count,
        "sandbox_example_count": len(example_paths),
        "skipped_empty_count": skipped_empty_count,
        "skipped_placeholder_count": skipped_placeholder_count,
        "skipped_example_count": skipped_example_count,
        "template_results": template_results,
        "manifest": manifest,
        "overlay": overlay,
        "output_paths": {
            "result_json": RESULT_JSON,
            "result_md": RESULT_MD,
            "manifest_json": MANIFEST_JSON,
            "manifest_md": MANIFEST_MD,
            "overlay_json": OVERLAY_JSON,
            "overlay_md": OVERLAY_MD,
            "docs_result_json": DOC_RESULT_JSON,
            "docs_markdown": DOC_MD,
        },
        "canonical_packets_mutated": False,
        "network_used": False,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
        "safety_summary": dict(SAFETY_SUMMARY),
    }
    return report


def _summary(report):
    return {
        "schema_version": report["schema_version"],
        "task_id": report["task_id"],
        "status": report["status"],
        "ingest_status": report["ingest_status"],
        "reason": report["reason"],
        "dry_run": report["dry_run"],
        "include_drafts": report["include_drafts"],
        "strict_ready": report["strict_ready"],
        "real_filled_template_count": report["real_filled_template_count"],
        "real_ingested_template_count": report["real_ingested_template_count"],
        "sandbox_example_count": report["sandbox_example_count"],
        "skipped_empty_count": report["skipped_empty_count"],
        "skipped_placeholder_count": report["skipped_placeholder_count"],
        "skipped_example_count": report["skipped_example_count"],
        "canonical_packets_mutated": False,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def render_ingest_result_markdown(report):
    lines = [
        "# PMBOT SOURCE-005 Manual Capture Ingest Result",
        "",
        f"- schema_version: {report['schema_version']}",
        f"- task_id: {report['task_id']}",
        f"- status: {report['status']}",
        f"- ingest_status: {report['ingest_status']}",
        f"- reason: {report['reason'] or 'none'}",
        f"- dry_run: {str(report['dry_run']).lower()}",
        f"- include_drafts: {str(report['include_drafts']).lower()}",
        f"- strict_ready: {str(report['strict_ready']).lower()}",
        f"- real_filled_template_count: {report['real_filled_template_count']}",
        f"- real_ingested_template_count: {report['real_ingested_template_count']}",
        f"- sandbox_example_count: {report['sandbox_example_count']}",
        f"- skipped_empty_count: {report['skipped_empty_count']}",
        f"- skipped_placeholder_count: {report['skipped_placeholder_count']}",
        f"- skipped_example_count: {report['skipped_example_count']}",
        f"- canonical_packets_mutated: {str(report['canonical_packets_mutated']).lower()}",
        "",
        "## Current Outcome",
        "",
    ]
    if report["real_ingested_template_count"]:
        lines.append("- Local overlay contains real manually filled capture data.")
    else:
        lines.append("- Real ingest is pending manual operator-filled templates.")
        lines.append("- Empty, not_started, placeholder, and sandbox/example records were skipped.")
    lines.extend(
        [
            "",
            "## Overlay Policy",
            "",
            "- Ingest writes a versioned local overlay artifact only.",
            "- Canonical packets remain unchanged.",
            "- Workbench consumption can be added later after a separate review task.",
            "",
            "## Safety Summary",
            "",
            "- no OpenRouter calls",
            "- no Polymarket API calls",
            "- no network calls",
            "- no trading authority",
            "- no queue, runtime, dispatcher, background, browser, wallet, or order authority",
            "- no market action guidance",
            "- no probability, EV, edge, confidence, or side selection",
            "",
        ]
    )
    return "\n".join(lines)


def render_ingest_manifest_markdown(manifest):
    lines = [
        "# PMBOT SOURCE-005 Manual Capture Ingest Manifest",
        "",
        f"- schema_version: {manifest['schema_version']}",
        f"- task_id: {manifest['task_id']}",
        f"- status: {manifest['status']}",
        f"- capture_dir: {manifest['capture_dir']}",
        f"- example_dir: {manifest['example_dir']}",
        f"- total_real_template_count: {manifest['total_real_template_count']}",
        f"- real_filled_template_count: {manifest['real_filled_template_count']}",
        f"- real_ingested_template_count: {manifest['real_ingested_template_count']}",
        f"- sandbox_example_count: {manifest['sandbox_example_count']}",
        f"- skipped_empty_count: {manifest['skipped_empty_count']}",
        f"- skipped_placeholder_count: {manifest['skipped_placeholder_count']}",
        f"- skipped_example_count: {manifest['skipped_example_count']}",
        f"- canonical_packets_mutated: {str(manifest['canonical_packets_mutated']).lower()}",
        "",
        "## Capture Status Counts",
        "",
    ]
    for status, count in manifest["capture_status_counts"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## Required Ingest Fields", ""])
    for field in manifest["required_ingest_fields"]:
        lines.append(f"- {field}")
    lines.extend(["", "## Eligible Market IDs", ""])
    if manifest["eligible_market_ids"]:
        for market_id in manifest["eligible_market_ids"]:
            lines.append(f"- {market_id}")
    else:
        lines.append("- none")
    lines.extend(["", "## Sandbox Example Paths", ""])
    if manifest["sandbox_example_paths"]:
        for path in manifest["sandbox_example_paths"]:
            lines.append(f"- {path}")
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def render_overlay_markdown(overlay):
    lines = [
        "# PMBOT SOURCE-005 Manual Capture Ingested Overlay",
        "",
        f"- schema_version: {overlay['schema_version']}",
        f"- task_id: {overlay['task_id']}",
        f"- status: {overlay['status']}",
        f"- overlay_scope: {overlay['overlay_scope']}",
        f"- canonical_packets_mutated: {str(overlay['canonical_packets_mutated']).lower()}",
        f"- real_ingested_template_count: {overlay['real_ingested_template_count']}",
        "",
        "## Markets",
        "",
    ]
    if overlay["markets"]:
        for entry in overlay["markets"]:
            lines.append(f"- {entry['market_id']}: {entry['capture_path']}")
    else:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Safety Summary",
            "",
            "- local overlay only",
            "- no network calls",
            "- no market action guidance",
            "",
        ]
    )
    return "\n".join(lines)


def build_docs_result(report):
    return {
        "task_id": TASK_ID,
        "status": "completed_local_validation_pending_commit",
        "head_before": HEAD_BEFORE,
        "head_after": "reported_in_final_response_after_commit",
        "head_after_note": (
            "A committed result artifact cannot contain its own final commit hash; "
            "the final executor response reports the pushed head."
        ),
        "pushed": False,
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
        "source_005_ingest_logic_created": True,
        "real_filled_template_count": report["real_filled_template_count"],
        "real_ingested_template_count": report["real_ingested_template_count"],
        "ingest_status": report["ingest_status"],
        "reason": report["reason"],
        "sandbox_examples_skipped": True,
        "empty_not_started_templates_skipped": True,
        "placeholder_fields_skipped": True,
        "canonical_packets_mutated": False,
        "overlay_artifact_created": True,
        "tests_run": [],
        "files_created": [
            RESULT_JSON,
            RESULT_MD,
            MANIFEST_JSON,
            MANIFEST_MD,
            OVERLAY_JSON,
            OVERLAY_MD,
            DOC_RESULT_JSON,
            DOC_MD,
        ],
        "files_modified": [GENERATED_BY],
        "next_recommended_action": (
            "Operator fills at least one real capture template with required source fields, "
            "then reruns this ingest script with --write."
        ),
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def render_docs_markdown(report):
    lines = [
        "# PMBOT SOURCE-005 Manual Capture Ingest From Filled Templates",
        "",
        "SOURCE-005 adds a local ingest layer for manually filled SOURCE-004 templates.",
        "It does not treat empty real templates or sandbox examples as source improvement.",
        "",
        "## Result",
        "",
        f"- ingest_status: {report['ingest_status']}",
        f"- reason: {report['reason'] or 'none'}",
        f"- real_filled_template_count: {report['real_filled_template_count']}",
        f"- real_ingested_template_count: {report['real_ingested_template_count']}",
        f"- sandbox_example_count: {report['sandbox_example_count']}",
        f"- skipped_empty_count: {report['skipped_empty_count']}",
        f"- skipped_placeholder_count: {report['skipped_placeholder_count']}",
        f"- skipped_example_count: {report['skipped_example_count']}",
        "",
        "## Ingest Rules",
        "",
        "- Skip `not_started` templates.",
        "- Skip empty or placeholder required source fields.",
        "- Skip sandbox/example templates.",
        "- Default ingest accepts `ready_for_local_review` and `reviewed` records.",
        "- `--include-drafts` allows fully filled `draft` records.",
        "- `--strict-ready` keeps the ingest limited to review-ready statuses.",
        "",
        "## Current Honest State",
        "",
    ]
    if report["real_ingested_template_count"]:
        lines.append("- At least one real capture template was ingested into the overlay.")
    else:
        lines.append("- Real ingest is pending manual operator-filled source templates.")
    lines.extend(
        [
            "",
            "## Safety Boundary",
            "",
            "- no OpenRouter calls",
            "- no Polymarket API calls",
            "- no network calls",
            "- no trading authority",
            "- no queue, runtime, dispatcher, background, browser, wallet, or order authority",
            "- no market action guidance",
            "- no probability, EV, edge, confidence, or side selection",
            "",
            "## Next Action",
            "",
            "- Fill one real capture template from manual local source review, then rerun `python -m pm_bot.llm.ingest_manual_resolution_source_capture --write --summary-only`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_ingest_artifacts(root=ROOT, include_drafts=False, strict_ready=False):
    report = build_ingest_report(
        root=root,
        include_drafts=include_drafts,
        strict_ready=strict_ready,
        dry_run=False,
    )
    manifest = report["manifest"]
    overlay = report["overlay"]
    docs_result = build_docs_result(report)
    _write_json(RESULT_JSON, report, root=root)
    _write_text(RESULT_MD, render_ingest_result_markdown(report), root=root)
    _write_json(MANIFEST_JSON, manifest, root=root)
    _write_text(MANIFEST_MD, render_ingest_manifest_markdown(manifest), root=root)
    _write_json(OVERLAY_JSON, overlay, root=root)
    _write_text(OVERLAY_MD, render_overlay_markdown(overlay), root=root)
    _write_json(DOC_RESULT_JSON, docs_result, root=root)
    _write_text(DOC_MD, render_docs_markdown(report), root=root)
    return report


def main(argv):
    args = _parse_args(argv)
    if args.write and args.dry_run:
        raise SystemExit("--write and --dry-run cannot be combined")
    if args.write:
        report = write_ingest_artifacts(
            ROOT,
            include_drafts=args.include_drafts,
            strict_ready=args.strict_ready,
        )
    else:
        report = build_ingest_report(
            ROOT,
            include_drafts=args.include_drafts,
            strict_ready=args.strict_ready,
            dry_run=True,
        )
    if args.summary_only:
        print(json.dumps(_summary(report), indent=2, ensure_ascii=True))
    else:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
