import argparse
import importlib.util
import json
from pathlib import Path


def _load_support(root: Path):
    path = root / "pm_bot" / "quality" / "research_quality_support.py"
    spec = importlib.util.spec_from_file_location("pmbot_research_quality_support", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _parse_args():
    parser = argparse.ArgumentParser(description="Build a deterministic PMBOT reasoning trace artifact.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_reasoning_trace_report(root: Path):
    support = _load_support(root)
    cases = support.load_cases(root)["cases"]
    traces = [support.build_reasoning_trace(case) for case in cases]
    return {
        "schema_version": "v1",
        "artifact_id": "PMBOT-BATCH-004-REASONING-TRACE",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "traces": traces,
    }


def render_markdown(report):
    lines = [
        "# PMBOT Reasoning Trace",
        "",
        "Deterministic reasoning traces for fixture-only PMBOT research cases. No network, no wallet, no orders, and no runtime wiring.",
        "",
    ]
    for trace in report["traces"]:
        lines.extend(
            [
                f"## {trace['case_id']}",
                f"- Market: {trace['normalized_research_case']['market_id']}",
                f"- Decision: {trace['final_paper_only_decision']}",
                f"- Confidence: {trace['confidence_band']} ({trace['confidence_score']})",
                f"- Risk flags: {', '.join(trace['risk_flags']) or 'none'}",
                f"- Data-quality flags: {', '.join(trace['data_quality_flags']) or 'none'}",
                f"- Safety: {trace['no_action_safety_confirmation']}",
                "",
            ]
        )
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_reasoning_trace_report(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
