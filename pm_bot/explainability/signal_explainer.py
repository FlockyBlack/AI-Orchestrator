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
    parser = argparse.ArgumentParser(description="Build deterministic PMBOT signal explanations.")
    return parser.parse_args()


def build_signal_explanations(root: Path):
    support = _load_support(root)
    cases = support.load_cases(root)["cases"]
    explanations = [support.build_signal_explanation(case) for case in cases]
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BATCH-004-SIGNAL-EXPLANATIONS",
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "no_network_or_api": True,
        "explanations": explanations,
    }


def main():
    _parse_args()
    root = Path(__file__).resolve().parents[2]
    report = build_signal_explanations(root)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
