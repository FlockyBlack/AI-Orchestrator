import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pm_bot.ingest.validate_polymarket_raw_snapshot import (
    FORBIDDEN_KEYS,
    build_report_for_payload,
    validate_snapshot,
)


ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "pm_bot" / "ingest" / "validate_polymarket_raw_snapshot.py"
FIXTURE = ROOT / "pm_bot" / "ingest" / "polymarket_raw_snapshot_fixture.v1.json"
EXPECTED = ROOT / "pm_bot" / "ingest" / "expected_polymarket_raw_snapshot_validation.v1.json"
EVENTS_FIXTURE = ROOT / "pm_bot" / "ingest" / "polymarket_events_raw_snapshot_fixture.v1.json"
EVENTS_EXPECTED = ROOT / "pm_bot" / "ingest" / "expected_polymarket_events_raw_snapshot_validation.v1.json"


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_keys(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            yield str(key)
            yield from _iter_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_keys(item)


def _run_validator(*args, check=True):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=check,
    )


class PolymarketRawSnapshotValidationTests(unittest.TestCase):
    def test_fixture_validates_against_expected_report(self):
        result = _run_validator(str(FIXTURE))
        payload = json.loads(result.stdout)
        expected = _load_json(EXPECTED)
        self.assertEqual(payload, expected)

    def test_events_fixture_validates_against_expected_report(self):
        result = _run_validator(str(EVENTS_FIXTURE))
        payload = json.loads(result.stdout)
        expected = _load_json(EVENTS_EXPECTED)
        self.assertEqual(payload, expected)

    def test_validate_snapshot_accepts_fixture(self):
        payload = _load_json(FIXTURE)
        self.assertEqual(validate_snapshot(payload, "fixture"), [])

    def test_validate_snapshot_accepts_events_fixture(self):
        payload = _load_json(EVENTS_FIXTURE)
        self.assertEqual(validate_snapshot(payload, "events_fixture"), [])
        self.assertEqual(payload["normalized_summary"]["events_count"], 1)
        self.assertEqual(payload["normalized_summary"]["nested_markets_count"], 2)
        self.assertEqual(payload["normalized_summary"]["active_open_nested_markets_count"], 2)

    def test_missing_required_field_is_quarantined(self):
        payload = _load_json(FIXTURE)
        payload.pop("raw_payload")
        report = build_report_for_payload(payload, "bad.json")
        codes = {item["code"] for item in report["findings"]}
        self.assertFalse(report["validation_passed"])
        self.assertTrue(report["quarantine_required"])
        self.assertFalse(report["downstream_feed_allowed"])
        self.assertIn("missing_required_field:raw_payload", codes)
        self.assertIn("raw_payload_bad_type", codes)

    def test_unsafe_network_boundary_is_rejected(self):
        payload = _load_json(FIXTURE)
        payload["network_boundary"]["authenticated_endpoints_used"] = True
        findings = validate_snapshot(payload, "bad.json")
        codes = {item["code"] for item in findings}
        self.assertIn("unsafe_network_boundary:authenticated_endpoints_used", codes)

    def test_prohibited_key_is_rejected(self):
        payload = _load_json(FIXTURE)
        payload["raw_payload"][0]["api_key"] = "not-real"
        findings = validate_snapshot(payload, "bad.json")
        codes = {item["code"] for item in findings}
        self.assertIn("prohibited_key_seen", codes)

    def test_supported_fixtures_emit_no_prohibited_trading_auth_or_wallet_fields(self):
        for fixture_path in (FIXTURE, EVENTS_FIXTURE):
            payload = _load_json(fixture_path)
            seen = {key.lower() for key in _iter_keys(payload)}
            self.assertFalse(seen & FORBIDDEN_KEYS)

    def test_events_without_nested_markets_are_rejected(self):
        payload = _load_json(EVENTS_FIXTURE)
        payload["raw_payload"][0]["markets"] = []
        payload["raw_payload_sha256"] = "invalid-for-test"
        findings = validate_snapshot(payload, "bad_events.json")
        codes = {item["code"] for item in findings}
        self.assertIn("raw_payload_no_nested_markets", codes)
        self.assertIn("raw_payload_no_active_open_nested_markets", codes)

    def test_write_report_uses_requested_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "validation.json"
            result = _run_validator(str(FIXTURE), "--write-report", str(output_path))
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.returncode, 0)
            payload = _load_json(output_path)
            self.assertTrue(payload["validation_passed"])


if __name__ == "__main__":
    unittest.main()
