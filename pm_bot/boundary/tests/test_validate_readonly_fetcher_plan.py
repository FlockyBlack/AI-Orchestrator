import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNNER = ROOT / "pm_bot" / "boundary" / "validate_readonly_fetcher_plan.py"


def _run():
    return subprocess.run([sys.executable, str(RUNNER)], cwd=ROOT, capture_output=True, text=True, check=True)


def _load_module():
    spec = importlib.util.spec_from_file_location("pmbot_readonly_plan_validator", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ValidateReadonlyFetcherPlanTests(unittest.TestCase):
    def test_script_succeeds(self):
        payload = json.loads(_run().stdout)
        self.assertTrue(payload["validation_passed"])

    def test_plan_requires_approval(self):
        payload = json.loads(_run().stdout)
        self.assertTrue(payload["checks"]["future_implementation_requires_approval"])

    def test_live_fetcher_package_is_blocking(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            docs = root / "docs"
            docs.mkdir(parents=True, exist_ok=True)
            for path in module.REQUIRED_DOCS.values():
                target = root / path.relative_to(module.ROOT)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
            package_dir = root / "pm_bot" / "live_readonly"
            package_dir.mkdir(parents=True, exist_ok=True)
            report = module.build_report(root)
        self.assertFalse(report["checks"]["no_live_fetcher_module_exists"])
        self.assertIn("pm_bot/live_readonly", report["forbidden_live_fetcher_modules"])

    def test_paper_replay_contract_remains_no_execution(self):
        payload = json.loads(_run().stdout)
        self.assertTrue(payload["checks"]["paper_replay_remains_no_execution"])

    def test_standard_library_only(self):
        tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"ast", "json", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
