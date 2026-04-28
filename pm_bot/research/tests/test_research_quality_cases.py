import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CASES_PATH = ROOT / "pm_bot" / "research" / "research_quality_cases.v1.json"


class ResearchQualityCasesTests(unittest.TestCase):
    def test_case_contract_contains_expected_coverage(self):
        payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))
        cases = payload["cases"]
        self.assertEqual(len(cases), 12)
        decisions = {case["expected_decision"] for case in cases}
        self.assertEqual(decisions, {"accept", "reject", "watchlist", "exclude", "no_action"})

    def test_all_cases_are_fixture_only_and_paper_only(self):
        payload = json.loads(CASES_PATH.read_text(encoding="utf-8"))
        for case in payload["cases"]:
            self.assertTrue(case["fixture_only"])
            self.assertTrue(case["paper_only"])
            self.assertIn("expected_rejection_or_warning_reasons", case)


if __name__ == "__main__":
    unittest.main()
