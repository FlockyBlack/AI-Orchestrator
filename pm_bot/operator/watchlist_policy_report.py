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


def _load_support(root: Path):
    return _load_module(root / "pm_bot" / "operator" / "operator_support.py", "pmbot_operator_support_watchlist")


def _parse_args():
    parser = argparse.ArgumentParser(description="Build the PMBOT watchlist no-action policy report.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_watchlist_policy_report(root: Path):
    support = _load_module(
        root / "pm_bot" / "validation" / "adversarial_support.py",
        "pmbot_adversarial_support_watchlist",
    )
    operator_support = _load_support(root)
    replay_cases = [support.evaluate_replay_case(case) for case in support.load_replay_cases(root)]
    scenarios = [support.evaluate_market_shock_scenario(item) for item in support.load_market_shock_scenarios(root)]
    covered = []
    for reason in ("duplicate_snapshot", "outlier_price_move", "correlation_conflict"):
        replay_hits = sorted(item["case_id"] for item in replay_cases if reason in item["warning_reasons"])
        scenario_hits = sorted(item["scenario_id"] for item in scenarios if reason in item["warning_reasons"])
        covered.append(
            {
                "reason": reason,
                "replay_cases": replay_hits,
                "shock_scenarios": scenario_hits,
                "allowed_decisions": ["watchlist_no_action", "reject_no_action"],
            }
        )
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BATCH-006-WATCHLIST-POLICY",
        "watchlist_policy_version": "PMBOT-BATCH-005-warning-policy",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "operator_review_only": True,
        "cases_covered": covered,
        "watchlist_is_no_action": True,
        "watchlist_requires_human_review": True,
        "watchlist_can_execute": False,
        "future_live_mode_requires_separate_approval": True,
        "critical_rule": operator_support.watchlist_policy_statement(),
    }


def render_markdown(report):
    lines = [
        "# PMBOT Watchlist Policy Report",
        "",
        "Deterministic encoding of the PMBOT-BATCH-005 warning policy.",
        "",
        f"- Watchlist is no-action: {str(report['watchlist_is_no_action']).lower()}",
        f"- Watchlist requires human review: {str(report['watchlist_requires_human_review']).lower()}",
        f"- Watchlist can execute: {str(report['watchlist_can_execute']).lower()}",
        f"- Future live mode requires separate approval: {str(report['future_live_mode_requires_separate_approval']).lower()}",
        "",
        "## Covered Cases",
    ]
    for item in report["cases_covered"]:
        lines.append(
            f"- {item['reason']}: replay={', '.join(item['replay_cases']) or 'none'} | "
            f"shock={', '.join(item['shock_scenarios']) or 'none'} | decisions={', '.join(item['allowed_decisions'])}"
        )
    lines.extend(["", f"- Critical rule: {report['critical_rule']}", ""])
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_watchlist_policy_report(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
