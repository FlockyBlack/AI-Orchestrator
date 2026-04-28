import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
GATE = ROOT / "pm_bot" / "research" / "validate_selected_ingest_dossier_human_review_records.py"
JSON_RESULT = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_human_review_records_result.v1.json"
MARKDOWN_REPORT = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_human_review_records_report.v1.md"
EXPECTED_JSON_RESULT = ROOT / "pm_bot" / "research" / "expected_selected_ingest_dossier_human_review_records_result.v1.json"

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
PROHIBITED_COMPLETED_LANGUAGE = {
    "completed_dossier",
    "final_dossier",
    "bet_recommendation",
    "trade_recommendation",
    "market_decision",
}
ALLOWED_COMPLETED_LANGUAGE_VALUES = {"approved_for_final_dossier_draft"}


def _run_gate(*extra_args):
    return subprocess.run(
        [sys.executable, str(GATE), *extra_args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _load_module():
    spec = importlib.util.spec_from_file_location("selected_ingest_dossier_human_review_record_gate", GATE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_result():
    _run_gate()
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


def _language_key(text):
    return str(text).lower().replace("-", "_").replace(" ", "_")


def _walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _walk_strings(value):
    if isinstance(value, dict):
        for nested in value.values():
            yield from _walk_strings(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, str):
        yield value


def _approved_review_record(market_id):
    return {
        "market_id": market_id,
        "human_review_status": "review_completed",
        "human_review_outcome": "approved_for_final_dossier_draft",
        "reviewer_notes": "Selected ingest approval test record with all required checks.",
        "review_checks": {
            "evidence_matches_resolution_criteria": True,
            "uncertainty_register_reviewed": True,
            "missing_information_reviewed": True,
            "no_trading_recommendation_present": True,
            "no_probability_or_ev_present": True,
            "no_side_recommendation_present": True,
            "no_market_decision_present": True,
        },
        "requested_revision_items": [],
        "quality_flags": [],
        "next_manual_action": "prepare_future_draft_artifact",
    }


def _build_with_records(records):
    module = _load_module()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        fixture_path = temp_path / "selected_ingest_human_review_records.json"
        fixture_path.write_text(
            json.dumps({"human_review_records": records}, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        return module.build_selected_ingest_dossier_human_review_record_result(
            review_records_path=fixture_path,
            json_output_path=temp_path / "result.json",
            markdown_output_path=temp_path / "report.md",
            expected_json_output_path=temp_path / "expected.json",
        )


class SelectedIngestDossierHumanReviewRecordGateTests(unittest.TestCase):
    def test_default_export_matches_expected_json_result(self):
        _run_gate()

        self.assertEqual(_load_json(JSON_RESULT), _load_json(EXPECTED_JSON_RESULT))

    def test_valid_human_review_record_for_market_824952_is_accepted(self):
        result = _load_result()
        accepted = result["accepted_human_review_records"]

        self.assertEqual(result["selected_market_ids"], EXPECTED_SELECTED_MARKET_IDS)
        self.assertEqual(result["review_pack_market_ids"], ["824952"])
        self.assertEqual(len(accepted), 1)
        self.assertEqual(accepted[0]["market_id"], "824952")
        self.assertEqual(accepted[0]["human_review_status"], "review_completed")
        self.assertEqual(accepted[0]["human_review_outcome"], "approved_for_final_dossier_draft")
        for check in result["required_approval_review_checks"]:
            self.assertIs(accepted[0]["review_checks"][check], True)

    def test_unknown_market_id_is_rejected(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["unknown-market-id"]

        self.assertIn("unknown_market_id", _codes(errors))

    def test_selected_market_id_not_present_in_human_review_pack_is_rejected(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["692258"]

        self.assertIn("selected_market_id_not_in_review_pack", _codes(errors))

    def test_immutable_review_pack_field_override_is_rejected(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["824952"]

        self.assertIn("immutable_review_pack_field_override:title_question", _codes(errors))

    def test_prohibited_trading_execution_recommendation_fields_are_rejected(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["824952"]
        codes = _codes(errors)

        for field in (
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
        ):
            self.assertIn(f"prohibited_human_review_field:{field}", codes)
            self.assertIn(f"unexpected_human_review_field:{field}", codes)

    def test_probability_ev_score_side_and_market_decision_fields_are_rejected(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["824952"]
        codes = _codes(errors)

        for field in (
            "probability",
            "expected_value",
            "ev",
            "score",
            "signal",
            "side",
            "yes_no_decision",
            "buy",
            "sell",
            "market_decision",
        ):
            self.assertIn(f"prohibited_human_review_field:{field}", codes)
            self.assertIn(f"unexpected_human_review_field:{field}", codes)

    def test_approved_for_final_dossier_draft_requires_all_required_review_checks(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["824952"]
        codes = _codes(errors)

        self.assertIn("required_approval_review_check_not_true:no_probability_or_ev_present", codes)
        self.assertIn("required_approval_review_check_not_true:no_market_decision_present", codes)

    def test_needs_draft_revision_requires_requested_revision_items(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["824952"]

        self.assertIn("needs_draft_revision_requires_requested_revision_items", _codes(errors))

    def test_rejected_for_research_quality_requires_reviewer_notes(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["824952"]

        self.assertIn("rejected_for_research_quality_requires_reviewer_notes", _codes(errors))

    def test_completed_and_final_dossier_language_is_rejected_and_not_accepted(self):
        result = _load_result()
        errors = result["errors_by_market_id"]["824952"]
        codes = _codes(errors)

        for phrase in PROHIBITED_COMPLETED_LANGUAGE:
            self.assertIn(f"prohibited_dossier_language:{phrase}", codes)
        for record in result["accepted_human_review_records"]:
            for text in _walk_strings(record):
                if text in ALLOWED_COMPLETED_LANGUAGE_VALUES:
                    continue
                normalized = _language_key(text)
                for phrase in PROHIBITED_COMPLETED_LANGUAGE:
                    self.assertNotIn(phrase, normalized)

    def test_accepted_records_contain_no_betting_trading_score_probability_ev_or_market_decision_fields(self):
        result = _load_result()
        for record in result["accepted_human_review_records"]:
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
                "# Selected Ingest Dossier Human Review Records v1",
                "## Summary",
                "## Selected Market IDs",
                "## Review Pack Market IDs",
                "## Accepted Human Review Records",
                "### record 0: 824952",
                "## Rejected Human Review Records",
                "### record 2: 692258",
                "### record 3: 824952",
                "### record 4: 824952",
                "### record 5: 824952",
                "### record 6: 824952",
                "### record 7: 824952",
                "### record 8: 824952",
                "### record 9: 824952",
                "### record 1: unknown-market-id",
                "## Errors By Market ID",
                "### 692258",
                "### 824952",
                "### unknown-market-id",
                "## Safety Boundary",
                "## Limitations",
            ],
        )
        expected_summary = {
            "review_records_read": 10,
            "review_records_accepted": 1,
            "review_records_rejected": 9,
            "approved_for_final_dossier_draft": 1,
            "needs_draft_revision": 0,
            "rejected_for_research_quality": 0,
            "watch_only": 0,
        }
        self.assertEqual(summary, expected_summary)
        for field, expected in expected_summary.items():
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

    def test_keyed_human_review_record_payload_is_supported_for_review_pack_market(self):
        module = _load_module()
        keyed_payload = {
            "schema_version": "selected-keyed-dossier-human-review-records-test.v1",
            "824952": _approved_review_record("824952"),
        }
        keyed_payload["824952"].pop("market_id")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fixture_path = temp_path / "keyed_records.json"
            fixture_path.write_text(json.dumps(keyed_payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            result = module.build_selected_ingest_dossier_human_review_record_result(
                review_records_path=fixture_path,
                json_output_path=temp_path / "result.json",
                markdown_output_path=temp_path / "report.md",
                expected_json_output_path=temp_path / "expected.json",
            )

        self.assertEqual(result["review_summary"]["review_records_read"], 1)
        self.assertEqual(result["review_summary"]["review_records_accepted"], 1)
        self.assertEqual(result["accepted_human_review_records"][0]["market_id"], "824952")

    def test_custom_valid_revision_record_is_accepted_for_review_pack_market(self):
        result = _build_with_records([
            {
                "market_id": "824952",
                "human_review_status": "needs_revision",
                "human_review_outcome": "needs_draft_revision",
                "reviewer_notes": "Needs targeted draft edits.",
                "review_checks": {},
                "requested_revision_items": ["Add source timing note."],
                "quality_flags": [],
                "next_manual_action": "revise_notes",
            }
        ])

        self.assertEqual(result["review_summary"]["review_records_accepted"], 1)
        self.assertEqual(result["review_summary"]["needs_draft_revision"], 1)

    def test_selected_market_id_without_pack_cannot_be_accepted_from_custom_records(self):
        result = _build_with_records([_approved_review_record("692258")])
        rejected = result["rejected_human_review_records"][0]

        self.assertEqual(result["review_summary"]["review_records_accepted"], 0)
        self.assertIn("selected_market_id_not_in_review_pack", _codes(rejected["errors"]))

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
            "validate_selected_ingest_dossier_human_review_records",
            "selected_ingest_dossier_human_review_records",
            "selected_ingest_dossier_human_review_record_gate",
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
