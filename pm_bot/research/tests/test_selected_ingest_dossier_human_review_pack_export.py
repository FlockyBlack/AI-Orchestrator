import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EXPORTER = ROOT / "pm_bot" / "research" / "export_selected_ingest_dossier_human_review_pack.py"
VALIDATION_RESULT = ROOT / "pm_bot" / "research" / "selected_ingest_manual_dossier_draft_validation_result.v1.json"
SKELETONS = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_draft_skeletons.v1.json"
JSON_OUTPUT = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_human_review_pack.v1.json"
MARKDOWN_OUTPUT = ROOT / "pm_bot" / "research" / "selected_ingest_dossier_human_review_pack.v1.md"
EXPECTED_JSON_OUTPUT = ROOT / "pm_bot" / "research" / "expected_selected_ingest_dossier_human_review_pack.v1.json"

EXPECTED_SELECTED_MARKET_IDS = ["692258", "824952", "691547", "597964", "598936"]
EXPECTED_SUMMARY = {
    "accepted_drafts_seen": 1,
    "human_review_packs_exported": 1,
    "draft_records_skipped": 6,
    "completed_dossiers_created": 0,
}
EXPECTED_CHECKLIST = [
    "evidence_matches_resolution_criteria",
    "uncertainty_register_reviewed",
    "missing_information_reviewed",
    "no_trading_recommendation_present",
    "no_probability_or_ev_present",
    "no_side_recommendation_present",
    "no_market_decision_present",
]
EXPECTED_ALLOWED_REVIEW_OUTCOMES = [
    "approved_for_final_dossier_draft",
    "needs_draft_revision",
    "rejected_for_research_quality",
    "watch_only",
]
EXPECTED_PROHIBITED_REVIEW_OUTPUTS = [
    "bet recommendation",
    "trade recommendation",
    "YES/NO side selection",
    "probability estimate",
    "expected value calculation",
    "score/signal",
    "market decision",
    "order/paper order",
]
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
    "market_decision",
    "market_decisions",
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
    spec = importlib.util.spec_from_file_location("selected_ingest_dossier_human_review_pack_exporter", EXPORTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_export():
    _run_exporter()
    return _load_json(JSON_OUTPUT)


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


def _skeleton_by_market_id(market_id):
    for skeleton in _load_json(SKELETONS)["dossier_draft_skeletons"]:
        if skeleton["market_id"] == market_id:
            return skeleton
    raise AssertionError(f"missing skeleton {market_id}")


class SelectedIngestDossierHumanReviewPackExportTests(unittest.TestCase):
    def test_default_export_matches_expected_json(self):
        _run_exporter()

        self.assertEqual(_load_json(JSON_OUTPUT), _load_json(EXPECTED_JSON_OUTPUT))

    def test_only_ready_human_review_selected_ingest_records_are_exported(self):
        export = _load_export()
        packs = export["human_review_packs"]

        self.assertEqual(export["selected_market_ids"], EXPECTED_SELECTED_MARKET_IDS)
        self.assertEqual(export["export_summary"], EXPECTED_SUMMARY)
        self.assertEqual(export["exported_market_ids"], ["824952"])
        self.assertEqual(len(packs), 1)
        self.assertEqual(packs[0]["market_id"], "824952")
        self.assertEqual(packs[0]["review_pack_status"], "human_review_pack_only")

    def test_rejected_incomplete_and_non_ready_drafts_are_skipped(self):
        module = _load_module()
        validation = _load_json(VALIDATION_RESULT)
        ready_record = validation["accepted_draft_records"][0]
        non_ready_record = dict(ready_record)
        non_ready_record["record_index"] = 8
        non_ready_record["draft_status"] = "needs_more_information"
        non_ready_record["next_manual_action"] = "add_missing_information"
        custom_validation = dict(validation)
        custom_validation["accepted_draft_records"] = [ready_record, non_ready_record]
        custom_validation["rejected_draft_records"] = [validation["rejected_draft_records"][0]]
        custom_validation["draft_validation_summary"] = {
            "draft_records_read": 3,
            "draft_records_accepted": 2,
            "draft_records_rejected": 1,
            "draft_ready_for_human_review": 1,
            "needs_more_information": 1,
            "draft_incomplete": 0,
            "draft_rejected": 0,
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            validation_path = temp_path / "validation.json"
            validation_path.write_text(json.dumps(custom_validation, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            export = module.build_selected_ingest_dossier_human_review_pack_export(
                validation_result_path=validation_path,
                json_output_path=temp_path / "pack.json",
                markdown_output_path=temp_path / "pack.md",
                expected_json_output_path=temp_path / "expected.json",
            )

        self.assertEqual(export["exported_market_ids"], ["824952"])
        self.assertEqual(export["export_summary"]["accepted_drafts_seen"], 2)
        self.assertEqual(export["export_summary"]["human_review_packs_exported"], 1)
        self.assertEqual(export["export_summary"]["draft_records_skipped"], 2)

    def test_human_review_checklist_is_structural_only(self):
        export = _load_export()

        self.assertEqual(export["human_review_checklist"], EXPECTED_CHECKLIST)
        for pack in export["human_review_packs"]:
            self.assertEqual(pack["human_review_checklist"], EXPECTED_CHECKLIST)

    def test_allowed_review_outcomes_contain_no_betting_or_trading_decision(self):
        export = _load_export()
        forbidden_tokens = {
            "bet",
            "betting",
            "trade",
            "trading",
            "order",
            "side",
            "yes_no",
            "probability",
            "expected_value",
            "ev",
            "score",
            "signal",
            "buy",
            "sell",
            "market_decision",
        }

        self.assertEqual(export["allowed_review_outcomes"], EXPECTED_ALLOWED_REVIEW_OUTCOMES)
        for outcome in export["allowed_review_outcomes"]:
            self.assertTrue(forbidden_tokens.isdisjoint(_field_tokens(outcome)), msg=f"decision-like outcome emitted: {outcome}")

    def test_prohibited_review_outputs_explicitly_forbid_required_outputs(self):
        export = _load_export()

        self.assertEqual(export["prohibited_review_outputs"], EXPECTED_PROHIBITED_REVIEW_OUTPUTS)
        for required_phrase in (
            "bet recommendation",
            "trade recommendation",
            "side selection",
            "probability estimate",
            "expected value calculation",
            "score/signal",
            "market decision",
            "order/paper order",
        ):
            self.assertIn(required_phrase, " | ".join(export["prohibited_review_outputs"]))
        for pack in export["human_review_packs"]:
            self.assertEqual(pack["prohibited_review_outputs"], EXPECTED_PROHIBITED_REVIEW_OUTPUTS)

    def test_no_completed_dossier_language_is_emitted_outside_required_summary_count(self):
        export = _load_export()
        markdown = MARKDOWN_OUTPUT.read_text(encoding="utf-8").lower()
        rendered_packs = json.dumps(export["human_review_packs"], sort_keys=True).lower()

        self.assertEqual(export["export_summary"]["completed_dossiers_created"], 0)
        self.assertNotIn("completed dossier", rendered_packs + markdown)
        self.assertNotIn("completed-dossier", rendered_packs + markdown)

    def test_no_betting_trading_recommendation_score_probability_or_ev_fields_exist(self):
        export = _load_export()

        for key in _walk_keys(export):
            self.assertTrue(
                PROHIBITED_FIELD_TOKENS.isdisjoint(_field_tokens(key)),
                msg=f"prohibited field emitted: {key}",
            )

    def test_source_ingest_artifact_references_are_exported(self):
        export = _load_export()
        pack = export["human_review_packs"][0]
        skeleton = _skeleton_by_market_id("824952")

        self.assertEqual(
            pack["source_ingest_artifacts"],
            {key: skeleton["source_ingest_artifacts"][key] for key in sorted(skeleton["source_ingest_artifacts"])},
        )

    def test_prohibited_accepted_draft_fields_fail_export(self):
        module = _load_module()
        validation = _load_json(VALIDATION_RESULT)
        unsafe_record = dict(validation["accepted_draft_records"][0])
        unsafe_record["probability"] = "not allowed"
        validation["accepted_draft_records"] = [unsafe_record]
        validation["rejected_draft_records"] = []
        validation["draft_validation_summary"] = {
            "draft_records_read": 1,
            "draft_records_accepted": 1,
            "draft_records_rejected": 0,
            "draft_ready_for_human_review": 1,
            "needs_more_information": 0,
            "draft_incomplete": 0,
            "draft_rejected": 0,
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            validation_path = temp_path / "validation.json"
            validation_path.write_text(json.dumps(validation, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
            with self.assertRaises(ValueError) as raised:
                module.build_selected_ingest_dossier_human_review_pack_export(
                    validation_result_path=validation_path,
                    json_output_path=temp_path / "pack.json",
                    markdown_output_path=temp_path / "pack.md",
                    expected_json_output_path=temp_path / "expected.json",
                )

        self.assertIn("accepted draft records contain prohibited fields", str(raised.exception))
        self.assertIn("probability", str(raised.exception))

    def test_markdown_report_has_stable_headings_and_summary_counts(self):
        export = _load_export()
        markdown = MARKDOWN_OUTPUT.read_text(encoding="utf-8")

        heading_lines = [line for line in markdown.splitlines() if line.startswith("#")]
        self.assertEqual(
            heading_lines,
            [
                "# Selected Ingest Dossier Human Review Pack v1",
                "## Summary",
                "## Selected Market IDs",
                "## Human Review Packs",
                "### 824952",
                "#### Review Notes",
                "#### Evidence Summary By Source",
                "#### Uncertainty Register",
                "#### Open Questions",
                "#### Human Review Checklist",
                "#### Allowed Review Outcomes",
                "#### Prohibited Review Outputs",
                "#### Source Ingest Artifacts",
            ],
        )
        for field, expected in EXPECTED_SUMMARY.items():
            self.assertIn(f"- {field}: {expected}", markdown)
        self.assertIn("- 824952", markdown)
        self.assertIn("- review_pack_status: human_review_pack_only", markdown)
        self.assertEqual(export["export_summary"], EXPECTED_SUMMARY)

    def test_json_output_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            json_path = temp_path / "pack.json"
            markdown_path = temp_path / "pack.md"
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
            ROOT / "pm_bot" / "paper",
            ROOT / "pm_bot" / "scoring",
            ROOT / "pm_bot" / "signals",
        ]
        targets = (
            "export_selected_ingest_dossier_human_review_pack",
            "selected_ingest_dossier_human_review_pack",
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
            "run_codex(",
        ]
        for term in forbidden:
            self.assertNotIn(term, source)


if __name__ == "__main__":
    unittest.main()
