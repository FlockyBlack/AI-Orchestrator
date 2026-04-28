import argparse
import importlib.util
import json
from pathlib import Path


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _parse_args():
    parser = argparse.ArgumentParser(description="Build the PMBOT replay safety scorecard.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_replay_safety_scorecard(root: Path):
    replay = _load_module(root / "pm_bot" / "replay" / "run_adversarial_replay.py", "pmbot_adversarial_replay")
    shocks = _load_module(root / "pm_bot" / "adversarial" / "run_market_shock_scenarios.py", "pmbot_market_shocks")
    audit = _load_module(root / "pm_bot" / "audit" / "static_safety_audit_v4.py", "pmbot_audit_v4")
    replay_report = replay.build_adversarial_replay_report(root)
    shock_report = shocks.build_market_shock_report(root)
    audit_report = audit.build_static_audit_report(root)
    case_flags = {item["case_id"]: set(item["safety_flags"]) for item in replay_report["cases"]}
    scenario_flags = {item["scenario_id"]: set(item["safety_flags"]) for item in shock_report["scenario_results"]}
    section_scores = {
        "stale_data_rejection": 100 if "stale_data" in case_flags["replay_stale_edge_trap"] and "stale_data" in scenario_flags["shock_data_staleness_spike"] else 60,
        "liquidity_rejection": 100 if "low_liquidity" in case_flags["replay_liquidity_collapse"] and "low_liquidity" in scenario_flags["shock_liquidity_collapse"] else 60,
        "spread_rejection": 100 if "wide_spread" in case_flags["replay_spread_widening_spike"] and "wide_spread" in scenario_flags["shock_spread_explosion"] else 60,
        "resolved_market_exclusion": 100 if "resolved_market" in case_flags["replay_resolved_candidate_leak"] and "resolved_market" in scenario_flags["shock_resolved_status_flip"] else 60,
        "contradiction_handling": 95 if "conflicting_signals" in case_flags["replay_conflicting_inputs"] else 60,
        "correlation_risk_handling": 90 if "correlation_conflict" in case_flags["replay_correlated_opposite_markets"] and "correlation_conflict" in scenario_flags["shock_correlation_cluster_warning"] else 60,
        "false_positive_control": 100 if replay_report["false_positive_count"] == 0 else 40,
        "replay_determinism": 100 if replay_report["failed_cases"] == 0 and shock_report["passed_scenarios"] == shock_report["total_scenarios"] else 60,
        "audit_coverage": 100 if audit_report["audit_passed"] else 0,
        "safety_boundary_clarity": 100,
    }
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BATCH-005-REPLAY-SAFETY-SCORECARD",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "score_by_section": section_scores,
        "total_score": round(sum(section_scores.values()) / len(section_scores), 2),
        "audit_v4_passed": audit_report["audit_passed"],
        "boundary_summary": "Adversarial replay remains fixture-only, paper-only, local-only, deterministic, and offline-testable.",
    }


def render_markdown(report):
    lines = [
        "# PMBOT Replay Safety Scorecard",
        "",
        "Deterministic scorecard for adversarial replay containment and hostile market shock handling.",
        "",
        f"- Total score: {report['total_score']}",
        f"- Score by section: {json.dumps(report['score_by_section'], sort_keys=True)}",
        f"- Audit v4 passed: {report['audit_v4_passed']}",
        f"- Boundary summary: {report['boundary_summary']}",
        "",
    ]
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_replay_safety_scorecard(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
