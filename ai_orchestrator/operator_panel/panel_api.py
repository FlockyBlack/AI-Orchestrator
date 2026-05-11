from __future__ import annotations

from pathlib import Path
from typing import Any

from .panel_actions import (
    build_panel_dashboard_action,
    codex_adapter_dry_run_action,
    continue_run_action,
    continue_run_with_codex_cli_action,
    create_app_server_session_plan_action,
    create_codex_packet_action,
    create_queue_action,
    export_next_codex_prompt_action,
    ingest_codex_result_action,
    probe_app_server_schema_action,
    recover_run_action,
    render_app_server_dry_run_command_action,
    run_short_app_server_dry_run_action,
    run_fake_steps_action,
    save_pasted_plan_action,
    test_codex_cli_config_action,
    validate_plan_action,
)


def get_dashboard_json(repo_root: str | Path, queue_root: str | Path) -> dict[str, Any]:
    return build_panel_dashboard_action(repo_root, queue_root)


def post_validate_plan(form: dict[str, str], queue_root: str | Path) -> dict[str, Any]:
    return validate_plan_action(form.get("plan_file", ""))


def post_save_plan(form: dict[str, str], queue_root: str | Path) -> dict[str, Any]:
    return save_pasted_plan_action(form.get("plan_json", ""), queue_root, form.get("filename", "pasted_plan.json"))


def post_create_queue(form: dict[str, str], queue_root: str | Path) -> dict[str, Any]:
    return create_queue_action(form.get("plan_file", ""), queue_root)


def post_run_fake_steps(form: dict[str, str], queue_root: str | Path) -> dict[str, Any]:
    return run_fake_steps_action(form.get("plan_file", ""), queue_root, _int(form.get("max_steps"), 3))


def post_continue_run(form: dict[str, str], queue_root: str | Path) -> dict[str, Any]:
    return continue_run_action(
        form.get("run_id", ""),
        queue_root,
        _int(form.get("max_steps"), 3),
        executor=form.get("executor", "fake") or "fake",
    )


def post_continue_codex_cli(form: dict[str, str], queue_root: str | Path) -> dict[str, Any]:
    return continue_run_with_codex_cli_action(
        form.get("run_id", ""),
        queue_root,
        _int(form.get("max_steps"), 1),
        approval_text=form.get("approval_text", ""),
        approval_checked=form.get("approval_checked", "").lower() in {"1", "true", "on", "yes"},
    )


def post_test_codex_cli_config(form: dict[str, str], queue_root: str | Path) -> dict[str, Any]:
    return test_codex_cli_config_action(queue_root)


def post_recover_run(form: dict[str, str], queue_root: str | Path) -> dict[str, Any]:
    allow_clear = form.get("allow_stale_lock_clear", "").lower() in {"1", "true", "on", "yes"}
    return recover_run_action(form.get("run_id", ""), queue_root, allow_stale_lock_clear=allow_clear)


def post_export_handoff_prompt(form: dict[str, str], queue_root: str | Path) -> dict[str, Any]:
    return export_next_codex_prompt_action(form.get("run_id", ""), queue_root)


def post_create_codex_packet(form: dict[str, str], queue_root: str | Path) -> dict[str, Any]:
    return create_codex_packet_action(
        form.get("run_id", ""),
        queue_root,
        form.get("adapter_mode", "manual_handoff") or "manual_handoff",
    )


def post_codex_adapter_dry_run(form: dict[str, str], queue_root: str | Path) -> dict[str, Any]:
    return codex_adapter_dry_run_action(form.get("run_id", ""), queue_root)


def post_ingest_codex_result(form: dict[str, str], queue_root: str | Path) -> dict[str, Any]:
    return ingest_codex_result_action(
        form.get("packet_path", ""),
        form.get("result_json_text", "") or form.get("result_json_path", ""),
        queue_root,
    )


def post_app_server_schema_probe(form: dict[str, str], queue_root: str | Path) -> dict[str, Any]:
    return probe_app_server_schema_action(queue_root, form.get("schema_dir", ""))


def post_app_server_render_command(form: dict[str, str], repo_root: str | Path, queue_root: str | Path) -> dict[str, Any]:
    return render_app_server_dry_run_command_action(
        repo_root,
        queue_root,
        form.get("schema_dir", ""),
        form.get("listen_mode", "stdio") or "stdio",
    )


def post_app_server_dry_run(form: dict[str, str], repo_root: str | Path, queue_root: str | Path) -> dict[str, Any]:
    return run_short_app_server_dry_run_action(
        repo_root,
        queue_root,
        form.get("schema_dir", ""),
        approval_text=form.get("approval_text", ""),
    )


def post_create_app_server_session_plan(form: dict[str, str], queue_root: str | Path) -> dict[str, Any]:
    return create_app_server_session_plan_action(
        form.get("run_id", ""),
        queue_root,
        form.get("workspace_root", ""),
        form.get("schema_dir", ""),
    )


def _int(value: str | None, default: int) -> int:
    try:
        return int(value or default)
    except ValueError:
        return default
