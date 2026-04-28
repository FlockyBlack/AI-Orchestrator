import json
from collections import defaultdict
from pathlib import Path


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_bundle(root: Path):
    return load_json(root / "pm_bot" / "fixtures" / "multi_market_fixture_bundle.v1.json")


def evaluate_market(market, constraints):
    plan = market.get("paper_position_plan") or {}
    warnings = []
    rejection_reasons = []
    allocation = round(float(plan.get("allocation_usd", 0.0)), 4)
    entry_price = float(plan.get("entry_price", 0.0)) if plan else 0.0
    target_price = float(plan.get("target_price", 0.0)) if plan else 0.0
    quantity = int(plan.get("quantity", 0)) if plan else 0
    expected_delta = round((target_price - entry_price) * quantity, 4)

    excluded = market["status"] in {"resolved", "closed"}
    if excluded:
        warnings.append("resolved_or_closed_market")

    if int(market.get("stale_hours", 0)) > int(constraints["max_stale_hours"]):
        warnings.append("stale_data")
        rejection_reasons.append("stale_data")

    if float(market.get("liquidity_usd_24h", 0.0)) < float(constraints["min_liquidity_usd_24h"]):
        warnings.append("low_liquidity")
        rejection_reasons.append("low_liquidity")

    if int(market.get("spread_bps_assumption", 0)) > int(constraints["max_spread_bps"]):
        warnings.append("wide_spread")
        rejection_reasons.append("wide_spread")

    if plan and int(plan.get("expected_edge_bps", 0)) <= 0:
        warnings.append("negative_edge")
        rejection_reasons.append("negative_edge")

    if plan and not market.get("research_notes"):
        warnings.append("missing_research_notes")

    if plan and allocation > float(constraints["max_market_allocation_usd"]):
        warnings.append("market_allocation_cap")
        rejection_reasons.append("market_allocation_cap")

    if market.get("risk_metadata", {}).get("concentration_candidate"):
        warnings.append("high_concentration_candidate")

    accepted_candidate = bool(plan) and not excluded and not rejection_reasons
    candidate_status = "accepted" if accepted_candidate else "rejected" if plan and not excluded else "excluded"

    return {
        "market_id": market["market_id"],
        "title": market["title"],
        "category": market["category"],
        "status": market["status"],
        "allocation_usd": allocation,
        "quantity": quantity,
        "entry_price": entry_price,
        "target_price": target_price,
        "expected_edge_bps": int(plan.get("expected_edge_bps", 0)) if plan else 0,
        "expected_value_delta": expected_delta,
        "accepted_candidate": accepted_candidate,
        "excluded": excluded,
        "candidate_status": candidate_status,
        "warnings": sorted(set(warnings)),
        "rejection_reasons": sorted(set(rejection_reasons)),
        "correlated_group": market.get("risk_metadata", {}).get("correlated_group", "uncategorized"),
        "paper_position_plan_present": bool(plan),
    }


def summarize_bundle(bundle):
    constraints = bundle["portfolio_constraints"]
    analyses = [evaluate_market(market, constraints) for market in bundle["markets"]]
    accepted = [item for item in analyses if item["accepted_candidate"]]
    rejected = [item for item in analyses if item["candidate_status"] == "rejected"]
    excluded = [item for item in analyses if item["excluded"]]

    exposure_by_category = defaultdict(float)
    exposure_by_market = {}
    correlated_exposure = defaultdict(float)
    portfolio_warnings = []
    portfolio_warning_details = []

    allocated = round(sum(item["allocation_usd"] for item in accepted), 4)
    total_capital = round(float(constraints["total_paper_capital_usd"]), 4)
    allocation_ratio = round((allocated / total_capital) if total_capital else 0.0, 4)

    for item in accepted:
        exposure_by_market[item["market_id"]] = round(item["allocation_usd"], 4)
        exposure_by_category[item["category"]] += item["allocation_usd"]
        correlated_exposure[item["correlated_group"]] += item["allocation_usd"]

    for category, amount in sorted(exposure_by_category.items()):
        amount = round(amount, 4)
        exposure_by_category[category] = amount
        if amount > float(constraints["max_category_allocation_usd"]):
            portfolio_warnings.append(f"category_concentration:{category}")
            portfolio_warning_details.append(
                {
                    "warning": f"category_concentration:{category}",
                    "allocation_usd": amount,
                }
            )

    for group, amount in sorted(correlated_exposure.items()):
        amount = round(amount, 4)
        correlated_exposure[group] = amount
        if amount > float(constraints["max_correlated_group_allocation_usd"]):
            portfolio_warnings.append(f"correlated_group:{group}")
            portfolio_warning_details.append(
                {
                    "warning": f"correlated_group:{group}",
                    "allocation_usd": amount,
                }
            )

    if allocation_ratio > float(constraints["max_total_allocation_ratio"]):
        portfolio_warnings.append("portfolio_exposure_cap")
        portfolio_warning_details.append(
            {
                "warning": "portfolio_exposure_cap",
                "allocation_ratio": allocation_ratio,
            }
        )

    largest = max(accepted, key=lambda item: (item["allocation_usd"], item["market_id"])) if accepted else None
    warning_counts = defaultdict(int)
    for item in analyses:
        for warning in item["warnings"]:
            warning_counts[warning] += 1
    for warning in portfolio_warnings:
        warning_counts[warning] += 1

    risk_flags = sorted(
        set(
            list(warning_counts.keys())
            + [reason for item in rejected for reason in item["rejection_reasons"]]
            + [warning for warning in portfolio_warnings]
        )
    )

    return {
        "constraints": constraints,
        "market_analyses": analyses,
        "accepted_candidates": accepted,
        "rejected_candidates": rejected,
        "excluded_markets": excluded,
        "accepted_candidate_count": len(accepted),
        "rejected_candidate_count": len(rejected),
        "excluded_market_count": len(excluded),
        "paper_candidate_count": sum(1 for item in analyses if item["paper_position_plan_present"] and not item["excluded"]),
        "total_paper_capital_usd": total_capital,
        "allocated_paper_capital_usd": allocated,
        "unallocated_paper_capital_usd": round(total_capital - allocated, 4),
        "allocation_ratio": allocation_ratio,
        "exposure_by_market": dict(sorted(exposure_by_market.items())),
        "exposure_by_category": {key: round(value, 4) for key, value in sorted(exposure_by_category.items())},
        "correlated_group_exposure": {key: round(value, 4) for key, value in sorted(correlated_exposure.items())},
        "largest_paper_position": {
            "market_id": largest["market_id"],
            "allocation_usd": largest["allocation_usd"],
            "category": largest["category"],
        }
        if largest
        else None,
        "warning_counts": dict(sorted(warning_counts.items())),
        "portfolio_warnings": sorted(portfolio_warnings),
        "portfolio_warning_details": portfolio_warning_details,
        "estimated_paper_value_delta": round(sum(item["expected_value_delta"] for item in accepted), 4),
        "risk_flags": risk_flags,
    }
