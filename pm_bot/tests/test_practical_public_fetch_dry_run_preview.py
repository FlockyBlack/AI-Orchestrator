from __future__ import annotations

import json
from pathlib import Path

from pm_bot.practical.public_fetch_dry_run_preview import build_fetch_dry_run_preview

FIXTURE = Path("pm_bot/tests/fixtures/public_read_only_fetch_prep/fetch_plan_5_markets.valid.json")


def test_dry_run_preview_says_live_fetch_is_not_allowed_now() -> None:
    plan = json.loads(FIXTURE.read_text(encoding="utf-8"))
    preview = build_fetch_dry_run_preview(plan)

    assert preview["live_fetch_allowed_now"] is False
    assert preview["live_fetch"]["allowed_now"] is False
    assert "Operator approval" in preview["live_fetch"]["reason"]


def test_dry_run_preview_operator_approval_required() -> None:
    plan = json.loads(FIXTURE.read_text(encoding="utf-8"))
    preview = build_fetch_dry_run_preview(plan)

    assert preview["approval_status"]["operator_approval_required"] is True
    assert preview["approval_status"]["operator_approval_granted"] is False


def test_dry_run_preview_summarizes_request_count_and_categories() -> None:
    plan = json.loads(FIXTURE.read_text(encoding="utf-8"))
    preview = build_fetch_dry_run_preview(plan)

    assert preview["request_count"] == 10
    assert preview["source_category_counts"]["public_market_metadata_endpoint_placeholder"] == 5
    assert preview["evidence_expected_counts"]
