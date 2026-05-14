from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from pm_bot.trading_core.authenticated_polymarket_connector import (
    build_authenticated_connector_capability_report,
    summarize_authenticated_connector_capability_report,
)
from pm_bot.trading_core.btc_market_analysis_order_intent import (
    evaluate_btc_analysis_to_order_intent,
    summarize_btc_analysis_order_intent,
)
from pm_bot.trading_core.live_canary_readiness_evidence_bundle import (
    build_live_canary_readiness_evidence_bundle,
    summarize_live_canary_readiness_evidence_bundle,
)
from pm_bot.trading_core.live_canary_replay_acceptance import build_live_connector_blocker_matrix
from pm_bot.trading_core.live_credentials_auth_boundary import (
    evaluate_live_auth_boundary_for_tiny_canary,
    summarize_live_credentials_status,
)
from pm_bot.trading_core.live_enablement_config import (
    build_live_enablement_config_preflight,
    summarize_live_enablement_config_preflight,
)
from pm_bot.trading_core.live_order_submission_boundary import (
    build_live_order_submission_boundary_receipt,
    summarize_live_order_submission_boundary_receipt,
)
from pm_bot.trading_core.polymarket_btc_read_only_connector import (
    PolymarketBTCReadOnlyConnector,
    build_default_btc_read_only_config,
    summarize_btc_market_snapshot,
)
from pm_bot.trading_core.polymarket_public_market_data import load_polymarket_public_market_snapshot
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text
from pm_bot.trading_core.secret_boundary_policy import validate_secret_boundary_result_artifact
from pm_bot.trading_core.supervised_tiny_canary_runbook import (
    build_supervised_tiny_canary_approval_packet,
    render_supervised_tiny_canary_approval_packet_markdown,
    summarize_supervised_tiny_canary_approval_packet,
)
from pm_bot.trading_core.tiny_live_canary_gonogo_gate import (
    build_tiny_live_canary_gonogo_gate,
    summarize_tiny_live_canary_gonogo_gate,
)
from pm_bot.trading_core.wallet_signing_boundary import (
    build_wallet_signing_boundary_report,
    summarize_wallet_signing_boundary_report,
)

PAPER_CANARY_DRILL_RESULT_CONTRACT = "pmbot_polymarket_agents_adapted_paper_canary_drill_result.v1"
PAPER_CANARY_DRILL_STATUS_CONTRACT = "pmbot_polymarket_agents_adapted_paper_canary_drill_status.v1"
PAPER_CANARY_DRILL_VALIDATION_CONTRACT = "pmbot_polymarket_agents_adapted_paper_canary_drill_validation.v1"

TASK_ID = "ORCH-PMBOT-TRADING-MVP-052-POLYMARKET-AGENTS-ADAPTED-END-TO-END-PAPER-CANARY-DRILL"
DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/paper_canary_drill_052")
PMBOT_ARTIFACT_DIR_ENV = "PMBOT_ARTIFACT_DIR"

REQUIRED_FALSE_FLAGS = (
    "live_execution_approved",
    "canary_executable_now",
    "real_execution_available",
    "order_submission_enabled",
    "wallet_signing_enabled",
    "signing_enabled",
    "signed_payload_generation_enabled",
    "signed_order_generation_enabled",
    "authenticated_polymarket_enabled",
    "live_connector_enabled",
    "allowed_for_live",
)

FORBIDDEN_ARTIFACT_KEYS = frozenset(
    {
        "signed_payload",
        "signed_order",
        "signature",
        "raw_transaction",
        "order_id",
        "order_ids",
        "tx_hash",
        "transaction_hash",
        "fill",
        "fills",
        "fill_id",
        "balance",
        "balances",
        "private_key",
        "mnemonic",
        "seed_phrase",
        "api_key",
        "access_token",
        "bearer_token",
        "telegram_bot_token",
        "raw_telegram_bot_token",
    }
)


def resolve_paper_canary_artifact_dir(artifact_dir: str | Path | None = None) -> Path:
    configured = clean_text(artifact_dir) or clean_text(os.environ.get(PMBOT_ARTIFACT_DIR_ENV))
    return Path(configured) if configured else DEFAULT_ARTIFACT_DIR


def paper_canary_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = resolve_paper_canary_artifact_dir(artifact_dir)
    return {
        "root": root,
        "normalized_market": root / "paper_canary_normalized_market_052.json",
        "market_snapshot": root / "paper_canary_market_snapshot_052.json",
        "order_intent": root / "paper_canary_order_intent_052.json",
        "risk_readiness": root / "paper_canary_risk_readiness_052.json",
        "gonogo": root / "paper_canary_gonogo_052.json",
        "approval_packet": root / "paper_canary_supervised_approval_packet_052.json",
        "approval_packet_md": root / "paper_canary_supervised_approval_packet_052.md",
        "result": root / "paper_canary_drill_052_result.json",
        "operator_md": root / "paper_canary_drill_052_operator.md",
        "latest_status": root / "latest_paper_canary_status_052.json",
        "latest_status_md": root / "latest_paper_canary_status_052.md",
    }


def run_paper_canary_drill(
    *,
    market: str = "BTC",
    dry_run: bool = True,
    artifact_dir: str | Path | None = None,
    network_check: bool = False,
    write_artifacts: bool = True,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("paper canary drill requires --dry-run; live execution is not available")

    paths = paper_canary_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    public_snapshot = load_polymarket_public_market_snapshot(
        market=market,
        network_check=network_check,
        fetched_at=generated_at,
        generated_at=generated_at,
    )
    normalized_market = dict(public_snapshot["normalized_market"])
    normalized_market_summary = dict(public_snapshot["normalized_market_summary"])
    btc_payload = dict(public_snapshot["btc_connector_fixture_payload"])

    btc_config = build_default_btc_read_only_config(
        config_id="paper-canary-drill-052-btc-read-only-config",
        market_id=normalized_market["market_id"],
        market_slug=normalized_market["slug"],
        network_enabled=False,
        generated_at=generated_at,
    )
    btc_connector_result = PolymarketBTCReadOnlyConnector(btc_config).build_snapshot_from_fixture_payload(
        btc_payload,
        current_time=generated_at,
    )
    if btc_connector_result.get("success") is not True:
        raise ValueError(f"BTC fixture connector failed: {btc_connector_result.get('status')}")
    btc_market_snapshot = dict(btc_connector_result["snapshot"])
    btc_market_summary = summarize_btc_market_snapshot(btc_market_snapshot)
    btc_market_summary["latest_btc_market_snapshot_path"] = path_refs["market_snapshot"]

    live_auth_decision = evaluate_live_auth_boundary_for_tiny_canary(generated_at=generated_at)
    live_auth_summary = summarize_live_credentials_status(live_auth_decision, generated_at=generated_at)
    btc_order_intent_result = evaluate_btc_analysis_to_order_intent(
        btc_market_snapshot,
        readiness_evidence_reference=path_refs["risk_readiness"],
        audit_replay_reference="paper_canary_drill_052:fixture_replay_compatible",
        ui_panel_reference=path_refs["latest_status"],
        latest_btc_analysis_path=path_refs["risk_readiness"],
        latest_btc_order_intent_path=path_refs["order_intent"],
        latest_btc_risk_decision_path=path_refs["risk_readiness"],
        live_auth_boundary_decision=live_auth_decision,
        generated_at=generated_at,
    )
    btc_intent_summary = summarize_btc_analysis_order_intent(
        btc_order_intent_result,
        latest_btc_analysis_path=path_refs["risk_readiness"],
        latest_btc_order_intent_path=path_refs["order_intent"],
        latest_btc_risk_decision_path=path_refs["risk_readiness"],
        generated_at=generated_at,
    )
    order_intent = dict(dict(btc_order_intent_result.get("order_intent_plan", {})).get("order_intent") or {})
    paper_order_intent = _paper_order_intent_review(order_intent, btc_intent_summary, generated_at=generated_at)

    blocker_matrix = build_live_connector_blocker_matrix(generated_at=generated_at)
    live_order_boundary = build_live_order_submission_boundary_receipt(
        btc_dry_run_order_intent=btc_order_intent_result,
        risk_decision=btc_order_intent_result.get("risk_decision", {}),
        risk_decision_summary=btc_order_intent_result.get("risk_decision_summary", {}),
        risk_control_plane_summary=btc_order_intent_result.get("risk_control_plane_summary", {}),
        live_credentials_auth_boundary=live_auth_decision,
        live_credentials_auth_boundary_summary=live_auth_summary,
        blocker_matrix=blocker_matrix,
        generated_at=generated_at,
    )
    live_order_boundary_summary = summarize_live_order_submission_boundary_receipt(
        live_order_boundary,
        latest_live_order_submission_boundary_path=path_refs["risk_readiness"],
        generated_at=generated_at,
    )

    live_enablement = build_live_enablement_config_preflight(generated_at=generated_at)
    live_enablement_summary = summarize_live_enablement_config_preflight(
        live_enablement,
        latest_live_enablement_config_preflight_path=path_refs["risk_readiness"],
        generated_at=generated_at,
    )
    authenticated_connector = build_authenticated_connector_capability_report(generated_at=generated_at)
    authenticated_connector_summary = summarize_authenticated_connector_capability_report(
        authenticated_connector,
        latest_authenticated_polymarket_connector_scaffold_path=path_refs["risk_readiness"],
        generated_at=generated_at,
    )
    wallet_boundary = build_wallet_signing_boundary_report(generated_at=generated_at)
    wallet_boundary_summary = summarize_wallet_signing_boundary_report(
        wallet_boundary,
        latest_wallet_signing_boundary_path=path_refs["risk_readiness"],
        generated_at=generated_at,
    )

    provisional_gonogo = build_tiny_live_canary_gonogo_gate(
        market_id=btc_market_summary["market_id"],
        market_slug=btc_market_summary["market_slug"],
        btc_market_snapshot_summary=btc_market_summary,
        btc_analysis_summary=btc_intent_summary,
        dry_run_order_intent_summary=btc_intent_summary,
        risk_limit_summary=btc_order_intent_result.get("risk_control_plane_summary", {}),
        auth_boundary_summary=live_auth_summary,
        order_submission_boundary_summary=live_order_boundary_summary,
        readiness_evidence_summary={},
        live_enablement_config_preflight_summary=live_enablement_summary,
        authenticated_polymarket_connector_scaffold_summary=authenticated_connector_summary,
        kill_switch_summary={},
        blocker_matrix=blocker_matrix,
        latest_tiny_live_canary_gonogo_gate_path=path_refs["gonogo"],
        generated_at=generated_at,
    )
    provisional_gonogo_summary = summarize_tiny_live_canary_gonogo_gate(
        provisional_gonogo,
        latest_tiny_live_canary_gonogo_gate_path=path_refs["gonogo"],
        generated_at=generated_at,
    )

    readiness_bundle = build_live_canary_readiness_evidence_bundle(
        live_credentials_auth_boundary=live_auth_summary,
        blocker_matrix=blocker_matrix,
        risk_limit_control_plane=btc_order_intent_result.get("risk_control_plane_summary", {}),
        btc_read_only_market_connector=btc_market_summary,
        btc_analysis_order_intent_dry_run=btc_intent_summary,
        live_order_submission_boundary_dry_run_adapter=live_order_boundary_summary,
        tiny_live_canary_gonogo_gate=provisional_gonogo_summary,
        live_enablement_config_preflight=live_enablement,
        live_enablement_config_preflight_summary=live_enablement_summary,
        authenticated_polymarket_connector_scaffold=authenticated_connector,
        authenticated_polymarket_connector_scaffold_summary=authenticated_connector_summary,
        wallet_signing_boundary_report=wallet_boundary,
        wallet_signing_boundary_summary=wallet_boundary_summary,
        result_artifact_references=[path_refs["result"]],
        artifact_reference_overrides={
            "btc_read_only_market_connector": path_refs["market_snapshot"],
            "btc_market_analysis_to_order_intent_dry_run": path_refs["order_intent"],
            "live_order_submission_boundary_dry_run_adapter": path_refs["risk_readiness"],
            "tiny_live_canary_manual_execution_checklist_and_final_gonogo_gate": path_refs["gonogo"],
            "readiness_evidence_bundle": path_refs["risk_readiness"],
        },
        generated_at=generated_at,
    )
    readiness_summary = summarize_live_canary_readiness_evidence_bundle(
        readiness_bundle,
        latest_readiness_evidence_bundle_path=path_refs["risk_readiness"],
        generated_at=generated_at,
    )

    gonogo = build_tiny_live_canary_gonogo_gate(
        market_id=btc_market_summary["market_id"],
        market_slug=btc_market_summary["market_slug"],
        btc_market_snapshot_summary=btc_market_summary,
        btc_analysis_summary=btc_intent_summary,
        dry_run_order_intent_summary=btc_intent_summary,
        risk_limit_summary=btc_order_intent_result.get("risk_control_plane_summary", {}),
        auth_boundary_summary=live_auth_summary,
        order_submission_boundary_summary=live_order_boundary_summary,
        readiness_evidence_summary=readiness_summary,
        live_enablement_config_preflight_summary=live_enablement_summary,
        authenticated_polymarket_connector_scaffold_summary=authenticated_connector_summary,
        kill_switch_summary={},
        blocker_matrix=blocker_matrix,
        latest_tiny_live_canary_gonogo_gate_path=path_refs["gonogo"],
        generated_at=generated_at,
    )
    gonogo_summary = summarize_tiny_live_canary_gonogo_gate(
        gonogo,
        latest_tiny_live_canary_gonogo_gate_path=path_refs["gonogo"],
        generated_at=generated_at,
    )
    approval_packet = build_supervised_tiny_canary_approval_packet(
        live_enablement_config_preflight=live_enablement,
        live_enablement_config_preflight_summary=live_enablement_summary,
        authenticated_polymarket_connector_scaffold=authenticated_connector,
        authenticated_polymarket_connector_scaffold_summary=authenticated_connector_summary,
        wallet_signing_boundary_report=wallet_boundary,
        wallet_signing_boundary_summary=wallet_boundary_summary,
        risk_cap_readiness_summary=btc_order_intent_result.get("risk_control_plane_summary", {}),
        tiny_live_canary_gonogo_gate=gonogo,
        tiny_live_canary_gonogo_gate_summary=gonogo_summary,
        readiness_evidence_bundle=readiness_bundle,
        readiness_evidence_bundle_summary=readiness_summary,
        canary_replay_acceptance={
            "contract_version": "pmbot_paper_canary_fixture_replay_acceptance.v1",
            "status": "fixture_replay_compatible",
            "review_only": True,
            "execution_enabling": False,
            "live_execution_approved": False,
            "canary_executable_now": False,
        },
        blocker_matrix=blocker_matrix,
        artifact_paths={
            "live_enablement_config_preflight": path_refs["risk_readiness"],
            "authenticated_polymarket_connector_scaffold": path_refs["risk_readiness"],
            "wallet_signing_boundary": path_refs["risk_readiness"],
            "btc_risk_decision": path_refs["risk_readiness"],
            "tiny_live_canary_gonogo_gate": path_refs["gonogo"],
            "readiness_evidence_bundle": path_refs["risk_readiness"],
            "live_connector_blocker_matrix": "paper_canary_drill_052:blockers_generated",
            "supervised_tiny_canary_approval_packet": path_refs["approval_packet"],
            "supervised_tiny_canary_approval_packet_md": path_refs["approval_packet_md"],
            "operator_ui_panel_json": path_refs["latest_status"],
        },
        generated_at=generated_at,
    )
    approval_summary = summarize_supervised_tiny_canary_approval_packet(
        approval_packet,
        latest_supervised_tiny_canary_approval_packet_json_path=path_refs["approval_packet"],
        latest_supervised_tiny_canary_approval_packet_md_path=path_refs["approval_packet_md"],
        generated_at=generated_at,
    )

    result = {
        "contract_version": PAPER_CANARY_DRILL_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "drill_id": _stable_id(
            "paper-canary-drill-052",
            {
                "market_id": normalized_market.get("market_id"),
                "generated_at": generated_at,
                "artifact_dir": normalize_path(paths["root"]),
            },
        ),
        "generated_at": generated_at,
        "market": clean_text(market).upper(),
        "market_label": f"{clean_text(market).upper()} fixture",
        "status": "paper_canary_drill_completed",
        "execution_mode": "paper",
        "review_only": True,
        "dry_run": True,
        "fixture_mode": True,
        "network_check_requested": network_check is True,
        "network_used": False,
        "market_snapshot": btc_market_snapshot,
        "normalized_market": normalized_market,
        "normalized_market_summary": normalized_market_summary,
        "simulated_context_summary": _simulated_context_summary(
            normalized_market_summary=normalized_market_summary,
            btc_market_summary=btc_market_summary,
            generated_at=generated_at,
        ),
        "simulated_paper_order_intent": paper_order_intent,
        "risk_readiness_summary": {
            "btc_analysis_order_intent_summary": btc_intent_summary,
            "risk_control_plane_summary": dict(btc_order_intent_result.get("risk_control_plane_summary", {})),
            "live_credentials_auth_boundary_summary": live_auth_summary,
            "live_order_submission_boundary_summary": live_order_boundary_summary,
            "live_enablement_config_preflight_summary": live_enablement_summary,
            "authenticated_polymarket_connector_scaffold_summary": authenticated_connector_summary,
            "wallet_signing_boundary_summary": wallet_boundary_summary,
        },
        "go_no_go_summary": gonogo_summary,
        "readiness_evidence_summary": readiness_summary,
        "supervised_operator_approval_packet_reference": {
            "json_path": path_refs["approval_packet"],
            "markdown_path": path_refs["approval_packet_md"],
            "packet_id": approval_packet.get("packet_id"),
            "status": approval_summary.get("status"),
            "review_only": True,
            "live_execution_approved": False,
        },
        "evidence_replay_compatible_artifact": {
            "status": "fixture_replay_compatible",
            "result_path": path_refs["result"],
            "market_snapshot_path": path_refs["market_snapshot"],
            "risk_readiness_path": path_refs["risk_readiness"],
            "gonogo_path": path_refs["gonogo"],
            "approval_packet_path": path_refs["approval_packet"],
            "replay_is_not_execution": True,
            "execution_enabling": False,
        },
        "artifact_paths": path_refs,
        "operator_ui_status_feed": {},
        "telegram_visible_summary": "",
        "validation": {},
        **_paper_canary_safety_flags(),
    }
    status = summarize_paper_canary_drill_result(result, generated_at=generated_at)
    result["operator_ui_status_feed"] = status
    result["telegram_visible_summary"] = render_paper_canary_telegram_status(status)
    result["validation"] = validate_paper_canary_drill_result(result, generated_at=generated_at)
    if result["validation"].get("valid") is not True:
        raise ValueError("; ".join(result["validation"].get("errors", [])))

    if write_artifacts:
        _write_paper_canary_artifacts(
            paths=paths,
            result=result,
            normalized_market=normalized_market,
            btc_market_snapshot=btc_market_snapshot,
            order_intent=paper_order_intent,
            risk_readiness=result["risk_readiness_summary"],
            gonogo=gonogo,
            approval_packet=approval_packet,
            status=status,
        )
    return result


def summarize_paper_canary_drill_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result)
    paths = dict(value.get("artifact_paths", {}))
    gonogo = dict(value.get("go_no_go_summary", {}))
    intent = dict(value.get("simulated_paper_order_intent", {}))
    market = dict(value.get("normalized_market_summary", {}))
    return {
        "contract_version": PAPER_CANARY_DRILL_STATUS_CONTRACT,
        "status_id": _stable_id(
            "paper-canary-drill-status-052",
            {
                "drill_id": value.get("drill_id"),
                "status": value.get("status"),
                "result_path": paths.get("result"),
            },
        ),
        "task_id": TASK_ID,
        "drill_id": clean_text(value.get("drill_id")),
        "generated_at": generated_at,
        "status": clean_text(value.get("status") or "not_available"),
        "market": clean_text(value.get("market_label") or value.get("market")),
        "market_id": clean_text(market.get("market_id")),
        "market_slug": clean_text(market.get("slug")),
        "mode": "paper / review-only",
        "execution_mode": "paper",
        "review_only": True,
        "fixture_mode": True,
        "network_used": False,
        "live_execution": "blocked",
        "go_no_go_status": clean_text(gonogo.get("status") or "NO_GO_UNRESOLVED_BLOCKERS"),
        "overall_decision": clean_text(gonogo.get("overall_decision") or "NO_GO"),
        "paper_order_intent_status": clean_text(
            intent.get("paper_order_intent_status") or "paper_order_intent_review_ready"
        ),
        "artifact": clean_text(paths.get("result")),
        "latest_status_path": clean_text(paths.get("latest_status")),
        "operator_markdown_path": clean_text(paths.get("operator_md")),
        "approval_packet_path": clean_text(paths.get("approval_packet")),
        **_paper_canary_safety_flags(),
    }


def validate_paper_canary_drill_result(
    result: Mapping[str, Any],
    *,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    value = dict(result or {})
    errors: list[str] = []
    if value.get("contract_version") != PAPER_CANARY_DRILL_RESULT_CONTRACT:
        errors.append(f"contract_version must be {PAPER_CANARY_DRILL_RESULT_CONTRACT}")
    if value.get("execution_mode") != "paper":
        errors.append("execution_mode must be paper")
    if value.get("review_only") is not True:
        errors.append("review_only must be true")
    for field in REQUIRED_FALSE_FLAGS:
        if value.get(field) is not False:
            errors.append(f"{field} must be false")
    if value.get("resolved_blocker_count") != 0:
        errors.append("resolved_blocker_count must be 0")
    if value.get("network_used") is not False:
        errors.append("network_used must be false")
    forbidden_paths = _find_forbidden_key_paths(value)
    if forbidden_paths:
        errors.append("forbidden fake execution or secret fields present")
    secret_validation = validate_secret_boundary_result_artifact(value, generated_at=generated_at)
    if secret_validation.get("valid") is not True:
        errors.append("static secret boundary validation failed")
    valid = not errors
    return {
        "contract_version": PAPER_CANARY_DRILL_VALIDATION_CONTRACT,
        "validation_id": _stable_id(
            "paper-canary-drill-validation-052",
            {"drill_id": value.get("drill_id"), "errors": errors, "forbidden_paths": forbidden_paths},
        ),
        "generated_at": generated_at,
        "valid": valid,
        "status": "passed" if valid else "blocked",
        "errors": errors,
        "forbidden_artifact_key_paths": forbidden_paths,
        "secret_boundary_validation": secret_validation,
        **_paper_canary_safety_flags(),
    }


def render_paper_canary_drill_markdown(result: Mapping[str, Any]) -> str:
    status = dict(result.get("operator_ui_status_feed", {}))
    intent = dict(result.get("simulated_paper_order_intent", {}))
    risk = dict(result.get("risk_readiness_summary", {}))
    gonogo = dict(result.get("go_no_go_summary", {}))
    paths = dict(result.get("artifact_paths", {}))
    lines = [
        "# PMBOT Paper Canary Drill 052",
        "",
        f"- Status: `{result.get('status')}`",
        f"- Market: `{status.get('market')}`",
        "- Mode: `paper / review-only`",
        "- Live execution: `blocked`",
        "- Fixture mode: `true`",
        "- Network used: `false`",
        "- Review-only status feed: `" + clean_text(paths.get("latest_status")) + "`",
        "",
        "## Market Snapshot",
        "",
        f"- Market ID: `{status.get('market_id')}`",
        f"- Slug: `{status.get('market_slug')}`",
        f"- Source: `{dict(result.get('normalized_market_summary', {})).get('source')}`",
        "",
        "## Paper Intent",
        "",
        f"- Status: `{intent.get('paper_order_intent_status')}`",
        f"- Market: `{intent.get('market_id')}` / `{intent.get('market_slug')}`",
        f"- Notional USD: `{intent.get('notional_usd')}`",
        f"- Limit price: `{intent.get('limit_price')}`",
        "- This is not order submission.",
        "",
        "## Risk And Gates",
        "",
        f"- Risk decision: `{dict(risk.get('btc_analysis_order_intent_summary', {})).get('risk_decision_status')}`",
        f"- Go/no-go: `{gonogo.get('overall_decision')}`",
        f"- Go/no-go status: `{gonogo.get('status')}`",
        f"- Resolved blockers: `{result.get('resolved_blocker_count')}`",
        "",
        "## Required False Flags",
        "",
        *bullet_lines(f"{field}: `{str(result.get(field)).lower()}`" for field in REQUIRED_FALSE_FLAGS),
        "",
        "## Artifacts",
        "",
        *bullet_lines(f"{key}: `{value}`" for key, value in paths.items() if key != "root"),
        "",
        "## Safety",
        "",
        "- No wallet connection, signing, authenticated Polymarket call, or real order submission is available.",
        "- No order, transaction, fill, balance, or profit/loss execution result is generated.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_paper_canary_status_markdown(status: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Latest PMBOT Paper Canary Status",
            "",
            f"- Status: `{status.get('status')}`",
            f"- Market: `{status.get('market')}`",
            f"- Mode: `{status.get('mode')}`",
            f"- Live execution: `{status.get('live_execution')}`",
            f"- Overall decision: `{status.get('overall_decision')}`",
            f"- Artifact: `{status.get('artifact')}`",
        ]
    ) + "\n"


def render_paper_canary_telegram_status(status: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "Paper canary drill completed.",
            f"Market: {clean_text(status.get('market'))}",
            "Mode: paper / review-only",
            "Live execution: blocked",
            f"Artifact: {clean_text(status.get('artifact'))}",
        ]
    )


def _paper_order_intent_review(
    order_intent: Mapping[str, Any],
    intent_summary: Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    value = dict(order_intent or {})
    result = {
        "paper_intent_id": _stable_id(
            "paper-canary-order-intent-052",
            {
                "intent_id": value.get("intent_id"),
                "market_id": intent_summary.get("intent_market_id"),
                "generated_at": generated_at,
            },
        ),
        "paper_order_intent_status": "paper_order_intent_review_ready",
        "market_id": clean_text(value.get("market_id") or intent_summary.get("intent_market_id")),
        "market_slug": clean_text(value.get("market_slug") or intent_summary.get("intent_market_slug")),
        "side_label": clean_text(value.get("side_label") or "track_primary_outcome"),
        "notional_usd": value.get("notional_usd") or intent_summary.get("intent_notional_usd"),
        "quantity": value.get("quantity"),
        "limit_price": value.get("limit_price") or intent_summary.get("intent_limit_price"),
        "intent_source": "polymarket_agents_adapted_fixture_paper_canary_052",
        "created_at": generated_at,
        "paper_only": True,
        "review_only": True,
        "order_intent_is_not_order_submission": True,
        "analysis_is_not_live_recommendation": True,
        "executable_submission_payload_present": False,
        "fake_execution_artifacts_emitted": False,
    }
    result.update(_paper_canary_safety_flags())
    return result


def _simulated_context_summary(
    *,
    normalized_market_summary: Mapping[str, Any],
    btc_market_summary: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "contract_version": "pmbot_paper_canary_drill_simulated_context_summary.v1",
        "context_id": _stable_id(
            "paper-canary-context-052",
            {
                "market_id": normalized_market_summary.get("market_id"),
                "snapshot_id": btc_market_summary.get("snapshot_id"),
            },
        ),
        "generated_at": generated_at,
        "market_id": clean_text(normalized_market_summary.get("market_id")),
        "market_slug": clean_text(normalized_market_summary.get("slug")),
        "source": clean_text(normalized_market_summary.get("source")),
        "fixture_mode": normalized_market_summary.get("fixture_mode") is True,
        "paper_tradeable_filter_status": clean_text(
            normalized_market_summary.get("paper_tradeable_filter_status")
        ),
        "btc_market_connector_status": clean_text(btc_market_summary.get("btc_market_connector_status")),
        "risk_control_market_data_status": clean_text(btc_market_summary.get("risk_control_market_data_status")),
        "operator_note": (
            "Deterministic fixture context for PMBOT paper canary review; no market recommendation "
            "or live execution signal is produced."
        ),
        **_paper_canary_safety_flags(),
    }


def _write_paper_canary_artifacts(
    *,
    paths: Mapping[str, Path],
    result: Mapping[str, Any],
    normalized_market: Mapping[str, Any],
    btc_market_snapshot: Mapping[str, Any],
    order_intent: Mapping[str, Any],
    risk_readiness: Mapping[str, Any],
    gonogo: Mapping[str, Any],
    approval_packet: Mapping[str, Any],
    status: Mapping[str, Any],
) -> None:
    write_json(paths["normalized_market"], normalized_market)
    write_json(paths["market_snapshot"], btc_market_snapshot)
    write_json(paths["order_intent"], order_intent)
    write_json(paths["risk_readiness"], risk_readiness)
    write_json(paths["gonogo"], gonogo)
    write_json(paths["approval_packet"], approval_packet)
    write_text(paths["approval_packet_md"], render_supervised_tiny_canary_approval_packet_markdown(approval_packet))
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_paper_canary_drill_markdown(result))
    write_json(paths["latest_status"], status)
    write_text(paths["latest_status_md"], render_paper_canary_status_markdown(status))


def _find_forbidden_key_paths(value: Any, path: str = "$") -> list[str]:
    paths: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            next_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_ARTIFACT_KEYS:
                paths.append(next_path)
            paths.extend(_find_forbidden_key_paths(nested, next_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            paths.extend(_find_forbidden_key_paths(nested, f"{path}[{index}]"))
    return paths


def _paper_canary_safety_flags() -> dict[str, Any]:
    return {
        "execution_mode": "paper",
        "review_only": True,
        "live_execution_approved": False,
        "canary_executable_now": False,
        "real_execution_available": False,
        "order_submission_enabled": False,
        "wallet_signing_enabled": False,
        "signing_enabled": False,
        "signed_payload_generation_enabled": False,
        "signed_order_generation_enabled": False,
        "authenticated_polymarket_enabled": False,
        "live_connector_enabled": False,
        "allowed_for_live": False,
        "resolved_blocker_count": 0,
        "execution_enabling": False,
        "network_used": False,
        "external_api_calls_performed": False,
        "environment_inspected": False,
        "environment_secrets_read": False,
        "secrets_read": False,
        "secrets_printed": False,
        "secrets_persisted": False,
        "wallet_used": False,
        "wallet_signing_performed": False,
        "cryptographic_signing_performed": False,
        "authenticated_endpoint_call_performed": False,
        "real_order_submitted": False,
        "live_execution_allowed": False,
        "live_execution_performed": False,
        "fake_execution_artifacts_emitted": False,
        "browser_automation_added": False,
        "scheduler_or_daemon_added": False,
        "autonomous_live_trading_added": False,
        "outcome_resolution_invented": False,
        "price_data_invented": False,
        "pnl_invented": False,
    }


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:16]}"
