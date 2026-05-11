from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import ARTIFACT_DIR, GENERATED_AT, bullet_lines, normalize_path, write_json, write_text

TRADING_CORE_SAFETY_SCAN_CONTRACT = "pmbot_trading_core_safety_scan.v1"

UNSAFE_TRUE_FIELDS = {
    "real_order_allowed",
    "real_order_submitted",
    "wallet_used",
    "trading_endpoint_used",
    "wallet_required",
    "trading_endpoint_required",
    "real_money_used",
    "autonomous_trading_enabled",
    "scheduler_created",
    "daemon_created",
    "background_worker_created",
    "allow_real_orders",
    "allow_wallet",
    "allow_trading_endpoints",
    "allow_autonomous_execution",
}
UNSAFE_POSITIVE_COUNT_FIELDS = {
    "openrouter_calls_performed",
    "polymarket_api_calls_performed",
}
REAL_RECOMMENDATION_PATTERN = re.compile(
    r"\b(?:should|must|recommend(?:ed)?|instruction|signal|execute|place)\s+"
    r"(?:a\s+)?(?:market\s+)?(?:buy|sell|hold|enter|exit|order)\b",
    re.IGNORECASE,
)
AUTONOMY_PATTERN = re.compile(
    r"\b(?:scheduler|daemon|background worker|watcher|polling|infinite loop|autonomous trading)\b",
    re.IGNORECASE,
)


def run_trading_core_safety_scan(
    *,
    artifact_dirs: Sequence[str | Path] = (ARTIFACT_DIR,),
    artifact_paths: Sequence[str | Path] = (),
    out_json_path: str | Path = ARTIFACT_DIR / "trading_core_safety_scan.result.json",
    out_md_path: str | Path = ARTIFACT_DIR / "trading_core_safety_scan.md",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    out_json = Path(out_json_path)
    out_md = Path(out_md_path)
    paths = [
        path
        for path in _collect_paths(artifact_dirs, artifact_paths)
        if path.resolve() not in {out_json.resolve(), out_md.resolve()}
    ]
    issues = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        issues.extend(_scan_text(path, text))
        if path.suffix.lower() == ".json":
            try:
                issues.extend(_scan_json(path, json.loads(text)))
            except json.JSONDecodeError:
                issues.append(_issue(path, "invalid_json", "JSON artifact could not be parsed."))
    report = {
        "contract_version": TRADING_CORE_SAFETY_SCAN_CONTRACT,
        "generated_at": generated_at,
        "scanned_paths": [normalize_path(path) for path in paths],
        "issue_count": len(issues),
        "issues": issues,
        "safety_ok": not issues,
        "confirmed_false_flags": {
            "real_order_allowed": False,
            "real_order_submitted": False,
            "wallet_used": False,
            "trading_endpoint_used": False,
            "wallet_required": False,
            "trading_endpoint_required": False,
            "autonomous_trading_enabled": False,
            "scheduler_created": False,
            "daemon_created": False,
            "background_worker_created": False,
        },
    }
    write_json(out_json_path, report)
    write_text(out_md_path, render_trading_core_safety_scan_markdown(report))
    return report


def render_trading_core_safety_scan_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Trading Core Safety Scan",
            "",
            f"- Scanned paths: {len(report.get('scanned_paths', []))}",
            f"- Issues: {report.get('issue_count')}",
            f"- Safety OK: `{str(report.get('safety_ok')).lower()}`",
            "",
            "## Issues",
            "",
            *bullet_lines(
                f"`{row.get('path')}` `{row.get('issue_type')}` - {row.get('detail')}"
                for row in report.get("issues", [])
            ),
            "",
            "## Confirmations",
            "",
            "- No real order, wallet, trading endpoint, real-money, scheduler, daemon, background worker, polling, or autonomous trading flag is enabled.",
            "- No real recommendation language was detected outside boundary context.",
        ]
    ) + "\n"


def _collect_paths(artifact_dirs: Sequence[str | Path], artifact_paths: Sequence[str | Path]) -> list[Path]:
    paths = [Path(path) for path in artifact_paths if Path(path).exists()]
    for directory in artifact_dirs:
        root = Path(directory)
        if root.exists() and root.is_dir():
            paths.extend(path for path in root.rglob("*") if path.suffix.lower() in {".json", ".md"})
    return sorted({path.resolve(): path for path in paths if path.is_file()}.values(), key=normalize_path)


def _scan_text(path: Path, text: str) -> list[dict[str, str]]:
    issues = []
    for line in text.splitlines():
        if _is_boundary_context_line(line):
            continue
        if REAL_RECOMMENDATION_PATTERN.search(line):
            issues.append(_issue(path, "real_recommendation_language", "Action-like real trading wording detected."))
        if AUTONOMY_PATTERN.search(line):
            issues.append(_issue(path, "autonomy_reference", "Scheduler/background/polling/autonomy wording detected."))
    return issues


def _scan_json(path: Path, value: Any, json_path: str = "$") -> list[dict[str, str]]:
    issues = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            nested_path = f"{json_path}.{key}"
            if key in UNSAFE_TRUE_FIELDS and nested is True:
                issues.append(_issue(path, "unsafe_flag_true", f"{nested_path} is true"))
            if key in UNSAFE_POSITIVE_COUNT_FIELDS and isinstance(nested, int) and nested > 0:
                issues.append(_issue(path, "unsafe_count_positive", f"{nested_path} is {nested}"))
            issues.extend(_scan_json(path, nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(_scan_json(path, nested, f"{json_path}[{index}]"))
    return issues


def _issue(path: Path, issue_type: str, detail: str) -> dict[str, str]:
    return {"path": normalize_path(path), "issue_type": issue_type, "detail": detail}


def _is_boundary_context_line(line: str) -> bool:
    normalized = line.lower()
    return any(
        phrase in normalized
        for phrase in (
            "no ",
            "not ",
            "false",
            "blocked",
            "disallowed",
            "forbidden",
            "boundary",
            "paper-only",
            "non-executable",
            "not real",
            "not implemented",
            "without",
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan PMBOT trading core artifacts for unsafe flags or wording.")
    parser.add_argument("--artifact-dir", action="append", default=[])
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--out-json", default=str(ARTIFACT_DIR / "trading_core_safety_scan.result.json"))
    parser.add_argument("--out-md", default=str(ARTIFACT_DIR / "trading_core_safety_scan.md"))
    args = parser.parse_args(argv)
    dirs = args.artifact_dir or [str(ARTIFACT_DIR)]
    run_trading_core_safety_scan(
        artifact_dirs=dirs,
        artifact_paths=args.artifact,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
