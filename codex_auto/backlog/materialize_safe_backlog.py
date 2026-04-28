import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKLOG_PATH = PROJECT_ROOT / "docs" / "PM_BOT_SAFE_BACKLOG_V1.json"
PLAN_PATH = PROJECT_ROOT / "docs" / "PM_BOT_MASTER_PLAN_V1.md"
CANDIDATES_ROOT = PROJECT_ROOT / "codex_auto" / "tasks" / "candidates"
PROMPTS_ROOT = PROJECT_ROOT / "codex_auto" / "prompts"
PROMPT_FILE = PROMPTS_ROOT / "PMBOT-BATCH-001.codex_prompt.txt"
PROMPT_MANIFEST_FILE = PROMPTS_ROOT / "PMBOT-BATCH-001.prompt_manifest.json"
REPORT_FILE = CANDIDATES_ROOT / "PMBOT-BATCH-001.materialization.json"

SAFE_MODES = {"DESIGN_ONLY", "FIXTURE_ONLY", "PAPER_ONLY", "READ_ONLY_VALIDATION", "DRY_RUN_ONLY"}
FORBIDDEN_TERMS = (
    "live trading",
    "wallet",
    "private key",
    "real order",
    "runtime wiring",
    "dispatcher",
    "run_codex",
    "api execution",
    "network execution",
)
COMMON_FORBIDDEN_PATHS = [
    "scripts/dispatcher.py",
    "scripts/run_codex.py",
    "tasks/",
    "state/",
    "runtime/",
    "results/",
    "freeze/",
    "checkpoint/",
]
COMMON_FORBIDDEN_SCOPE = [
    "dispatcher modification",
    "run_codex modification",
    "active task mutation",
    "runtime-loop modification",
    "state/result/freeze/checkpoint mutation",
    "runtime wiring",
    "external Codex CLI execution",
    "network usage",
    "API usage",
    "wallet usage",
    "private key usage",
    "trading behavior",
    "real orders",
    "final Flocky/OpenClaw done claim",
    "second runtime source of truth",
]
COMMON_SAFETY_FLAGS = [
    "runtime_changed",
    "dispatcher_touched",
    "run_codex_touched",
    "active_task_files_touched",
    "freeze_record_modified",
    "result_records_modified",
    "checkpoint_records_modified",
    "network_used",
    "api_used",
    "wallet_used",
    "private_key_used",
    "trading_used",
    "single_runtime_source_rule_preserved",
]

TARGET_SPECS = [
    {
        "filename": "PMBOT-005-PAPER-SIMULATION.task.json",
        "materialized_task_id": "PMBOT-005-PAPER-SIMULATION",
        "codex_task_id": "PMBOT-005-PAPER-SIMULATION",
        "preferred_ids": ["PMBOT-005"],
        "keywords": ["paper simulation", "portfolio simulator", "simulator"],
        "mode": "PAPER_ONLY",
        "allowed_paths": ["pm_bot/paper/", "pm_bot/paper/tests/"],
        "fallback_title": "Paper simulation slice",
        "fallback_summary": "Implement a paper-only portfolio simulator slice with deterministic state transitions and no execution authority.",
        "fallback_done_criteria": [
            "Paper simulation inputs and outputs are deterministic",
            "Execution remains explicitly disabled",
            "Tests remain local and offline"
        ]
    },
    {
        "filename": "PMBOT-006-RISK-LIMITS.task.json",
        "materialized_task_id": "PMBOT-006-RISK-LIMITS",
        "codex_task_id": "PMBOT-006-RISK-LIMITS",
        "preferred_ids": ["PMBOT-011"],
        "keywords": ["risk limits", "scenario caps", "exposure"],
        "mode": "PAPER_ONLY",
        "allowed_paths": ["pm_bot/risk/", "pm_bot/risk/tests/"],
        "fallback_title": "Risk limits slice",
        "fallback_summary": "Define paper-only position caps, scenario constraints, and risk checks for simulated exposure.",
        "fallback_done_criteria": [
            "Risk limit checks are deterministic",
            "Paper-only constraints remain explicit",
            "No runtime or execution authority is introduced"
        ]
    },
    {
        "filename": "PMBOT-007-FEES-SLIPPAGE.task.json",
        "materialized_task_id": "PMBOT-007-FEES-SLIPPAGE",
        "codex_task_id": "PMBOT-007-FEES-SLIPPAGE",
        "preferred_ids": ["PMBOT-012"],
        "keywords": ["fees", "slippage", "accounting"],
        "mode": "PAPER_ONLY",
        "allowed_paths": ["pm_bot/accounting/", "pm_bot/accounting/tests/"],
        "fallback_title": "Fees and slippage accounting slice",
        "fallback_summary": "Model simulated costs for paper-only outcomes with deterministic fee and slippage accounting.",
        "fallback_done_criteria": [
            "Paper-only accounting remains deterministic",
            "No real order execution logic is introduced",
            "Tests pass without network access"
        ]
    },
    {
        "filename": "PMBOT-008-RESEARCH-DASHBOARD.task.json",
        "materialized_task_id": "PMBOT-008-RESEARCH-DASHBOARD",
        "codex_task_id": "PMBOT-008-RESEARCH-DASHBOARD",
        "preferred_ids": ["PMBOT-006", "PMBOT-013"],
        "keywords": ["dashboard", "report", "report layout"],
        "mode": "DESIGN_ONLY",
        "allowed_paths": ["pm_bot/reports/", "pm_bot/reports/tests/"],
        "fallback_title": "Research dashboard/report slice",
        "fallback_summary": "Define a local report layout for paper signals, exposures, and postmortem summaries.",
        "fallback_done_criteria": [
            "Report sections are documented",
            "Rendered outputs remain local-only",
            "No runtime wiring or live feeds are introduced"
        ]
    },
    {
        "filename": "PMBOT-009-FIXTURE-POSTMORTEM.task.json",
        "materialized_task_id": "PMBOT-009-FIXTURE-POSTMORTEM",
        "codex_task_id": "PMBOT-009-FIXTURE-POSTMORTEM",
        "preferred_ids": ["PMBOT-007", "PMBOT-014"],
        "keywords": ["postmortem", "lessons", "failures"],
        "mode": "DESIGN_ONLY",
        "allowed_paths": ["pm_bot/postmortem/", "pm_bot/postmortem/tests/"],
        "fallback_title": "Fixture postmortem slice",
        "fallback_summary": "Create a paper-only postmortem artifact for fixture runs with lessons, failures, and follow-up items.",
        "fallback_done_criteria": [
            "Postmortem schema is documented",
            "Critic-facing lessons remain explicit",
            "No execution path is implied"
        ]
    },
    {
        "filename": "PMBOT-010-STATIC-SAFETY-AUDIT.task.json",
        "materialized_task_id": "PMBOT-010-STATIC-SAFETY-AUDIT",
        "codex_task_id": "PMBOT-010-STATIC-SAFETY-AUDIT",
        "preferred_ids": ["PMBOT-009", "PMBOT-010", "PMBOT-016"],
        "keywords": ["dependency audit", "validation", "static safety audit", "read-only validation"],
        "mode": "READ_ONLY_VALIDATION",
        "allowed_paths": ["pm_bot/audit/", "pm_bot/audit/tests/"],
        "fallback_title": "Static safety audit slice",
        "fallback_summary": "Perform a read-only static audit of PM bot slices to confirm standard-library-only behavior and absence of execution or trading dependencies.",
        "fallback_done_criteria": [
            "Imports are reviewed read-only",
            "Forbidden capability surfaces are reported",
            "No dependencies are added"
        ]
    },
]


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_text(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return handle.read()


def _utc_timestamp():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _contains_forbidden(text: str):
    lowered = text.lower()
    return any(term in lowered for term in FORBIDDEN_TERMS)


def _normalize_scope(items):
    return [str(item) for item in items]


def _safe_backlog_items(backlog):
    items = []
    for task in backlog.get("tasks", []):
        combined_text = f"{task.get('title', '')} {task.get('summary', '')}".lower()
        if task.get("mode") not in SAFE_MODES:
            continue
        if _contains_forbidden(combined_text):
            continue
        items.append(task)
    return items


def _stable_generated_at():
    return datetime.fromtimestamp(BACKLOG_PATH.stat().st_mtime, tz=timezone.utc).replace(microsecond=0).isoformat()


def _select_source_task(spec, safe_items):
    for preferred_id in spec["preferred_ids"]:
        for item in safe_items:
            if item.get("task_id") == preferred_id:
                return item
    for keyword in spec["keywords"]:
        for item in safe_items:
            combined = f"{item.get('title', '')} {item.get('summary', '')}".lower()
            if keyword in combined:
                return item
    return None


def _candidate_payload(spec, source_task):
    if source_task is None:
        source_backlog_task_id = f"{spec['materialized_task_id']}-DERIVED"
        title = spec["fallback_title"]
        summary = spec["fallback_summary"]
        mode = spec["mode"]
        allowed_scope = [title]
        done_criteria = spec["fallback_done_criteria"]
    else:
        source_backlog_task_id = source_task["task_id"]
        title = source_task["title"]
        summary = source_task["summary"]
        mode = source_task["mode"] if source_task["mode"] in SAFE_MODES else spec["mode"]
        allowed_scope = _normalize_scope(source_task.get("allowed_scope", []))
        done_criteria = _normalize_scope(source_task.get("done_criteria", []))

    forbidden_scope = list(dict.fromkeys(COMMON_FORBIDDEN_SCOPE + _normalize_scope(source_task.get("forbidden_scope", []) if source_task else [])))
    return {
        "schema_version": "v1",
        "materialized_task_id": spec["materialized_task_id"],
        "source_backlog_task_id": source_backlog_task_id,
        "codex_task_id": spec["codex_task_id"],
        "title": title,
        "summary": summary,
        "queue_state": "candidate",
        "mode": mode,
        "executor": "Codex",
        "source_backlog_path": "docs/PM_BOT_SAFE_BACKLOG_V1.json",
        "generated_prompt_ref": "codex_auto/prompts/PMBOT-BATCH-001.codex_prompt.txt",
        "allowed_paths": spec["allowed_paths"],
        "forbidden_paths": COMMON_FORBIDDEN_PATHS,
        "allowed_scope": allowed_scope,
        "forbidden_scope": forbidden_scope,
        "done_criteria": done_criteria,
        "requires_human_approval": True,
        "approved_for_execution": False,
        "dry_run_default": True,
        "flocky_validation_required": True,
        "runtime_wiring_allowed": False,
        "external_codex_cli_allowed": False,
        "safety_flags": COMMON_SAFETY_FLAGS,
    }


def _build_prompt_text(candidates):
    lines = [
        "TASK_ID: PMBOT-BATCH-001",
        "MODE: CODEX_SAFE_IMPLEMENTATION_BUNDLED",
        f"PROJECT_PATH: {PROJECT_ROOT}",
        "",
        "Context:",
        "- This is a generated future Codex prompt pack for safe PM bot candidate tasks only.",
        "- It is not executed by the current materializer.",
        "- External Codex CLI must not be invoked by the current materializer.",
        "",
        "Safety rules:",
        "- No runtime wiring.",
        "- No dispatcher or run_codex modification.",
        "- No active task mutation.",
        "- No runtime/state/result/freeze/checkpoint mutation.",
        "- No network/API/wallet/private key/trading.",
        "- No real orders.",
        "- No second runtime source of truth.",
        "- Final Flocky/OpenClaw done must not be claimed.",
        "",
        "Allowed candidate paths:",
    ]
    for candidate in candidates:
        lines.append(f"- {candidate['codex_task_id']}: {', '.join(candidate['allowed_paths'])}")
    lines.extend(
        [
            "",
            "Forbidden paths:",
            "- scripts/dispatcher.py",
            "- scripts/run_codex.py",
            "- tasks/",
            "- state/",
            "- runtime/",
            "- results/",
            "- freeze/",
            "- checkpoint/",
            "",
            "Phase plan:",
            "1. PMBOT-005 paper simulation",
            "2. PMBOT-006 risk limits",
            "3. PMBOT-007 fees/slippage accounting",
            "4. PMBOT-008 research dashboard/report",
            "5. PMBOT-009 fixture postmortem",
            "6. PMBOT-010 static safety audit",
            "",
            "Tests required:",
            "- Add or update local offline tests for each allowed path slice only.",
            "- Validate deterministic outputs and safety gates.",
            "",
            "Full validation required:",
            "- Run the smallest relevant tests first.",
            "- Confirm no runtime wiring, no network/API/wallet/private key/trading, and no external Codex CLI invocation.",
            "",
            "Final output required:",
            '- Return compact JSON only with status, changed files, tests run, tests passed, safety check, risks, notes, and recommended next action.',
        ]
    )
    return "\n".join(lines) + "\n"


def _write_if_missing_or_same(path: Path, content: str):
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            return "already_exists_valid"
        if path.suffix == ".json":
            try:
                json.loads(existing)
                return "already_exists_valid"
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"existing_conflict:{path}") from exc
        if existing.strip():
            return "already_exists_valid"
        raise RuntimeError(f"existing_conflict:{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "created"


def main(argv):
    if len(argv) != 2:
        print(json.dumps({"status": "blocked", "source_backlog_path": None, "candidates_created": [], "prompts_created": [], "skipped": ["usage: materialize_safe_backlog.py <backlog.json>"], "safety_check": {}}, separators=(",", ":")))
        return 2

    source_path = Path(argv[1])
    backlog = _load_json(source_path)
    _ = _load_text(PLAN_PATH)
    safe_items = _safe_backlog_items(backlog)

    candidates_created = []
    prompts_created = []
    skipped = []
    validations = []
    candidates = []

    for spec in TARGET_SPECS:
        source_task = _select_source_task(spec, safe_items)
        candidate = _candidate_payload(spec, source_task)
        candidates.append(candidate)
        target_path = CANDIDATES_ROOT / spec["filename"]
        content = json.dumps(candidate, indent=2) + "\n"
        outcome = _write_if_missing_or_same(target_path, content)
        validations.append(f"{spec['filename']}:{outcome}")
        if outcome == "created":
            candidates_created.append(str(target_path.relative_to(PROJECT_ROOT)).replace("\\", "/"))
        if source_task is None:
            skipped.append(f"fallback_used:{spec['materialized_task_id']}")

    prompt_text = _build_prompt_text(candidates)
    prompt_outcome = _write_if_missing_or_same(PROMPT_FILE, prompt_text)
    validations.append(f"{PROMPT_FILE.name}:{prompt_outcome}")
    if prompt_outcome == "created":
        prompts_created.append(str(PROMPT_FILE.relative_to(PROJECT_ROOT)).replace("\\", "/"))

    prompt_manifest = {
        "schema_version": "v1",
        "prompt_id": "PMBOT-BATCH-001",
        "generated_at": _stable_generated_at(),
        "prompt_path": "codex_auto/prompts/PMBOT-BATCH-001.codex_prompt.txt",
        "candidate_task_refs": [f"codex_auto/tasks/candidates/{spec['filename']}" for spec in TARGET_SPECS],
        "execution_allowed_now": False,
        "requires_flocky_review_before_execution": True,
        "requires_human_approval_before_execution": True,
        "runtime_wiring_allowed": False,
        "external_codex_cli_allowed_now": False,
        "safety_check": {
            "runtime_changed": False,
            "dispatcher_touched": False,
            "run_codex_touched": False,
            "active_task_files_touched": False,
            "freeze_record_modified": False,
            "result_records_modified": False,
            "checkpoint_records_modified": False,
            "network_used": False,
            "api_used": False,
            "wallet_used": False,
            "private_key_used": False,
            "trading_used": False,
            "single_runtime_source_rule_preserved": True
        }
    }
    manifest_outcome = _write_if_missing_or_same(PROMPT_MANIFEST_FILE, json.dumps(prompt_manifest, indent=2) + "\n")
    validations.append(f"{PROMPT_MANIFEST_FILE.name}:{manifest_outcome}")
    if manifest_outcome == "created":
        prompts_created.append(str(PROMPT_MANIFEST_FILE.relative_to(PROJECT_ROOT)).replace("\\", "/"))

    report = {
        "schema_version": "v1",
        "report_id": "PMBOT-BATCH-001",
        "source_backlog_path": "docs/PM_BOT_SAFE_BACKLOG_V1.json",
        "generated_at": _stable_generated_at(),
        "candidates_created": [f"codex_auto/tasks/candidates/{spec['filename']}" for spec in TARGET_SPECS],
        "candidates_skipped": skipped,
        "prompts_created": [
            "codex_auto/prompts/PMBOT-BATCH-001.codex_prompt.txt",
            "codex_auto/prompts/PMBOT-BATCH-001.prompt_manifest.json"
        ],
        "validation_summary": {
            "candidate_count": len(TARGET_SPECS),
            "writes": [f"{spec['filename']}:managed" for spec in TARGET_SPECS] + ["PMBOT-BATCH-001.codex_prompt.txt:managed", "PMBOT-BATCH-001.prompt_manifest.json:managed", "PMBOT-BATCH-001.materialization.json:managed"],
            "generated_prompt_not_executed": True
        },
        "safety_check": {
            "runtime_changed": False,
            "dispatcher_touched": False,
            "run_codex_touched": False,
            "active_task_files_touched": False,
            "freeze_record_modified": False,
            "result_records_modified": False,
            "checkpoint_records_modified": False,
            "network_used": False,
            "api_used": False,
            "wallet_used": False,
            "private_key_used": False,
            "trading_used": False,
            "single_runtime_source_rule_preserved": True
        },
        "recommended_next_action": "Run bundled Flocky validation on generated candidates before any promotion to ready."
    }
    report_outcome = _write_if_missing_or_same(REPORT_FILE, json.dumps(report, indent=2) + "\n")
    validations.append(f"{REPORT_FILE.name}:{report_outcome}")
    if report_outcome == "created":
        candidates_created.append(str(REPORT_FILE.relative_to(PROJECT_ROOT)).replace("\\", "/"))

    print(
        json.dumps(
            {
                "status": "done",
                "source_backlog_path": str(source_path.relative_to(PROJECT_ROOT)).replace("\\", "/") if source_path.is_absolute() else str(source_path).replace("\\", "/"),
                "candidates_created": candidates_created,
                "prompts_created": prompts_created,
                "skipped": skipped,
                "safety_check": report["safety_check"],
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
