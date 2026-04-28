import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REVIEWER = ROOT / "codex_auto" / "promotion" / "review_candidate_bundle.py"
REQUEST = ROOT / "codex_auto" / "tasks" / "promotion_requests" / "PMBOT-BATCH-001.promotion_request.json"
DECISION = ROOT / "codex_auto" / "tasks" / "promotion_decisions" / "PMBOT-BATCH-001.promotion_decision.json"


def _run_reviewer(*args):
    return subprocess.run(
        [sys.executable, str(REVIEWER), *map(str, args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class ReviewCandidateBundleTests(unittest.TestCase):
    def test_review_candidate_bundle_approves_valid_bundle_for_ready_promotion_only(self):
        result = _run_reviewer(REQUEST)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["decision"], "approve_for_ready_promotion")
        self.assertTrue(payload["approved_for_ready_promotion"])

    def test_review_decision_has_approved_for_execution_false(self):
        payload = json.loads(_run_reviewer(REQUEST).stdout)
        self.assertFalse(payload["approved_for_execution"])

    def test_review_decision_has_external_codex_cli_allowed_now_false(self):
        payload = json.loads(_run_reviewer(REQUEST).stdout)
        self.assertFalse(payload["external_codex_cli_allowed_now"])

    def test_review_decision_has_human_approval_required_before_execution_true(self):
        payload = json.loads(_run_reviewer(REQUEST).stdout)
        self.assertTrue(payload["human_approval_required_before_execution"])

    def test_review_decision_does_not_claim_final_done(self):
        payload = json.loads(_run_reviewer(REQUEST).stdout)
        serialized = json.dumps(payload, ensure_ascii=False).lower()
        self.assertNotIn("final flocky done", serialized)
        self.assertNotIn("final openclaw done", serialized)

    def test_write_decision_writes_expected_artifact(self):
        result = _run_reviewer(REQUEST, "--write-decision")
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(DECISION.exists())
        on_disk = json.loads(DECISION.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["promotion_decision_id"], payload["promotion_decision_id"])

    def test_scripts_import_no_dispatcher_or_run_codex_or_runtime_modules(self):
        source = REVIEWER.read_text(encoding="utf-8").lower()
        self.assertNotIn("import dispatcher", source)
        self.assertNotIn("from dispatcher", source)
        self.assertNotIn("import run_codex", source)
        self.assertNotIn("from run_codex", source)
        self.assertNotIn("runtime loop", source)

    def test_scripts_do_not_use_network_api_wallet_private_key_or_trading(self):
        source = REVIEWER.read_text(encoding="utf-8").lower()
        self.assertNotIn("requests", source)
        self.assertNotIn("urllib.request", source)
        self.assertNotIn("socket", source)

    def test_standard_library_only(self):
        source = REVIEWER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
