from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from pm_bot.practical.one_market_analysis import (
    OUTCOME_RECORD_CONTRACT_VERSION,
    PAPER_HYPOTHESIS_SAFETY_LABEL,
    RESULT_CONTRACT_VERSION as ANALYSIS_RESULT_CONTRACT_VERSION,
    _canonical_json,
    _clean_text,
    _is_network_like,
    _normalize_path_string,
)

FEEDBACK_RESULT_CONTRACT_VERSION = "pmbot_one_market_paper_feedback_result.v1"
DEFAULT_FEEDBACK_JSON_PATH = "pm_bot/practical/artifacts/one_market_feedback_sample_001.result.json"
DEFAULT_FEEDBACK_MD_PATH = "pm_bot/practical/artifacts/one_market_feedback_sample_001.md"

REQUIRED_OUTCOME_FIELDS = (
    "actual_outcome_summary",
    "contract_version",
    "market_id",
    "operator_notes",
    "outcome_status",
    "resolution_source_reference",
    "resolved_at",
)
ALLOWED_OUTCOME_STATUSES = {"ambiguous", "resolved", "unresolved", "void"}
ALLOWED_QUALITY_LABELS = {
    "ambiguous",
    "incomplete",
    "unresolved",
    "useful",
    "wrong_due_to_bad_reasoning",
    "wrong_due_to_missing_evidence",
}


@dataclass(frozen=True)
class PaperFeedbackValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()


class PaperFeedbackError(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


def load_analysis_result(path: str | Path) -> dict[str, Any]:
    return _load_json_object(path, "analysis")


def load_outcome_record(path: str | Path) -> dict[str, Any]:
    return _load_json_object(path, "outcome")


def validate_outcome_record(outcome: Any) -> PaperFeedbackValidationResult:
    errors: list[str] = []
    if not isinstance(outcome, Mapping):
        return PaperFeedbackValidationResult(False, ("outcome record must be an object",))
    for field in REQUIRED_OUTCOME_FIELDS:
        if field not in outcome:
            errors.append(f"outcome.{field} is required")
    if outcome.get("contract_version") != OUTCOME_RECORD_CONTRACT_VERSION:
        errors.append(f"outcome.contract_version must be {OUTCOME_RECORD_CONTRACT_VERSION}")
    if outcome.get("outcome_status") not in ALLOWED_OUTCOME_STATUSES:
        errors.append("outcome.outcome_status must be unresolved, resolved, void, or ambiguous")
    for field in ("actual_outcome_summary", "market_id", "outcome_status", "resolution_source_reference"):
        if field in outcome and not isinstance(outcome.get(field), str):
            errors.append(f"outcome.{field} must be a string")
    if "resolved_at" in outcome and outcome.get("resolved_at") is not None and not isinstance(outcome.get("resolved_at"), str):
        errors.append("outcome.resolved_at must be a string or null")
    if "operator_notes" in outcome and not _is_string_list(outcome.get("operator_notes")):
        errors.append("outcome.operator_notes must be a list of strings")
    return PaperFeedbackValidationResult(not errors, tuple(errors))


def validate_analysis_result(analysis: Any) -> PaperFeedbackValidationResult:
    errors: list[str] = []
    if not isinstance(analysis, Mapping):
        return PaperFeedbackValidationResult(False, ("analysis result must be an object",))
    required = (
        "analysis_id",
        "contract_version",
        "market_id",
        "missing_evidence",
        "paper_hypothesis",
        "paper_hypothesis_safety_label",
        "source_attribution",
    )
    for field in required:
        if field not in analysis:
            errors.append(f"analysis.{field} is required")
    if analysis.get("contract_version") != ANALYSIS_RESULT_CONTRACT_VERSION:
        errors.append(f"analysis.contract_version must be {ANALYSIS_RESULT_CONTRACT_VERSION}")
    if analysis.get("paper_hypothesis_safety_label") != PAPER_HYPOTHESIS_SAFETY_LABEL:
        errors.append("analysis.paper_hypothesis_safety_label must remain paper-only")
    return PaperFeedbackValidationResult(not errors, tuple(errors))


def build_paper_feedback_result(
    analysis: Mapping[str, Any],
    outcome: Mapping[str, Any],
    *,
    generated_artifact_paths: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    analysis_validation = validate_analysis_result(analysis)
    if not analysis_validation.valid:
        raise PaperFeedbackError(analysis_validation.errors)
    outcome_validation = validate_outcome_record(outcome)
    if not outcome_validation.valid:
        raise PaperFeedbackError(outcome_validation.errors)
    if str(analysis["market_id"]) != str(outcome["market_id"]):
        raise PaperFeedbackError(("outcome.market_id must match analysis.market_id",))

    artifact_paths = {
        "feedback_markdown": DEFAULT_FEEDBACK_MD_PATH,
        "feedback_result_json": DEFAULT_FEEDBACK_JSON_PATH,
    }
    if generated_artifact_paths:
        artifact_paths.update(dict(generated_artifact_paths))

    quality_label = _quality_label(analysis, outcome)
    source_review = _source_contribution_review(analysis, quality_label)
    feedback_id = _feedback_id(analysis, outcome)
    result = {
        "actual_outcome_summary": _clean_text(outcome["actual_outcome_summary"]),
        "analysis_id": _clean_text(analysis["analysis_id"]),
        "analysis_quality_label": quality_label,
        "contract_version": FEEDBACK_RESULT_CONTRACT_VERSION,
        "feedback_id": feedback_id,
        "generated_artifacts": dict(sorted(artifact_paths.items())),
        "market_id": _clean_text(analysis["market_id"]),
        "missing_evidence_lessons": _missing_evidence_lessons(analysis, quality_label),
        "next_prompt_improvements": _next_prompt_improvements(quality_label),
        "no_real_trade_decision": True,
        "operator_notes": [_clean_text(note) for note in outcome["operator_notes"]],
        "orders_or_trading_actions": False,
        "outcome_status": _clean_text(outcome["outcome_status"]),
        "paper_hypothesis_review": _paper_hypothesis_review(analysis, outcome, quality_label),
        "reasoning_lessons": _reasoning_lessons(quality_label),
        "resolved_at": _clean_text(outcome["resolved_at"]) if outcome.get("resolved_at") is not None else None,
        "resolution_source_reference": _clean_text(outcome["resolution_source_reference"]),
        "source_contribution_review": source_review,
        "source_quality_lessons": _source_quality_lessons(source_review),
        "wallet_or_private_key_access": False,
    }
    return result


def run_paper_feedback(
    *,
    analysis_path: str | Path,
    outcome_path: str | Path,
    out_json_path: str | Path | None = None,
    out_md_path: str | Path | None = None,
) -> dict[str, Any]:
    analysis = load_analysis_result(analysis_path)
    outcome = load_outcome_record(outcome_path)
    artifact_paths = {}
    if out_json_path is not None:
        artifact_paths["feedback_result_json"] = _normalize_path_string(out_json_path)
    if out_md_path is not None:
        artifact_paths["feedback_markdown"] = _normalize_path_string(out_md_path)
    result = build_paper_feedback_result(analysis, outcome, generated_artifact_paths=artifact_paths)
    if out_json_path is not None:
        _write_json(Path(out_json_path), result)
    if out_md_path is not None:
        _write_text(Path(out_md_path), render_feedback_markdown(result))
    return result


def render_feedback_markdown(feedback: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT One-Market Paper Feedback",
        "",
        f"- Feedback ID: `{feedback['feedback_id']}`",
        f"- Analysis ID: `{feedback['analysis_id']}`",
        f"- Market ID: `{feedback['market_id']}`",
        f"- Outcome status: `{feedback['outcome_status']}`",
        f"- Analysis quality: `{feedback['analysis_quality_label']}`",
        "",
        "## Outcome",
        "",
        feedback["actual_outcome_summary"] or "No outcome summary recorded.",
        "",
        "## Paper hypothesis review",
        "",
        f"- Review status: `{feedback['paper_hypothesis_review']['review_status']}`",
        f"- Qualitative result: {feedback['paper_hypothesis_review']['qualitative_result']}",
        "",
        "## Source contribution review",
        "",
        *_bullet_lines(_format_source_review(row) for row in feedback["source_contribution_review"]),
        "",
        "## Missing evidence lessons",
        "",
        *_bullet_lines(feedback["missing_evidence_lessons"]),
        "",
        "## Reasoning lessons",
        "",
        *_bullet_lines(feedback["reasoning_lessons"]),
        "",
        "## Source quality lessons",
        "",
        *_bullet_lines(feedback["source_quality_lessons"]),
        "",
        "## Next prompt improvements",
        "",
        *_bullet_lines(feedback["next_prompt_improvements"]),
        "",
        "## Safety",
        "",
        "- Local analysis and outcome JSON files only.",
        "- No real trade decision was produced.",
        "- Orders or trading actions: false.",
        "- Wallet/private-key access: false.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build local PMBOT paper feedback for one market.")
    parser.add_argument("--analysis", required=True, help="Local one-market analysis result JSON.")
    parser.add_argument("--outcome", required=True, help="Local outcome record JSON.")
    parser.add_argument("--out-json", required=True, help="Output feedback JSON.")
    parser.add_argument("--out-md", required=True, help="Output feedback Markdown.")
    args = parser.parse_args(argv)

    run_paper_feedback(
        analysis_path=args.analysis,
        outcome_path=args.outcome,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


def _quality_label(analysis: Mapping[str, Any], outcome: Mapping[str, Any]) -> str:
    status = str(outcome["outcome_status"])
    review_text = " ".join([str(outcome.get("actual_outcome_summary", "")), *outcome.get("operator_notes", [])]).lower()
    if status == "unresolved":
        return "unresolved"
    if status in {"ambiguous", "void"}:
        return "ambiguous"
    if "bad reasoning" in review_text:
        return "wrong_due_to_bad_reasoning"
    if "missing evidence" in review_text or "omitted evidence" in review_text:
        return "wrong_due_to_missing_evidence"
    if "useful" in review_text or "aligned" in review_text or "matched" in review_text:
        return "useful"
    if analysis.get("missing_evidence"):
        return "incomplete"
    return "useful"


def _source_contribution_review(analysis: Mapping[str, Any], quality_label: str) -> list[dict[str, Any]]:
    stale_source_ids = {
        str(note.get("source_id"))
        for note in analysis.get("staleness_notes", [])
        if isinstance(note, Mapping)
    }
    contradiction_source_ids = _contradiction_source_ids(analysis.get("contradiction_notes", []))
    review: list[dict[str, Any]] = []
    for attribution in analysis["source_attribution"]:
        source_id = str(attribution["source_id"])
        used = attribution.get("used_in_analysis") is True
        if not used:
            label = "unused"
            issue = "Source was present but not used in the local analysis."
            handling = "Keep as context unless a later packet needs its claim type."
        elif source_id in contradiction_source_ids:
            label = "contradictory"
            issue = "Source was part of a contradiction note."
            handling = "Require operator review when this source conflicts with another local record."
        elif source_id in stale_source_ids:
            label = "stale"
            issue = "Source freshness status was stale or equivalent."
            handling = "Require a fresher local capture before relying on the same claim."
        elif quality_label == "wrong_due_to_missing_evidence":
            label = "insufficient"
            issue = "Used source did not cover the evidence later identified as material."
            handling = "Pair this source with the missing evidence type in future packets."
        elif quality_label == "wrong_due_to_bad_reasoning":
            label = "misleading"
            issue = "Source may have been interpreted incorrectly in the local analysis."
            handling = "Add a prompt check separating source claim from reasoning step."
        elif quality_label == "useful":
            label = "useful"
            issue = "Source contributed to a useful qualitative analysis review."
            handling = "Keep source attribution and limitations visible in future packets."
        else:
            label = "unknown"
            issue = "Outcome review did not resolve source usefulness."
            handling = "Keep source in pending review until a resolved outcome exists."
        review.append(
            {
                "claim_type": _clean_text(attribution["claim_type"]),
                "evidence_role": "used_source" if used else "unused_context",
                "observed_issue": issue,
                "source_id": _clean_text(source_id),
                "source_name": _clean_text(attribution["source_name"]),
                "suggested_future_handling": handling,
                "usefulness_label": label,
            }
        )
    return sorted(review, key=lambda row: row["source_id"])


def _contradiction_source_ids(notes: Any) -> set[str]:
    source_ids: set[str] = set()
    if not isinstance(notes, list):
        return source_ids
    for note in notes:
        if not isinstance(note, Mapping):
            continue
        for value in note.get("conflicting_values", []):
            if not isinstance(value, Mapping):
                continue
            for source in value.get("sources", []):
                if isinstance(source, Mapping) and isinstance(source.get("source_id"), str):
                    source_ids.add(source["source_id"])
    return source_ids


def _paper_hypothesis_review(
    analysis: Mapping[str, Any],
    outcome: Mapping[str, Any],
    quality_label: str,
) -> dict[str, Any]:
    outcome_status = outcome["outcome_status"]
    return {
        "hypothesis_id": _clean_text(analysis["paper_hypothesis"]["hypothesis_id"]),
        "outcome_check_completed": outcome_status in {"resolved", "void", "ambiguous"},
        "paper_only_non_executable": True,
        "qualitative_result": _qualitative_result_sentence(quality_label),
        "review_status": "outcome_pending" if outcome_status == "unresolved" else "reviewed",
    }


def _qualitative_result_sentence(quality_label: str) -> str:
    sentences = {
        "ambiguous": "Outcome review is ambiguous; do not learn a source preference from it.",
        "incomplete": "Analysis had useful structure but still lacked material evidence.",
        "unresolved": "Outcome is not resolved, so the paper hypothesis remains pending.",
        "useful": "Analysis was useful for later review against the recorded outcome.",
        "wrong_due_to_bad_reasoning": "Analysis appears wrong because the reasoning step was flawed.",
        "wrong_due_to_missing_evidence": "Analysis appears wrong because material evidence was missing.",
    }
    return sentences[quality_label]


def _missing_evidence_lessons(analysis: Mapping[str, Any], quality_label: str) -> list[str]:
    missing = [_clean_text(item) for item in analysis.get("missing_evidence", [])]
    if quality_label == "wrong_due_to_missing_evidence" and missing:
        return [f"Missing evidence was material: {item}" for item in missing]
    if missing:
        return [f"Track whether this missing evidence matters later: {item}" for item in missing]
    return ["No missing evidence lesson was recorded from this outcome."]


def _reasoning_lessons(quality_label: str) -> list[str]:
    if quality_label == "wrong_due_to_bad_reasoning":
        return ["Separate evidence summary from the reasoning claim in the next analysis card."]
    if quality_label == "wrong_due_to_missing_evidence":
        return ["Add an explicit missing-evidence impact check before writing the paper-only hypothesis."]
    if quality_label == "useful":
        return ["Preserve compact source attribution and outcome check fields."]
    if quality_label == "unresolved":
        return ["Wait for a local outcome record before judging the analysis."]
    return ["Keep ambiguous outcomes out of source usefulness updates unless reviewed by an operator."]


def _source_quality_lessons(source_review: Sequence[Mapping[str, Any]]) -> list[str]:
    labels = sorted({str(row["usefulness_label"]) for row in source_review})
    return [f"Observed source usefulness label: {label}" for label in labels]


def _next_prompt_improvements(quality_label: str) -> list[str]:
    improvements = {
        "ambiguous": ["Ask the operator to mark ambiguous outcomes separately from source failures."],
        "incomplete": ["Ask for a short missing-evidence impact note before the paper-only hypothesis."],
        "unresolved": ["Keep the outcome placeholder visible until a resolved local record exists."],
        "useful": ["Keep the current compact card shape and source attribution fields."],
        "wrong_due_to_bad_reasoning": ["Add a required reasoning audit note for each key claim."],
        "wrong_due_to_missing_evidence": ["Add a required material-missing-evidence check before analysis completion."],
    }
    return improvements[quality_label]


def _feedback_id(analysis: Mapping[str, Any], outcome: Mapping[str, Any]) -> str:
    digest_input = {
        "analysis_id": analysis["analysis_id"],
        "market_id": analysis["market_id"],
        "outcome": outcome,
    }
    digest = hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest()[:12]
    return f"{analysis['analysis_id']}.feedback.{digest}"


def _format_source_review(row: Mapping[str, Any]) -> str:
    return (
        f"`{row['source_id']}` ({row['source_name']}): "
        f"`{row['usefulness_label']}`; {row['observed_issue']}"
    )


def _bullet_lines(items: Iterable[str]) -> list[str]:
    return [f"- {item}" for item in items]


def _load_json_object(path: str | Path, label: str) -> dict[str, Any]:
    path_string = _normalize_path_string(path)
    if _is_network_like(path_string):
        raise PaperFeedbackError((f"{label} path must be local: {path_string}",))
    path_obj = Path(path)
    if not path_obj.exists():
        raise PaperFeedbackError((f"{label} path does not exist: {path_string}",))
    payload = json.loads(path_obj.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise PaperFeedbackError((f"{label} JSON must be an object",))
    return payload


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
