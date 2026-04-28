import argparse
import json
import sys
from pathlib import Path


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_args():
    parser = argparse.ArgumentParser(description="Run deterministic PMBOT demo scenarios.")
    parser.add_argument("--output")
    return parser.parse_args()


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


def build_scenario_report(suite, root: Path):
    scenario_results = []
    for scenario in suite["scenarios"]:
        refs = list(scenario.get("market_refs", []))
        present = []
        for ref in refs:
            resolved = (root / ref).resolve()
            present.append(resolved.exists())
        scenario_results.append(
            {
                "scenario_id": scenario["scenario_id"],
                "source_type": scenario["source_type"],
                "expected_modules": list(scenario["expected_modules"]),
                "market_ref_count": len(refs),
                "all_market_refs_present": all(present),
                "expected_safety_flags": dict(scenario["expected_safety_flags"]),
                "research_only": True,
                "execution_allowed": False,
                "trading_allowed": False,
                "live_data_allowed": False,
                "wallet_required": False,
                "credential_material_required": False,
                "status": "ready" if all(present) else "missing_refs",
            }
        )

    overall_status = "ready" if all(item["status"] == "ready" for item in scenario_results) else "missing_refs"
    return {
        "schema_version": "v2",
        "scenario_suite_id": suite["scenario_suite_id"],
        "source_type": suite["source_type"],
        "research_only": True,
        "execution_allowed": False,
        "trading_allowed": False,
        "live_data_allowed": False,
        "wallet_required": False,
        "credential_material_required": False,
        "scenario_count": len(scenario_results),
        "overall_status": overall_status,
        "scenario_results": scenario_results,
    }


def main(argv=None):
    args = _parse_args() if argv is None else _parse_args()
    root = Path(__file__).resolve().parents[2]
    suite = _load_json(root / "pm_bot" / "scenarios" / "scenario_suite.v2.json")
    report = build_scenario_report(suite, root)
    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output_path = _resolve_output(root, args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
