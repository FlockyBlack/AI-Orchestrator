from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, normalize_path, safe_summary, write_json, write_text

SAFETY_SCAN_CONTRACT_VERSION = "pmbot_practical_safety_scan.v1"
UNSAFE_FLAG_FIELDS = {
    "authenticated_endpoints_used",
    "live_network_used",
    "market_recommendation_generated",
    "orders_or_trading_actions",
    "probability_ev_edge_or_side_selection_generated",
    "runtime_or_dispatcher_changes",
    "wallet_or_private_key_access",
}
UNSAFE_COUNT_FIELDS = {
    "openrouter_calls_performed",
    "polymarket_api_calls_performed",
}
ACTION_PATTERN = re.compile(
    r"\b(?:should|must|recommend(?:ed)?|instruction|signal|execute|place)\s+"
    r"(?:a\s+)?(?:market\s+)?(?:buy|sell|hold|enter|exit|order)\b",
    re.IGNORECASE,
)
SIGNAL_PATTERN = re.compile(r"\b(?:probability|ev|edge|confidence)\b.{0,40}\b(?:signal|instruction)\b", re.IGNORECASE)


def run_practical_safety_scan(
    *,
    artifact_dirs: Sequence[str | Path] = (),
    artifact_paths: Sequence[str | Path] = (),
    out_json_path: str | Path | None = None,
    out_md_path: str | Path | None = None,
) -> dict[str, Any]:
    paths = _collect_paths(artifact_dirs, artifact_paths)
    issues = []
    scanned = []
    for path in paths:
        scanned.append(normalize_path(path))
        text = Path(path).read_text(encoding="utf-8")
        issues.extend(_scan_text(path, text))
        if Path(path).suffix.lower() == ".json":
            try:
                issues.extend(_scan_json_flags(path, json.loads(text)))
            except json.JSONDecodeError:
                issues.append(_issue(path, "invalid_json", "JSON artifact could not be parsed."))
    report = {
        "contract_version": SAFETY_SCAN_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "scanned_paths": scanned,
        "issue_count": len(issues),
        "issues": issues,
        "safety_ok": not issues,
        "safety_summary": safe_summary(),
    }
    if out_json_path is not None:
        write_json(out_json_path, report)
    if out_md_path is not None:
        write_text(out_md_path, render_practical_safety_scan_markdown(report))
    return report


def render_practical_safety_scan_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Practical Safety Scan",
            "",
            f"- Scanned paths: {len(report['scanned_paths'])}",
            f"- Issues: {report['issue_count']}",
            f"- Safety OK: `{str(report['safety_ok']).lower()}`",
            "",
            "## Issues",
            "",
            *bullet_lines(f"`{row['path']}` `{row['issue_type']}` - {row['detail']}" for row in report["issues"]),
            "",
            "## Safety boundary",
            "",
            "- Detects actionable trading wording and unsafe artifact flags.",
            "- The scanner itself reads local artifact files only.",
        ]
    ) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan PMBOT practical artifacts for unsafe trading-action output.")
    parser.add_argument("--artifact-dir", action="append", default=[], help="Artifact directory to scan; repeatable.")
    parser.add_argument("--artifact", action="append", default=[], help="Specific artifact path to scan; repeatable.")
    parser.add_argument("--out-json", required=True, help="Output safety scan JSON.")
    parser.add_argument("--out-md", required=True, help="Output safety scan Markdown.")
    args = parser.parse_args(argv)
    if not args.artifact_dir and not args.artifact:
        parser.error("--artifact-dir or --artifact is required")
    run_practical_safety_scan(
        artifact_dirs=args.artifact_dir,
        artifact_paths=args.artifact,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


def _collect_paths(artifact_dirs: Sequence[str | Path], artifact_paths: Sequence[str | Path]) -> list[Path]:
    paths = [Path(path) for path in artifact_paths]
    for directory in artifact_dirs:
        root = Path(directory)
        if root.exists() and root.is_dir():
            paths.extend(path for path in root.rglob("*") if path.suffix.lower() in {".json", ".md"})
    return sorted({path.resolve(): path for path in paths if path.exists() and path.is_file()}.values(), key=normalize_path)


def _scan_text(path: str | Path, text: str) -> list[dict[str, str]]:
    issues = []
    if ACTION_PATTERN.search(text):
        issues.append(_issue(path, "actionable_trading_wording", "Action-like trading wording was detected."))
    if SIGNAL_PATTERN.search(text):
        issues.append(_issue(path, "trading_signal_wording", "Quantitative signal wording was detected."))
    return issues


def _scan_json_flags(path: str | Path, value: Any, json_path: str = "$") -> list[dict[str, str]]:
    issues = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            nested_path = f"{json_path}.{key}"
            if key in UNSAFE_FLAG_FIELDS and nested is True:
                issues.append(_issue(path, "unsafe_flag_true", f"{nested_path} is true"))
            if key in UNSAFE_COUNT_FIELDS and isinstance(nested, int) and nested > 0:
                issues.append(_issue(path, "unsafe_count_positive", f"{nested_path} is {nested}"))
            issues.extend(_scan_json_flags(path, nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(_scan_json_flags(path, nested, f"{json_path}[{index}]"))
    return issues


def _issue(path: str | Path, issue_type: str, detail: str) -> dict[str, str]:
    return {"path": normalize_path(path), "issue_type": issue_type, "detail": detail}


if __name__ == "__main__":
    raise SystemExit(main())
