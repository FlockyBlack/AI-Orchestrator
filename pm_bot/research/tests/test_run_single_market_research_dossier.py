import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "research" / "run_single_market_research_dossier.py"
PACKET = ROOT / "pm_bot" / "research" / "single_market_research_packet.v1.json"
EXPECTED_JSON = ROOT / "pm_bot" / "research" / "expected_single_market_research_dossier.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "research" / "expected_single_market_research_dossier.v1.md"
OPERATOR_CYCLE_RUNNER = ROOT / "pm_bot" / "paper" / "run_manual_paper_operator_cycle.py"
LIFECYCLE_GATES_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_numeric_lifecycle_regression_gates.py"


def _frag(*parts):
    return "".join(parts)


def _run_json(*args):
    return subprocess.run([sys.executable, str(RUNNER), *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown(*args):
    return subprocess.run([sys.executable, str(RUNNER), "--markdown", *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _base_packet():
    return json.loads(PACKET.read_text(encoding="utf-8"))


def _write_packet(temp_dir, payload):
    path = Path(temp_dir) / "packet.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def _source(source_id, source_type, note, reliability_hint="high primary source"):
    return {
        "source_id": source_id,
        "source_type": source_type,
        "title": f"{source_id} title",
        "url": f"https://example.org/manual-fixtures/{source_id}",
        "published_at": "2026-04-27",
        "excerpt_or_note": note,
        "reliability_hint": reliability_hint,
    }


class RunSingleMarketResearchDossierTests(unittest.TestCase):
    def test_json_output_is_deterministic_and_matches_expected(self):
        first = _run_json().stdout
        second = _run_json().stdout
        self.assertEqual(first, second)
        self.assertEqual(json.loads(first), json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_markdown_output_is_deterministic_and_matches_expected(self):
        first = _run_markdown().stdout
        second = _run_markdown().stdout
        self.assertEqual(first, second)
        self.assertEqual(first, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_missing_resolution_criteria_blocks_paper_candidate(self):
        payload = _base_packet()
        payload["resolution_criteria"] = ""
        with tempfile.TemporaryDirectory() as temp_dir:
            packet = _write_packet(temp_dir, payload)
            result = json.loads(_run_json("--packet", str(packet)).stdout)
        self.assertEqual(result["decision"], "no_action")
        self.assertIn("missing_resolution_criteria", result["reason_codes"])
        self.assertEqual(result["paper_orders_created"], 0)

    def test_weak_sources_block_paper_candidate(self):
        payload = _base_packet()
        payload["sources"] = [
            _source("weak_social_yes", "social", "[YES] Anonymous social post claims approval is likely.", "low unverified social source"),
            _source("weak_other_no", "other", "[NO] Unverified forum note claims the schedule may slip.", "low rumor source"),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            packet = _write_packet(temp_dir, payload)
            result = json.loads(_run_json("--packet", str(packet)).stdout)
        self.assertEqual(result["decision"], "no_action")
        self.assertIn("weak_sources", result["reason_codes"])
        self.assertEqual(result["summary"]["paper_orders_created"], 0)

    def test_overlapping_probability_range_blocks_paper_candidate(self):
        payload = _base_packet()
        payload["yes_price"] = 0.5
        payload["no_price"] = 0.5
        payload["sources"] = [
            _source("official_yes", "official_statement", "[YES] Official schedule still lists certification before the deadline."),
            _source("court_no", "court_record", "[NO] Court docket shows a pending procedural challenge."),
            _source("news_yes", "news", "[YES] Reputable local reporting says leadership expects passage.", "medium corroborated reporting"),
            _source("analysis_no", "analysis", "[NO] Scenario analysis says bond counsel review may delay publication.", "medium scenario analysis"),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            packet = _write_packet(temp_dir, payload)
            result = json.loads(_run_json("--packet", str(packet)).stdout)
        self.assertEqual(result["decision"], "watchlist")
        self.assertTrue(result["edge_estimate_vs_market"]["range_overlaps_market"])
        self.assertIn("probability_range_overlaps_market", result["reason_codes"])
        self.assertEqual(result["paper_orders_created"], 0)

    def test_strong_fixture_evidence_can_label_candidate_without_orders(self):
        result = json.loads(_run_json().stdout)
        self.assertIn(result["decision"], {"watchlist", "paper_candidate"})
        self.assertEqual(result["decision"], "paper_candidate")
        self.assertEqual(result["summary"]["yes_evidence_count"], 3)
        self.assertEqual(result["summary"]["no_evidence_count"], 1)
        self.assertEqual(result["paper_orders_created"], 0)
        self.assertFalse(result["workspace_state_written"])
        self.assertNotIn("paper_orders", result)

    def test_existing_paper_commands_still_pass(self):
        operator = json.loads(subprocess.run(
            [sys.executable, str(OPERATOR_CYCLE_RUNNER)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout)
        gates = json.loads(subprocess.run(
            [sys.executable, str(LIFECYCLE_GATES_RUNNER)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout)
        self.assertTrue(operator["safety_flags"]["offline_only"])
        self.assertEqual(operator["summary"]["new_paper_orders_created"], 0)
        self.assertEqual(gates["status"], "passed")

    def test_safety_flags_remain_locked_down(self):
        payload = json.loads(_run_json().stdout)
        flags = payload["safety_flags"]
        self.assertTrue(flags["offline_only"])
        self.assertTrue(flags["paper_only"])
        for key in (
            "live_fetcher_implemented",
            "api_used",
            "network_used",
            "wallet_used",
            "real_order_created",
            "trading_allowed",
            "runtime_wiring_changed",
            "dispatcher_touched",
            "prompt_automation_added",
        ):
            self.assertFalse(flags[key])

    def test_no_runtime_network_wallet_or_live_order_behavior(self):
        source = RUNNER.read_text(encoding="utf-8").lower()
        forbidden = [
            _frag("re", "quests"),
            _frag("urllib", ".", "request"),
            "socket",
            _frag("run", "_", "codex"),
            _frag("private", "_", "key"),
            _frag("submit", "_", "order"),
            _frag("execute", "_", "trade"),
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
        self.assertLessEqual(imports, {"argparse", "json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
