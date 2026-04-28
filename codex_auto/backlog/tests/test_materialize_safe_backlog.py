import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MATERIALIZER = ROOT / "codex_auto" / "backlog" / "materialize_safe_backlog.py"
BACKLOG = ROOT / "docs" / "PM_BOT_SAFE_BACKLOG_V1.json"
CANDIDATES = [
    ROOT / "codex_auto" / "tasks" / "candidates" / "PMBOT-005-PAPER-SIMULATION.task.json",
    ROOT / "codex_auto" / "tasks" / "candidates" / "PMBOT-006-RISK-LIMITS.task.json",
    ROOT / "codex_auto" / "tasks" / "candidates" / "PMBOT-007-FEES-SLIPPAGE.task.json",
    ROOT / "codex_auto" / "tasks" / "candidates" / "PMBOT-008-RESEARCH-DASHBOARD.task.json",
    ROOT / "codex_auto" / "tasks" / "candidates" / "PMBOT-009-FIXTURE-POSTMORTEM.task.json",
    ROOT / "codex_auto" / "tasks" / "candidates" / "PMBOT-010-STATIC-SAFETY-AUDIT.task.json",
]
REPORT = ROOT / "codex_auto" / "tasks" / "candidates" / "PMBOT-BATCH-001.materialization.json"
PROMPT = ROOT / "codex_auto" / "prompts" / "PMBOT-BATCH-001.codex_prompt.txt"
PROMPT_MANIFEST = ROOT / "codex_auto" / "prompts" / "PMBOT-BATCH-001.prompt_manifest.json"


def _run_materializer():
    return subprocess.run(
        [sys.executable, str(MATERIALIZER), str(BACKLOG)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class MaterializeSafeBacklogTests(unittest.TestCase):
    def test_materializer_reads_backlog(self):
        result = _run_materializer()
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["status"], "done")
        self.assertEqual(payload["source_backlog_path"], "docs/PM_BOT_SAFE_BACKLOG_V1.json")

    def test_materializer_creates_or_validates_expected_candidates(self):
        _run_materializer()
        for candidate in CANDIDATES:
            self.assertTrue(candidate.exists())

    def test_materializer_creates_report_and_prompt_pack(self):
        _run_materializer()
        self.assertTrue(REPORT.exists())
        self.assertTrue(PROMPT.exists())
        self.assertTrue(PROMPT_MANIFEST.exists())

    def test_generated_candidates_are_candidate_state_only(self):
        _run_materializer()
        for candidate in CANDIDATES:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
            self.assertEqual(payload["queue_state"], "candidate")
            self.assertFalse(payload["approved_for_execution"])
            self.assertTrue(payload["dry_run_default"])
            self.assertTrue(payload["flocky_validation_required"])
            self.assertFalse(payload["runtime_wiring_allowed"])
            self.assertFalse(payload["external_codex_cli_allowed"])

    def test_generated_prompt_not_executed(self):
        _run_materializer()
        payload = json.loads(PROMPT_MANIFEST.read_text(encoding="utf-8"))
        self.assertFalse(payload["execution_allowed_now"])
        self.assertTrue(payload["requires_flocky_review_before_execution"])
        self.assertTrue(payload["requires_human_approval_before_execution"])

    def test_materializer_standard_library_only(self):
        source = MATERIALIZER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"json", "sys", "datetime", "pathlib"})

    def test_materializer_has_no_dispatcher_run_codex_runtime_network_or_trading_usage(self):
        source = MATERIALIZER.read_text(encoding="utf-8").lower()
        self.assertNotIn("import dispatcher", source)
        self.assertNotIn("from dispatcher", source)
        self.assertNotIn("import run_codex", source)
        self.assertNotIn("from run_codex", source)
        self.assertNotIn("runtime loop", source)
        self.assertNotIn("requests", source)
        self.assertNotIn("urllib.request", source)
        self.assertNotIn("socket", source)


if __name__ == "__main__":
    unittest.main()
