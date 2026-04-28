import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
GATE = ROOT / "pm_bot" / "paper" / "validate_final_dossier_paper_readiness.py"
JSON_RESULT = ROOT / "pm_bot" / "paper" / "final_dossier_paper_readiness_result.v1.json"
MARKDOWN_REPORT = ROOT / "pm_bot" / "paper" / "final_dossier_paper_readiness_report.v1.md"
EXPECTED_JSON_RESULT = ROOT / "pm_bot" / "paper" / "expected_final_dossier_paper_readiness_result.v1.json"
SOURCE_DRAFTS = ROOT / "pm_bot" / "research" / "selected_ingest_final_dossier_drafts.v1.json"

EXPECTED_SUMMARY = {
    "final_dossier_drafts_read": 1,
    "readiness_records_written": 1,
    "eligible_for_future_paper_policy_review": 1,
    "needs_manual_dossier_repair": 0,
    "blocked_by_prohibited_content": 0,
    "paper_orders_created": 0,
}
PROHIBITED_OUTPUT_FIELD_TOKENS = {
    "score",
    "signal",
    "probability",
    "expected_value",
    "ev",
    "side",
    "yes_no_decision",
    "recommendation",
}


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
    spec = importlib.util.spec_from_file_location("final_dossier_paper_readiness_gate", GATE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_result():
    _run_gate()
    return _load_json(JSON_RESULT)


def _source_draft():
    return dict(_load_json(SOURCE_DRAFTS)["final_dossier_drafts"][0])


def _build_with_draft(draft):
    module = _load_module()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        source_payload = _load_json(SOURCE_DRAFTS)
        payload = dict(source_payload)
        payload["final_dossier_drafts"] = [draft]
        draft_path = temp_path / "drafts.json"
        draft_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        return module.build_final_dossier_paper_readiness_result(
            final_dossier_drafts_path=draft_path,
            json_output_path=temp_path / "result.json",
            markdown_output_path=temp_path / "report.md",
            expected_json_output_path=temp_path / "expected.json",
        )


def _field_tokens(key):
    lower = str(key).lower()
    normalized = []
    current = []
    for char in lower:
        if char.isalnum() or char == "_":
            current.append(char)
        else:
            if current:
                normalized.extend("".join(current).split("_"))
                current = []
    if current:
        normalized.extend("".join(current).split("_"))
    return {token for token in normalized if token} | {lower}


def _walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _check_map(record):
    return {item["check_id"]: item["passed"] for item in record["readiness_checks"]}


class FinalDossierPaperReadinessGateTests(unittest.TestCase):
    def test_default_export_matches_expected_json_result(self):
        _run_gate()

        self.assertEqual(_load_json(JSON_RESULT), _load_json(EXPECTED_JSON_RESULT))

    def test_final_dossier_draft_for_market_824952_is_read(self):
        result = _load_result()

        self.assertEqual(result["exported_market_ids"], ["824952"])
        self.assertEqual(result["readiness_summary"], EXPECTED_SUMMARY)
        self.assertEqual(len(result["readiness_records"]), 1)
        self.assertEqual(result["readiness_records"][0]["market_id"], "824952")
        self.assertEqual(result["readiness_records"][0]["final_draft_status"], "final_dossier_draft_only")

    def test_eligible_readiness_status_is_structural_only(self):
        result = _load_result()
        record = result["readiness_records"][0]
        checks = _check_map(record)

        self.assertEqual(record["readiness_status"], "eligible_for_future_paper_policy_review")
        self.assertTrue(record["structural_only"])
        self.assertTrue(record["future_paper_policy_review_only"])
        self.assertEqual(record["paper_orders_created"], 0)
        for check_id in result["required_readiness_checks"]:
            self.assertTrue(checks[check_id], msg=f"required readiness check failed: {check_id}")

    def test_missing_required_sections_produce_manual_dossier_repair(self):
        draft = _source_draft()
        draft["resolution_criteria_summary"] = ""
        draft["evidence_summary_by_source"] = []
        draft.pop("open_questions")
        result = _build_with_draft(draft)
        record = result["readiness_records"][0]

        self.assertEqual(record["readiness_status"], "needs_manual_dossier_repair")
        self.assertIn("missing_resolution_criteria_summary", record["failure_codes"])
        self.assertIn("missing_evidence_summary_by_source", record["failure_codes"])
        self.assertIn("missing_open_questions_field", record["failure_codes"])

    def test_non_final_dossier_draft_status_produces_manual_dossier_repair(self):
        draft = _source_draft()
        draft["final_draft_status"] = "completed_dossier"
        result = _build_with_draft(draft)
        record = result["readiness_records"][0]

        self.assertEqual(record["readiness_status"], "needs_manual_dossier_repair")
        self.assertIn("invalid_final_draft_status", record["failure_codes"])

    def test_prohibited_recommendation_trading_probability_ev_side_and_market_decision_fields_block(self):
        prohibited_fields = (
            "recommendation",
            "order",
            "trade",
            "execution",
            "probability",
            "expected_value",
            "ev",
            "side",
            "yes_no_decision",
            "buy",
            "sell",
            "market_decision",
            "score",
            "signal",
        )
        for field in prohibited_fields:
            with self.subTest(field=field):
                draft = _source_draft()
                draft[field] = "prohibited"
                result = _build_with_draft(draft)
                record = result["readiness_records"][0]

                self.assertEqual(record["readiness_status"], "blocked_by_prohibited_content")
                self.assertIn(field, record["blocking_paths"])

    def test_nested_prohibited_trade_field_blocks(self):
        draft = _source_draft()
        draft["final_draft_sections"]["nested"] = {"order": "prohibited"}
        result = _build_with_draft(draft)
        record = result["readiness_records"][0]

        self.assertEqual(record["readiness_status"], "blocked_by_prohibited_content")
        self.assertIn("final_draft_sections.nested.order", record["blocking_paths"])

    def test_no_paper_orders_are_created(self):
        result = _load_result()

        self.assertEqual(result["readiness_summary"]["paper_orders_created"], 0)
        self.assertEqual(result["readiness_records"][0]["paper_orders_created"], 0)
        self.assertFalse(result["safety"]["paper_orders"])

    def test_no_score_probability_ev_side_or_recommendation_fields_exist_in_accepted_record(self):
        result = _load_result()
        record = result["readiness_records"][0]

        self.assertEqual(record["readiness_status"], "eligible_for_future_paper_policy_review")
        for key in _walk_keys(record):
            self.assertTrue(
                PROHIBITED_OUTPUT_FIELD_TOKENS.isdisjoint(_field_tokens(key)),
                msg=f"accepted readiness record contains prohibited output key: {key}",
            )

    def test_markdown_report_has_stable_headings_and_summary_counts(self):
        result = _load_result()
        markdown = MARKDOWN_REPORT.read_text(encoding="utf-8")

        heading_lines = [line for line in markdown.splitlines() if line.startswith("#")]
        self.assertEqual(
            heading_lines,
            [
                "# PMBOT Final Dossier Paper Readiness Gate v1",
                "## Summary",
                "## Readiness Records",
                "### 824952",
                "#### Checks",
                "## Safety Boundary",
                "## Limitations",
            ],
        )
        for field, expected in EXPECTED_SUMMARY.items():
            self.assertIn(f"- {field}: {expected}", markdown)
        self.assertIn("  - 824952", markdown)
        self.assertIn("- readiness_status: eligible_for_future_paper_policy_review", markdown)
        self.assertEqual(result["readiness_summary"], EXPECTED_SUMMARY)

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
            "validate_final_dossier_paper_readiness",
            "final_dossier_paper_readiness_result",
            "final_dossier_paper_readiness_report",
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
