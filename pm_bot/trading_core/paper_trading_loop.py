from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.paper_execution_risk import evaluate_paper_execution_risk
from pm_bot.trading_core.paper_mock_market_client import PaperMockMarketClient
from pm_bot.trading_core.paper_order_intent_builder import build_paper_order_intent
from pm_bot.trading_core.paper_strategy_engine import build_paper_strategy
from pm_bot.trading_core.paper_trading_loop_models import (
    REQUIRED_FALSE_FLAGS,
    LatestPaperTradingStatus,
    PaperLoopArtifact,
    build_no_signal_result,
    paper_trading_safety_flags,
    stable_id,
    validate_paper_loop_artifact,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/paper_trading_loop_053")
PMBOT_ARTIFACT_DIR_ENV = "PMBOT_ARTIFACT_DIR"


def resolve_paper_trading_loop_artifact_dir(artifact_dir: str | Path | None = None) -> Path:
    configured = clean_text(artifact_dir) or clean_text(os.environ.get(PMBOT_ARTIFACT_DIR_ENV))
    return Path(configured) if configured else DEFAULT_ARTIFACT_DIR


def paper_trading_loop_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = resolve_paper_trading_loop_artifact_dir(artifact_dir)
    return {
        "root": root,
        "result": root / "paper_trading_loop_053_result.json",
        "operator_md": root / "paper_trading_loop_053_operator.md",
        "latest_status": root / "latest_paper_trading_status_053.json",
        "market_snapshot": root / "paper_trading_market_snapshot_053.json",
        "strategy_signal": root / "paper_trading_strategy_signal_053.json",
        "risk": root / "paper_trading_risk_053.json",
        "order_intent": root / "paper_trading_order_intent_053.json",
        "no_signal": root / "paper_trading_no_signal_053.json",
    }


def run_paper_trading_loop(
    *,
    market: str = "BTC",
    strategy: str = "tiny-momentum",
    dry_run: bool = True,
    fixture: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    write_artifacts: bool = True,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("paper trading loop requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or "BTC"
    strategy_name = clean_text(strategy).lower() or "tiny-momentum"
    paths = paper_trading_loop_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    artifact_run_id = stable_id(
        "paper-trading-loop-053",
        {
            "market": market_symbol,
            "strategy": strategy_name,
            "artifact_dir": normalize_path(paths["root"]),
            "generated_at": generated_at,
        },
    )

    client = PaperMockMarketClient(fixture_path=fixture)
    snapshot = client.load_market_snapshot(
        market=market_symbol,
        artifact_run_id=artifact_run_id,
        generated_at=generated_at,
    )
    engine = build_paper_strategy(strategy_name)
    signal_model = engine.evaluate(snapshot, artifact_run_id=artifact_run_id, generated_at=generated_at)
    signal = signal_model.to_dict() if signal_model is not None else None
    no_signal = None
    if signal is None:
        no_signal = build_no_signal_result(
            artifact_run_id=artifact_run_id,
            strategy_name=engine.name,
            market_symbol=market_symbol,
            normalized_market_ref=clean_text(snapshot.get("normalized_market_ref")),
            reason=engine.no_signal_reason(snapshot),
            price_delta=float(snapshot.get("price_delta", 0) or 0),
            generated_at=generated_at,
        )

    risk = evaluate_paper_execution_risk(
        signal=signal,
        artifact_run_id=artifact_run_id,
        strategy_name=engine.name,
        market_symbol=market_symbol,
        dry_run=True,
        execution_mode="paper",
        live_execution_approved=False,
        authenticated_polymarket_enabled=False,
        wallet_signing_enabled=False,
        signing_enabled=False,
        order_submission_enabled=False,
        payload_generation_enabled=False,
        order_generation_enabled=False,
        generated_at=generated_at,
    )
    paper_intent = (
        build_paper_order_intent(
            signal=signal,
            risk=risk,
            artifact_run_id=artifact_run_id,
            generated_at=generated_at,
        )
        if signal is not None
        else None
    )

    result = PaperLoopArtifact(
        artifact_run_id=artifact_run_id,
        market_symbol=market_symbol,
        strategy_name=engine.name,
        loop_status=_loop_status(signal=signal, risk=risk, paper_intent=paper_intent),
        snapshot=snapshot,
        strategy_signal=signal,
        no_signal=no_signal,
        risk=risk,
        paper_order_intent=paper_intent,
        artifact_paths=path_refs,
        generated_at=generated_at,
    ).to_dict()
    status = summarize_paper_trading_loop_result(result, generated_at=generated_at)
    result["latest_status"] = status
    result["operator_ui_status_feed"] = status
    result["telegram_visible_summary"] = render_paper_trading_loop_telegram_status(status)
    result["validation"] = validate_paper_loop_artifact(result)
    if result["validation"].get("valid") is not True:
        raise ValueError("; ".join(result["validation"].get("errors", [])))

    if write_artifacts:
        _write_paper_trading_loop_artifacts(
            paths=paths,
            result=result,
            snapshot=snapshot,
            signal=signal,
            no_signal=no_signal,
            risk=risk,
            paper_intent=paper_intent,
            status=status,
        )
    return result


def summarize_paper_trading_loop_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    risk = dict(value.get("risk", {}))
    signal = dict(value.get("strategy_signal") or {})
    no_signal = dict(value.get("no_signal") or {})
    intent = dict(value.get("paper_order_intent") or {})
    paths = dict(value.get("artifact_paths", {}))
    paper_intent_status = clean_text(intent.get("paper_intent_status") or "no_paper_intent")
    paper_intent_summary = (
        f"{intent.get('outcome')} {intent.get('side')} at {intent.get('limit_price')} "
        f"size {intent.get('size')}"
        if intent
        else clean_text(no_signal.get("reason") or risk.get("operator_summary") or "no paper intent")
    )
    status = LatestPaperTradingStatus(
        artifact_run_id=clean_text(value.get("artifact_run_id")),
        market_symbol=clean_text(value.get("market_symbol")).upper(),
        strategy_name=clean_text(value.get("strategy_name")),
        status=clean_text(value.get("loop_status") or "not_available"),
        signal_status=clean_text(signal.get("signal_status") or no_signal.get("signal_status") or "not_available"),
        risk_decision=clean_text(risk.get("risk_decision") or "not_available"),
        paper_intent_status=paper_intent_status,
        paper_intent_summary=paper_intent_summary,
        artifact_path=clean_text(paths.get("result")),
        latest_status_path=clean_text(paths.get("latest_status")),
        operator_markdown_path=clean_text(paths.get("operator_md")),
        generated_at=generated_at,
    ).to_dict()
    return status


def render_paper_trading_loop_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    snapshot = dict(value.get("snapshot", {}))
    signal = dict(value.get("strategy_signal") or {})
    no_signal = dict(value.get("no_signal") or {})
    risk = dict(value.get("risk", {}))
    intent = dict(value.get("paper_order_intent") or {})
    paths = dict(value.get("artifact_paths", {}))
    safety = paper_trading_safety_flags()
    lines = [
        "# PMBOT Paper Trading Loop 053",
        "",
        f"- Status: `{value.get('loop_status')}`",
        f"- Market: `{value.get('market_symbol')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        "- Mode: `paper / review-only`",
        "- Live execution blocked: `true`",
        "- One-shot operator-triggered pass: `true`",
        "",
        "## Snapshot Summary",
        "",
        f"- Market ref: `{snapshot.get('normalized_market_ref')}`",
        f"- Slug: `{snapshot.get('market_slug')}`",
        f"- Primary outcome: `{snapshot.get('primary_outcome')}`",
        f"- Observed price: `{snapshot.get('observed_price')}`",
        f"- Previous observed price: `{snapshot.get('previous_observed_price')}`",
        f"- Price delta: `{snapshot.get('price_delta')}`",
        f"- Fixture source: `{snapshot.get('fixture_source')}`",
        "",
        "## Signal Summary",
        "",
    ]
    if signal:
        lines.extend(
            [
                f"- Signal status: `{signal.get('signal_status')}`",
                f"- Outcome: `{signal.get('outcome')}`",
                f"- Side: `{signal.get('side')}`",
                f"- Limit price: `{signal.get('limit_price')}`",
                f"- Size: `{signal.get('size')}`",
                f"- Notional: `{signal.get('notional')}`",
                f"- Confidence: `{signal.get('confidence')}`",
                f"- Reason: {clean_text(signal.get('reason'))}",
            ]
        )
    else:
        lines.extend(
            [
                "- Signal status: `no_signal`",
                f"- No-signal reason: {clean_text(no_signal.get('reason'))}",
            ]
        )
    lines.extend(
        [
            "",
            "## Risk Decision",
            "",
            f"- Risk decision: `{risk.get('risk_decision')}`",
            f"- Approved for paper intent: `{str(risk.get('approved_for_paper_intent') is True).lower()}`",
            "- Approved for live: `false`",
            "- Live execution blocked: `true`",
            f"- Operator summary: {clean_text(risk.get('operator_summary'))}",
            "",
            "## Paper Intent",
            "",
        ]
    )
    if intent:
        lines.extend(
            [
                f"- Paper intent status: `{intent.get('paper_intent_status')}`",
                f"- Paper intent ref: `{intent.get('paper_intent_ref')}`",
                "- Intent ref is execution identifier: `false`",
                f"- Outcome: `{intent.get('outcome')}`",
                f"- Side: `{intent.get('side')}`",
                f"- Limit price: `{intent.get('limit_price')}`",
                f"- Size: `{intent.get('size')}`",
                f"- Notional: `{intent.get('notional')}`",
                "- Intent is not order submission.",
            ]
        )
    else:
        lines.extend(
            [
                "- Paper intent status: `no_paper_intent`",
                f"- No-intent reason: {clean_text(risk.get('operator_summary') or no_signal.get('reason'))}",
            ]
        )
    lines.extend(
        [
            "",
            "## Safety Flags",
            "",
            *bullet_lines(f"{field}: `{str(value.get(field)).lower()}`" for field in REQUIRED_FALSE_FLAGS),
            f"- resolved_blocker_count: `{value.get('resolved_blocker_count')}`",
            f"- network_used: `{str(value.get('network_used')).lower()}`",
            f"- wallet_used: `{str(value.get('wallet_used')).lower()}`",
            f"- real_order_submitted: `{str(value.get('real_order_submitted')).lower()}`",
            "",
            "## Artifacts",
            "",
            *bullet_lines(f"{key}: `{path}`" for key, path in paths.items() if key != "root"),
            "",
            "## Next Operator Action",
            "",
            "- Review only, no live action available.",
            "- No execution identifier, wallet action, signing, authenticated call, or live order action is produced.",
        ]
    )
    for field, expected in safety.items():
        if field in value and value.get(field) != expected:
            lines.append(f"- Safety mismatch: `{field}` expected `{expected}`")
    return "\n".join(lines).rstrip() + "\n"


def render_paper_trading_loop_telegram_status(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Paper trading loop completed.",
            f"Market: {clean_text(value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name'))}",
            "Mode: paper / review-only",
            "Live execution: blocked",
            f"Risk decision: {clean_text(value.get('risk_decision'))}",
            f"Paper intent: {clean_text(value.get('paper_intent_status'))}",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def _write_paper_trading_loop_artifacts(
    *,
    paths: Mapping[str, Path],
    result: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    signal: Mapping[str, Any] | None,
    no_signal: Mapping[str, Any] | None,
    risk: Mapping[str, Any],
    paper_intent: Mapping[str, Any] | None,
    status: Mapping[str, Any],
) -> None:
    write_json(paths["market_snapshot"], snapshot)
    if signal is not None:
        write_json(paths["strategy_signal"], signal)
    if no_signal is not None:
        write_json(paths["no_signal"], no_signal)
    write_json(paths["risk"], risk)
    if paper_intent is not None:
        write_json(paths["order_intent"], paper_intent)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_paper_trading_loop_markdown(result))
    write_json(paths["latest_status"], status)


def _loop_status(
    *,
    signal: Mapping[str, Any] | None,
    risk: Mapping[str, Any],
    paper_intent: Mapping[str, Any] | None,
) -> str:
    if signal is None:
        return "paper_loop_completed_no_signal"
    if risk.get("approved_for_paper_intent") is not True:
        return "paper_loop_completed_risk_blocked"
    if paper_intent:
        return "paper_loop_completed_paper_intent_ready"
    return "paper_loop_completed_no_intent"
