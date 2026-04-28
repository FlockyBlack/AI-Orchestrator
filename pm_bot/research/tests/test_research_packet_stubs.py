import ast
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "research" / "run_research_packet_stubs.py"
QUEUE = ROOT / "pm_bot" / "research" / "expected_market_research_candidate_queue.v1.json"
EXPECTED_JSON = ROOT / "pm_bot" / "research" / "expected_research_packet_stubs.v1.json"


REQUIRED_STUB_FIELDS = {
    "market_id",
    "title",
    "question",
    "category",
    "packet_type",
    "current_yes_price",
    "liquidity",
    "deadline",
    "resolution_criteria_summary",
    "why_selected_for_research",
    "why_not_bet_yet",
    "source_plan",
    "search_queries",
    "official_sources_to_check",
    "credible_news_sources_to_check",
    "evidence_slots",
    "missing_information",
    "completion_status",
}


FORBIDDEN_STUB_FIELDS = {
    "completed_dossier",
    "completed_dossiers",
    "dossier",
    "decision",
    "trade",
    "trades",
    "order",
    "orders",
    "paper_order",
    "paper_orders",
    "real_order",
    "real_orders",
    "paper_orders_created",
    "real_order_created",
    "workspace_state_written",
}


def _run_json(*args):
    return subprocess.run([sys.executable, str(RUNNER), *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _load_module(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


class ResearchPacketStubTests(unittest.TestCase):
    def test_json_output_is_deterministic_and_matches_expected(self):
        first = _run_json().stdout
        second = _run_json().stdout
        self.assertEqual(first, second)
        self.assertEqual(json.loads(first), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_exactly_lower_risk_operator_shortlist_candidates_are_included(self):
        payload = json.loads(_run_json().stdout)
        queue = json.loads(QUEUE.read_text(encoding="utf-8"))
        expected_ids = [row["market_id"] for row in queue["operator_shortlist_candidates"]]
        self.assertEqual(payload["selected_market_ids"], expected_ids)
        self.assertEqual([stub["market_id"] for stub in payload["packet_stubs"]], expected_ids)
        self.assertEqual(payload["selected_count"], 10)
        self.assertEqual([stub["shortlist_rank"] for stub in payload["packet_stubs"]], list(range(1, 11)))

    def test_limit_option_keeps_top_shortlist_order(self):
        payload = json.loads(_run_json("--limit", "3").stdout)
        self.assertEqual(payload["selected_count"], 3)
        self.assertEqual(payload["selected_market_ids"], ["569368", "569366", "569343"])
        self.assertEqual([stub["shortlist_rank"] for stub in payload["packet_stubs"]], [1, 2, 3])

    def test_required_fields_are_present(self):
        payload = json.loads(_run_json().stdout)
        for stub in payload["packet_stubs"]:
            self.assertLessEqual(REQUIRED_STUB_FIELDS, set(stub))
            self.assertIsInstance(stub["source_plan"], str)
            self.assertTrue(stub["source_plan"])
            for key in ("search_queries", "official_sources_to_check", "credible_news_sources_to_check"):
                self.assertIsInstance(stub[key], list)
                self.assertTrue(stub[key])
                self.assertTrue(all(isinstance(item, str) and item for item in stub[key]))

    def test_completion_status_is_always_stub_only(self):
        payload = json.loads(_run_json().stdout)
        self.assertTrue(payload["packet_stubs"])
        self.assertTrue(all(stub["completion_status"] == "stub_only" for stub in payload["packet_stubs"]))

    def test_evidence_slots_are_empty_placeholders(self):
        payload = json.loads(_run_json().stdout)
        for stub in payload["packet_stubs"]:
            self.assertIsInstance(stub["evidence_slots"], dict)
            self.assertTrue(stub["evidence_slots"])
            self.assertTrue(all(value == [] for value in stub["evidence_slots"].values()))

    def test_no_completed_dossier_order_or_trade_fields_in_stubs(self):
        payload = json.loads(_run_json().stdout)
        for stub in payload["packet_stubs"]:
            self.assertTrue(FORBIDDEN_STUB_FIELDS.isdisjoint(set(_walk_keys(stub))))

    def test_builder_reads_local_queue_artifact_only(self):
        module = _load_module(RUNNER, "research_packet_stubs_module")
        report = module.build_research_packet_stubs(str(QUEUE), limit=2)
        self.assertEqual(report["selected_market_ids"], ["569368", "569366"])
        self.assertEqual(report["queue_artifact_path"], str(QUEUE))
        self.assertTrue(report["safety_flags"]["offline_only"])
        self.assertFalse(report["safety_flags"]["api_used"])
        self.assertFalse(report["safety_flags"]["network_used"])
        self.assertFalse(report["safety_flags"]["wallet_used"])

    def test_no_runtime_network_wallet_or_live_order_behavior(self):
        source = RUNNER.read_text(encoding="utf-8").lower()
        forbidden = [
            "requests",
            "urllib.request",
            "socket",
            "websocket",
            "httpx",
            "aiohttp",
            "private_key",
            "submit_order",
            "execute_trade",
            "run_codex",
        ]
        for term in forbidden:
            self.assertNotIn(term, source)

    def test_standard_library_only(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "sys"})


if __name__ == "__main__":
    unittest.main()
