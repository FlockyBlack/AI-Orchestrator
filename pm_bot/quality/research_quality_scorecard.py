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
    parser = argparse.ArgumentParser(description="Build the PMBOT research quality scorecard.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args()


def build_research_quality_scorecard(root: Path):
    support = _load_support(root)
    sections = support.scorecard_sections(root)
    strengths = [
        "Broad deterministic fixture coverage across accept, watchlist, reject, exclude, and no-action outcomes.",
        "Explainability and confidence scoring are generated from one local rule set.",
        "Safety boundaries remain explicit and runtime wiring remains blocked.",
    ]
    gaps = [
        "All cases remain synthetic and do not validate against live market behavior.",
        "Export targets are limited to local JSON and Markdown artifacts.",
    ]
    blocked = [
        "Live fetcher implementation",
        "Live Polymarket API",
        "Wallet/private key handling",
        "Real order execution",
        "Autonomous trading",
        "Runtime wiring",
        "Dispatcher/run_codex integration",
    ]
    recommended = [
        "Add more synthetic edge cases.",
        "Expand local explainability templates.",
        "Add local report export variants.",
        "Review a read-only fetcher design without implementation.",
        "Harden fixture replay workflows.",
        "Add adversarial safety fixtures.",
    ]
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BATCH-004-RESEARCH-QUALITY-SCORECARD",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "score_by_section": sections,
        "total_score": round(sum(sections.values()) / len(sections), 2),
        "strengths": strengths,
        "gaps": gaps,
        "blocked_future_work": blocked,
        "recommended_next_safe_tasks": recommended,
    }


def render_markdown(report):
    lines = [
        "# PMBOT Research Quality Scorecard",
        "",
        "Deterministic local scorecard for the PMBOT research quality layer.",
        "",
        f"- Total score: {report['total_score']}",
        f"- Score by section: {json.dumps(report['score_by_section'], sort_keys=True)}",
        "",
        "## Strengths",
    ]
    lines.extend(f"- {item}" for item in report["strengths"])
    lines.extend(["", "## Gaps"])
    lines.extend(f"- {item}" for item in report["gaps"])
    lines.extend(["", "## Blocked Future Work"])
    lines.extend(f"- {item}" for item in report["blocked_future_work"])
    lines.extend(["", "## Recommended Next Safe Tasks"])
    lines.extend(f"- {item}" for item in report["recommended_next_safe_tasks"])
    lines.append("")
    return "\n".join(lines)


def main():
    args = _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_research_quality_scorecard(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
