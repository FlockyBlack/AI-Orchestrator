import json
from pathlib import Path


CONFIDENCE_BANDS = (
    ("high", 75),
    ("medium", 60),
    ("low", 45),
)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_bundle(root: Path):
    return load_json(root / "pm_bot" / "fixtures" / "multi_market_fixture_bundle.v1.json")


def load_cases(root: Path):
    return load_json(root / "pm_bot" / "research" / "research_quality_cases.v1.json")


def clamp(value, lower=0, upper=100):
    return max(lower, min(upper, int(round(value))))


def _spread_score(spread_bps: int):
    if spread_bps <= 40:
        return 95
    if spread_bps <= 80:
        return 80
    if spread_bps <= 140:
        return 60
    if spread_bps <= 200:
        return 35
    return 20


def _freshness_score(stale_hours: int):
    if stale_hours <= 4:
        return 95
    if stale_hours <= 12:
        return 80
    if stale_hours <= 24:
        return 65
    if stale_hours <= 48:
        return 40
    return 15


def _liquidity_score(liquidity_usd: float):
    if liquidity_usd >= 200000:
        return 95
    if liquidity_usd >= 120000:
        return 82
    if liquidity_usd >= 80000:
        return 68
    if liquidity_usd >= 50000:
        return 55
    if liquidity_usd >= 25000:
        return 35
    return 15


def _research_completeness_score(inputs):
    score = 50
    if inputs.get("research_note_present", False):
        score += 25
    if inputs.get("paper_notes_present", False):
        score += 10
    if inputs.get("notes_quality") == "strong":
        score += 10
    elif inputs.get("notes_quality") == "partial":
        score += 0
    else:
        score -= 10
    score -= 10 * int(inputs.get("missing_fields_count", 0))
    return clamp(score)


def _signal_strength_score(inputs):
    edge_bps = int(inputs.get("expected_edge_bps", 0))
    support_count = int(inputs.get("supporting_signal_count", 0))
    contradiction = int(inputs.get("contradiction_level", 0))
    thesis = int(inputs.get("thesis_clarity", 0))
    base = 50 + min(max(edge_bps, -300), 500) / 10
    base += support_count * 6
    base += (thesis - 50) * 0.3
    base -= contradiction * 0.4
    if inputs.get("conflict_flag", False):
        base -= 18
    return clamp(base)


def _risk_quality_score(level: str):
    mapping = {
        "low": 90,
        "medium": 65,
        "high": 35,
    }
    return mapping.get(level, 50)


def _collect_penalties(case, component_scores):
    penalties = []
    signal_inputs = case["signal_inputs"]
    risk_inputs = case["risk_inputs"]
    data_quality = case["data_quality_inputs"]

    if int(signal_inputs.get("expected_edge_bps", 0)) <= 0:
        penalties.append({"reason": "insufficient_edge", "points": 20})
    if risk_inputs.get("liquidity_usd_24h", 0.0) < 50000.0:
        penalties.append({"reason": "low_liquidity", "points": 20})
    if int(risk_inputs.get("spread_bps", 0)) > 140:
        penalties.append({"reason": "wide_spread", "points": 18})
    if int(data_quality.get("stale_hours", 0)) > 24:
        penalties.append({"reason": "stale_data", "points": 18})
    if int(signal_inputs.get("contradiction_level", 0)) >= 75 or signal_inputs.get("conflict_flag", False):
        penalties.append({"reason": "conflicting_signals", "points": 18})
    if not data_quality.get("research_note_present", False):
        penalties.append({"reason": "missing_research_notes", "points": 8})
    if risk_inputs.get("correlated_exposure_level") == "high":
        penalties.append({"reason": "correlated_exposure", "points": 12})
    if risk_inputs.get("concentration_level") == "high":
        penalties.append({"reason": "concentration_risk", "points": 12})
    if risk_inputs.get("resolved_or_closed", False):
        penalties.append({"reason": "resolved_or_closed_market", "points": 100})
    if risk_inputs.get("risk_level") == "high":
        penalties.append({"reason": "high_risk_profile", "points": 10})
    if signal_inputs.get("paper_only_no_action", False):
        penalties.append({"reason": "paper_only_no_action", "points": 15})

    return penalties


def compute_confidence_breakdown(case):
    signal_inputs = case["signal_inputs"]
    risk_inputs = case["risk_inputs"]
    data_quality = case["data_quality_inputs"]

    component_scores = {
        "signal_strength": _signal_strength_score(signal_inputs),
        "data_freshness": _freshness_score(int(data_quality.get("stale_hours", 0))),
        "liquidity_quality": _liquidity_score(float(risk_inputs.get("liquidity_usd_24h", 0.0))),
        "spread_quality": _spread_score(int(risk_inputs.get("spread_bps", 0))),
        "research_completeness": _research_completeness_score(data_quality),
        "correlation_risk": _risk_quality_score(risk_inputs.get("correlated_exposure_level", "medium")),
        "concentration_risk": _risk_quality_score(risk_inputs.get("concentration_level", "medium")),
        "scenario_consistency": clamp(int(signal_inputs.get("scenario_consistency", 50))),
        "audit_safety": 100 if case.get("fixture_only") and case.get("paper_only") else 0,
    }

    penalties = _collect_penalties(case, component_scores)
    warnings = [item["reason"] for item in penalties if item["reason"] not in {"resolved_or_closed_market", "insufficient_edge"}]
    hard_reject_reasons = [
        item["reason"]
        for item in penalties
        if item["reason"] in {"resolved_or_closed_market", "low_liquidity", "wide_spread", "stale_data", "insufficient_edge", "conflicting_signals"}
    ]

    raw_score = sum(component_scores.values()) / len(component_scores)
    penalty_total = sum(item["points"] for item in penalties)
    total_confidence_score = clamp(raw_score - penalty_total)

    missing_information = []
    if not data_quality.get("research_note_present", False):
        missing_information.append("research_note")
    if int(data_quality.get("missing_fields_count", 0)) > 0:
        missing_information.append("incomplete_case_fields")
    if int(signal_inputs.get("supporting_signal_count", 0)) < 2:
        missing_information.append("limited_supporting_signals")

    if risk_inputs.get("resolved_or_closed", False):
        confidence_band = "reject"
        final_decision = "exclude"
    elif hard_reject_reasons:
        confidence_band = "reject"
        final_decision = "reject"
    elif signal_inputs.get("paper_only_no_action", False):
        confidence_band = "low" if total_confidence_score >= 45 else "reject"
        final_decision = "no_action"
    elif total_confidence_score >= 75 and risk_inputs.get("risk_level") != "high" and not missing_information:
        confidence_band = "high"
        final_decision = "accept"
    elif total_confidence_score >= 55:
        confidence_band = "medium" if total_confidence_score >= 60 else "low"
        final_decision = "watchlist"
    elif total_confidence_score >= 40:
        confidence_band = "low"
        final_decision = "watchlist"
    else:
        confidence_band = "reject"
        final_decision = "reject"

    summary = {
        "accept": "Synthetic paper candidate clears deterministic quality gates.",
        "watchlist": "Synthetic paper candidate remains inspectable but needs more evidence before paper sizing.",
        "reject": "Synthetic paper candidate fails deterministic quality gates and stays no-action.",
        "exclude": "Resolved or closed synthetic market is excluded from paper research consideration.",
        "no_action": "Paper-only monitoring case intentionally avoids any paper position proposal.",
    }[final_decision]

    return {
        "case_id": case["case_id"],
        "market_id": case["market_id"],
        "total_confidence_score": total_confidence_score,
        "confidence_band": confidence_band,
        "component_scores": component_scores,
        "penalties": penalties,
        "warnings": sorted(set(warnings)),
        "hard_reject_reasons": sorted(set(hard_reject_reasons)),
        "missing_information": missing_information,
        "final_decision": final_decision,
        "decision_support_summary": summary,
        "paper_research_only": True,
        "no_real_order_statement": "Paper/research only. No real order, no wallet action, no runtime execution.",
    }


def _positive_factors(case, breakdown):
    signal_inputs = case["signal_inputs"]
    risk_inputs = case["risk_inputs"]
    factors = []
    if int(signal_inputs.get("expected_edge_bps", 0)) > 0:
        factors.append(f"positive synthetic edge of {signal_inputs['expected_edge_bps']} bps")
    if int(signal_inputs.get("supporting_signal_count", 0)) >= 2:
        factors.append("multiple supporting synthetic signals are present")
    if float(risk_inputs.get("liquidity_usd_24h", 0.0)) >= 50000.0:
        factors.append("liquidity is above the local paper research floor")
    if int(risk_inputs.get("spread_bps", 0)) <= 80:
        factors.append("spread assumptions are manageable for a paper study")
    if case["data_quality_inputs"].get("research_note_present", False):
        factors.append("research notes are present for review")
    return factors


def _negative_factors(case, breakdown):
    negatives = []
    reasons = breakdown["hard_reject_reasons"] + [item["reason"] for item in breakdown["penalties"]]
    if "insufficient_edge" in reasons:
        negatives.append("edge estimate is not positive enough to justify a paper candidate")
    if "conflicting_signals" in reasons:
        negatives.append("signals conflict with each other and reduce directional clarity")
    if "missing_research_notes" in reasons:
        negatives.append("research narrative is incomplete")
    if "paper_only_no_action" in reasons:
        negatives.append("case is intentionally scoped as monitoring-only")
    return sorted(set(negatives))


def _risk_factors(case, breakdown):
    risk_inputs = case["risk_inputs"]
    factors = []
    if "low_liquidity" in [item["reason"] for item in breakdown["penalties"]]:
        factors.append("liquidity is below the deterministic floor")
    if "wide_spread" in [item["reason"] for item in breakdown["penalties"]]:
        factors.append("spread assumptions are too wide for a clean paper entry")
    if risk_inputs.get("correlated_exposure_level") == "high":
        factors.append("correlated exposure is already elevated")
    if risk_inputs.get("concentration_level") == "high":
        factors.append("concentration risk is elevated")
    if risk_inputs.get("risk_level") == "high":
        factors.append("overall risk profile is high despite signal strength")
    return factors


def _data_quality_factors(case, breakdown):
    data_quality = case["data_quality_inputs"]
    factors = []
    if int(data_quality.get("stale_hours", 0)) > 24:
        factors.append("fixture timestamp is stale for deterministic review")
    if not data_quality.get("research_note_present", False):
        factors.append("research note is missing")
    if int(data_quality.get("missing_fields_count", 0)) > 0:
        factors.append("some case fields are incomplete")
    return factors


def build_signal_explanation(case):
    breakdown = compute_confidence_breakdown(case)
    headline_map = {
        "accept": "Accepted paper candidate with inspectable rationale.",
        "watchlist": "Watchlist paper candidate needs tighter evidence before sizing.",
        "reject": "Rejected paper candidate due to deterministic quality failures.",
        "exclude": "Excluded case because the synthetic market is resolved or closed.",
        "no_action": "No-action monitoring case kept outside paper positioning.",
    }
    explanation_steps = [
        "Load the deterministic research case and confirm fixture-only / paper-only scope.",
        "Score signal strength, freshness, liquidity, spread, research completeness, and risk concentration components.",
        "Apply hard rejections for resolved markets, stale data, low liquidity, wide spread, insufficient edge, or conflicting signals.",
        "Translate the component scores and penalties into a confidence band and paper-only decision.",
    ]
    return {
        "case_id": case["case_id"],
        "market_id": case["market_id"],
        "final_decision": breakdown["final_decision"],
        "headline": headline_map[breakdown["final_decision"]],
        "positive_factors": _positive_factors(case, breakdown),
        "negative_factors": _negative_factors(case, breakdown),
        "risk_factors": _risk_factors(case, breakdown),
        "data_quality_factors": _data_quality_factors(case, breakdown),
        "missing_information": breakdown["missing_information"],
        "explanation_steps": explanation_steps,
        "confidence_band": breakdown["confidence_band"],
        "confidence_score": breakdown["total_confidence_score"],
        "paper_only_action": {
            "accept": "paper_candidate_only",
            "watchlist": "watchlist_only",
            "reject": "reject_no_action",
            "exclude": "exclude_no_action",
            "no_action": "monitor_only",
        }[breakdown["final_decision"]],
        "no_real_order_statement": breakdown["no_real_order_statement"],
        "safety_boundaries": [
            "fixture_only",
            "paper_only",
            "local_only",
            "no_network",
            "no_live_api",
            "no_wallet",
            "no_real_orders",
            "no_runtime_wiring",
        ],
    }


def build_reasoning_trace(case):
    breakdown = compute_confidence_breakdown(case)
    explanation = build_signal_explanation(case)
    normalized_case = {
        "case_id": case["case_id"],
        "market_id": case["market_id"],
        "category": case["category"],
        "candidate_type": case["candidate_type"],
        "signal_inputs": case["signal_inputs"],
        "risk_inputs": case["risk_inputs"],
        "data_quality_inputs": case["data_quality_inputs"],
    }
    return {
        "trace_id": f"{case['case_id']}_trace",
        "case_id": case["case_id"],
        "input_fixture": case,
        "normalized_research_case": normalized_case,
        "confidence_components": breakdown["component_scores"],
        "penalties": breakdown["penalties"],
        "risk_flags": explanation["risk_factors"],
        "data_quality_flags": explanation["data_quality_factors"],
        "explanation_steps": explanation["explanation_steps"],
        "final_paper_only_decision": breakdown["final_decision"],
        "confidence_band": breakdown["confidence_band"],
        "confidence_score": breakdown["total_confidence_score"],
        "no_action_safety_confirmation": "No live action, no wallet usage, no order placement, and no runtime wiring.",
    }


def sort_cases_for_comparison(cases):
    decision_rank = {"accept": 0, "watchlist": 1, "no_action": 2, "reject": 3, "exclude": 4}
    enriched = []
    for case in cases:
        breakdown = compute_confidence_breakdown(case)
        enriched.append((case, breakdown))
    enriched.sort(
        key=lambda item: (
            decision_rank[item[1]["final_decision"]],
            -item[1]["total_confidence_score"],
            item[0]["case_id"],
        )
    )
    return enriched


def scorecard_sections(root: Path):
    cases = load_cases(root)["cases"]
    case_ids = {case["case_id"] for case in cases}
    decisions = {compute_confidence_breakdown(case)["final_decision"] for case in cases}
    warnings = {reason for case in cases for reason in case["expected_rejection_or_warning_reasons"]}
    sections = {
        "fixture_coverage": 100 if len(cases) >= 12 else 70,
        "scenario_coverage": 100 if len(case_ids) == len(cases) else 60,
        "explainability_completeness": 95 if {"accept", "watchlist", "reject", "exclude", "no_action"} <= decisions else 70,
        "rejection_coverage": 95 if {"low_liquidity", "wide_spread", "stale_data", "conflicting_signals"} <= warnings else 70,
        "portfolio_risk_coverage": 90 if {"correlated_exposure", "concentration_risk"} <= warnings else 65,
        "dashboard_coverage": 85,
        "audit_coverage": 90,
        "determinism": 100,
        "safety_boundary_clarity": 100,
    }
    return sections
