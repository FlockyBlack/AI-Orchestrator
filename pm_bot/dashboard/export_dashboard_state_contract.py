import argparse
import json
import sys
from pathlib import Path


TASK_ID = "PMBOT-DASHBOARD-001-DASHBOARD-STATE-EXPORT-CONTRACT"
ROOT = Path(__file__).resolve().parents[2]
DASHBOARD_DIR = ROOT / "pm_bot" / "dashboard"
PAPER_DIR = ROOT / "pm_bot" / "paper"
DOCS_DIR = ROOT / "docs"

DEFAULT_CONTRACT = DASHBOARD_DIR / "dashboard_state_contract.v1.json"
DEFAULT_PREVIEW_JSON = DASHBOARD_DIR / "dashboard_state_preview.v1.json"
DEFAULT_PREVIEW_MD = DASHBOARD_DIR / "dashboard_state_preview.v1.md"
DEFAULT_EXPECTED_PREVIEW_JSON = DASHBOARD_DIR / "expected_dashboard_state_preview.v1.json"

PAPER_ACCOUNTING_LEDGER = PAPER_DIR / "paper_accounting_ledger.v1.json"
PAPER_ACCOUNTING_PNL_PREVIEW = PAPER_DIR / "paper_accounting_pnl_preview.v1.json"
PAPER_FILL_EVENTS = PAPER_DIR / "paper_fill_events.v1.json"
PAPER_PORTFOLIO_SNAPSHOT = PAPER_DIR / "paper_portfolio_snapshot.v1.json"
PAPER_METRICS_REPORT = PAPER_DIR / "paper_metrics_report.v1.json"
MANUAL_PAPER_INTENT_LEDGER = PAPER_DIR / "manual_paper_intent_ledger.v1.json"

ROUND_PLAN = DOCS_DIR / "PMBOT_INFRA_005_ABC_PARALLEL_FEATURE_ROUND_PLAN.md"
ROUND_RESULT_CONTRACT = DOCS_DIR / "PMBOT_INFRA_005_CODEX_PARALLEL_RESULT_CONTRACT.v1.json"
PAPER_BATCH_011_013_RESULT = DOCS_DIR / "PMBOT_PAPER_BATCH_011_013_RESULT.json"
PAPER_BATCH_014_016_RESULT = DOCS_DIR / "PMBOT_PAPER_BATCH_014_016_RESULT.json"
INTEGRATION_002_RESULT = DOCS_DIR / "PMBOT_INTEGRATION_002_RESULT.json"
INTEGRATION_003_RESULT = DOCS_DIR / "PMBOT_INTEGRATION_003_RESULT.json"
LATEST_STAGE_SUMMARY = DOCS_DIR / "PM_BOT_STAGE_SUMMARY_V55.md"

DASHBOARD_STATE_SCHEMA_VERSION = "dashboard_state_preview.v1"
CONTRACT_SCHEMA_VERSION = "dashboard_state_contract.v1"
GENERATED_BY = "pm_bot/dashboard/export_dashboard_state_contract.py"
NOT_STRATEGY_PROFITABILITY_WARNING = (
    "Paper accounting PnL is fixture/manual accounting only and is not strategy profitability."
)

SAFETY_FLAGS = {
    "dashboard_runtime": False,
    "server": False,
    "frontend": False,
    "browser_automation": False,
    "runtime_wiring": False,
    "network_api": False,
    "authenticated_data": False,
    "credentials": False,
    "wallet": False,
    "trading": False,
    "real_orders": False,
    "live_trading": False,
    "autonomous_paper_orders": False,
    "scoring_probability_ev_edge": False,
    "market_decisions": False,
}

FORBIDDEN_CAPABILITIES = [
    "dashboard server or hosted runtime",
    "frontend application or browser automation",
    "network/API calls or live fetch results",
    "authenticated endpoints or authenticated data",
    "credentials, API keys, wallet access, private keys, or signing",
    "trading endpoints, real orders, live trading, or autonomous paper orders",
    "betting recommendations or market side recommendations",
    "probability estimates, EV calculations, edge calculations, or market scoring",
    "truth inference, live resolution, or market decisions",
    "dispatcher, run_codex, prompt automation, or runtime wiring changes",
]


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export the deterministic local PMBOT dashboard state contract and preview artifacts."
    )
    parser.add_argument("--write", action="store_true", help="Write contract, JSON preview, Markdown preview, and expected fixture.")
    parser.add_argument("--markdown", action="store_true", help="Print the Markdown dashboard state preview.")
    parser.add_argument("--contract", action="store_true", help="Print the JSON contract instead of the preview.")
    return parser.parse_args(argv)


def _display_path(path):
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def _load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _artifact_pointer(path, artifact_type, required=True):
    return {
        "path": _display_path(path),
        "artifact_type": artifact_type,
        "required": required,
        "present": Path(path).exists(),
    }


def _parse_stage_summary(path=LATEST_STAGE_SUMMARY):
    if not Path(path).exists():
        return {
            "source_path": _display_path(path),
            "present": False,
            "task": None,
            "status": "not_available",
        }
    task = None
    status = None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("Task: "):
            task = line.removeprefix("Task: ").strip()
        elif line.startswith("Status: "):
            status = line.removeprefix("Status: ").strip()
    return {
        "source_path": _display_path(path),
        "present": True,
        "task": task,
        "status": status,
    }


def _market_ids_from_payload(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            if key == "market_ids" and isinstance(nested, list):
                for market_id in nested:
                    if isinstance(market_id, (str, int)):
                        yield str(market_id)
            elif key == "market_id" and isinstance(nested, (str, int)):
                yield str(nested)
            else:
                yield from _market_ids_from_payload(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _market_ids_from_payload(item)


def _test_status_from_result_doc(path, payload):
    tests = payload.get("tests", [])
    if not isinstance(tests, list):
        tests = []
    return {
        "source_path": _display_path(path),
        "task_id": payload.get("task_id"),
        "status": payload.get("status"),
        "tests": [
            {
                "command": item.get("command"),
                "status": item.get("status"),
                "result": item.get("result") or item.get("summary"),
            }
            for item in tests
            if isinstance(item, dict)
        ],
    }


def build_dashboard_state_contract():
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "PMBOT_DASHBOARD_STATE_CONTRACT.v1",
        "title": "PMBOT Dashboard State Contract v1",
        "description": (
            "Schema-like local contract for a deterministic PMBOT dashboard state snapshot. "
            "This contract describes local artifacts only and does not define any dashboard runtime."
        ),
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "generated_by",
            "generated_at_policy",
            "market_ids",
            "product_stage_summary",
            "paper_accounting_summary",
            "latest_artifact_pointers",
            "test_status_summary",
            "safety_flags",
            "forbidden_capabilities",
            "operator_next_actions",
            "interpretation_warnings",
            "no_autonomous_decision_status",
        ],
        "properties": {
            "schema_version": {"const": DASHBOARD_STATE_SCHEMA_VERSION},
            "generated_by": {"const": GENERATED_BY},
            "generated_at_policy": {
                "type": "object",
                "required": ["wall_clock_time_used", "policy"],
                "properties": {
                    "wall_clock_time_used": {"const": False},
                    "policy": {"type": "string"},
                    "fixed_value": {"type": "string"},
                },
            },
            "market_ids": {"type": "array", "items": {"type": "string"}},
            "product_stage_summary": {"type": "object"},
            "paper_accounting_summary": {"type": "object"},
            "latest_artifact_pointers": {"type": "object"},
            "test_status_summary": {"type": "object"},
            "safety_flags": {"type": "object"},
            "forbidden_capabilities": {"type": "array", "items": {"type": "string"}},
            "operator_next_actions": {"type": "array", "items": {"type": "object"}},
            "interpretation_warnings": {"type": "array", "items": {"type": "string"}},
            "no_autonomous_decision_status": {"type": "object"},
        },
        "contract_boundary": {
            "local_file_reads_only": True,
            "deterministic_output": True,
            "stable_ordering": True,
            "dashboard_runtime_defined": False,
            "server_defined": False,
            "frontend_defined": False,
            "network_or_api_defined": False,
            "trading_or_ordering_defined": False,
            "scoring_probability_ev_edge_defined": False,
            "market_decision_defined": False,
        },
        "source_artifact_requirements": [
            _display_path(PAPER_ACCOUNTING_LEDGER),
            _display_path(PAPER_PORTFOLIO_SNAPSHOT),
            _display_path(PAPER_METRICS_REPORT),
            _display_path(PAPER_BATCH_014_016_RESULT),
            _display_path(INTEGRATION_003_RESULT),
        ],
    }


def build_dashboard_state_preview():
    paper_batch_011_013 = _load_json(PAPER_BATCH_011_013_RESULT)
    paper_batch_014_016 = _load_json(PAPER_BATCH_014_016_RESULT)
    integration_002 = _load_json(INTEGRATION_002_RESULT)
    integration_003 = _load_json(INTEGRATION_003_RESULT)
    accounting_ledger = _load_json(PAPER_ACCOUNTING_LEDGER)
    pnl_preview = _load_json(PAPER_ACCOUNTING_PNL_PREVIEW)
    portfolio_snapshot = _load_json(PAPER_PORTFOLIO_SNAPSHOT)
    metrics_report = _load_json(PAPER_METRICS_REPORT)
    stage_summary = _parse_stage_summary()

    market_ids = sorted(
        set(_market_ids_from_payload(accounting_ledger))
        | set(_market_ids_from_payload(pnl_preview))
        | set(_market_ids_from_payload(portfolio_snapshot))
        | set(_market_ids_from_payload(metrics_report))
        | set(_market_ids_from_payload(paper_batch_014_016))
    )

    latest_artifact_pointers = {
        "dashboard_contract": _artifact_pointer(DEFAULT_CONTRACT, "json_contract", required=True),
        "dashboard_preview_json": _artifact_pointer(DEFAULT_PREVIEW_JSON, "json_preview", required=True),
        "dashboard_preview_markdown": _artifact_pointer(DEFAULT_PREVIEW_MD, "markdown_preview", required=True),
        "dashboard_expected_preview_json": _artifact_pointer(
            DEFAULT_EXPECTED_PREVIEW_JSON, "json_expected_fixture", required=True
        ),
        "paper_accounting_ledger_json": _artifact_pointer(PAPER_ACCOUNTING_LEDGER, "paper_accounting_json"),
        "paper_accounting_pnl_preview_json": _artifact_pointer(
            PAPER_ACCOUNTING_PNL_PREVIEW, "paper_accounting_json"
        ),
        "paper_fill_events_json": _artifact_pointer(PAPER_FILL_EVENTS, "paper_fill_json"),
        "manual_paper_intent_ledger_json": _artifact_pointer(MANUAL_PAPER_INTENT_LEDGER, "paper_manual_fixture_json"),
        "paper_portfolio_snapshot_json": _artifact_pointer(PAPER_PORTFOLIO_SNAPSHOT, "paper_portfolio_json"),
        "paper_metrics_report_json": _artifact_pointer(PAPER_METRICS_REPORT, "paper_metrics_json"),
        "paper_batch_011_013_result": _artifact_pointer(PAPER_BATCH_011_013_RESULT, "docs_result_json"),
        "paper_batch_014_016_result": _artifact_pointer(PAPER_BATCH_014_016_RESULT, "docs_result_json"),
        "integration_002_result": _artifact_pointer(INTEGRATION_002_RESULT, "docs_result_json"),
        "integration_003_result": _artifact_pointer(INTEGRATION_003_RESULT, "docs_result_json"),
        "latest_stage_summary": _artifact_pointer(LATEST_STAGE_SUMMARY, "docs_markdown", required=False),
        "abc_round_plan": _artifact_pointer(ROUND_PLAN, "docs_markdown", required=True),
        "abc_round_result_contract": _artifact_pointer(ROUND_RESULT_CONTRACT, "docs_contract_json", required=True),
    }

    paper_accounting_metrics = metrics_report["paper_accounting_metrics"]
    return {
        "schema_version": DASHBOARD_STATE_SCHEMA_VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_policy": {
            "wall_clock_time_used": False,
            "policy": "deterministic_static_snapshot_no_current_time",
            "fixed_value": "not_emitted",
        },
        "market_ids": market_ids,
        "product_stage_summary": {
            "dashboard_scope": TASK_ID,
            "abc_round_stage": "CODEX_B dashboard state export contract round 001",
            "latest_overall_stage": stage_summary,
            "paper_accounting_stage": {
                "paper_batch_011_013_status": paper_batch_011_013.get("status"),
                "integration_002_verdict": integration_002.get("integration_verdict"),
                "paper_batch_014_016_status": paper_batch_014_016.get("status"),
                "integration_003_verdict": integration_003.get("integration_verdict"),
                "current_known_paper_status": "paper_portfolio_metrics_accepted_for_git_readiness_stage",
            },
        },
        "paper_accounting_summary": {
            "ledger_status": accounting_ledger.get("paper_accounting_ledger_status"),
            "portfolio_status": portfolio_snapshot.get("paper_portfolio_status"),
            "metrics_report_status": metrics_report.get("paper_metrics_report_status"),
            "market_ids": market_ids,
            "counts": {
                "paper_accounting_ledger_entries": accounting_ledger["counts"]["paper_accounting_ledger_entries"],
                "paper_accounting_settled_count": accounting_ledger["counts"]["paper_accounting_settled_count"],
                "paper_accounting_open_count": accounting_ledger["counts"]["paper_accounting_open_count"],
                "paper_portfolio_snapshot_records": portfolio_snapshot["counts"]["paper_portfolio_snapshot_records"],
                "paper_metrics_report_records": metrics_report["counts"]["paper_metrics_report_records"],
                "real_orders_created": 0,
                "live_orders_created": 0,
                "autonomous_paper_orders_created": 0,
            },
            "paper_accounting_metrics": {
                "paper_accounting_total_records": paper_accounting_metrics["paper_accounting_total_records"],
                "paper_accounting_settled_count": paper_accounting_metrics["paper_accounting_settled_count"],
                "paper_accounting_open_count": paper_accounting_metrics["paper_accounting_open_count"],
                "paper_accounting_win_count": paper_accounting_metrics["paper_accounting_win_count"],
                "paper_accounting_loss_count": paper_accounting_metrics["paper_accounting_loss_count"],
                "paper_accounting_flat_count": paper_accounting_metrics["paper_accounting_flat_count"],
                "paper_accounting_cumulative_pnl": paper_accounting_metrics["paper_accounting_cumulative_pnl"],
                "paper_accounting_average_pnl": paper_accounting_metrics["paper_accounting_average_pnl"],
                "paper_accounting_gross_profit": paper_accounting_metrics["paper_accounting_gross_profit"],
                "paper_accounting_gross_loss": paper_accounting_metrics["paper_accounting_gross_loss"],
                "paper_accounting_max_gain": paper_accounting_metrics["paper_accounting_max_gain"],
                "paper_accounting_max_loss": paper_accounting_metrics["paper_accounting_max_loss"],
            },
            "accounting_boundary": {
                "paper_accounting_only": True,
                "operator_manual_fixture_source": True,
                "strategy_profitability": False,
                "warning": NOT_STRATEGY_PROFITABILITY_WARNING,
            },
        },
        "latest_artifact_pointers": latest_artifact_pointers,
        "test_status_summary": {
            "derivation_policy": "copied from local result docs only; this export does not run tests while building state",
            "source_docs": [
                _test_status_from_result_doc(PAPER_BATCH_011_013_RESULT, paper_batch_011_013),
                _test_status_from_result_doc(INTEGRATION_002_RESULT, integration_002),
                _test_status_from_result_doc(PAPER_BATCH_014_016_RESULT, paper_batch_014_016),
                _test_status_from_result_doc(INTEGRATION_003_RESULT, integration_003),
            ],
        },
        "safety_flags": SAFETY_FLAGS,
        "forbidden_capabilities": FORBIDDEN_CAPABILITIES,
        "operator_next_actions": [
            {
                "action_id": "review_dashboard_state_contract",
                "description": "Review static JSON and Markdown dashboard state artifacts.",
                "non_trading_action": True,
                "requires_runtime": False,
            },
            {
                "action_id": "run_focused_dashboard_contract_tests",
                "description": "Run local pytest coverage for the dashboard state contract export.",
                "non_trading_action": True,
                "requires_runtime": False,
            },
            {
                "action_id": "integration_review_only",
                "description": "Use this snapshot as a stable contract input for a future reviewed dashboard.",
                "non_trading_action": True,
                "requires_runtime": False,
            },
        ],
        "interpretation_warnings": [
            NOT_STRATEGY_PROFITABILITY_WARNING,
            "This snapshot does not recommend a side, size, price, market, or trade.",
            "This snapshot does not contain probability estimates, EV, edge, market scoring, truth inference, live prices, or live fetch results.",
            "This snapshot reads local artifacts only and does not create executable orders or autonomous paper orders.",
        ],
        "no_autonomous_decision_status": {
            "autonomous_selection_enabled": False,
            "paper_order_generation_enabled": False,
            "operator_manual_review_required": True,
            "status": "no_autonomous_market_decision_or_order_status_defined",
        },
    }


def render_dashboard_state_markdown(preview_payload):
    accounting = preview_payload["paper_accounting_summary"]
    metrics = accounting["paper_accounting_metrics"]
    paper_stage = preview_payload["product_stage_summary"]["paper_accounting_stage"]
    pointers = preview_payload["latest_artifact_pointers"]
    lines = [
        "# PMBOT Dashboard State Preview v1",
        "",
        f"- schema_version: {preview_payload['schema_version']}",
        f"- generated_by: {preview_payload['generated_by']}",
        f"- generated_at_policy: {preview_payload['generated_at_policy']['policy']}",
        f"- market_ids: {', '.join(preview_payload['market_ids'])}",
        "",
        "## Product Stage",
        "",
        f"- dashboard_scope: {preview_payload['product_stage_summary']['dashboard_scope']}",
        f"- current_known_paper_status: {paper_stage['current_known_paper_status']}",
        f"- integration_003_verdict: {paper_stage['integration_003_verdict']}",
        "",
        "## Paper Accounting Summary",
        "",
        f"- ledger_status: {accounting['ledger_status']}",
        f"- portfolio_status: {accounting['portfolio_status']}",
        f"- metrics_report_status: {accounting['metrics_report_status']}",
        f"- paper_accounting_total_records: {metrics['paper_accounting_total_records']}",
        f"- paper_accounting_settled_count: {metrics['paper_accounting_settled_count']}",
        f"- paper_accounting_open_count: {metrics['paper_accounting_open_count']}",
        f"- paper_accounting_cumulative_pnl: {metrics['paper_accounting_cumulative_pnl']}",
        f"- paper_accounting_gross_profit: {metrics['paper_accounting_gross_profit']}",
        f"- paper_accounting_gross_loss: {metrics['paper_accounting_gross_loss']}",
        "",
        "## Artifact Pointers",
        "",
    ]
    for key in sorted(pointers):
        pointer = pointers[key]
        lines.append(f"- {key}: {pointer['path']} (present={str(pointer['present']).lower()})")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- dashboard_runtime: false",
            "- server: false",
            "- frontend: false",
            "- browser_automation: false",
            "- runtime_wiring: false",
            "- network_api: false",
            "- wallet: false",
            "- trading: false",
            "- autonomous_paper_orders: false",
            "- scoring_probability_ev_edge: false",
            "- market_decisions: false",
            "",
            "## Interpretation Warnings",
            "",
        ]
    )
    for warning in preview_payload["interpretation_warnings"]:
        lines.append(f"- {warning}")
    lines.append("")
    return "\n".join(lines)


def write_dashboard_state_artifacts():
    contract = build_dashboard_state_contract()
    _write_json(DEFAULT_CONTRACT, contract)

    # First pass materializes all generated files so artifact pointers are true
    # even when the exporter is run in a fresh checkout.
    preview = build_dashboard_state_preview()
    _write_json(DEFAULT_PREVIEW_JSON, preview)
    _write_json(DEFAULT_EXPECTED_PREVIEW_JSON, preview)
    _write_text(DEFAULT_PREVIEW_MD, render_dashboard_state_markdown(preview))

    preview = build_dashboard_state_preview()
    _write_json(DEFAULT_PREVIEW_JSON, preview)
    _write_json(DEFAULT_EXPECTED_PREVIEW_JSON, preview)
    _write_text(DEFAULT_PREVIEW_MD, render_dashboard_state_markdown(preview))
    return {
        "task_id": TASK_ID,
        "status": "dashboard_state_contract_exported",
        "files_written": [
            _display_path(DEFAULT_CONTRACT),
            _display_path(DEFAULT_PREVIEW_JSON),
            _display_path(DEFAULT_PREVIEW_MD),
            _display_path(DEFAULT_EXPECTED_PREVIEW_JSON),
        ],
        "market_ids": preview["market_ids"],
        "safety_flags": SAFETY_FLAGS,
    }


def main(argv):
    args = _parse_args(argv)
    if args.write:
        print(json.dumps(write_dashboard_state_artifacts(), indent=2, ensure_ascii=True))
        return 0
    if args.contract:
        print(json.dumps(build_dashboard_state_contract(), indent=2, ensure_ascii=True))
        return 0
    preview = build_dashboard_state_preview()
    if args.markdown:
        print(render_dashboard_state_markdown(preview), end="")
    else:
        print(json.dumps(preview, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
