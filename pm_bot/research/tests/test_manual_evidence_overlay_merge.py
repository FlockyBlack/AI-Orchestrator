import ast
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
MERGER = ROOT / "pm_bot" / "research" / "merge_manual_evidence_overlay.py"
VALIDATOR = ROOT / "pm_bot" / "research" / "validate_manual_research_packets.py"
STUBS = ROOT / "pm_bot" / "research" / "expected_research_packet_stubs.v1.json"
OVERLAY = ROOT / "pm_bot" / "research" / "manual_evidence_overlay_fixture.v1.json"
MERGED = ROOT / "pm_bot" / "research" / "merged_manual_research_packets.v1.json"
EXPECTED_MERGED = ROOT / "pm_bot" / "research" / "expected_merged_manual_research_packets.v1.json"
EXPECTED_REPORT = ROOT / "pm_bot" / "research" / "expected_manual_evidence_overlay_merge_report.v1.json"


def _run_merger(*extra_args):
    return subprocess.run(
        [sys.executable, str(MERGER), *extra_args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _run_validator(*extra_args):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *extra_args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _load_module(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _packet_by_market_id(payload, market_id):
    for packet in payload["packets"]:
        if packet["market_id"] == market_id:
            return packet
    raise AssertionError(f"missing packet {market_id}")


def _stub_by_market_id(market_id):
    for packet in _load_json(STUBS)["packet_stubs"]:
        if packet["market_id"] == market_id:
            return packet
    raise AssertionError(f"missing stub {market_id}")


def _codes(errors):
    return {item["code"] for item in errors}


class ManualEvidenceOverlayMergeTests(unittest.TestCase):
    def test_default_merge_matches_expected_packets_and_report(self):
        module = _load_module(MERGER, "manual_evidence_overlay_merger")
        merged_payload, report = module.build_merge_artifacts()

        self.assertEqual(merged_payload, _load_json(EXPECTED_MERGED))
        self.assertEqual(report, _load_json(EXPECTED_REPORT))
        self.assertEqual(report["overlays_read"], 5)
        self.assertEqual(report["overlays_accepted"], 2)
        self.assertEqual(report["overlays_rejected"], 3)
        self.assertTrue(report["merged_packets_validation_passed"])

    def test_valid_overlays_merge_into_expected_manual_fields(self):
        merged_payload = _load_json(EXPECTED_MERGED)
        partial = _packet_by_market_id(merged_payload, "569366")
        ready = _packet_by_market_id(merged_payload, "563650")

        self.assertEqual(partial["completion_status"], "needs_more_information")
        self.assertEqual(partial["official_sources_checked"], ["offline-check:569366:market-rules", "offline-check:569366:election-authority"])
        self.assertEqual(partial["credible_news_sources_checked"], ["offline-check:569366:reuters-query"])
        self.assertEqual(len(partial["evidence_slots"]["official_resolution_criteria"]), 1)
        self.assertTrue(partial["missing_information"])

        self.assertEqual(ready["completion_status"], "ready_for_operator_review")
        self.assertEqual(ready["missing_information"], [])
        self.assertEqual(len(ready["evidence_slots"]["official_resolution_criteria"]), 1)
        self.assertEqual(len(ready["evidence_slots"]["official_yes_evidence"]), 1)
        self.assertEqual(len(ready["evidence_slots"]["credible_news_yes_evidence"]), 1)
        self.assertEqual(len(ready["evidence_slots"]["source_reliability_notes"]), 1)

    def test_immutable_stub_fields_are_preserved_for_accepted_and_rejected_overlays(self):
        module = _load_module(MERGER, "manual_evidence_overlay_merger")
        immutable_fields = module.IMMUTABLE_STUB_FIELDS
        merged_payload = _load_json(EXPECTED_MERGED)

        for market_id in ("569366", "563650", "569368", "569343"):
            packet = _packet_by_market_id(merged_payload, market_id)
            stub = _stub_by_market_id(market_id)
            for field in immutable_fields:
                self.assertEqual(packet[field], stub[field], msg=f"{market_id}:{field}")

        rejected_title_packet = _packet_by_market_id(merged_payload, "569368")
        self.assertEqual(rejected_title_packet["title"], _stub_by_market_id("569368")["title"])
        self.assertEqual(rejected_title_packet["completion_status"], "stub_only")

    def test_unknown_market_id_overlay_is_rejected(self):
        report = _load_json(EXPECTED_REPORT)
        self.assertIn("unknown-market-id", report["rejected_market_ids"])
        self.assertEqual(_codes(report["errors_by_market_id"]["unknown-market-id"]), {"unknown_market_id"})

    def test_immutable_override_attempt_is_rejected(self):
        report = _load_json(EXPECTED_REPORT)
        self.assertIn("569368", report["rejected_market_ids"])
        self.assertEqual(_codes(report["errors_by_market_id"]["569368"]), {"immutable_field_override:title"})

    def test_prohibited_order_trade_wallet_execution_and_recommendation_fields_fail(self):
        report = _load_json(EXPECTED_REPORT)
        codes = _codes(report["errors_by_market_id"]["569343"])
        for field in ("order", "trade", "wallet", "execution", "recommendation"):
            self.assertIn(f"prohibited_overlay_field:{field}", codes)
            self.assertIn(f"unexpected_overlay_field:{field}", codes)
        self.assertEqual(_packet_by_market_id(_load_json(EXPECTED_MERGED), "569343")["completion_status"], "stub_only")

    def test_overlay_with_structurally_invalid_ready_status_is_rejected_by_validator_contract(self):
        module = _load_module(MERGER, "manual_evidence_overlay_merger")
        payload = copy.deepcopy(_load_json(OVERLAY))
        payload["overlays"] = [
            {
                "market_id": "569334",
                "completion_status": "ready_for_operator_review",
                "missing_information": [],
                "operator_notes": "Missing required evidence slots for ready status.",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            overlay_path = temp_path / "overlay.json"
            overlay_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            merged_payload, report = module.build_merge_artifacts(overlay_path=overlay_path, output_path=temp_path / "merged.json")

        self.assertEqual(report["overlays_accepted"], 0)
        self.assertEqual(report["overlays_rejected"], 1)
        self.assertIn("merged_packet_failed_validator", _codes(report["errors_by_market_id"]["569334"]))
        self.assertEqual(_packet_by_market_id(merged_payload, "569334")["completion_status"], "stub_only")

    def test_merged_packets_pass_existing_validator(self):
        result = _run_validator("--packets", str(MERGED))
        self.assertEqual(result.returncode, 0)
        report = json.loads(result.stdout)
        self.assertEqual(report["total_packets_checked"], 10)
        self.assertEqual(report["invalid_packets"], 0)
        self.assertEqual(report["ready_for_operator_review"], 1)
        self.assertEqual(report["needs_more_information"], 1)

    def test_cli_outputs_are_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_path = temp_path / "merged.json"
            expected_path = temp_path / "expected.json"
            report_path = temp_path / "report.json"
            args = [
                "--output",
                str(output_path),
                "--expected-output",
                str(expected_path),
                "--report-output",
                str(report_path),
            ]
            first = _run_merger(*args)
            first_merged = output_path.read_text(encoding="utf-8")
            first_expected = expected_path.read_text(encoding="utf-8")
            first_report = report_path.read_text(encoding="utf-8")
            second = _run_merger(*args)

            self.assertEqual(first.returncode, 0)
            self.assertEqual(second.returncode, 0)
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(first_merged, output_path.read_text(encoding="utf-8"))
            self.assertEqual(first_expected, expected_path.read_text(encoding="utf-8"))
            self.assertEqual(first_report, report_path.read_text(encoding="utf-8"))
            self.assertEqual(json.loads(first_merged), json.loads(first_expected))

    def test_keyed_overlay_payload_is_supported(self):
        module = _load_module(MERGER, "manual_evidence_overlay_merger")
        payload = {
            "schema_version": "keyed-overlay-test.v1",
            "569333": {
                "completion_status": "manual_evidence_added",
                "evidence_slots": {
                    "official_resolution_criteria": [
                        {
                            "source_name": "Manual keyed overlay source",
                            "source_type": "official_resolution_criteria",
                            "source_url_or_reference": "offline-reference:569333:keyed",
                            "captured_claim": "Manual keyed overlay records one structural evidence item.",
                            "relevance_to_resolution": "Shows keyed overlay parsing without resolving the market.",
                            "operator_notes": "Used only for deterministic parser coverage."
                        }
                    ]
                },
                "operator_notes": "Keyed overlay accepted."
            }
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            overlay_path = temp_path / "keyed_overlay.json"
            overlay_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            merged_payload, report = module.build_merge_artifacts(overlay_path=overlay_path, output_path=temp_path / "merged.json")

        self.assertEqual(report["overlays_read"], 1)
        self.assertEqual(report["overlays_accepted"], 1)
        self.assertEqual(report["overlays_rejected"], 0)
        self.assertEqual(_packet_by_market_id(merged_payload, "569333")["completion_status"], "manual_evidence_added")

    def test_merger_uses_standard_library_only(self):
        tree = ast.parse(MERGER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "copy", "importlib", "json", "pathlib", "sys"})

    def test_merger_has_no_live_fetcher_or_runtime_imports(self):
        source = MERGER.read_text(encoding="utf-8").lower()
        forbidden = [
            "requests",
            "urllib.request",
            "httpx",
            "aiohttp",
            "socket",
            "websocket",
            "py_clob_client",
            "gamma-api",
            "submit_order",
            "execute_trade",
        ]
        for term in forbidden:
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()
