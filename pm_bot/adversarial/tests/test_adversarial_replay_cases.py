import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "pm_bot" / "adversarial" / "adversarial_replay_cases.v1.json"


class AdversarialReplayCaseFixtureTests(unittest.TestCase):
    def test_cases_cover_required_adversarial_shapes(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cases = payload["cases"]
        self.assertGreaterEqual(len(cases), 12)
        case_ids = {case["case_id"] for case in cases}
        self.assertIn("replay_adversarial_false_positive", case_ids)
        self.assertIn("replay_watchlist_escalation_block", case_ids)

    def test_all_cases_are_fixture_and_paper_only(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        for case in payload["cases"]:
            self.assertTrue(case["fixture_only"])
            self.assertTrue(case["paper_only"])
            self.assertIn("synthetic_market_inputs", case)
            self.assertIn("replay_timeline_steps", case)
            self.assertIn("expected_rejection_or_warning_reasons", case)


if __name__ == "__main__":
    unittest.main()
