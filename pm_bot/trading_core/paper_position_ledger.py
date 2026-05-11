from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.execution_simulator import run_execution_simulator
from pm_bot.trading_core.schemas import (
    ARTIFACT_DIR,
    GENERATED_AT,
    PAPER_POSITION_LEDGER_CONTRACT,
    PAPER_POSITION_RECORD_CONTRACT,
    assert_valid,
    bullet_lines,
    clean_text,
    load_json_object,
    mapping_rows,
    trading_core_safety_summary,
    validate_paper_position_ledger,
    validate_paper_position_record,
    write_json,
    write_text,
)


def build_paper_position_ledger(
    *,
    execution_batch: Mapping[str, Any],
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    positions = []
    for result in mapping_rows(execution_batch.get("results")):
        if result.get("simulated_fill") is not True:
            continue
        record = {
            "contract_version": PAPER_POSITION_RECORD_CONTRACT,
            "position_id": f"paper-position-020-021-{clean_text(result.get('execution_id'))}",
            "opened_at": generated_at,
            "source_execution_id": clean_text(result.get("execution_id")),
            "intent_id": clean_text(result.get("intent_id")),
            "market_id": clean_text(result.get("market_id")),
            "market_title": clean_text(result.get("market_title")),
            "hypothesis_id": clean_text(result.get("hypothesis_id")),
            "side_label": "track_yes",
            "side_label_meaning": "paper tracking label only; not a real market side or recommendation",
            "notional_usd": float(result.get("filled_notional_usd", 0) or 0),
            "max_loss_usd": float(result.get("filled_notional_usd", 0) or 0),
            "paper_fill_price_usd": result.get("paper_fill_price_usd"),
            "paper_units": float(result.get("paper_units", 0) or 0),
            "paper_exposure_usd": float(result.get("filled_notional_usd", 0) or 0),
            "outcome_status": "unresolved",
            "realized_pnl_usd": None,
            "unrealized_pnl_usd": None,
            "pnl_note": "No real PnL is computed because there is no local resolved outcome and no live price.",
            "paper_only": True,
            "real_position": False,
            "live_price_used": False,
        }
        valid, errors = validate_paper_position_record(record)
        assert_valid(record["position_id"], valid, errors)
        positions.append(record)

    total_exposure = round(sum(float(row.get("paper_exposure_usd", 0) or 0) for row in positions), 2)
    ledger = {
        "contract_version": PAPER_POSITION_LEDGER_CONTRACT,
        "ledger_id": "paper-position-ledger-night-020-021",
        "generated_at": generated_at,
        "positions": positions,
        "open_position_count": len(positions),
        "unresolved_position_count": len([row for row in positions if row["outcome_status"] == "unresolved"]),
        "total_paper_exposure_usd": total_exposure,
        "paper_only": True,
        "real_positions_created": False,
        "live_prices_used": False,
        "safety_summary": trading_core_safety_summary(),
    }
    valid, errors = validate_paper_position_ledger(ledger)
    assert_valid(ledger["ledger_id"], valid, errors)
    return ledger


def run_paper_position_ledger(
    *,
    execution_batch: Mapping[str, Any] | None = None,
    out_json_path: str | Path = ARTIFACT_DIR / "paper_position_ledger.json",
    out_md_path: str | Path = ARTIFACT_DIR / "paper_position_ledger.md",
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    batch = dict(execution_batch or run_execution_simulator(generated_at=generated_at))
    ledger = build_paper_position_ledger(execution_batch=batch, generated_at=generated_at)
    write_json(out_json_path, ledger)
    write_text(out_md_path, render_paper_position_ledger_markdown(ledger))
    return ledger


def render_paper_position_ledger_markdown(ledger: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Paper Position Ledger",
        "",
        f"- Open paper positions: {ledger.get('open_position_count')}",
        f"- Total paper exposure: `${ledger.get('total_paper_exposure_usd')}`",
        "- Outcome status stays unresolved until local outcome evidence exists.",
        "",
        "## Positions",
        "",
    ]
    for position in mapping_rows(ledger.get("positions")):
        lines.extend(
            [
                f"### `{position.get('market_id')}`",
                "",
                f"- Position: `{position.get('position_id')}`",
                f"- Title: {position.get('market_title')}",
                f"- Paper exposure: `${position.get('paper_exposure_usd')}`",
                f"- Paper units: `{position.get('paper_units')}`",
                f"- Outcome: `{position.get('outcome_status')}`",
                f"- PnL: {position.get('pnl_note')}",
                "",
            ]
        )
    lines.extend(
        [
            "## Safety",
            "",
            *bullet_lines(
                [
                    "Positions are paper-only records",
                    "No real positions were created",
                    "No live prices were used",
                    "No realized PnL is computed without local resolved outcomes",
                ]
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def load_and_run_paper_position_ledger(
    *,
    execution_path: str | Path = ARTIFACT_DIR / "simulated_execution_results.json",
    out_json_path: str | Path = ARTIFACT_DIR / "paper_position_ledger.json",
    out_md_path: str | Path = ARTIFACT_DIR / "paper_position_ledger.md",
) -> dict[str, Any]:
    execution_batch = load_json_object(execution_path, label="simulated execution results")
    return run_paper_position_ledger(
        execution_batch=execution_batch,
        out_json_path=out_json_path,
        out_md_path=out_md_path,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build PMBOT paper position ledger from simulated fills.")
    parser.add_argument("--executions", default=str(ARTIFACT_DIR / "simulated_execution_results.json"))
    parser.add_argument("--out-json", default=str(ARTIFACT_DIR / "paper_position_ledger.json"))
    parser.add_argument("--out-md", default=str(ARTIFACT_DIR / "paper_position_ledger.md"))
    args = parser.parse_args(argv)
    load_and_run_paper_position_ledger(
        execution_path=args.executions,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
