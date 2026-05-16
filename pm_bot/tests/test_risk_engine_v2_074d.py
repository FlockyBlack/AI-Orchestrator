from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Mapping

from pm_bot.trading_core.risk_engine_v2_review import (
    SAFE_CLI_COMMAND,
    risk_engine_v2_review_artifact_paths,
    run_risk_engine_v2_review,
)

GENERATED_AT = "2026-05-16T00:00:00+04:00"
RAW_PRIVATE_KEY = "0x" + "9" * 64
RAW_API_SECRET = "raw-api-secret-risk-engine-v2-never-output"


def _minimal_env(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    env = {
        "PYTHONPATH": str(Path.cwd()),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "COMSPEC": os.environ.get("COMSPEC", ""),
        "PATH": os.environ.get("PATH", ""),
    }
    env.update(dict(extra or {}))
    return env


def test_risk_engine_v2_review_empty_local_artifacts_blocks_live_and_writes_status(tmp_path: Path) -> None:
    generated = run_risk_engine_v2_review(
        market="btc",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_root=tmp_path / "sources",
        output_dir=tmp_path / "out",
        generated_at=GENERATED_AT,
    )
    latest = generated["latest_status"]
    paths = risk_engine_v2_review_artifact_paths(tmp_path / "out")

    assert latest["title"] == "🛡 Risk Engine v2"
    assert latest["market"] == "BTC"
    assert latest["strategy"] == "tiny-momentum"
    assert latest["allowed_for_live"] is False
    assert latest["first_supervised_tiny_order_blocked"] is True
    assert latest["gate_count"] == 7
    assert latest["remaining_blocker_count"] > 0
    assert latest["unknown_group_count"] > 0
    assert latest["top_blockers"]
    assert latest["safe_cli_command"] == SAFE_CLI_COMMAND
    assert paths["result"].exists()
    assert paths["latest_status"].exists()
    assert paths["safety_snapshot"].exists()


def test_risk_engine_v2_runner_requires_dry_run_and_rejects_live_flags(tmp_path: Path) -> None:
    missing_dry_run = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.risk_engine_v2_review",
            "--market",
            "BTC",
            "--artifacts-dir",
            str(tmp_path / "missing_dry_run"),
        ],
        cwd=Path.cwd(),
        env=_minimal_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    forbidden = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.risk_engine_v2_review",
            "--market",
            "BTC",
            "--dry-run",
            "--submit",
        ],
        cwd=Path.cwd(),
        env=_minimal_env(
            {
                "POLYMARKET_PRIVATE_KEY": RAW_PRIVATE_KEY,
                "POLYMARKET_API_SECRET": RAW_API_SECRET,
            }
        ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert missing_dry_run.returncode != 0
    assert "requires --dry-run" in missing_dry_run.stderr
    assert forbidden.returncode != 0
    assert "unsupported live/auth/wallet/sign/order/write flag" in forbidden.stderr
    rendered = "\n".join([missing_dry_run.stdout, missing_dry_run.stderr, forbidden.stdout, forbidden.stderr])
    assert RAW_PRIVATE_KEY not in rendered
    assert RAW_API_SECRET not in rendered


def test_risk_engine_v2_runner_json_output_stays_review_only(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.risk_engine_v2_review",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifact-root",
            str(tmp_path / "sources"),
            "--artifacts-dir",
            str(tmp_path / "out"),
            "--json",
        ],
        cwd=Path.cwd(),
        env=_minimal_env(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    payload = json.loads(completed.stdout)

    assert completed.returncode == 0, completed.stderr
    assert payload["allowed_for_live"] is False
    assert payload["first_supervised_tiny_order_blocked"] is True
    assert payload["network_used"] is False
    assert payload["polymarket_api_calls_performed"] == 0
    assert payload["wallet_enabled"] is False
    assert payload["signing_enabled"] is False
    assert payload["order_submission_enabled"] is False
    assert payload["background_worker_added"] is False
