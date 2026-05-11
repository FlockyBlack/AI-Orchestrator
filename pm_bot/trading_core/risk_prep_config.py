from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import ARTIFACT_DIR, GENERATED_AT, bullet_lines, clean_text, write_json, write_text

FUTURE_RISK_ENGINE_CONFIG_CONTRACT = "pmbot_future_risk_engine_config.v1"
RISK_ENGINE_CONFIG_CONTRACT = "pmbot_risk_engine_config.v1"
RISK_ENGINE_CONFIG_VERSION = "risk-engine-config-v1"


class FutureRiskEngineConfigError(ValueError):
    pass


class RiskEngineConfigError(ValueError):
    pass


def build_default_risk_engine_config(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    config = {
        "contract_version": RISK_ENGINE_CONFIG_CONTRACT,
        "config_version": RISK_ENGINE_CONFIG_VERSION,
        "config_id": "risk-engine-config-026",
        "generated_at": generated_at,
        "paper_only": True,
        "live_prep_only": True,
        "paper_live_prep_only": True,
        "applied_to_real_execution": False,
        "max_total_exposure_usd": 0.0,
        "max_market_exposure_usd": 0.0,
        "max_per_market_exposure_usd": 0.0,
        "max_single_action_notional_usd": 0.0,
        "market_allowlist": [],
        "market_denylist": [],
        "per_run_action_cap": 0,
        "require_fresh_evidence": True,
        "block_on_source_gap": True,
        "kill_switch_enabled": True,
        "manual_approval_required": True,
        "default_no_network_mode": True,
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
    valid, errors = validate_risk_engine_config(config)
    config["validation"] = {"valid": valid, "errors": errors}
    if not valid:
        raise RiskEngineConfigError("; ".join(errors))
    return config


def build_default_future_risk_engine_config(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    config = build_default_risk_engine_config(generated_at=generated_at)
    config["contract_version"] = FUTURE_RISK_ENGINE_CONFIG_CONTRACT
    config["config_id"] = "future-risk-engine-config-024"
    valid, errors = validate_future_risk_engine_config(config)
    config["validation"] = {"valid": valid, "errors": errors}
    if not valid:
        raise FutureRiskEngineConfigError("; ".join(errors))
    return config


def validate_risk_engine_config(config: Mapping[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if config.get("contract_version") not in {RISK_ENGINE_CONFIG_CONTRACT, FUTURE_RISK_ENGINE_CONFIG_CONTRACT}:
        errors.append(
            f"contract_version must be {RISK_ENGINE_CONFIG_CONTRACT!r} "
            f"or {FUTURE_RISK_ENGINE_CONFIG_CONTRACT!r}"
        )
    for field in ("config_id", "config_version", "generated_at"):
        if not clean_text(config.get(field)):
            errors.append(f"{field} must be a non-empty string")
    for field in (
        "max_total_exposure_usd",
        "max_market_exposure_usd",
        "max_single_action_notional_usd",
    ):
        _require_non_negative_number(config, field, errors)
    if "max_per_market_exposure_usd" in config:
        _require_non_negative_number(config, "max_per_market_exposure_usd", errors)
        if (
            isinstance(config.get("max_market_exposure_usd"), (int, float))
            and not isinstance(config.get("max_market_exposure_usd"), bool)
            and isinstance(config.get("max_per_market_exposure_usd"), (int, float))
            and not isinstance(config.get("max_per_market_exposure_usd"), bool)
            and float(config["max_market_exposure_usd"]) != float(config["max_per_market_exposure_usd"])
        ):
            errors.append("max_per_market_exposure_usd must match max_market_exposure_usd")
    _require_non_negative_integer(config, "per_run_action_cap", errors)
    _require_string_list(config, "market_allowlist", errors)
    _require_string_list(config, "market_denylist", errors)
    _require_no_duplicate_strings(config, "market_allowlist", errors)
    _require_no_duplicate_strings(config, "market_denylist", errors)
    for field in (
        "require_fresh_evidence",
        "block_on_source_gap",
        "kill_switch_enabled",
        "manual_approval_required",
    ):
        _require_bool_type(config, field, errors)
    for field, expected in (
        ("paper_only", True),
        ("live_prep_only", True),
        ("paper_live_prep_only", True),
        ("applied_to_real_execution", False),
        ("default_no_network_mode", True),
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


def validate_future_risk_engine_config(config: Mapping[str, Any]) -> tuple[bool, list[str]]:
    valid, errors = validate_risk_engine_config(config)
    errors = list(errors)
    if config.get("contract_version") != FUTURE_RISK_ENGINE_CONFIG_CONTRACT:
        errors.append(f"contract_version must be {FUTURE_RISK_ENGINE_CONFIG_CONTRACT!r}")
    for field, expected in (
        ("kill_switch_enabled", True),
        ("manual_approval_required", True),
    ):
        if config.get(field) is not expected:
            errors.append(f"{field} must be {str(expected).lower()}")
    return valid and not errors, errors


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
            f"- max_market_exposure_usd: `{config.get('max_market_exposure_usd')}`",
            f"- max_per_market_exposure_usd: `{config.get('max_per_market_exposure_usd')}`",
            f"- max_single_action_notional_usd: `{config.get('max_single_action_notional_usd')}`",
            f"- per_run_action_cap: `{config.get('per_run_action_cap')}`",
            f"- market_allowlist: `{config.get('market_allowlist')}`",
            f"- market_denylist: `{config.get('market_denylist')}`",
            "",
            "## Required Gates",
            "",
            f"- require_fresh_evidence: `{str(config.get('require_fresh_evidence')).lower()}`",
            f"- block_on_source_gap: `{str(config.get('block_on_source_gap')).lower()}`",
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


def _require_no_duplicate_strings(config: Mapping[str, Any], field: str, errors: list[str]) -> None:
    value = config.get(field)
    if not isinstance(value, list):
        return
    strings = [item for item in value if isinstance(item, str)]
    duplicates = sorted({item for item in strings if strings.count(item) > 1})
    if duplicates:
        errors.append(f"{field} contains duplicate entries: {', '.join(duplicates)}")


def _require_bool_type(config: Mapping[str, Any], field: str, errors: list[str]) -> None:
    if not isinstance(config.get(field), bool):
        errors.append(f"{field} must be a boolean")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write the PMBOT future risk engine config skeleton.")
    parser.add_argument("--out-json", default=str(ARTIFACT_DIR / "future_risk_engine_config.json"))
    parser.add_argument("--out-md", default=str(ARTIFACT_DIR / "future_risk_engine_config.md"))
    args = parser.parse_args(argv)
    write_default_future_risk_engine_config(out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
