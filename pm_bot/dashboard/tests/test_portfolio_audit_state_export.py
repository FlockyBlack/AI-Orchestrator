import ast
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "dashboard" / "export_portfolio_audit_state.py"
CONTRACT = ROOT / "pm_bot" / "dashboard" / "portfolio_audit_state_contract.v1.json"
PREVIEW_JSON = ROOT / "pm_bot" / "dashboard" / "portfolio_audit_state_preview.v1.json"
PREVIEW_MD = ROOT / "pm_bot" / "dashboard" / "portfolio_audit_state_preview.v1.md"
EXPECTED_PREVIEW_JSON = ROOT / "pm_bot" / "dashboard" / "expected_portfolio_audit_state_preview.v1.json"

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
    spec = importlib.util.spec_from_file_location("portfolio_audit_state", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class PortfolioAuditStateExportTests(unittest.TestCase):
    def test_write_exports_contract_preview_markdown_and_expected_fixture(self):
        result = json.loads(_run_write().stdout)

        self.assertEqual(result["status"], "portfolio_audit_state_exported")
        self.assertEqual(result["audit_status"], "reconciliation_passed")
        self.assertFalse(result["future_batch_audit_present"])
        self.assertEqual(result["known_market_ids"], ["824952", "series_btc_above_90000_2026_05_31"])
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

    def test_contract_declares_required_portfolio_audit_state_fields(self):
        _run_write()
        contract = _load_json(CONTRACT)
        module = _load_module()

        self.assertEqual(contract, module.build_portfolio_audit_state_contract())
        self.assertEqual(contract["$id"], "PMBOT_PORTFOLIO_AUDIT_STATE_CONTRACT.v1")
        self.assertIn("portfolio_accounting_summary", contract["required"])
        self.assertIn("audit_summary_existing", contract["required"])
        self.assertIn("future_batch_audit_placeholder", contract["required"])
        self.assertFalse(contract["contract_boundary"]["dashboard_runtime_defined"])
        self.assertFalse(contract["contract_boundary"]["server_defined"])
        self.assertFalse(contract["contract_boundary"]["frontend_defined"])
        self.assertFalse(contract["contract_boundary"]["network_or_api_defined"])
        self.assertFalse(contract["contract_boundary"]["trading_or_ordering_defined"])
        self.assertFalse(contract["contract_boundary"]["scoring_probability_ev_edge_defined"])

    def test_preview_contains_portfolio_accounting_audit_and_required_warnings(self):
        _run_write()
        preview = _load_json(PREVIEW_JSON)

        self.assertEqual(preview["schema_version"], "portfolio_audit_state_preview.v1")
        self.assertEqual(preview["dashboard_state_export_version"], "v2")
        self.assertEqual(preview["generated_by"], "pm_bot/dashboard/export_portfolio_audit_state.py")
        self.assertFalse(preview["generated_at_policy"]["wall_clock_time_used"])
        self.assertEqual(preview["known_market_ids"], ["824952", "series_btc_above_90000_2026_05_31"])

        accounting = preview["portfolio_accounting_summary"]
        self.assertEqual(accounting["summary_status"], "portfolio_accounting_state_ready")
        self.assertEqual(accounting["accepted_accounting_market_ids"], ["824952"])
        self.assertEqual(accounting["counts"]["paper_accounting_ledger_entries"], 1)
        self.assertEqual(accounting["counts"]["paper_accounting_settled_count"], 1)
        self.assertEqual(accounting["counts"]["paper_accounting_open_count"], 0)
        self.assertEqual(accounting["counts"]["real_orders_created"], 0)
        self.assertEqual(accounting["counts"]["live_orders_created"], 0)
        self.assertEqual(accounting["counts"]["autonomous_paper_orders_created"], 0)
        self.assertEqual(accounting["paper_accounting_metrics"]["paper_accounting_cumulative_pnl"], "6.00")
        self.assertTrue(accounting["accounting_boundary"]["paper_accounting_only"])
        self.assertTrue(accounting["accounting_boundary"]["operator_manual_fixture_source"])
        self.assertFalse(accounting["accounting_boundary"]["strategy_profitability"])
        self.assertIn("not strategy profitability", accounting["accounting_boundary"]["warning"])

        audit = preview["audit_summary_existing"]
        self.assertTrue(audit["present"])
        self.assertEqual(audit["audit_status"], "reconciliation_passed")
        self.assertEqual(audit["counts"]["artifacts_checked"], 14)
        self.assertEqual(audit["counts"]["checks_total"], 14)
        self.assertEqual(audit["counts"]["checks_passed"], 14)
        self.assertEqual(audit["counts"]["checks_failed"], 0)
        self.assertEqual(audit["mismatches_count"], 0)
        self.assertEqual(audit["warnings_count"], 0)
        self.assertEqual(audit["paper_orders_created"], 0)
        self.assertEqual(audit["autonomous_actions_created"], 0)

        self.assertIn(
            "Paper accounting PnL is fixture/manual accounting only and is not strategy profitability.",
            preview["interpretation_warnings"],
        )
        self.assertIn(
            "Audit pass/fail state reflects deterministic local artifact consistency only, not truth inference.",
            preview["interpretation_warnings"],
        )
        self.assertIn(
            "This snapshot does not recommend a side, size, price, market, or trade.",
            preview["interpretation_warnings"],
        )

    def test_artifact_pointers_future_placeholder_and_safety_flags_are_explicit(self):
        _run_write()
        preview = _load_json(PREVIEW_JSON)
        pointers = preview["artifact_pointers"]

        self.assertEqual(
            pointers["paper_017_reconciliation_audit_json"]["path"],
            "pm_bot/paper/paper_accounting_reconciliation_audit.v1.json",
        )
        self.assertEqual(pointers["paper_metrics_report_json"]["path"], "pm_bot/paper/paper_metrics_report.v1.json")
        self.assertEqual(pointers["integration_006_result"]["path"], "docs/PMBOT_INTEGRATION_006_RESULT.json")
        self.assertEqual(pointers["infra_008_result"]["path"], "docs/PMBOT_INFRA_008_RESULT.json")
        self.assertFalse(pointers["infra_008_result"]["present"])
        self.assertFalse(pointers["infra_008_result"]["required"])
        self.assertTrue(all(pointer["present"] for pointer in pointers.values() if pointer["required"]))

        placeholder = preview["future_batch_audit_placeholder"]
        self.assertFalse(placeholder["paper_018_required"])
        self.assertFalse(placeholder["paper_018_present"])
        self.assertIsNone(placeholder["batch_audit_status"])
        self.assertEqual(placeholder["batch_ids"], [])
        self.assertEqual(placeholder["batch_audit_summary"], {})
        self.assertEqual(placeholder["warnings"], [])

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

    def test_markdown_preview_matches_cli_output(self):
        _run_write()
        markdown = PREVIEW_MD.read_text(encoding="utf-8")

        self.assertEqual(_run_markdown().stdout, markdown)
        self.assertIn("PMBOT Portfolio Audit State Preview v1", markdown)
        self.assertIn("paper_017_status: completed_ready_for_review", markdown)
        self.assertIn("Paper accounting PnL is fixture/manual accounting only", markdown)
        self.assertIn("paper_018_present: false", markdown)

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
