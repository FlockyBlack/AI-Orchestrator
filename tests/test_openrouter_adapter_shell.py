import ast
import json
from pathlib import Path
import subprocess
import sys

from pm_bot.llm import run_openrouter_adapter as adapter


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "pm_bot" / "llm" / "run_openrouter_adapter.py"
CONTRACT = ROOT / "pm_bot" / "llm" / "openrouter_adapter_contract.v1.json"
GITIGNORE = ROOT / ".gitignore"


def _run(tmp_path, *args):
    return adapter.run_adapter([*args, "--out-dir", str(tmp_path)], root=ROOT)


def test_dry_run_by_market_id_563650_selects_prompt_and_packet(tmp_path):
    code, summary = _run(tmp_path, "--market-id", "563650", "--dry-run")

    assert code == 0
    assert summary["status"] == "dry_run_ready"
    assert summary["market_id"] == "563650"
    assert summary["selected_prompt_path"] == "pm_bot/llm/manual_packet_batch/563650_prompt.v1.md"
    assert summary["selected_packet_path"] == "pm_bot/llm/manual_packet_batch/563650_packet.v1.json"


def test_dry_run_by_prompt_path_works_and_infers_packet(tmp_path):
    code, summary = _run(
        tmp_path,
        "--prompt-path",
        "pm_bot/llm/manual_packet_batch/563650_prompt.v1.md",
        "--dry-run",
    )

    assert code == 0
    assert summary["status"] == "dry_run_ready"
    assert summary["market_id"] == "563650"
    assert summary["selected_prompt_path"] == "pm_bot/llm/manual_packet_batch/563650_prompt.v1.md"
    assert summary["selected_packet_path"] == "pm_bot/llm/manual_packet_batch/563650_packet.v1.json"


def test_default_selection_ignores_legacy_real_local_prompt(tmp_path):
    legacy = ROOT / "pm_bot" / "llm" / "real_local_market_llm_trial_prompt.v1.md"
    assert legacy.exists()

    code, summary = _run(tmp_path, "--dry-run")

    assert code == 0
    assert summary["status"] == "dry_run_ready"
    assert summary["selected_prompt_path"] != "pm_bot/llm/real_local_market_llm_trial_prompt.v1.md"
    assert summary["selected_prompt_path"].startswith("pm_bot/llm/manual_packet_batch/")
    assert summary["selected_prompt_path"].endswith("_prompt.v1.md")


def test_missing_prompt_returns_blocked_missing_prompt(tmp_path):
    code, summary = _run(tmp_path, "--market-id", "999999999", "--dry-run")

    assert code == 1
    assert summary["status"] == "blocked_missing_prompt"
    assert summary["selected_prompt_path"] == "pm_bot/llm/manual_packet_batch/999999999_prompt.v1.md"
    assert "missing_prompt" in summary["warnings"]


def test_dry_run_does_not_require_openrouter_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    code, summary = _run(tmp_path, "--market-id", "563650", "--dry-run")

    assert code == 0
    assert summary["status"] == "dry_run_ready"
    assert summary["api_key_read"] is False


def test_script_does_not_read_openrouter_api_key():
    source = SCRIPT.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    assert "OPENROUTER_API_KEY" not in source
    assert "getenv" not in source
    assert "environ" not in source
    assert "os" not in imported_roots


def test_network_manual_confirm_flag_is_rejected_in_009(tmp_path):
    code, summary = _run(
        tmp_path,
        "--market-id",
        "563650",
        "--dry-run",
        "--manual-confirm-network",
    )

    assert code == 1
    assert summary["status"] == "blocked_network_not_implemented"
    assert summary["network_calls_made"] is False


def test_summary_records_network_calls_made_false(tmp_path):
    _code, summary = _run(tmp_path, "--market-id", "563650", "--dry-run")

    assert summary["network_calls_made"] is False


def test_summary_records_api_key_read_false(tmp_path):
    _code, summary = _run(tmp_path, "--market-id", "563650", "--dry-run")

    assert summary["api_key_read"] is False


def test_summary_records_no_runtime_wiring_true(tmp_path):
    _code, summary = _run(tmp_path, "--market-id", "563650", "--dry-run")

    assert summary["runtime_wiring"] is False
    assert summary["no_runtime_wiring"] is True


def test_summary_records_no_trading_decision_true(tmp_path):
    _code, summary = _run(tmp_path, "--market-id", "563650", "--dry-run")

    assert summary["trading_decision"] is False
    assert summary["no_trading_decision"] is True


def test_adapter_dry_runs_directory_is_ignored_by_git():
    text = GITIGNORE.read_text(encoding="utf-8")

    assert "pm_bot/llm/openrouter_adapter_dry_runs/" in text


def test_invalid_model_profile_returns_blocked_status(tmp_path):
    code, summary = _run(
        tmp_path,
        "--market-id",
        "563650",
        "--dry-run",
        "--model-profile",
        "unknown_profile",
    )

    assert code != 0
    assert summary["status"] in {"blocked_invalid_contract", "blocked_invalid_args"}


def test_contract_json_validates_with_json_tool():
    completed = subprocess.run(
        [sys.executable, "-m", "json.tool", str(CONTRACT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0


def test_operator_next_action_file_is_written_in_dry_run(tmp_path):
    code, summary = _run(tmp_path, "--market-id", "563650", "--dry-run")

    assert code == 0
    next_action_path = tmp_path / "operator_next_action_563650.md"
    assert next_action_path.exists()
    text = next_action_path.read_text(encoding="utf-8")
    assert "dry-run only" in text
    assert "No network call was made" in text
    assert "No API key was read" in text
    assert summary["artifact_paths"]["operator_next_action"] == str(next_action_path)
