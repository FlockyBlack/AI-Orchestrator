import json
import subprocess
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / 'governance' / 'validation' / 'validate_governance_artifacts.py'
FIXTURES = ROOT / 'governance' / 'fixtures'


class GovernanceValidatorTests(unittest.TestCase):
    def run_validator(self, fixture_name):
        proc = subprocess.run(
            [sys.executable, str(VALIDATOR), str(FIXTURES / fixture_name)],
            capture_output=True,
            text=True,
            check=False,
        )
        return proc.returncode, json.loads(proc.stdout)

    def test_valid_fixture_passes(self):
        code, out = self.run_validator('valid_pm_v1_stable_warning_bundle.v1.json')
        self.assertEqual(code, 0)
        self.assertEqual(out['status'], 'valid')
        self.assertTrue(out['warnings_preserved'])
        self.assertTrue(out['final_done_allowed'])

    def test_invalid_final_done_without_critic_fails(self):
        code, out = self.run_validator('invalid_final_done_without_critic.v1.json')
        self.assertNotEqual(code, 0)
        self.assertEqual(out['status'], 'invalid')
        self.assertIn('final_done_requires_valid_critic_gate', out['errors'])

    def test_invalid_mismatched_source_run_id_fails(self):
        code, out = self.run_validator('invalid_mismatched_source_run_id.v1.json')
        self.assertNotEqual(code, 0)
        self.assertEqual(out['status'], 'invalid')
        self.assertTrue(any(e.startswith('source_run_id_mismatch:') for e in out['errors']))

    def test_invalid_warning_erased_fails(self):
        code, out = self.run_validator('invalid_warning_erased.v1.json')
        self.assertNotEqual(code, 0)
        self.assertEqual(out['status'], 'invalid')
        self.assertIn('accepted_warnings_not_preserved', out['errors'])

    def test_validator_has_no_forbidden_imports(self):
        text = VALIDATOR.read_text(encoding='utf-8').lower()
        self.assertNotIn('import dispatcher', text)
        self.assertNotIn('import run_codex', text)
        self.assertNotIn('runtime loop', text)

    def test_validator_works_offline_with_local_fixtures(self):
        text = VALIDATOR.read_text(encoding='utf-8').lower()
        self.assertNotIn('requests', text)
        self.assertNotIn('urllib.request', text)
        self.assertNotIn('socket', text)


if __name__ == '__main__':
    unittest.main()
