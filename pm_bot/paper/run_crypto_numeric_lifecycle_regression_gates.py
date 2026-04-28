import argparse
import importlib.util
import json
import sys
from pathlib import Path


SAFETY_FLAGS = {
    "offline_only": True,
    "paper_only": True,
    "execution_allowed": False,
    "trading_allowed": False,
    "real_order_created": False,
    "wallet_used": False,
    "api_used": False,
    "network_used": False,
}

EXPECTED_SUMMARY = {
    "scenarios": 7,
    "filled_orders": 3,
    "wins": 2,
    "losses": 0,
    "bad_entries": 0,
    "rejected_bad_cases": 1,
}


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Validate crypto numeric paper lifecycle replay regression gates.")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _gate(name, passed, details):
    return {
        "gate_id": name,
        "passed": bool(passed),
        "details": details,
    }


def _safety_locked(payload):
    return all(payload.get(key) == value for key, value in SAFETY_FLAGS.items())


def _scenarios_by_id(report):
    return {row["scenario_id"]: row for row in report["scenarios"]}


def _all_scenario_safety_locked(report):
    return all(_safety_locked(row) for row in report["scenarios"])


def _aggregate_gate(report):
    summary = report["replay_summary"]
    mismatches = {
        key: {"expected": expected, "actual": summary.get(key)}
        for key, expected in EXPECTED_SUMMARY.items()
        if summary.get(key) != expected
    }
    return _gate("aggregate_outcomes_locked", not mismatches, {"mismatches": mismatches})


def _bad_entry_gate(report):
    summary = report["replay_summary"]
    return _gate(
        "bad_entries_locked_zero",
        summary["bad_entries"] == 0 and summary["losses"] == 0,
        {"bad_entries": summary["bad_entries"], "losses": summary["losses"]},
    )


def _settled_no_gate(report):
    rows = _scenarios_by_id(report)
    row = rows["filled_loss"]
    events = row["ledger_events"]
    blocked = (
        row["lifecycle_status"] == "not_filled"
        and row["paper_orders_filled"] == 0
        and row["paper_orders_not_filled"] == 1
        and row["paper_pnl"] == 0
        and len(events) == 2
        and events[1]["event_type"] == "paper_order_not_filled"
        and events[1]["reason"] == "Fixture market is already settled no; paper fill blocked."
    )
    return _gate("settled_no_fill_guard_locked", blocked, {"scenario": row["scenario_id"], "status": row["lifecycle_status"]})


def _no_action_reject_gate(report):
    rows = _scenarios_by_id(report)
    rejected = rows["rejected_raw_market"]
    no_action = rows["no_action_watchlist_or_reject"]
    passed = (
        rejected["paper_orders_submitted"] == 0
        and rejected["paper_orders_filled"] == 0
        and rejected["rejected_raw_markets"] == 1
        and no_action["paper_orders_submitted"] == 0
        and no_action["paper_orders_filled"] == 0
        and no_action["no_action_entries"] == 1
    )
    return _gate(
        "no_action_and_rejected_do_not_order",
        passed,
        {
            "rejected_raw_market_orders": rejected["paper_orders_submitted"],
            "no_action_orders": no_action["paper_orders_submitted"],
        },
    )


def _winning_fill_gate(report):
    rows = _scenarios_by_id(report)
    filled_win = rows["filled_win"]
    settled_position = rows["settled_position"]
    passed = (
        filled_win["paper_orders_filled"] == 1
        and filled_win["paper_pnl"] > 0
        and settled_position["paper_orders_filled"] == 1
        and settled_position["paper_pnl"] > 0
    )
    return _gate(
        "winning_scenarios_still_fill",
        passed,
        {
            "filled_win_pnl": filled_win["paper_pnl"],
            "settled_position_pnl": settled_position["paper_pnl"],
        },
    )


def _safety_gate(report):
    passed = _safety_locked(report) and _all_scenario_safety_locked(report)
    return _gate("safety_flags_locked", passed, {"top_level": _safety_locked(report), "scenarios": _all_scenario_safety_locked(report)})


def build_regression_gates(root: Path):
    replay = _load_module(root / "pm_bot" / "paper" / "run_crypto_numeric_lifecycle_replay.py", "pmbot_lifecycle_regression_replay")
    replay_report = replay.build_lifecycle_replay(root)
    gates = [
        _aggregate_gate(replay_report),
        _bad_entry_gate(replay_report),
        _settled_no_gate(replay_report),
        _no_action_reject_gate(replay_report),
        _winning_fill_gate(replay_report),
        _safety_gate(replay_report),
    ]
    failed = [gate for gate in gates if not gate["passed"]]
    summary = replay_report["replay_summary"]
    return {
        "schema_version": "v1",
        "report_id": "PMBOT-BRAIN-014-LIFECYCLE-REGRESSION-GATES",
        "source_report_id": replay_report["report_id"],
        "deterministic": True,
        **SAFETY_FLAGS,
        "status": "passed" if not failed else "failed",
        "gates_summary": {
            "gates_checked": len(gates),
            "gates_passed": len(gates) - len(failed),
            "gates_failed": len(failed),
            "safety_flags_locked": next(gate["passed"] for gate in gates if gate["gate_id"] == "safety_flags_locked"),
            "bad_entries_locked_zero": next(gate["passed"] for gate in gates if gate["gate_id"] == "bad_entries_locked_zero"),
            "settled_no_fill_guard_locked": next(gate["passed"] for gate in gates if gate["gate_id"] == "settled_no_fill_guard_locked"),
        },
        "locked_replay_summary": {
            "scenarios": summary["scenarios"],
            "filled_orders": summary["filled_orders"],
            "wins": summary["wins"],
            "losses": summary["losses"],
            "bad_entries": summary["bad_entries"],
            "rejected_bad_cases": summary["rejected_bad_cases"],
            "total_paper_pnl": summary["total_paper_pnl"],
        },
        "gates": gates,
        "limitations": [
            "Validates deterministic fixture replay output only; no live markets, prices, or APIs are fetched.",
            "Regression gates lock current offline paper lifecycle outcomes and safety flags.",
            "No runtime integration, prompt automation, credentials, wallet access, real orders, or live trading is included.",
        ],
        "review_note": "Lifecycle regression gates are offline checks for review and CI-style local validation only.",
    }


def render_markdown(report):
    summary = report["gates_summary"]
    replay = report["locked_replay_summary"]
    lines = [
        "# PMBOT Crypto Numeric Lifecycle Regression Gates",
        "",
        "Deterministic offline regression gates for crypto numeric paper lifecycle replay.",
        "",
        "## Gate Summary",
        "",
        f"- Status: {report['status']}",
        f"- Gates checked: {summary['gates_checked']}",
        f"- Gates passed: {summary['gates_passed']}",
        f"- Gates failed: {summary['gates_failed']}",
        f"- Safety flags locked: {str(summary['safety_flags_locked']).lower()}",
        f"- Bad entries locked zero: {str(summary['bad_entries_locked_zero']).lower()}",
        f"- Settled-no fill guard locked: {str(summary['settled_no_fill_guard_locked']).lower()}",
        "",
        "## Locked Replay Summary",
        "",
        f"- Scenarios: {replay['scenarios']}",
        f"- Filled orders: {replay['filled_orders']}",
        f"- Wins: {replay['wins']}",
        f"- Losses: {replay['losses']}",
        f"- Bad entries: {replay['bad_entries']}",
        f"- Rejected bad cases: {replay['rejected_bad_cases']}",
        f"- Total paper PnL: {replay['total_paper_pnl']:.2f}",
        "",
        "## Gates",
        "",
        "| gate_id | passed |",
        "| --- | --- |",
    ]
    for gate in report["gates"]:
        lines.append(f"| {gate['gate_id']} | {str(gate['passed']).lower()} |")
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    lines.extend(["", "- offline_only=true; paper_only=true; execution_allowed=false; trading_allowed=false; real_order_created=false; wallet_used=false; api_used=false; network_used=false", ""])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    report = build_regression_gates(root)
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
