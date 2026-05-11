from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, write_json, write_text

OPERATOR_WORKFLOW_CONFIG_CONTRACT = "pmbot_operator_workflow_config.v1"
OPERATOR_ARTIFACT_DIR = Path("pm_bot/operator_runner/artifacts/night_020_021")


def default_operator_workflow_config(
    *,
    run_id: str = "operator-workflow-night-020-021-run-001",
    artifact_root: str | Path = OPERATOR_ARTIFACT_DIR / "run_001",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    return {
        "contract_version": OPERATOR_WORKFLOW_CONFIG_CONTRACT,
        "run_id": run_id,
        "generated_at": generated_at,
        "artifact_root": str(artifact_root).replace("\\", "/"),
        "include_daily_summary": True,
        "include_practical_dashboard": True,
        "include_trading_core": True,
        "include_safety_scan": True,
        "allow_live_fetch": False,
        "allow_openrouter": False,
        "allow_polymarket_api": False,
        "allow_wallet": False,
        "allow_orders": False,
        "allow_real_trading": False,
        "max_runtime_mode": "one_shot",
        "background_mode_allowed": False,
    }


def validate_operator_workflow_config(config: Mapping[str, Any]) -> tuple[bool, list[str]]:
    errors = []
    if config.get("contract_version") != OPERATOR_WORKFLOW_CONFIG_CONTRACT:
        errors.append("contract_version mismatch")
    for field in ("run_id", "artifact_root"):
        if not isinstance(config.get(field), str) or not config.get(field):
            errors.append(f"{field} must be a non-empty string")
    for field in (
        "include_daily_summary",
        "include_practical_dashboard",
        "include_trading_core",
        "include_safety_scan",
    ):
        if config.get(field) is not True:
            errors.append(f"{field} must be true")
    for field in (
        "allow_live_fetch",
        "allow_openrouter",
        "allow_polymarket_api",
        "allow_wallet",
        "allow_orders",
        "allow_real_trading",
        "background_mode_allowed",
    ):
        if config.get(field) is not False:
            errors.append(f"{field} must be false")
    if config.get("max_runtime_mode") != "one_shot":
        errors.append("max_runtime_mode must be one_shot")
    return not errors, errors


def write_operator_workflow_config(
    *,
    config: Mapping[str, Any] | None = None,
    out_json_path: str | Path = OPERATOR_ARTIFACT_DIR / "operator_workflow_config.json",
    out_md_path: str | Path = OPERATOR_ARTIFACT_DIR / "operator_workflow_config.md",
) -> dict[str, Any]:
    active_config = dict(config or default_operator_workflow_config())
    valid, errors = validate_operator_workflow_config(active_config)
    if not valid:
        raise ValueError(f"unsafe operator workflow config: {'; '.join(errors)}")
    write_json(out_json_path, active_config)
    write_text(out_md_path, render_operator_workflow_config_markdown(active_config))
    return active_config


def render_operator_workflow_config_markdown(config: Mapping[str, Any]) -> str:
    rows = [
        f"run_id: `{config.get('run_id')}`",
        f"artifact_root: `{config.get('artifact_root')}`",
        f"include_daily_summary: `{str(config.get('include_daily_summary')).lower()}`",
        f"include_practical_dashboard: `{str(config.get('include_practical_dashboard')).lower()}`",
        f"include_trading_core: `{str(config.get('include_trading_core')).lower()}`",
        f"include_safety_scan: `{str(config.get('include_safety_scan')).lower()}`",
        f"allow_live_fetch: `{str(config.get('allow_live_fetch')).lower()}`",
        f"allow_openrouter: `{str(config.get('allow_openrouter')).lower()}`",
        f"allow_polymarket_api: `{str(config.get('allow_polymarket_api')).lower()}`",
        f"allow_wallet: `{str(config.get('allow_wallet')).lower()}`",
        f"allow_orders: `{str(config.get('allow_orders')).lower()}`",
        f"allow_real_trading: `{str(config.get('allow_real_trading')).lower()}`",
        f"max_runtime_mode: `{config.get('max_runtime_mode')}`",
        f"background_mode_allowed: `{str(config.get('background_mode_allowed')).lower()}`",
    ]
    return "\n".join(
        [
            "# PMBOT Operator Workflow Config",
            "",
            "This config is for one explicit local run.",
            "",
            "## Fields",
            "",
            *bullet_lines(rows),
        ]
    ) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the PMBOT one-shot operator workflow config.")
    parser.add_argument("--out-json", default=str(OPERATOR_ARTIFACT_DIR / "operator_workflow_config.json"))
    parser.add_argument("--out-md", default=str(OPERATOR_ARTIFACT_DIR / "operator_workflow_config.md"))
    parser.add_argument("--artifact-root", default=str(OPERATOR_ARTIFACT_DIR / "run_001"))
    args = parser.parse_args(argv)
    config = default_operator_workflow_config(artifact_root=args.artifact_root)
    write_operator_workflow_config(config=config, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
