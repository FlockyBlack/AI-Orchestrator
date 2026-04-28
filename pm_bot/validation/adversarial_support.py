import json
from pathlib import Path


REJECT_REASON_ORDER = [
    "stale_data",
    "low_liquidity",
    "wide_spread",
    "conflicting_signals",
    "resolved_market",
    "missing_market_status",
    "confidence_vs_data_mismatch",
]
WARNING_REASON_ORDER = [
    "correlation_conflict",
    "duplicate_snapshot",
    "outlier_price_move",
    "watchlist_only",
    "confidence_downgrade",
    "category_exposure_spike",
]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_replay_cases(root: Path):
    return load_json(root / "pm_bot" / "adversarial" / "adversarial_replay_cases.v1.json")["cases"]


def load_market_shock_scenarios(root: Path):
    return load_json(root / "pm_bot" / "adversarial" / "market_shock_scenarios.v1.json")["scenarios"]


def _dedupe_keep_order(values):
    seen = set()
    ordered = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def _base_reasons(inputs):
    reject_reasons = []
    warning_reasons = []
    if int(inputs.get("data_age_minutes", 0)) >= 180:
        reject_reasons.append("stale_data")
    if float(inputs.get("liquidity_usd", 0.0)) < 10000.0:
        reject_reasons.append("low_liquidity")
    if int(inputs.get("spread_bps", 0)) >= 250:
        reject_reasons.append("wide_spread")
    if inputs.get("signal_conflict", False):
        reject_reasons.append("conflicting_signals")
    if inputs.get("market_status") == "resolved" or inputs.get("resolved_candidate_visible", False):
        reject_reasons.append("resolved_market")
    if inputs.get("market_status") in {"unknown", "", None}:
        reject_reasons.append("missing_market_status")
    if int(inputs.get("confidence_score", 0)) >= 90 and int(inputs.get("data_quality_score", 100)) < 40:
        reject_reasons.append("confidence_vs_data_mismatch")
    if inputs.get("correlation_conflict", False):
        warning_reasons.append("correlation_conflict")
    if inputs.get("duplicate_snapshot", False):
        warning_reasons.append("duplicate_snapshot")
    if float(inputs.get("outlier_move_pct", 0.0)) >= 25.0:
        warning_reasons.append("outlier_price_move")
    if inputs.get("watchlist_only", False) or inputs.get("candidate_state") == "watchlist":
        warning_reasons.append("watchlist_only")
    if int(inputs.get("confidence_score", 0)) <= 55 or int(inputs.get("data_quality_score", 100)) < 50:
        warning_reasons.append("confidence_downgrade")
    if int(inputs.get("category_exposure_pct", 0)) >= 40:
        warning_reasons.append("category_exposure_spike")
    reject_reasons = [reason for reason in REJECT_REASON_ORDER if reason in reject_reasons]
    warning_reasons = [reason for reason in WARNING_REASON_ORDER if reason in warning_reasons]
    return reject_reasons, warning_reasons


def evaluate_market_inputs(inputs):
    reject_reasons, warning_reasons = _base_reasons(inputs)

    if "resolved_market" in reject_reasons:
        decision = "exclude"
    elif reject_reasons:
        decision = "reject"
    elif warning_reasons:
        decision = "watchlist"
    elif int(inputs.get("paper_edge_bps", 0)) >= 120 and int(inputs.get("confidence_score", 0)) >= 70:
        decision = "accept"
    else:
        decision = "watchlist"

    safety_flags = _dedupe_keep_order(reject_reasons + warning_reasons)
    risk_level = "high" if len(reject_reasons) >= 2 else "medium" if reject_reasons or len(warning_reasons) >= 2 else "low"
    return {
        "decision": decision,
        "reject_reasons": reject_reasons,
        "warning_reasons": warning_reasons,
        "safety_flags": safety_flags,
        "risk_level": risk_level,
        "paper_only_no_action_summary": "Paper-only replay validation. No real order, no wallet action, and no runtime execution.",
    }


def evaluate_replay_case(case):
    evaluation = evaluate_market_inputs(case["synthetic_market_inputs"])
    expected = case["expected_decision"]
    expected_reasons = case["expected_rejection_or_warning_reasons"]
    missing_expected = [reason for reason in expected_reasons if reason not in evaluation["safety_flags"]]
    is_false_positive = evaluation["decision"] == "accept" and expected != "accept"
    high_risk_false_positive = is_false_positive and evaluation["risk_level"] == "high"
    return {
        "case_id": case["case_id"],
        "market_id": case["synthetic_market_inputs"]["market_id"],
        "expected_decision": expected,
        "actual_decision": evaluation["decision"],
        "decision_matches_expected": evaluation["decision"] == expected,
        "reject_reasons": evaluation["reject_reasons"],
        "warning_reasons": evaluation["warning_reasons"],
        "safety_flags": evaluation["safety_flags"],
        "missing_expected_reasons": missing_expected,
        "is_false_positive": is_false_positive,
        "high_risk_false_positive": high_risk_false_positive,
        "risk_level": evaluation["risk_level"],
        "paper_only_no_action_summary": evaluation["paper_only_no_action_summary"],
        "fixture_only": case["fixture_only"],
        "paper_only": case["paper_only"],
    }


def apply_market_shock(scenario):
    shocked = dict(scenario["base_inputs"])
    shocked.update(scenario["shock_overrides"])
    return shocked


def evaluate_market_shock_scenario(scenario):
    shocked_inputs = apply_market_shock(scenario)
    evaluation = evaluate_market_inputs(shocked_inputs)
    expected = scenario["expected_decision"]
    expected_reasons = scenario["expected_reasons"]
    missing_expected = [reason for reason in expected_reasons if reason not in evaluation["safety_flags"]]
    return {
        "scenario_id": scenario["scenario_id"],
        "shock_type": scenario["shock_type"],
        "expected_decision": expected,
        "actual_decision": evaluation["decision"],
        "decision_matches_expected": evaluation["decision"] == expected,
        "safety_flags": evaluation["safety_flags"],
        "reject_reasons": evaluation["reject_reasons"],
        "warning_reasons": evaluation["warning_reasons"],
        "missing_expected_reasons": missing_expected,
        "paper_only_no_action_summary": evaluation["paper_only_no_action_summary"],
        "shocked_inputs": shocked_inputs,
        "fixture_only": scenario["fixture_only"],
        "paper_only": scenario["paper_only"],
    }


def count_reasons(entries, field_name):
    counts = {}
    for entry in entries:
        for reason in entry[field_name]:
            counts[reason] = counts.get(reason, 0) + 1
    return dict(sorted(counts.items()))


def top_reasons(entries, field_name, limit):
    counts = count_reasons(entries, field_name)
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [reason for reason, _ in ranked[:limit]]
