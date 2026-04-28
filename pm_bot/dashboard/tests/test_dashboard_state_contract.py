import ast
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "dashboard" / "export_dashboard_state_contract.py"
CONTRACT = ROOT / "pm_bot" / "dashboard" / "dashboard_state_contract.v1.json"
PREVIEW_JSON = ROOT / "pm_bot" / "dashboard" / "dashboard_state_preview.v1.json"
PREVIEW_MD = ROOT / "pm_bot" / "dashboard" / "dashboard_state_preview.v1.md"
EXPECTED_PREVIEW_JSON = ROOT / "pm_bot" / "dashboard" / "expected_dashboard_state_preview.v1.json"

NEW_JSON_FILES = [
    CONTRACT,
    PREVIEW_JSON,
    EXPECTED_PREVIEW_JSON,
]

FORBIDDEN_IMPORTS = {
    "aiohttp",
    "django",
    "fastapi",
    "flask",
    "httpx",
    "requests",
    "selenium",
    "socket",
    "urllib",
    "webbrowser",
    "websockets",
}


def _frag(*parts):
    return "".join(parts)


def _run_write():
    return subprocess.run(
        [sys.executable, str(RUNNER), "--write"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _run_json():
    return subprocess.run(
        [sys.executable, str(RUNNER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _run_markdown():
    return subprocess.run(
        [sys.executable, str(RUNNER), "--markdown"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_module():
    spec = importlib.util.spec_from_file_location("dashboard_state_contract", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class DashboardStateContractTests(unittest.TestCase):
    def test_write_exports_contract_preview_markdown_and_expected_fixture(self):
        result = json.loads(_run_write().stdout)

        self.assertEqual(result["status"], "dashboard_state_contract_exported")
        self.assertEqual(result["market_ids"], ["824952"])
        for path in NEW_JSON_FILES:
            self.assertIsInstance(_load_json(path), dict)
        self.assertTrue(PREVIEW_MD.exists())

    def test_preview_json_matches_expected_fixture_and_default_stdout(self):
        _run_write()
        preview = _load_json(PREVIEW_JSON)
        expected = _load_json(EXPECTED_PREVIEW_JSON)
        stdout_preview = json.loads(_run_json().stdout)

        self.assertEqual(preview, expected)
        self.assertEqual(stdout_preview, expected)

    def test_contract_declares_required_dashboard_state_fields(self):
        _run_write()
        contract = _load_json(CONTRACT)
        module = _load_module()

        self.assertEqual(contract, module.build_dashboard_state_contract())
        self.assertEqual(contract["$id"], "PMBOT_DASHBOARD_STATE_CONTRACT.v1")
        self.assertFalse(contract["contract_boundary"]["dashboard_runtime_defined"])
        self.assertFalse(contract["contract_boundary"]["network_or_api_defined"])
        self.assertFalse(contract["contract_boundary"]["trading_or_ordering_defined"])
        self.assertIn("paper_accounting_summary", contract["required"])
        self.assertIn("forbidden_capabilities", contract["required"])

    def test_preview_contains_only_local_contract_state_and_required_warnings(self):
        _run_write()
        preview = _load_json(PREVIEW_JSON)

        self.assertEqual(preview["schema_version"], "dashboard_state_preview.v1")
        self.assertEqual(preview["generated_by"], "pm_bot/dashboard/export_dashboard_state_contract.py")
        self.assertFalse(preview["generated_at_policy"]["wall_clock_time_used"])
        self.assertEqual(preview["market_ids"], ["824952"])
        self.assertEqual(
            preview["product_stage_summary"]["paper_accounting_stage"]["current_known_paper_status"],
            "paper_portfolio_metrics_accepted_for_git_readiness_stage",
        )

        accounting = preview["paper_accounting_summary"]
        self.assertEqual(accounting["ledger_status"], "paper_accounting_ledger_history_ready")
        self.assertEqual(accounting["portfolio_status"], "paper_portfolio_snapshot_ready")
        self.assertEqual(accounting["metrics_report_status"], "paper_metrics_report_ready")
        self.assertEqual(accounting["paper_accounting_metrics"]["paper_accounting_cumulative_pnl"], "6.00")
        self.assertTrue(accounting["accounting_boundary"]["paper_accounting_only"])
        self.assertTrue(accounting["accounting_boundary"]["operator_manual_fixture_source"])
        self.assertFalse(accounting["accounting_boundary"]["strategy_profitability"])
        self.assertIn("not strategy profitability", accounting["accounting_boundary"]["warning"])

        self.assertIn(
            "This snapshot does not recommend a side, size, price, market, or trade.",
            preview["interpretation_warnings"],
        )
        self.assertIn(
            "This snapshot does not contain probability estimates, EV, edge, market scoring, truth inference, live prices, or live fetch results.",
            preview["interpretation_warnings"],
        )

    def test_artifact_pointers_and_safety_flags_are_explicit(self):
        _run_write()
        preview = _load_json(PREVIEW_JSON)
        pointers = preview["latest_artifact_pointers"]

        self.assertEqual(pointers["paper_accounting_ledger_json"]["path"], "pm_bot/paper/paper_accounting_ledger.v1.json")
        self.assertEqual(pointers["paper_metrics_report_json"]["path"], "pm_bot/paper/paper_metrics_report.v1.json")
        self.assertEqual(pointers["integration_003_result"]["path"], "docs/PMBOT_INTEGRATION_003_RESULT.json")
        self.assertTrue(all(pointer["present"] for pointer in pointers.values() if pointer["required"]))

        safety = preview["safety_flags"]
        self.assertFalse(safety["dashboard_runtime"])
        self.assertFalse(safety["server"])
        self.assertFalse(safety["frontend"])
        self.assertFalse(safety["browser_automation"])
        self.assertFalse(safety["runtime_wiring"])
        self.assertFalse(safety["network_api"])
        self.assertFalse(safety["wallet"])
        self.assertFalse(safety["trading"])
        self.assertFalse(safety["autonomous_paper_orders"])
        self.assertFalse(safety["scoring_probability_ev_edge"])
        self.assertFalse(safety["market_decisions"])
        self.assertFalse(preview["no_autonomous_decision_status"]["autonomous_selection_enabled"])
        self.assertFalse(preview["no_autonomous_decision_status"]["paper_order_generation_enabled"])

    def test_markdown_preview_matches_cli_output(self):
        _run_write()
        self.assertEqual(_run_markdown().stdout, PREVIEW_MD.read_text(encoding="utf-8"))
        self.assertIn("PMBOT Dashboard State Preview v1", PREVIEW_MD.read_text(encoding="utf-8"))
        self.assertIn("Paper accounting PnL is fixture/manual accounting only", PREVIEW_MD.read_text(encoding="utf-8"))

    def test_runner_uses_standard_library_and_no_runtime_network_or_server_imports(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "sys"})
        self.assertTrue(imports.isdisjoint(FORBIDDEN_IMPORTS))

        source_no_spaces = RUNNER.read_text(encoding="utf-8").lower().replace(" ", "")
        forbidden_call_terms = [
            _frag("import", "requests"),
            _frag("requests", "."),
            _frag("import", "httpx"),
            _frag("httpx", "."),
            _frag("import", "flask"),
            _frag("flask", "."),
            _frag("import", "fastapi"),
            _frag("fastapi", "."),
            _frag("urllib", ".", "request"),
            _frag("webbrowser", "."),
            _frag("selenium", "."),
            _frag("submit", "_", "order", "("),
            _frag("execute", "_", "trade", "("),
            _frag("place", "_", "order", "("),
            _frag("scripts", "/", "dispatcher", ".", "py"),
            _frag("scripts", "/", "run", "_", "codex", ".", "py"),
        ]
        for term in forbidden_call_terms:
            self.assertNotIn(term, source_no_spaces)


if __name__ == "__main__":
    unittest.main()
