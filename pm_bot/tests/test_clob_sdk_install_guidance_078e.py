from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.live_account_readonly_state_models import (
    EXPECTED_SDK_INSTALL_COMMAND,
    EXPECTED_SDK_MODULE,
)
from pm_bot.trading_core.telegram_balance_readonly_status_077f import (
    SAFE_ACCOUNT_PROBE_COMMAND,
    build_telegram_balance_readonly_status,
)

GENERATED_AT = "2026-05-17T00:00:00+04:00"
REPO_ROOT = Path(__file__).resolve().parents[2]
RUNBOOK_PATH = REPO_ROOT / "docs" / "PMBOT_CLOB_SDK_INSTALL_AND_READONLY_BALANCE_RUNBOOK_078E.md"


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_visible_runtime_credentials(root: Path) -> None:
    artifact_dir = root / "runtime_credential_visibility_077c"
    latest = {
        "contract_version": "pmbot_latest_runtime_credential_visibility_077c_status.v1",
        "status": "runtime_credentials_visible",
        "polymarket_l2_visible": True,
        "wallet_context_visible": True,
        "telegram_credentials_visible": True,
        "raw_values_emitted": False,
        "allowed_for_live": False,
    }
    result = {
        "contract_version": "pmbot_runtime_credential_visibility_077c_result.v1",
        "status": "runtime_credentials_visible",
        "group_summary": {
            "polymarket_l2_visible": True,
            "polymarket_l2_missing_env_vars": [],
            "wallet_context_visible": True,
            "wallet_context_missing_env_vars": [],
            "telegram_credentials_visible": True,
        },
        "raw_values_emitted": False,
        "allowed_for_live": False,
        "trading_requested": False,
    }
    _write_json(artifact_dir / "latest_runtime_credential_visibility_077c_status.json", latest)
    _write_json(artifact_dir / "runtime_credential_visibility_077c_result.json", result)


def _write_sdk_unavailable_account_artifact(root: Path) -> None:
    latest = {
        "contract_version": "pmbot_latest_live_account_readonly_state_status_070c.v1",
        "status": "blocked_sdk_unavailable",
        "sdk_status": "blocked_sdk_unavailable",
        "expected_sdk_module": EXPECTED_SDK_MODULE,
        "expected_install_command": EXPECTED_SDK_INSTALL_COMMAND,
        "python_executable": "C:/safe/python.exe",
        "account_state_probe_performed": False,
        "generated_at": GENERATED_AT,
        "allowed_for_live": False,
        "trading_requested": False,
        "order_submission_enabled": False,
        "wallet_connection_attempted": False,
        "signing_enabled": False,
        "raw_values_emitted": False,
    }
    _write_json(
        root / "live_account_readonly_state_probe_070c" / "latest_live_account_readonly_state_status_070c.json",
        latest,
    )


def test_clob_sdk_install_runbook_contains_required_no_live_commands() -> None:
    text = RUNBOOK_PATH.read_text(encoding="utf-8")

    required_snippets = (
        "where python",
        "python --version",
        "python -m pip --version",
        "python -m pip show py-clob-client",
        "python -m pip show py-clob-client-v2",
        EXPECTED_SDK_INSTALL_COMMAND,
        "python -m pip install py-clob-client-v2",
        "@'",
        "'@ | python -",
        SAFE_ACCOUNT_PROBE_COMMAND,
        "does not install packages automatically",
        "Use `python -m pip ...`, not a standalone `pip ...` command.",
        "no raw secrets in terminal output",
        "`allowed_for_live` remains `false`",
        "`trading_requested` remains `false`",
    )
    for snippet in required_snippets:
        assert snippet in text

    forbidden_snippets = (
        "allowed_for_live" + "=true",
        "trading_requested" + "=true",
        "--live",
        "--execute",
        "--submit",
        "--cancel",
    )
    for snippet in forbidden_snippets:
        assert snippet not in text


def test_telegram_balance_sdk_missing_guidance_shows_exact_copy_and_safe_commands(tmp_path: Path) -> None:
    _write_visible_runtime_credentials(tmp_path)
    _write_sdk_unavailable_account_artifact(tmp_path)

    status = build_telegram_balance_readonly_status(artifact_root=tmp_path, generated_at=GENERATED_AT)
    text = status["status_text_ru"]

    assert status["screen_variant"] == "account_probe_blocked_sdk_unavailable"
    assert "Проверка баланса недоступна: не найден Polymarket CLOB SDK в текущем Python." in text
    assert "Проверка аккаунта заблокирована" not in text
    assert "Безопасные команды:" in text
    assert EXPECTED_SDK_INSTALL_COMMAND in text
    assert SAFE_ACCOUNT_PROBE_COMMAND in text
    assert "Python: C:/safe/python.exe" in text
    assert "Баланс не прочитан; фейковые значения не показываются." in text


def test_install_guidance_constants_stay_no_live_and_expected() -> None:
    assert EXPECTED_SDK_MODULE == "py_clob_client.client"
    assert EXPECTED_SDK_INSTALL_COMMAND == "python -m pip install py-clob-client"
    assert SAFE_ACCOUNT_PROBE_COMMAND == (
        "python -m pm_bot.operator_runner.live_account_readonly_state_probe "
        "--market BTC --strategy tiny-momentum --dry-run"
    )
    assert "--dry-run" in SAFE_ACCOUNT_PROBE_COMMAND
    assert "allowed_for_live" + "=true" not in EXPECTED_SDK_INSTALL_COMMAND
    assert "trading_requested" + "=true" not in EXPECTED_SDK_INSTALL_COMMAND
