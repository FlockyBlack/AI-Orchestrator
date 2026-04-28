import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EXPORTER = ROOT / "pm_bot" / "research" / "export_dossier_draft_skeletons.py"
MERGED_PACKETS = ROOT / "pm_bot" / "research" / "merged_manual_research_packets.v1.json"
JSON_OUTPUT = ROOT / "pm_bot" / "research" / "dossier_draft_skeletons.v1.json"
MARKDOWN_OUTPUT = ROOT / "pm_bot" / "research" / "dossier_draft_skeletons.v1.md"
EXPECTED_JSON_OUTPUT = ROOT / "pm_bot" / "research" / "expected_dossier_draft_skeletons.v1.json"


PROHIBITED_FIELD_TOKENS = {
    "order",
    "orders",
    "trade",
    "trades",
    "trading",
    "wallet",
    "wallets",
    "private_key",
    "private_keys",
    "execution",
    "executions",
    "recommendation",
    "recommendations",
    "score",
    "scores",
    "signal",
    "signals",
    "probability",
    "probabilities",
    "expected_value",
    "expected_values",
    "ev",
    "side",
    "sides",
    "bet",
    "bets",
    "betting",
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
    spec = importlib.util.spec_from_file_location("dossier_draft_skeleton_exporter", EXPORTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_export():
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


class DossierDraftSkeletonExportTests(unittest.TestCase):
    def test_default_export_matches_expected_json(self):
        _run_exporter()
        self.assertEqual(_load_json(JSON_OUTPUT), _load_json(EXPECTED_JSON_OUTPUT))

    def test_only_accepted_ready_review_records_are_exported(self):
        export = _load_export()
        skeletons = export["dossier_draft_skeletons"]

        self.assertEqual(export["exported_market_ids"], ["563650"])
        self.assertEqual(len(skeletons), 1)
        self.assertEqual(skeletons[0]["market_id"], "563650")
        self.assertNotIn("569344", export["exported_market_ids"])
        self.assertNotIn("569366", export["exported_market_ids"])
        self.assertNotIn("573656", export["exported_market_ids"])

    def test_skipped_packet_counts_are_correct(self):
        export = _load_export()
        summary = export["export_summary"]

        self.assertEqual(summary["packets_read"], 10)
        self.assertEqual(summary["accepted_review_records_seen"], 3)
        self.assertEqual(summary["ready_review_records_seen"], 1)
        self.assertEqual(summary["dossier_draft_skeletons_exported"], 1)
        self.assertEqual(summary["packets_skipped"], 9)
        self.assertEqual(
            summary["skipped_packet_counts"],
            {
                "stub_only": 7,
                "needs_more_information": 1,
                "manual_evidence_added_without_accepted_ready_review": 0,
                "watch_only_manual": 1,
                "research_quality_rejected": 0,
                "invalid": 0,
            },
        )
        self.assertEqual(export["skipped_market_ids_by_reason"]["watch_only_manual"], ["573656"])
        self.assertEqual(export["skipped_market_ids_by_reason"]["needs_more_information"], ["569366"])
        self.assertEqual(export["skipped_market_ids_by_reason"]["stub_only"], ["569332", "569333", "569334", "569343", "569344", "569368", "569373"])

    def test_manual_evidence_added_without_accepted_ready_review_is_skipped(self):
        module = _load_module()
        source_payload = _load_json(MERGED_PACKETS)
        ready_packet = _packet_by_market_id(source_payload, "563650")
        manual_packet = dict(ready_packet)
        manual_packet["completion_status"] = "manual_evidence_added"
        merged_payload = {
            "schema_version": "manual-evidence-skip-test.v1",
            "packets": [manual_packet],
        }
        queue_payload = {
            "schema_version": "queue-test.v1",
            "groups": {
                "ready_for_operator_review": [],
                "needs_more_information": [],
                "manual_evidence_added": [{"market_id": "563650"}],
                "stub_only": [],
                "invalid": [],
            },
        }
        review_payload = {
            "schema_version": "review-result-test.v1",
            "accepted_review_records": [],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            merged_path = temp_path / "merged.json"
            queue_path = temp_path / "queue.json"
            review_path = temp_path / "review.json"
            merged_path.write_text(json.dumps(merged_payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            queue_path.write_text(json.dumps(queue_payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            review_path.write_text(json.dumps(review_payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            export = module.build_dossier_draft_skeleton_export(
                merged_packets_path=merged_path,
                operator_review_queue_path=queue_path,
                review_records_result_path=review_path,
                json_output_path=temp_path / "out.json",
                markdown_output_path=temp_path / "out.md",
                expected_json_output_path=temp_path / "expected.json",
            )

        self.assertEqual(export["export_summary"]["dossier_draft_skeletons_exported"], 0)
        self.assertEqual(export["export_summary"]["packets_skipped"], 1)
        self.assertEqual(export["export_summary"]["skipped_packet_counts"]["manual_evidence_added_without_accepted_ready_review"], 1)

    def test_draft_status_is_always_skeleton_only(self):
        export = _load_export()
        for skeleton in export["dossier_draft_skeletons"]:
            self.assertEqual(skeleton["draft_status"], "dossier_draft_skeleton_only")

    def test_no_completed_dossier_language_is_emitted(self):
        rendered = json.dumps(_load_export(), sort_keys=True).lower()
        rendered += MARKDOWN_OUTPUT.read_text(encoding="utf-8").lower()

        for phrase in PROHIBITED_COMPLETION_PHRASES:
            self.assertNotIn(phrase, rendered)

    def test_no_betting_trading_recommendation_score_probability_or_ev_fields_exist(self):
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
        source_packet = _packet_by_market_id(merged_payload, "563650")
        skeleton = export["dossier_draft_skeletons"][0]

        self.assertEqual(skeleton["evidence_inventory"], _expected_evidence_inventory(source_packet))
        for key in _walk_keys(skeleton["evidence_inventory"]):
            self.assertTrue(PROHIBITED_INFERENCE_FIELDS.isdisjoint(_field_tokens(key)), msg=f"inference field emitted: {key}")

    def test_markdown_report_has_stable_headings_and_summary_counts(self):
        export = _load_export()
        markdown = MARKDOWN_OUTPUT.read_text(encoding="utf-8")
        summary = export["export_summary"]

        heading_lines = [line for line in markdown.splitlines() if line.startswith("#")]
        self.assertEqual(
            heading_lines,
            [
                "# PMBOT Dossier Draft Skeletons v1",
                "## Summary",
                "## Draft Skeletons",
                "### 563650",
                "#### Source Coverage Summary",
                "#### Evidence Inventory",
                "#### Missing Information Reviewed",
                "#### Operator Review Notes",
                "#### Sections To Fill",
                "#### Open Questions",
                "## Skipped Packets",
                "### stub_only (7)",
                "### needs_more_information (1)",
                "### manual_evidence_added_without_accepted_ready_review (0)",
                "### watch_only_manual (1)",
                "### research_quality_rejected (0)",
                "### invalid (0)",
            ],
        )
        for field in (
            "packets_read",
            "accepted_review_records_seen",
            "ready_review_records_seen",
            "dossier_draft_skeletons_exported",
            "packets_skipped",
        ):
            self.assertIn(f"- {field}: {summary[field]}", markdown)
        for reason, count in summary["skipped_packet_counts"].items():
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

    def test_exporter_uses_standard_library_only(self):
        tree = ast.parse(EXPORTER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "sys"})

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
            "submit_order",
            "execute_trade",
            "run_codex",
        ]
        for term in forbidden:
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()
