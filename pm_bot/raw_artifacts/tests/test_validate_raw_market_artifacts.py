import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "pm_bot" / "raw_artifacts" / "validate_raw_market_artifacts.py"
FIXTURES_DIR = ROOT / "pm_bot" / "raw_artifacts" / "fixtures"
VALID_DIR = FIXTURES_DIR / "valid"
INVALID_DIR = FIXTURES_DIR / "invalid"
EXPECTED_REPORT = ROOT / "pm_bot" / "raw_artifacts" / "expected_raw_artifact_validation_report.v1.json"


def _parts(*values):
    return "".join(values)


def _run_validator(*extra_args, cwd=ROOT, check=True):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *extra_args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def _load_expected():
    return json.loads(EXPECTED_REPORT.read_text(encoding="utf-8"))


class ValidateRawMarketArtifactsTests(unittest.TestCase):
    def test_default_cli_matches_expected_report(self):
        result = _run_validator()
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload, _load_expected())
        self.assertEqual(payload["fixtures_dir"], "pm_bot/raw_artifacts/fixtures")

    def test_all_valid_fixtures_pass(self):
        from pm_bot.raw_artifacts.validate_raw_market_artifacts import validate_artifact

        for path in sorted(VALID_DIR.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            findings = validate_artifact(payload, str(path.relative_to(FIXTURES_DIR)).replace("\\", "/"))
            self.assertEqual(findings, [], msg=str(path))

    def test_invalid_fixtures_fail_for_intended_reasons(self):
        from pm_bot.raw_artifacts.validate_raw_market_artifacts import build_validation_report

        report = build_validation_report(FIXTURES_DIR)
        findings_by_file = {}
        for item in report["quarantine_findings"]:
            findings_by_file.setdefault(item["file"], []).append(item["code"])

        expected_codes = {
            "invalid/invalid_missing_required_field.json": {"missing_required_field:provenance", "provenance_not_object"},
            "invalid/invalid_bad_contract_version.json": {"bad_contract_version"},
            "invalid/invalid_stale_captured_at.json": {"stale_captured_at"},
            "invalid/invalid_malformed_outcomes.json": {"outcomes_not_list"},
            "invalid/invalid_side_value.json": {"invalid_outcome_side:0"},
            "invalid/invalid_price_out_of_range.json": {"price_out_of_range"},
            "invalid/invalid_conflicting_safety_network.json": {"unsafe_safety_flag:network_used"},
            "invalid/invalid_wallet_order_trading_flags.json": {
                "unsafe_safety_flag:wallet_used",
                "unsafe_safety_flag:order_capable",
                "unsafe_safety_flag:trading_capable",
            },
            "invalid/invalid_empty_ids_and_duplicates.json": {
                "empty_artifact_id",
                "invalid_market_field:market_id",
                "duplicate_outcome_name",
                "duplicate_outcome_side",
            },
        }

        self.assertEqual(set(findings_by_file), set(expected_codes))
        for file_name, codes in expected_codes.items():
            self.assertTrue(codes.issubset(set(findings_by_file[file_name])), msg=file_name)

    def test_report_order_is_deterministic(self):
        first = json.loads(_run_validator().stdout)
        second = json.loads(_run_validator().stdout)
        self.assertEqual(first, second)
        self.assertEqual(
            [item["file"] for item in first["quarantine_findings"]],
            sorted(item["file"] for item in first["quarantine_findings"]),
        )

    def test_safety_flags_are_rejected(self):
        from pm_bot.raw_artifacts.validate_raw_market_artifacts import validate_artifact

        payload = json.loads((INVALID_DIR / "invalid_wallet_order_trading_flags.json").read_text(encoding="utf-8"))
        findings = validate_artifact(payload, "invalid/invalid_wallet_order_trading_flags.json")
        codes = {item["code"] for item in findings}
        self.assertIn("unsafe_safety_flag:wallet_used", codes)
        self.assertIn("unsafe_safety_flag:order_capable", codes)
        self.assertIn("unsafe_safety_flag:trading_capable", codes)

    def test_stale_artifact_uses_deterministic_reference_time(self):
        from pm_bot.raw_artifacts.validate_raw_market_artifacts import REFERENCE_TIME_TEXT, validate_artifact

        payload = json.loads((INVALID_DIR / "invalid_stale_captured_at.json").read_text(encoding="utf-8"))
        findings = validate_artifact(payload, "invalid/invalid_stale_captured_at.json")
        stale = [item for item in findings if item["code"] == "stale_captured_at"]
        self.assertEqual(len(stale), 1)
        self.assertIn(REFERENCE_TIME_TEXT, stale[0]["message"])

    def test_validator_has_no_forbidden_imports(self):
        source = VALIDATOR.read_text(encoding="utf-8")
        fragments = [
            _parts("import ", "re", "quests"),
            _parts("import ", "http", "x"),
            _parts("import ", "aio", "http"),
            _parts("urllib", ".", "request"),
            _parts("import ", "so", "cket"),
            "py_clob_client",
        ]
        lowered = source.lower()
        for fragment in fragments:
            self.assertNotIn(fragment.lower(), lowered)

        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "re", "sys", "datetime", "pathlib"})

    def test_custom_fixtures_dir_works(self):
        from pm_bot.raw_artifacts.validate_raw_market_artifacts import build_validation_report

        report = build_validation_report(FIXTURES_DIR)
        self.assertEqual(report["checked_files_count"], len(list(FIXTURES_DIR.rglob("*.json"))))
        self.assertEqual(report["valid_files_count"], len(list(VALID_DIR.glob("*.json"))))
        self.assertEqual(report["invalid_files_count"], len(list(INVALID_DIR.glob("*.json"))))

    def test_write_report_uses_requested_path(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "artifact_report.json"
            result = _run_validator("--write-report", str(output_path))
            self.assertEqual(result.stdout, "")
            self.assertTrue(output_path.exists())
            payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(payload, _load_expected())

    def test_expected_report_does_not_embed_original_root_path(self):
        expected_text = EXPECTED_REPORT.read_text(encoding="utf-8")
        self.assertNotIn(str(ROOT).replace("\\", "/"), expected_text)

    def test_cli_supports_custom_fixtures_dir_with_tmp_copy(self):
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            temp_fixtures = temp_root / "fixtures"
            (temp_fixtures / "valid").mkdir(parents=True)
            (temp_fixtures / "invalid").mkdir(parents=True)
            for source in VALID_DIR.glob("*.json"):
                (temp_fixtures / "valid" / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            for source in INVALID_DIR.glob("*.json"):
                (temp_fixtures / "invalid" / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

            result = _run_validator("--fixtures-dir", str(temp_fixtures))
            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(payload["valid_files_count"], len(list(VALID_DIR.glob("*.json"))))
            self.assertEqual(payload["invalid_files_count"], len(list(INVALID_DIR.glob("*.json"))))
            self.assertEqual(payload["fixtures_dir"], str(temp_fixtures).replace("\\", "/"))

    def test_build_validation_report_normalizes_project_relative_default_fixtures_dir(self):
        from pm_bot.raw_artifacts.validate_raw_market_artifacts import build_validation_report

        report = build_validation_report(FIXTURES_DIR)
        self.assertEqual(report["fixtures_dir"], "pm_bot/raw_artifacts/fixtures")

    def test_expected_report_is_not_only_assertion(self):
        payload = json.loads(_run_validator().stdout)
        self.assertEqual(payload["unexpected_failures"], [])
        self.assertEqual(payload["unexpected_passes"], [])
        self.assertFalse(payload["safety_summary"]["network_used_detected"])
        self.assertFalse(payload["safety_summary"]["wallet_detected"])


if __name__ == "__main__":
    unittest.main()
