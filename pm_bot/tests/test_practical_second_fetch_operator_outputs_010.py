from __future__ import annotations

import json
import re
from pathlib import Path

ARTIFACT_DIR = Path("pm_bot/practical/artifacts/public_source_url_fixes_010")

ACTION_PATTERN = re.compile(
    r"\b(?:should|must|recommend(?:ed)?|instruction|signal|execute|place)\s+"
    r"(?:a\s+)?(?:market\s+)?(?:buy|sell|hold|enter|exit|order)\b",
    re.IGNORECASE,
)
SIGNAL_PATTERN = re.compile(r"\b(?:probability|ev|edge|confidence)\b.{0,40}\b(?:signal|instruction)\b", re.IGNORECASE)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_second_public_evidence_operator_review_packet_exists() -> None:
    packet = _load(ARTIFACT_DIR / "second_public_evidence_operator_review_packet_010.json")

    assert (ARTIFACT_DIR / "second_public_evidence_operator_review_packet_010.md").exists()
    assert packet["contract_version"] == "pmbot_second_public_evidence_operator_review_packet.v1"
    assert packet["no_real_trade_decision"] is True
    assert packet["automatic_analysis_update_performed"] is False


def test_repair_summary_learning_and_console_outputs_exist() -> None:
    summary = _load(ARTIFACT_DIR / "source_url_repair_result_summary_010.json")
    learning = _load(ARTIFACT_DIR / "source_accessibility_learning_010.json")
    console = _load(ARTIFACT_DIR / "operator_console_second_fetch_010.json")

    assert (ARTIFACT_DIR / "source_url_repair_result_summary_010.md").exists()
    assert (ARTIFACT_DIR / "source_accessibility_learning_010.md").exists()
    assert (ARTIFACT_DIR / "operator_console_second_fetch_010.md").exists()
    assert summary["contract_version"] == "pmbot_public_source_url_repair_result_summary.v1"
    assert learning["contract_version"] == "pmbot_source_accessibility_learning.v1"
    assert console["contract_version"] == "pmbot_operator_console_second_fetch_card.v1"
    assert learning["no_autonomous_training_performed"] is True
    assert learning["no_real_trade_decision"] is True


def test_safety_scan_passes_and_unsafe_flags_are_false() -> None:
    scan = _load(ARTIFACT_DIR / "public_source_url_fixes_safety_scan_010.result.json")

    assert scan["safety_ok"] is True
    assert scan["openrouter_calls_performed"] == 0
    assert scan["authenticated_endpoints_used"] is False
    assert scan["wallet_or_private_key_access"] is False
    assert scan["orders_or_trading_actions"] is False
    assert scan["runtime_or_dispatcher_changes"] is False
    assert scan["market_recommendation_generated"] is False
    assert scan["probability_ev_edge_or_side_selection_generated"] is False
    assert scan["automatic_analysis_update_performed"] is False
    assert scan["no_autonomous_trading"] is True


def test_operator_outputs_do_not_contain_trading_recommendation_language() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in ARTIFACT_DIR.rglob("*")
        if path.suffix.lower() in {".json", ".md"}
    )

    assert ACTION_PATTERN.search(text) is None
    assert SIGNAL_PATTERN.search(text) is None


def test_no_wallet_order_or_trading_unsafe_flags() -> None:
    for path in ARTIFACT_DIR.rglob("*.json"):
        payload = _load(path)
        encoded = json.dumps(payload, sort_keys=True)
        assert '"wallet_or_private_key_access": true' not in encoded
        assert '"orders_or_trading_actions": true' not in encoded
        assert '"market_recommendation_generated": true' not in encoded
        assert '"probability_ev_edge_or_side_selection_generated": true' not in encoded
