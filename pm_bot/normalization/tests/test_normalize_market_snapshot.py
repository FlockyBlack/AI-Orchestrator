import ast
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NORMALIZER = ROOT / "pm_bot" / "normalization" / "normalize_market_snapshot.py"
FIXTURE = ROOT / "pm_bot" / "fixtures" / "market_snapshot_stub.v1.json"
EXPECTED = ROOT / "pm_bot" / "normalization" / "expected_normalized_market.v1.json"


def _run_normalizer():
    return subprocess.run(
        [sys.executable, str(NORMALIZER), str(FIXTURE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


class NormalizeMarketSnapshotTests(unittest.TestCase):
    def test_deterministic_output_matches_expected(self):
        result = _run_normalizer()
        payload = json.loads(result.stdout)
        expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
        self.assertEqual(payload, expected)

    def test_no_runtime_imports(self):
        source = NORMALIZER.read_text(encoding="utf-8")
        self.assertNotIn("dispatcher", source)
        self.assertNotIn("run_codex", source)
        self.assertNotIn("runtime_loop", source)

    def test_no_network_api_wallet_or_trading(self):
        source = NORMALIZER.read_text(encoding="utf-8")
        self.assertNotIn("requests", source)
        self.assertNotIn("urllib.request", source)
        self.assertNotIn("wallet", source.lower())
        self.assertNotIn("private_key", source.lower())
        self.assertNotIn("order", source.lower())

    def test_no_active_task_reads(self):
        source = NORMALIZER.read_text(encoding="utf-8")
        self.assertNotIn("active_tasks", source)

    def test_source_fixture_not_mutated(self):
        before = FIXTURE.read_bytes()
        _run_normalizer()
        after = FIXTURE.read_bytes()
        self.assertEqual(before, after)

    def test_standard_library_only(self):
        tree = ast.parse(NORMALIZER.read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module.split(".")[0])
        self.assertLessEqual(imports, {"argparse", "json", "pathlib"})


if __name__ == "__main__":
    unittest.main()
