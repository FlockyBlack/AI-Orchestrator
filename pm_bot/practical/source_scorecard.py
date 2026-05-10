from __future__ import annotations

import argparse
from typing import Any, Mapping, Sequence

from pm_bot.practical.practical_io import GENERATED_AT, bullet_lines, clean_text, load_json_object, safe_summary, write_json, write_text

SOURCE_SCORECARD_CONTRACT_VERSION = "pmbot_source_scorecard.v1"
LABEL_FIELDS = {
    "useful": "useful_count",
    "stale": "stale_count",
    "misleading": "misleading_count",
    "contradictory": "contradictory_count",
    "insufficient": "insufficient_count",
    "unknown": "unknown_count",
}


def build_source_scorecard(ledger: Mapping[str, Any]) -> dict[str, Any]:
    rows = []
    for record in ledger.get("source_records", []):
        if not isinstance(record, Mapping):
            continue
        counts = {field: 0 for field in LABEL_FIELDS.values()}
        label_counts = record.get("source_label_counts")
        if isinstance(label_counts, Mapping):
            for label, field in LABEL_FIELDS.items():
                counts[field] = int(label_counts.get(label, 0))
        else:
            label = clean_text(record.get("usefulness_label") or "unknown")
            counts[LABEL_FIELDS.get(label, "unknown_count")] += 1
        rows.append(
            {
                "source_id": clean_text(record.get("source_id")),
                "source_name": clean_text(record.get("source_name")),
                "markets_used": record.get("markets_used", []),
                **counts,
                "suggested_handling": clean_text(record.get("suggested_future_handling")),
                "notes": clean_text(record.get("observed_issue", "")),
            }
        )
    return {
        "contract_version": SOURCE_SCORECARD_CONTRACT_VERSION,
        "generated_at": GENERATED_AT,
        "source_scorecard": sorted(rows, key=lambda row: row["source_id"]),
        "source_count": len(rows),
        "safety_summary": safe_summary(),
    }


def run_source_scorecard(
    *,
    ledger_path: str,
    out_json_path: str | None = None,
    out_md_path: str | None = None,
) -> dict[str, Any]:
    ledger = load_json_object(ledger_path, label="source learning ledger")
    scorecard = build_source_scorecard(ledger)
    if out_json_path is not None:
        write_json(out_json_path, scorecard)
    if out_md_path is not None:
        write_text(out_md_path, render_source_scorecard_markdown(scorecard))
    return scorecard


def render_source_scorecard_markdown(scorecard: Mapping[str, Any]) -> str:
    lines = [
        "# PMBOT Source Scorecard",
        "",
        f"- Sources: {scorecard['source_count']}",
        "",
        "## Sources",
        "",
    ]
    for row in scorecard["source_scorecard"]:
        lines.append(
            f"- `{row['source_id']}` useful={row['useful_count']} stale={row['stale_count']} "
            f"misleading={row['misleading_count']} contradictory={row['contradictory_count']} "
            f"insufficient={row['insufficient_count']} unknown={row['unknown_count']}"
        )
    lines.extend(
        [
            "",
            "## Safety boundary",
            "",
            "- The scorecard is a transparent local ledger view.",
            "- No autonomous training or trading action is performed.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a source scorecard from a PMBOT source learning ledger.")
    parser.add_argument("--ledger", required=True, help="Local source learning ledger JSON.")
    parser.add_argument("--out-json", required=True, help="Output scorecard JSON.")
    parser.add_argument("--out-md", required=True, help="Output scorecard Markdown.")
    args = parser.parse_args(argv)
    run_source_scorecard(ledger_path=args.ledger, out_json_path=args.out_json, out_md_path=args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
