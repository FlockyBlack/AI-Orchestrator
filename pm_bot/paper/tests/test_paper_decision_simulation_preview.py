import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EXPORTER = ROOT / "pm_bot" / "paper" / "export_paper_decision_simulation_preview.py"
POLICY_RESULT = ROOT / "pm_bot" / "paper" / "paper_policy_review_result.v1.json"
SOURCE_DRAFTS = ROOT / "pm_bot" / "research" / "selected_ingest_final_dossier_drafts.v1.json"
JSON_RESULT = ROOT / "pm_bot" / "paper" / "paper_decision_simulation_preview.v1.json"
MARKDOWN_REPORT = ROOT / "pm_bot" / "paper" / "paper_decision_simulation_preview.v1.md"
EXPECTED_JSON_RESULT = ROOT / "pm_bot" / "paper" / "expected_paper_decision_simulation_preview.v1.json"

READY_STATUS = "ready_for_future_paper_decision_policy_design"
EXPECTED_SUMMARY = {
    "policy_records_read": 4,
    "preview_records_written": 1,
    READY_STATUS: 1,
    "needs_more_manual_review": 0,
    "blocked_by_policy": 0,
    "paper_orders_created": 0,
}
EXPECTED_PREVIEW_FIELDS = [
    "market_id",
    "title_question",
    "event_id",
    "event_title",
    "category",
    "packet_type",
    "deadline",
    "current_yes_price",
    "liquidity",
    "volume",
    "resolution_criteria_summary",
    "evidence_inventory_summary",
    "uncertainty_register_summary",
    "missing_information_review",
    "open_questions",
    "human_review_summary",
    "paper_readiness_status",
    "paper_policy_status",
    "simulation_preview_status",
    "blocked_reasons",
    "next_manual_action",
]
PROHIBITED_OUTPUT_FIELD_TOKENS = {
    "order",
    "orders",
    "trade",
    "trades",
    "wallet",
    "private_key",
    "execution",
    "recommendation",
    "recommendations",
    "bet",
    "stake",
    "size",
    "entry_price",
    "limit_price",
    "price_target",
    "score",
    "scores",
    "signal",
    "signals",
    "probability",
    "probabilities",
    "expected_value",
    "expected_values",
    "ev",
    "side",
    "sides",
    "yes_no_decision",
    "buy",
    "sell",
    "market_decision",
    "market_decisions",
}


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
    spec = importlib.util.spec_from_file_location("paper_decision_simulation_preview", EXPORTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_result():
    _run_exporter()
    return _load_json(JSON_RESULT)


def _policy_payload():
    return _load_json(POLICY_RESULT)


def _drafts_payload():
    return _load_json(SOURCE_DRAFTS)


def _build_with_payloads(policy_payload=None, drafts_payload=None):
    module = _load_module()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        policy_path = temp_path / "policy_result.json"
        drafts_path = temp_path / "drafts.json"
        policy_path.write_text(
            json.dumps(policy_payload or _policy_payload(), indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        drafts_path.write_text(
            json.dumps(drafts_payload or _drafts_payload(), indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        return module.build_paper_decision_simulation_preview(
            policy_review_result_path=policy_path,
            final_dossier_drafts_path=drafts_path,
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


class PaperDecisionSimulationPreviewTests(unittest.TestCase):
    def test_default_export_matches_expected_json_result(self):
        _run_exporter()

        self.assertEqual(_load_json(JSON_RESULT), _load_json(EXPECTED_JSON_RESULT))

    def test_market_824952_is_exported_from_eligible_policy_record(self):
        result = _load_result()

        self.assertEqual(result["market_ids"], ["824952"])
        self.assertEqual(result["preview_summary"], EXPECTED_SUMMARY)
        self.assertEqual(len(result["preview_records"]), 1)

        record = result["preview_records"][0]
        self.assertEqual(list(record), EXPECTED_PREVIEW_FIELDS)
        self.assertEqual(record["market_id"], "824952")
        self.assertEqual(record["paper_readiness_status"], "eligible_for_future_paper_policy_review")
        self.assertEqual(record["paper_policy_status"], "eligible_for_future_paper_decision_simulation")
        self.assertEqual(record["simulation_preview_status"], READY_STATUS)
        self.assertEqual(record["next_manual_action"], "design_paper_decision_policy")
        self.assertEqual(record["blocked_reasons"], [])

    def test_non_eligible_policy_records_are_skipped(self):
        payload = _policy_payload()
        for record in payload["policy_records"]:
            record["future_policy_status"] = "blocked_by_policy"

        result = _build_with_payloads(policy_payload=payload)

        self.assertEqual(result["preview_records"], [])
        self.assertEqual(result["market_ids"], [])
        self.assertEqual(result["preview_summary"]["policy_records_read"], 4)
        self.assertEqual(result["preview_summary"]["preview_records_written"], 0)
        self.assertEqual(result["preview_summary"][READY_STATUS], 0)

    def test_simulation_preview_status_is_deterministic(self):
        first = _load_result()
        second = _load_result()

        self.assertEqual(first["preview_records"][0]["simulation_preview_status"], READY_STATUS)
        self.assertEqual(first, second)

    def test_no_side_decision_recommendation_score_probability_ev_or_order_fields_are_emitted(self):
        result = _load_result()
        record = result["preview_records"][0]

        self.assertNotIn("yes_no_decision", record)
        self.assertNotIn("market_decision", record)
        for key in _walk_keys(record):
            self.assertTrue(
                PROHIBITED_OUTPUT_FIELD_TOKENS.isdisjoint(_field_tokens(key)),
                msg=f"preview record contains prohibited output key: {key}",
            )

    def test_no_paper_orders_are_created(self):
        result = _load_result()

        self.assertEqual(result["preview_summary"]["paper_orders_created"], 0)
        self.assertEqual(result["preview_records"][0]["blocked_reasons"], [])

    def test_prohibited_policy_record_content_is_blocked_deterministically(self):
        payload = _policy_payload()
        payload["policy_records"][0]["policy_payload"] = {"probability": "prohibited"}

        result = _build_with_payloads(policy_payload=payload)
        record = result["preview_records"][0]

        self.assertEqual(record["market_id"], "824952")
        self.assertEqual(record["simulation_preview_status"], "blocked_by_policy")
        self.assertEqual(record["next_manual_action"], "stop_policy_blocked")
        self.assertEqual(record["blocked_reasons"], ["prohibited_field_name_in_policy_record"])

    def test_missing_structural_preview_content_needs_manual_review(self):
        drafts_payload = _drafts_payload()
        draft = drafts_payload["final_dossier_drafts"][0]
        draft["human_review_notes"] = ""
        draft["final_draft_sections"]["human_review_summary"]["human_review_notes"] = ""

        result = _build_with_payloads(drafts_payload=drafts_payload)
        record = result["preview_records"][0]

        self.assertEqual(record["simulation_preview_status"], "needs_more_manual_review")
        self.assertEqual(record["next_manual_action"], "add_manual_review")
        self.assertEqual(record["blocked_reasons"], ["missing_preview_field:human_review_summary"])

    def test_markdown_report_has_stable_headings_and_summary_counts(self):
        result = _load_result()
        markdown = MARKDOWN_REPORT.read_text(encoding="utf-8")

        heading_lines = [line for line in markdown.splitlines() if line.startswith("#")]
        self.assertEqual(
            heading_lines,
            [
                "# PMBOT Paper Decision Simulation Preview v1",
                "## Summary",
                "## Preview Records",
                "### 824952",
                "## Limitations",
            ],
        )
        for field, expected in EXPECTED_SUMMARY.items():
            self.assertIn(f"- {field}: {expected}", markdown)
        self.assertIn("  - 824952", markdown)
        self.assertIn(f"- simulation_preview_status: {READY_STATUS}", markdown)
        self.assertEqual(result["preview_summary"], EXPECTED_SUMMARY)

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
            "export_paper_decision_simulation_preview",
            "paper_decision_simulation_preview",
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
