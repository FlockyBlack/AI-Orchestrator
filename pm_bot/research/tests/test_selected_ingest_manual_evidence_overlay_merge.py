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
MERGER = ROOT / "pm_bot" / "research" / "merge_selected_ingest_manual_evidence_overlay.py"
VALIDATOR = ROOT / "pm_bot" / "research" / "validate_manual_research_packets.py"
STUBS = ROOT / "pm_bot" / "research" / "selected_ingest_research_packet_stubs.v1.json"
OVERLAY = ROOT / "pm_bot" / "research" / "selected_ingest_manual_evidence_overlay_fixture.v1.json"
MERGED = ROOT / "pm_bot" / "research" / "selected_ingest_merged_manual_research_packets.v1.json"
EXPECTED_MERGED = ROOT / "pm_bot" / "research" / "expected_selected_ingest_merged_manual_research_packets.v1.json"
REPORT = ROOT / "pm_bot" / "research" / "selected_ingest_manual_evidence_overlay_merge_report.v1.md"

EXPECTED_SELECTED_MARKET_IDS = ["692258", "824952", "691547", "597964", "598936"]
PROHIBITED_OUTPUT_FIELD_NAMES = {
    "completed_dossier",
    "completed_dossiers",
    "dossier",
    "entry_price",
    "ev",
    "expected_value",
    "limit_price",
    "market_decision",
    "order",
    "orders",
    "paper_order",
    "paper_orders",
    "price_target",
    "probability",
    "recommendation",
    "recommendations",
    "score",
    "scores",
    "side",
    "signal",
    "trade",
    "trades",
    "wallet",
    "wallets",
    "yes_no_decision",
}


def _load_module(path=MERGER):
    spec = importlib.util.spec_from_file_location("selected_ingest_manual_evidence_overlay_merge", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


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


def _walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


class SelectedIngestManualEvidenceOverlayMergeTests(unittest.TestCase):
    def test_default_merge_matches_expected_packets_and_summary(self):
        module = _load_module()
        merged_payload, report = module.build_merge_artifacts()

        self.assertEqual(merged_payload, _load_json(EXPECTED_MERGED))
        self.assertEqual(merged_payload["selected_market_ids"], EXPECTED_SELECTED_MARKET_IDS)
        self.assertEqual(report["summary"]["overlays_read"], 5)
        self.assertEqual(report["summary"]["overlays_accepted"], 2)
        self.assertEqual(report["summary"]["overlays_rejected"], 3)
        self.assertEqual(report["summary"]["packets_written"], 5)
        self.assertTrue(report["merged_packets_validation_passed"])

    def test_valid_selected_overlays_merge_correctly(self):
        payload = _load_json(EXPECTED_MERGED)
        partial = _packet_by_market_id(payload, "692258")
        ready = _packet_by_market_id(payload, "824952")

        self.assertEqual(partial["completion_status"], "needs_more_information")
        self.assertEqual(partial["official_sources_checked"], ["offline-check:692258:local-market-rules", "offline-check:692258:company-source-placeholder"])
        self.assertEqual(partial["credible_news_sources_checked"], ["offline-check:692258:credible-news-query-placeholder"])
        self.assertEqual(len(partial["evidence_slots"]["official_resolution_criteria"]), 1)
        self.assertTrue(partial["missing_information"])

        self.assertEqual(ready["completion_status"], "ready_for_operator_review")
        self.assertEqual(ready["missing_information"], [])
        self.assertEqual(len(ready["evidence_slots"]["official_resolution_criteria"]), 1)
        self.assertEqual(len(ready["evidence_slots"]["official_yes_evidence"]), 1)
        self.assertEqual(len(ready["evidence_slots"]["credible_news_yes_evidence"]), 1)
        self.assertEqual(len(ready["evidence_slots"]["source_reliability_notes"]), 1)

    def test_evidence_is_copied_structurally_without_truth_inference(self):
        overlay_payload = _load_json(OVERLAY)
        merged_payload = _load_json(EXPECTED_MERGED)
        overlay_ready = next(item for item in overlay_payload["overlays"] if item["market_id"] == "824952")
        merged_ready = _packet_by_market_id(merged_payload, "824952")

        for slot_name, slot_items in overlay_ready["evidence_slots"].items():
            self.assertEqual(merged_ready["evidence_slots"][slot_name], slot_items)
        for slot_name, slot_items in merged_ready["evidence_slots"].items():
            if slot_name not in overlay_ready["evidence_slots"]:
                self.assertEqual(slot_items, [])
        for slot_items in merged_ready["evidence_slots"].values():
            for item in slot_items:
                self.assertEqual(set(item), set(_load_module().EVIDENCE_ITEM_FIELDS))
                self.assertIn("structural validation only", item["captured_claim"])
        self.assertNotIn("resolved_outcome", merged_ready)
        self.assertNotIn("truth_status", merged_ready)

    def test_unknown_market_id_overlay_is_rejected(self):
        report = _load_module().build_merge_artifacts()[1]

        self.assertIn("999999", report["rejected_market_ids"])
        self.assertEqual(_codes(report["summary"]["errors_by_market_id"]["999999"]), {"unknown_market_id"})

    def test_immutable_stub_field_override_is_rejected_and_stub_is_preserved(self):
        report = _load_module().build_merge_artifacts()[1]
        payload = _load_json(EXPECTED_MERGED)
        packet = _packet_by_market_id(payload, "691547")
        stub = _stub_by_market_id("691547")

        self.assertIn("691547", report["rejected_market_ids"])
        self.assertEqual(_codes(report["summary"]["errors_by_market_id"]["691547"]), {"immutable_field_override:title"})
        self.assertEqual(packet["title"], stub["title"])
        self.assertEqual(packet["completion_status"], "stub_only")

    def test_prohibited_trade_wallet_recommendation_probability_and_decision_fields_fail(self):
        report = _load_module().build_merge_artifacts()[1]
        codes = _codes(report["summary"]["errors_by_market_id"]["597964"])
        prohibited_fields = {
            "order",
            "trade",
            "wallet",
            "private_key",
            "execution",
            "recommendation",
            "bet",
            "stake",
            "size",
            "entry_price",
            "limit_price",
            "price_target",
            "score",
            "signal",
            "probability",
            "expected_value",
            "ev",
            "side",
            "yes_no_decision",
            "buy",
            "sell",
            "market_decision",
        }

        for field in prohibited_fields:
            self.assertIn(f"prohibited_overlay_field:{field}", codes)
            self.assertIn(f"unexpected_overlay_field:{field}", codes)
        self.assertEqual(_packet_by_market_id(_load_json(EXPECTED_MERGED), "597964")["completion_status"], "stub_only")

    def test_completion_status_rules_are_validator_backed(self):
        module = _load_module()
        payload = copy.deepcopy(_load_json(OVERLAY))
        payload["overlays"] = [
            {
                "market_id": "598936",
                "completion_status": "ready_for_operator_review",
                "missing_information": [],
                "operator_notes": "Ready status without required structured evidence must fail.",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            overlay_path = temp_path / "overlay.json"
            overlay_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            merged_payload, report = module.build_merge_artifacts(overlay_path=overlay_path, output_path=temp_path / "merged.json")

        self.assertEqual(report["summary"]["overlays_accepted"], 0)
        self.assertEqual(report["summary"]["overlays_rejected"], 1)
        self.assertIn("merged_packet_failed_validator", _codes(report["summary"]["errors_by_market_id"]["598936"]))
        self.assertEqual(_packet_by_market_id(merged_payload, "598936")["completion_status"], "stub_only")

    def test_merged_packets_pass_existing_manual_packet_validator(self):
        result = _run_validator("--packets", str(MERGED))

        self.assertEqual(result.returncode, 0)
        report = json.loads(result.stdout)
        self.assertEqual(report["total_packets_checked"], 5)
        self.assertEqual(report["invalid_packets"], 0)
        self.assertEqual(report["ready_for_operator_review"], 1)
        self.assertEqual(report["needs_more_information"], 1)

    def test_no_prohibited_decision_fields_exist_in_merged_packets(self):
        payload = _load_json(EXPECTED_MERGED)

        for key in _walk_keys(payload["packets"]):
            normalized = key.lower()
            self.assertNotIn(normalized, PROHIBITED_OUTPUT_FIELD_NAMES, msg=key)
            self.assertNotIn("expected_value", normalized, msg=key)
            self.assertNotIn("market_decision", normalized, msg=key)
            self.assertNotIn("probability", normalized, msg=key)
            self.assertNotIn("recommendation", normalized, msg=key)
            self.assertFalse(normalized.endswith("_score"), msg=key)

    def test_output_json_and_markdown_are_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_path = temp_path / "merged.json"
            expected_path = temp_path / "expected.json"
            report_path = temp_path / "report.md"
            args = [
                "--output",
                str(output_path),
                "--expected-output",
                str(expected_path),
                "--report-output",
                str(report_path),
            ]
            first = _run_merger(*args)
            first_output = output_path.read_text(encoding="utf-8")
            first_expected = expected_path.read_text(encoding="utf-8")
            first_report = report_path.read_text(encoding="utf-8")
            second = _run_merger(*args)

            self.assertEqual(first.returncode, 0)
            self.assertEqual(second.returncode, 0)
            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(first_output, output_path.read_text(encoding="utf-8"))
            self.assertEqual(first_expected, expected_path.read_text(encoding="utf-8"))
            self.assertEqual(first_report, report_path.read_text(encoding="utf-8"))
            self.assertEqual(json.loads(first_output), json.loads(first_expected))

    def test_markdown_report_has_stable_summary_counts(self):
        markdown = REPORT.read_text(encoding="utf-8")

        for heading in (
            "# Selected Ingest Manual Evidence Overlay Merge Report v1",
            "## Summary",
            "## Source Artifacts",
            "## Selected Market IDs",
            "## Errors By Market ID",
            "## Safety Boundary",
        ):
            self.assertIn(heading, markdown)
        for line in (
            "- overlays_read: 5",
            "- overlays_accepted: 2",
            "- overlays_rejected: 3",
            "- packets_written: 5",
            "- ready_for_operator_review: 1",
            "- needs_more_information: 1",
        ):
            self.assertIn(line, markdown)
        for market_id in EXPECTED_SELECTED_MARKET_IDS:
            self.assertIn(f"- `{market_id}`", markdown)

    def test_no_runtime_or_downstream_automation_exists(self):
        runtime_roots = [
            ROOT / "codex_auto",
            ROOT / "config",
            ROOT / "runs",
            ROOT / "scripts",
            ROOT / "state",
            ROOT / "tasks",
            ROOT / "pm_bot" / "paper",
            ROOT / "pm_bot" / "scoring",
            ROOT / "pm_bot" / "signals",
        ]
        targets = (
            "merge_selected_ingest_manual_evidence_overlay",
            "selected_ingest_merged_manual_research_packets",
            "selected_ingest_manual_evidence_overlay_merge_report",
        )
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

    def test_merger_uses_standard_library_only(self):
        tree = ast.parse(MERGER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "copy", "importlib", "json", "pathlib", "sys"})

    def test_merger_has_no_live_fetcher_or_trading_endpoint_imports(self):
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
