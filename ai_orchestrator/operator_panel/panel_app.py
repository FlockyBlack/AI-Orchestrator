from __future__ import annotations

import argparse
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from . import panel_api
from .panel_actions import inspect_git_action
from .panel_state import discover_runs
from .panel_renderer import (
    render_artifacts_page,
    render_dashboard_page,
    render_git_page,
    render_handoff_page,
    render_codex_cli_page,
    render_plans_page,
    render_result_page,
    render_run_page,
    render_runs_page,
)


def make_handler(repo_root: str | Path, queue_root: str | Path) -> type[BaseHTTPRequestHandler]:
    repo_root_value = str(repo_root)
    queue_root_value = str(queue_root)

    class OperatorPanelHandler(BaseHTTPRequestHandler):
        server_version = "AIOrchestratorOperatorPanel/0.1"

        def do_GET(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            try:
                html = route_get(parsed.path, parsed.query, repo_root_value, queue_root_value)
            except Exception as exc:  # pragma: no cover - HTTP boundary
                self._send_html(render_result_page({"status": "failed", "error": str(exc)}, repo_root=repo_root_value, queue_root=queue_root_value), HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            self._send_html(html)

        def do_POST(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            length = int(self.headers.get("Content-Length", "0") or "0")
            body = self.rfile.read(length).decode("utf-8") if length else ""
            form = {key: values[-1] for key, values in parse_qs(body, keep_blank_values=True).items()}
            try:
                result = route_post(parsed.path, form, repo_root_value, queue_root_value)
            except Exception as exc:  # pragma: no cover - HTTP boundary
                result = {"status": "failed", "error": str(exc)}
            self._send_html(render_result_page(result, repo_root=repo_root_value, queue_root=queue_root_value))

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

        def _send_html(self, content: str, status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = content.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

    return OperatorPanelHandler


def route_get(path: str, query: str, repo_root: str | Path, queue_root: str | Path) -> str:
    data = panel_api.get_dashboard_json(repo_root, queue_root)
    if path == "/":
        return render_dashboard_page(data, repo_root=str(repo_root), queue_root=str(queue_root))
    if path == "/plans":
        return render_plans_page(data.get("plans", []), repo_root=str(repo_root), queue_root=str(queue_root))
    if path == "/runs":
        return render_runs_page(data.get("runs", []), repo_root=str(repo_root), queue_root=str(queue_root))
    if path == "/run":
        params = {key: values[-1] for key, values in parse_qs(query).items()}
        run_id = params.get("id", "")
        run = _build_run_detail(queue_root, run_id)
        return render_run_page(run, _collect_artifacts(queue_root, run_id), repo_root=str(repo_root), queue_root=str(queue_root))
    if path == "/artifacts":
        return render_artifacts_page(_collect_artifact_groups(queue_root), repo_root=str(repo_root), queue_root=str(queue_root))
    if path == "/git":
        return render_git_page(inspect_git_action(repo_root), repo_root=str(repo_root), queue_root=str(queue_root))
    if path == "/codex-handoff":
        paths = _collect_handoff_paths(queue_root)
        packet = _latest_codex_packet(queue_root)
        prompt_path = packet.get("prompt_path") or (paths[-1] if paths else "")
        prompt = Path(prompt_path).read_text(encoding="utf-8") if prompt_path and Path(prompt_path).exists() else ""
        template_path = packet.get("expected_result_template_path", "")
        template_text = Path(template_path).read_text(encoding="utf-8") if template_path and Path(template_path).exists() else ""
        ingestion_path = packet.get("ingestion_report_json_path", "")
        ingestion = _read_json(ingestion_path) if ingestion_path and Path(ingestion_path).exists() else {}
        handoff_paths = paths + ([str(packet["packet_path"])] if packet.get("packet_path") else [])
        return render_handoff_page(
            prompt,
            handoff_paths,
            repo_root=str(repo_root),
            queue_root=str(queue_root),
            task_id=str(packet.get("task_id") or _task_id_from_handoff(prompt_path)),
            packet=packet,
            template_text=template_text,
            ingestion=ingestion,
        )
    if path == "/codex-cli":
        return render_codex_cli_page(data, repo_root=str(repo_root), queue_root=str(queue_root))
    return render_result_page({"status": "not_found", "path": path}, repo_root=str(repo_root), queue_root=str(queue_root))


def route_post(path: str, form: dict[str, str], repo_root: str | Path, queue_root: str | Path) -> dict[str, Any]:
    if path == "/actions/save-plan":
        return panel_api.post_save_plan(form, queue_root)
    if path == "/actions/validate-plan":
        return panel_api.post_validate_plan(form, queue_root)
    if path == "/actions/create-queue":
        return panel_api.post_create_queue(form, queue_root)
    if path == "/actions/run-fake-steps":
        return panel_api.post_run_fake_steps(form, queue_root)
    if path == "/actions/continue-run":
        result = panel_api.post_continue_run(form, queue_root)
        result["redirect_to"] = f"/run?id={form.get('run_id', '')}"
        return result
    if path == "/actions/test-codex-cli-config":
        result = panel_api.post_test_codex_cli_config(form, queue_root)
        result["redirect_to"] = "/codex-cli"
        return result
    if path == "/actions/continue-codex-cli":
        result = panel_api.post_continue_codex_cli(form, queue_root)
        result["redirect_to"] = f"/run?id={form.get('run_id', '')}"
        return result
    if path == "/actions/create-codex-packet":
        result = panel_api.post_create_codex_packet(form, queue_root)
        result["redirect_to"] = "/codex-handoff"
        return result
    if path == "/actions/codex-adapter-dry-run":
        result = panel_api.post_codex_adapter_dry_run(form, queue_root)
        result["redirect_to"] = "/codex-handoff"
        return result
    if path == "/actions/ingest-codex-result":
        result = panel_api.post_ingest_codex_result(form, queue_root)
        result["redirect_to"] = f"/run?id={result.get('run_id', '')}"
        return result
    if path == "/actions/recover-run":
        result = panel_api.post_recover_run(form, queue_root)
        result["redirect_to"] = f"/run?id={form.get('run_id', '')}"
        return result
    if path == "/actions/export-codex-prompt":
        result = panel_api.post_export_handoff_prompt(form, queue_root)
        result["redirect_to"] = "/codex-handoff"
        return result
    return {"status": "not_found", "path": path}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local AI-Orchestrator operator panel.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--queue-root", default="agent_tasks")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    if args.host not in {"127.0.0.1", "localhost"}:
        raise SystemExit("operator panel must bind to 127.0.0.1/localhost unless code is changed deliberately")
    handler = make_handler(args.repo_root, args.queue_root)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(json.dumps({"status": "serving", "url": f"http://{args.host}:{args.port}", "repo_root": args.repo_root, "queue_root": args.queue_root}, sort_keys=True))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


def _collect_artifacts(queue_root: str | Path, run_id: str = "") -> list[str]:
    root = Path(queue_root)
    pattern = f"generated/*/{run_id}/**/*" if run_id else "generated/**/*"
    artifacts = []
    for path in sorted(root.glob(pattern)):
        if path.is_file() and path.name != "manifest.json":
            artifacts.append(str(path))
    return artifacts[-200:]


def _collect_artifact_groups(queue_root: str | Path) -> dict[str, list[str]]:
    all_files = _collect_artifacts(queue_root)
    return {
        "state JSON": [path for path in all_files if path.endswith("state.json")],
        "dashboard JSON/MD": [path for path in all_files if "/dashboard/" in path.replace("\\", "/")],
        "recovery reports": [path for path in all_files if "/recovery/" in path.replace("\\", "/")],
        "handoff prompts": [path for path in all_files if "/handoff/" in path.replace("\\", "/")],
        "codex packets": [path for path in all_files if "/codex_packets/" in path.replace("\\", "/")],
        "fake executor artifacts": [path for path in all_files if "/artifacts/" in path.replace("\\", "/")],
        "other": [
            path
            for path in all_files
            if not any(token in path.replace("\\", "/") for token in ("/dashboard/", "/recovery/", "/handoff/", "/codex_packets/", "/artifacts/"))
        ],
    }


def _collect_handoff_paths(queue_root: str | Path) -> list[str]:
    return [str(path) for path in sorted(Path(queue_root).glob("generated/*/*/handoff/*_codex_prompt.md"))]


def _latest_codex_packet(queue_root: str | Path) -> dict[str, Any]:
    packets = sorted(Path(queue_root).glob("generated/*/*/codex_packets/*/packet.json"))
    if not packets:
        return {}
    packet_path = packets[-1]
    payload = _read_json(packet_path)
    task_dir = packet_path.parent
    payload.update(
        {
            "packet_path": str(packet_path),
            "prompt_path": str(task_dir / "prompt.md"),
            "expected_result_template_path": str(task_dir / "expected_result_template.json"),
            "ingestion_report_json_path": str(task_dir / "ingestion_report.json"),
            "ingestion_report_md_path": str(task_dir / "ingestion_report.md"),
        }
    )
    return payload


def _build_run_detail(queue_root: str | Path, run_id: str) -> dict[str, Any]:
    summary = next((item for item in discover_runs(queue_root) if item["run_id"] == run_id), {"run_id": run_id, "status": "missing"})
    matches = sorted(Path(queue_root).glob(f"generated/*/{run_id}/manifest.json"))
    if not matches:
        return summary
    manifest_path = matches[0]
    manifest = _read_json(manifest_path)
    state_path = Path(str(manifest.get("state_path") or manifest_path.parent / "state.json"))
    state = _read_json(state_path)
    task_states = state.get("task_states", {}) if isinstance(state.get("task_states", {}), dict) else {}
    tasks = []
    for task_id in manifest.get("task_ids", []):
        task_path = Path(str(manifest.get("task_paths", {}).get(task_id) or manifest_path.parent / "tasks" / f"{task_id}.json"))
        task = _read_json(task_path)
        task_state = task_states.get(task_id, {}) if isinstance(task_states.get(task_id, {}), dict) else {}
        status = _task_status(task_id, state, task_state)
        tasks.append(
            {
                "task_id": str(task_id),
                "title": str(task.get("title") or ""),
                "status": status,
                "dependencies": [str(value) for value in task.get("dependencies", [])],
                "retry_count": int(state.get("retry_counts", {}).get(task_id, 0)) if isinstance(state.get("retry_counts", {}), dict) else 0,
                "max_retries": int(task.get("max_retries", 0) or 0),
                "artifact_paths": [str(value) for value in task_state.get("artifact_paths", [])],
                "last_event": str(task_state.get("last_event") or ""),
            }
        )
    detail = dict(summary)
    detail.update(
        {
            "manifest_path": str(manifest_path),
            "state_path": str(state_path),
            "manifest": manifest,
            "state": state,
            "tasks": tasks,
            "updated_at": str(state.get("updated_at") or manifest.get("updated_at") or ""),
        }
    )
    return detail


def _task_status(task_id: str, state: dict[str, Any], task_state: dict[str, Any]) -> str:
    if task_id in state.get("completed_task_ids", []):
        return "completed"
    if task_id in state.get("blocked_task_ids", []):
        return "blocked"
    if task_id in state.get("failed_task_ids", []):
        return "failed"
    if task_id in state.get("skipped_task_ids", []):
        return "skipped"
    return str(task_state.get("status") or "pending")


def _read_json(path: str | Path) -> dict[str, Any]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _task_id_from_handoff(path: str) -> str:
    if not path:
        return ""
    name = Path(path).name
    suffix = "_codex_prompt.md"
    return name[: -len(suffix)] if name.endswith(suffix) else name


if __name__ == "__main__":
    raise SystemExit(main())
