from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

from pm_bot.operator_runner.operator_ui_panel_v1 import (
    build_operator_ui_panel_v1,
    summarize_operator_ui_panel_v1,
)
from pm_bot.operator_runner.telegram_operator_control_bot import (
    build_telegram_operator_control_summary,
)
from pm_bot.trading_core.paper_canary_drill import (
    PAPER_CANARY_DRILL_RESULT_CONTRACT,
    PAPER_CANARY_DRILL_STATUS_CONTRACT,
    PMBOT_ARTIFACT_DIR_ENV,
    REQUIRED_FALSE_FLAGS,
    paper_canary_artifact_paths,
    render_paper_canary_telegram_status,
    resolve_paper_canary_artifact_dir,
    run_paper_canary_drill,
    validate_paper_canary_drill_result,
)
from pm_bot.trading_core.live_canary_replay_acceptance import build_live_connector_blocker_matrix

GENERATED_AT = "2026-05-14T00:00:00Z"

FORBIDDEN_EXACT_KEYS = {
    "signed_payload",
    "signed_order",
    "signature",
    "raw_transaction",
    "order_id",
    "order_ids",
    "tx_hash",
    "transaction_hash",
    "fill",
    "fills",
    "fill_id",
    "balance",
    "balances",
    "private_key",
    "mnemonic",
    "seed_phrase",
    "api_key",
    "api_secret",
    "access_token",
    "bearer_token",
    "telegram_bot_token",
    "raw_telegram_bot_token",
}

BAD_OPERATOR_PHRASES = (
    "approve live",
    "execute trade",
    "buy now",
    "sell now",
    "signed order",
    "tx hash",
    "fake fill",
    "balance:",
    "pnl",
)


def _walk_key_paths(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            next_path = f"{path}.{key_text}"
            if key_text.lower() in FORBIDDEN_EXACT_KEYS:
                paths.append(next_path)
            paths.extend(_walk_key_paths(nested, next_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(_walk_key_paths(nested, f"{path}[{index}]"))
    return paths


def _assert_required_false_flags(value: Mapping[str, Any]) -> None:
    assert value["execution_mode"] == "paper"
    assert value["review_only"] is True
    for field in REQUIRED_FALSE_FLAGS:
        assert value[field] is False
    assert value["resolved_blocker_count"] == 0
    assert value["network_used"] is False
    assert value["external_api_calls_performed"] is False
    assert value["environment_secrets_read"] is False
    assert value["secrets_read"] is False
    assert value["secrets_printed"] is False
    assert value["wallet_used"] is False
    assert value["cryptographic_signing_performed"] is False
    assert value["authenticated_endpoint_call_performed"] is False
    assert value["real_order_submitted"] is False
    assert value["fake_execution_artifacts_emitted"] is False


def test_paper_canary_drill_module_emits_json_markdown_and_latest_status(tmp_path: Path) -> None:
    result = run_paper_canary_drill(
        market="BTC",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    paths = paper_canary_artifact_paths(tmp_path)
    saved_result = json.loads(paths["result"].read_text(encoding="utf-8"))
    latest_status = json.loads(paths["latest_status"].read_text(encoding="utf-8"))
    operator_md = paths["operator_md"].read_text(encoding="utf-8")

    assert result["contract_version"] == PAPER_CANARY_DRILL_RESULT_CONTRACT
    assert saved_result == result
    assert latest_status["contract_version"] == PAPER_CANARY_DRILL_STATUS_CONTRACT
    assert latest_status["status"] == "paper_canary_drill_completed"
    assert latest_status["market"] == "BTC fixture"
    assert latest_status["mode"] == "paper / review-only"
    assert latest_status["live_execution"] == "blocked"
    assert paths["normalized_market"].exists()
    assert paths["market_snapshot"].exists()
    assert paths["order_intent"].exists()
    assert paths["risk_readiness"].exists()
    assert paths["gonogo"].exists()
    assert paths["approval_packet"].exists()
    assert paths["approval_packet_md"].exists()
    assert paths["latest_status_md"].exists()
    assert "This is not order submission." in operator_md
    assert "No wallet connection, signing, authenticated Polymarket call, or real order submission is available." in operator_md
    assert result["validation"]["valid"] is True
    assert validate_paper_canary_drill_result(result, generated_at=GENERATED_AT)["valid"] is True
    _assert_required_false_flags(result)
    _assert_required_false_flags(latest_status)


def test_paper_canary_cli_uses_pmbot_artifact_dir_and_prints_concise_operator_output(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv(PMBOT_ARTIFACT_DIR_ENV, str(tmp_path))
    env = os.environ.copy()

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.paper_canary_drill",
            "--market",
            "BTC",
            "--dry-run",
        ],
        cwd=Path.cwd(),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    paths = paper_canary_artifact_paths(tmp_path)

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip().splitlines() == [
        "Paper canary drill completed.",
        "Market: BTC fixture",
        "Mode: paper / review-only",
        "Live execution: blocked",
        f"Artifact: {paths['result'].as_posix()}",
    ]
    assert resolve_paper_canary_artifact_dir() == tmp_path
    assert paths["result"].exists()
    assert paths["operator_md"].exists()
    assert paths["latest_status"].exists()


def test_default_paper_drill_does_not_open_network_auth_wallet_signing_or_order_paths(
    monkeypatch,
    tmp_path: Path,
) -> None:
    def blocked_socket(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("paper canary drill must not open network sockets by default")

    monkeypatch.setattr(socket, "socket", blocked_socket)

    result = run_paper_canary_drill(
        market="BTC",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )

    assert result["network_check_requested"] is False
    assert result["network_used"] is False
    assert result["authenticated_polymarket_enabled"] is False
    assert result["live_connector_enabled"] is False
    assert result["order_submission_enabled"] is False
    assert result["wallet_signing_enabled"] is False
    assert result["signing_enabled"] is False
    assert result["signed_payload_generation_enabled"] is False
    assert result["signed_order_generation_enabled"] is False
    _assert_required_false_flags(result)


def test_artifacts_contain_no_signed_payload_order_fake_execution_ids_or_secret_fields(tmp_path: Path) -> None:
    result = run_paper_canary_drill(
        market="BTC",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    paths = paper_canary_artifact_paths(tmp_path)
    loaded_artifacts = [
        result,
        json.loads(paths["result"].read_text(encoding="utf-8")),
        json.loads(paths["latest_status"].read_text(encoding="utf-8")),
        json.loads(paths["normalized_market"].read_text(encoding="utf-8")),
        json.loads(paths["market_snapshot"].read_text(encoding="utf-8")),
        json.loads(paths["order_intent"].read_text(encoding="utf-8")),
    ]

    for artifact in loaded_artifacts:
        assert _walk_key_paths(artifact) == []
    assert result["simulated_paper_order_intent"]["order_intent_is_not_order_submission"] is True
    assert result["simulated_paper_order_intent"]["executable_submission_payload_present"] is False
    assert result["simulated_paper_order_intent"]["fake_execution_artifacts_emitted"] is False
    assert result["simulated_paper_order_intent"]["analysis_is_not_live_recommendation"] is True


def test_operator_ui_reads_latest_paper_canary_status_passively(tmp_path: Path) -> None:
    result = run_paper_canary_drill(
        market="BTC",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    status = json.loads(paper_canary_artifact_paths(tmp_path)["latest_status"].read_text(encoding="utf-8"))
    panel = build_operator_ui_panel_v1(
        dashboard={"paper_canary_drill_status_summary": status},
        blocker_matrix=build_live_connector_blocker_matrix(generated_at=GENERATED_AT),
        latest_paths={"paper_canary_drill_status": status["latest_status_path"]},
        generated_at=GENERATED_AT,
    )
    summary = summarize_operator_ui_panel_v1(panel)
    section_ids = {section["section_id"] for section in panel["sections"]}

    assert result["operator_ui_status_feed"] == status
    assert panel["validation"]["valid"] is True
    assert panel["paper_canary_drill_section_ready"] is True
    assert panel["paper_canary_drill_status_summary"]["status"] == "paper_canary_drill_completed"
    assert panel["paper_canary_drill_status_summary"]["market"] == "BTC fixture"
    assert panel["paper_canary_drill_status_summary"]["live_execution"] == "blocked"
    assert panel["paper_canary_drill_status_summary"]["artifact"] == status["artifact"]
    assert "paper_canary_drill" in section_ids
    assert summary["paper_canary_drill_status"] == "paper_canary_drill_completed"
    assert summary["paper_canary_drill_market"] == "BTC fixture"
    assert summary["paper_canary_drill_live_execution"] == "blocked"
    assert panel["ui_exposes_no_executable_live_action"] is True


def test_telegram_visible_summary_is_review_only_and_has_no_live_execution_commands(tmp_path: Path) -> None:
    result = run_paper_canary_drill(
        market="BTC",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )
    status = result["operator_ui_status_feed"]
    text = render_paper_canary_telegram_status(status)
    control_summary = build_telegram_operator_control_summary(
        context={"paper_canary_drill_status_summary": status},
        generated_at=GENERATED_AT,
    )
    serialized_paper_canary_summary = json.dumps(
        control_summary["paper_canary_drill_status_summary"],
        sort_keys=True,
    ).lower()

    assert text.splitlines()[0] == "Paper canary drill completed."
    assert "Live execution: blocked" in text
    assert control_summary["paper_canary_drill_status_summary"]["status"] == "paper_canary_drill_completed"
    assert control_summary["paper_canary_drill_status_summary"]["live_execution"] == "blocked"
    assert control_summary["validation"]["valid"] is True
    for phrase in BAD_OPERATOR_PHRASES:
        assert phrase not in text.lower()
        assert phrase not in serialized_paper_canary_summary
    assert control_summary["review_only"] is True
    assert control_summary["order_submission_enabled"] is False
    assert control_summary["wallet_signing_enabled"] is False
    assert control_summary["signing_enabled"] is False
    assert control_summary["live_execution_approved"] is False


def test_artifact_paths_are_direct_windows_safe_lookups_without_recursive_scan(tmp_path: Path) -> None:
    paths = paper_canary_artifact_paths(tmp_path)

    assert paths["root"] == tmp_path
    assert paths["result"] == tmp_path / "paper_canary_drill_052_result.json"
    assert paths["latest_status"] == tmp_path / "latest_paper_canary_status_052.json"
    assert paths["operator_md"] == tmp_path / "paper_canary_drill_052_operator.md"
    assert all(path.parent == tmp_path for key, path in paths.items() if key != "root")

    run_paper_canary_drill(
        market="BTC",
        dry_run=True,
        artifact_dir=tmp_path,
        generated_at=GENERATED_AT,
    )

    assert paths["latest_status"].is_file()
    assert json.loads(paths["latest_status"].read_text(encoding="utf-8"))["artifact"] == paths["result"].as_posix()
