from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.portfolio_state import run_portfolio_state
from pm_bot.trading_core.schemas import (
    ARTIFACT_DIR,
    GENERATED_AT,
    POST_EXECUTION_AUDIT_CONTRACT,
    POST_EXECUTION_AUDIT_RECORD_CONTRACT,
    assert_valid,
    bullet_lines,
    clean_text,
    load_json_object,
    mapping_rows,
    trading_core_safety_summary,
    validate_post_execution_audit_record,
    write_json,
    write_text,
)


def build_post_execution_audit(
    *,
    candidates_batch: Mapping[str, Any],
    risk_gate_batch: Mapping[str, Any],
    execution_batch: Mapping[str, Any],
    ledger: Mapping[str, Any],
    portfolio_state: Mapping[str, Any],
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    records = [
        _audit_record(
            "intent-risk-consistency",
            "Intent to risk gate consistency",
            _check_intent_risk_consistency(candidates_batch, risk_gate_batch),
        ),
        _audit_record(
            "risk-execution-consistency",
            "Risk gate to execution consistency",
            _check_risk_execution_consistency(risk_gate_batch, execution_batch),
        ),
        _audit_record(
            "execution-ledger-consistency",
            "Execution to ledger consistency",
            _check_execution_ledger_consistency(execution_batch, ledger),
        ),
        _audit_record(
            "portfolio-ledger-consistency",
            "Portfolio to ledger consistency",
            _check_portfolio_ledger_consistency(portfolio_state, ledger),
        ),
        _audit_record(
            "safety-flags",
            "Paper trading safety flags",
            _check_safety_flags(candidates_batch, risk_gate_batch, execution_batch, ledger, portfolio_state),
        ),
    ]
    violations = [
        detail
        for record in records
        if record["status"] == "failed"
        for detail in record.get("details", [])
    ]
    warnings = [
        detail
        for record in records
        if record["status"] == "warning"
        for detail in record.get("details", [])
    ]
    audit = {
        "contract_version": POST_EXECUTION_AUDIT_CONTRACT,
        "audit_id": "post-execution-audit-night-020-021",
        "generated_at": generated_at,
        "records": records,
        "violations": violations,
        "warnings": warnings,
        "audit_passed": not violations,
        "safety_flags": trading_core_safety_summary(),
    }
    return audit


def run_post_execution_audit(
    *,
    candidates_batch: Mapping[str, Any],
    risk_gate_batch: Mapping[str, Any],
    execution_batch: Mapping[str, Any],
    ledger: Mapping[str, Any],
    portfolio_state: Mapping[str, Any] | None = None,
    out_json_path: str | Path = ARTIFACT_DIR / "post_execution_audit.json",
    out_md_path: str | Path = ARTIFACT_DIR / "post_execution_audit.md",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    active_portfolio = dict(portfolio_state or run_portfolio_state(ledger=ledger, generated_at=generated_at))
    audit = build_post_execution_audit(
        candidates_batch=candidates_batch,
        risk_gate_batch=risk_gate_batch,
        execution_batch=execution_batch,
        ledger=ledger,
        portfolio_state=active_portfolio,
        generated_at=generated_at,
    )
    write_json(out_json_path, audit)
    write_text(out_md_path, render_post_execution_audit_markdown(audit))
    return audit


def render_post_execution_audit_markdown(audit: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Post-Execution Audit",
        "",
        f"- Audit passed: `{str(audit.get('audit_passed')).lower()}`",
        f"- Violations: {len(audit.get('violations', []))}",
        f"- Warnings: {len(audit.get('warnings', []))}",
        "",
        "## Checks",
        "",
    ]
    for record in mapping_rows(audit.get("records")):
        lines.extend(
            [
                f"### {record.get('check_name')}",
                "",
                f"- Status: `{record.get('status')}`",
                *bullet_lines(str(item) for item in record.get("details", [])),
                "",
            ]
        )
    lines.extend(
        [
            "## Safety flags",
            "",
            "- real_order_submitted: `false`",
            "- wallet_used: `false`",
            "- trading_endpoint_used: `false`",
            "- real_money_used: `false`",
            "- autonomous_trading_enabled: `false`",
        ]
    )
    return "\n".join(lines) + "\n"


def load_and_run_post_execution_audit(
    *,
    candidates_path: str | Path = ARTIFACT_DIR / "paper_trade_intent_candidates.json",
    risk_gate_path: str | Path = ARTIFACT_DIR / "risk_gate_results.json",
    executions_path: str | Path = ARTIFACT_DIR / "simulated_execution_results.json",
    ledger_path: str | Path = ARTIFACT_DIR / "paper_position_ledger.json",
    portfolio_path: str | Path = ARTIFACT_DIR / "paper_portfolio_state.json",
    out_json_path: str | Path = ARTIFACT_DIR / "post_execution_audit.json",
    out_md_path: str | Path = ARTIFACT_DIR / "post_execution_audit.md",
) -> dict[str, Any]:
    return run_post_execution_audit(
        candidates_batch=load_json_object(candidates_path, label="intent candidates"),
        risk_gate_batch=load_json_object(risk_gate_path, label="risk gate"),
        execution_batch=load_json_object(executions_path, label="executions"),
        ledger=load_json_object(ledger_path, label="ledger"),
        portfolio_state=load_json_object(portfolio_path, label="portfolio"),
        out_json_path=out_json_path,
        out_md_path=out_md_path,
    )


def _audit_record(check_id: str, name: str, result: tuple[str, list[str]]) -> dict[str, Any]:
    status, details = result
    record = {
        "contract_version": POST_EXECUTION_AUDIT_RECORD_CONTRACT,
        "check_id": check_id,
        "check_name": name,
        "status": status,
        "details": details,
    }
    valid, errors = validate_post_execution_audit_record(record)
    assert_valid(check_id, valid, errors)
    return record


def _check_intent_risk_consistency(
    candidates_batch: Mapping[str, Any],
    risk_gate_batch: Mapping[str, Any],
) -> tuple[str, list[str]]:
    candidates = {clean_text(row.get("intent_id")) for row in mapping_rows(candidates_batch.get("candidates"))}
    risk_results = {clean_text(row.get("intent_id")) for row in mapping_rows(risk_gate_batch.get("results"))}
    missing = sorted(candidates - risk_results)
    extra = sorted(risk_results - candidates)
    if missing or extra:
        return "failed", [f"missing risk results: {missing}", f"extra risk results: {extra}"]
    return "passed", [f"risk result exists for all {len(candidates)} intent candidates"]


def _check_risk_execution_consistency(
    risk_gate_batch: Mapping[str, Any],
    execution_batch: Mapping[str, Any],
) -> tuple[str, list[str]]:
    risk_by_intent = {clean_text(row.get("intent_id")): row for row in mapping_rows(risk_gate_batch.get("results"))}
    issues = []
    for execution in mapping_rows(execution_batch.get("results")):
        risk = risk_by_intent.get(clean_text(execution.get("intent_id")))
        if not risk:
            issues.append(f"execution without risk result: {execution.get('intent_id')}")
            continue
        if risk.get("blocked") is True and execution.get("execution_status") != "rejected":
            issues.append(f"blocked intent was not rejected: {execution.get('intent_id')}")
        if risk.get("allowed") is True and execution.get("paper_action_type") == "simulated_entry":
            if execution.get("execution_status") != "immediate_fill":
                issues.append(f"allowed simulated_entry did not fill: {execution.get('intent_id')}")
    if issues:
        return "failed", issues
    return "passed", ["risk gate results align with execution statuses"]


def _check_execution_ledger_consistency(
    execution_batch: Mapping[str, Any],
    ledger: Mapping[str, Any],
) -> tuple[str, list[str]]:
    filled_executions = [row for row in mapping_rows(execution_batch.get("results")) if row.get("simulated_fill") is True]
    ledger_positions = mapping_rows(ledger.get("positions"))
    ledger_execution_ids = {clean_text(row.get("source_execution_id")) for row in ledger_positions}
    ledger_open_keys = {_open_position_key(row.get("market_id"), row.get("intent_id")) for row in ledger_positions}
    duplicate_prevented_open_keys = {
        _open_position_key(row.get("market_id"), row.get("intent_id"))
        for row in filled_executions
        if clean_text(row.get("idempotency_status")) == "already_open_position"
    }
    filled_execution_ids = {clean_text(row.get("execution_id")) for row in filled_executions}
    missing = []
    for execution in filled_executions:
        execution_id = clean_text(execution.get("execution_id"))
        if execution_id in ledger_execution_ids:
            continue
        open_key = _open_position_key(execution.get("market_id"), execution.get("intent_id"))
        if clean_text(execution.get("idempotency_status")) == "already_open_position" and open_key in ledger_open_keys:
            continue
        missing.append(execution_id)
    allowed_extra_ledger_ids = {
        clean_text(row.get("source_execution_id"))
        for row in ledger_positions
        if _open_position_key(row.get("market_id"), row.get("intent_id")) in duplicate_prevented_open_keys
    }
    extra = sorted(ledger_execution_ids - filled_execution_ids - allowed_extra_ledger_ids)
    if missing or extra:
        return "failed", [f"fills missing from ledger: {missing}", f"ledger extras: {extra}"]
    return "passed", [f"ledger has one position for each of {len(filled_execution_ids)} paper fills"]


def _check_portfolio_ledger_consistency(
    portfolio_state: Mapping[str, Any],
    ledger: Mapping[str, Any],
) -> tuple[str, list[str]]:
    ledger_exposure = round(float(ledger.get("total_paper_exposure_usd", 0) or 0), 2)
    portfolio_exposure = round(float(portfolio_state.get("total_paper_exposure_usd", 0) or 0), 2)
    if ledger_exposure != portfolio_exposure:
        return "failed", [f"ledger exposure {ledger_exposure} != portfolio exposure {portfolio_exposure}"]
    return "passed", [f"portfolio exposure matches ledger exposure: {portfolio_exposure}"]


def _check_safety_flags(*artifacts: Mapping[str, Any]) -> tuple[str, list[str]]:
    issues = []
    for artifact in artifacts:
        for path, key, value in _walk_flags(artifact):
            if key in {"real_order_allowed", "real_order_submitted", "wallet_required", "wallet_used"} and value is True:
                issues.append(f"{path}.{key} is true")
            if key in {"trading_endpoint_required", "trading_endpoint_used", "real_money_used"} and value is True:
                issues.append(f"{path}.{key} is true")
    if issues:
        return "failed", issues
    return "passed", ["all audited real-money and endpoint flags remain false"]


def _walk_flags(value: Any, path: str = "$") -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            rows.append((path, str(key), nested))
            rows.extend(_walk_flags(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            rows.extend(_walk_flags(nested, f"{path}[{index}]"))
    return rows


def _open_position_key(market_id: Any, intent_id: Any) -> str:
    return ":".join([clean_text(market_id), clean_text(intent_id)])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run PMBOT paper post-execution audit.")
    parser.add_argument("--candidates", default=str(ARTIFACT_DIR / "paper_trade_intent_candidates.json"))
    parser.add_argument("--risk-gate", default=str(ARTIFACT_DIR / "risk_gate_results.json"))
    parser.add_argument("--executions", default=str(ARTIFACT_DIR / "simulated_execution_results.json"))
    parser.add_argument("--ledger", default=str(ARTIFACT_DIR / "paper_position_ledger.json"))
    parser.add_argument("--portfolio", default=str(ARTIFACT_DIR / "paper_portfolio_state.json"))
    parser.add_argument("--out-json", default=str(ARTIFACT_DIR / "post_execution_audit.json"))
    parser.add_argument("--out-md", default=str(ARTIFACT_DIR / "post_execution_audit.md"))
    args = parser.parse_args(argv)
    load_and_run_post_execution_audit(
        candidates_path=args.candidates,
        risk_gate_path=args.risk_gate,
        executions_path=args.executions,
        ledger_path=args.ledger,
        portfolio_path=args.portfolio,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
