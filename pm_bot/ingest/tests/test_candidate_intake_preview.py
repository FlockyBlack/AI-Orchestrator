import json
import tempfile
import unittest
from pathlib import Path

from pm_bot.ingest.build_candidate_intake_preview import (
    BUCKETS,
    ITEM_FIELDS,
    CandidateIntakePreviewError,
    build_candidate_intake_preview,
    render_markdown_report,
    write_preview_artifacts,
)


ROOT = Path(__file__).resolve().parents[3]
EVENTS_RAW_FIXTURE = ROOT / "pm_bot" / "ingest" / "polymarket_events_raw_snapshot_fixture.v1.json"
EXPECTED_NORMALIZED = ROOT / "pm_bot" / "ingest" / "expected_normalized_market_preview.v1.json"
EXPECTED_CANDIDATE = ROOT / "pm_bot" / "ingest" / "expected_candidate_intake_preview.v1.json"


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _normalized_payload(records):
    return {
        "artifact_type": "polymarket_normalized_market_preview",
        "records": records,
        "schema_version": "normalized_market_preview.v1",
        "summary": {"normalized_records_written": len(records)},
    }


def _record(**overrides):
    record = {
        "accepting_orders": True,
        "active": True,
        "category_or_tags": ["fixture"],
        "closed": False,
        "description": "Resolution criteria text for structural fixture only.",
        "end_date": "2026-12-31T00:00:00Z",
        "event_id": "event-1",
        "event_title": "Fixture event",
        "liquidity": 10.0,
        "market_id": "market-1",
        "outcome_prices": ["0.25", "0.75"],
        "outcomes": ["Yes", "No"],
        "question": "Will the fixture condition occur?",
        "volume": None,
    }
    record.update(overrides)
    return record


def _build_from_records(records):
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "normalized.json"
        _write_json(path, _normalized_payload(records))
        return build_candidate_intake_preview(path)


def _iter_keys(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            yield str(key)
            yield from _iter_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_keys(item)


class CandidateIntakePreviewTests(unittest.TestCase):
    def test_normalized_preview_input_is_accepted_against_expected_fixture(self):
        preview = build_candidate_intake_preview(EXPECTED_NORMALIZED)
        expected = _load_json(EXPECTED_CANDIDATE)
        self.assertEqual(preview, expected)
        self.assertEqual(preview["summary"]["normalized_records_read"], 2)
        self.assertEqual(preview["summary"]["missing_required_fields"], 2)
        for bucket in BUCKETS:
            for item in preview["buckets"][bucket]:
                self.assertEqual(tuple(item.keys()), ITEM_FIELDS)
                self.assertEqual(item["bucket"], bucket)

    def test_raw_snapshot_input_is_rejected(self):
        with self.assertRaises(CandidateIntakePreviewError) as caught:
            build_candidate_intake_preview(EVENTS_RAW_FIXTURE)
        self.assertEqual(caught.exception.code, "raw_snapshot_input_rejected")

    def test_validation_report_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "normalized.validation.json"
            _write_json(path, _normalized_payload([]))
            with self.assertRaises(CandidateIntakePreviewError) as caught:
                build_candidate_intake_preview(path)
        self.assertEqual(caught.exception.code, "validation_report_input_rejected")

    def test_usable_bucket_is_assigned_only_from_structure(self):
        high_volume = _record(
            market_id="market-b",
            liquidity=100000.0,
            outcome_prices=["0.99", "0.01"],
            question="Will fixture B resolve?",
            volume=500000.0,
        )
        low_volume = _record(
            market_id="market-a",
            liquidity=1.0,
            outcome_prices=["0.01", "0.99"],
            question="Will fixture A resolve?",
            volume=2.0,
        )
        preview = _build_from_records([high_volume, low_volume])

        usable = preview["buckets"]["usable_for_research_preview"]
        self.assertEqual([item["market_id"] for item in usable], ["market-a", "market-b"])
        self.assertEqual(preview["summary"]["usable_for_research_preview"], 2)
        self.assertEqual(preview["summary"]["missing_required_fields"], 0)
        self.assertEqual(preview["summary"]["closed_or_not_accepting"], 0)
        for item in usable:
            self.assertEqual(item["next_manual_action"], "eligible_for_manual_research_packet_preview")
            self.assertEqual(item["structural_findings"], [])

    def test_closed_records_are_not_marked_usable(self):
        preview = _build_from_records(
            [
                _record(
                    accepting_orders=False,
                    closed=True,
                    market_id="closed-1",
                    question="Will closed fixture resolve?",
                )
            ]
        )
        self.assertEqual(preview["summary"]["usable_for_research_preview"], 0)
        self.assertEqual(preview["summary"]["closed_or_not_accepting"], 1)
        closed_item = preview["buckets"]["closed_or_not_accepting"][0]
        self.assertEqual(closed_item["bucket"], "closed_or_not_accepting")
        self.assertEqual(closed_item["structural_findings"], ["closed", "not_accepting_orders"])
        self.assertEqual(closed_item["next_manual_action"], "skip_closed_or_not_accepting")

    def test_missing_required_fields_are_reported_deterministically(self):
        incomplete = _record(
            description="",
            end_date=None,
            event_id="",
            event_title="",
            liquidity=None,
            market_id="",
            outcome_prices=["0.2"],
            question="",
            volume=None,
        )
        preview = _build_from_records([incomplete])
        missing = preview["buckets"]["missing_required_fields"][0]
        self.assertEqual(missing["bucket"], "missing_required_fields")
        self.assertEqual(
            missing["structural_findings"],
            [
                "outcome_prices_count_mismatch",
                "missing_market_id",
                "missing_question",
                "missing_event_title_or_event_id",
                "missing_end_date",
                "missing_liquidity_or_volume",
                "missing_description_or_resolution_criteria",
            ],
        )
        self.assertEqual(missing["next_manual_action"], "fix_or_inspect_missing_fields")

    def test_unsupported_and_watch_only_structures_are_bucketed(self):
        malformed = _record(active="true", market_id="malformed-1")
        watch_only = _record(accepting_orders=None, market_id="watch-1")
        preview = _build_from_records([malformed, watch_only])

        self.assertEqual(preview["summary"]["unsupported_or_malformed"], 1)
        self.assertEqual(preview["summary"]["watch_only_structure"], 1)
        self.assertEqual(
            preview["buckets"]["unsupported_or_malformed"][0]["structural_findings"],
            ["malformed_active"],
        )
        self.assertEqual(
            preview["buckets"]["watch_only_structure"][0]["structural_findings"],
            ["accepting_orders_unknown"],
        )

    def test_no_ranking_scoring_recommendation_probability_ev_side_order_or_trade_fields_exist(self):
        preview = build_candidate_intake_preview(EXPECTED_NORMALIZED)
        forbidden_exact = {
            "decision",
            "edge",
            "ev",
            "expected_value",
            "market_decision",
            "order",
            "orders",
            "probability",
            "recommendation",
            "score",
            "side",
            "signal",
            "trade",
            "trading",
        }
        allowed_order_fields = {"accepting_orders"}
        for key in _iter_keys(preview):
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

    def test_output_json_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            input_path = temp_root / "normalized.json"
            first_json = temp_root / "first.json"
            second_json = temp_root / "second.json"
            _write_json(input_path, _normalized_payload([_record(market_id="deterministic-1")]))
            write_preview_artifacts(input_path, first_json, temp_root / "first.md")
            write_preview_artifacts(input_path, second_json, temp_root / "second.md")
            self.assertEqual(first_json.read_text(encoding="utf-8"), second_json.read_text(encoding="utf-8"))

    def test_markdown_report_has_stable_summary_counts(self):
        preview = build_candidate_intake_preview(EXPECTED_NORMALIZED)
        markdown = render_markdown_report(preview)
        self.assertIn(
            "- source_normalized_preview_path: `pm_bot/ingest/expected_normalized_market_preview.v1.json`",
            markdown,
        )
        self.assertIn("- normalized_records_read: 2", markdown)
        self.assertIn("- usable_for_research_preview: 0", markdown)
        self.assertIn("- missing_required_fields: 2", markdown)
        self.assertIn("- closed_or_not_accepting: 0", markdown)
        self.assertIn("- unsupported_or_malformed: 0", markdown)
        self.assertIn("- watch_only_structure: 0", markdown)

    def test_no_runtime_or_downstream_wiring_references_candidate_preview(self):
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
        targets = ("build_candidate_intake_preview", "candidate_intake_preview")
        matches = []
        for runtime_root in runtime_roots:
            if not runtime_root.exists():
                continue
            for path in runtime_root.rglob("*"):
                if path.suffix.lower() not in {".json", ".md", ".ps1", ".py", ".txt", ".yaml", ".yml"}:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
                if any(target in text for target in targets):
                    matches.append(str(path.relative_to(ROOT)).replace("\\", "/"))
        self.assertEqual(matches, [])


if __name__ == "__main__":
    unittest.main()
