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
EXPORTER = ROOT / "pm_bot" / "research" / "export_selected_ingest_operator_review_queue.py"
MERGED_PACKETS = ROOT / "pm_bot" / "research" / "selected_ingest_merged_manual_research_packets.v1.json"
JSON_QUEUE = ROOT / "pm_bot" / "research" / "selected_ingest_operator_review_queue.v1.json"
MARKDOWN_QUEUE = ROOT / "pm_bot" / "research" / "selected_ingest_operator_review_queue.v1.md"
EXPECTED_JSON_QUEUE = ROOT / "pm_bot" / "research" / "expected_selected_ingest_operator_review_queue.v1.json"

EXPECTED_SELECTED_MARKET_IDS = ["692258", "824952", "691547", "597964", "598936"]
PROHIBITED_FIELD_TOKENS = {
    "bet",
    "bets",
    "betting",
    "completed_dossier",
    "completed_dossiers",
    "dossier",
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
    "signal",
    "signals",
    "stake",
    "stakes",
    "trade",
    "trades",
    "wallet",
    "wallets",
}
PROHIBITED_ACTION_TOKENS = PROHIBITED_FIELD_TOKENS | {"buy", "sell"}
ALLOWED_NEXT_MANUAL_ACTIONS = {
    "operator_review_required",
    "add_missing_information",
    "fill_stub_evidence",
    "fix_validation_errors",
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
    spec = importlib.util.spec_from_file_location("selected_ingest_operator_review_queue", EXPORTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_queue():
    return _load_json(JSON_QUEUE)


def _load_merged_packets():
    return _load_json(MERGED_PACKETS)["packets"]


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
            yield str(key)
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _queue_items(queue):
    for group_name in queue["groups"]:
        yield from queue["groups"][group_name]


class SelectedIngestOperatorReviewQueueTests(unittest.TestCase):
    def test_default_export_matches_expected_json_queue(self):
        _run_exporter()

        self.assertEqual(_load_json(JSON_QUEUE), _load_json(EXPECTED_JSON_QUEUE))

    def test_all_five_selected_merged_packets_are_represented(self):
        _run_exporter()
        queue = _load_queue()
        merged_market_ids = [packet["market_id"] for packet in _load_merged_packets()]
        queue_market_ids = [item["market_id"] for item in _queue_items(queue)]

        self.assertEqual(queue["selected_market_ids"], EXPECTED_SELECTED_MARKET_IDS)
        self.assertEqual(queue["queue_summary"]["packets_total"], 5)
        self.assertEqual(sorted(queue_market_ids), sorted(merged_market_ids))
        self.assertEqual(sorted(queue_market_ids), sorted(EXPECTED_SELECTED_MARKET_IDS))

    def test_ready_for_operator_review_packet_is_grouped_correctly(self):
        _run_exporter()
        queue = _load_queue()
        ready = queue["groups"]["ready_for_operator_review"]

        self.assertEqual([item["market_id"] for item in ready], ["824952"])
        self.assertEqual(ready[0]["completion_status"], "ready_for_operator_review")
        self.assertEqual(ready[0]["next_manual_action"], "operator_review_required")
        self.assertEqual(ready[0]["missing_information_count"], 0)
        self.assertEqual(ready[0]["evidence_item_count"], 4)
        self.assertEqual(ready[0]["validation_errors"], [])

    def test_needs_more_information_packet_is_grouped_correctly(self):
        _run_exporter()
        queue = _load_queue()
        needs_more_information = queue["groups"]["needs_more_information"]

        self.assertEqual([item["market_id"] for item in needs_more_information], ["692258"])
        self.assertEqual(needs_more_information[0]["completion_status"], "needs_more_information")
        self.assertEqual(needs_more_information[0]["next_manual_action"], "add_missing_information")
        self.assertGreater(needs_more_information[0]["missing_information_count"], 0)
        self.assertEqual(needs_more_information[0]["evidence_item_count"], 1)
        self.assertEqual(needs_more_information[0]["validation_errors"], [])

    def test_stub_only_packets_remain_non_review_ready(self):
        _run_exporter()
        queue = _load_queue()
        stub_market_ids = [item["market_id"] for item in queue["groups"]["stub_only"]]
        ready_market_ids = {item["market_id"] for item in queue["groups"]["ready_for_operator_review"]}

        self.assertEqual(stub_market_ids, ["691547", "597964", "598936"])
        self.assertTrue(set(stub_market_ids).isdisjoint(ready_market_ids))
        for item in queue["groups"]["stub_only"]:
            self.assertEqual(item["completion_status"], "stub_only")
            self.assertEqual(item["next_manual_action"], "fill_stub_evidence")
            self.assertEqual(item["evidence_item_count"], 0)

    def test_invalid_packets_are_grouped_deterministically(self):
        module = _load_module()
        payload = copy.deepcopy(_load_json(MERGED_PACKETS))
        payload["packets"][0]["completion_status"] = "not_a_valid_status"

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            merged_path = temp_path / "merged.json"
            merged_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            queue = module.build_selected_ingest_operator_review_queue(
                merged_packets_path=merged_path,
                json_output_path=temp_path / "queue.json",
                markdown_output_path=temp_path / "queue.md",
            )

        invalid = queue["groups"]["invalid"]
        self.assertEqual([item["market_id"] for item in invalid], ["692258"])
        self.assertEqual(invalid[0]["next_manual_action"], "fix_validation_errors")
        self.assertEqual(queue["queue_summary"]["invalid"], 1)
        self.assertEqual(queue["queue_summary"]["packets_total"], 5)

    def test_next_manual_action_has_no_betting_or_trading_language(self):
        _run_exporter()
        queue = _load_queue()

        for item in _queue_items(queue):
            action = item["next_manual_action"]
            self.assertIn(action, ALLOWED_NEXT_MANUAL_ACTIONS)
            self.assertTrue(PROHIBITED_ACTION_TOKENS.isdisjoint(_field_tokens(action)), msg=action)

    def test_prohibited_fields_are_absent_from_queue_items(self):
        _run_exporter()
        queue = _load_queue()
        module = _load_module()
        expected_fields = list(module.QUEUE_ITEM_FIELDS)

        for item in _queue_items(queue):
            self.assertEqual(list(item), expected_fields)
            for key in _walk_keys(item):
                self.assertTrue(
                    PROHIBITED_FIELD_TOKENS.isdisjoint(_field_tokens(key)),
                    msg=f"{item['market_id']} contains prohibited field {key}",
                )

    def test_json_output_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            json_path = temp_path / "queue.json"
            markdown_path = temp_path / "queue.md"
            expected_path = temp_path / "expected_queue.json"
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

    def test_markdown_report_has_stable_headings_and_summary_counts(self):
        _run_exporter()
        queue = _load_queue()
        markdown = MARKDOWN_QUEUE.read_text(encoding="utf-8")
        summary = queue["queue_summary"]

        for heading in (
            "# Selected Ingest Operator Review Queue v1",
            "## Summary",
            "## Selected Market IDs",
            "## Safety Boundary",
        ):
            self.assertIn(heading, markdown)
        self.assertIn(f"- packets_total: {summary['packets_total']}", markdown)
        self.assertIn(f"- ready_for_operator_review: {summary['ready_for_operator_review']}", markdown)
        self.assertIn(f"- needs_more_information: {summary['needs_more_information']}", markdown)
        self.assertIn(f"- manual_evidence_added: {summary['manual_evidence_added']}", markdown)
        self.assertIn(f"- stub_only: {summary['stub_only']}", markdown)
        self.assertIn(f"- invalid: {summary['invalid']}", markdown)

        group_heading_lines = [
            line
            for line in markdown.splitlines()
            if line.startswith("## ")
            and line
            not in {"## Summary", "## Selected Market IDs", "## Safety Boundary"}
        ]
        self.assertEqual(
            group_heading_lines,
            [
                "## ready_for_operator_review (1)",
                "## needs_more_information (1)",
                "## manual_evidence_added (0)",
                "## stub_only (3)",
                "## invalid (0)",
            ],
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
            "export_selected_ingest_operator_review_queue",
            "selected_ingest_operator_review_queue",
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
