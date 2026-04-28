import argparse
import importlib.util
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-BRAIN-037-THRESHOLD-HIT-POLICY-SCENARIO-COVERAGE"
SCHEMA_VERSION = "threshold_hit_policy_scenario_results.v1"
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCENARIOS = ROOT / "pm_bot" / "paper" / "threshold_hit_policy_scenarios.v1.json"
DEFAULT_REFERENCE_CONTEXT = ROOT / "pm_bot" / "paper" / "threshold_hit_reference_context.v1.json"
DEFAULT_DECISION_POLICY = ROOT / "pm_bot" / "paper" / "threshold_hit_decision_policy.v1.json"
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

_REVIEW_MODULE = None
_TRIAGE_MODULE = None


def _default_scenarios_arg():
    return str(DEFAULT_SCENARIOS.relative_to(ROOT))


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Run deterministic offline crypto threshold-hit policy scenarios.")
    parser.add_argument("--scenarios", default=_default_scenarios_arg())
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


def _load_module(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"Unable to load module: {path}")
    spec.loader.exec_module(module)
    return module


def _load_review_module():
    global _REVIEW_MODULE
    if _REVIEW_MODULE is None:
        _REVIEW_MODULE = _load_module(
            ROOT / "pm_bot" / "paper" / "run_crypto_threshold_hit_review_table.py",
            "pmbot_threshold_hit_review_for_policy_scenarios",
        )
    return _REVIEW_MODULE


def _load_triage_module():
    global _TRIAGE_MODULE
    if _TRIAGE_MODULE is None:
        _TRIAGE_MODULE = _load_module(
            ROOT / "pm_bot" / "paper" / "run_crypto_threshold_hit_triage_report.py",
            "pmbot_threshold_hit_triage_for_policy_scenarios",
        )
    return _TRIAGE_MODULE


def _load_scenario_suite(path):
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ValueError("scenario fixture must be a JSON object")
    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("scenario fixture must include a non-empty scenarios list")
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            raise ValueError("each scenario must be a JSON object")
        if not scenario.get("scenario_id"):
            raise ValueError("each scenario must include scenario_id")
        if not isinstance(scenario.get("market"), dict):
            raise ValueError(f"scenario must include a market object: {scenario.get('scenario_id')}")
    return payload


def _scenario_reference_context(base_context, scenario):
    reference_assets = scenario.get("reference_assets")
    if reference_assets is None:
        return base_context
    assets = {}
    base_assets = base_context.get("assets", {})
    for asset in reference_assets:
        key = str(asset).upper()
        if key in base_assets:
            assets[key] = base_assets[key]
    context = dict(base_context)
    context["assets"] = assets
    return context


def _assets_with_reference_price(reference_context):
    assets = reference_context.get("assets", {})
    result = []
    for asset, entry in assets.items():
        if isinstance(entry, dict) and entry.get("reference_price") is not None:
            result.append(str(asset).upper())
    return sorted(set(result))


def _reason_counts(rows):
    counts = {}
    for row in rows:
        for code in row["reason_codes"]:
            counts[code] = counts.get(code, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def _decision_counts(rows):
    decisions = ("no_action", "watchlist", "policy_blocked", "paper_candidate")
    return {decision: sum(1 for row in rows if row["actual_decision"] == decision) for decision in decisions}


def _expected_reason_codes(scenario):
    return sorted(str(code) for code in scenario.get("expected_reason_codes", []))


def _scenario_source(scenario_id):
    return f"embedded_threshold_hit_policy_scenario:{scenario_id}"


def _unsupported_result(scenario, triage_report):
    candidate = triage_report["candidate_table"][0] if triage_report["candidate_table"] else {}
    reason_codes = [candidate["reason_code"]] if candidate.get("reason_code") else []
    actual_decision = "triage_rejected" if candidate else "not_threshold_hit_candidate"
    expected_reason_codes = _expected_reason_codes(scenario)
    decision_matches = actual_decision == scenario["expected_decision"]
    reason_codes_match = reason_codes == expected_reason_codes
    return {
        "scenario_id": scenario["scenario_id"],
        "market_id": candidate.get("market_id") or str(scenario["market"].get("id", "unknown")),
        "candidate_title": candidate.get("title") or str(scenario["market"].get("title") or scenario["market"].get("question") or ""),
        "candidate_question": candidate.get("question") or str(scenario["market"].get("question") or scenario["market"].get("title") or ""),
        "triage_status": candidate.get("triage_status", "not_candidate"),
        "expected_decision": scenario["expected_decision"],
        "actual_decision": actual_decision,
        "passed_policy_checks": [],
        "failed_policy_checks": [],
        "expected_reason_codes": expected_reason_codes,
        "reason_codes": reason_codes,
        "decision_matches": decision_matches,
        "reason_codes_match": reason_codes_match,
        "result": "pass" if decision_matches and reason_codes_match else "fail",
    }


def _reviewed_result(scenario, row):
    expected_reason_codes = _expected_reason_codes(scenario)
    reason_codes = list(row["reason_codes"])
    decision_matches = row["review_decision"] == scenario["expected_decision"]
    reason_codes_match = reason_codes == expected_reason_codes
    return {
        "scenario_id": scenario["scenario_id"],
        "market_id": row["market_id"],
        "candidate_title": row["title"],
        "candidate_question": row["question"],
        "triage_status": "supported",
        "expected_decision": scenario["expected_decision"],
        "actual_decision": row["review_decision"],
        "passed_policy_checks": row["passed_policy_checks"],
        "failed_policy_checks": row["failed_policy_checks"],
        "expected_reason_codes": expected_reason_codes,
        "reason_codes": reason_codes,
        "decision_matches": decision_matches,
        "reason_codes_match": reason_codes_match,
        "result": "pass" if decision_matches and reason_codes_match else "fail",
    }


def _run_scenario(scenario, reference_context, decision_policy):
    review = _load_review_module()
    triage = _load_triage_module()
    source = _scenario_source(scenario["scenario_id"])
    payload = [scenario["market"]]
    scenario_context = _scenario_reference_context(reference_context, scenario)
    triage_report = triage.build_crypto_threshold_hit_triage_report(ROOT, source, payload)
    review_report = review.build_crypto_threshold_hit_review_table(
        ROOT,
        source,
        payload,
        reference_context=scenario_context,
        decision_policy=decision_policy,
    )
    if review_report["rows"]:
        result = _reviewed_result(scenario, review_report["rows"][0])
    else:
        result = _unsupported_result(scenario, triage_report)
    result["reference_assets_available"] = _assets_with_reference_price(scenario_context)
    return result


def build_crypto_threshold_hit_policy_scenarios(scenarios_path):
    scenarios_path = _resolve_path(scenarios_path)
    suite = _load_scenario_suite(scenarios_path)
    reference_context_path = _resolve_path(suite.get("reference_context_path", DEFAULT_REFERENCE_CONTEXT))
    decision_policy_path = _resolve_path(suite.get("decision_policy_path", DEFAULT_DECISION_POLICY))
    review = _load_review_module()
    reference_context = review._load_reference_context(reference_context_path)
    decision_policy = review._load_decision_policy(decision_policy_path)
    results = [_run_scenario(scenario, reference_context, decision_policy) for scenario in suite["scenarios"]]
    reviewed = [row for row in results if row["triage_status"] == "supported"]
    decision_counts = _decision_counts(reviewed)
    summary = {
        "scenario_count": len(results),
        "reviewed_candidates": len(reviewed),
        "no_action_count": decision_counts["no_action"],
        "watchlist_count": decision_counts["watchlist"],
        "policy_blocked_count": decision_counts["policy_blocked"],
        "paper_candidate_count": decision_counts["paper_candidate"],
        "paper_orders_created": 0,
        "policy_reason_counts": _reason_counts(reviewed),
        "all_expected_decisions_passed": all(row["decision_matches"] for row in results),
        "all_expected_results_passed": all(row["result"] == "pass" for row in results),
        "safety_flags": SAFETY_FLAGS,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "deterministic": True,
        "as_of_date": review.AS_OF_DATE,
        "scenario_fixture_path": str(scenarios_path.relative_to(ROOT)) if scenarios_path.is_relative_to(ROOT) else str(scenarios_path),
        "reference_context_path": str(reference_context_path.relative_to(ROOT)) if reference_context_path.is_relative_to(ROOT) else str(reference_context_path),
        "decision_policy_path": str(decision_policy_path.relative_to(ROOT)) if decision_policy_path.is_relative_to(ROOT) else str(decision_policy_path),
        "decision_policy_version": decision_policy["decision_policy_version"],
        "scenario_suite_id": suite["scenario_suite_id"],
        "summary": summary,
        "scenarios": results,
        "safety_flags": SAFETY_FLAGS,
        "limitations": [
            "Reads deterministic local JSON fixtures only; no live fetcher, network, external API, credentials, wallet access, orders, or trading are included.",
            "Scenarios call the existing threshold-hit triage, review, reference-context, and decision-policy logic.",
            "No paper orders, runtime wiring, dispatcher changes, prompt automation, or workspace state writes are included.",
        ],
    }


def _md(value):
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(report):
    summary = report["summary"]
    lines = [
        "# Crypto Threshold-Hit Policy Scenarios",
        "",
        f"- Scenario fixture: {report['scenario_fixture_path']}",
        f"- Reference context: {report['reference_context_path']}",
        f"- Decision policy: {report['decision_policy_path']}",
        f"- Decision policy version: {report['decision_policy_version']}",
        f"- As of date: {report['as_of_date']}",
        f"- Scenario count: {summary['scenario_count']}",
        f"- Reviewed candidates: {summary['reviewed_candidates']}",
        f"- No action: {summary['no_action_count']}",
        f"- Watchlist: {summary['watchlist_count']}",
        f"- Policy blocked: {summary['policy_blocked_count']}",
        f"- Paper candidates: {summary['paper_candidate_count']}",
        f"- Paper orders created: {summary['paper_orders_created']}",
        f"- Policy reason counts: {json.dumps(summary['policy_reason_counts'], sort_keys=True)}",
        f"- All expected decisions passed: {str(summary['all_expected_decisions_passed']).lower()}",
        f"- All expected results passed: {str(summary['all_expected_results_passed']).lower()}",
        "",
        "## Scenarios",
        "",
        "| scenario_id | question | expected | actual | passed_policy_checks | failed_policy_checks | reason_codes | result |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["scenarios"]:
        lines.append(
            f"| {_md(row['scenario_id'])} | {_md(row['candidate_question'])} | {_md(row['expected_decision'])} | "
            f"{_md(row['actual_decision'])} | {_md(json.dumps(row['passed_policy_checks']))} | "
            f"{_md(json.dumps(row['failed_policy_checks']))} | {_md(json.dumps(row['reason_codes']))} | {_md(row['result'])} |"
        )
    lines.extend(["", "## Safety Flags", ""])
    lines.append(
        "- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; dispatcher_touched=false; prompt_automation_added=false"
    )
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    report = build_crypto_threshold_hit_policy_scenarios(args.scenarios)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
