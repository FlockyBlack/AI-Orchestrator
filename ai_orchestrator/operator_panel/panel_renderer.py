from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def render_layout(title: str, body: str, *, repo_root: str, queue_root: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_e(title)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 0; background: #f6f7f4; color: #202124; }}
    header {{ background: #26322f; color: white; padding: 14px 18px; }}
    nav a {{ color: white; margin-right: 14px; text-decoration: none; }}
    main {{ padding: 18px; max-width: 1280px; margin: 0 auto; }}
    section {{ margin: 0 0 18px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 12px; }}
    .card {{ background: white; border: 1px solid #d8d8d0; border-radius: 8px; padding: 12px; }}
    .muted {{ color: #676c69; }}
    .ok {{ color: #17643b; font-weight: 700; }}
    .warn {{ color: #8a4b00; font-weight: 700; }}
    .bad {{ color: #a32424; font-weight: 700; }}
    pre, textarea.copy {{ white-space: pre-wrap; background: #111827; color: #f9fafb; padding: 12px; overflow: auto; width: 100%; box-sizing: border-box; }}
    input, textarea, select {{ width: 100%; box-sizing: border-box; padding: 8px; margin: 4px 0 10px; }}
    button {{ padding: 8px 12px; border: 1px solid #26322f; background: #26322f; color: white; border-radius: 6px; margin: 0 6px 8px 0; }}
    table {{ border-collapse: collapse; width: 100%; background: white; }}
    th, td {{ border: 1px solid #d8d8d0; padding: 8px; text-align: left; vertical-align: top; }}
    code {{ word-break: break-word; }}
    .inline-form {{ display: inline-block; margin-right: 8px; }}
  </style>
</head>
<body>
<header>
  <nav>
    <a href="/">Dashboard</a>
    <a href="/plans">Plans</a>
    <a href="/runs">Runs</a>
    <a href="/artifacts">Artifacts</a>
    <a href="/git">Git</a>
    <a href="/codex-handoff">Codex Handoff</a>
  </nav>
  <div class="muted">repo: {_e(repo_root)} | queue: {_e(queue_root)}</div>
</header>
<main>
{body}
</main>
</body>
</html>"""


def render_dashboard_page(data: dict[str, Any], *, repo_root: str, queue_root: str) -> str:
    active = data.get("active_run") or {}
    dashboard = data.get("dashboard") or {}
    git = data.get("git", {})
    counts = dashboard.get("counts", {})
    body = f"""
<section class="grid">
  <div class="card"><strong>Branch</strong><br>{_e(git.get('branch', ''))}<br><span class="muted">{_e(git.get('head', ''))}</span><br>dirty: {_e(_dirty(git))}</div>
  <div class="card"><strong>Active run</strong><br>{_link_run(active.get('run_id', 'none'))}<br><span class="{_status_class(active.get('status', ''))}">{_e(active.get('status', ''))}</span></div>
  <div class="card"><strong>Tasks</strong><br>done {_e(counts.get('completed', 0))} / total {_e(counts.get('total', 0))}<br>blocked {_e(counts.get('blocked', 0))}, failed {_e(counts.get('failed', 0))}, pending {_e(counts.get('pending', active.get('pending_count', 0)))}</div>
  <div class="card"><strong>Safety</strong><br>{_e(dashboard.get('safety_status', 'unknown'))}<br><span class="muted">consistency: {_e(dashboard.get('state_consistency_status', ''))}</span></div>
</section>
<section class="card">
  <h2>Run controls</h2>
  {_active_run_controls(active)}
</section>
<section class="grid">
  <div class="card"><strong>Current task</strong><br><code>{_e(dashboard.get('current_task') or active.get('current_task_id') or 'none')}</code></div>
  <div class="card"><strong>Next runnable</strong>{_list_inline(dashboard.get('next_runnable_tasks') or [])}</div>
  <div class="card"><strong>Retry counts</strong><pre>{_e(json.dumps(dashboard.get('retry_counts') or {}, indent=2, sort_keys=True))}</pre></div>
  <div class="card"><strong>Latest checkpoint</strong><br><code>{_e((dashboard.get('latest_checkpoint') or {}).get('checkpoint_id', 'none'))}</code></div>
</section>
<section class="grid">
  <div class="card"><strong>Latest artifacts</strong>{_list(dashboard.get('latest_artifacts') or active.get('latest_artifacts') or [])}</div>
  <div class="card"><strong>Latest handoff prompt</strong><br><code>{_e(dashboard.get('latest_handoff_prompt_path') or active.get('latest_handoff_prompt_path') or 'none')}</code></div>
  <div class="card"><strong>Latest recovery report</strong><br><code>{_e(dashboard.get('latest_recovery_report_path') or active.get('latest_recovery_report_path') or 'none')}</code></div>
  <div class="card"><strong>Next operator action</strong><br>{_e(dashboard.get('next_operator_action', ''))}</div>
</section>
<section class="card">
  <h2>Plan runner</h2>
  {render_plan_forms(data.get('plans', []))}
</section>
<section class="card">
  <h2>Current dashboard JSON</h2>
  <pre>{_e(json.dumps(dashboard, indent=2, sort_keys=True))}</pre>
</section>
"""
    return render_layout("Operator Panel", body, repo_root=repo_root, queue_root=queue_root)


def render_plans_page(plans: list[dict[str, Any]], *, repo_root: str, queue_root: str) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{_e(plan['plan_id'])}</td>"
        f"<td>{_e(plan['version'])}</td>"
        f"<td>{_e(plan['title'])}</td>"
        f"<td>{plan['task_count']}</td>"
        f"<td>{plan.get('milestone_count', 0)}</td>"
        f"<td><code>{_e(plan.get('expected_head', ''))}</code></td>"
        f"<td>{_e('; '.join(plan.get('safety_boundaries', [])[:3]))}</td>"
        f"<td><code>{_e(plan['path'])}</code></td>"
        "</tr>"
        for plan in plans
    )
    body = f"""
<section class="card">
  <h1>Plans</h1>
  <table><tr><th>plan_id</th><th>version</th><th>title</th><th>tasks</th><th>milestones</th><th>expected head</th><th>safety boundaries</th><th>path</th></tr>{rows}</table>
</section>
<section class="card">
  <h2>Paste plan</h2>
  <form method="post" action="/actions/save-plan">
    <label>Filename</label><input name="filename" value="pasted_plan.json">
    <label>Plan JSON</label><textarea name="plan_json" rows="14"></textarea>
    <button type="submit">Save plan</button>
  </form>
</section>
"""
    return render_layout("Plans", body, repo_root=repo_root, queue_root=queue_root)


def render_runs_page(runs: list[dict[str, Any]], *, repo_root: str, queue_root: str) -> str:
    rows = "".join(
        "<tr>"
        f'<td><a href="/run?id={_e(run["run_id"])}">{_e(run["run_id"])}</a></td>'
        f"<td>{_e(run['plan_id'])}</td>"
        f"<td class=\"{_status_class(run['status'])}\">{_e(run['status'])}</td>"
        f"<td>{run['completed_count']}</td>"
        f"<td>{run.get('blocked_count', 0)}</td>"
        f"<td>{run.get('failed_count', 0)}</td>"
        f"<td>{run.get('pending_count', 0)}</td>"
        f"<td>{_e(run.get('updated_at', ''))}</td>"
        "</tr>"
        for run in runs
    )
    body = f"<section class=\"card\"><h1>Runs</h1><table><tr><th>run_id</th><th>plan_id</th><th>status</th><th>completed</th><th>blocked</th><th>failed</th><th>pending</th><th>updated_at</th></tr>{rows}</table></section>"
    return render_layout("Runs", body, repo_root=repo_root, queue_root=queue_root)


def render_run_page(run: dict[str, Any], artifacts: list[str], *, repo_root: str, queue_root: str) -> str:
    tasks = run.get("tasks", []) if isinstance(run.get("tasks"), list) else []
    rows = "".join(
        "<tr>"
        f"<td><code>{_e(task.get('task_id', ''))}</code></td>"
        f"<td>{_e(task.get('title', ''))}</td>"
        f"<td class=\"{_status_class(task.get('status', ''))}\">{_e(task.get('status', ''))}</td>"
        f"<td>{_e(', '.join(task.get('dependencies', [])))}</td>"
        f"<td>{_e(task.get('retry_count', 0))}/{_e(task.get('max_retries', 0))}</td>"
        f"<td>{_list(task.get('artifact_paths', []))}</td>"
        f"<td>{_e(task.get('last_event', ''))}</td>"
        "</tr>"
        for task in tasks
    )
    body = f"""
<section class="card">
  <h1>Run {_e(run.get('run_id', ''))}</h1>
  <p><strong>plan:</strong> {_e(run.get('plan_id', ''))} | <strong>status:</strong> <span class="{_status_class(run.get('status', ''))}">{_e(run.get('status', ''))}</span> | <strong>updated:</strong> {_e(run.get('updated_at', ''))}</p>
  {_run_action_forms(run.get('run_id', ''))}
</section>
<section class="card">
  <h2>Tasks</h2>
  <table><tr><th>task_id</th><th>title</th><th>status</th><th>dependencies</th><th>retry</th><th>artifact</th><th>last event</th></tr>{rows}</table>
</section>
<section class="card"><h2>Artifacts</h2>{_list(artifacts)}</section>
<section class="card"><h2>Raw run</h2><pre>{_e(json.dumps(run, indent=2, sort_keys=True))}</pre></section>
"""
    return render_layout("Run", body, repo_root=repo_root, queue_root=queue_root)


def render_artifacts_page(artifacts: dict[str, list[str]] | list[str], *, repo_root: str, queue_root: str) -> str:
    if isinstance(artifacts, dict):
        body = "<section class=\"card\"><h1>Artifacts</h1>"
        for label, values in artifacts.items():
            body += f"<h2>{_e(label)}</h2>{_list(values)}"
        body += "</section>"
    else:
        body = f"<section class=\"card\"><h1>Artifacts</h1>{_list(artifacts)}</section>"
    return render_layout("Artifacts", body, repo_root=repo_root, queue_root=queue_root)


def render_git_page(git: dict[str, Any], *, repo_root: str, queue_root: str) -> str:
    return render_layout("Git", f"<section class=\"card\"><h1>Git</h1><pre>{_e(json.dumps(git, indent=2, sort_keys=True))}</pre></section>", repo_root=repo_root, queue_root=queue_root)


def render_handoff_page(prompt_text: str, handoff_paths: list[str], *, repo_root: str, queue_root: str, task_id: str = "") -> str:
    expected = {
        "task_id": task_id or "<TASK_ID>",
        "status": "completed|blocked|failed",
        "validation_passed": True,
        "safety_ok": True,
        "artifacts": [],
        "commands_run": [],
        "summary": "",
        "remaining_risks": [],
    }
    body = f"""
<section class="card">
  <h1>Codex Handoff</h1>
  <p class="muted">Generated prompts are files for manual operator review. The panel does not call Codex.</p>
  <p><strong>task_id:</strong> <code>{_e(task_id or 'unknown')}</code></p>
  <p><strong>path:</strong></p>{_list(handoff_paths[-10:])}
  <h2>Expected result JSON</h2>
  <pre>{_e(json.dumps(expected, indent=2, sort_keys=True))}</pre>
  <h2>Prompt</h2>
  <textarea class="copy" rows="28" readonly>{_e(prompt_text)}</textarea>
</section>
"""
    return render_layout("Codex Handoff", body, repo_root=repo_root, queue_root=queue_root)


def render_plan_forms(plans: list[dict[str, Any]]) -> str:
    options = "".join(f'<option value="{_e(plan["path"])}">{_e(plan["plan_id"] or Path(plan["path"]).name)}</option>' for plan in plans)
    return f"""
<form method="post" action="/actions/validate-plan">
  <label>Plan file</label><select name="plan_file">{options}</select>
  <button type="submit">Validate</button>
</form>
<form method="post" action="/actions/create-queue">
  <label>Plan file</label><select name="plan_file">{options}</select>
  <button type="submit">Create queue</button>
</form>
<form method="post" action="/actions/run-fake-steps">
  <label>Plan file</label><select name="plan_file">{options}</select>
  <label>Max steps</label><input name="max_steps" value="3">
  <button type="submit">Run fake steps</button>
</form>
"""


def render_result_page(result: dict[str, Any], *, repo_root: str, queue_root: str) -> str:
    back = result.get("redirect_to") or result.get("back_to") or "/"
    return render_layout(
        "Action Result",
        f"<section class=\"card\"><h1>Action Result</h1><p>Status: <strong>{_e(result.get('status', ''))}</strong></p><pre>{_e(json.dumps(result, indent=2, sort_keys=True))}</pre><p><a href=\"{_e(back)}\">Back</a> | <a href=\"/runs\">Runs</a> | <a href=\"/artifacts\">Artifacts</a></p></section>",
        repo_root=repo_root,
        queue_root=queue_root,
    )


def _active_run_controls(active: dict[str, Any]) -> str:
    run_id = str(active.get("run_id") or "")
    if not run_id or run_id == "none":
        return "<p class=\"muted\">No active run.</p>"
    return _run_action_forms(run_id)


def _run_action_forms(run_id: str) -> str:
    return f"""
<form class="inline-form" method="post" action="/actions/continue-run">
  <input type="hidden" name="run_id" value="{_e(run_id)}">
  <input type="hidden" name="max_steps" value="1">
  <button type="submit">Continue 1 step</button>
</form>
<form class="inline-form" method="post" action="/actions/continue-run">
  <input type="hidden" name="run_id" value="{_e(run_id)}">
  <input type="hidden" name="max_steps" value="3">
  <button type="submit">Continue 3 steps</button>
</form>
<form class="inline-form" method="post" action="/actions/export-codex-prompt">
  <input type="hidden" name="run_id" value="{_e(run_id)}">
  <button type="submit">Export handoff prompt</button>
</form>
<form class="inline-form" method="post" action="/actions/recover-run">
  <input type="hidden" name="run_id" value="{_e(run_id)}">
  <button type="submit">Recover</button>
</form>
<form class="inline-form" method="get" action="/run">
  <input type="hidden" name="id" value="{_e(run_id)}">
  <button type="submit">Refresh</button>
</form>
"""


def _list(values: list[str]) -> str:
    if not values:
        return "<p class=\"muted\">None</p>"
    return "<ul>" + "".join(f"<li><code>{_e(value)}</code></li>" for value in values) + "</ul>"


def _list_inline(values: list[str]) -> str:
    if not values:
        return "<br><span class=\"muted\">None</span>"
    return "<ul>" + "".join(f"<li><code>{_e(value)}</code></li>" for value in values[:10]) + "</ul>"


def _link_run(run_id: Any) -> str:
    value = str(run_id or "")
    if not value or value == "none":
        return "none"
    return f'<a href="/run?id={_e(value)}">{_e(value)}</a>'


def _status_class(status: Any) -> str:
    value = str(status).lower()
    if value in {"failed", "blocked", "inconsistent", "missing_state"}:
        return "bad"
    if value in {"paused", "recovering", "needs_retry", "max_steps"}:
        return "warn"
    if value in {"completed", "done", "recovered", "running", "ok"}:
        return "ok"
    return ""


def _dirty(git: dict[str, Any]) -> str:
    status = git.get("git_status", {})
    if isinstance(status, dict):
        stdout = str(status.get("stdout") or "")
        return "yes" if stdout.strip() else "no"
    return "unknown"


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)
