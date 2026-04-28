import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.raw_artifacts.validate_raw_market_artifacts import (
    EXPECTED_CONTRACT_VERSION,
    build_validation_report,
    validate_artifact,
)


DEFAULT_FIXTURES_DIR = ROOT / "pm_bot" / "raw_artifacts" / "fixtures"
MANIFEST_VERSION = "raw_ingestion_manifest.v1"
NEXT_ALLOWED_STAGE = "design_only_normalization_contract"


def _load_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _iter_fixture_files(fixtures_dir):
    return sorted(path for path in fixtures_dir.rglob("*.json") if path.is_file())


def _relative_fixture_path(path, fixtures_dir):
    return str(path.resolve().relative_to(fixtures_dir.resolve())).replace("\\", "/")


def _artifact_id_or_none(payload):
    value = payload.get("artifact_id") if isinstance(payload, dict) else None
    if isinstance(value, str) and value.strip():
        return value
    return None


def _market_id_or_none(payload):
    market = payload.get("market") if isinstance(payload, dict) else None
    value = market.get("market_id") if isinstance(market, dict) else None
    if isinstance(value, str) and value.strip():
        return value
    return None


def _reasons_from_findings(findings):
    return [
        {
            "code": item["code"],
            "severity": item["severity"],
            "message": item["message"],
        }
        for item in findings
    ]


def build_ingestion_manifest(fixtures_dir):
    fixtures_dir = Path(fixtures_dir).resolve()
    report = build_validation_report(fixtures_dir)
    accepted_artifacts = []
    quarantined_artifacts = []
    findings_by_file = {}

    for item in report["quarantine_findings"]:
        findings_by_file.setdefault(item["file"], []).append(item)

    if fixtures_dir.exists():
        for path in _iter_fixture_files(fixtures_dir):
            relative_path = _relative_fixture_path(path, fixtures_dir)
            payload = _load_json(path)
            findings = validate_artifact(payload, relative_path)
            if findings:
                quarantined_artifacts.append(
                    {
                        "file": relative_path,
                        "artifact_id": _artifact_id_or_none(payload),
                        "reasons": _reasons_from_findings(findings),
                        "handoff_ready_for_normalization": False,
                    }
                )
                continue

            accepted_artifacts.append(
                {
                    "artifact_id": payload["artifact_id"],
                    "file": relative_path,
                    "market_id": payload["market"]["market_id"],
                    "source_type": payload["source_type"],
                    "captured_at": payload["captured_at"],
                    "outcome_count": len(payload["outcomes"]),
                    "handoff_ready_for_normalization": True,
                }
            )
    elif findings_by_file:
        for file_name in sorted(findings_by_file):
            quarantined_artifacts.append(
                {
                    "file": file_name,
                    "artifact_id": None,
                    "reasons": _reasons_from_findings(findings_by_file[file_name]),
                    "handoff_ready_for_normalization": False,
                }
            )

    accepted_artifacts.sort(key=lambda item: item["file"])
    quarantined_artifacts.sort(key=lambda item: item["file"])

    return {
        "manifest_version": MANIFEST_VERSION,
        "source_contract_version": EXPECTED_CONTRACT_VERSION,
        "fixtures_dir": report["fixtures_dir"],
        "validation_passed": report["validation_passed"],
        "accepted_artifacts": accepted_artifacts,
        "quarantined_artifacts": quarantined_artifacts,
        "counts": {
            "checked_files": report["checked_files_count"],
            "accepted": len(accepted_artifacts),
            "quarantined": len(quarantined_artifacts),
            "unexpected_failures": len(report["unexpected_failures"]),
            "unexpected_passes": len(report["unexpected_passes"]),
        },
        "safety_summary": report["safety_summary"],
        "next_allowed_stage": NEXT_ALLOWED_STAGE,
        "live_fetcher_implemented": False,
        "normalization_implemented": False,
        "runtime_wiring_added": False,
    }


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Build an offline ingestion manifest from local raw artifact fixtures.")
    parser.add_argument("--fixtures-dir", default=str(DEFAULT_FIXTURES_DIR))
    parser.add_argument("--write-manifest")
    return parser.parse_args(argv)


def main(argv):
    args = _parse_args(argv)
    fixtures_dir = Path(args.fixtures_dir)
    if not fixtures_dir.is_absolute():
        fixtures_dir = (ROOT / fixtures_dir).resolve()
    manifest = build_ingestion_manifest(fixtures_dir)
    rendered = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    if args.write_manifest:
        output_path = Path(args.write_manifest)
        if not output_path.is_absolute():
            output_path = (ROOT / output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if manifest["validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
