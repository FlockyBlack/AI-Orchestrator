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
    body {{ font-family: system-ui, sans-serif; margin: 0; background: #f7f7f4; color: #202124; }}
    header {{ background: #25312f; color: white; padding: 14px 18px; }}
    nav a {{ color: white; margin-right: 14px; text-decoration: none; }}
    main {{ padding: 18px; max-width: 1180px; margin: 0 auto; }}
    section {{ margin: 0 0 18px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }}
    .card {{ background: white; border: 1px solid #d8d8d0; border-radius: 8px; padding: 12px; }}
    .muted {{ color: #686b6a; }}
    pre {{ white-space: pre-wrap; background: #111827; color: #f9fafb; padding: 12px; overflow: auto; }}
    input, textarea, select {{ width: 100%; box-sizing: border-box; padding: 8px; margin: 4px 0 10px; }}
    button {{ padding: 8px 12px; border: 1px solid #25312f; background: #25312f; color: white; border-radius: 6px; }}
    table {{ border-collapse: collapse; width: 100%; background: white; }}
    th, td {{ border: 1px solid #d8d8d0; padding: 8px; text-align: left; vertical-align: top; }}
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
    git = data.get("git", {})
    body = f"""
<section class="grid">
  <div class="card"><strong>Branch</strong><br>{_e(git.get('branch', ''))}<br><span class="muted">{_e(git.get('head', ''))}</span></div>
  <div class="card"><strong>Plans</strong><br>{len(data.get('plans', []))}</div>
  <div class="card"><strong>Runs</strong><br>{len(data.get('runs', []))}</div>
  <div class="card"><strong>Active run</strong><br>{_e(active.get('run_id', 'none'))}<br><span class="muted">{_e(active.get('status', ''))}</span></div>
</section>
<section class="card">
  <h2>Plan runner</h2>
  {render_plan_forms(data.get('plans', []))}
</section>
<section class="card">
  <h2>Current dashboard</h2>
  <pre>{_e(json.dumps(data.get('dashboard') or {}, indent=2, sort_keys=True))}</pre>
</section>
"""
    return render_layout("Operator Panel", body, repo_root=repo_root, queue_root=queue_root)


def render_plans_page(plans: list[dict[str, Any]], *, repo_root: str, queue_root: str) -> str:
    rows = "".join(
        f"<tr><td>{_e(plan['plan_id'])}</td><td>{_e(plan['version'])}</td><td>{_e(plan['title'])}</td><td>{plan['task_count']}</td><td><code>{_e(plan['path'])}</code></td></tr>"
        for plan in plans
    )
    body = f"""
<section class="card">
  <h1>Plans</h1>
  <table><tr><th>plan_id</th><th>version</th><th>title</th><th>tasks</th><th>path</th></tr>{rows}</table>
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
        f'<tr><td><a href="/run?id={_e(run["run_id"])}">{_e(run["run_id"])}</a></td><td>{_e(run["plan_id"])}</td><td>{_e(run["status"])}</td><td>{run["completed_count"]}/{run["task_count"]}</td><td>{run["blocked_count"]}</td><td>{run["failed_count"]}</td></tr>'
        for run in runs
    )
    body = f"<section class=\"card\"><h1>Runs</h1><table><tr><th>run_id</th><th>plan_id</th><th>status</th><th>done</th><th>blocked</th><th>failed</th></tr>{rows}</table></section>"
    return render_layout("Runs", body, repo_root=repo_root, queue_root=queue_root)


def render_run_page(run: dict[str, Any], artifacts: list[str], *, repo_root: str, queue_root: str) -> str:
    body = f"""
<section class="card">
  <h1>Run {_e(run.get('run_id', ''))}</h1>
  <pre>{_e(json.dumps(run, indent=2, sort_keys=True))}</pre>
  <form method="post" action="/actions/continue-run">
    <input type="hidden" name="run_id" value="{_e(run.get('run_id', ''))}">
    <label>Max steps</label><input name="max_steps" value="5">
    <button type="submit">Continue fake steps</button>
  </form>
  <form method="post" action="/actions/export-codex-prompt">
    <input type="hidden" name="run_id" value="{_e(run.get('run_id', ''))}">
    <button type="submit">Export Codex prompt</button>
  </form>
</section>
<section class="card"><h2>Artifacts</h2>{_list(artifacts)}</section>
"""
    return render_layout("Run", body, repo_root=repo_root, queue_root=queue_root)


def render_artifacts_page(artifacts: list[str], *, repo_root: str, queue_root: str) -> str:
    return render_layout("Artifacts", f"<section class=\"card\"><h1>Artifacts</h1>{_list(artifacts)}</section>", repo_root=repo_root, queue_root=queue_root)


def render_git_page(git: dict[str, Any], *, repo_root: str, queue_root: str) -> str:
    return render_layout("Git", f"<section class=\"card\"><h1>Git</h1><pre>{_e(json.dumps(git, indent=2, sort_keys=True))}</pre></section>", repo_root=repo_root, queue_root=queue_root)


def render_handoff_page(prompt_text: str, handoff_paths: list[str], *, repo_root: str, queue_root: str) -> str:
    body = f"""
<section class="card">
  <h1>Codex Handoff</h1>
  <p class="muted">Generated prompts are files for manual operator review. The panel does not call Codex.</p>
  {_list(handoff_paths)}
  <pre>{_e(prompt_text)}</pre>
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
    return render_layout("Action Result", f"<section class=\"card\"><h1>Action Result</h1><pre>{_e(json.dumps(result, indent=2, sort_keys=True))}</pre><p><a href=\"/\">Back</a></p></section>", repo_root=repo_root, queue_root=queue_root)


def _list(values: list[str]) -> str:
    if not values:
        return "<p class=\"muted\">None</p>"
    return "<ul>" + "".join(f"<li><code>{_e(value)}</code></li>" for value in values) + "</ul>"


def _e(value: Any) -> str:
    return html.escape(str(value), quote=True)
