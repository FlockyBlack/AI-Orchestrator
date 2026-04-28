import json
import tempfile
import unittest
from pathlib import Path

from pm_bot.ingest.capture_polymarket_readonly_snapshot import (
    build_query,
    capture_polymarket_snapshot,
    raw_payload_hash,
)
from pm_bot.ingest.validate_polymarket_raw_snapshot import FORBIDDEN_KEYS


ROOT = Path(__file__).resolve().parents[3]
MARKETS_FIXTURE = ROOT / "pm_bot" / "ingest" / "polymarket_raw_snapshot_fixture.v1.json"
EVENTS_FIXTURE = ROOT / "pm_bot" / "ingest" / "polymarket_events_raw_snapshot_fixture.v1.json"


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


class PolymarketReadonlySnapshotCaptureTests(unittest.TestCase):
    def test_build_query_is_conservative_and_readonly(self):
        self.assertEqual(build_query(2), {"active": "true", "closed": "false", "limit": "2"})
        self.assertEqual(build_query(500)["limit"], "100")
        self.assertEqual(build_query(0)["limit"], "1")

    def test_capture_defaults_to_events_and_writes_valid_artifact(self):
        fixture = _load_json(EVENTS_FIXTURE)
        calls = []

        def fake_fetch(url, timeout_seconds):
            calls.append({"timeout_seconds": timeout_seconds, "url": url})
            return fixture["raw_payload"]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            result = capture_polymarket_snapshot(
                limit=2,
                output_dir=temp_root / "raw_snapshots",
                quarantine_dir=temp_root / "quarantine",
                timeout_seconds=7,
                fetch_json_func=fake_fetch,
                now_func=lambda: fixture["fetched_at"],
            )

            self.assertTrue(result["validation_passed"])
            self.assertEqual(result["source"], "polymarket_gamma_events")
            self.assertEqual(result["events_count"], 1)
            self.assertEqual(result["nested_markets_count"], 2)
            self.assertEqual(result["active_open_nested_markets_count"], 2)
            self.assertIsNone(result["quarantine_path"])
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0]["timeout_seconds"], 7)
            self.assertIn("/events?", calls[0]["url"])
            self.assertIn("active=true", calls[0]["url"])
            self.assertIn("closed=false", calls[0]["url"])
            self.assertIn("limit=2", calls[0]["url"])

            artifact_path = Path(result["artifact_path"])
            self.assertTrue(artifact_path.exists())
            self.assertTrue(str(artifact_path).endswith(".json"))
            self.assertEqual(artifact_path.parent.name, "raw_snapshots")
            self.assertFalse((temp_root / "quarantine").exists())

            payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["raw_payload"], fixture["raw_payload"])
            self.assertEqual(payload["raw_payload_sha256"], raw_payload_hash(fixture["raw_payload"]))
            self.assertEqual(payload["normalized_summary"], fixture["normalized_summary"])
            self.assertEqual(payload["source"]["name"], "polymarket_gamma_events")
            self.assertEqual(payload["source"]["source_url"], payload["source"]["url"])
            self.assertTrue(payload["validation"]["passed"])
            self.assertFalse({key.lower() for key in _iter_keys(payload)} & FORBIDDEN_KEYS)

            report_path = Path(result["report_path"])
            self.assertTrue(report_path.exists())
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertTrue(report["validation_passed"])
            self.assertFalse(report["downstream_feed_allowed"])

    def test_capture_preserves_explicit_markets_path(self):
        fixture = _load_json(MARKETS_FIXTURE)
        calls = []

        def fake_fetch(url, timeout_seconds):
            calls.append({"timeout_seconds": timeout_seconds, "url": url})
            return fixture["raw_payload"]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            result = capture_polymarket_snapshot(
                limit=2,
                output_dir=temp_root / "raw_snapshots",
                quarantine_dir=temp_root / "quarantine",
                fetch_json_func=fake_fetch,
                now_func=lambda: fixture["fetched_at"],
                source="markets",
            )

            self.assertTrue(result["validation_passed"])
            self.assertEqual(result["source"], "polymarket_gamma_markets")
            self.assertEqual(result["market_count"], 2)
            self.assertEqual(len(calls), 1)
            self.assertIn("/markets?", calls[0]["url"])

            payload = json.loads(Path(result["artifact_path"]).read_text(encoding="utf-8"))
            self.assertEqual(payload["raw_payload"], fixture["raw_payload"])
            self.assertEqual(payload["normalized_summary"], fixture["normalized_summary"])
            self.assertEqual(payload["source"]["name"], "polymarket_gamma_markets")

    def test_capture_quarantines_missing_market_fields(self):
        def fake_fetch(url, timeout_seconds):
            return [{"id": "", "active": True, "closed": False, "outcomes": []}]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            result = capture_polymarket_snapshot(
                limit=1,
                output_dir=temp_root / "raw_snapshots",
                quarantine_dir=temp_root / "quarantine",
                fetch_json_func=fake_fetch,
                now_func=lambda: "2026-04-28T00:00:00Z",
                source="markets",
            )

            self.assertFalse(result["validation_passed"])
            self.assertIsNotNone(result["quarantine_path"])
            quarantine_path = Path(result["quarantine_path"])
            self.assertEqual(quarantine_path.parent.name, "quarantine")
            self.assertTrue(quarantine_path.exists())
            payload = json.loads(quarantine_path.read_text(encoding="utf-8"))
            codes = {item["code"] for item in payload["validation"]["findings"]}
            self.assertIn("summary_market_missing_id:0", codes)
            self.assertIn("summary_market_missing_question:0", codes)
            self.assertIn("summary_market_bad_outcome_count:0", codes)

    def test_fetch_failure_does_not_write_artifacts(self):
        def fake_fetch(url, timeout_seconds):
            raise RuntimeError("public read-only market data fetch failed: timed out")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            with self.assertRaisesRegex(RuntimeError, "timed out"):
                capture_polymarket_snapshot(
                    limit=1,
                    output_dir=temp_root / "raw_snapshots",
                    quarantine_dir=temp_root / "quarantine",
                    fetch_json_func=fake_fetch,
                    now_func=lambda: "2026-04-28T00:00:00Z",
                )

            self.assertFalse((temp_root / "raw_snapshots").exists())
            self.assertFalse((temp_root / "quarantine").exists())

    def test_no_runtime_wiring_references_capture_script(self):
        runtime_roots = [
            ROOT / "codex_auto",
            ROOT / "config",
            ROOT / "scripts",
            ROOT / "tasks",
        ]
        targets = ("capture_polymarket_readonly_snapshot", "capture_polymarket_snapshot")
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

    def test_tests_do_not_need_live_network(self):
        markets_fixture = _load_json(MARKETS_FIXTURE)
        events_fixture = _load_json(EVENTS_FIXTURE)
        self.assertEqual(markets_fixture["source"]["name"], "polymarket_gamma_markets")
        self.assertEqual(events_fixture["source"]["name"], "polymarket_gamma_events")
        self.assertEqual(events_fixture["network_boundary"]["credentials_required"], False)
        self.assertEqual(events_fixture["network_boundary"]["authenticated_endpoints_used"], False)

if __name__ == "__main__":
    unittest.main()
