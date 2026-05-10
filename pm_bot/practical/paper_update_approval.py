from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import bullet_lines, clean_text, load_json_object, write_json, write_text

APPROVAL_CONTRACT_VERSION = "pmbot_paper_update_operator_approval.v1"
TASK_ID = "ORCH-PMBOT-PRACTICAL-012-OPERATOR-APPROVED-PAPER-HYPOTHESIS-UPDATE-APPLICATION"
DEFAULT_OUT_DIR = Path("pm_bot/practical/artifacts/paper_update_application_012")
SAFE_APPROVAL_STATUS = "approved_for_paper_tracking_update_only"

APPROVAL_SCOPE = [
    "paper_tracking_update_only",
    "non_executable",
    "no_real_trade_decision",
    "no_orders",
    "no_wallet",
    "no_trading",
    "original_artifacts_preserved",
    "versioned_snapshot_required",
]

BLOCKED_SCOPE = [
    "blocked real trading",
    "blocked wallet/signing/orders",
    "blocked trading recommendations",
    "blocked probability/EV/edge/side-selection trading signal",
    "blocked automatic market action",
    "blocked outcome resolution without local outcome record",
]

ACTIONABLE_TRADING_PATTERN = re.compile(
    r"\b(?:should|must|recommend(?:ed)?|instruction|signal|execute|place)\b.{0,80}"
    r"\b(?:buy|sell|hold|enter|exit|order)\b",
    re.IGNORECASE,
)


class PaperUpdateApprovalError(ValueError):
    pass


def current_utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_paper_update_operator_approval(
    update_candidates: Sequence[Mapping[str, Any]],
    *,
    approval_for_task_id: str = TASK_ID,
    approved_at: str | None = None,
) -> dict[str, Any]:
    candidates = [dict(candidate) for candidate in update_candidates]
    if not candidates:
        raise PaperUpdateApprovalError("at least one update candidate is required for approval")

    for candidate in candidates:
        validate_update_candidate_for_paper_approval(candidate)

    candidate_ids = [clean_text(candidate.get("update_candidate_id")) for candidate in candidates]
    approval_id = "paper-update-approval-012-" + "-".join(candidate_ids)
    return {
        "contract_version": APPROVAL_CONTRACT_VERSION,
        "approval_id": approval_id,
        "approval_for_task_id": approval_for_task_id,
        "approval_status": SAFE_APPROVAL_STATUS,
        "approved_update_candidate_ids": candidate_ids,
        "approved_market_ids": _unique_values(candidate.get("market_id") for candidate in candidates),
        "approved_hypothesis_ids": _unique_values(candidate.get("hypothesis_id") for candidate in candidates),
        "approved_by": "operator",
        "approved_at": approved_at or current_utc_timestamp(),
        "approval_scope": list(APPROVAL_SCOPE),
        "blocked_scope": list(BLOCKED_SCOPE),
        "reusable": False,
        "expires_after_task": True,
    }


def validate_update_candidate_for_paper_approval(candidate: Mapping[str, Any]) -> None:
    required_false = {
        "update_applied": candidate.get("update_applied"),
        "market_recommendation_generated": candidate.get("market_recommendation_generated"),
        "probability_ev_edge_or_side_selection_generated": candidate.get(
            "probability_ev_edge_or_side_selection_generated"
        ),
        "orders_or_trading_actions": candidate.get("orders_or_trading_actions"),
        "wallet_or_private_key_access": candidate.get("wallet_or_private_key_access"),
        "automatic_analysis_update_performed": candidate.get("automatic_analysis_update_performed"),
    }
    required_true = {
        "operator_approval_required": candidate.get("operator_approval_required"),
        "no_real_trade_decision": candidate.get("no_real_trade_decision"),
    }
    missing_identity = [
        field
        for field in ("update_candidate_id", "market_id", "hypothesis_id")
        if not clean_text(candidate.get(field))
    ]
    if missing_identity:
        raise PaperUpdateApprovalError(f"candidate is missing required fields: {', '.join(missing_identity)}")
    for field, value in required_false.items():
        if value is not False:
            raise PaperUpdateApprovalError(f"candidate field {field} must be false")
    for field, value in required_true.items():
        if value is not True:
            raise PaperUpdateApprovalError(f"candidate field {field} must be true")
    if _contains_actionable_trading_instruction(candidate):
        raise PaperUpdateApprovalError("candidate contains action-like trading wording")


def validate_operator_approval(approval: Mapping[str, Any], candidates: Sequence[Mapping[str, Any]]) -> None:
    if approval.get("contract_version") != APPROVAL_CONTRACT_VERSION:
        raise PaperUpdateApprovalError("approval contract_version is invalid")
    if approval.get("approval_status") != SAFE_APPROVAL_STATUS:
        raise PaperUpdateApprovalError("approval status is not paper-update-only")
    if approval.get("reusable") is not False or approval.get("expires_after_task") is not True:
        raise PaperUpdateApprovalError("approval must be non-reusable and expire after the task")
    scope = set(approval.get("approval_scope", []))
    blocked = set(approval.get("blocked_scope", []))
    if not set(APPROVAL_SCOPE).issubset(scope):
        raise PaperUpdateApprovalError("approval scope is incomplete")
    if not set(BLOCKED_SCOPE).issubset(blocked):
        raise PaperUpdateApprovalError("blocked scope is incomplete")

    approved_ids = set(approval.get("approved_update_candidate_ids", []))
    expected_ids = {clean_text(candidate.get("update_candidate_id")) for candidate in candidates}
    if approved_ids != expected_ids:
        raise PaperUpdateApprovalError("approval candidate ids do not match requested candidates")


def write_paper_update_operator_approval_012(
    update_candidates: Sequence[Mapping[str, Any]],
    *,
    out_dir: str | Path = DEFAULT_OUT_DIR,
    approved_at: str | None = None,
) -> dict[str, Any]:
    approval = build_paper_update_operator_approval(update_candidates, approved_at=approved_at)
    validate_operator_approval(approval, update_candidates)
    out_path = Path(out_dir)
    write_json(out_path / "paper_update_operator_approval_012.json", approval)
    write_text(out_path / "paper_update_operator_approval_012.md", render_paper_update_operator_approval_markdown(approval))
    return approval


def render_paper_update_operator_approval_markdown(approval: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Paper Update Operator Approval",
            "",
            f"- Approval ID: `{approval.get('approval_id')}`",
            f"- Task: `{approval.get('approval_for_task_id')}`",
            f"- Status: `{approval.get('approval_status')}`",
            f"- Approved by: `{approval.get('approved_by')}`",
            f"- Approved at: `{approval.get('approved_at')}`",
            f"- Reusable: `{str(approval.get('reusable')).lower()}`",
            f"- Expires after task: `{str(approval.get('expires_after_task')).lower()}`",
            "",
            "## Approved Candidates",
            "",
            *bullet_lines(f"`{candidate_id}`" for candidate_id in approval.get("approved_update_candidate_ids", [])),
            "",
            "## Approved Markets",
            "",
            *bullet_lines(f"`{market_id}`" for market_id in approval.get("approved_market_ids", [])),
            "",
            "## Approved Hypotheses",
            "",
            *bullet_lines(f"`{hypothesis_id}`" for hypothesis_id in approval.get("approved_hypothesis_ids", [])),
            "",
            "## Approval Scope",
            "",
            *bullet_lines(str(item) for item in approval.get("approval_scope", [])),
            "",
            "## Blocked Scope",
            "",
            *bullet_lines(str(item) for item in approval.get("blocked_scope", [])),
            "",
            "## Safety Boundary",
            "",
            "- Applies only to a versioned paper tracking snapshot.",
            "- Original artifacts are preserved.",
            "- No real trade decision, wallet path, order path, or automatic market action is approved.",
        ]
    ) + "\n"


def _unique_values(values: Sequence[Any]) -> list[str]:
    unique = sorted({clean_text(value) for value in values if clean_text(value)})
    return unique


def _contains_actionable_trading_instruction(value: Any) -> bool:
    for text in _walk_strings(value):
        normalized = text.lower()
        if any(boundary in normalized for boundary in ("blocked", "no ", "not ", "false", "without")):
            continue
        if ACTIONABLE_TRADING_PATTERN.search(text):
            return True
    return False


def _walk_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        strings: list[str] = []
        for nested in value.values():
            strings.extend(_walk_strings(nested))
        return strings
    if isinstance(value, list):
        strings = []
        for nested in value:
            strings.extend(_walk_strings(nested))
        return strings
    return []


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a paper-only operator approval artifact.")
    parser.add_argument("--candidate", action="append", required=True, help="Candidate JSON path; repeatable.")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="Output artifact directory.")
    args = parser.parse_args(argv)
    candidates = [load_json_object(path, label="paper update candidate") for path in args.candidate]
    write_paper_update_operator_approval_012(candidates, out_dir=args.out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
