from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pm_bot.trading_core.static_safety_invariant_report import (
    run_static_safety_invariant_report,
    static_safety_invariant_report_artifact_paths,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"

NEW_060Q_RUNTIME_FILES = (
    Path("pm_bot/trading_core/static_safety_invariant_report_models.py"),
    Path("pm_bot/trading_core/static_safety_invariant_report.py"),
    Path("pm_bot/operator_runner/static_safety_invariant_report.py"),
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fake_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "pm_bot" / "trading_core" / "artifacts").mkdir(parents=True)
    return root


def _finding_categories(report: dict) -> set[str]:
    return {str(row.get("category")) for row in report.get("findings", [])}


def _finding_pattern_ids(report: dict) -> set[str]:
    return {str(row.get("pattern_id")) for row in report.get("findings", [])}


def test_static_safety_invariant_report_command_runs(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.static_safety_invariant_report",
            "--scope",
            "pm_bot",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path / "cli_artifacts"),
        ],
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Static safety invariant report completed." in completed.stdout
    assert "Live execution: blocked" in completed.stdout
    assert "Order submission: blocked" in completed.stdout
    assert "Signing: blocked" in completed.stdout
    assert "Wallet: blocked" in completed.stdout


def test_temp_runtime_file_with_unsafe_order_submission_pattern_is_detected(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    _write(
        repo / "pm_bot" / "trading_core" / "unsafe_runtime.py",
        "order_submission_enabled = True\nclient.submit_order({'market': 'BTC'})\n",
    )

    report = run_static_safety_invariant_report(
        scope="pm_bot",
        dry_run=True,
        repository_root=repo,
        artifact_dir=repo / "out",
        generated_at=GENERATED_AT,
    )

    assert report["critical_count"] >= 1
    assert "order_submission_activation" in _finding_categories(report)
    assert {"unsafe_true_assignment", "order_submission_call"}.issubset(_finding_pattern_ids(report))


def test_temp_artifact_with_signed_payload_marker_is_detected(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    _write(repo / "pm_bot" / "trading_core" / "runtime.py", "SAFE_FLAG = False\n")
    _write(
        repo / "pm_bot" / "trading_core" / "artifacts" / "unsafe_signed.json",
        json.dumps({"signed_payload_generated": True, "signed_payload": "fake-marker"}),
    )

    report = run_static_safety_invariant_report(
        scope="pm_bot",
        dry_run=True,
        include_artifacts=True,
        repository_root=repo,
        artifact_dir=repo / "out",
        generated_at=GENERATED_AT,
    )

    assert report["critical_count"] >= 1
    assert "signer_activation" in _finding_categories(report)
    assert "unsafe_json_flag_true" in _finding_pattern_ids(report)


def test_temp_artifact_with_fake_tx_order_fill_balance_and_pnl_fields_is_detected(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    _write(repo / "pm_bot" / "trading_core" / "runtime.py", "SAFE_FLAG = False\n")
    _write(
        repo / "pm_bot" / "trading_core" / "artifacts" / "fake_execution.json",
        json.dumps(
            {
                "tx_hash": "0xabc",
                "order_id": "order-1",
                "fill": {"price": 0.5},
                "balance": 100,
                "pnl": 4.2,
            }
        ),
    )

    report = run_static_safety_invariant_report(
        scope="pm_bot",
        dry_run=True,
        include_artifacts=True,
        repository_root=repo,
        artifact_dir=repo / "out",
        generated_at=GENERATED_AT,
    )

    assert report["critical_count"] >= 5
    assert "runtime_account_or_execution_artifact" in _finding_categories(report)
    assert "tx_order_fill_balance_pnl_field" in _finding_pattern_ids(report)


def test_docs_and_tests_references_are_allowlisted_under_strict_scan(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    _write(repo / "pm_bot" / "trading_core" / "runtime.py", "SAFE_FLAG = False\n")
    _write(
        repo / "pm_bot" / "tests" / "test_forbidden_examples.py",
        "order_submission_enabled = True\nclient.submit_order({'example': True})\n",
    )

    report = run_static_safety_invariant_report(
        scope="pm_bot",
        dry_run=True,
        strict=True,
        repository_root=repo,
        artifact_dir=repo / "out",
        generated_at=GENERATED_AT,
    )

    assert report["critical_count"] == 0
    assert report["allowed_reference_count"] >= 1
    assert {row["severity"] for row in report["findings"]} == {"allowed_reference"}


def test_safe_false_flags_pass_without_critical_findings(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    _write(repo / "pm_bot" / "trading_core" / "runtime.py", "SAFE_FLAG = False\n")
    safe_flags = {
        "live_execution_approved": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "resolved_blocker_count": 0,
    }
    _write(repo / "pm_bot" / "trading_core" / "artifacts" / "safe_false_flags.json", json.dumps(safe_flags))

    report = run_static_safety_invariant_report(
        scope="pm_bot",
        dry_run=True,
        include_artifacts=True,
        repository_root=repo,
        artifact_dir=repo / "out",
        generated_at=GENERATED_AT,
    )

    assert report["critical_count"] == 0
    assert report["safe_false_reference_count"] >= len(safe_flags)
    assert report["safety_ok"] is True


def test_latest_status_and_operator_markdown_are_written(tmp_path: Path) -> None:
    repo = _fake_repo(tmp_path)
    _write(repo / "pm_bot" / "trading_core" / "runtime.py", "SAFE_FLAG = False\n")
    out_dir = repo / "out"

    report = run_static_safety_invariant_report(
        scope="pm_bot",
        dry_run=True,
        repository_root=repo,
        artifact_dir=out_dir,
        generated_at=GENERATED_AT,
    )
    paths = static_safety_invariant_report_artifact_paths(out_dir)
    latest_status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))
    operator_md = paths["operator_md"].read_text(encoding="utf-8")

    assert report["latest_status"]["latest_status_path"] == paths["latest_status"].as_posix()
    assert latest_status["status"] == "passed"
    assert "live execution blocked" in operator_md
    assert "order submission blocked" in operator_md
    assert "signing blocked" in operator_md
    assert "wallet usage blocked" in operator_md


def test_existing_052_to_059_focused_commands_still_have_blocked_live_summaries(tmp_path: Path) -> None:
    commands = [
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.paper_canary_drill",
            "--market",
            "BTC",
            "--dry-run",
            "--artifact-dir",
            str(tmp_path / "paper_canary_052"),
        ],
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.live_connector_preflight",
            "--market",
            "BTC",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path / "live_connector_056"),
        ],
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.authenticated_clob_preflight",
            "--market",
            "BTC",
            "--dry-run",
            "--no-order-auth-get",
            "--artifacts-dir",
            str(tmp_path / "auth_clob_059"),
        ],
    ]
    outputs = []
    for command in commands:
        completed = subprocess.run(
            command,
            cwd=Path.cwd(),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr
        outputs.append(completed.stdout)

    assert "Paper canary drill completed." in outputs[0]
    assert "Live connector preflight completed." in outputs[1]
    assert "No-order auth GET: mocked" in outputs[2]
    assert all("Live execution: blocked" in output for output in outputs)


def test_no_scheduler_daemon_background_or_autonomous_loop_added() -> None:
    forbidden_runtime_terms = (
        "while True",
        "time.sleep(",
        "import threading",
        "import asyncio",
        "Start-Process",
    )
    for path in NEW_060Q_RUNTIME_FILES:
        source = path.read_text(encoding="utf-8")
        for term in forbidden_runtime_terms:
            assert term not in source, path
