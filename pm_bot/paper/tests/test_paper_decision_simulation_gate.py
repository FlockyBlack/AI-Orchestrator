import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
GATE = ROOT / "pm_bot" / "paper" / "run_paper_decision_simulation_gate.py"
POLICY_SPEC = ROOT / "pm_bot" / "paper" / "paper_decision_policy_spec.v1.json"
JSON_RESULT = ROOT / "pm_bot" / "paper" / "paper_decision_simulation_gate.v1.json"
MARKDOWN_REPORT = ROOT / "pm_bot" / "paper" / "paper_decision_simulation_gate.v1.md"
EXPECTED_JSON_RESULT = ROOT / "pm_bot" / "paper" / "expected_paper_decision_simulation_gate.v1.json"

PASSED_STATUS = "paper_simulation_gate_passed_for_manual_review"
ALLOWED_STATUSES = [
    PASSED_STATUS,
    "paper_watch_only",
    "paper_blocked_needs_more_review",
    "paper_blocked_by_policy",
]
EXPECTED_SUMMARY = {
    "policy_specs_read": 1,
    "gate_records_written": 1,
    PASSED_STATUS: 1,
    "paper_watch_only": 0,
    "paper_blocked_needs_more_review": 0,
    "paper_blocked_by_policy": 0,
    "paper_orders_created": 0,
}
EXPECTED_RECORD_FIELDS = [
    "market_id",
    "simulation_status",
    "policy_findings",
    "blocking_reasons",
    "watch_only_reasons",
    "required_manual_followup",
    "simulation_notes",
    "safety_flags",
    "paper_orders_created",
]
PROHIBITED_OUTPUT_FIELD_TOKENS = {
    "side",
    "buy",
    "sell",
    "yes",
    "no",
    "outcome_side",
    "selected_outcome",
    "probability",
    "implied_probability",
    "fair_probability",
    "ev",
    "expected_value",
    "edge",
    "score",
    "confidence_score",
    "size",
    "stake",
    "quantity",
    "order",
    "orders",
    "order_plan",
    "paper_order",
    "recommendation",
    "decision",
    "trade_decision",
}
OUTPUT_FIELD_EXCEPTIONS = {"paper_orders_created"}


def _frag(*parts):
    return "".join(parts)


def _run_gate(*extra_args):
    return subprocess.run(
        [sys.executable, str(GATE), *extra_args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _load_module():
    spec = importlib.util.spec_from_file_location("paper_decision_simulation_gate", GATE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_result():
    _run_gate()
    return _load_json(JSON_RESULT)


def _policy_spec_payload():
    return _load_json(POLICY_SPEC)


def _build_with_policy_spec(policy_spec_payload):
    module = _load_module()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        policy_spec_path = temp_path / "policy_spec.json"
        policy_spec_path.write_text(
            json.dumps(policy_spec_payload, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        return module.build_paper_decision_simulation_gate(
            policy_spec_path=policy_spec_path,
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


class PaperDecisionSimulationGateTests(unittest.TestCase):
    def test_default_export_matches_expected_json_result(self):
        _run_gate()

        self.assertEqual(_load_json(JSON_RESULT), _load_json(EXPECTED_JSON_RESULT))

    def test_market_824952_gate_record_is_exported_from_policy_spec_chain(self):
        result = _load_result()

        self.assertEqual(result["source_policy_spec_path"], "pm_bot/paper/paper_decision_policy_spec.v1.json")
        self.assertEqual(result["source_preview_path"], "pm_bot/paper/paper_decision_simulation_preview.v1.json")
        self.assertEqual(result["market_ids"], ["824952"])
        self.assertEqual(result["allowed_simulation_statuses"], ALLOWED_STATUSES)
        self.assertEqual(result["gate_summary"], EXPECTED_SUMMARY)
        self.assertEqual(len(result["gate_records"]), 1)

        record = result["gate_records"][0]
        self.assertEqual(list(record), EXPECTED_RECORD_FIELDS)
        self.assertEqual(record["market_id"], "824952")
        self.assertIn(record["simulation_status"], ALLOWED_STATUSES)
        self.assertEqual(record["simulation_status"], PASSED_STATUS)
        self.assertEqual(record["blocking_reasons"], [])
        self.assertEqual(record["watch_only_reasons"], [])
        self.assertEqual(record["paper_orders_created"], 0)

    def test_unknown_simulation_status_is_rejected(self):
        module = _load_module()

        with self.assertRaises(ValueError):
            module.validate_simulation_status("unknown_status")

        result = _load_result()
        result["gate_records"][0]["simulation_status"] = "unknown_status"
        with self.assertRaises(ValueError):
            module.validate_gate_payload(result)

    def test_prohibited_output_fields_are_not_emitted(self):
        result = _load_result()

        for key in _walk_keys(result):
            if key in OUTPUT_FIELD_EXCEPTIONS:
                continue
            self.assertTrue(
                PROHIBITED_OUTPUT_FIELD_TOKENS.isdisjoint(_field_tokens(key)),
                msg=f"gate output contains prohibited key: {key}",
            )

    def test_fixture_with_prohibited_source_field_is_blocked_without_echoing_field(self):
        payload = _policy_spec_payload()
        payload["policy_specs"][0]["probability"] = "prohibited"

        result = _build_with_policy_spec(payload)
        record = result["gate_records"][0]

        self.assertEqual(record["market_id"], "824952")
        self.assertEqual(record["simulation_status"], "paper_blocked_by_policy")
        self.assertEqual(record["blocking_reasons"], ["prohibited_source_field_present", "unexpected_policy_spec_field_present"])
        self.assertNotIn("probability", json.dumps(result, sort_keys=True).lower())

    def test_output_matches_expected_fixture_deterministically(self):
        first = _load_result()
        second = _load_result()

        self.assertEqual(first, second)
        self.assertEqual(first, _load_json(EXPECTED_JSON_RESULT))

    def test_no_paper_order_artifacts_are_created(self):
        result = _load_result()

        self.assertEqual(result["gate_summary"]["paper_orders_created"], 0)
        self.assertEqual(result["gate_records"][0]["paper_orders_created"], 0)
        matches = []
        for path in (ROOT / "pm_bot" / "paper").rglob("*"):
            if path.is_file() and ("paper_order" in path.name.lower() or "order_plan" in path.name.lower()):
                matches.append(str(path.relative_to(ROOT)).replace("\\", "/"))
        self.assertEqual(matches, [])

    def test_markdown_report_has_stable_headings_and_summary_counts(self):
        result = _load_result()
        markdown = MARKDOWN_REPORT.read_text(encoding="utf-8")

        heading_lines = [line for line in markdown.splitlines() if line.startswith("#")]
        self.assertEqual(
            heading_lines,
            [
                "# PMBOT Paper Simulation Gate v1",
                "## Summary",
                "## Gate Records",
                "### 824952",
                "## Limitations",
            ],
        )
        for field, expected in EXPECTED_SUMMARY.items():
            self.assertIn(f"- {field}: {expected}", markdown)
        self.assertIn(f"- simulation_status: {PASSED_STATUS}", markdown)
        self.assertEqual(result["gate_summary"], EXPECTED_SUMMARY)

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

            first = _run_gate(*args)
            first_json = json_path.read_text(encoding="utf-8")
            first_markdown = markdown_path.read_text(encoding="utf-8")
            second = _run_gate(*args)

            self.assertEqual(first.stdout, second.stdout)
            self.assertEqual(first_json, json_path.read_text(encoding="utf-8"))
            self.assertEqual(first_markdown, markdown_path.read_text(encoding="utf-8"))
            self.assertEqual(json.loads(first_json), json.loads(expected_path.read_text(encoding="utf-8")))

    def test_json_artifacts_parse(self):
        _run_gate()

        for path in (JSON_RESULT, EXPECTED_JSON_RESULT):
            self.assertIsInstance(_load_json(path), dict)

    def test_gate_uses_standard_library_only(self):
        tree = ast.parse(GATE.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "sys"})

    def test_gate_has_no_live_fetcher_runtime_or_downstream_automation_imports(self):
        source = GATE.read_text(encoding="utf-8").lower()
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
