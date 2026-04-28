import ast
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
BUILDER = ROOT / "pm_bot" / "raw_artifacts" / "build_ingestion_manifest.py"
FIXTURES_DIR = ROOT / "pm_bot" / "raw_artifacts" / "fixtures"
EXPECTED_MANIFEST = ROOT / "pm_bot" / "raw_artifacts" / "expected_ingestion_manifest.v1.json"


def _run_builder(*extra_args, cwd=ROOT, check=True):
    return subprocess.run(
        [sys.executable, str(BUILDER), *extra_args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def _load_expected():
    return json.loads(EXPECTED_MANIFEST.read_text(encoding="utf-8"))


def test_default_cli_builds_manifest_successfully():
    result = _run_builder()
    payload = json.loads(result.stdout)
    assert result.returncode == 0
    assert payload["validation_passed"] is True
    assert payload["fixtures_dir"] == "pm_bot/raw_artifacts/fixtures"
    assert payload["counts"]["accepted"] == 3
    assert payload["counts"]["quarantined"] == 9


def test_expected_manifest_matches_actual_output():
    result = _run_builder()
    payload = json.loads(result.stdout)
    assert payload == _load_expected()


def test_custom_fixtures_dir_works_with_tmp_copy(tmp_path):
    temp_fixtures = tmp_path / "copied-fixtures"
    shutil.copytree(FIXTURES_DIR, temp_fixtures)

    result = _run_builder("--fixtures-dir", str(temp_fixtures))
    payload = json.loads(result.stdout)

    assert result.returncode == 0
    assert payload["counts"]["checked_files"] == 12
    assert payload["counts"]["accepted"] == 3
    assert payload["counts"]["quarantined"] == 9
    assert payload["fixtures_dir"] == str(temp_fixtures).replace("\\", "/")


def test_write_manifest_writes_only_requested_path(tmp_path):
    output_path = tmp_path / "manifest.json"
    result = _run_builder("--write-manifest", str(output_path))

    assert result.returncode == 0
    assert result.stdout == ""
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == _load_expected()
    assert sorted(path.name for path in tmp_path.iterdir()) == ["manifest.json"]


def test_handoff_readiness_flags_match_acceptance_state():
    payload = json.loads(_run_builder().stdout)

    assert all(item["handoff_ready_for_normalization"] is True for item in payload["accepted_artifacts"])
    assert all(item["handoff_ready_for_normalization"] is False for item in payload["quarantined_artifacts"])


def test_manifest_ordering_is_deterministic():
    first = json.loads(_run_builder().stdout)
    second = json.loads(_run_builder().stdout)

    assert first == second
    assert [item["file"] for item in first["accepted_artifacts"]] == sorted(
        item["file"] for item in first["accepted_artifacts"]
    )
    assert [item["file"] for item in first["quarantined_artifacts"]] == sorted(
        item["file"] for item in first["quarantined_artifacts"]
    )


def test_expected_manifest_is_root_independent():
    expected_text = EXPECTED_MANIFEST.read_text(encoding="utf-8")

    assert "pm_bot/raw_artifacts/fixtures" in expected_text
    assert str(ROOT).replace("\\", "/") not in expected_text
    assert "C:/Users/OpenC/Documents/AI-Orchestrator" not in expected_text


def test_builder_has_no_forbidden_live_network_wallet_runtime_imports():
    source = BUILDER.read_text(encoding="utf-8")
    lowered = source.lower()

    forbidden_fragments = [
        "import requests",
        "import httpx",
        "import aiohttp",
        "urllib.request",
        "import socket",
        "import websocket",
        "py_clob_client",
        "subprocess",
        "run_codex",
        "dispatcher",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in lowered

    tree = ast.parse(source)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])

    assert imports <= {"argparse", "json", "sys", "pathlib", "pm_bot"}
