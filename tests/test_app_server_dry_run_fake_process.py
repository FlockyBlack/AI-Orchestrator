from __future__ import annotations

import sys
from pathlib import Path

from ai_orchestrator.symphony_adapter.app_server_session_dry_run import (
    AppServerDryRunConfig,
    build_default_dry_run_config,
    run_app_server_dry_run,
    write_app_server_dry_run_artifacts,
)
from test_codex_app_server_protocol_index import _write_schema_dir


def test_fake_app_server_success_records_started_and_stopped(tmp_path: Path) -> None:
    schema_dir = _write_schema_dir(tmp_path)
    config = _fake_config(tmp_path, schema_dir, "success")

    result = run_app_server_dry_run(config)

    assert result.process_started is True
    assert result.process_stopped is True
    assert result.protocol_probe_attempted is True
    assert result.protocol_probe_succeeded is True
    assert result.schema_only is False
    assert "fake app-server mode=success" in result.stderr


def test_fake_app_server_timeout_stops_process_safely(tmp_path: Path) -> None:
    schema_dir = _write_schema_dir(tmp_path)
    config = AppServerDryRunConfig.from_dict(
        {
            **_fake_config(tmp_path, schema_dir, "hangs_until_timeout").to_dict(),
            "timeout_seconds": 1,
            "startup_timeout_seconds": 0.2,
            "shutdown_timeout_seconds": 0.2,
        }
    )

    result = run_app_server_dry_run(config)

    assert result.process_started is True
    assert result.protocol_probe_attempted is True
    assert result.protocol_probe_succeeded is False
    assert result.process_stopped is True
    assert any("timed out" in error for error in result.errors)


def test_dry_run_artifacts_written(tmp_path: Path) -> None:
    schema_dir = _write_schema_dir(tmp_path)
    result = run_app_server_dry_run(_fake_config(tmp_path, schema_dir, "success"))

    paths = write_app_server_dry_run_artifacts(result, tmp_path / "artifacts")

    for path in paths.values():
        assert Path(path).exists()


def _fake_config(tmp_path: Path, schema_dir: Path, mode: str) -> AppServerDryRunConfig:
    fake = Path(__file__).parent / "fixtures" / "fake_app_server" / "fake_app_server.py"
    config = build_default_dry_run_config(tmp_path, schema_dir, tmp_path)
    return AppServerDryRunConfig.from_dict(
        {
            **config.to_dict(),
            "codex_command": [sys.executable, str(fake), mode],
            "operator_approved": True,
            "timeout_seconds": 3,
            "startup_timeout_seconds": 1,
            "shutdown_timeout_seconds": 1,
        }
    )
