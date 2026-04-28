import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EXPORTER = ROOT / "pm_bot" / "paper" / "export_paper_decision_policy_spec.py"
PREVIEW = ROOT / "pm_bot" / "paper" / "paper_decision_simulation_preview.v1.json"
JSON_RESULT = ROOT / "pm_bot" / "paper" / "paper_decision_policy_spec.v1.json"
MARKDOWN_REPORT = ROOT / "pm_bot" / "paper" / "paper_decision_policy_spec.v1.md"
EXPECTED_JSON_RESULT = ROOT / "pm_bot" / "paper" / "expected_paper_decision_policy_spec.v1.json"

ACCEPTED_PREVIEW_STATUS = "ready_for_future_paper_decision_policy_design"
EXPECTED_SUMMARY = {
    "preview_records_read": 1,
    "policy_specs_written": 1,
    "markets_covered": 1,
    "paper_orders_created": 0,
}
EXPECTED_FUTURE_STATUSES = [
    "paper_simulation_allowed",
    "paper_watch_only",
    "paper_blocked_needs_more_review",
    "paper_blocked_by_policy",
]
EXPECTED_REQUIRED_INPUTS = [
    "market_id",
    "question/title",
    "resolution_criteria_summary",
    "evidence_inventory_summary",
    "uncertainty_register_summary",
    "missing_information_review",
    "open_questions",
    "current_yes_price",
    "liquidity",
    "volume",
    "paper_readiness_status",
    "paper_policy_status",
]
EXPECTED_ALLOWED_OUTPUT_FIELDS = [
    "market_id",
    "simulation_status",
    "policy_findings",
    "blocking_reasons",
    "watch_only_reasons",
    "required_manual_followup",
    "simulation_notes",
]
EXPECTED_ALWAYS_FORBIDDEN = [
    "real_order",
    "live_order",
    "wallet",
    "private_key",
    "execution",
    "trade_execution",
    "authenticated_endpoint",
]
EXPECTED_PAPER_004_FORBIDDEN = [
    "side",
    "recommendation",
    "probability",
    "expected_value",
    "ev",
    "score",
    "signal",
    "stake",
    "size",
    "entry_price",
    "limit_price",
    "price_target",
    "market_decision",
    "buy",
    "sell",
]
EXPECTED_POLICY_BLOCKERS = [
    "missing_resolution_criteria",
    "missing_evidence_inventory",
    "unresolved_critical_questions",
    "prohibited_trading_language_present",
    "probability_or_ev_present",
    "side_or_recommendation_present",
    "market_decision_present",
    "order_or_trade_present",
]
EXPECTED_WATCH_ONLY_REASONS = [
    "insufficient_source_coverage",
    "high_unresolved_uncertainty",
    "stale_manual_review",
    "ambiguous_resolution_criteria",
]


def _frag(*parts):
    return "".join(parts)


def _run_exporter(*extra_args):
    return subprocess.run(
        [sys.executable, str(EXPORTER), *extra_args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _load_module():
    spec = importlib.util.spec_from_file_location("paper_decision_policy_spec", EXPORTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_result():
    _run_exporter()
    return _load_json(JSON_RESULT)


def _preview_payload():
    return _load_json(PREVIEW)


def _build_with_preview(preview_payload):
    module = _load_module()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        preview_path = temp_path / "preview.json"
        preview_path.write_text(
            json.dumps(preview_payload, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        return module.build_paper_decision_policy_spec(
            preview_path=preview_path,
            json_output_path=temp_path / "result.json",
            markdown_output_path=temp_path / "report.md",
            expected_json_output_path=temp_path / "expected.json",
        )


def _field_tokens(key):
    lower = str(key).lower()
    normalized_chars = []
    previous_was_separator = False
    for char in lower:
        if char.isalnum():
            normalized_chars.append(char)
            previous_was_separator = False
        elif not previous_was_separator:
            normalized_chars.append("_")
            previous_was_separator = True
    normalized_key = "".join(normalized_chars).strip("_")
    parts = [part for part in normalized_key.split("_") if part]
    tokens = {lower, normalized_key}
    tokens.update(parts)
    for index in range(len(parts) - 1):
        tokens.add(f"{parts[index]}_{parts[index + 1]}")
    for index in range(len(parts) - 2):
        tokens.add(f"{parts[index]}_{parts[index + 1]}_{parts[index + 2]}")
    return {token for token in tokens if token}


def _walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


class PaperDecisionPolicySpecTests(unittest.TestCase):
    def test_default_export_matches_expected_json_result(self):
        _run_exporter()

        self.assertEqual(_load_json(JSON_RESULT), _load_json(EXPECTED_JSON_RESULT))

    def test_market_824952_is_covered_by_policy_spec(self):
        result = _load_result()

        self.assertEqual(result["market_ids"], ["824952"])
        self.assertEqual(result["policy_spec_summary"], EXPECTED_SUMMARY)
        self.assertEqual(len(result["policy_specs"]), 1)

        spec_record = result["policy_specs"][0]
        self.assertEqual(spec_record["market_id"], "824952")
        self.assertEqual(spec_record["accepted_preview_status"], ACCEPTED_PREVIEW_STATUS)
        self.assertEqual(spec_record["policy_spec_status"], "paper_decision_policy_constraints_defined")
        self.assertTrue(spec_record["source_policy_record_present"])
        self.assertTrue(spec_record["source_final_dossier_draft_present"])

    def test_only_ready_policy_design_previews_are_accepted(self):
        payload = _preview_payload()
        payload["preview_records"][0]["simulation_preview_status"] = "needs_more_manual_review"

        result = _build_with_preview(payload)

        self.assertEqual(result["policy_specs"], [])
        self.assertEqual(result["market_ids"], [])
        self.assertEqual(
            result["policy_spec_summary"],
            {
                "preview_records_read": 1,
                "policy_specs_written": 0,
                "markets_covered": 0,
                "paper_orders_created": 0,
            },
        )

    def test_allowed_future_statuses_are_present(self):
        result = _load_result()

        self.assertEqual(result["allowed_future_simulation_statuses"], EXPECTED_FUTURE_STATUSES)

    def test_required_future_inputs_are_present(self):
        result = _load_result()

        self.assertEqual(result["required_future_simulation_inputs"], EXPECTED_REQUIRED_INPUTS)
        self.assertEqual(
            result["policy_specs"][0]["future_input_source_fields"]["question/title"],
            "title_question",
        )

    def test_allowed_and_prohibited_future_output_fields_are_explicit(self):
        result = _load_result()

        self.assertEqual(result["allowed_future_output_fields"], EXPECTED_ALLOWED_OUTPUT_FIELDS)
        self.assertEqual(result["always_forbidden_future_fields"], EXPECTED_ALWAYS_FORBIDDEN)
        self.assertEqual(result["paper_004_forbidden_output_fields"], EXPECTED_PAPER_004_FORBIDDEN)
        self.assertTrue(
            set(result["allowed_future_output_fields"]).isdisjoint(result["always_forbidden_future_fields"])
        )
        self.assertTrue(
            set(result["allowed_future_output_fields"]).isdisjoint(result["paper_004_forbidden_output_fields"])
        )

    def test_policy_blockers_and_watch_only_reasons_are_defined(self):
        result = _load_result()

        self.assertEqual(result["policy_blockers"], EXPECTED_POLICY_BLOCKERS)
        self.assertEqual(result["watch_only_reasons"], EXPECTED_WATCH_ONLY_REASONS)

    def test_policy_spec_records_emit_no_decision_scoring_or_execution_fields(self):
        result = _load_result()
        prohibited_field_tokens = set(EXPECTED_ALWAYS_FORBIDDEN) | set(EXPECTED_PAPER_004_FORBIDDEN) | {
            "order",
            "orders",
            "trade",
            "trades",
            "trading",
            "probabilities",
            "expected_values",
            "market_decisions",
            "recommendations",
            "scores",
            "signals",
            "sides",
            "yes_no_decision",
        }

        for record in result["policy_specs"]:
            for key in _walk_keys(record):
                self.assertTrue(
                    prohibited_field_tokens.isdisjoint(_field_tokens(key)),
                    msg=f"policy spec record contains prohibited output key: {key}",
                )

    def test_no_paper_orders_are_created(self):
        result = _load_result()

        self.assertEqual(result["policy_spec_summary"]["paper_orders_created"], 0)
        self.assertNotIn("paper_order", result["policy_specs"][0])

    def test_markdown_report_has_stable_headings_and_summary_counts(self):
        result = _load_result()
        markdown = MARKDOWN_REPORT.read_text(encoding="utf-8")

        heading_lines = [line for line in markdown.splitlines() if line.startswith("#")]
        self.assertEqual(
            heading_lines,
            [
                "# PMBOT Paper Decision Policy Spec v1",
                "## Summary",
                "## Future Simulation Contract",
                "## Policy Constraint Codes",
                "## Policy Specs",
                "### 824952",
                "## Safety Boundary",
                "## Limitations",
            ],
        )
        for field, expected in EXPECTED_SUMMARY.items():
            self.assertIn(f"- {field}: {expected}", markdown)
        self.assertIn("  - 824952", markdown)
        self.assertIn("- allowed_future_simulation_statuses:", markdown)
        self.assertEqual(result["policy_spec_summary"], EXPECTED_SUMMARY)

    def test_json_output_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            json_path = temp_path / "result.json"
            markdown_path = temp_path / "report.md"
            expected_path = temp_path / "expected.json"
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

    def test_no_runtime_or_downstream_automation_exists(self):
        runtime_roots = [
            ROOT / "codex_auto",
            ROOT / "config",
            ROOT / "runs",
            ROOT / "scripts",
            ROOT / "state",
            ROOT / "tasks",
        ]
        targets = (
            "export_paper_decision_policy_spec",
            "paper_decision_policy_spec",
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

    def test_json_artifacts_parse(self):
        _run_exporter()

        for path in (JSON_RESULT, EXPECTED_JSON_RESULT):
            self.assertIsInstance(_load_json(path), dict)

    def test_exporter_uses_standard_library_only(self):
        tree = ast.parse(EXPORTER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "sys"})

    def test_exporter_has_no_live_fetcher_runtime_or_downstream_automation_imports(self):
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
            "submit_order",
            "execute_trade",
            _frag("dis", "patcher"),
            _frag("run", "_", "codex"),
            _frag("prompt", "_", "automation"),
        ]
        for term in forbidden:
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()
