import copy
import json
import tempfile
import unittest
from pathlib import Path

from pm_bot.ingest.capture_polymarket_readonly_snapshot import raw_payload_hash
from pm_bot.ingest.normalize_polymarket_raw_snapshot_preview import (
    RECORD_FIELDS,
    NormalizationPreviewError,
    build_normalized_preview,
    render_markdown_report,
    write_preview_artifacts,
)


ROOT = Path(__file__).resolve().parents[3]
EVENTS_FIXTURE = ROOT / "pm_bot" / "ingest" / "polymarket_events_raw_snapshot_fixture.v1.json"
MARKETS_FIXTURE = ROOT / "pm_bot" / "ingest" / "polymarket_raw_snapshot_fixture.v1.json"
EXPECTED = ROOT / "pm_bot" / "ingest" / "expected_normalized_market_preview.v1.json"


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def _iter_keys(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            yield str(key)
            yield from _iter_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_keys(item)


class PolymarketRawSnapshotNormalizationPreviewTests(unittest.TestCase):
    def test_events_with_nested_markets_fixture_normalizes_against_expected(self):
        preview = build_normalized_preview(EVENTS_FIXTURE)
        expected = _load_json(EXPECTED)
        self.assertEqual(preview, expected)
        self.assertEqual(preview["summary"]["events_seen"], 1)
        self.assertEqual(preview["summary"]["nested_markets_seen"], 2)
        self.assertEqual(preview["summary"]["normalized_records_written"], 2)
        self.assertEqual(preview["summary"]["active_open_records"], 2)
        self.assertEqual(preview["summary"]["closed_records"], 0)
        self.assertEqual(preview["summary"]["parse_warning_count"], 0)

        for record in preview["records"]:
            self.assertEqual(tuple(record.keys()), RECORD_FIELDS)
            self.assertEqual(record["source_name"], "polymarket_gamma_events")
            self.assertEqual(record["event_id"], "2001")
            self.assertIsInstance(record["outcomes"], list)
            self.assertIsInstance(record["outcome_prices"], list)
            self.assertIsInstance(record["clob_token_ids"], list)

    def test_validation_report_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "snapshot.validation.json"
            _write_json(path, {"validation_passed": True})
            with self.assertRaises(NormalizationPreviewError) as caught:
                build_normalized_preview(path)
        self.assertEqual(caught.exception.code, "validation_report_input_rejected")

    def test_invalid_raw_snapshot_is_rejected(self):
        payload = _load_json(EVENTS_FIXTURE)
        payload.pop("raw_payload")
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid_snapshot.json"
            _write_json(path, payload)
            with self.assertRaises(NormalizationPreviewError) as caught:
                build_normalized_preview(path)
        self.assertEqual(caught.exception.code, "invalid_raw_snapshot")
        codes = {item["code"] for item in caught.exception.details["findings"]}
        self.assertIn("missing_required_field:raw_payload", codes)

    def test_unsupported_source_shape_is_rejected(self):
        with self.assertRaises(NormalizationPreviewError) as caught:
            build_normalized_preview(MARKETS_FIXTURE)
        self.assertEqual(caught.exception.code, "unsupported_source_shape")
        self.assertEqual(caught.exception.details["source_name"], "polymarket_gamma_markets")

    def test_json_string_fields_are_parsed_safely(self):
        payload = copy.deepcopy(_load_json(EVENTS_FIXTURE))
        first_market = payload["raw_payload"][0]["markets"][0]
        second_market = payload["raw_payload"][0]["markets"][1]
        first_market["outcomePrices"] = "[\"0.11\", \"0.89\"]"
        first_market["clobTokenIds"] = "[\"token-yes\", \"token-no\"]"
        second_market["outcomePrices"] = "not-json"
        second_market["clobTokenIds"] = "{\"not\":\"a-list\"}"
        payload["raw_payload_sha256"] = raw_payload_hash(payload["raw_payload"])

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "parse_warning_snapshot.json"
            _write_json(path, payload)
            preview = build_normalized_preview(path)

        records = {record["market_id"]: record for record in preview["records"]}
        self.assertEqual(records["3001"]["outcome_prices"], ["0.11", "0.89"])
        self.assertEqual(records["3001"]["clob_token_ids"], ["token-yes", "token-no"])
        self.assertEqual(records["3002"]["outcome_prices"], [])
        self.assertEqual(records["3002"]["clob_token_ids"], [])
        self.assertEqual(preview["summary"]["parse_warning_count"], 2)
        self.assertEqual(
            [(item["code"], item["field"], item["event_index"], item["market_index"]) for item in preview["parse_warnings"]],
            [
                ("json_value_not_list", "clobTokenIds", 0, 1),
                ("json_list_parse_failed", "outcomePrices", 0, 1),
            ],
        )

    def test_parse_warnings_are_deterministic(self):
        payload = copy.deepcopy(_load_json(EVENTS_FIXTURE))
        payload["raw_payload"][0]["markets"][0]["outcomes"] = "{\"not\":\"a-list\"}"
        payload["raw_payload"][0]["markets"][1]["outcomePrices"] = ""
        payload["raw_payload_sha256"] = raw_payload_hash(payload["raw_payload"])

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "deterministic_warnings_snapshot.json"
            _write_json(path, payload)
            first = build_normalized_preview(path)
            second = build_normalized_preview(path)

        self.assertEqual(first["parse_warnings"], second["parse_warnings"])
        self.assertEqual(
            [(item["code"], item["field"], item["market_index"]) for item in first["parse_warnings"]],
            [
                ("json_value_not_list", "outcomes", 0),
                ("json_string_empty", "outcomePrices", 1),
            ],
        )

    def test_no_recommendation_score_probability_ev_side_order_or_trade_fields_exist(self):
        preview = build_normalized_preview(EVENTS_FIXTURE)
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
        allowed_order_fields = {"accepting_orders", "enable_order_book"}
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
            first_json = temp_root / "first.json"
            second_json = temp_root / "second.json"
            write_preview_artifacts(EVENTS_FIXTURE, first_json, temp_root / "first.md")
            write_preview_artifacts(EVENTS_FIXTURE, second_json, temp_root / "second.md")
            self.assertEqual(first_json.read_text(encoding="utf-8"), second_json.read_text(encoding="utf-8"))

    def test_markdown_report_has_stable_summary_counts(self):
        markdown = render_markdown_report(build_normalized_preview(EVENTS_FIXTURE))
        self.assertIn("- source_snapshot_path: `pm_bot/ingest/polymarket_events_raw_snapshot_fixture.v1.json`", markdown)
        self.assertIn("- source_name: `polymarket_gamma_events`", markdown)
        self.assertIn("- events_seen: 1", markdown)
        self.assertIn("- nested_markets_seen: 2", markdown)
        self.assertIn("- normalized_records_written: 2", markdown)
        self.assertIn("- active_open_records: 2", markdown)
        self.assertIn("- closed_records: 0", markdown)
        self.assertIn("- parse_warning_count: 0", markdown)
        self.assertIn("- none", markdown)

    def test_no_runtime_or_downstream_wiring_references_preview_script(self):
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
        targets = ("normalize_polymarket_raw_snapshot_preview", "normalized_market_preview")
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
