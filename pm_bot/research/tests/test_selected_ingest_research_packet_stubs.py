import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BUILDER = ROOT / "pm_bot" / "research" / "build_selected_ingest_research_packet_stubs.py"
SELECTION_INDEX = ROOT / "pm_bot" / "ingest" / "operator_candidate_selection_index.v1.json"
SELECTION_OVERLAY = ROOT / "pm_bot" / "ingest" / "operator_candidate_selection_overlay_selected_first5.v1.json"
NORMALIZED_PREVIEW = ROOT / "pm_bot" / "ingest" / "normalized_market_preview.v1.json"
EXPECTED_JSON = ROOT / "pm_bot" / "research" / "expected_selected_ingest_research_packet_stubs.v1.json"

EXPECTED_SELECTED_MARKET_IDS = ["692258", "824952", "691547", "597964", "598936"]


def _load_module(path=BUILDER):
    spec = importlib.util.spec_from_file_location("selected_ingest_research_packet_stubs", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _build_payload():
    return _load_module().build_selected_ingest_research_packet_stubs()


def _walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


class SelectedIngestResearchPacketStubTests(unittest.TestCase):
    def test_overlay_validation_is_required(self):
        module = _load_module()
        index_payload = _load_json(SELECTION_INDEX)
        overlay_payload = _load_json(SELECTION_OVERLAY)
        normalized_payload = _load_json(NORMALIZED_PREVIEW)
        overlay_payload["selections"][0]["score"] = 1

        with self.assertRaises(module.OperatorSelectionPackError) as caught:
            module.build_selected_ingest_research_packet_stubs_payload(
                index_payload,
                overlay_payload,
                normalized_payload,
            )
        self.assertEqual(caught.exception.code, "overlay_prohibited_fields")

    def test_exactly_five_selected_market_ids_are_exported(self):
        payload = _build_payload()

        self.assertEqual(payload["summary"]["selected_market_ids_read"], 5)
        self.assertEqual(payload["summary"]["research_packet_stubs_created"], 5)
        self.assertEqual(payload["selected_market_ids"], EXPECTED_SELECTED_MARKET_IDS)
        self.assertEqual([stub["market_id"] for stub in payload["packet_stubs"]], EXPECTED_SELECTED_MARKET_IDS)

    def test_exported_market_ids_match_validated_overlay_order(self):
        module = _load_module()
        index_payload = _load_json(SELECTION_INDEX)
        overlay_payload = _load_json(SELECTION_OVERLAY)
        validation = module.validate_overlay_payload(overlay_payload, index_payload)
        expected_ids = [
            row["market_id"]
            for row in overlay_payload["selections"]
            if row["selected_for_research_stub"] is True
        ]

        payload = module.build_selected_ingest_research_packet_stubs()
        self.assertTrue(validation["overlay_valid"])
        self.assertEqual(payload["selected_market_ids"], expected_ids)

    def test_unselected_candidates_are_not_exported(self):
        overlay_payload = _load_json(SELECTION_OVERLAY)
        unselected_market_id = next(
            row["market_id"]
            for row in overlay_payload["selections"]
            if row["selected_for_research_stub"] is False
        )
        payload = _build_payload()

        self.assertNotIn(unselected_market_id, payload["selected_market_ids"])
        self.assertNotIn(unselected_market_id, [stub["market_id"] for stub in payload["packet_stubs"]])

    def test_missing_selected_market_id_is_rejected(self):
        module = _load_module()
        index_payload = _load_json(SELECTION_INDEX)
        overlay_payload = _load_json(SELECTION_OVERLAY)
        normalized_payload = _load_json(NORMALIZED_PREVIEW)
        missing_market_id = EXPECTED_SELECTED_MARKET_IDS[0]
        normalized_payload["records"] = [
            row for row in normalized_payload["records"] if row.get("market_id") != missing_market_id
        ]

        with self.assertRaises(module.SelectedIngestResearchStubError) as caught:
            module.build_selected_ingest_research_packet_stubs_payload(
                index_payload,
                overlay_payload,
                normalized_payload,
            )
        self.assertEqual(caught.exception.code, "selected_market_id_missing_from_normalized_preview")
        self.assertEqual(caught.exception.details["market_id"], missing_market_id)

    def test_completion_status_is_always_stub_only(self):
        payload = _build_payload()

        self.assertTrue(payload["packet_stubs"])
        self.assertTrue(payload["summary"]["completion_status_all_stub_only"])
        self.assertTrue(all(stub["completion_status"] == "stub_only" for stub in payload["packet_stubs"]))

    def test_evidence_slots_are_empty_placeholders(self):
        payload = _build_payload()

        for stub in payload["packet_stubs"]:
            self.assertEqual(tuple(stub["evidence_slots"].keys()), _load_module().EVIDENCE_SLOT_NAMES)
            self.assertTrue(all(value == [] for value in stub["evidence_slots"].values()))

    def test_no_completed_dossier_order_trade_wallet_execution_recommendation_score_probability_ev_side_or_market_decision_fields_exist(self):
        payload = _build_payload()
        forbidden_exact = {
            "completed_dossier",
            "completed_dossiers",
            "dossier",
            "execution",
            "executions",
            "ev",
            "expected_value",
            "market_decision",
            "order",
            "orders",
            "paper_order",
            "paper_orders",
            "probability",
            "recommendation",
            "recommendations",
            "score",
            "scores",
            "side",
            "trade",
            "trades",
            "wallet",
            "wallets",
        }
        for key in _walk_keys(payload):
            normalized = key.lower()
            self.assertNotIn(normalized, forbidden_exact)
            self.assertFalse(normalized.endswith("_score"))
            self.assertNotIn("expected_value", normalized)
            self.assertNotIn("market_decision", normalized)
            self.assertNotIn("probability", normalized)
            self.assertNotIn("recommendation", normalized)

    def test_source_and_search_plans_are_templates_only_and_do_not_fetch(self):
        payload = _build_payload()
        for stub in payload["packet_stubs"]:
            self.assertTrue(stub["source_plan"].startswith("Template only:"))
            self.assertTrue(all(item.startswith("Template only:") for item in stub["search_queries"]))
            self.assertTrue(
                all(item.startswith("Manual check template:") for item in stub["official_sources_to_check"])
            )
            self.assertTrue(
                all(item.startswith("Manual check template:") for item in stub["credible_news_sources_to_check"])
            )
            planned_text = "\n".join(
                [stub["source_plan"]]
                + stub["search_queries"]
                + stub["official_sources_to_check"]
                + stub["credible_news_sources_to_check"]
            ).lower()
            self.assertNotIn("http://", planned_text)
            self.assertNotIn("https://", planned_text)

        source = BUILDER.read_text(encoding="utf-8").lower()
        for term in ("requests", "urllib.request", "httpx", "aiohttp", "socket", "websocket", "py_clob_client"):
            self.assertNotIn(term, source)

    def test_current_yes_price_is_null_when_yes_outcome_is_ambiguous(self):
        module = _load_module()
        index_payload = _load_json(SELECTION_INDEX)
        overlay_payload = _load_json(SELECTION_OVERLAY)
        normalized_payload = copy.deepcopy(_load_json(NORMALIZED_PREVIEW))
        ambiguous_id = EXPECTED_SELECTED_MARKET_IDS[0]
        for row in normalized_payload["records"]:
            if row.get("market_id") == ambiguous_id:
                row["outcomes"] = ["Up", "Down"]
                row["outcome_prices"] = ["0.1", "0.9"]

        payload = module.build_selected_ingest_research_packet_stubs_payload(
            index_payload,
            overlay_payload,
            normalized_payload,
        )
        first_stub = payload["packet_stubs"][0]
        self.assertEqual(first_stub["market_id"], ambiguous_id)
        self.assertIsNone(first_stub["current_yes_price"])
        self.assertIn("current_yes_price_unavailable_or_ambiguous", first_stub["missing_information"])

    def test_source_ingest_artifact_references_are_present(self):
        payload = _build_payload()
        expected_sources = {
            "selection_index": "pm_bot/ingest/operator_candidate_selection_index.v1.json",
            "selection_overlay": "pm_bot/ingest/operator_candidate_selection_overlay_selected_first5.v1.json",
            "normalized_preview": "pm_bot/ingest/normalized_market_preview.v1.json",
        }

        self.assertEqual(payload["source_ingest_artifacts"], expected_sources)
        for stub in payload["packet_stubs"]:
            self.assertEqual(
                stub["source_ingest_artifacts"]["operator_candidate_selection_index"],
                expected_sources["selection_index"],
            )
            self.assertEqual(
                stub["source_ingest_artifacts"]["operator_candidate_selection_overlay"],
                expected_sources["selection_overlay"],
            )
            self.assertEqual(
                stub["source_ingest_artifacts"]["normalized_market_preview"],
                expected_sources["normalized_preview"],
            )
            self.assertTrue(stub["source_ingest_artifacts"]["normalized_source_snapshot_path"])

    def test_output_json_is_deterministic_and_matches_expected(self):
        module = _load_module()
        first = module.build_selected_ingest_research_packet_stubs()
        second = module.build_selected_ingest_research_packet_stubs()
        self.assertEqual(first, second)
        self.assertEqual(first, _load_json(EXPECTED_JSON))

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            output_json = temp_root / "selected.json"
            output_md = temp_root / "selected.md"
            expected_json = temp_root / "expected.json"
            module.write_selected_ingest_research_packet_stub_artifacts(
                output_json=output_json,
                output_md=output_md,
                expected_json=expected_json,
            )
            first_text = output_json.read_text(encoding="utf-8")
            module.write_selected_ingest_research_packet_stub_artifacts(
                output_json=output_json,
                output_md=output_md,
                expected_json=expected_json,
            )
            self.assertEqual(first_text, output_json.read_text(encoding="utf-8"))
            self.assertEqual(json.loads(first_text), json.loads(expected_json.read_text(encoding="utf-8")))

    def test_markdown_report_has_stable_headings_and_summary_counts(self):
        module = _load_module()
        payload = module.build_selected_ingest_research_packet_stubs()
        markdown = module.render_markdown_report(payload)

        expected_headings = [
            "# Selected Ingest Research Packet Stubs",
            "## Summary",
            "## Source Artifacts",
            "## Safety Boundary",
            "## Selected Market IDs",
            "## Packet Stubs",
        ]
        for heading in expected_headings:
            self.assertIn(heading, markdown)
        self.assertIn("- selected_market_ids_read: 5", markdown)
        self.assertIn("- research_packet_stubs_created: 5", markdown)
        self.assertIn("- completion_status_all_stub_only: true", markdown)
        for market_id in EXPECTED_SELECTED_MARKET_IDS:
            self.assertIn(f"### market_id: `{market_id}`", markdown)

    def test_research_007_manual_packet_validator_accepts_stub_only_packets(self):
        validator_path = ROOT / "pm_bot" / "research" / "validate_manual_research_packets.py"
        spec = importlib.util.spec_from_file_location("manual_research_packet_validator", validator_path)
        validator = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(validator)

        for stub in _build_payload()["packet_stubs"]:
            self.assertEqual(validator.validate_packet(stub), [], msg=stub["market_id"])

    def test_no_runtime_or_downstream_automation_references_new_bridge(self):
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
            "build_selected_ingest_research_packet_stubs",
            "selected_ingest_research_packet_stubs",
            "selected_ingest_market_research_stub",
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

    def test_cli_writes_requested_artifacts_without_default_runtime_wiring(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            output_json = temp_root / "selected.json"
            output_md = temp_root / "selected.md"
            expected_json = temp_root / "expected.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(BUILDER),
                    "--output-json",
                    str(output_json),
                    "--output-md",
                    str(output_md),
                    "--expected-json",
                    str(expected_json),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

            stdout = json.loads(result.stdout)
            self.assertTrue(stdout["input_accepted"])
            self.assertEqual(stdout["selected_market_ids"], EXPECTED_SELECTED_MARKET_IDS)
            self.assertEqual(_load_json(output_json), _load_json(expected_json))
            self.assertTrue(output_md.read_text(encoding="utf-8").startswith("# Selected Ingest Research Packet Stubs"))


if __name__ == "__main__":
    unittest.main()
