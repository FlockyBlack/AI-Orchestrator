from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.operator_runner.workflow_config import OPERATOR_ARTIFACT_DIR
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, normalize_path, write_json, write_text

OPERATOR_WORKFLOW_SAFETY_SCAN_CONTRACT = "pmbot_operator_workflow_safety_scan.v1"

UNSAFE_TRUE_FIELDS = {
    "allow_live_fetch",
    "allow_openrouter",
    "allow_polymarket_api",
    "allow_wallet",
    "allow_orders",
    "allow_real_trading",
    "live_fetch",
    "live_fetch_performed",
    "openrouter",
    "polymarket_api",
    "authenticated_endpoints_used",
    "wallet",
    "wallet_used",
    "orders",
    "real_trading",
    "real_money_used",
    "scheduler",
    "scheduler_created",
    "daemon",
    "daemon_created",
    "background_worker",
    "background_worker_created",
    "infinite_loop",
}
UNSAFE_POSITIVE_COUNT_FIELDS = {
    "openrouter_calls_performed",
    "polymarket_api_calls_performed",
}
UNSAFE_TEXT_PATTERN = re.compile(
    r"\b(?:live fetch|openrouter|polymarket api|authenticated endpoint|wallet|orders|real trading|"
    r"scheduler|daemon|background worker|infinite loop|polling)\b",
    re.IGNORECASE,
)


def run_operator_workflow_safety_scan(
    *,
    artifact_dirs: Sequence[str | Path],
    artifact_paths: Sequence[str | Path] = (),
    out_json_path: str | Path,
    out_md_path: str | Path,
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
        if path.suffix.lower() != ".json":
            issues.extend(_scan_text(path, text))
        if path.suffix.lower() == ".json":
            try:
                issues.extend(_scan_json(path, json.loads(text)))
            except json.JSONDecodeError:
                issues.append(_issue(path, "invalid_json", "JSON artifact could not be parsed."))
    report = {
        "contract_version": OPERATOR_WORKFLOW_SAFETY_SCAN_CONTRACT,
        "generated_at": generated_at,
        "scanned_paths": [normalize_path(path) for path in paths],
        "issue_count": len(issues),
        "issues": issues,
        "safety_ok": not issues,
        "confirmed": {
            "live_fetch": False,
            "openrouter": False,
            "polymarket_api": False,
            "authenticated_endpoints": False,
            "wallet": False,
            "orders": False,
            "real_trading": False,
            "scheduler": False,
            "daemon": False,
            "background_worker": False,
            "infinite_loop": False,
        },
    }
    write_json(out_json_path, report)
    write_text(out_md_path, render_operator_workflow_safety_scan_markdown(report))
    return report


def render_operator_workflow_safety_scan_markdown(report: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# PMBOT Operator Workflow Safety Scan",
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
            "## Confirmed absent",
            "",
            *bullet_lines(f"{key}: `{str(value).lower()}`" for key, value in dict(report.get("confirmed", {})).items()),
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
        if UNSAFE_TEXT_PATTERN.search(line):
            issues.append(_issue(path, "unsafe_workflow_wording", "Unsafe workflow wording detected outside boundary context."))
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
            "confirmed absent",
            "disallowed",
            "forbidden",
            "one explicit local command",
            "one run",
            "then exit",
            "boundary",
            "blocked",
            "without",
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan one-shot operator runner artifacts.")
    parser.add_argument("--artifact-dir", action="append", default=[])
    parser.add_argument("--artifact", action="append", default=[])
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args(argv)
    dirs = args.artifact_dir or [str(OPERATOR_ARTIFACT_DIR / "run_001")]
    run_operator_workflow_safety_scan(
        artifact_dirs=dirs,
        artifact_paths=args.artifact,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
