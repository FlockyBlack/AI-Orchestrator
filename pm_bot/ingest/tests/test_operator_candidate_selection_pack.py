import json
import tempfile
import unittest
from pathlib import Path

from pm_bot.ingest.export_operator_candidate_selection_pack import (
    OVERLAY_SELECTION_FIELDS,
    SELECTION_FIELDS,
    OperatorSelectionPackError,
    build_overlay_template,
    build_selection_index,
    build_selection_index_payload,
    render_markdown_pack,
    validate_overlay_payload,
    write_selection_pack_artifacts,
)


ROOT = Path(__file__).resolve().parents[3]
ACTUAL_CANDIDATE_PREVIEW = ROOT / "pm_bot" / "ingest" / "candidate_intake_preview.v1.json"
EXPECTED_OPERATOR_INDEX = ROOT / "pm_bot" / "ingest" / "expected_operator_candidate_selection_index.v1.json"
FIXTURE_SOURCE_PATH = ROOT / "pm_bot" / "ingest" / "fixture_candidate_intake_preview.v1.json"


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _candidate(**overrides):
    candidate = {
        "accepting_orders": True,
        "active": True,
        "bucket": "usable_for_research_preview",
        "category_or_tags": ["fixture"],
        "closed": False,
        "end_date": "2026-12-31T00:00:00Z",
        "event_id": "event-1",
        "event_title": "Fixture event",
        "has_description": True,
        "liquidity": 10.0,
        "market_id": "market-1",
        "next_manual_action": "eligible_for_manual_research_packet_preview",
        "outcome_prices_count": 2,
        "outcomes_count": 2,
        "question": "Will the fixture condition occur?",
        "structural_findings": [],
        "volume": 20.0,
    }
    candidate.update(overrides)
    return candidate


def _candidate_preview(usable=None, closed=None, missing=None):
    usable = [] if usable is None else usable
    closed = [] if closed is None else closed
    missing = [] if missing is None else missing
    buckets = {
        "closed_or_not_accepting": closed,
        "missing_required_fields": missing,
        "unsupported_or_malformed": [],
        "usable_for_research_preview": usable,
        "watch_only_structure": [],
    }
    return {
        "artifact_type": "polymarket_candidate_intake_preview",
        "buckets": buckets,
        "schema_version": "candidate_intake_preview.v1",
        "source_normalized_preview_path": "pm_bot/ingest/fixture_normalized_market_preview.v1.json",
        "summary": {
            "closed_or_not_accepting": len(closed),
            "missing_required_fields": len(missing),
            "normalized_records_read": len(usable) + len(closed) + len(missing),
            "unsupported_or_malformed": 0,
            "usable_for_research_preview": len(usable),
            "watch_only_structure": 0,
        },
    }


def _iter_keys(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            yield str(key)
            yield from _iter_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_keys(item)


class OperatorCandidateSelectionPackTests(unittest.TestCase):
    def test_expected_json_fixture_matches_projection_from_usable_bucket_only(self):
        preview = _candidate_preview(
            usable=[
                _candidate(
                    category_or_tags=["fixture", "policy"],
                    event_id="event-b",
                    event_title="Fixture event B",
                    liquidity=100000.0,
                    market_id="market-b",
                    question="Will fixture B resolve?",
                    volume=500000.0,
                ),
                _candidate(
                    end_date="2026-11-30T00:00:00Z",
                    event_id="event-a",
                    event_title="Fixture event A",
                    liquidity=1.0,
                    market_id="market-a",
                    question="Will fixture A resolve?",
                    volume=2.0,
                ),
            ],
            closed=[
                _candidate(
                    accepting_orders=False,
                    bucket="closed_or_not_accepting",
                    closed=True,
                    market_id="closed-1",
                    structural_findings=["closed", "not_accepting_orders"],
                )
            ],
        )
        index = build_selection_index_payload(preview, FIXTURE_SOURCE_PATH)
        expected = _load_json(EXPECTED_OPERATOR_INDEX)
        self.assertEqual(index, expected)
        self.assertEqual([item["market_id"] for item in index["candidates"]], ["market-b", "market-a"])

    def test_all_actual_usable_candidates_are_represented(self):
        candidate_preview = _load_json(ACTUAL_CANDIDATE_PREVIEW)
        index = build_selection_index(ACTUAL_CANDIDATE_PREVIEW)
        usable = candidate_preview["buckets"]["usable_for_research_preview"]

        self.assertEqual(index["summary"]["usable_candidates_seen"], 50)
        self.assertEqual(index["summary"]["candidates_exported"], 50)
        self.assertEqual(len(index["candidates"]), 50)
        self.assertEqual(
            [item["market_id"] for item in index["candidates"]],
            [item["market_id"] for item in usable],
        )
        for candidate in index["candidates"]:
            self.assertEqual(tuple(candidate.keys()), SELECTION_FIELDS)
            self.assertEqual(candidate["bucket"], "usable_for_research_preview")

    def test_closed_or_not_accepting_candidates_are_not_exported(self):
        closed = _candidate(
            accepting_orders=False,
            bucket="closed_or_not_accepting",
            closed=True,
            market_id="closed-1",
            structural_findings=["closed", "not_accepting_orders"],
        )
        preview = _candidate_preview(usable=[_candidate(market_id="usable-1")], closed=[closed])
        index = build_selection_index_payload(preview, FIXTURE_SOURCE_PATH)

        self.assertEqual([candidate["market_id"] for candidate in index["candidates"]], ["usable-1"])
        self.assertNotIn("closed-1", [candidate["market_id"] for candidate in index["candidates"]])

    def test_no_ranking_scoring_recommendation_probability_ev_side_order_or_trade_fields_exist(self):
        index = build_selection_index(ACTUAL_CANDIDATE_PREVIEW)
        overlay = build_overlay_template(index)
        forbidden_exact = {
            "bet",
            "decision",
            "edge",
            "ev",
            "execution",
            "expected_value",
            "market_decision",
            "order",
            "orders",
            "probability",
            "recommendation",
            "score",
            "side",
            "signal",
            "stake",
            "trade",
            "trading",
        }
        allowed_order_fields = {"accepting_orders"}
        for payload in (index, overlay):
            for key in _iter_keys(payload):
                normalized = key.lower()
                self.assertNotIn(normalized, forbidden_exact)
                self.assertFalse(normalized.endswith("_score"))
                self.assertNotIn("probability", normalized)
                self.assertNotIn("recommendation", normalized)
                self.assertNotIn("expected_value", normalized)
                if "order" in normalized:
                    self.assertIn(normalized, allowed_order_fields)
                if "trade" in normalized or "trading" in normalized:
                    self.fail(f"Unexpected trade/trading field: {key}")

    def test_selection_overlay_template_is_blank_and_safe(self):
        index = build_selection_index(ACTUAL_CANDIDATE_PREVIEW)
        overlay = build_overlay_template(index)

        self.assertEqual(overlay["artifact_type"], "polymarket_operator_candidate_selection_overlay")
        self.assertEqual(overlay["schema_version"], "operator_candidate_selection_overlay.v1")
        self.assertEqual(len(overlay["selections"]), 50)
        for selection in overlay["selections"]:
            self.assertEqual(tuple(selection.keys()), OVERLAY_SELECTION_FIELDS)
            self.assertIsInstance(selection["market_id"], str)
            self.assertFalse(selection["selected_for_research_stub"])
            self.assertEqual(selection["operator_reason"], "")
            self.assertEqual(selection["operator_priority"], "")
            self.assertEqual(selection["operator_notes"], "")

    def test_invalid_selected_market_id_is_rejected_by_overlay_validator(self):
        index = build_selection_index_payload(
            _candidate_preview(usable=[_candidate(market_id="usable-1")]),
            FIXTURE_SOURCE_PATH,
        )
        overlay = build_overlay_template(index)
        overlay["selections"][0]["market_id"] = "unknown-market"

        with self.assertRaises(OperatorSelectionPackError) as caught:
            validate_overlay_payload(overlay, index)
        self.assertEqual(caught.exception.code, "overlay_market_id_unknown")

    def test_prohibited_overlay_fields_are_rejected_by_overlay_validator(self):
        index = build_selection_index_payload(
            _candidate_preview(usable=[_candidate(market_id="usable-1")]),
            FIXTURE_SOURCE_PATH,
        )
        overlay = build_overlay_template(index)
        overlay["selections"][0]["score"] = 1

        with self.assertRaises(OperatorSelectionPackError) as caught:
            validate_overlay_payload(overlay, index)
        self.assertEqual(caught.exception.code, "overlay_prohibited_fields")

    def test_selected_overlay_requires_operator_reason(self):
        index = build_selection_index_payload(
            _candidate_preview(usable=[_candidate(market_id="usable-1")]),
            FIXTURE_SOURCE_PATH,
        )
        overlay = build_overlay_template(index)
        overlay["selections"][0]["selected_for_research_stub"] = True

        with self.assertRaises(OperatorSelectionPackError) as caught:
            validate_overlay_payload(overlay, index)
        self.assertEqual(caught.exception.code, "overlay_selected_reason_required")

    def test_output_json_is_deterministic(self):
        preview = _candidate_preview(usable=[_candidate(market_id="deterministic-1")])
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            input_path = temp_root / "candidate_intake.json"
            output_index = temp_root / "selection_index.json"
            output_overlay = temp_root / "selection_overlay.json"
            output_md = temp_root / "selection_pack.md"
            _write_json(input_path, preview)

            write_selection_pack_artifacts(input_path, output_md, output_index, output_overlay)
            first_index_text = output_index.read_text(encoding="utf-8")
            first_overlay_text = output_overlay.read_text(encoding="utf-8")
            write_selection_pack_artifacts(input_path, output_md, output_index, output_overlay)

            self.assertEqual(first_index_text, output_index.read_text(encoding="utf-8"))
            self.assertEqual(first_overlay_text, output_overlay.read_text(encoding="utf-8"))

    def test_markdown_report_has_stable_summary_counts(self):
        index = build_selection_index(ACTUAL_CANDIDATE_PREVIEW)
        markdown = render_markdown_pack(index)

        self.assertIn(
            "- source_candidate_intake_preview_path: `pm_bot/ingest/candidate_intake_preview.v1.json`",
            markdown,
        )
        self.assertIn("- usable_candidates_seen: 50", markdown)
        self.assertIn("- candidates_exported: 50", markdown)
        self.assertIn("- selection_overlay_template_created: true", markdown)
        self.assertIn("- research_packets_created: 0", markdown)

    def test_no_runtime_or_downstream_wiring_references_selection_pack(self):
        runtime_roots = [
            ROOT / "codex_auto",
            ROOT / "config",
            ROOT / "scripts",
            ROOT / "tasks",
            ROOT / "pm_bot" / "paper",
            ROOT / "pm_bot" / "research",
            ROOT / "pm_bot" / "scoring",
            ROOT / "pm_bot" / "signals",
        ]
        targets = (
            "export_operator_candidate_selection_pack",
            "operator_candidate_selection_index",
            "operator_candidate_selection_overlay",
            "operator_candidate_selection_pack",
        )
        allowed_inert_bridge_paths = {
            "pm_bot/research/build_selected_ingest_research_packet_stubs.py",
            "pm_bot/research/expected_selected_ingest_research_packet_stubs.v1.json",
            "pm_bot/research/selected_ingest_research_packet_stubs.v1.json",
            "pm_bot/research/selected_ingest_research_packet_stubs.v1.md",
            "pm_bot/research/tests/test_selected_ingest_research_packet_stubs.py",
        }
        matches = []
        for runtime_root in runtime_roots:
            if not runtime_root.exists():
                continue
            for path in runtime_root.rglob("*"):
                if path.suffix.lower() not in {".json", ".md", ".ps1", ".py", ".txt", ".yaml", ".yml"}:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                if any(target in text for target in targets):
                    relative_path = str(path.relative_to(ROOT)).replace("\\", "/")
                    if relative_path not in allowed_inert_bridge_paths:
                        matches.append(relative_path)
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
