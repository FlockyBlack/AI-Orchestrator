from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.practical_workflow_index import build_practical_workflow_index

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/daily_workflow_015")
CATALOG_JSON = ARTIFACT_DIR / "practical_command_catalog_015.json"
CATALOG_MD = ARTIFACT_DIR / "practical_command_catalog_015.md"
INDEX_JSON = ARTIFACT_DIR / "practical_workflow_index_015.json"
INDEX_MD = ARTIFACT_DIR / "practical_workflow_index_015.md"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_command_catalog_exists() -> None:
    catalog = _load(CATALOG_JSON)

    assert CATALOG_MD.exists()
    assert catalog["contract_version"] == "pmbot_practical_command_catalog.v1"
    assert catalog["safe_commands"]
    assert catalog["manual_only_steps"]
    assert catalog["prohibited_commands"]


def test_safe_commands_do_not_include_trading_wallet_or_order_commands() -> None:
    catalog = _load(CATALOG_JSON)
    forbidden_fragments = (
        "wallet",
        "private-key",
        "private_key",
        "signing",
        "order",
        "trade",
        "trading",
        "openrouter",
        "polymarket",
        "run-codex-once",
        "run-codex-batch",
    )

    for row in catalog["safe_commands"]:
        command = row["command"].lower()
        assert all(fragment not in command for fragment in forbidden_fragments)
        assert row["local_only"] is True
        assert row["requires_api_key"] is False
        assert row["requires_network"] is False


def test_workflow_index_exists_and_lists_expected_dashboard_paths() -> None:
    index = _load(INDEX_JSON)

    assert INDEX_MD.exists()
    assert index["contract_version"] == "pmbot_practical_workflow_index.v1"
    assert index["primary_dashboard"]["path"] == "docs/PMBOT_PRACTICAL_DAILY_OPERATOR_RUNBOOK.md"
    assert index["daily_summary"]["md_path"] == "pm_bot/practical/artifacts/daily_workflow_015/daily_workflow_summary_015.md"
    assert index["manual_feedback_dashboard"]["md_path"] == (
        "pm_bot/practical/artifacts/manual_outcome_feedback_014/feedback_readiness_dashboard_014.md"
    )
    assert index["outcome_recheck_queue"]["md_path"] == (
        "pm_bot/practical/artifacts/outcome_recheck_source_learning_013/outcome_recheck_queue_013.md"
    )
    assert index["public_evidence_dashboard"]["md_path"] == (
        "pm_bot/practical/artifacts/public_evidence_dashboard_011/public_evidence_tracking_dashboard_011.md"
    )


def test_workflow_index_reports_missing_artifacts_if_absent() -> None:
    missing_path = "pm_bot/practical/artifacts/daily_workflow_015/definitely_missing_015.marker"
    index = build_practical_workflow_index(expected_paths=[missing_path])

    assert any(row["path"] == missing_path for row in index["missing_expected_artifacts"])


def test_prohibited_actions_are_present() -> None:
    catalog = _load(CATALOG_JSON)
    prohibited = "\n".join(catalog["prohibited_commands"]).lower()

    assert "run-codex-once" in prohibited
    assert "run-codex-batch" in prohibited
    assert "openrouter" in prohibited
    assert "polymarket" in prohibited
    assert "wallet" in prohibited
    assert "trading endpoint" in prohibited
