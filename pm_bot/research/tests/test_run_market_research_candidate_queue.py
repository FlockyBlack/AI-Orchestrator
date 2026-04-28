import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "research" / "run_market_research_candidate_queue.py"
REAL_SOURCE = ROOT / "local_snapshots" / "polymarket_markets_active_500_001.json"
EXPECTED_JSON = ROOT / "pm_bot" / "research" / "expected_market_research_candidate_queue.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "research" / "expected_market_research_candidate_queue.v1.md"
SINGLE_DOSSIER_RUNNER = ROOT / "pm_bot" / "research" / "run_single_market_research_dossier.py"
SCENARIOS_RUNNER = ROOT / "pm_bot" / "research" / "run_research_dossier_scenarios.py"
OPERATOR_CYCLE_RUNNER = ROOT / "pm_bot" / "paper" / "run_manual_paper_operator_cycle.py"
LIFECYCLE_GATES_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_numeric_lifecycle_regression_gates.py"


def _frag(*parts):
    return "".join(parts)


def _run_json(*args):
    return subprocess.run([sys.executable, str(RUNNER), *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown(*args):
    return subprocess.run([sys.executable, str(RUNNER), "--markdown", *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _load_module(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _market(
    market_id,
    question,
    description,
    liquidity,
    yes_price,
    end_date,
    category="",
):
    return {
        "id": market_id,
        "question": question,
        "category": category,
        "description": description,
        "outcomes": json.dumps(["Yes", "No"]),
        "outcomePrices": json.dumps([str(yes_price), str(round(1.0 - yes_price, 4))]),
        "liquidity": str(liquidity),
        "endDate": end_date,
        "active": True,
        "closed": False,
    }


def _write_fixture(temp_dir, rows):
    path = Path(temp_dir) / "markets.json"
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


class RunMarketResearchCandidateQueueTests(unittest.TestCase):
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

    def test_top_n_option_limits_candidate_rows(self):
        payload = json.loads(_run_json("--top-n", "20").stdout)
        self.assertEqual(payload["top_n"], 20)
        self.assertEqual(payload["shortlist_top_n"], 10)
        self.assertEqual(len(payload["top_n_candidates"]), 20)
        self.assertEqual([row["rank"] for row in payload["top_n_candidates"]], list(range(1, 21)))
        for row in payload["top_n_candidates"]:
            self.assertIn("research_tier", row)
            self.assertIn("risk_tier", row)
            self.assertIn("uncertainty_reason_codes", row)
            self.assertIn("operator_shortlist", row)
            self.assertIn("shortlist_rank", row)
            self.assertIn("shortlist_score", row)
            self.assertIn("shortlist_reason_codes", row)
            self.assertIn("why_selected_for_research", row)
            self.assertIn("why_not_lower_risk", row)
            self.assertIn("why_not_bet_yet", row)

    def test_shortlist_n_option_limits_operator_shortlist_rows(self):
        payload = json.loads(_run_json("--shortlist-n", "5").stdout)
        self.assertEqual(payload["shortlist_top_n"], 5)
        self.assertEqual(payload["operator_shortlist_count"], 5)
        self.assertEqual(len(payload["operator_shortlist_candidates"]), 5)
        self.assertEqual([row["shortlist_rank"] for row in payload["operator_shortlist_candidates"]], list(range(1, 6)))
        self.assertTrue(all(row["operator_shortlist"] for row in payload["operator_shortlist_candidates"]))

    def test_real_saved_500_market_snapshot_command_runs(self):
        payload = json.loads(_run_json().stdout)
        self.assertEqual(payload["source_path"], str(REAL_SOURCE))
        self.assertEqual(payload["source_shape"], "polymarket_gamma_markets_response")
        self.assertEqual(payload["top_level_shape"], "top_level_list")
        self.assertEqual(payload["markets_seen"], 500)
        self.assertEqual(payload["total_markets_seen"], 500)
        self.assertEqual(
            payload["total_markets_seen"],
            payload["candidates_ranked"] + payload["rejected_count"],
        )
        self.assertEqual(payload["top_n"], 10)
        self.assertEqual(payload["shortlist_top_n"], 10)
        self.assertEqual(len(payload["top_n_candidates"]), 10)
        self.assertEqual(payload["operator_shortlist_count"], 10)
        self.assertEqual(payload["lower_risk_operator_shortlist_count"], 10)
        self.assertGreater(payload["researchable_high_uncertainty_count"], 0)
        self.assertGreater(payload["watch_only_count"], 0)
        self.assertLessEqual(payload["operator_shortlist_count"], payload["shortlist_top_n"])
        self.assertEqual(len(payload["shortlist_candidate_examples"]), 5)
        self.assertEqual(len(payload["lower_risk_shortlist_examples"]), 5)
        self.assertGreaterEqual(len(payload["high_uncertainty_examples"]), 5)
        self.assertIn("operator_shortlist_candidate", payload["shortlist_reason_code_counts"])

    def test_operator_shortlist_count_is_small_and_deterministic(self):
        first = json.loads(_run_json().stdout)
        second = json.loads(_run_json().stdout)
        self.assertEqual(first["operator_shortlist_count"], 10)
        self.assertEqual(second["operator_shortlist_count"], 10)
        self.assertEqual(first["lower_risk_operator_shortlist_count"], 10)
        self.assertEqual(first["operator_shortlist_candidates"], second["operator_shortlist_candidates"])
        self.assertLess(first["operator_shortlist_count"], first["high_priority_count"])

    def test_before_gta_vi_markets_are_not_lower_risk_shortlist_by_default(self):
        payload = json.loads(_run_json("--top-n", "20").stdout)
        shortlist_titles = [row["title"].lower() for row in payload["operator_shortlist_candidates"]]
        self.assertFalse(any("gta vi" in title for title in shortlist_titles))
        gta_rows = [row for row in payload["top_n_candidates"] if "gta vi" in row["title"].lower()]
        self.assertGreaterEqual(len(gta_rows), 3)
        for row in gta_rows:
            self.assertFalse(row["operator_shortlist"])
            self.assertEqual(row["research_tier"], "researchable_high_uncertainty")
            self.assertIn("before_gta_vi_meta_event", row["uncertainty_reason_codes"])

    def test_war_invasion_and_ceasefire_markets_are_not_lower_risk_shortlist(self):
        payload = json.loads(_run_json("--top-n", "40").stdout)
        tail_rows = [
            row
            for row in payload["top_n_candidates"]
            if any(term in row["title"].lower() for term in ("ceasefire", "invade", "invasion", "war"))
        ]
        self.assertGreaterEqual(len(tail_rows), 3)
        for row in tail_rows:
            self.assertFalse(row["operator_shortlist"])
            self.assertIn(row["research_tier"], {"researchable_high_uncertainty", "watch_only"})
            self.assertIn("war_invasion_or_ceasefire_tail_risk", row["uncertainty_reason_codes"])

    def test_long_horizon_sports_markets_are_downranked_or_rejected(self):
        module = _load_module(RUNNER, "candidate_queue_module_sports")
        rows = [
            _market(
                "sports_future",
                "Will the New York Knicks win the 2028 NBA Finals?",
                "This market resolves Yes if the team wins the 2028 NBA Finals according to official league results.",
                500000,
                0.42,
                "2028-07-01T00:00:00Z",
            )
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_fixture(temp_dir, rows)
            report = module.build_candidate_queue(str(path), top_n=1)
        row = report["top_n_candidates"][0] if report["top_n_candidates"] else report["top_n_candidates"]
        all_rows = report["reason_code_counts"]
        self.assertIn("sports_long_horizon_downranked", all_rows)
        if row:
            self.assertIn(row["research_priority"], {"low", "reject"})
            self.assertLess(row["final_research_priority_score"], 0.55)
        else:
            self.assertEqual(report["rejected_count"], 1)

    def test_clear_diplomatic_legal_or_political_markets_rank_above_generic_sports_futures(self):
        rows = [
            _market(
                "diplomatic_clear",
                "Russia-Ukraine ceasefire by June 30, 2026?",
                "This market will resolve to Yes if official announcements from both governments or wide consensus credible media report a ceasefire by the deadline.",
                100000,
                0.47,
                "2026-06-30T00:00:00Z",
            ),
            _market(
                "legal_clear",
                "SCOTUS accepts sports event contract case by July 31, 2026?",
                "This market resolves Yes if the Supreme Court docket or an official order list shows the case accepted before the deadline.",
                75000,
                0.32,
                "2026-07-31T00:00:00Z",
            ),
            _market(
                "sports_future",
                "Will the Boston Celtics win the 2027 NBA Finals?",
                "This market resolves Yes if the team wins the 2027 NBA Finals according to official league results.",
                600000,
                0.48,
                "2027-07-01T00:00:00Z",
            ),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_fixture(temp_dir, rows)
            payload = json.loads(_run_json("--source", str(path), "--top-n", "3").stdout)
        ranked_ids = [row["market_id"] for row in payload["top_n_candidates"]]
        if "sports_future" in ranked_ids:
            self.assertLess(ranked_ids.index("diplomatic_clear"), ranked_ids.index("sports_future"))
            self.assertLess(ranked_ids.index("legal_clear"), ranked_ids.index("sports_future"))
        else:
            self.assertEqual(payload["rejected_count"], 1)
            self.assertIn("sports_long_horizon_downranked", payload["reason_code_counts"])
        self.assertEqual(payload["top_n_candidates"][0]["research_priority"], "high")

    def test_long_horizon_primaries_are_downranked_without_near_term_catalyst(self):
        rows = [
            _market(
                "political_long_horizon",
                "Will Jane Example win the 2028 Republican presidential primary?",
                "This market resolves according to certified official primary and convention results.",
                500000,
                0.45,
                "2028-11-07T00:00:00Z",
            ),
            _market(
                "legal_near_catalyst",
                "SCOTUS accepts Example emergency appeal by June 30, 2026?",
                "This market resolves Yes if the Supreme Court docket or an official order list shows the appeal accepted before the deadline.",
                60000,
                0.43,
                "2026-06-30T00:00:00Z",
            ),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_fixture(temp_dir, rows)
            payload = json.loads(_run_json("--source", str(path), "--top-n", "2", "--shortlist-n", "1").stdout)
        by_id = {row["market_id"]: row for row in payload["top_n_candidates"]}
        self.assertIn(by_id["political_long_horizon"]["research_priority"], {"high", "medium", "low"})
        self.assertFalse(by_id["political_long_horizon"]["operator_shortlist"])
        self.assertIn("long_horizon_election_or_primary", by_id["political_long_horizon"]["uncertainty_reason_codes"])
        self.assertIn("primary_market_uncertainty", by_id["political_long_horizon"]["uncertainty_reason_codes"])
        self.assertIn("shortlist_primary_market_no_near_term_catalyst", by_id["political_long_horizon"]["shortlist_reason_codes"])
        self.assertIn("shortlist_long_horizon_primary_or_election_downranked", by_id["political_long_horizon"]["shortlist_reason_codes"])
        self.assertEqual(payload["operator_shortlist_count"], 1)
        self.assertEqual(payload["operator_shortlist_candidates"][0]["market_id"], "legal_near_catalyst")

    def test_clear_lower_ambiguity_markets_can_enter_lower_risk_shortlist(self):
        rows = [
            _market(
                "crypto_clear",
                "Will Bitcoin hit $120k by July 31, 2026?",
                "This market resolves Yes if official exchange pricing or credible market data reports Bitcoin above the threshold before the deadline.",
                250000,
                0.48,
                "2026-07-31T00:00:00Z",
            ),
            _market(
                "diplomatic_clear",
                "Will the US announce a tariff exemption by June 30, 2026?",
                "This market resolves Yes if an official government announcement or credible media reports the tariff exemption before the deadline.",
                100000,
                0.47,
                "2026-06-30T00:00:00Z",
            ),
            _market(
                "legal_clear",
                "SCOTUS accepts Example emergency appeal by July 31, 2026?",
                "This market resolves Yes if the Supreme Court docket or an official order list shows the appeal accepted before the deadline.",
                75000,
                0.32,
                "2026-07-31T00:00:00Z",
            ),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_fixture(temp_dir, rows)
            payload = json.loads(_run_json("--source", str(path), "--top-n", "3", "--shortlist-n", "3").stdout)
        shortlist_ids = {row["market_id"] for row in payload["operator_shortlist_candidates"]}
        self.assertEqual(shortlist_ids, {"crypto_clear", "diplomatic_clear", "legal_clear"})
        self.assertEqual(payload["operator_shortlist_count"], 3)
        self.assertEqual(payload["lower_risk_operator_shortlist_count"], 3)
        self.assertTrue(all(row["research_tier"] == "lower_risk_operator_shortlist" for row in payload["operator_shortlist_candidates"]))

    def test_broad_researchable_queue_remains_available_with_high_uncertainty_tier(self):
        payload = json.loads(_run_json("--top-n", "20").stdout)
        self.assertEqual(payload["candidates_ranked"], 148)
        self.assertGreater(payload["researchable_high_uncertainty_count"], payload["lower_risk_operator_shortlist_count"])
        self.assertTrue(payload["high_uncertainty_examples"])
        high_uncertainty_ids = {row["market_id"] for row in payload["high_uncertainty_examples"]}
        self.assertIn("540844", high_uncertainty_ids)

    def test_low_liquidity_and_unclear_markets_are_penalized(self):
        rows = [
            _market(
                "low_liquidity_clear",
                "Will a named bill pass Congress by May 31, 2026?",
                "This market resolves according to official congressional records and public law publication before the deadline.",
                900,
                0.5,
                "2026-05-31T00:00:00Z",
            ),
            _market(
                "unclear_meme",
                "Will Jesus Christ return before GTA VI?",
                "This market has unclear religious resolution criteria and no reliable official resolution source.",
                900000,
                0.5,
                "2026-07-31T00:00:00Z",
            ),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_fixture(temp_dir, rows)
            payload = json.loads(_run_json("--source", str(path), "--top-n", "2").stdout)
        self.assertEqual(payload["candidates_ranked"], 0)
        self.assertEqual(payload["rejected_count"], 2)
        self.assertEqual(payload["reason_code_counts"]["low_liquidity"], 1)
        self.assertEqual(payload["reason_code_counts"]["unclear_meme_or_religious_rejected"], 1)

    def test_low_liquidity_researchable_market_is_excluded_from_shortlist(self):
        rows = [
            _market(
                "thin_legal",
                "SCOTUS accepts thin-liquidity appeal by May 31, 2026?",
                "This market resolves Yes if the Supreme Court docket or an official order list shows the appeal accepted before the deadline.",
                8000,
                0.46,
                "2026-05-31T00:00:00Z",
            ),
            _market(
                "unclear_meme",
                "Will Jesus Christ return before GTA VI?",
                "This market has unclear religious resolution criteria and no reliable official resolution source.",
                900000,
                0.5,
                "2026-07-31T00:00:00Z",
            ),
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            path = _write_fixture(temp_dir, rows)
            payload = json.loads(_run_json("--source", str(path), "--top-n", "2", "--shortlist-n", "2").stdout)
        self.assertEqual(payload["candidates_ranked"], 1)
        self.assertEqual(payload["operator_shortlist_count"], 0)
        row = payload["top_n_candidates"][0]
        self.assertEqual(row["market_id"], "thin_legal")
        self.assertFalse(row["operator_shortlist"])
        self.assertIn("shortlist_low_liquidity_excluded", row["shortlist_reason_codes"])

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

    def test_no_runtime_network_wallet_state_or_live_order_behavior(self):
        source = RUNNER.read_text(encoding="utf-8").lower()
        forbidden = [
            _frag("re", "quests"),
            _frag("urllib", ".", "request"),
            "socket",
            "websocket",
            "httpx",
            "aiohttp",
            _frag("run", "_", "codex"),
            _frag("private", "_", "key"),
            _frag("submit", "_", "order"),
            _frag("execute", "_", "trade"),
            _frag("paper", "_", "order", "_", "plan"),
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
        self.assertLessEqual(imports, {"argparse", "collections", "datetime", "json", "pathlib", "re", "sys"})

    def test_existing_research_and_paper_regression_commands_still_pass(self):
        single = json.loads(subprocess.run(
            [sys.executable, str(SINGLE_DOSSIER_RUNNER)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout)
        scenarios = json.loads(subprocess.run(
            [sys.executable, str(SCENARIOS_RUNNER)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout)
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
        self.assertEqual(single["decision"], "paper_candidate")
        self.assertTrue(scenarios["all_expected_decisions_passed"])
        self.assertEqual(operator["summary"]["new_paper_orders_created"], 0)
        self.assertEqual(gates["status"], "passed")


if __name__ == "__main__":
    unittest.main()
