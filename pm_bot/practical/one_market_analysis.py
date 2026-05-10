from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

INPUT_CONTRACT_VERSION = "pmbot_one_market_input.v1"
RESULT_CONTRACT_VERSION = "pmbot_one_market_analysis_result.v1"
OUTCOME_RECORD_CONTRACT_VERSION = "pmbot_one_market_outcome_record.v1"
ANALYSIS_MODE = "local_one_market"
PAPER_HYPOTHESIS_SAFETY_LABEL = "paper_only_non_executable_analysis_tracking"

DEFAULT_ANALYSIS_JSON_PATH = "pm_bot/practical/artifacts/one_market_analysis_sample_001.result.json"
DEFAULT_ANALYSIS_MD_PATH = "pm_bot/practical/artifacts/one_market_analysis_sample_001.md"

REQUIRED_INPUT_FIELDS = (
    "available_evidence",
    "contract_version",
    "created_at",
    "current_context_summary",
    "known_uncertainties",
    "market_id",
    "market_slug_or_reference",
    "market_title",
    "market_type",
    "missing_evidence",
    "operator_notes",
    "outcomes",
    "resolution_source_summary",
    "rules_summary",
    "source_packets",
)
REQUIRED_SOURCE_PACKET_FIELDS = (
    "captured_at",
    "claim_type",
    "claim_value",
    "evidence_summary",
    "freshness_status",
    "known_limitations",
    "source_id",
    "source_name",
    "source_type",
    "source_url_or_reference",
    "used_in_analysis",
)

SAFE_RESULT_FLAGS = {
    "authenticated_endpoints_used": False,
    "live_network_used": False,
    "market_recommendation_generated": False,
    "openrouter_calls_performed": 0,
    "orders_or_trading_actions": False,
    "polymarket_api_calls_performed": 0,
    "probability_ev_edge_or_side_selection_generated": False,
    "runtime_or_dispatcher_changes": False,
    "wallet_or_private_key_access": False,
}

FORBIDDEN_VALUE_TOKENS = {
    "advice",
    "bet",
    "buy",
    "confidence",
    "edge",
    "enter",
    "ev",
    "exit",
    "forecast",
    "guidance",
    "hold",
    "odds",
    "pick",
    "probability",
    "recommendation",
    "recommendations",
    "score",
    "scoring",
    "selection",
    "sell",
    "side",
    "stake",
    "wager",
}
PAPER_HYPOTHESIS_FORBIDDEN_TOKENS = {
    "buy",
    "sell",
    "hold",
    "enter",
    "exit",
    "probability",
    "ev",
    "edge",
    "confidence",
}
SENSITIVE_PATH_PARTS = {
    ".codex",
    ".env",
    ".git",
    "auth",
    "credential",
    "credentials",
    "key",
    "keys",
    "private",
    "secret",
    "secrets",
    "seed",
    "signing",
    "wallet",
}
SENSITIVE_TEXT_MARKERS = (
    ".env",
    "api_key",
    "auth token",
    "browser profile",
    "credential",
    "private key",
    "private_key",
    "secret",
    "seed phrase",
    "signing key",
    "wallet",
)
STALE_FRESHNESS_STATUSES = {
    "expired",
    "missing_timestamp",
    "outdated",
    "stale",
    "too_old",
    "unknown_stale",
}


@dataclass(frozen=True)
class PracticalValidationResult:
    valid: bool
    errors: tuple[str, ...] = ()


class OneMarketAnalysisError(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


def load_one_market_input(path: str | Path) -> dict[str, Any]:
    input_path = _resolve_local_json_path(path)
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise OneMarketAnalysisError(("input JSON must be an object",))
    return payload


def validate_one_market_input(payload: Any) -> PracticalValidationResult:
    errors: list[str] = []
    if not isinstance(payload, Mapping):
        return PracticalValidationResult(False, ("input must be an object",))

    errors.extend(_missing_fields(payload, REQUIRED_INPUT_FIELDS, "input"))
    if payload.get("contract_version") != INPUT_CONTRACT_VERSION:
        errors.append(f"input.contract_version must be {INPUT_CONTRACT_VERSION}")

    for field_name in (
        "created_at",
        "current_context_summary",
        "market_id",
        "market_slug_or_reference",
        "market_title",
        "market_type",
        "resolution_source_summary",
        "rules_summary",
    ):
        if field_name in payload and not _is_non_empty_string(payload.get(field_name)):
            errors.append(f"input.{field_name} must be a non-empty string")

    for field_name in (
        "available_evidence",
        "known_uncertainties",
        "missing_evidence",
        "operator_notes",
        "outcomes",
    ):
        if field_name in payload and not _is_string_list(payload.get(field_name)):
            errors.append(f"input.{field_name} must be a list of strings")

    source_packets = payload.get("source_packets")
    if not isinstance(source_packets, list) or not source_packets:
        errors.append("input.source_packets must be a non-empty list")
    else:
        errors.extend(_validate_source_packets(source_packets))

    sensitive_hits = _find_sensitive_markers(payload)
    if sensitive_hits:
        errors.append("sensitive marker detected in input at: " + ", ".join(sensitive_hits))

    return PracticalValidationResult(not errors, tuple(errors))


def build_one_market_analysis_result(
    payload: Mapping[str, Any],
    *,
    generated_artifact_paths: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    validation = validate_one_market_input(payload)
    if not validation.valid:
        raise OneMarketAnalysisError(validation.errors)

    artifact_paths = {
        "analysis_card_markdown": DEFAULT_ANALYSIS_MD_PATH,
        "analysis_result_json": DEFAULT_ANALYSIS_JSON_PATH,
    }
    if generated_artifact_paths:
        artifact_paths.update(dict(generated_artifact_paths))

    source_packets = [dict(packet) for packet in payload["source_packets"]]
    sources_used = [_source_summary(packet) for packet in source_packets if packet["used_in_analysis"] is True]
    sources_not_used = [_source_summary(packet) for packet in source_packets if packet["used_in_analysis"] is not True]
    source_attribution = [_source_attribution(packet) for packet in source_packets]
    staleness_notes = _build_staleness_notes(source_packets)
    contradiction_notes = _build_contradiction_notes(source_packets)
    missing_evidence = _clean_string_list(payload["missing_evidence"])
    uncertainty_notes = _clean_string_list(payload["known_uncertainties"])
    available_evidence = _clean_string_list(payload["available_evidence"])

    analysis_id = _analysis_id(payload)
    evidence_status = {
        "available_evidence_count": len(available_evidence),
        "contradiction_note_count": len(contradiction_notes),
        "missing_evidence_count": len(missing_evidence),
        "source_packets_count": len(source_packets),
        "stale_source_count": len(staleness_notes),
        "used_source_count": len(sources_used),
        "unused_source_count": len(sources_not_used),
    }
    result = {
        "analysis_id": analysis_id,
        "analysis_mode": ANALYSIS_MODE,
        "authenticated_endpoints_used": False,
        "contract_version": RESULT_CONTRACT_VERSION,
        "contradiction_notes": contradiction_notes,
        "evidence_status": evidence_status,
        "generated_artifacts": dict(sorted(artifact_paths.items())),
        "key_question": _key_question(payload),
        "live_network_used": False,
        "market_id": _clean_text(payload["market_id"]),
        "market_recommendation_generated": False,
        "market_title": _clean_text(payload["market_title"]),
        "missing_evidence": missing_evidence,
        "next_research_questions": _next_research_questions(missing_evidence, uncertainty_notes),
        "no_real_trade_decision": True,
        "openrouter_calls_performed": 0,
        "operator_summary": _operator_summary(payload, evidence_status),
        "orders_or_trading_actions": False,
        "outcome_tracking_status": {
            "required_contract_version": OUTCOME_RECORD_CONTRACT_VERSION,
            "review_required": True,
            "status": "placeholder_pending_outcome_record",
        },
        "paper_hypothesis": _paper_hypothesis(analysis_id, payload, sources_used, missing_evidence, uncertainty_notes),
        "paper_hypothesis_allowed": True,
        "paper_hypothesis_safety_label": PAPER_HYPOTHESIS_SAFETY_LABEL,
        "paper_hypothesis_tracking_fields": {
            "analysis_id": analysis_id,
            "created_from": ANALYSIS_MODE,
            "expected_outcome_record_contract_version": OUTCOME_RECORD_CONTRACT_VERSION,
            "market_id": _clean_text(payload["market_id"]),
            "outcome_record_required_fields": [
                "contract_version",
                "market_id",
                "outcome_status",
                "actual_outcome_summary",
                "resolved_at",
                "resolution_source_reference",
                "operator_notes",
            ],
            "tracking_status": "pending_outcome_record",
        },
        "polymarket_api_calls_performed": 0,
        "probability_ev_edge_or_side_selection_generated": False,
        "review_quality_score_inputs": {
            "available_evidence_count": len(available_evidence),
            "contradiction_note_count": len(contradiction_notes),
            "missing_evidence_count": len(missing_evidence),
            "operator_note_count": len(payload["operator_notes"]),
            "stale_source_count": len(staleness_notes),
            "used_source_count": len(sources_used),
        },
        "runtime_or_dispatcher_changes": False,
        "source_attribution": source_attribution,
        "sources_not_used": sources_not_used,
        "sources_used": sources_used,
        "staleness_notes": staleness_notes,
        "uncertainty_notes": uncertainty_notes,
        "wallet_or_private_key_access": False,
    }
    _assert_paper_hypothesis_safe(result["paper_hypothesis"])
    return result


def run_one_market_analysis(
    *,
    input_path: str | Path,
    out_json_path: str | Path | None = None,
    out_md_path: str | Path | None = None,
) -> dict[str, Any]:
    payload = load_one_market_input(input_path)
    artifact_paths = {}
    if out_json_path is not None:
        artifact_paths["analysis_result_json"] = _normalize_path_string(out_json_path)
    if out_md_path is not None:
        artifact_paths["analysis_card_markdown"] = _normalize_path_string(out_md_path)
    result = build_one_market_analysis_result(payload, generated_artifact_paths=artifact_paths)

    if out_json_path is not None:
        _write_json(Path(out_json_path), result)
    if out_md_path is not None:
        _write_text(Path(out_md_path), render_markdown_card(result))
    return result


def render_markdown_card(result: Mapping[str, Any]) -> str:
    _validate_result_shape_for_markdown(result)
    lines = [
        "# PMBOT One-Market Analysis Card",
        "",
        "## Market",
        "",
        f"- Market ID: `{result['market_id']}`",
        f"- Title: {result['market_title']}",
        f"- Analysis ID: `{result['analysis_id']}`",
        "",
        "## Main question",
        "",
        result["key_question"],
        "",
        "## Sources used",
        "",
        *_bullet_lines(_format_source_line(source) for source in result["sources_used"]),
        "",
        "## What we know",
        "",
        result["operator_summary"],
        "",
        "## What we do not know",
        "",
        *_bullet_lines(result["missing_evidence"] or ["No missing evidence recorded in the local packet."]),
        "",
        "## Evidence quality",
        "",
        f"- Used sources: {result['evidence_status']['used_source_count']}",
        f"- Unused sources: {result['evidence_status']['unused_source_count']}",
        f"- Missing evidence items: {result['evidence_status']['missing_evidence_count']}",
        f"- Stale source notes: {result['evidence_status']['stale_source_count']}",
        f"- Contradiction notes: {result['evidence_status']['contradiction_note_count']}",
        "",
        "## Contradictions / stale data",
        "",
        *_bullet_lines(_format_contradiction_note(note) for note in result["contradiction_notes"]),
        *_bullet_lines(_format_staleness_note(note) for note in result["staleness_notes"]),
        *(["- none"] if not result["contradiction_notes"] and not result["staleness_notes"] else []),
        "",
        "## Risks and traps",
        "",
        *_bullet_lines(result["uncertainty_notes"] or ["No uncertainty notes recorded in the local packet."]),
        "",
        "## Paper-only hypothesis for tracking",
        "",
        f"- Safety label: `{result['paper_hypothesis_safety_label']}`",
        f"- Tracked claim: {result['paper_hypothesis']['tracked_claim']}",
        f"- Outcome check: {result['paper_hypothesis']['outcome_check_needed']}",
        "",
        "## What would prove this wrong",
        "",
        *_bullet_lines(result["paper_hypothesis"]["refuting_evidence_needed"]),
        "",
        "## What to check next",
        "",
        *_bullet_lines(result["next_research_questions"]),
        "",
        "## Outcome tracking placeholder",
        "",
        f"- Status: `{result['outcome_tracking_status']['status']}`",
        f"- Required record: `{result['outcome_tracking_status']['required_contract_version']}`",
        "",
        "## Safety boundary",
        "",
        "- Local JSON fixture input only.",
        "- Live network used: false.",
        "- OpenRouter calls performed: 0.",
        "- Polymarket API calls performed: 0.",
        "- Authenticated endpoints used: false.",
        "- Wallet/private-key access: false.",
        "- Orders or trading actions: false.",
        "- Runtime or dispatcher changes: false.",
        "- No real trade decision was produced.",
        "- The paper-only hypothesis is non-executable and for analysis-quality tracking only.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local-only PMBOT one-market analysis.")
    parser.add_argument("--input", required=True, help="Local one-market input JSON.")
    parser.add_argument("--out-json", required=True, help="Output analysis result JSON.")
    parser.add_argument("--out-md", required=True, help="Output Markdown analysis card.")
    args = parser.parse_args(argv)

    run_one_market_analysis(
        input_path=args.input,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


def _validate_source_packets(source_packets: list[Any]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, packet in enumerate(source_packets):
        path = f"input.source_packets[{index}]"
        if not isinstance(packet, Mapping):
            errors.append(f"{path} must be an object")
            continue
        errors.extend(_missing_fields(packet, REQUIRED_SOURCE_PACKET_FIELDS, path))
        for field_name in (
            "captured_at",
            "claim_type",
            "claim_value",
            "evidence_summary",
            "freshness_status",
            "source_id",
            "source_name",
            "source_type",
            "source_url_or_reference",
        ):
            if field_name in packet and not _is_non_empty_string(packet.get(field_name)):
                errors.append(f"{path}.{field_name} must be a non-empty string")
        if "known_limitations" in packet and not _is_string_list(packet.get("known_limitations")):
            errors.append(f"{path}.known_limitations must be a list of strings")
        if "used_in_analysis" in packet and packet.get("used_in_analysis") not in (True, False):
            errors.append(f"{path}.used_in_analysis must be a boolean")
        source_id = packet.get("source_id")
        if isinstance(source_id, str):
            if source_id in seen_ids:
                errors.append(f"{path}.source_id duplicates an earlier source_id")
            seen_ids.add(source_id)
    return errors


def _source_summary(packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "claim_type": _clean_text(packet["claim_type"]),
        "freshness_status": _clean_text(packet["freshness_status"]),
        "source_id": _clean_text(packet["source_id"]),
        "source_name": _clean_text(packet["source_name"]),
        "source_type": _clean_text(packet["source_type"]),
    }


def _source_attribution(packet: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "captured_at": _clean_text(packet["captured_at"]),
        "claim_type": _clean_text(packet["claim_type"]),
        "claim_value": _clean_text(packet["claim_value"]),
        "evidence_summary": _clean_text(packet["evidence_summary"]),
        "freshness_status": _clean_text(packet["freshness_status"]),
        "known_limitations": _clean_string_list(packet["known_limitations"]),
        "source_id": _clean_text(packet["source_id"]),
        "source_name": _clean_text(packet["source_name"]),
        "source_type": _clean_text(packet["source_type"]),
        "source_url_or_reference": _clean_text(packet["source_url_or_reference"]),
        "used_in_analysis": packet["used_in_analysis"] is True,
    }


def _build_staleness_notes(source_packets: list[Mapping[str, Any]]) -> list[dict[str, str]]:
    notes: list[dict[str, str]] = []
    for packet in source_packets:
        freshness_status = str(packet.get("freshness_status", "")).lower().strip()
        if freshness_status in STALE_FRESHNESS_STATUSES:
            notes.append(
                {
                    "freshness_status": _clean_text(packet["freshness_status"]),
                    "note": "Source freshness needs operator review before reuse.",
                    "source_id": _clean_text(packet["source_id"]),
                    "source_name": _clean_text(packet["source_name"]),
                }
            )
    return sorted(notes, key=lambda note: note["source_id"])


def _build_contradiction_notes(source_packets: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, list[dict[str, str]]]] = {}
    for packet in source_packets:
        if packet.get("used_in_analysis") is not True:
            continue
        claim_type = _clean_text(packet["claim_type"])
        claim_value = _clean_text(packet["claim_value"])
        grouped.setdefault(claim_type, {}).setdefault(claim_value, []).append(
            {
                "source_id": _clean_text(packet["source_id"]),
                "source_name": _clean_text(packet["source_name"]),
            }
        )

    notes: list[dict[str, Any]] = []
    for claim_type, values in sorted(grouped.items()):
        if len(values) <= 1:
            continue
        notes.append(
            {
                "claim_type": claim_type,
                "conflicting_values": [
                    {
                        "claim_value": claim_value,
                        "sources": sorted(sources, key=lambda source: source["source_id"]),
                    }
                    for claim_value, sources in sorted(values.items())
                ],
                "note": "Used sources disagree on the same claim type; operator review is required.",
            }
        )
    return notes


def _operator_summary(payload: Mapping[str, Any], evidence_status: Mapping[str, int]) -> str:
    market_title = _clean_text(payload["market_title"])
    context = _clean_text(payload["current_context_summary"])
    return (
        f"Local one-market review for {market_title}. "
        f"{context} "
        f"The packet has {evidence_status['used_source_count']} used source(s), "
        f"{evidence_status['missing_evidence_count']} missing evidence item(s), "
        f"{evidence_status['stale_source_count']} stale source note(s), and "
        f"{evidence_status['contradiction_note_count']} contradiction note(s). "
        "The result is a paper-only analysis record for later outcome review."
    )


def _key_question(payload: Mapping[str, Any]) -> str:
    return "What local evidence would resolve the operator's review of: " + _clean_text(payload["market_title"])


def _paper_hypothesis(
    analysis_id: str,
    payload: Mapping[str, Any],
    sources_used: list[Mapping[str, Any]],
    missing_evidence: list[str],
    uncertainty_notes: list[str],
) -> dict[str, Any]:
    used_source_names = [str(source["source_name"]) for source in sources_used]
    assumptions = used_source_names or ["No used source was recorded in the local packet."]
    if uncertainty_notes:
        assumptions.extend(uncertainty_notes[:3])
    hypothesis = {
        "execution_boundary": "Paper-only review record. It is not a market instruction and cannot be used for orders.",
        "hypothesis_id": f"{analysis_id}.paper_hypothesis",
        "outcome_check_needed": (
            "Later compare the final outcome record with the local rules summary, "
            "resolution source summary, and source attribution."
        ),
        "refuting_evidence_needed": missing_evidence
        or ["A later outcome record shows the local evidence packet omitted a material source."],
        "source_assumptions_to_review": assumptions,
        "supporting_evidence_needed": [
            "Resolution evidence matches the local rules summary.",
            "Used source records remain applicable to the same market and outcome rules.",
            "No material missing evidence changes the qualitative review.",
        ],
        "safety_label": PAPER_HYPOTHESIS_SAFETY_LABEL,
        "tracked_claim": (
            "Track whether the local source-backed analysis remains useful after the market outcome is reviewed."
        ),
    }
    return _clean_nested_strings(hypothesis)


def _next_research_questions(missing_evidence: list[str], uncertainty_notes: list[str]) -> list[str]:
    questions = [f"Collect local evidence for: {item}" for item in missing_evidence]
    questions.extend(f"Clarify uncertainty: {item}" for item in uncertainty_notes[:3])
    if not questions:
        questions.append("Preserve the final outcome record when the market resolves.")
    return [_clean_text(question) for question in questions]


def _format_source_line(source: Mapping[str, Any]) -> str:
    return (
        f"`{source['source_id']}` ({source['source_name']}): "
        f"{source['source_type']}, freshness `{source['freshness_status']}`, claim `{source['claim_type']}`"
    )


def _format_contradiction_note(note: Mapping[str, Any]) -> str:
    values = ", ".join(str(item["claim_value"]) for item in note["conflicting_values"])
    return f"Contradiction on `{note['claim_type']}` across values: {values}"


def _format_staleness_note(note: Mapping[str, str]) -> str:
    return f"Stale source `{note['source_id']}` ({note['source_name']}): `{note['freshness_status']}`"


def _bullet_lines(items: Iterable[str]) -> list[str]:
    return [f"- {item}" for item in items]


def _analysis_id(payload: Mapping[str, Any]) -> str:
    digest_input = {
        "created_at": payload["created_at"],
        "market_id": payload["market_id"],
        "source_packets": payload["source_packets"],
    }
    digest = hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest()[:12]
    return f"{_slug_id(str(payload['market_id']))}.analysis.{digest}"


def _assert_paper_hypothesis_safe(value: Any) -> None:
    hits = _find_forbidden_tokens(value, PAPER_HYPOTHESIS_FORBIDDEN_TOKENS)
    if hits:
        raise OneMarketAnalysisError(("paper_hypothesis contains forbidden tracking terms at: " + ", ".join(hits),))


def _validate_result_shape_for_markdown(result: Mapping[str, Any]) -> None:
    required = (
        "analysis_id",
        "contradiction_notes",
        "evidence_status",
        "key_question",
        "market_id",
        "market_title",
        "missing_evidence",
        "next_research_questions",
        "operator_summary",
        "outcome_tracking_status",
        "paper_hypothesis",
        "paper_hypothesis_safety_label",
        "sources_used",
        "staleness_notes",
        "uncertainty_notes",
    )
    missing = [field for field in required if field not in result]
    if missing:
        raise OneMarketAnalysisError(("analysis result missing fields for markdown: " + ", ".join(missing),))


def _resolve_local_json_path(path: str | Path) -> Path:
    path_string = _normalize_path_string(path)
    if _is_network_like(path_string):
        raise OneMarketAnalysisError((f"input path must be local: {path_string}",))
    candidate = Path(path)
    _reject_sensitive_path(candidate)
    if not candidate.exists():
        raise OneMarketAnalysisError((f"input path does not exist: {path_string}",))
    if not candidate.is_file():
        raise OneMarketAnalysisError((f"input path must be a file: {path_string}",))
    return candidate


def _reject_sensitive_path(path: Path) -> None:
    lowered_parts = {part.lower() for part in path.parts}
    if lowered_parts & SENSITIVE_PATH_PARTS:
        raise OneMarketAnalysisError((f"sensitive input path is not allowed: {_normalize_path_string(path)}",))


def _find_sensitive_markers(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            hits.extend(_find_sensitive_markers(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            hits.extend(_find_sensitive_markers(nested, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in SENSITIVE_TEXT_MARKERS):
            hits.append(path)
    return hits


def _find_forbidden_tokens(value: Any, forbidden_tokens: set[str], path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_path = f"{path}.{key}"
            if _has_token(str(key), forbidden_tokens):
                hits.append(key_path)
            hits.extend(_find_forbidden_tokens(nested, forbidden_tokens, key_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            hits.extend(_find_forbidden_tokens(nested, forbidden_tokens, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_token(value, forbidden_tokens):
        hits.append(path)
    return hits


def _clean_string_list(values: Sequence[str]) -> list[str]:
    return [_clean_text(value) for value in values]


def _clean_nested_strings(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _clean_nested_strings(nested) for key, nested in value.items()}
    if isinstance(value, list):
        return [_clean_nested_strings(nested) for nested in value]
    if isinstance(value, str):
        return _clean_text(value)
    return value


def _clean_text(value: Any) -> str:
    raw = str(value).strip()
    return _replace_forbidden_value_tokens(raw)


def _replace_forbidden_value_tokens(value: str) -> str:
    def replace_match(match: re.Match[str]) -> str:
        token = match.group(0)
        if token.lower() in FORBIDDEN_VALUE_TOKENS:
            return "redacted-token"
        return token

    return re.sub(r"[A-Za-z0-9]+", replace_match, value)


def _missing_fields(payload: Mapping[str, Any], required_fields: Iterable[str], label: str) -> list[str]:
    return [f"{label}.{field} is required" for field in required_fields if field not in payload]


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _is_network_like(value: str) -> bool:
    lowered = value.lower()
    return "://" in lowered or lowered.startswith(("http:", "https:"))


def _has_token(value: str, forbidden_tokens: set[str]) -> bool:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & forbidden_tokens)


def _slug_id(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9_.-]+", "_", value.lower()).strip("_")
    return normalized or "one_market"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _normalize_path_string(path: str | Path) -> str:
    return str(path).replace("\\", "/")


if __name__ == "__main__":
    raise SystemExit(main())
