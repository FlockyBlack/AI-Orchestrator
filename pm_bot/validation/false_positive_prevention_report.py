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
    parser = argparse.ArgumentParser(description="Build the PMBOT false-positive prevention report.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_false_positive_prevention_report(root: Path):
    replay = _load_module(root / "pm_bot" / "replay" / "run_adversarial_replay.py", "pmbot_adversarial_replay")
    report = replay.build_adversarial_replay_report(root)
    cases = report["cases"]
    strongest_reasons = {}
    for item in cases:
        for reason in item["reject_reasons"]:
            strongest_reasons[reason] = strongest_reasons.get(reason, 0) + 1
    weak_areas = []
    if any("duplicate_snapshot" in item["warning_reasons"] for item in cases):
        weak_areas.append("Duplicate snapshots are downgraded to watchlist rather than hard rejected.")
    if any("outlier_price_move" in item["warning_reasons"] for item in cases):
        weak_areas.append("Outlier price moves still rely on watchlist downgrades instead of exclusion.")
    if any("correlation_conflict" in item["warning_reasons"] for item in cases):
        weak_areas.append("Correlation contradictions are contained but not treated as universal hard rejects.")
    recommendations = [
        "Add multi-step replay cases where shocks arrive in different orders.",
        "Add synthetic cases with repeated stale-to-fresh oscillations.",
        "Add fixture sets for category exposure interactions across several watchlist markets.",
    ]
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BATCH-005-FALSE-POSITIVE-PREVENTION",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "total_adversarial_cases": report["total_cases"],
        "cases_correctly_rejected": sum(1 for item in cases if item["actual_decision"] in {"reject", "exclude"}),
        "false_positives_count": report["false_positive_count"],
        "high_risk_false_positives_count": sum(1 for item in cases if item["high_risk_false_positive"]),
        "missed_warning_count": sum(len(item["missing_expected_reasons"]) for item in cases),
        "strongest_rejection_reasons": [
            reason for reason, _ in sorted(strongest_reasons.items(), key=lambda entry: (-entry[1], entry[0]))[:5]
        ],
        "weakest_current_detection_areas": weak_areas,
        "recommended_future_fixture_additions": recommendations,
        "paper_only_no_real_order_statement": "False-positive prevention remains a local paper-only validation layer. No real order path exists.",
    }


def render_markdown(report):
    lines = [
        "# PMBOT False-Positive Prevention Report",
        "",
        "Deterministic assessment of whether hostile replay cases are contained before any future live-data work.",
        "",
        f"- Total adversarial cases: {report['total_adversarial_cases']}",
        f"- Cases correctly rejected: {report['cases_correctly_rejected']}",
        f"- False positives: {report['false_positives_count']}",
        f"- High-risk false positives: {report['high_risk_false_positives_count']}",
        f"- Missed warnings: {report['missed_warning_count']}",
        f"- Strongest rejection reasons: {', '.join(report['strongest_rejection_reasons'])}",
        f"- Statement: {report['paper_only_no_real_order_statement']}",
        "",
        "## Weakest Current Detection Areas",
    ]
    lines.extend(f"- {item}" for item in report["weakest_current_detection_areas"])
    lines.extend(["", "## Recommended Future Fixture Additions"])
    lines.extend(f"- {item}" for item in report["recommended_future_fixture_additions"])
    lines.append("")
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_false_positive_prevention_report(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
