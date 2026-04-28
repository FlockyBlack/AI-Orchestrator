import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
GATE = ROOT / "pm_bot" / "research" / "validate_operator_review_records.py"
FIXTURE = ROOT / "pm_bot" / "research" / "operator_review_records_fixture.v1.json"
JSON_RESULT = ROOT / "pm_bot" / "research" / "operator_review_records_result.v1.json"
MARKDOWN_REPORT = ROOT / "pm_bot" / "research" / "operator_review_records_report.v1.md"
EXPECTED_JSON_RESULT = ROOT / "pm_bot" / "research" / "expected_operator_review_records_result.v1.json"


PROHIBITED_FIELD_TOKENS = {
    "order",
    "trade",
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
    "side",
}
ALLOWED_NEGATED_SAFETY_CHECKS = {"no_trading_recommendation_present"}


def _run_gate(*extra_args):
    return subprocess.run(
        [sys.executable, str(GATE), *extra_args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _load_module():
    spec = importlib.util.spec_from_file_location("operator_review_record_gate", GATE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_result():
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
        return module.build_operator_review_record_result(
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


class OperatorReviewRecordGateTests(unittest.TestCase):
    def test_default_export_matches_expected_json_result(self):
        _run_gate()
        self.assertEqual(_load_json(JSON_RESULT), _load_json(EXPECTED_JSON_RESULT))

    def test_valid_ready_review_record_is_accepted_for_ready_packet(self):
        result = _load_result()
        ready_records = [
            record
            for record in result["accepted_review_records"]
            if record["market_id"] == "563650" and record["review_outcome"] == "ready_for_dossier_drafting"
        ]

        self.assertEqual(len(ready_records), 1)
        self.assertEqual(ready_records[0]["queue_group"], "ready_for_operator_review")
        self.assertTrue(all(ready_records[0]["review_checks"][check] for check in result["required_ready_review_checks"]))

    def test_ready_for_dossier_drafting_is_rejected_for_stub_only_packets(self):
        result = _build_with_records([_ready_review_record("569368")])
        rejected = result["rejected_review_records"][0]

        self.assertEqual(result["review_summary"]["review_records_accepted"], 0)
        self.assertEqual(rejected["queue_group"], "stub_only")
        self.assertIn("ready_outcome_requires_ready_queue_group", _codes(rejected["errors"]))

    def test_ready_for_dossier_drafting_is_rejected_for_needs_more_information_packets(self):
        result = _build_with_records([_ready_review_record("569366")])
        rejected = result["rejected_review_records"][0]

        self.assertEqual(result["review_summary"]["review_records_accepted"], 0)
        self.assertEqual(rejected["queue_group"], "needs_more_information")
        self.assertIn("ready_outcome_requires_ready_queue_group", _codes(rejected["errors"]))

    def test_unknown_market_id_is_rejected(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["unknown-market-id"]

        self.assertIn("unknown_market_id", _codes(errors))

    def test_prohibited_trading_execution_recommendation_fields_are_rejected(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["569343"]
        codes = _codes(errors)

        self.assertIn("prohibited_review_field:recommendation", codes)
        self.assertIn("prohibited_review_field:probability", codes)
        self.assertIn("unexpected_review_field:recommendation", codes)

    def test_immutable_packet_field_override_attempts_are_rejected(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["569332"]

        self.assertIn("immutable_packet_field_override:title", _codes(errors))

    def test_needs_more_information_outcome_requires_requested_followup_information(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["569333"]

        self.assertIn("needs_more_information_requires_followup", _codes(errors))

    def test_accepted_review_records_contain_no_betting_trading_score_or_probability_fields(self):
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
                "# PMBOT Operator Review Records v1",
                "## Summary",
                "## Accepted Review Records",
                "### 563650",
                "### 569366",
                "### 573656",
                "## Rejected Review Records",
                "### 569332",
                "### 569333",
                "### 569343",
                "### 569344",
                "### unknown-market-id",
                "## Errors By Market ID",
                "### 569332",
                "### 569333",
                "### 569343",
                "### 569344",
                "### unknown-market-id",
                "## Limitations",
            ],
        )
        for field, expected in {
            "review_records_read": 8,
            "review_records_accepted": 3,
            "review_records_rejected": 5,
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
        result = _build_with_records([])
        self.assertEqual(result["review_summary"]["review_records_read"], 0)

        module = _load_module()
        keyed_payload = {
            "schema_version": "keyed-review-records-test.v1",
            "563650": _ready_review_record("563650"),
        }
        keyed_payload["563650"].pop("market_id")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fixture_path = temp_path / "keyed_records.json"
            fixture_path.write_text(json.dumps(keyed_payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            keyed_result = module.build_operator_review_record_result(
                review_records_path=fixture_path,
                json_output_path=temp_path / "result.json",
                markdown_output_path=temp_path / "report.md",
            )

        self.assertEqual(keyed_result["review_summary"]["review_records_read"], 1)
        self.assertEqual(keyed_result["review_summary"]["review_records_accepted"], 1)
        self.assertEqual(keyed_result["accepted_review_records"][0]["market_id"], "563650")

    def test_gate_uses_standard_library_only(self):
        tree = ast.parse(GATE.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "copy", "importlib", "json", "pathlib", "sys"})

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
