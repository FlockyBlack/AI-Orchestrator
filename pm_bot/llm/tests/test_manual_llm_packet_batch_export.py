import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LLM_DIR = ROOT / "pm_bot" / "llm"
EXPORTER = LLM_DIR / "export_manual_llm_packet_batch.py"
QUEUE_JSON = LLM_DIR / "manual_llm_review_queue.v1.json"
MANIFEST_JSON = LLM_DIR / "manual_llm_packet_batch_manifest.v1.json"
MANIFEST_MD = LLM_DIR / "manual_llm_packet_batch_manifest.v1.md"
EXPECTED_MANIFEST_JSON = LLM_DIR / "expected_manual_llm_packet_batch_manifest.v1.json"
BATCH_DIR = LLM_DIR / "manual_packet_batch"
DOC_RESULT = ROOT / "docs" / "PMBOT_LLM_015_RESULT.json"
DOC_MD = ROOT / "docs" / "PMBOT_LLM_015_MANUAL_PACKET_BATCH_EXPORT.md"

EXPECTED_MARKET_IDS = [
    "563650",
    "569332",
    "569333",
    "569334",
    "569343",
    "569344",
    "569366",
    "569368",
    "569373",
    "573656",
    "597964",
    "598936",
    "691547",
    "692258",
]


def _load_module():
    spec = importlib.util.spec_from_file_location("manual_llm_packet_batch", EXPORTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _run_exporter():
    return subprocess.run(
        [sys.executable, str(EXPORTER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )


class ManualLlmPacketBatchExportTests(unittest.TestCase):
    def test_batch_exporter_creates_packet_prompt_and_manifest_for_ready_items(self):
        completed = _run_exporter()
        stdout_manifest = json.loads(completed.stdout)
        manifest = _load_json(MANIFEST_JSON)

        self.assertEqual(stdout_manifest, manifest)
        self.assertEqual(manifest["exported_count"], 14)
        self.assertEqual(manifest["skipped_count"], 0)
        self.assertEqual(manifest["exported_market_ids"], EXPECTED_MARKET_IDS)
        self.assertEqual(manifest, _load_json(EXPECTED_MANIFEST_JSON))
        self.assertTrue(MANIFEST_MD.exists())
        self.assertTrue(DOC_MD.exists())
        self.assertEqual(_load_json(DOC_RESULT)["exported_count"], 14)
        for market_id in EXPECTED_MARKET_IDS:
            self.assertTrue((BATCH_DIR / f"{market_id}_packet.v1.json").exists())
            self.assertTrue((BATCH_DIR / f"{market_id}_prompt.v1.md").exists())

    def test_existing_accepted_market_remains_accepted_and_not_batch_exported(self):
        _run_exporter()
        queue = _load_json(QUEUE_JSON)
        item = next(item for item in queue["items"] if item["market_id"] == "824952")

        self.assertEqual(item["review_queue_status"], "response_accepted_for_operator_review")
        self.assertEqual(item["packet_path"], "pm_bot/llm/real_local_market_llm_trial_packet.v1.json")
        self.assertFalse((BATCH_DIR / "824952_packet.v1.json").exists())
        self.assertNotIn("824952", _load_json(MANIFEST_JSON)["exported_market_ids"])

    def test_queue_statuses_update_deterministically_after_export(self):
        _run_exporter()
        queue = _load_json(QUEUE_JSON)

        self.assertEqual(queue["queue_items_total"], 15)
        self.assertEqual(queue["queue_status_counts"]["waiting_for_operator_pasted_response"], 14)
        self.assertEqual(queue["queue_status_counts"]["response_accepted_for_operator_review"], 1)
        self.assertEqual(queue["queue_status_counts"]["ready_for_manual_packet_export"], 0)
        for market_id in EXPECTED_MARKET_IDS:
            item = next(item for item in queue["items"] if item["market_id"] == market_id)
            self.assertEqual(item["review_queue_status"], "waiting_for_operator_pasted_response")
            self.assertEqual(item["packet_validation_status"], "accepted")
            self.assertTrue(item["packet_path"].startswith("pm_bot/llm/manual_packet_batch/"))
            self.assertTrue(item["prompt_path"].startswith("pm_bot/llm/manual_packet_batch/"))

    def test_missing_source_artifact_is_skipped_without_crash(self):
        module = _load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queue_path = root / "pm_bot" / "llm" / "manual_llm_review_queue.v1.json"
            queue_path.parent.mkdir(parents=True)
            queue_path.write_text(
                json.dumps(
                    {
                        "queue_items_total": 1,
                        "items": [
                            {
                                "market_id": "111",
                                "candidate_source_type": "unit_test_source",
                                "source_artifact_path": "pm_bot/research/missing_source.json",
                                "review_queue_status": "ready_for_manual_packet_export",
                            }
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            manifest = module.export_manual_llm_packet_batch(root=root)

        self.assertEqual(manifest["exported_count"], 0)
        self.assertEqual(manifest["skipped_count"], 1)
        self.assertEqual(manifest["skipped_items"][0]["reason"], "source_artifact_missing")

    def test_generated_paths_are_repo_relative(self):
        _run_exporter()
        manifest = _load_json(MANIFEST_JSON)

        for item in manifest["per_market_artifacts"]:
            for key in ("packet_path", "prompt_path", "expected_response_path"):
                self.assertFalse(Path(item[key]).is_absolute())
                self.assertTrue(item[key].startswith("pm_bot/llm/manual_packet_batch/"))

    def test_generated_prompts_contain_safety_restrictions(self):
        _run_exporter()
        prompt = (BATCH_DIR / "563650_prompt.v1.md").read_text(encoding="utf-8")

        for text in (
            "Return only strict JSON compatible with `llm_analysis_response_schema.v1.json`.",
            "No trading recommendations.",
            "No buy, sell, hold, enter, or exit instructions.",
            "No probability.",
            "No EV.",
            "No value metrics.",
            "No scoring.",
            "No confidence for betting.",
            "No side selection.",
            "No market decision.",
            "No truth inference.",
            "No order instructions.",
            "No wallet, private key, or credential handling.",
            "No external data.",
            "No internet, news, or API.",
            "Use only the supplied packet.",
            "Output analysis-only JSON.",
        ):
            self.assertIn(text, prompt)

    def test_generated_batch_artifacts_avoid_restricted_literal_and_unsafe_claims(self):
        _run_exporter()
        checked_paths = [
            *BATCH_DIR.glob("*_packet.v1.json"),
            *BATCH_DIR.glob("*_prompt.v1.md"),
            MANIFEST_JSON,
            MANIFEST_MD,
        ]
        self.assertGreaterEqual(len(checked_paths), 30)
        for path in checked_paths:
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotRegex(text, r"\bedge\b")
            self.assertNotIn("buy yes", text)
            self.assertNotIn("sell no", text)
            self.assertNotIn("recommended_side", text)
            self.assertNotIn("fair_value", text)

    def test_output_fixture_is_deterministic_and_rerun_is_idempotent(self):
        first = json.loads(_run_exporter().stdout)
        second = json.loads(_run_exporter().stdout)

        self.assertEqual(first, second)
        self.assertEqual(first, _load_json(EXPECTED_MANIFEST_JSON))
        self.assertEqual(first, _load_json(MANIFEST_JSON))

    def test_runner_uses_standard_library_and_no_network_llm_browser_or_runtime_imports(self):
        source = EXPORTER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])

        self.assertLessEqual(imported_roots, {"argparse", "json", "pathlib", "pm_bot", "re", "sys"})
        for token in (
            "requests",
            "urllib",
            "httpx",
            "aiohttp",
            "socket",
            "websocket",
            "webbrowser",
            "selenium",
            "playwright",
            "openai",
            "anthropic",
            "py_clob_client",
            "subprocess",
        ):
            self.assertNotIn(token, imported_roots)


if __name__ == "__main__":
    unittest.main()
