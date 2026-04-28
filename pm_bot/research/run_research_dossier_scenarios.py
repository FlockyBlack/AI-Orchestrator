import argparse
import importlib.util
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path


TASK_ID = "PMBOT-RESEARCH-002-RESEARCH-DOSSIER-SCENARIO-COVERAGE"
SCHEMA_VERSION = "research_dossier_scenarios_result.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCENARIOS = ROOT / "pm_bot" / "research" / "research_dossier_scenarios.v1.json"
SINGLE_DOSSIER_RUNNER = ROOT / "pm_bot" / "research" / "run_single_market_research_dossier.py"
DECISIONS = ("no_action", "watchlist", "paper_candidate")
SAFETY_FLAGS = {
    "offline_only": True,
    "paper_only": True,
    "live_fetcher_implemented": False,
    "api_used": False,
    "network_used": False,
    "wallet_used": False,
    "real_order_created": False,
    "trading_allowed": False,
    "runtime_wiring_changed": False,
    "dispatcher_touched": False,
    "prompt_automation_added": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Run deterministic offline research dossier scenario coverage.")
    parser.add_argument("--scenarios", default=str(DEFAULT_SCENARIOS.relative_to(ROOT)))
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _resolve_path(path):
    value = Path(path)
    if value.is_absolute():
        return value
    return ROOT / value


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_single_dossier_module():
    spec = importlib.util.spec_from_file_location("single_market_research_dossier", SINGLE_DOSSIER_RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def _scenario_flags(scenario, packet):
    current_date = _parse_date(packet.get("current_date"))
    stale_after_days = int(scenario.get("stale_after_days", 45))
    stale_source_ids = []
    if current_date is not None:
        for source in packet.get("sources", []):
            published_at = _parse_date(source.get("published_at"))
            if published_at is not None and (current_date - published_at).days > stale_after_days:
                stale_source_ids.append(source.get("source_id"))
    notes = packet.get("operator_notes", [])
    lowered_notes = " ".join(str(note).lower() for note in notes)
    return {
        "missing_resolution_criteria": not str(packet.get("resolution_criteria") or "").strip(),
        "stale_source_count": len(stale_source_ids),
        "stale_source_ids": stale_source_ids,
        "operator_note_requires_manual_review": "manual review" in lowered_notes and "required" in lowered_notes,
    }


def _evaluate_packet(single_dossier, scenario_id, packet):
    sources = packet.get("sources") if isinstance(packet.get("sources"), list) else []
    yes_price = single_dossier._float_or_none(packet.get("yes_price"))
    no_price = single_dossier._float_or_none(packet.get("no_price"))
    source_analysis = single_dossier._analyze_sources(sources)
    missing = single_dossier._missing_information(packet, source_analysis, yes_price)
    probability_range = single_dossier._probability_estimate_range(yes_price, source_analysis)
    edge = single_dossier._edge_estimate(yes_price, probability_range)
    decision, reason_codes = single_dossier._decision(packet, source_analysis, missing, probability_range, edge)
    return {
        "scenario_id": scenario_id,
        "market": {
            "market_id": packet.get("market_id"),
            "market_title": packet.get("market_title"),
            "market_question": packet.get("market_question"),
            "resolution_criteria": packet.get("resolution_criteria"),
            "yes_price": yes_price,
            "no_price": no_price,
            "current_date": packet.get("current_date"),
        },
        "sources_count": len(sources),
        "yes_evidence_count": len(source_analysis["yes_evidence"]),
        "no_evidence_count": len(source_analysis["no_evidence"]),
        "uncertainty_factor_count": len(source_analysis["uncertainty_factors"]),
        "reliable_sources": source_analysis["reliable_sources"],
        "missing_information": missing,
        "probability_estimate_range": probability_range,
        "edge_estimate_vs_market": edge,
        "actual_decision": decision,
        "reason_codes": reason_codes,
        "human_review_note": single_dossier._human_review_note(decision, reason_codes),
        "operator_notes": packet.get("operator_notes", []),
        "paper_orders_created": 0,
        "workspace_state_written": False,
        "safety_flags": SAFETY_FLAGS,
    }


def run_scenarios(scenarios_path=None):
    scenario_file = _resolve_path(scenarios_path) if scenarios_path else DEFAULT_SCENARIOS
    payload = _load_json(scenario_file)
    single_dossier = _load_single_dossier_module()
    scenario_results = []
    decision_counts = Counter({decision: 0 for decision in DECISIONS})
    reason_counts = Counter()
    total_paper_orders_created = 0

    for scenario in payload["scenarios"]:
        scenario_id = scenario["scenario_id"]
        report = _evaluate_packet(single_dossier, scenario_id, scenario["packet"])
        expected_decision = scenario["expected_decision"]
        actual_decision = report["actual_decision"]
        expected_reason_codes = scenario.get("expected_reason_codes", [])
        expected_reason_codes_present = all(code in report["reason_codes"] for code in expected_reason_codes)
        decision_passed = actual_decision == expected_decision
        decision_counts[actual_decision] += 1
        reason_counts.update(report["reason_codes"])
        total_paper_orders_created += report["paper_orders_created"]
        scenario_results.append(
            {
                "scenario_id": scenario_id,
                "description": scenario.get("description"),
                "expected_decision": expected_decision,
                "actual_decision": actual_decision,
                "expected_decision_passed": decision_passed,
                "expected_reason_codes": expected_reason_codes,
                "expected_reason_codes_present": expected_reason_codes_present,
                "reason_codes": report["reason_codes"],
                "market_id": report["market"]["market_id"],
                "sources_count": report["sources_count"],
                "yes_evidence_count": report["yes_evidence_count"],
                "no_evidence_count": report["no_evidence_count"],
                "uncertainty_factor_count": report["uncertainty_factor_count"],
                "reliable_sources": report["reliable_sources"],
                "missing_information": report["missing_information"],
                "probability_estimate_range": report["probability_estimate_range"],
                "edge_estimate_vs_market": report["edge_estimate_vs_market"],
                "scenario_flags": _scenario_flags(scenario, scenario["packet"]),
                "paper_orders_created": report["paper_orders_created"],
                "workspace_state_written": report["workspace_state_written"],
                "safety_flags": report["safety_flags"],
            }
        )

    all_expected_decisions_passed = all(row["expected_decision_passed"] for row in scenario_results)
    all_expected_reason_codes_present = all(row["expected_reason_codes_present"] for row in scenario_results)
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "fixture_only": bool(payload.get("fixture_only")),
        "local_only": bool(payload.get("local_only")),
        "scenarios_path": str(scenario_file),
        "scenario_count": len(scenario_results),
        "no_action_count": decision_counts["no_action"],
        "watchlist_count": decision_counts["watchlist"],
        "paper_candidate_count": decision_counts["paper_candidate"],
        "paper_orders_created": total_paper_orders_created,
        "decision_reason_counts": dict(sorted(reason_counts.items())),
        "all_expected_decisions_passed": all_expected_decisions_passed,
        "all_expected_reason_codes_present": all_expected_reason_codes_present,
        "scenario_results": scenario_results,
        "safety_flags": SAFETY_FLAGS,
        "limitations": [
            "Uses only local JSON scenario fixtures and deterministic dossier functions.",
            "Does not fetch live sources, call APIs, use credentials, touch wallets, create orders, trade, or write runtime state.",
            "Paper-candidate remains a label only and is not connected to paper order planning.",
        ],
    }


def _md(value):
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(report):
    lines = [
        "# Research Dossier Scenario Coverage",
        "",
        f"- Task ID: {report['task_id']}",
        f"- Scenario count: {report['scenario_count']}",
        f"- No action count: {report['no_action_count']}",
        f"- Watchlist count: {report['watchlist_count']}",
        f"- Paper candidate count: {report['paper_candidate_count']}",
        f"- Paper orders created: {report['paper_orders_created']}",
        f"- All expected decisions passed: {str(report['all_expected_decisions_passed']).lower()}",
        f"- All expected reason codes present: {str(report['all_expected_reason_codes_present']).lower()}",
        "",
        "## Decision Reason Counts",
        "",
    ]
    for reason, count in report["decision_reason_counts"].items():
        lines.append(f"- {reason}: {count}")
    lines.extend(
        [
            "",
            "## Scenarios",
            "",
            "| scenario_id | expected | actual | passed | reason_codes | paper_orders_created |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in report["scenario_results"]:
        lines.append(
            f"| {_md(row['scenario_id'])} | {_md(row['expected_decision'])} | {_md(row['actual_decision'])} | "
            f"{_md(str(row['expected_decision_passed']).lower())} | {_md(json.dumps(row['reason_codes'], sort_keys=True))} | "
            f"{_md(row['paper_orders_created'])} |"
        )
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; dispatcher_touched=false; prompt_automation_added=false",
            "",
        ]
    )
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    report = run_scenarios(args.scenarios)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    if not report["all_expected_decisions_passed"] or not report["all_expected_reason_codes_present"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
