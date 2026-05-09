from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from pm_bot.practical.one_market_analysis import _canonical_json, _clean_text, _is_network_like, _normalize_path_string
from pm_bot.practical.paper_feedback import FEEDBACK_RESULT_CONTRACT_VERSION, PaperFeedbackError

LEDGER_CONTRACT_VERSION = "pmbot_source_learning_ledger.v1"
DEFAULT_LEDGER_JSON_PATH = "pm_bot/practical/artifacts/source_learning_ledger_sample_001.result.json"
DEFAULT_LEDGER_MD_PATH = "pm_bot/practical/artifacts/source_learning_ledger_sample_001.md"
GENERATED_AT = "2026-05-10T00:00:00Z"
USEFULNESS_PRIORITY = (
    "misleading",
    "contradictory",
    "stale",
    "insufficient",
    "useful",
    "unused",
    "unknown",
)


class SourceLearningError(ValueError):
    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


def load_feedback_result(path: str | Path) -> dict[str, Any]:
    path_string = _normalize_path_string(path)
    if _is_network_like(path_string):
        raise SourceLearningError((f"feedback path must be local: {path_string}",))
    path_obj = Path(path)
    if not path_obj.exists():
        raise SourceLearningError((f"feedback path does not exist: {path_string}",))
    payload = json.loads(path_obj.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SourceLearningError(("feedback JSON must be an object",))
    if payload.get("contract_version") != FEEDBACK_RESULT_CONTRACT_VERSION:
        raise SourceLearningError((f"feedback.contract_version must be {FEEDBACK_RESULT_CONTRACT_VERSION}",))
    return payload


def build_source_learning_ledger(
    feedback_results: Sequence[Mapping[str, Any]],
    *,
    generated_artifact_paths: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    if not feedback_results:
        raise SourceLearningError(("at least one feedback result is required",))

    artifact_paths = {
        "source_learning_ledger_json": DEFAULT_LEDGER_JSON_PATH,
        "source_learning_ledger_markdown": DEFAULT_LEDGER_MD_PATH,
    }
    if generated_artifact_paths:
        artifact_paths.update(dict(generated_artifact_paths))

    for index, feedback in enumerate(feedback_results):
        if feedback.get("contract_version") != FEEDBACK_RESULT_CONTRACT_VERSION:
            raise SourceLearningError((f"feedback_results[{index}].contract_version must be {FEEDBACK_RESULT_CONTRACT_VERSION}",))

    source_records = _source_records(feedback_results)
    summary = dict(sorted(Counter(record["usefulness_label"] for record in source_records).items()))
    failure_patterns = _source_failure_patterns(source_records)
    feedback_ids = sorted(_clean_text(feedback["feedback_id"]) for feedback in feedback_results)
    market_ids = sorted({_clean_text(feedback["market_id"]) for feedback in feedback_results})
    ledger_id = _ledger_id(feedback_results)
    ledger = {
        "analysis_prompt_improvement_notes": _analysis_prompt_improvement_notes(feedback_results),
        "contract_version": LEDGER_CONTRACT_VERSION,
        "generated_artifacts": dict(sorted(artifact_paths.items())),
        "generated_at": GENERATED_AT,
        "input_feedback_ids": feedback_ids,
        "ledger_id": ledger_id,
        "market_ids": market_ids,
        "no_autonomous_training_performed": True,
        "no_real_trade_decision": True,
        "recommended_source_handling_updates": _recommended_source_handling_updates(source_records),
        "source_failure_patterns": failure_patterns,
        "source_records": source_records,
        "source_usefulness_summary": summary,
    }
    return ledger


def run_source_learning(
    *,
    feedback_paths: Sequence[str | Path],
    out_json_path: str | Path | None = None,
    out_md_path: str | Path | None = None,
) -> dict[str, Any]:
    feedback_results = [load_feedback_result(path) for path in feedback_paths]
    artifact_paths = {}
    if out_json_path is not None:
        artifact_paths["source_learning_ledger_json"] = _normalize_path_string(out_json_path)
    if out_md_path is not None:
        artifact_paths["source_learning_ledger_markdown"] = _normalize_path_string(out_md_path)
    ledger = build_source_learning_ledger(feedback_results, generated_artifact_paths=artifact_paths)
    if out_json_path is not None:
        _write_json(Path(out_json_path), ledger)
    if out_md_path is not None:
        _write_text(Path(out_md_path), render_source_learning_markdown(ledger))
    return ledger


def render_source_learning_markdown(ledger: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Source Learning Ledger",
        "",
        f"- Ledger ID: `{ledger['ledger_id']}`",
        f"- Generated at: `{ledger['generated_at']}`",
        f"- Feedback records: {len(ledger['input_feedback_ids'])}",
        f"- Markets: {len(ledger['market_ids'])}",
        "",
        "## Source usefulness summary",
        "",
        *_bullet_lines(f"`{label}`: {count}" for label, count in ledger["source_usefulness_summary"].items()),
        "",
        "## Source records",
        "",
        *_bullet_lines(_format_source_record(record) for record in ledger["source_records"]),
        "",
        "## Source failure patterns",
        "",
        *_bullet_lines(ledger["source_failure_patterns"] or ["No source failure pattern recorded."]),
        "",
        "## Recommended source handling updates",
        "",
        *_bullet_lines(ledger["recommended_source_handling_updates"]),
        "",
        "## Analysis prompt improvement notes",
        "",
        *_bullet_lines(ledger["analysis_prompt_improvement_notes"]),
        "",
        "## Safety",
        "",
        "- No autonomous training was performed.",
        "- No real trade decision was produced.",
        "- Source learning is a transparent ledger update from local feedback artifacts only.",
    ]
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build local PMBOT source learning ledger from feedback.")
    parser.add_argument(
        "--feedback",
        required=True,
        action="append",
        help="Local feedback JSON. Repeat for more than one feedback result.",
    )
    parser.add_argument("--out-json", required=True, help="Output source learning ledger JSON.")
    parser.add_argument("--out-md", required=True, help="Output source learning ledger Markdown.")
    args = parser.parse_args(argv)

    run_source_learning(
        feedback_paths=args.feedback,
        out_json_path=args.out_json,
        out_md_path=args.out_md,
    )
    return 0


def _source_records(feedback_results: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for feedback in feedback_results:
        for row in feedback.get("source_contribution_review", []):
            if isinstance(row, Mapping) and isinstance(row.get("source_id"), str):
                record = dict(row)
                record["market_id"] = feedback["market_id"]
                grouped[row["source_id"]].append(record)

    records: list[dict[str, Any]] = []
    for source_id, rows in sorted(grouped.items()):
        labels = [str(row.get("usefulness_label", "unknown")) for row in rows]
        label = _dominant_label(labels)
        records.append(
            {
                "evidence_role": _join_unique(row.get("evidence_role", "unknown") for row in rows),
                "markets_used": sorted({_clean_text(row["market_id"]) for row in rows}),
                "observed_issue": _join_unique(row.get("observed_issue", "No issue recorded.") for row in rows),
                "source_id": _clean_text(source_id),
                "source_name": _clean_text(rows[0].get("source_name", source_id)),
                "suggested_future_handling": _join_unique(
                    row.get("suggested_future_handling", "Keep pending operator review.") for row in rows
                ),
                "usefulness_label": label,
            }
        )
    return records


def _dominant_label(labels: Sequence[str]) -> str:
    label_set = set(labels)
    for label in USEFULNESS_PRIORITY:
        if label in label_set:
            return label
    return "unknown"


def _source_failure_patterns(records: Sequence[Mapping[str, Any]]) -> list[str]:
    patterns: list[str] = []
    counts = Counter(record["usefulness_label"] for record in records)
    for label in ("misleading", "contradictory", "stale", "insufficient", "unused", "unknown"):
        if counts.get(label):
            patterns.append(f"{counts[label]} source record(s) labeled {label}.")
    return patterns


def _recommended_source_handling_updates(records: Sequence[Mapping[str, Any]]) -> list[str]:
    labels = {str(record["usefulness_label"]) for record in records}
    updates: list[str] = []
    if "stale" in labels:
        updates.append("Require freshness review before using stale source packets again.")
    if "contradictory" in labels:
        updates.append("Keep contradictory source claims visible in the operator card.")
    if "misleading" in labels:
        updates.append("Add a source-claim versus reasoning-step check for misleading records.")
    if "insufficient" in labels:
        updates.append("Pair insufficient sources with explicit missing-evidence checks.")
    if "unused" in labels:
        updates.append("Keep unused sources separate from sources that supported the analysis.")
    if not updates:
        updates.append("Preserve source attribution and limitation fields for future feedback review.")
    return updates


def _analysis_prompt_improvement_notes(feedback_results: Sequence[Mapping[str, Any]]) -> list[str]:
    notes: set[str] = set()
    for feedback in feedback_results:
        for note in feedback.get("next_prompt_improvements", []):
            notes.add(_clean_text(note))
    return sorted(notes) or ["No prompt improvement note recorded."]


def _ledger_id(feedback_results: Sequence[Mapping[str, Any]]) -> str:
    digest_input = {
        "feedback_ids": sorted(str(feedback["feedback_id"]) for feedback in feedback_results),
        "market_ids": sorted(str(feedback["market_id"]) for feedback in feedback_results),
    }
    digest = hashlib.sha256(_canonical_json(digest_input).encode("utf-8")).hexdigest()[:12]
    return f"source_learning_ledger.{digest}"


def _format_source_record(record: Mapping[str, Any]) -> str:
    return (
        f"`{record['source_id']}` ({record['source_name']}): "
        f"`{record['usefulness_label']}` across {len(record['markets_used'])} market(s)."
    )


def _join_unique(values: Iterable[Any]) -> str:
    cleaned = sorted({_clean_text(value) for value in values if str(value)})
    return "; ".join(cleaned)


def _bullet_lines(items: Iterable[str]) -> list[str]:
    return [f"- {item}" for item in items]


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
