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
EXPORTER = ROOT / "pm_bot" / "research" / "export_selected_ingest_dossier_draft_skeletons.py"
MERGED_PACKETS = ROOT / "pm_bot" / "research" / "selected_ingest_merged_manual_research_packets.v1.json"
OPERATOR_REVIEW_QUEUE = ROOT / "pm_bot" / "research" / "selected_ingest_operator_review_queue.v1.json"
REVIEW_RECORDS_RESULT = ROOT / "pm_bot" / "research" / "selected_ingest_operator_review_records_result.v1.json"
JSON_OUTPUT = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_draft_skeletons.v1.json"
MARKDOWN_OUTPUT = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_draft_skeletons.v1.md"
EXPECTED_JSON_OUTPUT = ROOT / "pm_bot" / "research" / "expected_selected_ingest_dossier_draft_skeletons.v1.json"

EXPECTED_SELECTED_MARKET_IDS = ["692258", "824952", "691547", "597964", "598936"]
PROHIBITED_FIELD_TOKENS = {
    "bet",
    "bets",
    "betting",
    "ev",
    "expected_value",
    "expected_values",
    "market_decision",
    "order",
    "orders",
    "paper_order",
    "paper_orders",
    "probability",
    "probabilities",
    "recommendation",
    "recommendations",
    "score",
    "scores",
    "side",
    "sides",
    "signal",
    "signals",
    "stake",
    "stakes",
    "trade",
    "trades",
    "trading",
    "wallet",
    "wallets",
}
ALLOWED_FIELD_NAMES = {"current_yes_price"}
PROHIBITED_COMPLETION_PHRASES = {
    "completed dossier",
    "complete dossier",
    "final dossier",
    "market conclusion",
    "side recommendation",
    "betting recommendation",
}
PROHIBITED_INFERENCE_FIELDS = {
    "truth",
    "truth_value",
    "is_true",
    "verified",
    "claim_status",
    "outcome_assessment",
}


def _run_exporter(*extra_args):
    return subprocess.run(
        [sys.executable, str(EXPORTER), *extra_args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _load_module():
    spec = importlib.util.spec_from_file_location("selected_ingest_dossier_draft_skeleton_exporter", EXPORTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_export():
    _run_exporter()
    return _load_json(JSON_OUTPUT)


def _field_tokens(key):
    normalized = []
    current = []
    for char in str(key).lower():
        if char.isalnum() or char == "_":
            current.append(char)
        else:
            if current:
                normalized.extend("".join(current).split("_"))
                current = []
    if current:
        normalized.extend("".join(current).split("_"))
    compact = str(key).lower()
    return {token for token in normalized if token} | {compact}


def _walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _packet_by_market_id(payload, market_id):
    for packet in payload["packets"]:
        if packet["market_id"] == market_id:
            return packet
    raise AssertionError(f"missing packet {market_id}")


def _expected_evidence_inventory(packet):
    module = _load_module()
    inventory = []
    for slot_name in module.EVIDENCE_SLOTS:
        for item in packet["evidence_slots"].get(slot_name, []):
            inventory.append({field: item[field].strip() for field in module.EVIDENCE_INVENTORY_FIELDS})
    return inventory


def _ready_review_record(market_id):
    return {
        "market_id": market_id,
        "review_status": "review_completed",
        "review_outcome": "ready_for_dossier_drafting",
        "reviewer_notes": "Structural ready outcome test record.",
        "review_checks": {
            "resolution_criteria_checked": True,
            "evidence_structure_checked": True,
            "source_coverage_checked": True,
            "missing_information_reviewed": True,
            "no_trading_recommendation_present": True,
            "no_probability_or_ev_present": True,
            "no_side_recommendation_present": True,
            "no_market_decision_present": True,
        },
        "requested_followup_information": [],
        "quality_flags": [],
        "queue_group": "stub_only",
        "packet_completion_status": "stub_only",
    }


class SelectedIngestDossierDraftSkeletonExportTests(unittest.TestCase):
    def test_default_export_matches_expected_json(self):
        _run_exporter()

        self.assertEqual(_load_json(JSON_OUTPUT), _load_json(EXPECTED_JSON_OUTPUT))

    def test_only_ready_for_dossier_drafting_selected_ingest_records_are_exported(self):
        export = _load_export()
        skeletons = export["dossier_draft_skeletons"]

        self.assertEqual(export["selected_market_ids"], EXPECTED_SELECTED_MARKET_IDS)
        self.assertEqual(export["exported_market_ids"], ["824952"])
        self.assertEqual(len(skeletons), 1)
        self.assertEqual(skeletons[0]["market_id"], "824952")
        self.assertNotIn("692258", export["exported_market_ids"])
        self.assertNotIn("598936", export["exported_market_ids"])
        self.assertNotIn("691547", export["exported_market_ids"])
        self.assertNotIn("597964", export["exported_market_ids"])

    def test_needs_more_information_watch_only_and_rejected_records_are_skipped(self):
        export = _load_export()
        summary = export["export_summary"]

        self.assertEqual(summary["ready_review_records_seen"], 1)
        self.assertEqual(summary["dossier_draft_skeletons_exported"], 1)
        self.assertEqual(summary["records_skipped"], 5)
        self.assertEqual(summary["completed_dossiers_created"], 0)
        self.assertEqual(export["skipped_market_ids_by_reason"]["needs_more_information"], ["692258"])
        self.assertEqual(export["skipped_market_ids_by_reason"]["watch_only_manual"], ["598936"])
        self.assertEqual(export["skipped_market_ids_by_reason"]["rejected_record"], ["691547", "597964", "unknown-market-id"])

    def test_stub_only_packet_is_skipped_even_with_ready_review_record(self):
        module = _load_module()
        merged_payload = copy.deepcopy(_load_json(MERGED_PACKETS))
        review_payload = {
            "schema_version": "selected-ingest-stub-ready-test.v1",
            "review_summary": {
                "review_records_read": 1,
                "review_records_accepted": 1,
                "review_records_rejected": 0,
                "ready_for_dossier_drafting": 1,
                "needs_more_information": 0,
                "research_quality_rejected": 0,
                "watch_only_manual": 0,
            },
            "accepted_review_records": [_ready_review_record("691547")],
            "rejected_review_records": [],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            merged_path = temp_path / "merged.json"
            review_path = temp_path / "review.json"
            merged_path.write_text(json.dumps(merged_payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            review_path.write_text(json.dumps(review_payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            export = module.build_selected_ingest_dossier_draft_skeleton_export(
                merged_packets_path=merged_path,
                operator_review_queue_path=OPERATOR_REVIEW_QUEUE,
                review_records_result_path=review_path,
                json_output_path=temp_path / "out.json",
                markdown_output_path=temp_path / "out.md",
                expected_json_output_path=temp_path / "expected.json",
            )

        self.assertEqual(export["export_summary"]["dossier_draft_skeletons_exported"], 0)
        self.assertEqual(export["skipped_packet_market_ids_by_reason"]["stub_only"], ["691547", "597964", "598936"])

    def test_draft_status_is_always_skeleton_only(self):
        export = _load_export()
        for skeleton in export["dossier_draft_skeletons"]:
            self.assertEqual(skeleton["draft_status"], "dossier_draft_skeleton_only")

    def test_no_completed_dossier_language_is_emitted(self):
        rendered = json.dumps(_load_export(), sort_keys=True).lower()
        rendered += MARKDOWN_OUTPUT.read_text(encoding="utf-8").lower()

        for phrase in PROHIBITED_COMPLETION_PHRASES:
            self.assertNotIn(phrase, rendered)

    def test_no_betting_trading_recommendation_score_probability_ev_side_or_decision_fields_exist(self):
        export = _load_export()

        for key in _walk_keys(export):
            if key in ALLOWED_FIELD_NAMES:
                continue
            self.assertTrue(
                PROHIBITED_FIELD_TOKENS.isdisjoint(_field_tokens(key)),
                msg=f"prohibited field emitted: {key}",
            )

    def test_evidence_inventory_is_structural_copy_without_truth_inference_fields(self):
        export = _load_export()
        merged_payload = _load_json(MERGED_PACKETS)
        source_packet = _packet_by_market_id(merged_payload, "824952")
        skeleton = export["dossier_draft_skeletons"][0]

        self.assertEqual(skeleton["evidence_inventory"], _expected_evidence_inventory(source_packet))
        for key in _walk_keys(skeleton["evidence_inventory"]):
            self.assertTrue(PROHIBITED_INFERENCE_FIELDS.isdisjoint(_field_tokens(key)), msg=f"inference field emitted: {key}")

    def test_source_ingest_artifact_references_are_exported(self):
        export = _load_export()
        source_packet = _packet_by_market_id(_load_json(MERGED_PACKETS), "824952")
        skeleton = export["dossier_draft_skeletons"][0]

        self.assertEqual(skeleton["source_ingest_artifacts"], {key: source_packet["source_ingest_artifacts"][key] for key in sorted(source_packet["source_ingest_artifacts"])})

    def test_markdown_report_has_stable_headings_and_summary_counts(self):
        export = _load_export()
        markdown = MARKDOWN_OUTPUT.read_text(encoding="utf-8")
        summary = export["export_summary"]

        heading_lines = [line for line in markdown.splitlines() if line.startswith("#")]
        self.assertEqual(
            heading_lines,
            [
                "# Selected Ingest Dossier Draft Skeletons v1",
                "## Summary",
                "## Selected Market IDs",
                "## Draft Skeletons",
                "### 824952",
                "#### Source Coverage Summary",
                "#### Evidence Inventory",
                "#### Missing Information Reviewed",
                "#### Operator Review Notes",
                "#### Sections To Fill",
                "#### Open Questions",
                "#### Source Ingest Artifacts",
                "## Skipped Records",
                "### needs_more_information (1)",
                "### watch_only_manual (1)",
                "### research_quality_rejected (0)",
                "### stub_only (0)",
                "### invalid (0)",
                "### rejected_record (3)",
            ],
        )
        for field in (
            "ready_review_records_seen",
            "dossier_draft_skeletons_exported",
            "records_skipped",
            "completed_dossiers_created",
        ):
            self.assertIn(f"- {field}: {summary[field]}", markdown)
        for reason, count in summary["skipped_record_counts"].items():
            self.assertIn(f"- skipped_{reason}: {count}", markdown)

    def test_json_output_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            json_path = temp_path / "skeletons.json"
            markdown_path = temp_path / "skeletons.md"
            expected_path = temp_path / "expected.json"
            args = [
                "--json-output",
                str(json_path),
                "--markdown-output",
                str(markdown_path),
                "--expected-json-output",
                str(expected_path),
            ]

            first = _run_exporter(*args)
            first_json = json_path.read_text(encoding="utf-8")
            first_markdown = markdown_path.read_text(encoding="utf-8")
            second = _run_exporter(*args)

            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(first_json, json_path.read_text(encoding="utf-8"))
            self.assertEqual(first_markdown, markdown_path.read_text(encoding="utf-8"))
            self.assertEqual(json.loads(first_json), json.loads(expected_path.read_text(encoding="utf-8")))

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
            "export_selected_ingest_dossier_draft_skeletons",
            "selected_ingest_dossier_draft_skeletons",
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

    def test_exporter_uses_standard_library_only(self):
        tree = ast.parse(EXPORTER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "importlib", "json", "pathlib", "sys"})

    def test_exporter_has_no_live_fetcher_or_runtime_terms(self):
        source = EXPORTER.read_text(encoding="utf-8").lower()
        forbidden = [
            "requests",
            "urllib.request",
            "httpx",
            "aiohttp",
            "socket",
            "websocket",
            "py_clob_client",
            "gamma-api",
            "private_key",
            "api_key",
            "run_codex",
            "submit_order",
            "execute_trade",
        ]
        for term in forbidden:
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()
