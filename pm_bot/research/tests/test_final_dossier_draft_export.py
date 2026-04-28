import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EXPORTER = ROOT / "pm_bot" / "research" / "export_final_dossier_drafts.py"
REVIEW_PACK = ROOT / "pm_bot" / "research" / "dossier_human_review_pack.v1.json"
REVIEW_RECORDS_RESULT = ROOT / "pm_bot" / "research" / "dossier_human_review_records_result.v1.json"
JSON_OUTPUT = ROOT / "pm_bot" / "research" / "final_dossier_drafts.v1.json"
MARKDOWN_OUTPUT = ROOT / "pm_bot" / "research" / "final_dossier_drafts.v1.md"
EXPECTED_JSON_OUTPUT = ROOT / "pm_bot" / "research" / "expected_final_dossier_drafts.v1.json"


PROHIBITED_FIELD_TOKENS = {
    "order",
    "orders",
    "trade",
    "trades",
    "trading",
    "wallet",
    "wallets",
    "private_key",
    "private_keys",
    "execution",
    "executions",
    "recommendation",
    "recommendations",
    "bet",
    "bets",
    "betting",
    "stake",
    "stakes",
    "size",
    "sizes",
    "entry_price",
    "entry_prices",
    "limit_price",
    "limit_prices",
    "price_target",
    "price_targets",
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
    "hold",
    "market_decision",
}
EXPECTED_SUMMARY = {
    "approved_review_records_seen": 1,
    "final_dossier_drafts_exported": 1,
    "review_records_skipped": 9,
    "completed_dossiers_created": 0,
}


def _run_exporter(*extra_args):
    return subprocess.run(
        [sys.executable, str(EXPORTER), *extra_args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


def _load_module():
    spec = importlib.util.spec_from_file_location("final_dossier_draft_exporter", EXPORTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_export():
    return _load_json(JSON_OUTPUT)


def _field_tokens(key):
    lower = str(key).lower()
    normalized_chars = []
    current = []
    for char in lower:
        if char.isalnum():
            current.append(char)
            normalized_chars.append(char)
        elif char == "_":
            if current:
                normalized_chars.append("_")
            current = []
        else:
            if current:
                normalized_chars.append("_")
            current = []
    normalized_key = "".join(normalized_chars).strip("_")
    tokens = {lower, normalized_key}
    tokens.update(token for token in normalized_key.split("_") if token)
    return {token for token in tokens if token}


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


def _approved_review_record():
    records = _load_json(REVIEW_RECORDS_RESULT)["accepted_human_review_records"]
    return dict(records[0])


class FinalDossierDraftExportTests(unittest.TestCase):
    def test_default_export_matches_expected_json(self):
        _run_exporter()
        self.assertEqual(_load_json(JSON_OUTPUT), _load_json(EXPECTED_JSON_OUTPUT))

    def test_only_approved_for_final_dossier_draft_records_are_exported(self):
        export = _load_export()
        drafts = export["final_dossier_drafts"]

        self.assertEqual(export["export_summary"], EXPECTED_SUMMARY)
        self.assertEqual(export["exported_market_ids"], ["563650"])
        self.assertEqual(len(drafts), 1)
        self.assertEqual(drafts[0]["market_id"], "563650")
        self.assertEqual(drafts[0]["final_draft_status"], "final_dossier_draft_only")

    def test_non_approved_records_are_skipped_without_context_lookup(self):
        module = _load_module()
        approved_record = _approved_review_record()
        watch_record = dict(approved_record)
        watch_record["record_index"] = 7
        watch_record["market_id"] = "569366"
        watch_record["human_review_outcome"] = "watch_only"
        watch_record["reviewer_notes"] = "Watch-only record must not produce a draft."
        custom_review_result = {
            "schema_version": "custom_review_result.v1",
            "review_summary": {
                "review_records_read": 2,
                "review_records_accepted": 2,
                "review_records_rejected": 0,
                "approved_for_final_dossier_draft": 1,
                "needs_draft_revision": 0,
                "rejected_for_research_quality": 0,
                "watch_only": 1,
            },
            "accepted_human_review_records": [watch_record, approved_record],
            "rejected_human_review_records": [],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            review_result_path = temp_path / "review_result.json"
            review_result_path.write_text(json.dumps(custom_review_result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            export = module.build_final_dossier_drafts_export(
                review_records_result_path=review_result_path,
                json_output_path=temp_path / "final.json",
                markdown_output_path=temp_path / "final.md",
                expected_json_output_path=temp_path / "expected.json",
            )

        self.assertEqual(export["exported_market_ids"], ["563650"])
        self.assertEqual(export["export_summary"]["approved_review_records_seen"], 1)
        self.assertEqual(export["export_summary"]["final_dossier_drafts_exported"], 1)
        self.assertEqual(export["export_summary"]["review_records_skipped"], 1)

    def test_final_draft_status_is_always_final_dossier_draft_only(self):
        export = _load_export()

        self.assertEqual(export["final_draft_status"], "final_dossier_draft_only")
        for draft in export["final_dossier_drafts"]:
            self.assertEqual(draft["final_draft_status"], "final_dossier_draft_only")

    def test_no_completed_dossier_language_is_emitted(self):
        export = _load_export()
        markdown = MARKDOWN_OUTPUT.read_text(encoding="utf-8").lower()
        item_text = json.dumps(export["final_dossier_drafts"], sort_keys=True).lower()

        self.assertNotIn("completed dossier", item_text)
        self.assertNotIn("completed-dossier", item_text)
        self.assertNotIn("completed dossier", markdown)
        self.assertNotIn("completed-dossier", markdown)

    def test_no_betting_trading_recommendation_score_probability_ev_side_or_market_decision_fields_exist(self):
        export = _load_export()

        for key in _walk_keys(export["final_dossier_drafts"]):
            self.assertTrue(
                PROHIBITED_FIELD_TOKENS.isdisjoint(_field_tokens(key)),
                msg=f"prohibited field emitted: {key}",
            )

    def test_no_betting_trading_recommendation_score_probability_ev_side_or_market_decision_language_in_drafts(self):
        export = _load_export()
        prohibited_phrases = {
            "bet recommendation",
            "trade recommendation",
            "recommendation",
            "probability estimate",
            "expected value",
            "market decision",
            "side recommendation",
            "paper order",
            "real order",
        }

        for text in _walk_strings(export["final_dossier_drafts"]):
            normalized = text.lower().replace("_", " ")
            for phrase in prohibited_phrases:
                self.assertNotIn(phrase, normalized)

    def test_evidence_and_review_content_are_copied_structurally_without_truth_inference(self):
        export = _load_export()
        pack = _load_json(REVIEW_PACK)["human_review_packs"][0]
        review_record = _load_json(REVIEW_RECORDS_RESULT)["accepted_human_review_records"][0]
        draft = export["final_dossier_drafts"][0]

        self.assertEqual(draft["evidence_summary_by_source"], pack["evidence_summary_by_source"])
        self.assertEqual(draft["final_draft_sections"]["evidence_inventory"], pack["evidence_summary_by_source"])
        self.assertEqual(draft["uncertainty_register"], pack["uncertainty_register"])
        self.assertEqual(draft["missing_information_review"], pack["missing_information_review"])
        self.assertEqual(draft["operator_review_notes"], pack["operator_review_notes"])
        self.assertEqual(draft["human_review_notes"], review_record["reviewer_notes"])
        self.assertEqual(draft["final_draft_sections"]["human_review_summary"]["human_review_notes"], review_record["reviewer_notes"])

    def test_markdown_export_has_stable_headings_and_summary_counts(self):
        export = _load_export()
        markdown = MARKDOWN_OUTPUT.read_text(encoding="utf-8")

        heading_lines = [line for line in markdown.splitlines() if line.startswith("#")]
        self.assertEqual(
            heading_lines,
            [
                "# PMBOT Final Dossier Drafts v1",
                "## Summary",
                "## Final Dossier Drafts",
                "### 563650",
                "#### Market Overview",
                "#### Resolution Rules",
                "#### Evidence Inventory",
                "#### Uncertainty Notes",
                "#### Source Coverage Notes",
                "#### Unresolved Questions",
                "#### Human Review Summary",
            ],
        )
        for field, expected in EXPECTED_SUMMARY.items():
            self.assertIn(f"- {field}: {expected}", markdown)
        self.assertIn("- 563650", markdown)
        self.assertIn("- final_draft_status: final_dossier_draft_only", markdown)
        self.assertEqual(export["export_summary"], EXPECTED_SUMMARY)

    def test_json_output_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            json_path = temp_path / "final.json"
            markdown_path = temp_path / "final.md"
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

    def test_exporter_uses_standard_library_only(self):
        tree = ast.parse(EXPORTER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "pathlib", "sys"})

    def test_exporter_has_no_live_fetcher_or_runtime_terms(self):
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
            "run_codex",
        ]
        for term in forbidden:
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()
