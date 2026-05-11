from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import ARTIFACT_DIR, GENERATED_AT, bullet_lines, clean_text, write_json, write_text

FUTURE_RISK_ENGINE_CONFIG_CONTRACT = "pmbot_future_risk_engine_config.v1"


class FutureRiskEngineConfigError(ValueError):
    pass


def build_default_future_risk_engine_config(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    config = {
        "contract_version": FUTURE_RISK_ENGINE_CONFIG_CONTRACT,
        "config_id": "future-risk-engine-config-024",
        "generated_at": generated_at,
        "paper_live_prep_only": True,
        "applied_to_real_execution": False,
        "max_total_exposure_usd": 0.0,
        "max_per_market_exposure_usd": 0.0,
        "market_allowlist": [],
        "market_denylist": [],
        "per_run_action_cap": 0,
        "kill_switch_enabled": True,
        "manual_approval_required": True,
        "wallet_integration_enabled": False,
        "signing_integration_enabled": False,
        "order_placement_enabled": False,
        "authenticated_endpoint_integration_enabled": False,
        "autonomous_execution_enabled": False,
        "notes": [
            "Skeleton is present for future review only.",
            "Caps default to zero while the kill switch is enabled.",
            "Manual approval remains required before any future live-prep change.",
            "No wallet, signing, order placement, or authenticated endpoint is connected.",
        ],
    }
    valid, errors = validate_future_risk_engine_config(config)
    config["validation"] = {"valid": valid, "errors": errors}
    if not valid:
        raise FutureRiskEngineConfigError("; ".join(errors))
    return config


def validate_future_risk_engine_config(config: Mapping[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if config.get("contract_version") != FUTURE_RISK_ENGINE_CONFIG_CONTRACT:
        errors.append(f"contract_version must be {FUTURE_RISK_ENGINE_CONFIG_CONTRACT!r}")
    for field in ("config_id", "generated_at"):
        if not clean_text(config.get(field)):
            errors.append(f"{field} must be a non-empty string")
    for field in ("max_total_exposure_usd", "max_per_market_exposure_usd"):
        _require_non_negative_number(config, field, errors)
    _require_non_negative_integer(config, "per_run_action_cap", errors)
    _require_string_list(config, "market_allowlist", errors)
    _require_string_list(config, "market_denylist", errors)
    for field, expected in (
        ("paper_live_prep_only", True),
        ("applied_to_real_execution", False),
        ("kill_switch_enabled", True),
        ("manual_approval_required", True),
        ("wallet_integration_enabled", False),
        ("signing_integration_enabled", False),
        ("order_placement_enabled", False),
        ("authenticated_endpoint_integration_enabled", False),
        ("autonomous_execution_enabled", False),
    ):
        if config.get(field) is not expected:
            errors.append(f"{field} must be {str(expected).lower()}")
    allowlist = set(str(item) for item in config.get("market_allowlist", []) if isinstance(item, str))
    denylist = set(str(item) for item in config.get("market_denylist", []) if isinstance(item, str))
    overlap = sorted(allowlist.intersection(denylist))
    if overlap:
        errors.append(f"market_allowlist and market_denylist overlap: {', '.join(overlap)}")
    return not errors, errors


def write_default_future_risk_engine_config(
    *,
    out_json_path: str | Path = ARTIFACT_DIR / "future_risk_engine_config.json",
    out_md_path: str | Path = ARTIFACT_DIR / "future_risk_engine_config.md",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    config = build_default_future_risk_engine_config(generated_at=generated_at)
    write_json(out_json_path, config)
    write_text(out_md_path, render_future_risk_engine_config_markdown(config))
    return config


def render_future_risk_engine_config_markdown(config: Mapping[str, Any]) -> str:
    validation = dict(config.get("validation", {}))
    return "\n".join(
        [
            "# PMBOT Future Risk Engine Config",
            "",
            "This is a paper/live-prep contract skeleton only.",
            "",
            "## Caps",
            "",
            f"- max_total_exposure_usd: `{config.get('max_total_exposure_usd')}`",
            f"- max_per_market_exposure_usd: `{config.get('max_per_market_exposure_usd')}`",
            f"- per_run_action_cap: `{config.get('per_run_action_cap')}`",
            f"- market_allowlist: `{config.get('market_allowlist')}`",
            f"- market_denylist: `{config.get('market_denylist')}`",
            "",
            "## Required Gates",
            "",
            f"- kill_switch_enabled: `{str(config.get('kill_switch_enabled')).lower()}`",
            f"- manual_approval_required: `{str(config.get('manual_approval_required')).lower()}`",
            "",
            "## Disabled Integrations",
            "",
            f"- wallet_integration_enabled: `{str(config.get('wallet_integration_enabled')).lower()}`",
            f"- signing_integration_enabled: `{str(config.get('signing_integration_enabled')).lower()}`",
            f"- order_placement_enabled: `{str(config.get('order_placement_enabled')).lower()}`",
            f"- authenticated_endpoint_integration_enabled: `{str(config.get('authenticated_endpoint_integration_enabled')).lower()}`",
            f"- autonomous_execution_enabled: `{str(config.get('autonomous_execution_enabled')).lower()}`",
            "",
            "## Validation",
            "",
            f"- valid: `{str(validation.get('valid')).lower()}`",
            *bullet_lines(str(item) for item in validation.get("errors", [])),
        ]
    ) + "\n"


def _require_non_negative_number(config: Mapping[str, Any], field: str, errors: list[str]) -> None:
    value = config.get(field)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        errors.append(f"{field} must be numeric")
        return
    if value < 0:
        errors.append(f"{field} must be >= 0")


def _require_non_negative_integer(config: Mapping[str, Any], field: str, errors: list[str]) -> None:
    value = config.get(field)
    if not isinstance(value, int) or isinstance(value, bool):
        errors.append(f"{field} must be an integer")
        return
    if value < 0:
        errors.append(f"{field} must be >= 0")


def _require_string_list(config: Mapping[str, Any], field: str, errors: list[str]) -> None:
    value = config.get(field)
    if not isinstance(value, list):
        errors.append(f"{field} must be a list")
        return
    if any(not isinstance(item, str) for item in value):
        errors.append(f"{field} must contain only strings")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the PMBOT future risk engine config skeleton.")
    parser.add_argument("--out-json", default=str(ARTIFACT_DIR / "future_risk_engine_config.json"))
    parser.add_argument("--out-md", default=str(ARTIFACT_DIR / "future_risk_engine_config.md"))
    args = parser.parse_args(argv)
    write_default_future_risk_engine_config(out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
