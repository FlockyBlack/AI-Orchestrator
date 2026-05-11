from __future__ import annotations

import json
from pathlib import Path

from pm_bot.operator_runner.workflow_config import validate_operator_workflow_config

FIXTURE_DIR = Path("pm_bot/tests/fixtures/operator_runner")


def _load(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_config_passes() -> None:
    valid, errors = validate_operator_workflow_config(_load("operator_workflow_config.valid.json"))

    assert valid is True
    assert errors == []


def test_live_fetch_config_blocked() -> None:
    valid, errors = validate_operator_workflow_config(_load("operator_workflow_config.unsafe_live_fetch.json"))

    assert valid is False
    assert "allow_live_fetch must be false" in errors


def test_real_trading_config_blocked() -> None:
    valid, errors = validate_operator_workflow_config(_load("operator_workflow_config.unsafe_real_trading.json"))

    assert valid is False
    assert "allow_real_trading must be false" in errors


def test_background_mode_blocked() -> None:
    config = _load("operator_workflow_config.valid.json")
    config["background_mode_allowed"] = True

    valid, errors = validate_operator_workflow_config(config)

    assert valid is False
    assert "background_mode_allowed must be false" in errors
