import json
from collections import Counter
from pathlib import Path


TASK_ID = "PMBOT-SOURCE-002-LOCAL-PACKET-COMPLETENESS-SCORER-INTEGRATION"
SCHEMA_VERSION = "packet_completeness_scorer.v1"
GATE_VERSION = "current_llm_batch_readiness_gate.v1"
GENERATED_BY = "pm_bot/llm/packet_completeness_scorer.py"
GENERATION_MARKER = "deterministic-source-002-local-packet-completeness-gate.v1"

ROOT = Path(__file__).resolve().parents[2]

SOURCE_PATHS = {
    "inventory_json": "pm_bot/llm/current_llm_market_packet_inventory.v1.json",
    "readiness_scores_json": "pm_bot/llm/current_llm_packet_evidence_readiness_scores.v1.json",
    "completeness_contract_json": "pm_bot/llm/llm_market_packet_completeness_contract.v1.json",
    "batch_readiness_gate_json": "pm_bot/llm/current_llm_batch_readiness_gate.v1.json",
    "batch_readiness_gate_md": "pm_bot/llm/current_llm_batch_readiness_gate.v1.md",
}

VALID_READINESS_BANDS = ("high", "medium", "low", "blocked")

SAFETY_FLAGS = {
    "local_only": True,
    "no_live_calls": True,
    "no_trading_authority": True,
    "no_queue_authority": True,
    "no_runtime_authority": True,
    "no_dispatcher_authority": True,
    "no_wallet_or_order_authority": True,
    "operator_review_only": True,
    "passive_context_only": True,
    "acceptance_is_not_trading_approval": True,
    "no_market_action_guidance": True,
    "no_probability_ev_edge_confidence_side_selection": True,
    "no_openrouter_calls": True,
    "no_polymarket_api_calls": True,
    "no_external_network_calls": True,
    "no_browser_automation": True,
}

GATE_LOGIC = {
    "high": "eligible_for_future_openrouter_batch_if_other_safety_constraints_pass",
    "medium": "eligible_only_with_warning_or_manual_operator_approval",
    "low": "needs_local_enrichment_before_future_openrouter_batch",
    "blocked": "not_eligible",
}


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


def _write_text(path, text, root=ROOT):
    resolved = _resolve(path, root=root)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(text, encoding="utf-8")


def _safe_dict(value):
    return value if isinstance(value, dict) else {}


def _safe_list(value):
    return value if isinstance(value, list) else []


def _unique_ordered(values):
    seen = set()
    output = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def _path_exists(path, root=ROOT):
    if not path:
        return False
    return _resolve(path, root=root).exists()


def _numeric_score(value):
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return max(0, min(100, int(value)))
    return 0


def load_inventory(path=SOURCE_PATHS["inventory_json"], root=ROOT):
    return _load_json(path, root=root)


def load_readiness_scores(path=SOURCE_PATHS["readiness_scores_json"], root=ROOT):
    return _load_json(path, root=root)


def load_completeness_contract(path=SOURCE_PATHS["completeness_contract_json"], root=ROOT):
    return _load_json(path, root=root)


def _readiness_by_market(readiness_scores):
    return {
        str(item.get("market_id")): item
        for item in _safe_list(_safe_dict(readiness_scores).get("markets"))
        if item.get("market_id") is not None
    }


def _band_for_score(score, packet_exists, prompt_exists, title_present):
    if not packet_exists or not prompt_exists or not title_present:
        return "blocked"
    if score >= 90:
        return "high"
    if score >= 60:
        return "medium"
    if score >= 30:
        return "low"
    return "blocked"


def _gate_status_for_band(band):
    return {
        "high": "eligible_if_other_safety_constraints_pass",
        "medium": "eligible_with_warning_manual_operator_approval_required",
        "low": "needs_local_enrichment_before_future_batch",
        "blocked": "not_eligible",
    }.get(band, "not_eligible")


def _warnings_for_band(band):
    if band == "medium":
        return [
            "medium readiness requires warning or manual operator approval before any future OpenRouter batch"
        ]
    if band == "low":
        return ["low readiness needs local enrichment before future OpenRouter batch"]
    if band == "blocked":
        return ["blocked readiness is not eligible for future LLM review or OpenRouter batch"]
    return []


def _recommended_actions(readiness_entry, band):
    actions = list(_safe_list(readiness_entry.get("recommended_local_enrichment_actions")))
    if band == "low":
        actions.append(
            "Complete local packet enrichment for missing checklist, risk, contradiction, and source fields before future batch review."
        )
    if band == "blocked":
        actions.append(
            "Restore required packet, prompt, title, and provenance fields before future review."
        )
    return _unique_ordered(actions)


def score_market_packet(market, readiness_entry=None, contract=None, root=ROOT):
    market = _safe_dict(market)
    readiness_entry = _safe_dict(readiness_entry)
    contract = _safe_dict(contract)
    market_id = str(market.get("market_id") or readiness_entry.get("market_id") or "")
    category = market.get("category") or readiness_entry.get("category") or "unknown"
    title = market.get("title_or_question") or readiness_entry.get("title_or_question")
    packet_path = market.get("packet_file_path")
    prompt_path = market.get("prompt_file_path")
    packet_exists = _path_exists(packet_path, root=root)
    prompt_exists = _path_exists(prompt_path, root=root)
    current_score = _numeric_score(readiness_entry.get("evidence_readiness_score"))
    computed_band = _band_for_score(current_score, packet_exists, prompt_exists, bool(title))
    source_band = readiness_entry.get("readiness_band")
    readiness_band = source_band if source_band in VALID_READINESS_BANDS else computed_band
    if computed_band == "blocked":
        readiness_band = "blocked"

    missing_or_weak_fields = _unique_ordered(
        str(item) for item in _safe_list(readiness_entry.get("missing_or_weak_fields"))
    )
    suitable_for_future_llm_review = readiness_band in {"high", "medium"} and packet_exists and prompt_exists
    suitable_for_future_openrouter_batch = (
        readiness_band in {"high", "medium"} and packet_exists and prompt_exists
    )
    needs_local_enrichment_before_review = (
        bool(readiness_entry.get("needs_local_enrichment_before_review"))
        or bool(missing_or_weak_fields)
        or readiness_band in {"low", "blocked"}
    )

    return {
        "market_id": market_id,
        "title_or_question": title,
        "category": category,
        "packet_file_path": packet_path,
        "prompt_file_path": prompt_path,
        "packet_exists": packet_exists,
        "prompt_exists": prompt_exists,
        "current_score": current_score,
        "evidence_readiness_score": current_score,
        "readiness_band": readiness_band,
        "future_llm_review_gate_status": _gate_status_for_band(readiness_band),
        "future_openrouter_batch_gate_status": _gate_status_for_band(readiness_band),
        "suitable_for_future_llm_review": suitable_for_future_llm_review,
        "suitable_for_future_openrouter_batch": suitable_for_future_openrouter_batch,
        "requires_manual_operator_approval_before_future_openrouter_batch": (
            readiness_band == "medium"
        ),
        "needs_local_enrichment_before_review": needs_local_enrichment_before_review,
        "needs_local_enrichment_before_future_openrouter_batch": readiness_band
        in {"low", "blocked"},
        "reviewed_by_openrouter": bool(
            readiness_entry.get("reviewed_by_openrouter")
            or market.get("already_reviewed_by_openrouter")
        ),
        "accepted_for_operator_review": bool(
            readiness_entry.get("accepted_for_operator_review")
            or market.get("accepted_for_operator_review")
        ),
        "missing_or_weak_fields": missing_or_weak_fields,
        "recommended_local_enrichment_actions": _recommended_actions(
            readiness_entry, readiness_band
        ),
        "warnings": _warnings_for_band(readiness_band),
        "contract_version": contract.get("contract_version"),
        "no_market_action_guidance": True,
        "no_probability_ev_edge_confidence_side_selection": True,
    }


def _top_missing_fields(markets, readiness_scores):
    aggregate_fields = _safe_list(_safe_dict(readiness_scores).get("aggregate", {}).get("top_missing_fields"))
    if aggregate_fields:
        return aggregate_fields
    counts = Counter()
    for market in markets:
        counts.update(_safe_list(market.get("missing_or_weak_fields")))
    return [
        {"field": field, "market_count": count}
        for field, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _next_local_focus(readiness_scores):
    aggregate = _safe_dict(_safe_dict(readiness_scores).get("aggregate"))
    source_focus = list(_safe_list(aggregate.get("recommended_next_local_enrichment_focus")))
    focus = [
        item for item in source_focus if item != "local packet completeness scorer integration"
    ]
    focus.append("packet completeness readiness gate review before future LLM batches")
    return _unique_ordered(focus)


def summarize_packet_readiness(inventory=None, readiness_scores=None, contract=None, root=ROOT):
    inventory = inventory if inventory is not None else load_inventory(root=root)
    readiness_scores = (
        readiness_scores if readiness_scores is not None else load_readiness_scores(root=root)
    )
    contract = contract if contract is not None else load_completeness_contract(root=root)
    readiness_lookup = _readiness_by_market(readiness_scores)
    per_market = [
        score_market_packet(
            market,
            readiness_entry=readiness_lookup.get(str(market.get("market_id")), {}),
            contract=contract,
            root=root,
        )
        for market in _safe_list(_safe_dict(inventory).get("markets"))
    ]

    band_counts = Counter(item["readiness_band"] for item in per_market)
    total_markets = len(per_market)
    aggregate = _safe_dict(_safe_dict(readiness_scores).get("aggregate"))
    average_score = aggregate.get("average_evidence_readiness_score")
    if average_score is None:
        average_score = round(
            sum(item["current_score"] for item in per_market) / total_markets, 2
        ) if total_markets else 0

    low_market_ids = [
        item["market_id"] for item in per_market if item["readiness_band"] == "low"
    ]
    blocked_market_ids = [
        item["market_id"] for item in per_market if item["readiness_band"] == "blocked"
    ]
    unreviewed_market_ids = [
        item["market_id"] for item in per_market if not item["reviewed_by_openrouter"]
    ]
    needs_before_batch_ids = [
        item["market_id"]
        for item in per_market
        if item["needs_local_enrichment_before_future_openrouter_batch"]
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": GENERATION_MARKER,
        "source_inventory_path": SOURCE_PATHS["inventory_json"],
        "source_readiness_scores_path": SOURCE_PATHS["readiness_scores_json"],
        "source_completeness_contract_path": SOURCE_PATHS["completeness_contract_json"],
        "total_markets": total_markets,
        "high_count": band_counts.get("high", 0),
        "medium_count": band_counts.get("medium", 0),
        "low_count": band_counts.get("low", 0),
        "blocked_count": band_counts.get("blocked", 0),
        "eligible_for_future_llm_review_count": sum(
            1 for item in per_market if item["suitable_for_future_llm_review"]
        ),
        "eligible_for_future_openrouter_batch_count": sum(
            1 for item in per_market if item["suitable_for_future_openrouter_batch"]
        ),
        "needs_local_enrichment_count": sum(
            1 for item in per_market if item["needs_local_enrichment_before_review"]
        ),
        "needs_local_enrichment_before_future_openrouter_batch_count": len(
            needs_before_batch_ids
        ),
        "reviewed_count": sum(1 for item in per_market if item["reviewed_by_openrouter"]),
        "unreviewed_count": sum(1 for item in per_market if not item["reviewed_by_openrouter"]),
        "average_evidence_readiness_score": average_score,
        "low_readiness_market_ids": low_market_ids,
        "blocked_market_ids": blocked_market_ids,
        "unreviewed_market_ids": unreviewed_market_ids,
        "needs_local_enrichment_before_future_openrouter_batch_market_ids": needs_before_batch_ids,
        "per_market_readiness": per_market,
        "top_missing_fields": _top_missing_fields(per_market, readiness_scores),
        "recommended_next_local_enrichment_focus": _next_local_focus(readiness_scores),
        "gate_logic": dict(GATE_LOGIC),
        "safety_flags": dict(SAFETY_FLAGS),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }


def build_batch_readiness_gate(root=ROOT):
    summary = summarize_packet_readiness(root=root)
    return {
        "schema_version": GATE_VERSION,
        "gate_version": GATE_VERSION,
        "task_id": TASK_ID,
        "generated_by": GENERATED_BY,
        "generated_at_marker": GENERATION_MARKER,
        "status": "batch_readiness_gate_created",
        "generated_from": {
            "current_llm_market_packet_inventory": SOURCE_PATHS["inventory_json"],
            "current_llm_packet_evidence_readiness_scores": SOURCE_PATHS[
                "readiness_scores_json"
            ],
            "llm_market_packet_completeness_contract": SOURCE_PATHS[
                "completeness_contract_json"
            ],
        },
        "total_markets": summary["total_markets"],
        "high_count": summary["high_count"],
        "medium_count": summary["medium_count"],
        "low_count": summary["low_count"],
        "blocked_count": summary["blocked_count"],
        "eligible_for_future_llm_review_count": summary[
            "eligible_for_future_llm_review_count"
        ],
        "eligible_for_future_openrouter_batch_count": summary[
            "eligible_for_future_openrouter_batch_count"
        ],
        "needs_local_enrichment_count": summary["needs_local_enrichment_count"],
        "needs_local_enrichment_before_future_openrouter_batch_count": summary[
            "needs_local_enrichment_before_future_openrouter_batch_count"
        ],
        "reviewed_count": summary["reviewed_count"],
        "unreviewed_count": summary["unreviewed_count"],
        "average_evidence_readiness_score": summary["average_evidence_readiness_score"],
        "per_market_readiness": summary["per_market_readiness"],
        "low_readiness_market_ids": summary["low_readiness_market_ids"],
        "blocked_market_ids": summary["blocked_market_ids"],
        "unreviewed_market_ids": summary["unreviewed_market_ids"],
        "needs_local_enrichment_before_future_openrouter_batch_market_ids": summary[
            "needs_local_enrichment_before_future_openrouter_batch_market_ids"
        ],
        "top_missing_fields": summary["top_missing_fields"],
        "recommended_next_local_enrichment_focus": summary[
            "recommended_next_local_enrichment_focus"
        ],
        "gate_logic": summary["gate_logic"],
        "future_live_batch_scheduled": False,
        "future_openrouter_batch_approved": False,
        "future_llm_review_approved": False,
        "local_only": True,
        "no_live_calls": True,
        "no_trading_authority": True,
        "no_queue_authority": True,
        "no_runtime_authority": True,
        "no_wallet_or_order_authority": True,
        "operator_review_only": True,
        "safety_flags": dict(SAFETY_FLAGS),
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
        "network_calls_performed": 0,
    }


def render_batch_readiness_gate_markdown(gate):
    lines = [
        "# PMBOT Current LLM Batch Readiness Gate v1",
        "",
        f"- gate_version: {gate['gate_version']}",
        f"- task_id: {gate['task_id']}",
        f"- status: {gate['status']}",
        f"- generated_by: {gate['generated_by']}",
        f"- inventory_source: {gate['generated_from']['current_llm_market_packet_inventory']}",
        "- readiness_source: "
        f"{gate['generated_from']['current_llm_packet_evidence_readiness_scores']}",
        f"- contract_source: {gate['generated_from']['llm_market_packet_completeness_contract']}",
        "",
        "## Summary",
        "",
        f"- total_markets: {gate['total_markets']}",
        f"- high_count: {gate['high_count']}",
        f"- medium_count: {gate['medium_count']}",
        f"- low_count: {gate['low_count']}",
        f"- blocked_count: {gate['blocked_count']}",
        f"- eligible_for_future_llm_review_count: {gate['eligible_for_future_llm_review_count']}",
        "- eligible_for_future_openrouter_batch_count: "
        f"{gate['eligible_for_future_openrouter_batch_count']}",
        f"- needs_local_enrichment_count: {gate['needs_local_enrichment_count']}",
        "- needs_local_enrichment_before_future_openrouter_batch_count: "
        f"{gate['needs_local_enrichment_before_future_openrouter_batch_count']}",
        f"- reviewed_count: {gate['reviewed_count']}",
        f"- unreviewed_count: {gate['unreviewed_count']}",
        f"- average_evidence_readiness_score: {gate['average_evidence_readiness_score']}",
        "",
        "## Gate Logic",
        "",
    ]
    for band in VALID_READINESS_BANDS:
        lines.append(f"- {band}: {gate['gate_logic'][band]}")

    lines.extend(["", "## Low Readiness Markets", ""])
    if gate["low_readiness_market_ids"]:
        for market_id in gate["low_readiness_market_ids"]:
            lines.append(f"- {market_id}")
    else:
        lines.append("- none")

    lines.extend(["", "## Unreviewed Markets", ""])
    if gate["unreviewed_market_ids"]:
        for market_id in gate["unreviewed_market_ids"]:
            lines.append(f"- {market_id}")
    else:
        lines.append("- none")

    lines.extend(["", "## Top Missing Fields", ""])
    for item in gate["top_missing_fields"][:10]:
        lines.append(f"- {item['field']}: {item['market_count']}")

    lines.extend(["", "## Recommended Next Local Enrichment Focus", ""])
    for item in gate["recommended_next_local_enrichment_focus"]:
        lines.append(f"- {item}")

    lines.extend(["", "## Per-Market Readiness", ""])
    for item in gate["per_market_readiness"]:
        lines.append(
            "- "
            f"{item['market_id']}: band={item['readiness_band']}; "
            f"score={item['current_score']}; "
            f"future_llm_review={str(item['suitable_for_future_llm_review']).lower()}; "
            "future_openrouter_batch="
            f"{str(item['suitable_for_future_openrouter_batch']).lower()}; "
            "needs_local_enrichment_before_future_batch="
            f"{str(item['needs_local_enrichment_before_future_openrouter_batch']).lower()}"
        )

    lines.extend(
        [
            "",
            "## Safety Flags",
            "",
            "- local_only: true",
            "- no_live_calls: true",
            "- no_trading_authority: true",
            "- no_queue_authority: true",
            "- no_runtime_authority: true",
            "- no_dispatcher_authority: true",
            "- no_wallet_or_order_authority: true",
            "- operator_review_only: true",
            "- passive_context_only: true",
            "- acceptance_is_not_trading_approval: true",
            "- no_market_action_guidance: true",
            "- future_live_batch_scheduled: false",
            "- future_openrouter_batch_approved: false",
            "- future_llm_review_approved: false",
            "- openrouter_calls_performed: 0",
            "- polymarket_api_calls_performed: 0",
            "- external_network_calls_performed: 0",
            "",
        ]
    )
    return "\n".join(lines)


def export_packet_completeness_report(
    root=ROOT,
    json_path=SOURCE_PATHS["batch_readiness_gate_json"],
    markdown_path=SOURCE_PATHS["batch_readiness_gate_md"],
):
    gate = build_batch_readiness_gate(root=root)
    _write_json(json_path, gate, root=root)
    _write_text(markdown_path, render_batch_readiness_gate_markdown(gate), root=root)
    return gate


def write_current_llm_batch_readiness_gate_artifacts(root=ROOT):
    gate = export_packet_completeness_report(root=root)
    return {
        "task_id": TASK_ID,
        "status": "batch_readiness_gate_written",
        "files_written": [
            SOURCE_PATHS["batch_readiness_gate_json"],
            SOURCE_PATHS["batch_readiness_gate_md"],
        ],
        "total_markets": gate["total_markets"],
        "high_count": gate["high_count"],
        "medium_count": gate["medium_count"],
        "low_count": gate["low_count"],
        "blocked_count": gate["blocked_count"],
        "eligible_for_future_llm_review_count": gate[
            "eligible_for_future_llm_review_count"
        ],
        "eligible_for_future_openrouter_batch_count": gate[
            "eligible_for_future_openrouter_batch_count"
        ],
        "needs_local_enrichment_count": gate["needs_local_enrichment_count"],
        "openrouter_calls_performed": 0,
        "polymarket_api_calls_performed": 0,
        "external_network_calls_performed": 0,
    }
