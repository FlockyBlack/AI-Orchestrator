import ast
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_threshold_hit_review_table.py"
EXPECTED_JSON = ROOT / "pm_bot" / "paper" / "expected_crypto_threshold_hit_review_table.v1.json"
EXPECTED_MD = ROOT / "pm_bot" / "paper" / "expected_crypto_threshold_hit_review_table.v1.md"
REFERENCE_CONTEXT = ROOT / "pm_bot" / "paper" / "threshold_hit_reference_context.v1.json"
DECISION_POLICY = ROOT / "pm_bot" / "paper" / "threshold_hit_decision_policy.v1.json"
REAL_SOURCE = ROOT / "local_snapshots" / "polymarket_markets_active_500_001.json"
THRESHOLD_TRIAGE_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_threshold_hit_triage_report.py"
REAL_TRIAGE_RUNNER = ROOT / "pm_bot" / "paper" / "run_real_market_triage_report.py"
OPERATOR_CYCLE_RUNNER = ROOT / "pm_bot" / "paper" / "run_manual_paper_operator_cycle.py"
LIFECYCLE_GATES_RUNNER = ROOT / "pm_bot" / "paper" / "run_crypto_numeric_lifecycle_regression_gates.py"
FIXTURE_WORKSPACE = ROOT / "pm_bot" / "paper" / "manual_paper_workspace"
SOURCE_SENTINEL = "embedded_crypto_threshold_hit_review_fixture"


def _frag(*parts):
    return "".join(parts)


def _fixture_rows():
    return [
        {
            "id": "fixture_bitcoin_hit_1m_before_event",
            "conditionId": "0xfixture_bitcoin_hit_1m_before_event",
            "question": "Will Bitcoin hit $1m before GTA VI?",
            "slug": "will-bitcoin-hit-1m-before-gta-vi",
            "active": True,
            "closed": False,
            "outcomes": "[\"Yes\", \"No\"]",
            "outcomePrices": "[\"0.490\", \"0.510\"]",
            "liquidity": 23456.0,
            "liquidityNum": 23456.0,
            "volumeNum": 60000.0,
            "bestBid": 0.48,
            "bestAsk": 0.5,
        },
        {
            "id": "fixture_btc_hit_150k_by_date",
            "conditionId": "0xfixture_btc_hit_150k_by_date",
            "question": "Will BTC hit $150k by June 30, 2026?",
            "slug": "will-btc-hit-150k-by-june-30-2026",
            "active": True,
            "closed": False,
            "outcomes": "[\"Yes\", \"No\"]",
            "outcomePrices": "[\"0.210\", \"0.790\"]",
            "liquidity": 12345.0,
            "liquidityNum": 12345.0,
            "volumeNum": 50000.0,
            "bestBid": 0.2,
            "bestAsk": 0.22,
        },
        {
            "id": "fixture_eth_reach_5000_by_date",
            "conditionId": "0xfixture_eth_reach_5000_by_date",
            "question": "Will ETH reach $5,000 by December 31, 2026?",
            "slug": "will-eth-reach-5000-by-december-31-2026",
            "active": True,
            "closed": False,
            "outcomes": "[\"Yes\", \"No\"]",
            "outcomePrices": "[\"0.330\", \"0.670\"]",
            "liquidity": 34567.0,
            "liquidityNum": 34567.0,
            "volumeNum": 70000.0,
            "bestBid": 0.32,
            "bestAsk": 0.34,
        },
    ]


def _run_json(*args):
    return subprocess.run([sys.executable, str(RUNNER), *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _run_markdown(*args):
    return subprocess.run([sys.executable, str(RUNNER), "--markdown", *args], cwd=ROOT, capture_output=True, text=True, check=True)


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_fixture(temp_dir):
    source = Path(temp_dir) / "crypto_threshold_hit_review_fixture.json"
    source.write_text(json.dumps(_fixture_rows(), indent=2), encoding="utf-8")
    return source


def _write_reference_context(temp_dir, assets):
    reference_context = Path(temp_dir) / "threshold_hit_reference_context.json"
    reference_context.write_text(
        json.dumps(
            {
                "schema_version": "threshold_hit_reference_context.v1",
                "captured_at": "2026-04-27T00:00:00Z",
                "assets": assets,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return reference_context


def _write_decision_policy(temp_dir, allow_paper_candidates):
    policy = Path(temp_dir) / "threshold_hit_decision_policy.json"
    policy.write_text(
        json.dumps(
            {
                "schema_version": "threshold_hit_decision_policy.v1",
                "decision_policy_version": "threshold_hit_decision_policy.test",
                "description": "Test-only deterministic threshold-hit decision policy.",
                "thresholds": {
                    "min_liquidity_for_review": 10000.0,
                    "max_yes_price_for_watchlist": 0.25,
                    "min_days_to_deadline_for_review": 7,
                    "max_distance_to_target_pct_for_watchlist": 75.0,
                },
                "allow_paper_candidates": allow_paper_candidates,
                "block_before_event_without_event_model": True,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return policy


def _normalized_payload(stdout, source):
    payload = json.loads(stdout)
    payload["source_path"] = SOURCE_SENTINEL
    return payload


def _normalized_markdown(stdout, source):
    return stdout.replace(str(source), SOURCE_SENTINEL)


def _fixture_file_snapshot():
    return {
        path.relative_to(FIXTURE_WORKSPACE).as_posix(): path.read_bytes()
        for path in sorted(FIXTURE_WORKSPACE.rglob("*"))
        if path.is_file()
    }


def _utf8_env():
    return {**os.environ, "PYTHONIOENCODING": "utf-8"}


class RunCryptoThresholdHitReviewTableTests(unittest.TestCase):
    def test_fixture_json_stdout_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            first = _run_json("--source", str(source)).stdout
            second = _run_json("--source", str(source)).stdout
            self.assertEqual(first, second)
            payload = _normalized_payload(first, source)
        self.assertEqual(payload, json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))
        self.assertEqual(payload["summary"]["paper_candidate_count"], 0)
        self.assertEqual(payload["summary"]["paper_orders_created"], 0)
        self.assertFalse(payload["summary"]["reference_context_used"])
        self.assertEqual(payload["summary"]["assets_with_reference_price"], [])

    def test_fixture_markdown_stdout_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            first = _run_markdown("--source", str(source)).stdout
            second = _run_markdown("--source", str(source)).stdout
            self.assertEqual(first, second)
            markdown = _normalized_markdown(first, source)
        self.assertEqual(markdown, EXPECTED_MD.read_text(encoding="utf-8"))

    def test_direct_builder_matches_expected_fixture(self):
        module = _load_module(RUNNER, "pmbot_test_crypto_threshold_hit_review")
        payload = module.build_crypto_threshold_hit_review_table(ROOT, SOURCE_SENTINEL, _fixture_rows())
        self.assertEqual(payload, json.loads(EXPECTED_JSON.read_text(encoding="utf-8")))

    def test_decision_policy_fixture_defaults_to_no_paper_candidates(self):
        policy = json.loads(DECISION_POLICY.read_text(encoding="utf-8"))
        self.assertFalse(policy["allow_paper_candidates"])
        self.assertTrue(policy["block_before_event_without_event_model"])

    def test_decision_policy_omitted_preserves_reference_context_behavior(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            payload = json.loads(_run_json(
                "--source",
                str(source),
                "--reference-context",
                str(REFERENCE_CONTEXT),
            ).stdout)
        self.assertEqual(payload["task_id"], "PMBOT-BRAIN-035-THRESHOLD-HIT-REFERENCE-CONTEXT")
        self.assertNotIn("decision_policy_used", payload["summary"])
        self.assertNotIn("policy_blocked_count", payload["summary"])
        for row in payload["rows"]:
            self.assertNotIn("decision_policy_version", row)
            self.assertNotIn("policy_checks", row)
        self.assertEqual(payload["summary"]["no_action_count"], 1)
        self.assertEqual(payload["summary"]["watchlist_count"], 2)
        self.assertEqual(payload["summary"]["paper_candidate_count"], 0)

    def test_reference_context_populates_btc_reference_fields(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            payload = json.loads(_run_json(
                "--source",
                str(source),
                "--reference-context",
                str(REFERENCE_CONTEXT),
            ).stdout)
        btc_rows = [row for row in payload["rows"] if row["asset"] == "BTC"]
        self.assertTrue(btc_rows)
        self.assertTrue(payload["summary"]["reference_context_used"])
        self.assertEqual(payload["summary"]["assets_with_reference_price"], ["BTC", "ETH"])
        for row in btc_rows:
            self.assertEqual(row["current_reference_price"], 100000.0)
            self.assertEqual(row["reference_price_captured_at"], "2026-04-27T00:00:00Z")
            self.assertEqual(row["reference_price_source"], "manual_offline_fixture")

    def test_reference_context_computes_deterministic_distance_and_multiple(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            payload = json.loads(_run_json(
                "--source",
                str(source),
                "--reference-context",
                str(REFERENCE_CONTEXT),
            ).stdout)
        by_date_btc = next(row for row in payload["rows"] if row["market_id"] == "fixture_btc_hit_150k_by_date")
        before_event_btc = next(row for row in payload["rows"] if row["market_type"] == "threshold_hit_before_event")
        eth = next(row for row in payload["rows"] if row["asset"] == "ETH")
        self.assertEqual(by_date_btc["distance_to_target_pct"], 50.0)
        self.assertEqual(by_date_btc["target_multiple"], 1.5)
        self.assertEqual(before_event_btc["distance_to_target_pct"], 900.0)
        self.assertEqual(before_event_btc["target_multiple"], 10.0)
        self.assertEqual(eth["distance_to_target_pct"], 100.0)
        self.assertEqual(eth["target_multiple"], 2.0)

    def test_reference_context_by_date_rows_are_reviewable_watchlist_not_paper_candidate(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            payload = json.loads(_run_json(
                "--source",
                str(source),
                "--reference-context",
                str(REFERENCE_CONTEXT),
            ).stdout)
        by_date_rows = [row for row in payload["rows"] if row["market_type"] == "threshold_hit_by_date"]
        self.assertTrue(by_date_rows)
        self.assertEqual(payload["summary"]["paper_candidate_count"], 0)
        self.assertEqual(payload["summary"]["paper_orders_created"], 0)
        for row in by_date_rows:
            self.assertEqual(row["model_assumption_status"], "reviewable")
            self.assertEqual(row["review_decision"], "watchlist")
            self.assertFalse(row["conservative_thresholds_pass"])
        by_date_btc = next(row for row in by_date_rows if row["market_id"] == "fixture_btc_hit_150k_by_date")
        self.assertIn("paper_candidate_disabled_pending_explicit_thresholds", by_date_btc["reason_codes"])

    def test_reference_context_before_event_still_requires_event_model(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            payload = json.loads(_run_json(
                "--source",
                str(source),
                "--reference-context",
                str(REFERENCE_CONTEXT),
            ).stdout)
        row = next(row for row in payload["rows"] if row["market_type"] == "threshold_hit_before_event")
        self.assertEqual(row["current_reference_price"], 100000.0)
        self.assertEqual(row["model_assumption_status"], "before_event_requires_event_model")
        self.assertEqual(row["review_decision"], "no_action")
        self.assertIn("before_event_requires_event_model", row["reason_codes"])
        self.assertNotIn("missing_reference_price", row["reason_codes"])

    def test_missing_asset_reference_still_yields_missing_reference_price(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            reference_context = _write_reference_context(
                temp_dir,
                {
                    "BTC": {
                        "reference_price": 100000.0,
                        "source": "manual_offline_fixture",
                    }
                },
            )
            payload = json.loads(_run_json(
                "--source",
                str(source),
                "--reference-context",
                str(reference_context),
            ).stdout)
        eth = next(row for row in payload["rows"] if row["asset"] == "ETH")
        self.assertIsNone(eth["current_reference_price"])
        self.assertEqual(eth["model_assumption_status"], "missing_reference_price")
        self.assertEqual(eth["review_decision"], "watchlist")
        self.assertIn("missing_reference_price", eth["reason_codes"])
        self.assertEqual(payload["summary"]["missing_assumption_reason_counts"], {"missing_reference_price": 1, "before_event_requires_event_model": 1})

    def test_decision_policy_applies_deterministic_checks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            payload = json.loads(_run_json(
                "--source",
                str(source),
                "--reference-context",
                str(REFERENCE_CONTEXT),
                "--decision-policy",
                str(DECISION_POLICY),
            ).stdout)
        self.assertEqual(payload["task_id"], "PMBOT-BRAIN-036-THRESHOLD-HIT-DECISION-POLICY")
        self.assertTrue(payload["summary"]["decision_policy_used"])
        self.assertEqual(payload["summary"]["decision_policy_version"], "threshold_hit_decision_policy.v1")
        self.assertEqual(payload["summary"]["paper_orders_created"], 0)
        self.assertEqual(payload["summary"]["paper_candidate_count"], 0)
        for row in payload["rows"]:
            self.assertEqual(row["decision_policy_version"], "threshold_hit_decision_policy.v1")
            self.assertTrue(row["policy_checks"])
            self.assertEqual(
                row["passed_policy_checks"],
                [check["name"] for check in row["policy_checks"] if check["passed"]],
            )
            self.assertEqual(
                row["failed_policy_checks"],
                [check["name"] for check in row["policy_checks"] if not check["passed"]],
            )
            self.assertEqual(row["reason_codes"], sorted(row["reason_codes"]))
            self.assertTrue(row["human_review_note"])

    def test_decision_policy_by_date_btc_rows_are_explainable_watchlist_or_blocked(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            payload = json.loads(_run_json(
                "--source",
                str(source),
                "--reference-context",
                str(REFERENCE_CONTEXT),
                "--decision-policy",
                str(DECISION_POLICY),
            ).stdout)
        btc_by_date = [
            row for row in payload["rows"]
            if row["asset"] == "BTC" and row["market_type"] == "threshold_hit_by_date"
        ]
        self.assertTrue(btc_by_date)
        for row in btc_by_date:
            self.assertIn(row["review_decision"], {"watchlist", "policy_blocked"})
            self.assertEqual(row["review_decision"], "watchlist")
            self.assertTrue(row["conservative_thresholds_pass"])
            self.assertEqual(row["failed_policy_checks"], ["allow_paper_candidates"])
            self.assertEqual(row["reason_codes"], ["paper_candidates_disabled_by_policy"])
            self.assertIn("deterministic offline checks pass", row["human_review_note"])

    def test_decision_policy_blocks_by_date_rows_that_fail_thresholds(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            payload = json.loads(_run_json(
                "--source",
                str(source),
                "--reference-context",
                str(REFERENCE_CONTEXT),
                "--decision-policy",
                str(DECISION_POLICY),
            ).stdout)
        eth = next(row for row in payload["rows"] if row["asset"] == "ETH")
        self.assertEqual(eth["review_decision"], "policy_blocked")
        self.assertFalse(eth["conservative_thresholds_pass"])
        self.assertIn("max_yes_price_for_watchlist", eth["failed_policy_checks"])
        self.assertIn("max_distance_to_target_pct_for_watchlist", eth["failed_policy_checks"])
        self.assertIn("yes_price_above_conservative_limit", eth["reason_codes"])
        self.assertIn("target_distance_above_watchlist_limit", eth["reason_codes"])

    def test_decision_policy_blocks_before_event_without_event_model(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            payload = json.loads(_run_json(
                "--source",
                str(source),
                "--reference-context",
                str(REFERENCE_CONTEXT),
                "--decision-policy",
                str(DECISION_POLICY),
            ).stdout)
        row = next(row for row in payload["rows"] if row["market_type"] == "threshold_hit_before_event")
        self.assertEqual(row["review_decision"], "policy_blocked")
        self.assertIn("before_event_event_model_present", row["failed_policy_checks"])
        self.assertIn("before_event_requires_event_model", row["reason_codes"])
        self.assertNotEqual(row["review_decision"], "paper_candidate")

    def test_decision_policy_allow_false_prevents_paper_candidate_even_when_checks_pass(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            policy = _write_decision_policy(temp_dir, allow_paper_candidates=False)
            payload = json.loads(_run_json(
                "--source",
                str(source),
                "--reference-context",
                str(REFERENCE_CONTEXT),
                "--decision-policy",
                str(policy),
            ).stdout)
        row = next(row for row in payload["rows"] if row["market_id"] == "fixture_btc_hit_150k_by_date")
        self.assertTrue(row["conservative_thresholds_pass"])
        self.assertEqual(row["review_decision"], "watchlist")
        self.assertEqual(row["failed_policy_checks"], ["allow_paper_candidates"])
        self.assertEqual(payload["summary"]["paper_candidate_count"], 0)
        self.assertEqual(payload["summary"]["paper_orders_created"], 0)

    def test_decision_policy_allow_true_can_label_fixture_paper_candidate_without_orders(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            policy = _write_decision_policy(temp_dir, allow_paper_candidates=True)
            before = _fixture_file_snapshot()
            payload = json.loads(_run_json(
                "--source",
                str(source),
                "--reference-context",
                str(REFERENCE_CONTEXT),
                "--decision-policy",
                str(policy),
            ).stdout)
        row = next(row for row in payload["rows"] if row["market_id"] == "fixture_btc_hit_150k_by_date")
        self.assertEqual(row["review_decision"], "paper_candidate")
        self.assertTrue(row["conservative_thresholds_pass"])
        self.assertEqual(row["failed_policy_checks"], [])
        self.assertEqual(row["reason_codes"], [])
        self.assertEqual(payload["summary"]["paper_candidate_count"], 1)
        self.assertEqual(payload["summary"]["paper_orders_created"], 0)
        self.assertNotIn("paper_orders", payload)
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_reference_context_json_stdout_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            first = _run_json("--source", str(source), "--reference-context", str(REFERENCE_CONTEXT)).stdout
            second = _run_json("--source", str(source), "--reference-context", str(REFERENCE_CONTEXT)).stdout
        self.assertEqual(first, second)

    def test_decision_policy_json_stdout_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            first = _run_json(
                "--source",
                str(source),
                "--reference-context",
                str(REFERENCE_CONTEXT),
                "--decision-policy",
                str(DECISION_POLICY),
            ).stdout
            second = _run_json(
                "--source",
                str(source),
                "--reference-context",
                str(REFERENCE_CONTEXT),
                "--decision-policy",
                str(DECISION_POLICY),
            ).stdout
        self.assertEqual(first, second)

    def test_reference_context_markdown_stdout_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            first = _run_markdown("--source", str(source), "--reference-context", str(REFERENCE_CONTEXT)).stdout
            second = _run_markdown("--source", str(source), "--reference-context", str(REFERENCE_CONTEXT)).stdout
        self.assertEqual(first, second)

    def test_decision_policy_markdown_stdout_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = _write_fixture(temp_dir)
            first = _run_markdown(
                "--source",
                str(source),
                "--reference-context",
                str(REFERENCE_CONTEXT),
                "--decision-policy",
                str(DECISION_POLICY),
            ).stdout
            second = _run_markdown(
                "--source",
                str(source),
                "--reference-context",
                str(REFERENCE_CONTEXT),
                "--decision-policy",
                str(DECISION_POLICY),
            ).stdout
        self.assertEqual(first, second)
        self.assertIn("- Decision policy used: true", first)
        self.assertIn("| market_id | question | asset | target | type | deadline | event | yes | implied_probability | liquidity | reference | reference_captured_at | reference_source | distance_pct | target_multiple | days | assumption_status | decision | policy_version | passed_policy_checks | failed_policy_checks | reason_codes | note |", first)

    def test_real_local_500_snapshot_command_runs(self):
        payload = json.loads(_run_json().stdout)
        summary = payload["summary"]
        self.assertEqual(payload["source_path"], str(REAL_SOURCE))
        self.assertEqual(summary["markets_seen"], 500)
        self.assertEqual(summary["threshold_hit_candidates"], 3)
        self.assertFalse(summary["reference_context_used"])
        self.assertEqual(summary["assets_with_reference_price"], [])
        self.assertEqual(summary["no_action_count"], 1)
        self.assertEqual(summary["watchlist_count"], 2)
        self.assertEqual(summary["paper_candidate_count"], 0)
        self.assertEqual(summary["paper_orders_created"], 0)
        self.assertEqual([row["market_id"] for row in payload["rows"]], ["540844", "573655", "573656"])
        self.assertEqual([row["review_decision"] for row in payload["rows"]], ["no_action", "watchlist", "watchlist"])

    def test_current_default_produces_no_paper_orders(self):
        before = _fixture_file_snapshot()
        payload = json.loads(_run_json().stdout)
        self.assertNotIn("paper_orders", payload)
        self.assertEqual(payload["summary"]["paper_orders_created"], 0)
        self.assertEqual(payload["summary"]["paper_candidate_count"], 0)
        self.assertEqual(_fixture_file_snapshot(), before)

    def test_missing_reference_price_prevents_paper_candidate(self):
        module = _load_module(RUNNER, "pmbot_test_crypto_threshold_hit_review_missing_ref")
        payload = module.build_crypto_threshold_hit_review_table(ROOT, SOURCE_SENTINEL, _fixture_rows())
        by_date_rows = [row for row in payload["rows"] if row["market_type"] == "threshold_hit_by_date"]
        self.assertTrue(by_date_rows)
        for row in by_date_rows:
            self.assertIsNone(row["current_reference_price"])
            self.assertEqual(row["model_assumption_status"], "missing_reference_price")
            self.assertEqual(row["review_decision"], "watchlist")
            self.assertIn("missing_reference_price", row["reason_codes"])
            self.assertNotEqual(row["review_decision"], "paper_candidate")

    def test_before_event_requires_event_model_by_default(self):
        payload = json.loads(_run_json().stdout)
        row = payload["rows"][0]
        self.assertEqual(row["market_type"], "threshold_hit_before_event")
        self.assertEqual(row["model_assumption_status"], "before_event_requires_event_model")
        self.assertFalse(row["event_model_fixture_present"])
        self.assertEqual(row["review_decision"], "no_action")
        self.assertIn("before_event_requires_event_model", row["reason_codes"])
        self.assertNotEqual(row["review_decision"], "paper_candidate")

    def test_threshold_hit_triage_report_still_passes(self):
        payload = json.loads(subprocess.run(
            [sys.executable, str(THRESHOLD_TRIAGE_RUNNER), "--source", str(REAL_SOURCE)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout)
        self.assertEqual(payload["summary"]["threshold_hit_crypto_candidates_found"], 3)
        self.assertEqual(payload["summary"]["supported_triage_candidates"], 3)
        subprocess.run(
            [sys.executable, str(THRESHOLD_TRIAGE_RUNNER), "--source", str(REAL_SOURCE), "--markdown"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )

    def test_real_market_triage_operator_and_lifecycle_still_pass(self):
        subprocess.run(
            [sys.executable, str(REAL_TRIAGE_RUNNER), "--source", str(REAL_SOURCE), "--markdown"],
            cwd=ROOT,
            env=_utf8_env(),
            capture_output=True,
            text=True,
            check=True,
        )
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

    def test_no_network_or_runtime_behavior(self):
        source = RUNNER.read_text(encoding="utf-8").lower()
        forbidden = [
            _frag("re", "quests"),
            _frag("urllib", ".", "request"),
            "socket",
            "websocket",
            "httpx",
            "aiohttp",
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
        self.assertLessEqual(imports, {"argparse", "datetime", "importlib", "json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
