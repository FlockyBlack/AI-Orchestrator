import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PROMOTER = ROOT / "codex_auto" / "ready_promotion" / "promote_candidates_to_ready.py"
READY_MANIFEST = ROOT / "codex_auto" / "tasks" / "ready" / "PMBOT-BATCH-001.ready_manifest.json"
EXECUTION_PREVIEW = ROOT / "codex_auto" / "tasks" / "ready" / "PMBOT-BATCH-001.execution_preview.json"
CANDIDATE = ROOT / "codex_auto" / "tasks" / "candidates" / "PMBOT-005-PAPER-SIMULATION.task.json"
READY_TASKS = [
    ROOT / "codex_auto" / "tasks" / "ready" / "PMBOT-005-PAPER-SIMULATION.task.json",
    ROOT / "codex_auto" / "tasks" / "ready" / "PMBOT-006-RISK-LIMITS.task.json",
    ROOT / "codex_auto" / "tasks" / "ready" / "PMBOT-007-FEES-SLIPPAGE.task.json",
    ROOT / "codex_auto" / "tasks" / "ready" / "PMBOT-008-RESEARCH-DASHBOARD.task.json",
    ROOT / "codex_auto" / "tasks" / "ready" / "PMBOT-009-FIXTURE-POSTMORTEM.task.json",
    ROOT / "codex_auto" / "tasks" / "ready" / "PMBOT-010-STATIC-SAFETY-AUDIT.task.json",
]


def _run_promoter():
    return subprocess.run(
        [sys.executable, str(PROMOTER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class PromoteCandidatesToReadyTests(unittest.TestCase):
    def test_promotes_six_candidates_to_ready_task_files(self):
        result = _run_promoter()
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(len(payload["ready_tasks_created_or_validated"]), 6)
        for path in READY_TASKS:
            self.assertTrue(path.exists())

    def test_creates_ready_manifest(self):
        _run_promoter()
        self.assertTrue(READY_MANIFEST.exists())

    def test_creates_execution_preview(self):
        _run_promoter()
        self.assertTrue(EXECUTION_PREVIEW.exists())

    def test_ready_tasks_have_queue_state_ready(self):
        _run_promoter()
        for path in READY_TASKS:
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["queue_state"], "ready")

    def test_ready_tasks_have_safety_flags_disabled(self):
        _run_promoter()
        for path in READY_TASKS:
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(payload["approved_for_execution"])
            self.assertFalse(payload["execution_allowed_now"])
            self.assertFalse(payload["external_codex_cli_allowed"])
            self.assertFalse(payload["runtime_wiring_allowed"])
            self.assertTrue(payload["requires_human_approval"])
            self.assertTrue(payload["human_approval_required_before_execution"])
            self.assertTrue(payload["flocky_review_required_before_execution"])

    def test_source_candidate_files_remain_unchanged(self):
        before = CANDIDATE.read_text(encoding="utf-8")
        _run_promoter()
        after = CANDIDATE.read_text(encoding="utf-8")
        self.assertEqual(before, after)

    def test_generated_prompt_is_not_executed_and_external_codex_cli_not_invoked(self):
        source = PROMOTER.read_text(encoding="utf-8").lower()
        self.assertNotIn("subprocess", source)
        self.assertNotIn("codex exec", source)
        self.assertNotIn("os.system", source)

    def test_no_runtime_files_are_modified(self):
        source = PROMOTER.read_text(encoding="utf-8").lower()
        self.assertNotIn("scripts/dispatcher.py", source)
        self.assertNotIn("scripts/run_codex.py", source)

    def test_standard_library_only(self):
        source = PROMOTER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
