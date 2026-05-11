from __future__ import annotations

from pathlib import Path

from ai_orchestrator.symphony_adapter.app_server_session_dry_run import (
    AppServerDryRunConfig,
    build_app_server_command,
    build_default_dry_run_config,
    validate_dry_run_config,
)
from test_codex_app_server_protocol_index import _write_schema_dir


def test_default_dry_run_config_validates(tmp_path: Path) -> None:
    schema_dir = _write_schema_dir(tmp_path)
    config = build_default_dry_run_config(tmp_path, schema_dir, tmp_path)

    validation = validate_dry_run_config(config)

    assert validation["valid"] is True
    assert build_app_server_command(config) == ("codex", "app-server", "--listen", "stdio://")
    assert config.allow_network is False
    assert config.allow_real_task_execution is False


def test_unsafe_flags_rejected(tmp_path: Path) -> None:
    schema_dir = _write_schema_dir(tmp_path)
    config = AppServerDryRunConfig.from_dict(
        {
            **build_default_dry_run_config(tmp_path, schema_dir, tmp_path).to_dict(),
            "allow_network": True,
            "allow_auth": True,
            "allow_browser": True,
            "allow_real_task_execution": True,
        }
    )

    validation = validate_dry_run_config(config)

    assert validation["valid"] is False
    assert any("allow_network" in error for error in validation["errors"])
    assert any("allow_auth" in error for error in validation["errors"])
    assert any("allow_browser" in error for error in validation["errors"])
    assert any("allow_real_task_execution" in error for error in validation["errors"])


def test_timeout_over_120_rejected(tmp_path: Path) -> None:
    schema_dir = _write_schema_dir(tmp_path)
    config = AppServerDryRunConfig.from_dict(
        {**build_default_dry_run_config(tmp_path, schema_dir, tmp_path).to_dict(), "timeout_seconds": 121}
    )

    validation = validate_dry_run_config(config)

    assert validation["valid"] is False
    assert "timeout_seconds must be <= 120" in validation["errors"]


def test_non_loopback_websocket_rejected(tmp_path: Path) -> None:
    schema_dir = _write_schema_dir(tmp_path)
    config = AppServerDryRunConfig.from_dict(
        {
            **build_default_dry_run_config(tmp_path, schema_dir, tmp_path).to_dict(),
            "listen_mode": "ws_loopback",
            "ws_host": "0.0.0.0",
        }
    )

    validation = validate_dry_run_config(config)

    assert validation["valid"] is False
    assert "ws_host must be loopback-only" in validation["errors"]
