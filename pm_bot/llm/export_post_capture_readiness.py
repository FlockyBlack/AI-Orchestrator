import argparse
import json
from collections import Counter
from pathlib import Path

from pm_bot.llm import ingest_manual_resolution_source_capture as ingest
from pm_bot.llm import manual_resolution_source_capture as capture


TASK_ID = "PMBOT-SOURCE-006-POST-CAPTURE-READINESS-AND-BATCH-GATE-REFRESH"
HEAD_BEFORE = "97e72f99a9202e5ea44b98a8df1dd2523fcef5c3"
REPORT_VERSION = "post_capture_readiness_report.v1"
GATE_VERSION = "post_capture_batch_readiness_gate.v1"
GENERATED_BY = "pm_bot/llm/export_post_capture_readiness.py"

ROOT = Path(__file__).resolve().parents[2]

READINESS_BEFORE_JSON = (
    "pm_bot/llm/current_llm_packet_evidence_readiness_scores_after_source_normalization.v1.json"
)
REPORT_JSON = "pm_bot/llm/post_capture_readiness_report.v1.json"
REPORT_MD = "pm_bot/llm/post_capture_readiness_report.v1.md"
GATE_JSON = "pm_bot/llm/post_capture_batch_readiness_gate.v1.json"
GATE_MD = "pm_bot/llm/post_capture_batch_readiness_gate.v1.md"
DOC_RESULT_JSON = "docs/PMBOT_SOURCE_006_RESULT.json"
DOC_MD = "docs/PMBOT_SOURCE_006_POST_CAPTURE_READINESS_AND_BATCH_GATE_REFRESH.md"

SOURCE_FIELDS = (
    "full_market_resolution_criteria_text",
    "full_resolution_rules",
    "official_source_references",
)
READY_INGESTED_STATUSES = set(ingest.READY_STATUSES)
DRAFT_STATUS = "draft"
OPERATOR_OVERRIDE_DOCUMENT_EXISTS = False

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
        description="Export PMBOT post-capture readiness and batch gate artifacts."
    )
    parser.add_argument("--write", action="store_true", help="Write readiness and gate artifacts.")
    parser.add_argument("--summary-only", action="store_true", help="Print concise summary JSON.")
    parser.add_argument("--markdown", action="store_true", help="Print report Markdown.")
    return parser.parse_args(argv)


def _resolve(path, root=ROOT):
    value = Path(path)
    return value if value.is_absolute() else Path(root) / value


def _load_json(path, root=ROOT):
    with _resolve(path, root=root).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_optional_json(path, root=ROOT):
    resolved = _resolve(path, root=root)
    if not resolved.exists():
        return None
    return _load_json(path, root=root)


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


def _capture_payloads(root=ROOT):
    payloads = []
    for path in sorted(_resolve(ingest.CAPTURE_DIR, root=root).glob("*_resolution_source_capture.v1.json")):
        payloads.append(_load_json(path, root=root))
    return payloads


def _is_non_empty(value):
    return value not in (None, "", [], {})


def _overlay_markets(overlay):
    markets = overlay.get("markets", []) if isinstance(overlay, dict) else []
    return [entry for entry in markets if isinstance(entry, dict)]


def _market_count_with_field(overlay, field):
    return sum(1 for entry in _overlay_markets(overlay) if _is_non_empty(entry.get(field)))


def _missing_count(total, present):
    return max(total - present, 0)


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _load_ingest_snapshot(root=ROOT):
    computed = ingest.build_ingest_report(root=root, dry_run=False)
    persisted_ingest_result = _load_optional_json(ingest.RESULT_JSON, root=root)
    persisted_overlay = _load_optional_json(ingest.OVERLAY_JSON, root=root)
    ingest_result = persisted_ingest_result or computed
    overlay = persisted_overlay
    if overlay is None:
        overlay = ingest_result.get("overlay") or computed.get("overlay", {})
    return {
        "computed": computed,
        "ingest_result": ingest_result,
        "overlay": overlay,
        "ingest_result_read": persisted_ingest_result is not None,
        "overlay_read": persisted_overlay is not None,
    }


def _market_status(entry):
    return entry.get("source_capture_status") or entry.get("capture_status") or "unknown"


def _market_count_with_status(markets, statuses):
    allowed = set(statuses)
    return sum(1 for entry in markets if _market_status(entry) in allowed)


def _text_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _text_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _text_values(item)
    elif isinstance(value, str):
        yield value


def _requires_direct_rules_verification(markets):
    if any(_market_status(entry) == DRAFT_STATUS for entry in markets):
        return True
    markers = (
        "direct polymarket rules",
        "operator verification",
        "requires operator verification",
    )
    for entry in markets:
        text = " ".join(_text_values(entry)).lower()
        if any(marker in text for marker in markers):
            return True
    return False


def _readiness_before(root=ROOT):
    payload = _load_json(READINESS_BEFORE_JSON, root=root)
    aggregate = payload.get("aggregate", {})
    return {
        "artifact_path": READINESS_BEFORE_JSON,
        "average_score": aggregate.get("updated_average_score"),
        "high_count": aggregate.get("updated_high_count"),
        "medium_count": aggregate.get("updated_medium_count"),
        "low_count": aggregate.get("updated_low_count"),
        "blocked_count": aggregate.get("updated_blocked_count"),
        "markets_still_missing_resolution_sources": [
            item.get("market_id")
            for item in payload.get("markets", [])
            if item.get("source_fields_still_missing")
        ],
    }


def _blocker_reasons(
    real_filled_count,
    real_ingested_count,
    draft_ingested_count=0,
    ready_ingested_count=0,
    direct_rules_verification_required=False,
    operator_override_document_exists=OPERATOR_OVERRIDE_DOCUMENT_EXISTS,
):
    blockers = []
    if real_filled_count == 0:
        blockers.append("no real manually filled source capture templates")
    if real_ingested_count == 0:
        blockers.append("no real manually ingested source capture templates")
    if real_ingested_count > 0 and draft_ingested_count > 0 and ready_ingested_count == 0:
        blockers.append("ingested source capture exists only as draft")
    if real_ingested_count > 0 and ready_ingested_count == 0:
        blockers.append("no ready_for_local_review or reviewed source capture templates")
    if real_ingested_count > 0 and direct_rules_verification_required:
        blockers.append("direct Polymarket rules verification still required")
    if not operator_override_document_exists:
        blockers.append("no explicit operator override document exists")
    return blockers


def _next_operator_actions(
    real_filled_count,
    real_ingested_count,
    ready_ingested_count=0,
    direct_rules_verification_required=False,
):
    if real_filled_count == 0:
        return [
            "Fill one real capture template with required source fields from manual local review.",
            "Set both capture status fields to draft, ready_for_local_review, or reviewed as appropriate.",
            "Run python -m pm_bot.llm.ingest_manual_resolution_source_capture --write --summary-only.",
        ]
    if real_ingested_count == 0:
        return [
            "Rerun SOURCE-005 ingest with the correct status option or advance the template to local review status.",
            "Run python -m pm_bot.llm.export_post_capture_readiness --write.",
        ]
    if ready_ingested_count == 0:
        return [
            "Verify the direct Polymarket Rules text locally before advancing any draft capture.",
            "Set at least one fully verified capture to ready_for_local_review or reviewed.",
            "Rerun SOURCE-005 ingest and then SOURCE-006 readiness export.",
        ]
    if direct_rules_verification_required:
        return [
            "Resolve direct Polymarket Rules verification notes before any future live read-only protocol step.",
            "Record an explicit operator override document only if the operator approves that separate protocol step.",
        ]
    return [
        "Review the local overlay before connecting any future read-only discovery task.",
        "Keep future network work separated behind explicit approval.",
    ]


def _live_readonly_readiness(real_ingested_count, ready_ingested_count, blockers):
    if real_ingested_count == 0:
        return "not_ready"
    if ready_ingested_count == 0:
        return "source_overlay_present_but_not_ready"
    if blockers:
        return "partially_ready"
    return "ready_for_protocol_review"


def build_post_capture_gate(report):
    real_filled = report["real_filled_template_count"]
    real_ingested = report["real_ingested_template_count"]
    ready_ingested = report["ready_ingested_template_count"]
    draft_ingested = report["draft_ingested_template_count"]
    operator_override_exists = report["operator_override_document_exists"]
    direct_rules_required = report["direct_polymarket_rules_verification_required"]
    blockers = _blocker_reasons(
        real_filled,
        real_ingested,
        draft_ingested_count=draft_ingested,
        ready_ingested_count=ready_ingested,
        direct_rules_verification_required=direct_rules_required,
        operator_override_document_exists=operator_override_exists,
    )
    readiness = _live_readonly_readiness(real_ingested, ready_ingested, blockers)
    future_live_002_allowed = (
        real_ingested > 0
        and ready_ingested > 0
        and not direct_rules_required
        and operator_override_exists
        and not blockers
    )
    return {
        "schema_version": GATE_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "status": "post_capture_batch_gate_created",
        "source_readiness_report_path": REPORT_JSON,
        "manual_capture_ingest_result_path": ingest.RESULT_JSON,
        "manual_capture_ingested_overlay_path": ingest.OVERLAY_JSON,
        "live_readonly_api_discovery_readiness": readiness,
        "future_live_002_allowed": future_live_002_allowed,
        "future_openrouter_batch_approved": False,
        "future_llm_review_approved": False,
        "real_filled_template_count": real_filled,
        "real_ingested_template_count": real_ingested,
        "draft_ingested_template_count": draft_ingested,
        "ready_ingested_template_count": ready_ingested,
        "ready_for_local_review_ingested_template_count": report[
            "ready_for_local_review_ingested_template_count"
        ],
        "reviewed_ingested_template_count": report["reviewed_ingested_template_count"],
        "blocker_reasons": blockers,
        "next_operator_actions": _next_operator_actions(
            real_filled,
            real_ingested,
            ready_ingested_count=ready_ingested,
            direct_rules_verification_required=direct_rules_required,
        ),
        "required_before_future_live_002": [
            "source/evidence readiness report exists",
            "manual capture ingest report exists",
            "at least one real filled capture template is ingested from ready_for_local_review or reviewed status",
            "direct Polymarket Rules text is locally verified",
            "explicit operator override document exists",
            "read-only safety protocol remains protocol-only until separately approved",
            "tests pass",
        ],
        "operator_override_document_exists": operator_override_exists,
        "direct_polymarket_rules_verification_required": direct_rules_required,
        "overlay_read_by_readiness_exporter": report["overlay_read_by_readiness_exporter"],
        "canonical_packets_mutated": False,
        "queue_mutated": False,
        "runtime_wiring_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "browser_automation_used": False,
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_post_capture_readiness_report(root=ROOT):
    ingest_snapshot = _load_ingest_snapshot(root=root)
    ingest_report = ingest_snapshot["ingest_result"]
    computed_ingest_report = ingest_snapshot["computed"]
    captures = _capture_payloads(root=root)
    status_counts = Counter(packet.get("capture_status") for packet in captures)
    overlay = ingest_snapshot["overlay"]
    overlay_markets = _overlay_markets(overlay)
    total = len(captures)
    real_ingested_count = len(overlay_markets)
    real_filled_count = _safe_int(
        ingest_report.get("real_filled_template_count"),
        computed_ingest_report.get("real_filled_template_count", 0),
    )
    sandbox_example_count = _safe_int(
        ingest_report.get("sandbox_example_count"),
        computed_ingest_report.get("sandbox_example_count", 0),
    )
    skipped_empty_count = _safe_int(
        ingest_report.get("skipped_empty_count"),
        computed_ingest_report.get("skipped_empty_count", 0),
    )
    skipped_placeholder_count = _safe_int(
        ingest_report.get("skipped_placeholder_count"),
        computed_ingest_report.get("skipped_placeholder_count", 0),
    )
    skipped_example_count = _safe_int(
        ingest_report.get("skipped_example_count"),
        computed_ingest_report.get("skipped_example_count", 0),
    )
    draft_ingested_count = _market_count_with_status(overlay_markets, (DRAFT_STATUS,))
    ready_for_local_review_count = _market_count_with_status(
        overlay_markets, ("ready_for_local_review",)
    )
    reviewed_count = _market_count_with_status(overlay_markets, ("reviewed",))
    ready_ingested_count = _market_count_with_status(
        overlay_markets, READY_INGESTED_STATUSES
    )
    direct_rules_required = _requires_direct_rules_verification(overlay_markets)
    with_resolution = _market_count_with_field(overlay, "full_market_resolution_criteria_text")
    with_rules = _market_count_with_field(overlay, "full_resolution_rules")
    with_sources = _market_count_with_field(overlay, "official_source_references")
    readiness_after_available = real_ingested_count > 0
    blockers = _blocker_reasons(
        real_filled_count,
        real_ingested_count,
        draft_ingested_count=draft_ingested_count,
        ready_ingested_count=ready_ingested_count,
        direct_rules_verification_required=direct_rules_required,
        operator_override_document_exists=OPERATOR_OVERRIDE_DOCUMENT_EXISTS,
    )
    live_readiness = _live_readonly_readiness(
        real_ingested_count,
        ready_ingested_count,
        blockers,
    )
    report = {
        "schema_version": REPORT_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "status": "post_capture_readiness_report_created",
        "total_capture_templates": total,
        "real_templates_not_started": status_counts.get("not_started", 0),
        "real_templates_draft": status_counts.get("draft", 0),
        "real_templates_ready_for_local_review": status_counts.get(
            "ready_for_local_review", 0
        ),
        "real_templates_reviewed": status_counts.get("reviewed", 0),
        "real_templates_needs_revision": status_counts.get("needs_revision", 0),
        "real_filled_template_count": real_filled_count,
        "real_ingested_template_count": real_ingested_count,
        "draft_ingested_template_count": draft_ingested_count,
        "ready_ingested_template_count": ready_ingested_count,
        "ready_for_local_review_ingested_template_count": ready_for_local_review_count,
        "reviewed_ingested_template_count": reviewed_count,
        "sandbox_example_count": sandbox_example_count,
        "skipped_empty_count": skipped_empty_count,
        "skipped_placeholder_count": skipped_placeholder_count,
        "skipped_example_count": skipped_example_count,
        "source_overlay_market_ids": [entry.get("market_id") for entry in overlay_markets],
        "markets_with_resolution_criteria_text": with_resolution,
        "markets_with_full_resolution_rules": with_rules,
        "markets_with_official_source_references": with_sources,
        "markets_still_missing_resolution_criteria_text": _missing_count(total, with_resolution),
        "markets_still_missing_full_resolution_rules": _missing_count(total, with_rules),
        "markets_still_missing_official_source_references": _missing_count(total, with_sources),
        "readiness_before": _readiness_before(root=root),
        "readiness_after_if_available": {
            "available": readiness_after_available,
            "status": "not_available_no_real_ingest"
            if not readiness_after_available
            else live_readiness,
            "score_recalculation_performed": False,
            "canonical_packets_mutated": False,
        },
        "manual_capture_ingest_result_path": ingest.RESULT_JSON,
        "manual_capture_overlay_path": ingest.OVERLAY_JSON,
        "manual_capture_ingest_result_read": ingest_snapshot["ingest_result_read"],
        "overlay_read_by_readiness_exporter": ingest_snapshot["overlay_read"],
        "direct_polymarket_rules_verification_required": direct_rules_required,
        "operator_override_document_exists": OPERATOR_OVERRIDE_DOCUMENT_EXISTS,
        "live_readonly_api_discovery_readiness": live_readiness,
        "blocker_reasons": blockers,
        "next_operator_actions": _next_operator_actions(
            real_filled_count,
            real_ingested_count,
            ready_ingested_count=ready_ingested_count,
            direct_rules_verification_required=direct_rules_required,
        ),
        "canonical_packets_mutated": False,
        "workbench_artifacts_mutated": False,
        "queue_mutated": False,
        "runtime_wiring_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "browser_automation_used": False,
        "safety_summary": dict(SAFETY_SUMMARY),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }
    report["gate"] = build_post_capture_gate(report)
    return report


def _summary(report):
    return {
        "schema_version": report["schema_version"],
        "task_id": report["task_id"],
        "status": report["status"],
        "total_capture_templates": report["total_capture_templates"],
        "real_filled_template_count": report["real_filled_template_count"],
        "real_ingested_template_count": report["real_ingested_template_count"],
        "draft_ingested_template_count": report["draft_ingested_template_count"],
        "ready_ingested_template_count": report["ready_ingested_template_count"],
        "sandbox_example_count": report["sandbox_example_count"],
        "live_readonly_api_discovery_readiness": report[
            "live_readonly_api_discovery_readiness"
        ],
        "future_live_002_allowed": report["gate"]["future_live_002_allowed"],
        "blocker_reasons": report["blocker_reasons"],
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def render_report_markdown(report):
    lines = [
        "# PMBOT SOURCE-006 Post-Capture Readiness Report",
        "",
        f"- schema_version: {report['schema_version']}",
        f"- task_id: {report['task_id']}",
        f"- status: {report['status']}",
        f"- total_capture_templates: {report['total_capture_templates']}",
        f"- real_templates_not_started: {report['real_templates_not_started']}",
        f"- real_templates_draft: {report['real_templates_draft']}",
        f"- real_templates_ready_for_local_review: {report['real_templates_ready_for_local_review']}",
        f"- real_templates_reviewed: {report['real_templates_reviewed']}",
        f"- real_templates_needs_revision: {report['real_templates_needs_revision']}",
        f"- real_filled_template_count: {report['real_filled_template_count']}",
        f"- real_ingested_template_count: {report['real_ingested_template_count']}",
        f"- draft_ingested_template_count: {report['draft_ingested_template_count']}",
        f"- ready_ingested_template_count: {report['ready_ingested_template_count']}",
        f"- ready_for_local_review_ingested_template_count: {report['ready_for_local_review_ingested_template_count']}",
        f"- reviewed_ingested_template_count: {report['reviewed_ingested_template_count']}",
        f"- sandbox_example_count: {report['sandbox_example_count']}",
        f"- skipped_empty_count: {report['skipped_empty_count']}",
        f"- skipped_placeholder_count: {report['skipped_placeholder_count']}",
        f"- skipped_example_count: {report['skipped_example_count']}",
        f"- overlay_read_by_readiness_exporter: {str(report['overlay_read_by_readiness_exporter']).lower()}",
        f"- direct_polymarket_rules_verification_required: {str(report['direct_polymarket_rules_verification_required']).lower()}",
        f"- operator_override_document_exists: {str(report['operator_override_document_exists']).lower()}",
        f"- markets_with_resolution_criteria_text: {report['markets_with_resolution_criteria_text']}",
        f"- markets_with_full_resolution_rules: {report['markets_with_full_resolution_rules']}",
        f"- markets_with_official_source_references: {report['markets_with_official_source_references']}",
        f"- markets_still_missing_resolution_criteria_text: {report['markets_still_missing_resolution_criteria_text']}",
        f"- markets_still_missing_full_resolution_rules: {report['markets_still_missing_full_resolution_rules']}",
        f"- markets_still_missing_official_source_references: {report['markets_still_missing_official_source_references']}",
        f"- live_readonly_api_discovery_readiness: {report['live_readonly_api_discovery_readiness']}",
        "",
        "## Readiness Before",
        "",
        f"- artifact_path: {report['readiness_before']['artifact_path']}",
        f"- average_score: {report['readiness_before']['average_score']}",
        f"- high_count: {report['readiness_before']['high_count']}",
        f"- medium_count: {report['readiness_before']['medium_count']}",
        f"- low_count: {report['readiness_before']['low_count']}",
        "",
        "## Readiness After",
        "",
        f"- available: {str(report['readiness_after_if_available']['available']).lower()}",
        f"- status: {report['readiness_after_if_available']['status']}",
        "- score_recalculation_performed: false",
        "- canonical_packets_mutated: false",
        "",
        "## Blockers",
        "",
    ]
    for blocker in report["blocker_reasons"]:
        lines.append(f"- {blocker}")
    lines.extend(["", "## Next Operator Actions", ""])
    for action in report["next_operator_actions"]:
        lines.append(f"- {action}")
    lines.extend(
        [
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


def render_gate_markdown(gate):
    lines = [
        "# PMBOT SOURCE-006 Post-Capture Batch Readiness Gate",
        "",
        f"- schema_version: {gate['schema_version']}",
        f"- task_id: {gate['task_id']}",
        f"- status: {gate['status']}",
        f"- live_readonly_api_discovery_readiness: {gate['live_readonly_api_discovery_readiness']}",
        f"- future_live_002_allowed: {str(gate['future_live_002_allowed']).lower()}",
        f"- future_openrouter_batch_approved: {str(gate['future_openrouter_batch_approved']).lower()}",
        f"- future_llm_review_approved: {str(gate['future_llm_review_approved']).lower()}",
        f"- real_filled_template_count: {gate['real_filled_template_count']}",
        f"- real_ingested_template_count: {gate['real_ingested_template_count']}",
        f"- draft_ingested_template_count: {gate['draft_ingested_template_count']}",
        f"- ready_ingested_template_count: {gate['ready_ingested_template_count']}",
        f"- direct_polymarket_rules_verification_required: {str(gate['direct_polymarket_rules_verification_required']).lower()}",
        f"- operator_override_document_exists: {str(gate['operator_override_document_exists']).lower()}",
        "",
        "## Blocker Reasons",
        "",
    ]
    for blocker in gate["blocker_reasons"]:
        lines.append(f"- {blocker}")
    lines.extend(["", "## Required Before Future LIVE-002", ""])
    for item in gate["required_before_future_live_002"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Safety Summary",
            "",
            "- no network calls",
            "- no market action guidance",
            "- no queue, runtime, dispatcher, background, browser, wallet, or order authority",
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
        "source_006_readiness_created": True,
        "post_capture_gate_created": True,
        "real_filled_template_count": report["real_filled_template_count"],
        "real_ingested_template_count": report["real_ingested_template_count"],
        "draft_ingested_template_count": report["draft_ingested_template_count"],
        "ready_ingested_template_count": report["ready_ingested_template_count"],
        "overlay_read_by_readiness_exporter": report["overlay_read_by_readiness_exporter"],
        "direct_polymarket_rules_verification_required": report[
            "direct_polymarket_rules_verification_required"
        ],
        "operator_override_document_exists": report["operator_override_document_exists"],
        "future_live_002_allowed": report["gate"]["future_live_002_allowed"],
        "sandbox_example_count": report["sandbox_example_count"],
        "live_readonly_api_discovery_readiness": report[
            "live_readonly_api_discovery_readiness"
        ],
        "blocker_reasons": report["blocker_reasons"],
        "workbench_artifacts_mutated": False,
        "canonical_packets_mutated": False,
        "queue_mutated": False,
        "runtime_wiring_changed": False,
        "dispatcher_changed": False,
        "tests_run": [],
        "files_created": [
            REPORT_JSON,
            REPORT_MD,
            GATE_JSON,
            GATE_MD,
            DOC_RESULT_JSON,
            DOC_MD,
        ],
        "files_modified": [GENERATED_BY],
        "next_recommended_action": report["next_operator_actions"][0],
        "safety_summary": dict(SAFETY_SUMMARY),
    }


def render_docs_markdown(report):
    lines = [
        "# PMBOT SOURCE-006 Post-Capture Readiness And Batch Gate Refresh",
        "",
        "SOURCE-006 reports whether manual source capture actually improved local readiness.",
        "Sandbox examples are counted separately and do not improve real readiness.",
        "",
        "## Current Honest State",
        "",
        f"- real_filled_template_count: {report['real_filled_template_count']}",
        f"- real_ingested_template_count: {report['real_ingested_template_count']}",
        f"- draft_ingested_template_count: {report['draft_ingested_template_count']}",
        f"- ready_ingested_template_count: {report['ready_ingested_template_count']}",
        f"- overlay_read_by_readiness_exporter: {str(report['overlay_read_by_readiness_exporter']).lower()}",
        f"- direct_polymarket_rules_verification_required: {str(report['direct_polymarket_rules_verification_required']).lower()}",
        f"- operator_override_document_exists: {str(report['operator_override_document_exists']).lower()}",
        f"- future_live_002_allowed: {str(report['gate']['future_live_002_allowed']).lower()}",
        f"- sandbox_example_count: {report['sandbox_example_count']}",
        f"- live_readonly_api_discovery_readiness: {report['live_readonly_api_discovery_readiness']}",
        "",
        "## Blockers",
        "",
    ]
    for blocker in report["blocker_reasons"]:
        lines.append(f"- {blocker}")
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
        ]
    )
    return "\n".join(lines)


def write_post_capture_readiness_artifacts(root=ROOT):
    report = build_post_capture_readiness_report(root=root)
    gate = report["gate"]
    docs_result = build_docs_result(report)
    _write_json(REPORT_JSON, report, root=root)
    _write_text(REPORT_MD, render_report_markdown(report), root=root)
    _write_json(GATE_JSON, gate, root=root)
    _write_text(GATE_MD, render_gate_markdown(gate), root=root)
    _write_json(DOC_RESULT_JSON, docs_result, root=root)
    _write_text(DOC_MD, render_docs_markdown(report), root=root)
    return report


def main(argv):
    args = _parse_args(argv)
    if args.write:
        report = write_post_capture_readiness_artifacts(ROOT)
    else:
        report = build_post_capture_readiness_report(ROOT)
    if args.markdown:
        print(render_report_markdown(report), end="")
    elif args.summary_only:
        print(json.dumps(_summary(report), indent=2, ensure_ascii=True))
    else:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
