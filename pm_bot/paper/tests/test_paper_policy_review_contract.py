import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CONTRACT = ROOT / "pm_bot" / "paper" / "validate_paper_policy_review_contract.py"
FIXTURE = ROOT / "pm_bot" / "paper" / "paper_policy_review_records_fixture.v1.json"
JSON_RESULT = ROOT / "pm_bot" / "paper" / "paper_policy_review_result.v1.json"
MARKDOWN_REPORT = ROOT / "pm_bot" / "paper" / "paper_policy_review_report.v1.md"
EXPECTED_JSON_RESULT = ROOT / "pm_bot" / "paper" / "expected_paper_policy_review_result.v1.json"

EXPECTED_SUMMARY = {
    "policy_records_read": 4,
    "policy_records_accepted": 1,
    "policy_records_rejected": 3,
    "eligible_for_future_paper_decision_simulation": 1,
    "watch_only_policy_review": 0,
    "needs_more_manual_review": 1,
    "blocked_by_policy": 2,
    "paper_orders_created": 0,
}
PROHIBITED_OUTPUT_FIELD_TOKENS = {
    "order",
    "orders",
    "recommendation",
    "recommendations",
    "score",
    "scores",
    "probability",
    "probabilities",
    "expected_value",
    "expected_values",
    "ev",
    "side",
    "sides",
}
PROHIBITED_FIELDS = (
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
    "market_decision",
)


def _frag(*parts):
    return "".join(parts)


def _run_contract(*extra_args):
    return subprocess.run(
        [sys.executable, str(CONTRACT), *extra_args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _load_module():
    spec = importlib.util.spec_from_file_location("paper_policy_review_contract", CONTRACT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_result():
    _run_contract()
    return _load_json(JSON_RESULT)


def _fixture_records():
    return _load_json(FIXTURE)["policy_review_records"]


def _valid_record():
    return dict(_fixture_records()[0])


def _build_with_records(records):
    module = _load_module()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        payload = dict(_load_json(FIXTURE))
        payload["policy_review_records"] = records
        fixture_path = temp_path / "policy_records.json"
        fixture_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        return module.build_paper_policy_review_result(
            policy_records_path=fixture_path,
            json_output_path=temp_path / "result.json",
            markdown_output_path=temp_path / "report.md",
            expected_json_output_path=temp_path / "expected.json",
        )


def _record_by_id(result, record_id):
    for record in result["policy_records"]:
        if record["record_id"] == record_id:
            return record
    raise AssertionError(f"missing record_id: {record_id}")


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
    return {token for token in tokens if token}


def _walk_keys(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield key
            yield from _walk_keys(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


class PaperPolicyReviewContractTests(unittest.TestCase):
    def test_default_export_matches_expected_json_result(self):
        _run_contract()

        self.assertEqual(_load_json(JSON_RESULT), _load_json(EXPECTED_JSON_RESULT))

    def test_valid_policy_review_record_for_market_824952_is_accepted(self):
        result = _load_result()
        record = _record_by_id(result, "policy-review-824952-valid")

        self.assertEqual(result["market_ids"], ["824952"])
        self.assertEqual(result["policy_summary"], EXPECTED_SUMMARY)
        self.assertEqual(record["market_id"], "824952")
        self.assertEqual(record["readiness_status"], "eligible_for_future_paper_policy_review")
        self.assertEqual(record["future_policy_status"], "eligible_for_future_paper_decision_simulation")
        self.assertEqual(record["record_validation_status"], "accepted")
        self.assertEqual(record["failure_codes"], [])
        self.assertTrue(all(item["passed"] for item in record["checks"]))

    def test_unknown_market_id_is_rejected(self):
        result = _load_result()
        record = _record_by_id(result, "policy-review-unknown-market")

        self.assertEqual(record["record_validation_status"], "rejected")
        self.assertEqual(record["future_policy_status"], "blocked_by_policy")
        self.assertIn("unknown_market_id", record["failure_codes"])
        self.assertFalse(record["source_readiness_record_found"])
        self.assertFalse(record["source_final_dossier_draft_found"])

    def test_incomplete_required_policy_checks_are_rejected(self):
        result = _load_result()
        record = _record_by_id(result, "policy-review-824952-incomplete")

        self.assertEqual(record["record_validation_status"], "rejected")
        self.assertEqual(record["future_policy_status"], "needs_more_manual_review")
        self.assertIn("missing_policy_check:evidence_inventory_present", record["failure_codes"])
        self.assertIn("policy_checks", record["blocking_paths"])

    def test_non_eligible_readiness_status_is_rejected(self):
        record = _valid_record()
        record["readiness_status"] = "needs_manual_dossier_repair"
        result = _build_with_records([record])
        output_record = result["policy_records"][0]

        self.assertEqual(output_record["record_validation_status"], "rejected")
        self.assertEqual(output_record["future_policy_status"], "blocked_by_policy")
        self.assertIn("invalid_record_readiness_status", output_record["failure_codes"])

    def test_prohibited_trading_recommendation_probability_ev_side_and_market_decision_fields_are_rejected(self):
        for field in PROHIBITED_FIELDS:
            with self.subTest(field=field):
                record = _valid_record()
                record[field] = "prohibited"
                result = _build_with_records([record])
                output_record = result["policy_records"][0]

                self.assertEqual(output_record["record_validation_status"], "rejected")
                self.assertEqual(output_record["future_policy_status"], "blocked_by_policy")
                self.assertIn(field, output_record["blocking_paths"])

    def test_nested_prohibited_field_is_rejected(self):
        record = _valid_record()
        record["policy_payload"] = {"market_decision": "prohibited"}
        result = _build_with_records([record])
        output_record = result["policy_records"][0]

        self.assertEqual(output_record["record_validation_status"], "rejected")
        self.assertEqual(output_record["future_policy_status"], "blocked_by_policy")
        self.assertIn("policy_payload.market_decision", output_record["blocking_paths"])

    def test_accepted_output_contains_no_side_recommendation_score_probability_ev_or_order_fields(self):
        result = _load_result()
        record = _record_by_id(result, "policy-review-824952-valid")

        self.assertEqual(record["record_validation_status"], "accepted")
        for key in _walk_keys(record):
            self.assertTrue(
                PROHIBITED_OUTPUT_FIELD_TOKENS.isdisjoint(_field_tokens(key)),
                msg=f"accepted policy record contains prohibited output key: {key}",
            )

    def test_no_paper_orders_are_created(self):
        result = _load_result()

        self.assertEqual(result["policy_summary"]["paper_orders_created"], 0)
        self.assertFalse(result["safety"]["paper_orders"])

    def test_markdown_report_has_stable_headings_and_summary_counts(self):
        result = _load_result()
        markdown = MARKDOWN_REPORT.read_text(encoding="utf-8")

        heading_lines = [line for line in markdown.splitlines() if line.startswith("#")]
        self.assertEqual(
            heading_lines,
            [
                "# PMBOT Paper Policy Review Contract v1",
                "## Summary",
                "## Policy Records",
                "### policy-review-824952-valid",
                "#### Checks",
                "### policy-review-824952-incomplete",
                "#### Checks",
                "### policy-review-824952-prohibited-field",
                "#### Checks",
                "### policy-review-unknown-market",
                "#### Checks",
                "## Safety Boundary",
                "## Limitations",
            ],
        )
        for field, expected in EXPECTED_SUMMARY.items():
            self.assertIn(f"- {field}: {expected}", markdown)
        self.assertIn("  - 824952", markdown)
        self.assertIn("- future_policy_status: eligible_for_future_paper_decision_simulation", markdown)
        self.assertEqual(result["policy_summary"], EXPECTED_SUMMARY)

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

            first = _run_contract(*args)
            first_json = json_path.read_text(encoding="utf-8")
            first_markdown = markdown_path.read_text(encoding="utf-8")
            second = _run_contract(*args)

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
            "validate_paper_policy_review_contract",
            "paper_policy_review_result",
            "paper_policy_review_report",
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

    def test_contract_uses_standard_library_only(self):
        tree = ast.parse(CONTRACT.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "sys"})

    def test_contract_has_no_live_fetcher_runtime_or_downstream_automation_imports(self):
        source = CONTRACT.read_text(encoding="utf-8").lower()
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
