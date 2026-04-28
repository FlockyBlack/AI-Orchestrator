import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
GATE = ROOT / "pm_bot" / "research" / "validate_manual_dossier_drafts.py"
FIXTURE = ROOT / "pm_bot" / "research" / "manual_dossier_drafts_fixture.v1.json"
JSON_RESULT = ROOT / "pm_bot" / "research" / "manual_dossier_draft_validation_result.v1.json"
MARKDOWN_REPORT = ROOT / "pm_bot" / "research" / "manual_dossier_draft_validation_report.v1.md"
EXPECTED_JSON_RESULT = ROOT / "pm_bot" / "research" / "expected_manual_dossier_draft_validation_result.v1.json"


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
    "ev",
    "side",
    "yes_no_decision",
    "buy",
    "sell",
}
PROHIBITED_COMPLETED_LANGUAGE = {
    "completed_dossier",
    "final_dossier",
    "bet_recommendation",
    "trade_recommendation",
    "market_decision",
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
    spec = importlib.util.spec_from_file_location("manual_dossier_draft_quality_gate", GATE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_result():
    return _load_json(JSON_RESULT)


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


def _language_key(text):
    return str(text).lower().replace("-", "_").replace(" ", "_")


def _walk_strings(value):
    if isinstance(value, dict):
        for nested in value.values():
            yield from _walk_strings(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, str):
        yield value


def _build_with_records(records):
    module = _load_module()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        fixture_path = temp_path / "manual_drafts.json"
        fixture_path.write_text(json.dumps({"draft_records": records}, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        return module.build_manual_dossier_draft_validation_result(
            draft_records_path=fixture_path,
            json_output_path=temp_path / "result.json",
            markdown_output_path=temp_path / "report.md",
            expected_json_output_path=temp_path / "expected.json",
        )


class ManualDossierDraftQualityGateTests(unittest.TestCase):
    def test_default_export_matches_expected_json_result(self):
        _run_gate()
        self.assertEqual(_load_json(JSON_RESULT), _load_json(EXPECTED_JSON_RESULT))

    def test_valid_manual_draft_for_exported_market_is_accepted(self):
        result = _load_result()
        accepted = result["accepted_draft_records"]

        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0]["market_id"], "563650")
        self.assertEqual(accepted[0]["draft_status"], "draft_ready_for_human_review")
        self.assertEqual(accepted[0]["next_manual_action"], "human_review_required")

    def test_unknown_market_id_is_rejected(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["unknown-market-id"]

        self.assertIn("unknown_market_id", _codes(errors))

    def test_non_skeleton_market_id_is_rejected(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["569366"]

        self.assertIn("non_skeleton_market_id", _codes(errors))

    def test_immutable_skeleton_field_override_is_rejected(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["563650"]

        self.assertIn("immutable_skeleton_field_override:title_question", _codes(errors))

    def test_prohibited_trading_execution_and_recommendation_fields_are_rejected(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["563650"]
        codes = _codes(errors)

        self.assertIn("prohibited_draft_field:trade", codes)
        self.assertIn("prohibited_draft_field:execution", codes)
        self.assertIn("prohibited_draft_field:order", codes)
        self.assertIn("prohibited_draft_field:wallet", codes)
        self.assertIn("prohibited_draft_field:recommendation", codes)

    def test_probability_ev_score_and_side_fields_are_rejected(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["563650"]
        codes = _codes(errors)

        self.assertIn("prohibited_draft_field:probability", codes)
        self.assertIn("prohibited_draft_field:expected_value", codes)
        self.assertIn("prohibited_draft_field:ev", codes)
        self.assertIn("prohibited_draft_field:score", codes)
        self.assertIn("prohibited_draft_field:side", codes)
        self.assertIn("prohibited_draft_field:yes_no_decision", codes)

    def test_ready_for_human_review_requires_required_sections(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["563650"]
        codes = _codes(errors)

        for field in result["required_ready_sections"]:
            self.assertIn(f"required_ready_section_empty:{field}", codes)

    def test_completed_dossier_language_is_rejected_and_not_accepted(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["563650"]

        self.assertIn("prohibited_dossier_language:completed_dossier", _codes(errors))
        for record in result["accepted_draft_records"]:
            rendered = json.dumps(record, sort_keys=True)
            for phrase in PROHIBITED_COMPLETED_LANGUAGE:
                self.assertNotIn(phrase, _language_key(rendered))

    def test_accepted_records_contain_no_betting_trading_score_probability_or_ev_fields(self):
        result = _load_result()
        for record in result["accepted_draft_records"]:
            for key in _walk_keys(record):
                self.assertTrue(
                    PROHIBITED_FIELD_TOKENS.isdisjoint(_field_tokens(key)),
                    msg=f"{record['market_id']} contains prohibited accepted key {key}",
                )

    def test_accepted_records_contain_no_completed_dossier_language(self):
        result = _load_result()
        for record in result["accepted_draft_records"]:
            for text in _walk_strings(record):
                normalized = _language_key(text)
                for phrase in PROHIBITED_COMPLETED_LANGUAGE:
                    self.assertNotIn(phrase, normalized)

    def test_markdown_report_has_stable_headings_and_summary_counts(self):
        result = _load_result()
        markdown = MARKDOWN_REPORT.read_text(encoding="utf-8")
        summary = result["draft_validation_summary"]

        heading_lines = [line for line in markdown.splitlines() if line.startswith("#")]
        self.assertEqual(
            heading_lines,
            [
                "# PMBOT Manual Dossier Draft Validation v1",
                "## Summary",
                "## Accepted Draft Records",
                "### record 0: 563650",
                "## Rejected Draft Records",
                "### record 3: 563650",
                "### record 4: 563650",
                "### record 5: 563650",
                "### record 6: 563650",
                "### record 7: 563650",
                "### record 2: 569366",
                "### record 1: unknown-market-id",
                "## Errors By Market ID",
                "### 563650",
                "### 569366",
                "### unknown-market-id",
                "## Limitations",
            ],
        )
        expected_summary = {
            "draft_records_read": 8,
            "draft_records_accepted": 1,
            "draft_records_rejected": 7,
            "draft_ready_for_human_review": 1,
            "needs_more_information": 0,
            "draft_incomplete": 0,
            "draft_rejected": 0,
        }
        self.assertEqual(summary, expected_summary)
        for field, expected in expected_summary.items():
            self.assertIn(f"- {field}: {expected}", markdown)
        self.assertIn("- 563650: 29", markdown)
        self.assertIn("- 569366: 1", markdown)
        self.assertIn("- unknown-market-id: 1", markdown)

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

    def test_keyed_draft_payload_is_supported(self):
        ready_record = {
            "draft_status": "draft_ready_for_human_review",
            "market_context_notes": "Keyed draft context note.",
            "resolution_criteria_notes": "Keyed draft resolution note.",
            "evidence_summary_by_source": ["Keyed draft source note."],
            "uncertainty_register": ["Keyed draft uncertainty note."],
            "missing_information_review": "Keyed draft missing information note.",
            "operator_review_notes": "Keyed draft operator note.",
            "next_manual_action": "human_review_required",
        }
        module = _load_module()
        keyed_payload = {
            "schema_version": "keyed-manual-dossier-drafts-test.v1",
            "563650": ready_record,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fixture_path = temp_path / "keyed_drafts.json"
            fixture_path.write_text(json.dumps(keyed_payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            result = module.build_manual_dossier_draft_validation_result(
                draft_records_path=fixture_path,
                json_output_path=temp_path / "result.json",
                markdown_output_path=temp_path / "report.md",
                expected_json_output_path=temp_path / "expected.json",
            )

        self.assertEqual(result["draft_validation_summary"]["draft_records_read"], 1)
        self.assertEqual(result["draft_validation_summary"]["draft_records_accepted"], 1)
        self.assertEqual(result["accepted_draft_records"][0]["market_id"], "563650")

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
