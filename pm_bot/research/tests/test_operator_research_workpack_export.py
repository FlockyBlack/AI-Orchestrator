import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EXPORTER = ROOT / "pm_bot" / "research" / "export_operator_research_workpack.py"
PACKET_STUBS = ROOT / "pm_bot" / "research" / "expected_research_packet_stubs.v1.json"
MARKDOWN_WORKPACK = ROOT / "pm_bot" / "research" / "operator_research_workpack.v1.md"
JSON_INDEX = ROOT / "pm_bot" / "research" / "operator_research_workpack_index.v1.json"
EXPECTED_JSON_INDEX = ROOT / "pm_bot" / "research" / "expected_operator_research_workpack_index.v1.json"


FORBIDDEN_OPERATOR_FIELD_TOKENS = {
    "order",
    "orders",
    "trade",
    "trades",
    "wallet",
    "wallets",
    "execution",
    "executions",
    "betting",
    "betting_recommendation",
    "betting_recommendations",
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
    spec = importlib.util.spec_from_file_location("operator_research_workpack_exporter", EXPORTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_index():
    return json.loads(JSON_INDEX.read_text(encoding="utf-8"))


def _load_stubs():
    return json.loads(PACKET_STUBS.read_text(encoding="utf-8"))


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
            yield key
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


class OperatorResearchWorkpackExportTests(unittest.TestCase):
    def test_default_export_matches_expected_index(self):
        _run_exporter()
        self.assertEqual(json.loads(JSON_INDEX.read_text(encoding="utf-8")), json.loads(EXPECTED_JSON_INDEX.read_text(encoding="utf-8")))

    def test_all_ten_stub_candidates_are_exported(self):
        payload = _load_index()
        stubs = _load_stubs()
        expected_ids = [packet["market_id"] for packet in stubs["packet_stubs"]]

        self.assertEqual(payload["export_count"], 10)
        self.assertEqual(payload["market_ids"], expected_ids)
        self.assertEqual([market["market_id"] for market in payload["markets"]], expected_ids)

    def test_required_operator_fields_are_present(self):
        module = _load_module()
        required = set(module.REQUIRED_OPERATOR_FIELDS)
        payload = _load_index()

        for market in payload["markets"]:
            self.assertLessEqual(required, set(market), msg=market["market_id"])
            self.assertTrue(market["market_id"])
            self.assertTrue(market["title_question"])
            self.assertEqual(market["completion_status"], "stub_only")

    def test_blank_evidence_templates_match_validator_fields(self):
        payload = _load_index()
        required_evidence_fields = payload["required_evidence_fields"]
        self.assertEqual(
            required_evidence_fields,
            [
                "source_name",
                "source_type",
                "source_url_or_reference",
                "captured_claim",
                "relevance_to_resolution",
                "operator_notes",
            ],
        )

        for market in payload["markets"]:
            template = market["blank_evidence_capture_template"]
            self.assertEqual(list(template), required_evidence_fields)
            self.assertTrue(all(value == "" for value in template.values()))

    def test_completion_statuses_remain_stub_only(self):
        payload = _load_index()
        self.assertEqual(payload["completion_statuses"], ["stub_only"])
        self.assertTrue(all(market["completion_status"] == "stub_only" for market in payload["markets"]))

    def test_no_order_trade_wallet_execution_or_betting_fields_in_market_exports(self):
        payload = _load_index()
        for market in payload["markets"]:
            for key in _walk_keys(market):
                self.assertTrue(
                    FORBIDDEN_OPERATOR_FIELD_TOKENS.isdisjoint(_field_tokens(key)),
                    msg=f"{market['market_id']} contains forbidden operator field {key}",
                )

    def test_markdown_has_stable_market_headings(self):
        payload = _load_index()
        markdown = MARKDOWN_WORKPACK.read_text(encoding="utf-8")
        heading_lines = [line for line in markdown.splitlines() if line.startswith("## Market ")]

        self.assertEqual(heading_lines, [f"## Market {market_id}" for market_id in payload["market_ids"]])
        for market_id in payload["market_ids"]:
            self.assertIn(f"- market_id: {market_id}", markdown)
            self.assertIn("- completion_status: stub_only", markdown)

    def test_json_index_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            markdown_path = temp_path / "workpack.md"
            index_path = temp_path / "index.json"
            expected_path = temp_path / "expected_index.json"

            _run_exporter("--markdown-output", str(markdown_path), "--json-index-output", str(index_path), "--expected-json-index-output", str(expected_path))
            first_index = index_path.read_text(encoding="utf-8")
            first_markdown = markdown_path.read_text(encoding="utf-8")
            _run_exporter("--markdown-output", str(markdown_path), "--json-index-output", str(index_path), "--expected-json-index-output", str(expected_path))
            second_index = index_path.read_text(encoding="utf-8")
            second_markdown = markdown_path.read_text(encoding="utf-8")

            self.assertEqual(first_index, second_index)
            self.assertEqual(first_markdown, second_markdown)
            self.assertEqual(json.loads(first_index), json.loads(expected_path.read_text(encoding="utf-8")))

    def test_exporter_uses_standard_library_only(self):
        tree = ast.parse(EXPORTER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "importlib", "json", "pathlib", "sys"})

    def test_exporter_has_no_network_or_runtime_terms(self):
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
            "submit_order",
            "execute_trade",
            "run_codex",
        ]
        for term in forbidden:
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()
