from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.first_supervised_tiny_order_readiness_models import (
    DEFAULT_MARKET,
    DEFAULT_STRATEGY,
    EXECUTION_MODE,
    FIRST_SUPERVISED_TINY_ORDER_READINESS_BLOCKERS_CONTRACT,
    FIRST_SUPERVISED_TINY_ORDER_READINESS_LATEST_STATUS_CONTRACT,
    FIRST_SUPERVISED_TINY_ORDER_READINESS_RESULT_CONTRACT,
    MODE,
    REQUIRED_FALSE_FLAGS,
    STATUS_BLOCKED_MISSING_EXPLICIT_LIVE_AUTHORIZATION,
    STATUS_BLOCKED_MISSING_LOCAL_REAL_CHECK_EVIDENCE,
    STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE,
    STATUS_BLOCKED_OPERATOR_STOP_REQUESTED,
    STATUS_BLOCKED_PAYLOAD_DRY_RUN_NOT_READY,
    STATUS_BLOCKED_RISK_ENGINE_REVIEW,
    STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK,
    STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN,
    STATUS_READY_FOR_SEPARATE_LIVE_AUTHORIZATION_PACKET,
    TASK_ID,
    FirstSupervisedTinyOrderReadinessSafetySnapshot,
    first_supervised_tiny_order_readiness_safety_flags,
    validate_first_supervised_tiny_order_readiness_result,
)
from pm_bot.trading_core.schemas import (
    GENERATED_AT,
    bullet_lines,
    clean_text,
    load_json_object,
    normalize_path,
    write_json,
    write_text,
)

DEFAULT_ARTIFACT_ROOT = Path("pm_bot/trading_core/artifacts")
DEFAULT_ARTIFACT_DIR = DEFAULT_ARTIFACT_ROOT / "first_supervised_tiny_order_readiness_077a"

SOURCE_CANDIDATES: dict[str, tuple[Path, ...]] = {
    "local_real_check_bundle_072c": (
        Path("local_real_check_bundle_072c/latest_local_real_check_bundle_status_072c.json"),
        Path("local_real_check_bundle_072c/local_real_check_bundle_072c_result.json"),
    ),
    "local_real_check_snapshot_073a": (
        Path("local_real_check_snapshot_073a/latest_local_real_check_snapshot_status_073a.json"),
        Path("local_real_check_snapshot_073a/local_real_check_snapshot_073a_result.json"),
    ),
    "real_local_check_evidence_review_074a": (
        Path("real_local_check_evidence_review_074a/latest_real_local_check_evidence_review_status_074a.json"),
        Path("real_local_check_evidence_review_074a/real_local_check_evidence_review_074a_result.json"),
    ),
    "operator_token_selection_packet_073b": (
        Path("operator_token_selection_packet_073b/latest_operator_token_selection_status_073b.json"),
        Path("operator_token_selection_packet_073b/operator_token_selection_packet_073b_result.json"),
        Path("operator_token_selection_packet_073b/operator_token_selection_packet_073b.json"),
    ),
    "selected_candidate_artifact_075d": (
        Path("selected_candidate_artifact_075d/latest_selected_candidate_artifact_075d.json"),
        Path("selected_candidate_artifact_075d/selected_candidate_artifact_075d.json"),
        Path("selected_candidate_artifact_075d/selected_candidate_artifact_075d_result.json"),
    ),
    "selected_token_verification_bridge_076a": (
        Path("selected_token_verification_bridge_076a/latest_selected_token_verification_076a_status.json"),
        Path("selected_token_verification_bridge_076a/selected_token_verification_076a_result.json"),
        Path("selected_token_verification_bridge_076a/selected_token_verification_076a_evidence.json"),
    ),
    "signer_diagnostic_evidence_bridge_076c": (
        Path("signer_diagnostic_evidence_bridge_076c/latest_signer_diagnostic_evidence_076c_status.json"),
        Path("signer_diagnostic_evidence_bridge_076c/signer_diagnostic_evidence_076c_result.json"),
    ),
    "selected_token_payload_readiness_gate_073c": (
        Path("selected_token_payload_readiness_gate_073c/latest_selected_token_payload_readiness_status_073c.json"),
        Path("selected_token_payload_readiness_gate_073c/selected_token_payload_readiness_gate_073c_result.json"),
    ),
    "payload_dry_run_readiness_076d": (
        Path("payload_dry_run_readiness_076d/latest_payload_dry_run_readiness_076d_status.json"),
        Path("payload_dry_run_readiness_076d/payload_dry_run_readiness_076d_result.json"),
    ),
    "signed_order_payload_dry_run_070a": (
        Path("signed_order_payload_dry_run_070a/latest_signed_order_payload_dry_run_status_070a.json"),
        Path("signed_order_payload_dry_run_070a/signed_order_payload_dry_run_070a_result.json"),
    ),
    "signed_payload_diagnostic_adapter_072e": (
        Path("signed_payload_diagnostic_adapter_072e/latest_signed_payload_diagnostic_adapter_status_072e.json"),
        Path("signed_payload_diagnostic_adapter_072e/signed_payload_diagnostic_adapter_072e_result.json"),
    ),
    "order_prep_packet_072a": (
        Path("order_prep_packet_072a/latest_order_prep_packet_status_072a.json"),
        Path("order_prep_packet_072a/order_prep_packet_072a_result.json"),
    ),
    "risk_engine_v2_074d": (
        Path("risk_engine_v2_074d/latest_risk_engine_v2_074d_status.json"),
        Path("risk_engine_v2_074d/risk_engine_v2_074d_result.json"),
    ),
    "first_live_order_final_blocker_reducer_072d": (
        Path("first_live_order_final_blocker_reducer_072d/latest_first_live_order_final_blockers_072d.json"),
        Path("first_live_order_final_blocker_reducer_072d/first_live_order_final_blocker_reducer_072d_result.json"),
    ),
    "static_safety_invariant_report_060q": (
        Path("static_safety_invariant_report_060q/latest_static_safety_invariant_report_status_060q.json"),
        Path("static_safety_invariant_report_060q/static_safety_invariant_report_060q_result.json"),
    ),
}

DEFAULT_TELEGRAM_LAUNCH_CONFIG_PATHS = (
    Path("pm_bot/operator_runner/artifacts/telegram_operator_control_state.json"),
    Path("pm_bot/trading_core/artifacts/telegram_operator_control_state/latest_telegram_operator_control_state.json"),
    Path("pm_bot/trading_core/artifacts/telegram_launch_config_076t/latest_telegram_launch_config_076t.json"),
)

DEFAULT_STOP_MARKER_PATHS = (
    Path("stop"),
    Path("halt"),
    Path("pm_bot/trading_core/artifacts/operator_stop_marker.json"),
    Path("pm_bot/trading_core/artifacts/operator_halt_marker.json"),
)

FORBIDDEN_RUNTIME_FLAGS = (
    "--live",
    "--live-execution",
    "--execute",
    "--trade",
    "--auth",
    "--authenticated",
    "--wallet",
    "--wallet-connect",
    "--sign",
    "--signing",
    "--submit",
    "--cancel",
    "--approve-live",
    "--record-approval",
    "--private-key",
    "--polymarket-private-key",
    "--seed",
    "--mnemonic",
    "--api-secret",
    "--auth-token",
    "--passphrase",
)

READY_SELECTED_TOKEN_STATUS = "selected_token_verified_for_payload_dry_run"
READY_SIGNER_STATUS = "signer_diagnostic_evidence_ok_for_payload_dry_run"
READY_PAYLOAD_STATUS = "payload_dry_run_ready_for_operator_review"
READY_SELECTED_PAYLOAD_STATUS = "ready_for_signed_payload_diagnostic"
READY_SIGNED_ADAPTER_STATUS = "unsigned_diagnostic_readiness_ready_no_signing"
READY_ORDER_PREP_STATUS = "order_prep_packet_ready_for_operator_review_non_executable"
READY_RISK_STATUS = "passed_review_check_no_live"
READY_FINAL_REDUCER_STATUS = "review_ready_no_live_authorization"
READY_STATIC_SAFETY_STATUSES = {"passed", "passed_with_warnings"}


def first_supervised_tiny_order_readiness_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "first_supervised_tiny_order_readiness_077a_result.json",
        "latest_status": root / "latest_first_supervised_tiny_order_readiness_077a_status.json",
        "blockers": root / "first_supervised_tiny_order_readiness_077a_blockers.json",
        "operator_md": root / "first_supervised_tiny_order_readiness_077a_operator_summary.md",
    }


def run_first_supervised_tiny_order_readiness_packet(
    *,
    market: str = DEFAULT_MARKET,
    strategy: str = DEFAULT_STRATEGY,
    dry_run: bool = True,
    artifact_root: str | Path | None = None,
    artifact_dir: str | Path | None = None,
    local_real_check_bundle_path: str | Path | None = None,
    local_real_check_snapshot_path: str | Path | None = None,
    real_local_check_evidence_review_path: str | Path | None = None,
    operator_token_selection_packet_path: str | Path | None = None,
    selected_candidate_artifact_path: str | Path | None = None,
    selected_token_verification_bridge_path: str | Path | None = None,
    signer_diagnostic_evidence_bridge_path: str | Path | None = None,
    selected_token_payload_readiness_gate_path: str | Path | None = None,
    payload_dry_run_readiness_path: str | Path | None = None,
    signed_order_payload_dry_run_path: str | Path | None = None,
    signed_payload_diagnostic_adapter_path: str | Path | None = None,
    order_prep_packet_path: str | Path | None = None,
    risk_engine_v2_path: str | Path | None = None,
    final_blocker_reducer_path: str | Path | None = None,
    static_safety_report_path: str | Path | None = None,
    telegram_launch_config_path: str | Path | None = None,
    stop_marker_path: str | Path | None = None,
    generated_at: str = GENERATED_AT,
    head_before: str = "",
    head_after: str = "",
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("first supervised tiny order readiness packet requires --dry-run; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_STRATEGY
    source_root = Path(artifact_root) if artifact_root else DEFAULT_ARTIFACT_ROOT
    paths = first_supervised_tiny_order_readiness_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    explicit_paths = {
        "local_real_check_bundle_072c": local_real_check_bundle_path,
        "local_real_check_snapshot_073a": local_real_check_snapshot_path,
        "real_local_check_evidence_review_074a": real_local_check_evidence_review_path,
        "operator_token_selection_packet_073b": operator_token_selection_packet_path,
        "selected_candidate_artifact_075d": selected_candidate_artifact_path,
        "selected_token_verification_bridge_076a": selected_token_verification_bridge_path,
        "signer_diagnostic_evidence_bridge_076c": signer_diagnostic_evidence_bridge_path,
        "selected_token_payload_readiness_gate_073c": selected_token_payload_readiness_gate_path,
        "payload_dry_run_readiness_076d": payload_dry_run_readiness_path,
        "signed_order_payload_dry_run_070a": signed_order_payload_dry_run_path,
        "signed_payload_diagnostic_adapter_072e": signed_payload_diagnostic_adapter_path,
        "order_prep_packet_072a": order_prep_packet_path,
        "risk_engine_v2_074d": risk_engine_v2_path,
        "first_live_order_final_blocker_reducer_072d": final_blocker_reducer_path,
        "static_safety_invariant_report_060q": static_safety_report_path,
    }
    source_artifacts = {
        source_id: _load_source_artifact(
            _select_source_path(source_root, SOURCE_CANDIDATES[source_id], explicit_paths.get(source_id)),
            source_id,
        )
        for source_id in SOURCE_CANDIDATES
    }
    telegram_launch_config = _summarize_telegram_launch_config(
        _load_source_artifact(
            _select_first_existing_path(
                explicit_path=telegram_launch_config_path,
                default_paths=DEFAULT_TELEGRAM_LAUNCH_CONFIG_PATHS,
            ),
            "telegram_launch_config",
        )
    )
    stop_marker = _summarize_stop_marker(
        _load_stop_marker(
            _select_first_existing_path(
                explicit_path=stop_marker_path,
                default_paths=DEFAULT_STOP_MARKER_PATHS,
            )
        )
    )
    operator_stop_requested = (
        telegram_launch_config.get("operator_stop_requested") is True
        or stop_marker.get("operator_stop_requested") is True
    )

    local_real_check = _summarize_local_real_check(source_artifacts)
    selected_candidate = _summarize_selected_candidate(
        source_artifacts["selected_candidate_artifact_075d"],
        market_symbol=market_symbol,
        strategy_name=strategy_name,
    )
    selected_token_verification = _summarize_selected_token_verification(
        source_artifacts["selected_token_verification_bridge_076a"],
        market_symbol=market_symbol,
        strategy_name=strategy_name,
    )
    signer_diagnostic = _summarize_signer_diagnostic(
        source_artifacts["signer_diagnostic_evidence_bridge_076c"]
    )
    payload_dry_run = _summarize_payload_dry_run(source_artifacts)
    risk_engine = _summarize_risk_engine(source_artifacts)
    component_statuses = {
        "local_real_check_evidence": local_real_check,
        "selected_candidate": selected_candidate,
        "selected_token_verification": selected_token_verification,
        "signer_diagnostic": signer_diagnostic,
        "payload_dry_run_readiness": payload_dry_run,
        "risk_engine": risk_engine,
        "telegram_launch_config": telegram_launch_config,
        "stop_marker": stop_marker,
    }
    blockers = _build_blockers(
        component_statuses=component_statuses,
        operator_stop_requested=operator_stop_requested,
        generated_at=generated_at,
    )
    status = blockers[0]["blocker_id"] if blockers else STATUS_READY_FOR_SEPARATE_LIVE_AUTHORIZATION_PACKET
    ready_for_authorization = status == STATUS_READY_FOR_SEPARATE_LIVE_AUTHORIZATION_PACKET
    current_top_blocker = (
        STATUS_BLOCKED_MISSING_EXPLICIT_LIVE_AUTHORIZATION
        if ready_for_authorization
        else clean_text(status)
    )
    execution_blockers = [
        _blocker(
            STATUS_BLOCKED_MISSING_EXPLICIT_LIVE_AUTHORIZATION,
            "explicit_live_authorization",
            "A separate future live authorization task is still required before any order execution.",
            generated_at=generated_at,
            blocks_authorization_packet=False,
        )
    ]
    next_command = _next_recommended_safe_command(status=status, market=market_symbol, strategy=strategy_name)
    future_live_task_can_be_considered = ready_for_authorization
    operator_summary = _operator_summary(
        status=status,
        ready_for_authorization=ready_for_authorization,
        current_top_blocker=current_top_blocker,
        next_command=next_command,
    )
    safety_snapshot = FirstSupervisedTinyOrderReadinessSafetySnapshot(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    blockers_artifact = _build_blockers_artifact(
        status=status,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        blockers=blockers,
        execution_blockers=execution_blockers,
        current_top_blocker=current_top_blocker,
        generated_at=generated_at,
    )
    latest_status = _build_latest_status(
        status=status,
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        component_statuses=component_statuses,
        blockers=blockers,
        execution_blockers=execution_blockers,
        ready_for_authorization=ready_for_authorization,
        current_top_blocker=current_top_blocker,
        telegram_launch_config=telegram_launch_config,
        operator_stop_requested=operator_stop_requested,
        future_live_task_can_be_considered=future_live_task_can_be_considered,
        next_command=next_command,
        operator_summary=operator_summary,
        artifact_paths=path_refs,
        generated_at=generated_at,
    )
    result: dict[str, Any] = {
        "contract_version": FIRST_SUPERVISED_TINY_ORDER_READINESS_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "dry_run": True,
        "question_answered": (
            "Are we ready to ask the operator for a separate explicit authorization to place "
            "the first supervised tiny post-only live order?"
        ),
        "answer": "yes_ready_to_ask_for_separate_authorization" if ready_for_authorization else "no_blocked",
        "first_supervised_tiny_order_ready_for_authorization": ready_for_authorization,
        "first_supervised_tiny_order_ready_for_execution": False,
        "explicit_live_authorization_present": False,
        "current_top_blocker": current_top_blocker,
        "future_separate_live_task_can_be_considered": future_live_task_can_be_considered,
        "next_recommended_safe_command": next_command,
        "next_recommended_safe_action": _next_recommended_safe_action(ready_for_authorization),
        "component_statuses": component_statuses,
        "source_artifacts": {
            source_id: _source_artifact_summary(row) for source_id, row in source_artifacts.items()
        },
        "telegram_launch_config": telegram_launch_config,
        "operator_stop_requested": operator_stop_requested,
        "stop_marker": stop_marker,
        "blockers": [dict(row) for row in blockers],
        "blocker_count": len(blockers),
        "execution_blockers": execution_blockers,
        "execution_blocker_count": len(execution_blockers),
        "resolved_blocker_count": 0,
        "safety_snapshot": safety_snapshot,
        "latest_status": latest_status,
        "blockers_artifact": blockers_artifact,
        "operator_summary": operator_summary,
        "artifact_paths": path_refs,
        "head_before": clean_text(head_before),
        "head_after": clean_text(head_after),
        "generated_at": generated_at,
        **first_supervised_tiny_order_readiness_safety_flags(),
    }
    result["first_supervised_tiny_order_ready_for_authorization"] = ready_for_authorization
    result["operator_stop_requested"] = operator_stop_requested
    result["validation"] = validate_first_supervised_tiny_order_readiness_result(result)

    write_json(paths["blockers"], blockers_artifact)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_first_supervised_tiny_order_readiness_markdown(result))
    return result


def render_first_supervised_tiny_order_readiness_cli_summary(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    return "\n".join(
        [
            "First supervised tiny order readiness packet 077A completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market_symbol') or value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy_name') or value.get('strategy'))}",
            f"selected candidate status: {clean_text(latest.get('selected_candidate_status'))}",
            f"selected token verified: {str(latest.get('selected_token_verified') is True).lower()}",
            f"signer diagnostic status: {clean_text(latest.get('signer_diagnostic_status'))}",
            f"payload dry-run readiness status: {clean_text(latest.get('payload_dry_run_readiness_status'))}",
            f"risk engine status: {clean_text(latest.get('risk_engine_status'))}",
            f"final blocker reducer status: {clean_text(latest.get('final_blocker_reducer_status'))}",
            f"operator stop requested: {str(latest.get('operator_stop_requested') is True).lower()}",
            "explicit live authorization present: false",
            f"ready for separate live authorization packet: {str(value.get('first_supervised_tiny_order_ready_for_authorization') is True).lower()}",
            "ready for execution: false",
            "allowed for live: false",
            "order submission enabled: false",
            "order cancel enabled: false",
            "signing by default: false",
            f"current top blocker: {clean_text(value.get('current_top_blocker'))}",
            f"next recommended safe command: {clean_text(value.get('next_recommended_safe_command'))}",
            f"Artifact: {clean_text(latest.get('artifact_path'))}",
        ]
    )


def render_first_supervised_tiny_order_readiness_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    paths = dict(value.get("artifact_paths", {}))
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    execution_blockers = [dict(row) for row in value.get("execution_blockers", []) if isinstance(row, Mapping)]
    passed = _passed_lines(latest)
    lines = [
        "# PMBOT First Supervised Tiny Order Readiness Packet 077A",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name') or value.get('strategy')}`",
        "- allowed_for_live: `false`",
        "- explicit_live_authorization_present: `false`",
        "- first_supervised_tiny_order_ready_for_execution: `false`",
        "- order submission, cancel, signing by default, wallet connection, and background trading remain disabled",
        "",
        "## What Passed",
        "",
        *bullet_lines(passed),
        "",
        "## What Blocks",
        "",
        *bullet_lines(f"`{row.get('blocker_id')}` - {row.get('reason')}" for row in blockers),
        *bullet_lines(
            f"`{row.get('blocker_id')}` - {row.get('reason')}" for row in execution_blockers
        ),
        "",
        "## Operator Context",
        "",
        f"- daily_limit: `{latest.get('daily_limit') or 'not present'}`",
        f"- max_loss: `{latest.get('max_loss') or 'not present'}`",
        f"- selected_markets: `{', '.join(latest.get('selected_markets') or []) or 'not present'}`",
        f"- operator_stop_requested: `{str(latest.get('operator_stop_requested') is True).lower()}`",
        "",
        "## Next Safe Command",
        "",
        f"`{value.get('next_recommended_safe_command')}`",
        "",
        "## Future Live Task",
        "",
        "A future separate live authorization task can be considered only when this packet reports "
        "`ready_for_separate_live_authorization_packet`. This packet itself cannot submit, cancel, sign by default, "
        "connect a wallet, or enable live execution.",
        "",
        "## Artifacts",
        "",
        *bullet_lines(f"`{path}`" for path in paths.values()),
        "",
        "## Required False Flags",
        "",
        *bullet_lines(f"`{field}=false`" for field in REQUIRED_FALSE_FLAGS),
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "077A readiness packet is no-live/no-submit/no-cancel/no-signing-by-default; "
            "rejects forbidden flag(s): "
            + ", ".join(requested)
        )


def _select_source_path(source_root: Path, candidates: Sequence[Path], explicit_path: str | Path | None) -> Path:
    if explicit_path:
        return Path(explicit_path)
    for candidate in candidates:
        path = source_root / candidate
        if path.exists():
            return path
    return source_root / candidates[0]


def _select_first_existing_path(
    *,
    explicit_path: str | Path | None,
    default_paths: Sequence[Path],
) -> Path:
    if explicit_path:
        return Path(explicit_path)
    for path in default_paths:
        if path.exists():
            return path
    return default_paths[0]


def _load_source_artifact(path: Path, label: str) -> dict[str, Any]:
    path_obj = Path(path)
    if not path_obj.exists():
        return {
            "source_id": clean_text(label),
            "available": False,
            "parsed": False,
            "path": normalize_path(path_obj),
            "status": "missing",
            "contract_version": "",
            "errors": ["artifact missing"],
        }
    try:
        payload = load_json_object(path_obj, label=label)
    except Exception as exc:  # pragma: no cover - defensive artifact loader
        return {
            "source_id": clean_text(label),
            "available": True,
            "parsed": False,
            "path": normalize_path(path_obj),
            "status": "unparseable",
            "contract_version": "",
            "errors": [clean_text(exc)],
        }
    return {
        "source_id": clean_text(label),
        "available": True,
        "parsed": True,
        "path": normalize_path(path_obj),
        "status": clean_text(payload.get("status")) or "present",
        "contract_version": clean_text(payload.get("contract_version")),
        "payload": payload,
        "errors": [],
    }


def _load_stop_marker(path: Path) -> dict[str, Any]:
    path_obj = Path(path)
    if not path_obj.exists():
        return {
            "source_id": "operator_stop_marker",
            "available": False,
            "parsed": False,
            "path": normalize_path(path_obj),
            "status": "missing",
            "errors": ["marker missing"],
        }
    try:
        payload = load_json_object(path_obj, label="operator stop marker")
    except Exception:
        text = path_obj.read_text(encoding="utf-8", errors="ignore")
        payload = {"status": "operator_stop_marker_present", "operator_stop_requested": bool(text.strip()) or True}
    return {
        "source_id": "operator_stop_marker",
        "available": True,
        "parsed": True,
        "path": normalize_path(path_obj),
        "status": clean_text(payload.get("status")) or "operator_stop_marker_present",
        "payload": payload,
        "errors": [],
    }


def _source_artifact_summary(source: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_id": clean_text(source.get("source_id")),
        "available": source.get("available") is True,
        "parsed": source.get("parsed") is True,
        "path": clean_text(source.get("path")),
        "status": clean_text(source.get("status")) or "missing",
        "contract_version": clean_text(source.get("contract_version")),
        "source_payload_embedded": False,
        "errors": [clean_text(item) for item in source.get("errors", [])],
    }


def _payload(source: Mapping[str, Any]) -> dict[str, Any]:
    payload = source.get("payload")
    return dict(payload) if isinstance(payload, Mapping) else {}


def _summarize_local_real_check(source_artifacts: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    keys = (
        "local_real_check_bundle_072c",
        "local_real_check_snapshot_073a",
        "real_local_check_evidence_review_074a",
    )
    sources = [source_artifacts[key] for key in keys]
    available = [source for source in sources if source.get("available") is True and source.get("parsed") is True]
    return {
        "ready": bool(available),
        "available": bool(available),
        "status": clean_text(available[-1].get("status")) if available else "missing",
        "bundle_status": clean_text(source_artifacts["local_real_check_bundle_072c"].get("status")),
        "snapshot_status": clean_text(source_artifacts["local_real_check_snapshot_073a"].get("status")),
        "evidence_review_status": clean_text(source_artifacts["real_local_check_evidence_review_074a"].get("status")),
        "available_source_count": len(available),
        "source_payloads_embedded": False,
    }


def _summarize_selected_candidate(
    source: Mapping[str, Any],
    *,
    market_symbol: str,
    strategy_name: str,
) -> dict[str, Any]:
    payload = _payload(source)
    status = clean_text(payload.get("status")) or clean_text(source.get("status")) or "missing"
    scope_matches = _scope_matches(payload, market_symbol=market_symbol, strategy_name=strategy_name)
    ready = (
        source.get("available") is True
        and source.get("parsed") is True
        and status == "selected_candidate_artifact_recorded"
        and (payload.get("selected_by_operator") is True or payload.get("selected_candidate_artifact_recorded") is True)
        and (payload.get("source_backed") is True or payload.get("selected_candidate_artifact_recorded") is True)
        and scope_matches
    )
    return {
        "ready": ready,
        "available": source.get("available") is True,
        "status": status,
        "selected_by_operator": payload.get("selected_by_operator") is True,
        "source_backed": payload.get("source_backed") is True,
        "scope_matches": scope_matches,
        "candidate_index_status": clean_text(payload.get("candidate_index_status")),
        "raw_token_included": False,
        "source_payload_embedded": False,
    }


def _summarize_selected_token_verification(
    source: Mapping[str, Any],
    *,
    market_symbol: str,
    strategy_name: str,
) -> dict[str, Any]:
    payload = _payload(source)
    status = clean_text(payload.get("status")) or clean_text(source.get("status")) or "missing"
    scope_matches = _scope_matches(payload, market_symbol=market_symbol, strategy_name=strategy_name)
    verified = (
        source.get("available") is True
        and source.get("parsed") is True
        and scope_matches
        and (
            payload.get("selected_token_verified_for_payload_dry_run") is True
            or status == READY_SELECTED_TOKEN_STATUS
        )
    )
    return {
        "verified": verified,
        "available": source.get("available") is True,
        "status": status,
        "scope_matches": scope_matches,
        "approves_live": False,
        "approves_submit": False,
        "source_payload_embedded": False,
    }


def _summarize_signer_diagnostic(source: Mapping[str, Any]) -> dict[str, Any]:
    payload = _payload(source)
    status = clean_text(payload.get("signer_diagnostic_evidence_status") or payload.get("status"))
    status = status or clean_text(source.get("status")) or "missing"
    diagnostic_status = clean_text(payload.get("source_diagnostic_status") or payload.get("diagnostic_status"))
    ok = (
        source.get("available") is True
        and source.get("parsed") is True
        and (
            payload.get("signer_diagnostic_evidence_ok_for_payload_dry_run") is True
            or payload.get("diagnostic_ok") is True
            or status == READY_SIGNER_STATUS
        )
        and _false_flags_ok(
            payload,
            (
                "allowed_for_live",
                "signer_ready_for_live",
                "order_submit_ready",
                "full_signed_payload_output",
                "signing_by_default",
                "order_submission_enabled",
                "order_cancellation_enabled",
            ),
        )
    )
    return {
        "diagnostic_ok": ok,
        "available": source.get("available") is True,
        "status": status,
        "source_diagnostic_status": diagnostic_status or "missing",
        "signer_ready_for_live": False,
        "order_submit_ready": False,
        "full_signed_payload_output": False,
        "signing_by_default": False,
        "source_payload_embedded": False,
    }


def _summarize_payload_dry_run(source_artifacts: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    readiness_source = source_artifacts["payload_dry_run_readiness_076d"]
    readiness_payload = _payload(readiness_source)
    readiness_status = clean_text(readiness_payload.get("status")) or clean_text(readiness_source.get("status"))
    selected_payload = _payload(source_artifacts["selected_token_payload_readiness_gate_073c"])
    signed_payload = _payload(source_artifacts["signed_order_payload_dry_run_070a"])
    adapter_payload = _payload(source_artifacts["signed_payload_diagnostic_adapter_072e"])
    order_prep_payload = _payload(source_artifacts["order_prep_packet_072a"])
    selected_payload_status = clean_text(selected_payload.get("status"))
    signed_payload_status = clean_text(signed_payload.get("status"))
    adapter_status = clean_text(adapter_payload.get("status"))
    order_prep_status = clean_text(order_prep_payload.get("status"))
    readiness_ready = (
        readiness_source.get("available") is True
        and readiness_source.get("parsed") is True
        and (
            readiness_status == READY_PAYLOAD_STATUS
            or readiness_payload.get("payload_dry_run_ready") is True
        )
    )
    fallback_ready = (
        selected_payload_status == READY_SELECTED_PAYLOAD_STATUS
        and bool(clean_text(signed_payload.get("payload_contract_fingerprint_sha256")))
        and adapter_status == READY_SIGNED_ADAPTER_STATUS
        and order_prep_status == READY_ORDER_PREP_STATUS
    )
    ready = readiness_ready or fallback_ready
    return {
        "ready": ready,
        "available": readiness_source.get("available") is True or bool(selected_payload_status),
        "status": readiness_status or selected_payload_status or "missing",
        "payload_dry_run_readiness_status": readiness_status or "missing",
        "selected_token_payload_readiness_status": selected_payload_status or "missing",
        "signed_order_payload_dry_run_status": signed_payload_status or "missing",
        "signed_payload_diagnostic_adapter_status": adapter_status or "missing",
        "order_prep_status": order_prep_status or "missing",
        "ready_for_submit": False,
        "source_payload_embedded": False,
    }


def _summarize_risk_engine(source_artifacts: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    risk_payload = _payload(source_artifacts["risk_engine_v2_074d"])
    final_payload = _payload(source_artifacts["first_live_order_final_blocker_reducer_072d"])
    static_payload = _payload(source_artifacts["static_safety_invariant_report_060q"])
    risk_status = clean_text(risk_payload.get("status")) or clean_text(source_artifacts["risk_engine_v2_074d"].get("status"))
    final_status = clean_text(final_payload.get("status")) or clean_text(
        source_artifacts["first_live_order_final_blocker_reducer_072d"].get("status")
    )
    static_status = clean_text(static_payload.get("status")) or clean_text(
        source_artifacts["static_safety_invariant_report_060q"].get("status")
    )
    risk_ready = (
        source_artifacts["risk_engine_v2_074d"].get("available") is True
        and (risk_status == READY_RISK_STATUS or risk_payload.get("risk_engine_v2_ready") is True)
    )
    final_clear = (
        source_artifacts["first_live_order_final_blocker_reducer_072d"].get("available") is True
        and (
            final_status == READY_FINAL_REDUCER_STATUS
            or _int_or_none(final_payload.get("remaining_blocker_count")) == 0
        )
    )
    static_ok = (
        source_artifacts["static_safety_invariant_report_060q"].get("available") is not True
        or static_status in READY_STATIC_SAFETY_STATUSES
        or static_payload.get("safety_ok") is True
    )
    return {
        "ready": risk_ready and final_clear and static_ok,
        "risk_engine_ready": risk_ready,
        "final_blocker_reducer_clear": final_clear,
        "static_safety_report_ok": static_ok,
        "risk_engine_status": risk_status or "missing",
        "final_blocker_reducer_status": final_status or "missing",
        "static_safety_report_status": static_status or "missing",
        "remaining_blocker_count": _int_or_none(final_payload.get("remaining_blocker_count")),
        "source_payload_embedded": False,
    }


def _summarize_telegram_launch_config(source: Mapping[str, Any]) -> dict[str, Any]:
    payload = _payload(source)
    nested = payload.get("telegram_launch_config")
    nested_payload = dict(nested) if isinstance(nested, Mapping) else {}
    daily_limit = _first_text(
        payload.get("launch_daily_limit"),
        payload.get("daily_limit"),
        nested_payload.get("daily_limit"),
    )
    max_loss = _first_text(
        payload.get("launch_max_loss"),
        payload.get("max_loss"),
        nested_payload.get("max_loss"),
    )
    selected_markets = _clean_list(
        payload.get("launch_selected_markets")
        or payload.get("selected_markets")
        or nested_payload.get("selected_markets")
        or ()
    )
    operator_stop_requested = (
        payload.get("operator_stop_requested") is True
        or nested_payload.get("operator_stop_requested") is True
    )
    local_trading_request_observed = (
        payload.get("trading_requested") is True
        or nested_payload.get("trading_requested") is True
    )
    return {
        "available": source.get("available") is True,
        "status": clean_text(payload.get("status")) or clean_text(source.get("status")) or "missing",
        "daily_limit": daily_limit,
        "max_loss": max_loss,
        "selected_markets": selected_markets,
        "operator_stop_requested": operator_stop_requested,
        "local_trading_request_observed": local_trading_request_observed,
        "launch_config_source_path": clean_text(source.get("path")),
        "source_payload_embedded": False,
    }


def _summarize_stop_marker(source: Mapping[str, Any]) -> dict[str, Any]:
    payload = _payload(source)
    requested = source.get("available") is True and (
        payload.get("operator_stop_requested") is not False
    )
    return {
        "available": source.get("available") is True,
        "status": clean_text(payload.get("status")) or clean_text(source.get("status")) or "missing",
        "operator_stop_requested": requested,
        "marker_path": clean_text(source.get("path")),
        "source_payload_embedded": False,
    }


def _build_blockers(
    *,
    component_statuses: Mapping[str, Mapping[str, Any]],
    operator_stop_requested: bool,
    generated_at: str,
) -> list[dict[str, Any]]:
    local_real_check = component_statuses["local_real_check_evidence"]
    selected_candidate = component_statuses["selected_candidate"]
    selected_token = component_statuses["selected_token_verification"]
    signer = component_statuses["signer_diagnostic"]
    payload = component_statuses["payload_dry_run_readiness"]
    risk = component_statuses["risk_engine"]
    blockers: list[dict[str, Any]] = []

    if local_real_check.get("ready") is not True:
        blockers.append(
            _blocker(
                STATUS_BLOCKED_MISSING_LOCAL_REAL_CHECK_EVIDENCE,
                "local_real_check_evidence",
                "Local real-check bundle, snapshot, or evidence review is missing.",
                generated_at=generated_at,
            )
        )
    elif selected_candidate.get("ready") is not True:
        blockers.append(
            _blocker(
                STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE,
                "selected_candidate",
                "No source-backed operator-selected candidate artifact is ready.",
                generated_at=generated_at,
            )
        )
    elif selected_token.get("verified") is not True:
        blockers.append(
            _blocker(
                STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN,
                "selected_token_verification",
                "Selected token verification bridge is missing or not verified for payload dry-run.",
                generated_at=generated_at,
            )
        )
    elif signer.get("diagnostic_ok") is not True:
        blockers.append(
            _blocker(
                STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK,
                "signer_diagnostic",
                "Signer diagnostic evidence bridge is missing or not OK for payload dry-run.",
                generated_at=generated_at,
            )
        )
    elif payload.get("ready") is not True:
        blockers.append(
            _blocker(
                STATUS_BLOCKED_PAYLOAD_DRY_RUN_NOT_READY,
                "payload_dry_run_readiness",
                "Payload dry-run readiness review, signed-payload adapter, or order prep evidence is not ready.",
                generated_at=generated_at,
            )
        )
    elif risk.get("ready") is not True:
        blockers.append(
            _blocker(
                STATUS_BLOCKED_RISK_ENGINE_REVIEW,
                "risk_engine",
                "Risk Engine v2, static safety report, or final blocker reducer still blocks review.",
                generated_at=generated_at,
            )
        )
    elif operator_stop_requested:
        blockers.append(
            _blocker(
                STATUS_BLOCKED_OPERATOR_STOP_REQUESTED,
                "operator_stop",
                "Operator stop or halt marker is present.",
                generated_at=generated_at,
            )
        )
    return blockers


def _blocker(
    blocker_id: str,
    category: str,
    reason: str,
    *,
    generated_at: str,
    blocks_authorization_packet: bool = True,
) -> dict[str, Any]:
    value = {
        "blocker_id": clean_text(blocker_id),
        "blocker_category": clean_text(category),
        "reason": clean_text(reason),
        "severity": "critical",
        "resolution_status": "unresolved",
        "resolved": False,
        "blocks_authorization_packet": blocks_authorization_packet,
        "blocks_live_execution": True,
        "generated_at": generated_at,
    }
    value.update(first_supervised_tiny_order_readiness_safety_flags())
    return value


def _build_blockers_artifact(
    *,
    status: str,
    market_symbol: str,
    strategy_name: str,
    blockers: Sequence[Mapping[str, Any]],
    execution_blockers: Sequence[Mapping[str, Any]],
    current_top_blocker: str,
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": FIRST_SUPERVISED_TINY_ORDER_READINESS_BLOCKERS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "blockers": [dict(row) for row in blockers],
        "blocker_count": len(blockers),
        "execution_blockers": [dict(row) for row in execution_blockers],
        "execution_blocker_count": len(execution_blockers),
        "current_top_blocker": clean_text(current_top_blocker),
        "resolved_blocker_count": 0,
        "generated_at": generated_at,
    }
    value.update(first_supervised_tiny_order_readiness_safety_flags())
    return value


def _build_latest_status(
    *,
    status: str,
    market_symbol: str,
    strategy_name: str,
    component_statuses: Mapping[str, Mapping[str, Any]],
    blockers: Sequence[Mapping[str, Any]],
    execution_blockers: Sequence[Mapping[str, Any]],
    ready_for_authorization: bool,
    current_top_blocker: str,
    telegram_launch_config: Mapping[str, Any],
    operator_stop_requested: bool,
    future_live_task_can_be_considered: bool,
    next_command: str,
    operator_summary: str,
    artifact_paths: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    selected_candidate = component_statuses["selected_candidate"]
    selected_token = component_statuses["selected_token_verification"]
    signer = component_statuses["signer_diagnostic"]
    payload = component_statuses["payload_dry_run_readiness"]
    risk = component_statuses["risk_engine"]
    value = {
        "contract_version": FIRST_SUPERVISED_TINY_ORDER_READINESS_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": clean_text(status),
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy": strategy_name,
        "strategy_name": strategy_name,
        "selected_candidate_status": clean_text(selected_candidate.get("status")) or "missing",
        "selected_candidate_ready": selected_candidate.get("ready") is True,
        "selected_token_verification_status": clean_text(selected_token.get("status")) or "missing",
        "selected_token_verified": selected_token.get("verified") is True,
        "signer_diagnostic_status": clean_text(signer.get("status")) or "missing",
        "signer_diagnostic_ok": signer.get("diagnostic_ok") is True,
        "payload_dry_run_readiness_status": clean_text(payload.get("status")) or "missing",
        "payload_dry_run_ready": payload.get("ready") is True,
        "risk_engine_status": clean_text(risk.get("risk_engine_status")) or "missing",
        "risk_engine_ready": risk.get("risk_engine_ready") is True,
        "final_blocker_reducer_status": clean_text(risk.get("final_blocker_reducer_status")) or "missing",
        "final_blocker_reducer_clear": risk.get("final_blocker_reducer_clear") is True,
        "static_safety_report_status": clean_text(risk.get("static_safety_report_status")) or "missing",
        "static_safety_report_ok": risk.get("static_safety_report_ok") is True,
        "daily_limit": clean_text(telegram_launch_config.get("daily_limit")),
        "max_loss": clean_text(telegram_launch_config.get("max_loss")),
        "selected_markets": _clean_list(telegram_launch_config.get("selected_markets") or ()),
        "operator_stop_requested": operator_stop_requested is True,
        "explicit_live_authorization_present": False,
        "first_supervised_tiny_order_ready_for_authorization": ready_for_authorization,
        "first_supervised_tiny_order_ready_for_execution": False,
        "future_separate_live_task_can_be_considered": future_live_task_can_be_considered,
        "current_top_blocker": clean_text(current_top_blocker),
        "blocker_count": len(blockers),
        "execution_blocker_count": len(execution_blockers),
        "resolved_blocker_count": 0,
        "next_recommended_safe_command": clean_text(next_command),
        "operator_summary": clean_text(operator_summary),
        "artifact_path": clean_text(artifact_paths.get("result")),
        "latest_status_path": clean_text(artifact_paths.get("latest_status")),
        "blockers_path": clean_text(artifact_paths.get("blockers")),
        "operator_markdown_path": clean_text(artifact_paths.get("operator_md")),
        "generated_at": generated_at,
    }
    value.update(first_supervised_tiny_order_readiness_safety_flags())
    value["operator_stop_requested"] = operator_stop_requested is True
    value["first_supervised_tiny_order_ready_for_authorization"] = ready_for_authorization
    return value


def _next_recommended_safe_command(*, status: str, market: str, strategy: str) -> str:
    suffix = f"--market {market} --strategy {strategy} --dry-run"
    if status == STATUS_BLOCKED_MISSING_LOCAL_REAL_CHECK_EVIDENCE:
        return f"python -m pm_bot.operator_runner.local_real_check_snapshot {suffix}"
    if status == STATUS_BLOCKED_MISSING_SELECTED_CANDIDATE:
        return f"python -m pm_bot.operator_runner.selected_candidate_artifact {suffix} --candidate-index 0"
    if status == STATUS_BLOCKED_UNVERIFIED_SELECTED_TOKEN:
        return f"python -m pm_bot.operator_runner.selected_token_verification_bridge {suffix}"
    if status == STATUS_BLOCKED_SIGNER_DIAGNOSTIC_NOT_OK:
        return f"python -m pm_bot.operator_runner.signer_diagnostic_evidence_bridge {suffix}"
    if status == STATUS_BLOCKED_PAYLOAD_DRY_RUN_NOT_READY:
        return f"python -m pm_bot.operator_runner.payload_dry_run_readiness_review {suffix}"
    if status == STATUS_BLOCKED_RISK_ENGINE_REVIEW:
        return f"python -m pm_bot.operator_runner.risk_engine_v2_review {suffix}"
    if status == STATUS_BLOCKED_OPERATOR_STOP_REQUESTED:
        return "N/A - operator stop marker must be reviewed and cleared by a separate operator action"
    return f"python -m pm_bot.operator_runner.first_supervised_tiny_order_readiness_packet {suffix}"


def _next_recommended_safe_action(ready_for_authorization: bool) -> str:
    if ready_for_authorization:
        return (
            "A future separate live authorization task can be considered; this 077A packet must not submit, "
            "cancel, sign by default, or enable live execution."
        )
    return "Resolve the current top blocker, then rerun the 077A readiness packet in dry-run mode."


def _operator_summary(
    *,
    status: str,
    ready_for_authorization: bool,
    current_top_blocker: str,
    next_command: str,
) -> str:
    if ready_for_authorization:
        return (
            "All non-live readiness gates are OK for asking the operator for a separate future live authorization. "
            "Execution remains blocked by missing explicit live authorization. Next safe command: "
            f"{next_command}"
        )
    return (
        "First supervised tiny order authorization readiness is blocked by "
        f"{current_top_blocker}. Next safe command: {next_command}"
    )


def _passed_lines(latest: Mapping[str, Any]) -> list[str]:
    checks = (
        ("selected candidate", latest.get("selected_candidate_ready") is True),
        ("selected token verification", latest.get("selected_token_verified") is True),
        ("signer diagnostic evidence", latest.get("signer_diagnostic_ok") is True),
        ("payload dry-run readiness", latest.get("payload_dry_run_ready") is True),
        ("risk engine review", latest.get("risk_engine_ready") is True),
        ("final blocker reducer", latest.get("final_blocker_reducer_clear") is True),
        ("static safety report", latest.get("static_safety_report_ok") is True),
    )
    return [label for label, passed in checks if passed]


def _scope_matches(payload: Mapping[str, Any], *, market_symbol: str, strategy_name: str) -> bool:
    if not payload:
        return False
    market_value = clean_text(payload.get("market_symbol") or payload.get("market")).upper()
    strategy_value = clean_text(payload.get("strategy_name") or payload.get("strategy"))
    if market_value and market_value != market_symbol:
        return False
    if strategy_value and strategy_value != strategy_name:
        return False
    return True


def _false_flags_ok(payload: Mapping[str, Any], fields: Sequence[str]) -> bool:
    if not payload:
        return False
    for field in fields:
        if field in payload and payload.get(field) is not False:
            return False
    return True


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _first_text(*values: Any) -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def _clean_list(value: Any) -> list[str]:
    if isinstance(value, str):
        candidates = [item.strip() for item in value.split(",")]
    elif isinstance(value, Sequence):
        candidates = [clean_text(item) for item in value]
    else:
        candidates = []
    return [item for item in candidates if item]
