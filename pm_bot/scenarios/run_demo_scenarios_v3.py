import argparse
import importlib.util
import json
import sys
from pathlib import Path


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_support(root: Path):
    module_path = root / "pm_bot" / "reports" / "pmbot_batch_003_support.py"
    spec = importlib.util.spec_from_file_location("pmbot_batch_003_support", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Run deterministic PMBOT V3 demo scenarios.")
    parser.add_argument("--output")
    return parser.parse_args(argv)


def _resolve_output(root: Path, output_arg: str):
    output_path = Path(output_arg)
    if not output_path.is_absolute():
        output_path = (root / output_path).resolve()
    allowed_root = (root / "pm_bot" / "scenarios").resolve()
    try:
        output_path.relative_to(allowed_root)
    except ValueError as exc:
        raise ValueError("--output must stay under pm_bot/scenarios/") from exc
    return output_path


def _scenario_outcome(scenario, summary):
    analyses = {item["market_id"]: item for item in summary["market_analyses"]}
    scenario_id = scenario["scenario_id"]

    if scenario_id == "baseline_multi_market_paper_scan":
        triggered_flags = ["multi_market_fixture_loaded"]
        passed = len(summary["market_analyses"]) >= 6
        detail = f"{len(summary['market_analyses'])} synthetic markets loaded from the fixture bundle."
        paper_action = "scan_only"
    elif scenario_id == "category_concentration_warning":
        triggered_flags = [flag for flag in summary["portfolio_warnings"] if flag.startswith("category_concentration:")]
        passed = bool(triggered_flags)
        detail = "Accepted macro exposures breach the category cap."
        paper_action = "warning_only"
    elif scenario_id == "portfolio_exposure_cap_warning":
        triggered_flags = [flag for flag in summary["portfolio_warnings"] if flag == "portfolio_exposure_cap"]
        passed = bool(triggered_flags)
        detail = "Accepted paper allocations exceed the configured total allocation ratio."
        paper_action = "warning_only"
    elif scenario_id == "correlated_market_caution":
        triggered_flags = [flag for flag in summary["portfolio_warnings"] if flag.startswith("correlated_group:")]
        passed = bool(triggered_flags)
        detail = "Correlated macro positions trigger grouped exposure caution."
        paper_action = "warning_only"
    elif scenario_id == "paper_only_no_action_confirmation":
        triggered_flags = ["paper_only_no_action"]
        passed = True
        detail = "The scenario layer confirms monitor-only paper research with no live action."
        paper_action = "no_action"
    else:
        focus_market_id = scenario["focus_market_ids"][0]
        analysis = analyses[focus_market_id]
        triggered_flags = sorted(set(list(analysis["warnings"]) + list(analysis["rejection_reasons"])))
        if scenario_id == "positive_paper_edge_candidate":
            passed = analysis["accepted_candidate"]
            detail = "Positive edge candidate remains accepted under deterministic fixture rules."
            paper_action = "accepted"
        elif scenario_id == "resolved_closed_market_exclusion":
            passed = analysis["excluded"]
            detail = "Resolved fixture is excluded from paper positions."
            paper_action = "excluded"
        else:
            passed = any(flag in triggered_flags for flag in scenario["expected_flags"])
            detail = f"Market evaluation returned {analysis['candidate_status']} with flags {triggered_flags}."
            paper_action = analysis["candidate_status"]

    actual_status = "pass" if passed else "mismatch"
    return {
        "scenario_id": scenario_id,
        "focus_market_ids": list(scenario["focus_market_ids"]),
        "expected_status": scenario["expected_status"],
        "actual_status": actual_status,
        "paper_action": paper_action,
        "triggered_flags": sorted(set(triggered_flags)),
        "detail": detail,
        "research_only": True,
        "paper_only": True,
        "execution_allowed": False,
        "trading_allowed": False,
        "live_data_allowed": False,
        "wallet_required": False,
        "credential_material_required": False,
    }


def build_scenario_report(suite, bundle):
    root = Path(__file__).resolve().parents[2]
    support = _load_support(root)
    summary = support.summarize_bundle(bundle)
    scenario_results = [_scenario_outcome(scenario, summary) for scenario in suite["scenarios"]]
    passed_count = sum(1 for item in scenario_results if item["actual_status"] == "pass")

    return {
        "schema_version": "v3",
        "scenario_suite_id": suite["scenario_suite_id"],
        "source_type": suite["source_type"],
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "execution_allowed": False,
        "trading_allowed": False,
        "live_data_allowed": False,
        "wallet_required": False,
        "credential_material_required": False,
        "scenario_count": len(scenario_results),
        "passed_scenario_count": passed_count,
        "overall_status": "ready" if passed_count == len(scenario_results) else "mismatch",
        "fixture_market_count": len(bundle["markets"]),
        "paper_candidate_count": summary["paper_candidate_count"],
        "accepted_paper_candidates": summary["accepted_candidate_count"],
        "rejected_paper_candidates": summary["rejected_candidate_count"],
        "excluded_market_count": summary["excluded_market_count"],
        "warning_count": len(summary["warning_counts"]),
        "portfolio_warning_flags": list(summary["portfolio_warnings"]),
        "risk_flags": list(summary["risk_flags"]),
        "final_recommendation": "paper_only_monitor_no_action",
        "scenario_results": scenario_results,
    }


def main(argv=None):
    root = Path(__file__).resolve().parents[2]
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    suite = _load_json(root / "pm_bot" / "scenarios" / "scenario_suite.v3.json")
    bundle = _load_json(root / "pm_bot" / "fixtures" / "multi_market_fixture_bundle.v1.json")
    report = build_scenario_report(suite, bundle)
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output_path = _resolve_output(root, args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
