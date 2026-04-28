import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EXPORTER = ROOT / "pm_bot" / "research" / "export_selected_ingest_operator_workpack.py"
STUBS = ROOT / "pm_bot" / "research" / "selected_ingest_research_packet_stubs.v1.json"
MARKDOWN = ROOT / "pm_bot" / "research" / "selected_ingest_operator_workpack.v1.md"
INDEX = ROOT / "pm_bot" / "research" / "selected_ingest_operator_workpack_index.v1.json"
OVERLAY = ROOT / "pm_bot" / "research" / "selected_ingest_manual_evidence_overlay_template.v1.json"
EXPECTED_INDEX = ROOT / "pm_bot" / "research" / "expected_selected_ingest_operator_workpack_index.v1.json"

EXPECTED_SELECTED_MARKET_IDS = ["692258", "824952", "691547", "597964", "598936"]
EXPECTED_EVIDENCE_FIELDS = [
    "source_name",
    "source_type",
    "source_url_or_reference",
    "captured_claim",
    "relevance_to_resolution",
    "operator_notes",
]
FORBIDDEN_FIELD_TOKENS = {
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


def _run_exporter(*extra_args):
    return subprocess.run(
        [sys.executable, str(EXPORTER), *extra_args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _load_module():
    spec = importlib.util.spec_from_file_location("selected_ingest_operator_workpack", EXPORTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


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
    return {token for token in normalized if token} | {str(key).lower()}


def _walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key)
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


class SelectedIngestOperatorWorkpackTests(unittest.TestCase):
    def test_default_export_matches_expected_index(self):
        _run_exporter()

        self.assertEqual(_load_json(INDEX), _load_json(EXPECTED_INDEX))

    def test_exactly_five_selected_stubs_are_exported_in_source_order(self):
        _run_exporter()
        index = _load_json(INDEX)
        stubs = _load_json(STUBS)
        stub_market_ids = [packet["market_id"] for packet in stubs["packet_stubs"]]

        self.assertEqual(index["selected_stub_packets_read"], 5)
        self.assertEqual(index["operator_workpack_items_exported"], 5)
        self.assertEqual(index["selected_market_ids"], EXPECTED_SELECTED_MARKET_IDS)
        self.assertEqual(index["selected_market_ids"], stub_market_ids)
        self.assertEqual([item["market_id"] for item in index["workpack_items"]], stub_market_ids)

    def test_required_workpack_fields_are_present(self):
        module = _load_module()
        index = module.build_workpack_index()
        required = set(module.REQUIRED_WORKPACK_ITEM_FIELDS)

        for item in index["workpack_items"]:
            self.assertLessEqual(required, set(item), msg=item["market_id"])
            self.assertTrue(item["title_question"])
            self.assertTrue(item["event_id"])
            self.assertTrue(item["event_title"])
            self.assertEqual(item["completion_status"], "stub_only")

    def test_completion_status_remains_stub_only(self):
        index = _load_module().build_workpack_index()

        self.assertEqual(index["completion_statuses"], ["stub_only"])
        self.assertTrue(all(item["completion_status"] == "stub_only" for item in index["workpack_items"]))

    def test_evidence_templates_are_blank(self):
        index = _load_module().build_workpack_index()

        self.assertEqual(index["required_evidence_fields"], EXPECTED_EVIDENCE_FIELDS)
        for item in index["workpack_items"]:
            template = item["blank_evidence_capture_template"]
            self.assertEqual(list(template), EXPECTED_EVIDENCE_FIELDS)
            self.assertTrue(all(value == "" for value in template.values()))

    def test_manual_evidence_overlay_template_is_blank_and_safe(self):
        _run_exporter()
        overlay = _load_json(OVERLAY)

        self.assertEqual(overlay["schema_version"], "selected_ingest_manual_evidence_overlay_template.v1")
        self.assertEqual(overlay["selected_market_ids"], EXPECTED_SELECTED_MARKET_IDS)
        self.assertEqual(list(overlay["blank_evidence_entry_template"]), EXPECTED_EVIDENCE_FIELDS)
        self.assertTrue(all(value == "" for value in overlay["blank_evidence_entry_template"].values()))
        self.assertEqual(list(overlay["manual_entries_by_market_id"]), EXPECTED_SELECTED_MARKET_IDS)

        for market_id, entry in overlay["manual_entries_by_market_id"].items():
            self.assertIn(market_id, EXPECTED_SELECTED_MARKET_IDS)
            self.assertEqual(entry["completion_status"], "stub_only")
            self.assertEqual(entry["manual_evidence_entries"], [])
            self.assertEqual(entry["missing_information"], [])
            self.assertEqual(entry["operator_notes"], "")

    def test_no_completed_dossier_or_decision_fields_exist_in_workpack_or_overlay(self):
        _run_exporter()
        payloads = [_load_json(INDEX), _load_json(OVERLAY)]

        for payload in payloads:
            for key in _walk_keys(payload):
                tokens = _field_tokens(key)
                self.assertTrue(
                    FORBIDDEN_FIELD_TOKENS.isdisjoint(tokens),
                    msg=f"forbidden field token in key {key}",
                )
                normalized = key.lower()
                self.assertNotIn("expected_value", normalized)
                self.assertNotIn("market_decision", normalized)
                self.assertNotIn("probability", normalized)
                self.assertNotIn("recommendation", normalized)

    def test_output_json_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            markdown_path = temp_path / "workpack.md"
            index_path = temp_path / "index.json"
            overlay_path = temp_path / "overlay.json"
            expected_path = temp_path / "expected.json"
            args = [
                "--markdown-output",
                str(markdown_path),
                "--index-output",
                str(index_path),
                "--overlay-output",
                str(overlay_path),
                "--expected-index-output",
                str(expected_path),
            ]

            _run_exporter(*args)
            first_index = index_path.read_text(encoding="utf-8")
            first_overlay = overlay_path.read_text(encoding="utf-8")
            first_markdown = markdown_path.read_text(encoding="utf-8")
            _run_exporter(*args)

            self.assertEqual(first_index, index_path.read_text(encoding="utf-8"))
            self.assertEqual(first_overlay, overlay_path.read_text(encoding="utf-8"))
            self.assertEqual(first_markdown, markdown_path.read_text(encoding="utf-8"))
            self.assertEqual(json.loads(first_index), json.loads(expected_path.read_text(encoding="utf-8")))

    def test_markdown_report_has_stable_headings_and_summary_counts(self):
        _run_exporter()
        markdown = MARKDOWN.read_text(encoding="utf-8")

        for heading in (
            "# Selected Ingest Operator Workpack v1",
            "## Summary",
            "## Source Artifact",
            "## Safety Boundary",
            "## Selected Market IDs",
            "## Workpack Items",
        ):
            self.assertIn(heading, markdown)
        self.assertIn("- selected_stub_packets_read: 5", markdown)
        self.assertIn("- operator_workpack_items_exported: 5", markdown)
        self.assertIn("- completion_status: stub_only", markdown)
        self.assertEqual(
            [line for line in markdown.splitlines() if line.startswith("### Market ")],
            [f"### Market {market_id}" for market_id in EXPECTED_SELECTED_MARKET_IDS],
        )

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
            "export_selected_ingest_operator_workpack",
            "selected_ingest_operator_workpack",
            "selected_ingest_manual_evidence_overlay_template",
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
