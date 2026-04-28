import ast
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EXPORTER = ROOT / "pm_bot" / "paper" / "export_paper_run_series_postmortem.py"
PAPER_019_OUTPUT = ROOT / "pm_bot" / "paper" / "multi_market_paper_run_series.v1.json"
OUTPUT = ROOT / "pm_bot" / "paper" / "paper_run_series_postmortem.v1.json"
OUTPUT_MD = ROOT / "pm_bot" / "paper" / "paper_run_series_postmortem.v1.md"
EXPECTED = ROOT / "pm_bot" / "paper" / "expected_paper_run_series_postmortem.v1.json"
RESULT = ROOT / "docs" / "PMBOT_PAPER_020_RESULT.json"

NEW_JSON_FILES = [OUTPUT, EXPECTED, RESULT]
ACCOUNTING_ONLY_WARNING = (
    "PAPER-019 PnL is accounting-only fixture output, not strategy profitability; "
    "it is not a recommendation, edge, EV, probability estimate, market score, "
    "or market truth evidence."
)


def _frag(*parts):
    return "".join(parts)


def _run_exporter():
    return subprocess.run([sys.executable, str(EXPORTER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_module():
    spec = importlib.util.spec_from_file_location("paper_run_series_postmortem", EXPORTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _walk_keys(value, prefix=""):
    if isinstance(value, dict):
        for key, nested in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield path, str(key)
            yield from _walk_keys(nested, path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk_keys(item, f"{prefix}[{index}]")


class PaperRunSeriesPostmortemTests(unittest.TestCase):
    def test_exporter_writes_deterministic_json_markdown_and_expected_fixture(self):
        first_stdout = _run_exporter().stdout
        first_payloads = {path: _load_json(path) for path in NEW_JSON_FILES}
        first_markdown = OUTPUT_MD.read_text(encoding="utf-8")
        second_stdout = _run_exporter().stdout
        second_payloads = {path: _load_json(path) for path in NEW_JSON_FILES}
        second_markdown = OUTPUT_MD.read_text(encoding="utf-8")

        self.assertEqual(first_stdout, second_stdout)
        self.assertEqual(first_payloads, second_payloads)
        self.assertEqual(first_markdown, second_markdown)
        self.assertTrue(OUTPUT.exists())
        self.assertTrue(OUTPUT_MD.exists())
        self.assertEqual(_load_json(OUTPUT), _load_json(EXPECTED))
        for path in NEW_JSON_FILES:
            self.assertIsInstance(_load_json(path), dict)

    def test_postmortem_reads_paper_019_output_and_preserves_summary_counts(self):
        _run_exporter()
        postmortem = _load_json(OUTPUT)
        paper_019 = _load_json(PAPER_019_OUTPUT)

        self.assertEqual(postmortem["schema_version"], "paper_run_series_postmortem.v1")
        self.assertEqual(postmortem["postmortem_status"], "postmortem_completed")
        self.assertEqual(postmortem["paper_019_summary"]["source_schema_version"], paper_019["schema_version"])
        self.assertEqual(postmortem["paper_019_summary"]["series_status"], paper_019["series_status"])
        self.assertEqual(postmortem["paper_019_summary"]["markets_seen"], paper_019["markets_seen"])
        self.assertEqual(postmortem["paper_019_summary"]["records_seen"], paper_019["records_seen"])
        self.assertEqual(postmortem["paper_019_summary"]["records_processed"], paper_019["records_processed"])
        self.assertEqual(postmortem["records_by_status"], paper_019["records_by_status"])

    def test_accounting_pnl_and_warning_match_paper_019(self):
        _run_exporter()
        postmortem = _load_json(OUTPUT)
        paper_019 = _load_json(PAPER_019_OUTPUT)
        markdown = OUTPUT_MD.read_text(encoding="utf-8")
        result = _load_json(RESULT)

        self.assertEqual(
            postmortem["accounting_interpretation"]["cumulative_pnl"],
            paper_019["accounting_summary"]["paper_accounting_cumulative_pnl"],
        )
        self.assertEqual(postmortem["accounting_interpretation"]["cumulative_pnl"], "-1.00")
        self.assertEqual(postmortem["accounting_interpretation"]["warning"], ACCOUNTING_ONLY_WARNING)
        self.assertIn(ACCOUNTING_ONLY_WARNING, markdown)
        self.assertTrue(result["postmortem_summary"]["accounting_only_warning_present"])
        self.assertEqual(result["postmortem_summary"]["cumulative_pnl"], "-1.00")

    def test_safety_counters_remain_zero(self):
        _run_exporter()
        postmortem = _load_json(OUTPUT)
        result = _load_json(RESULT)
        expected = {
            "real_orders_created": 0,
            "autonomous_paper_orders": 0,
            "network_calls": 0,
            "commands_executed": 0,
            "autonomous_decisions": 0,
        }

        self.assertEqual(postmortem["safety_counters"], expected)
        self.assertEqual(result["safety_counters"], expected)
        self.assertFalse(postmortem["safety_flags"]["network_api"])
        self.assertFalse(postmortem["safety_flags"]["trading"])
        self.assertFalse(postmortem["safety_flags"]["autonomous_paper_orders"])
        self.assertFalse(postmortem["safety_flags"]["truth_inference"])
        self.assertFalse(postmortem["safety_flags"]["dashboard_server"])

    def test_blocked_and_manual_review_records_are_described(self):
        _run_exporter()
        postmortem = _load_json(OUTPUT)
        markdown = OUTPUT_MD.read_text(encoding="utf-8")

        self.assertEqual(len(postmortem["accepted_record_summary"]), 3)
        self.assertEqual(len(postmortem["manual_review_record_summary"]), 1)
        self.assertEqual(len(postmortem["blocked_record_summary"]), 1)
        manual = postmortem["manual_review_record_summary"][0]
        blocked = postmortem["blocked_record_summary"][0]
        self.assertEqual(manual["record_id"], "paper-run-series-record-004")
        self.assertEqual(manual["processing_status"], "manual_review_only")
        self.assertTrue(manual["accounting_included"])
        self.assertEqual(blocked["record_id"], "paper-run-series-record-005")
        self.assertEqual(blocked["processing_status"], "blocked_fixture_record")
        self.assertFalse(blocked["accounting_included"])
        self.assertIn("manual_review_only", markdown)
        self.assertIn("blocked_fixture_record", markdown)
        self.assertIn("operator_manual_accounting_values_not_accepted", markdown)

    def test_no_active_strategy_probability_ev_edge_or_market_decision_fields_are_introduced(self):
        _run_exporter()
        payloads = [_load_json(OUTPUT), _load_json(EXPECTED), _load_json(RESULT)]
        blocked_exact = {
            "probability",
            "implied_probability",
            "fair_probability",
            "ev",
            "expected_value",
            "edge",
            "score",
            "confidence_score",
            "strategy",
            "recommendation",
            "trade_recommendation",
            "decision",
            "trade_decision",
            "bot_decision",
            "generated_side",
            "generated_price",
            "generated_size",
            "auto_side",
            "auto_price",
            "auto_size",
            "market_decision",
        }
        allowed_paths = {
            "recommended_next_fixture_expansions",
            "postmortem_summary.recommended_next_fixture_expansions",
            "safety.scoring_probability_ev_edge",
            "safety_flags.scoring_probability_ev_edge",
        }
        failures = []
        for payload in payloads:
            for path, key in _walk_keys(payload):
                if path in allowed_paths or path.startswith("source_artifacts"):
                    continue
                if ".safety_flags." in path or path.startswith("safety_flags."):
                    continue
                if ".safety." in path or path.startswith("safety."):
                    continue
                if key.lower() in blocked_exact:
                    failures.append(path)
        self.assertEqual(failures, [])

    def test_blocked_generation_for_missing_paper_019_output(self):
        module = _load_module()
        source_artifacts = module._source_artifacts()
        missing_path = ROOT / "pm_bot" / "paper" / "missing_paper_019_fixture.json"
        postmortem = module._blocked_postmortem(source_artifacts, missing_path, "missing source")

        self.assertEqual(postmortem["postmortem_status"], "postmortem_blocked")
        self.assertEqual(postmortem["paper_019_summary"]["records_seen"], 0)
        self.assertEqual(postmortem["safety_counters"]["network_calls"], 0)
        self.assertEqual(postmortem["accounting_interpretation"]["warning"], ACCOUNTING_ONLY_WARNING)

    def test_standard_library_only(self):
        tree = ast.parse(EXPORTER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "sys"})

    def test_no_runtime_network_order_or_dispatcher_terms_in_exporter_source(self):
        source = EXPORTER.read_text(encoding="utf-8").lower().replace(" ", "")
        forbidden_terms = [
            _frag("import", "requests"),
            _frag("requests", "."),
            _frag("urllib", ".", "request"),
            _frag("websocket", "."),
            _frag("socket", "."),
            _frag("submit", "_", "order", "("),
            _frag("execute", "_", "trade", "("),
            _frag("place", "_", "order", "("),
            _frag("scripts", "/", "dispatcher", ".", "py"),
            _frag("scripts", "/", "run", "_", "codex", ".", "py"),
        ]
        for term in forbidden_terms:
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()
