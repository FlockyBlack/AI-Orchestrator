import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
GATE = ROOT / "pm_bot" / "research" / "validate_selected_ingest_operator_review_records.py"
JSON_RESULT = ROOT / "pm_bot" / "research" / "selected_ingest_operator_review_records_result.v1.json"
MARKDOWN_REPORT = ROOT / "pm_bot" / "research" / "selected_ingest_operator_review_records_report.v1.md"
EXPECTED_JSON_RESULT = ROOT / "pm_bot" / "research" / "expected_selected_ingest_operator_review_records_result.v1.json"

EXPECTED_SELECTED_MARKET_IDS = ["692258", "824952", "691547", "597964", "598936"]
PROHIBITED_FIELD_TOKENS = {
    "order",
    "trade",
    "trading",
    "wallet",
    "private_key",
    "execution",
    "recommendation",
    "bet",
    "stake",
    "size",
    "entry_price",
    "limit_price",
    "price_target",
    "score",
    "signal",
    "probability",
    "expected_value",
    "ev",
    "side",
    "yes_no_decision",
    "buy",
    "sell",
    "market_decision",
}
ALLOWED_NEGATED_SAFETY_CHECKS = {
    "no_trading_recommendation_present",
    "no_probability_or_ev_present",
    "no_side_recommendation_present",
    "no_market_decision_present",
}


def _run_gate(*extra_args):
    return subprocess.run(
        [sys.executable, str(GATE), *extra_args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _load_module():
    spec = importlib.util.spec_from_file_location("selected_ingest_operator_review_record_gate", GATE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_result():
    _run_gate()
    return _load_json(JSON_RESULT)


def _ready_review_record(market_id):
    return {
        "market_id": market_id,
        "review_status": "review_completed",
        "review_outcome": "ready_for_dossier_drafting",
        "reviewer_notes": "Structural ready outcome test record.",
        "review_checks": {
            "resolution_criteria_checked": True,
            "evidence_structure_checked": True,
            "source_coverage_checked": True,
            "missing_information_reviewed": True,
            "no_trading_recommendation_present": True,
            "no_probability_or_ev_present": True,
            "no_side_recommendation_present": True,
            "no_market_decision_present": True,
        },
        "requested_followup_information": [],
        "quality_flags": [],
    }


def _needs_more_information_record(market_id):
    return {
        "market_id": market_id,
        "review_status": "needs_more_information",
        "review_outcome": "needs_more_information",
        "reviewer_notes": "More structural information is required.",
        "review_checks": {
            "missing_information_reviewed": True,
            "no_trading_recommendation_present": True,
            "no_probability_or_ev_present": True,
            "no_side_recommendation_present": True,
            "no_market_decision_present": True,
        },
        "requested_followup_information": [],
        "quality_flags": [],
    }


def _build_with_records(records):
    module = _load_module()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        fixture_path = temp_path / "review_records.json"
        fixture_path.write_text(json.dumps({"review_records": records}, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        return module.build_selected_ingest_operator_review_record_result(
            review_records_path=fixture_path,
            json_output_path=temp_path / "result.json",
            markdown_output_path=temp_path / "report.md",
        )


def _codes(errors):
    return {item["code"] for item in errors}


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
    return {token for token in normalized if token} | {str(key).lower()}


def _walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


class SelectedIngestOperatorReviewRecordGateTests(unittest.TestCase):
    def test_default_export_matches_expected_json_result(self):
        _run_gate()

        self.assertEqual(_load_json(JSON_RESULT), _load_json(EXPECTED_JSON_RESULT))

    def test_valid_review_record_for_ready_packet_is_accepted(self):
        result = _load_result()
        ready_records = [
            record
            for record in result["accepted_review_records"]
            if record["market_id"] == "824952" and record["review_outcome"] == "ready_for_dossier_drafting"
        ]

        self.assertEqual(result["selected_market_ids"], EXPECTED_SELECTED_MARKET_IDS)
        self.assertEqual(len(ready_records), 1)
        self.assertEqual(ready_records[0]["queue_group"], "ready_for_operator_review")
        self.assertTrue(all(ready_records[0]["review_checks"][check] for check in result["required_ready_review_checks"]))

    def test_ready_for_dossier_drafting_is_rejected_for_stub_only_packets(self):
        result = _build_with_records([_ready_review_record("691547")])
        rejected = result["rejected_review_records"][0]

        self.assertEqual(result["review_summary"]["review_records_accepted"], 0)
        self.assertEqual(rejected["queue_group"], "stub_only")
        self.assertIn("ready_outcome_requires_ready_queue_group", _codes(rejected["errors"]))

    def test_ready_for_dossier_drafting_is_rejected_for_needs_more_information_packets(self):
        result = _build_with_records([_ready_review_record("692258")])
        rejected = result["rejected_review_records"][0]

        self.assertEqual(result["review_summary"]["review_records_accepted"], 0)
        self.assertEqual(rejected["queue_group"], "needs_more_information")
        self.assertIn("ready_outcome_requires_ready_queue_group", _codes(rejected["errors"]))

    def test_unknown_market_id_is_rejected(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["unknown-market-id"]

        self.assertIn("unknown_market_id", _codes(errors))

    def test_immutable_field_override_attempts_are_rejected(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["691547"]

        self.assertIn("immutable_packet_field_override:title", _codes(errors))

    def test_prohibited_trading_execution_recommendation_fields_are_rejected(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["597964"]
        codes = _codes(errors)

        for field in ("order", "trade", "wallet", "private_key", "execution", "recommendation", "bet", "stake"):
            self.assertIn(f"prohibited_review_field:{field}", codes)
            self.assertIn(f"unexpected_review_field:{field}", codes)

    def test_probability_ev_score_side_and_market_decision_fields_are_rejected(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["597964"]
        codes = _codes(errors)

        for field in ("probability", "expected_value", "ev", "score", "signal", "side", "yes_no_decision", "buy", "sell", "market_decision"):
            self.assertIn(f"prohibited_review_field:{field}", codes)
            self.assertIn(f"unexpected_review_field:{field}", codes)

    def test_needs_more_information_outcome_requires_requested_followup_information(self):
        result = _build_with_records([_needs_more_information_record("692258")])
        rejected = result["rejected_review_records"][0]

        self.assertEqual(result["review_summary"]["review_records_accepted"], 0)
        self.assertIn("needs_more_information_requires_followup", _codes(rejected["errors"]))

    def test_accepted_records_contain_no_betting_trading_score_probability_ev_or_decision_fields(self):
        result = _load_result()
        for record in result["accepted_review_records"]:
            for key in _walk_keys(record):
                if key in ALLOWED_NEGATED_SAFETY_CHECKS:
                    continue
                self.assertTrue(
                    PROHIBITED_FIELD_TOKENS.isdisjoint(_field_tokens(key)),
                    msg=f"{record['market_id']} contains prohibited accepted key {key}",
                )

    def test_markdown_report_has_stable_headings_and_summary_counts(self):
        result = _load_result()
        markdown = MARKDOWN_REPORT.read_text(encoding="utf-8")
        summary = result["review_summary"]

        heading_lines = [line for line in markdown.splitlines() if line.startswith("#")]
        self.assertEqual(
            heading_lines,
            [
                "# Selected Ingest Operator Review Records v1",
                "## Summary",
                "## Selected Market IDs",
                "## Accepted Review Records",
                "### 692258",
                "### 824952",
                "### 598936",
                "## Rejected Review Records",
                "### 691547",
                "### 597964",
                "### unknown-market-id",
                "## Errors By Market ID",
                "### 597964",
                "### 691547",
                "### unknown-market-id",
                "## Safety Boundary",
                "## Limitations",
            ],
        )
        for field, expected in {
            "review_records_read": 6,
            "review_records_accepted": 3,
            "review_records_rejected": 3,
            "ready_for_dossier_drafting": 1,
            "needs_more_information": 1,
            "research_quality_rejected": 0,
            "watch_only_manual": 1,
        }.items():
            self.assertEqual(summary[field], expected)
            self.assertIn(f"- {field}: {expected}", markdown)

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

    def test_keyed_review_record_payload_is_supported(self):
        module = _load_module()
        keyed_payload = {
            "schema_version": "selected-keyed-review-records-test.v1",
            "824952": _ready_review_record("824952"),
        }
        keyed_payload["824952"].pop("market_id")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fixture_path = temp_path / "keyed_records.json"
            fixture_path.write_text(json.dumps(keyed_payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            result = module.build_selected_ingest_operator_review_record_result(
                review_records_path=fixture_path,
                json_output_path=temp_path / "result.json",
                markdown_output_path=temp_path / "report.md",
            )

        self.assertEqual(result["review_summary"]["review_records_read"], 1)
        self.assertEqual(result["review_summary"]["review_records_accepted"], 1)
        self.assertEqual(result["accepted_review_records"][0]["market_id"], "824952")

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
            "validate_selected_ingest_operator_review_records",
            "selected_ingest_operator_review_records",
            "selected_ingest_operator_review_record_gate",
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

    def test_gate_uses_standard_library_only(self):
        tree = ast.parse(GATE.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "copy", "json", "pathlib", "sys"})

    def test_gate_has_no_live_fetcher_or_runtime_imports(self):
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
            "run_codex(",
        ]
        for term in forbidden:
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()
