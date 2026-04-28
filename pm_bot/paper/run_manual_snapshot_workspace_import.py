import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path


TASK_ID = "PMBOT-BRAIN-028-MANUAL-SNAPSHOT-WORKSPACE-IMPORT"
WORKFLOW = "manual_snapshot_workspace_import"
SCHEMA_VERSION = "v1"
SAFETY_FLAGS = {
    "offline_only": True,
    "paper_only": True,
    "live_fetcher_implemented": False,
    "api_used": False,
    "network_used": False,
    "wallet_used": False,
    "real_order_created": False,
    "trading_allowed": False,
    "runtime_wiring_changed": False,
    "prompt_automation_added": False,
}


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Import manually saved local snapshot files into the paper workspace inbox.")
    parser.add_argument("--source", default=None)
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--out-manifest", default=None)
    parser.add_argument("--write-inbox", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _workspace_paths(root: Path, workspace_path=None):
    workspace = Path(workspace_path) if workspace_path else root / "pm_bot" / "paper" / "manual_paper_workspace"
    return {
        "workspace": workspace,
        "inbox": workspace / "inbox",
    }


def _source_path(root: Path, source_path=None):
    return Path(source_path) if source_path else root / "pm_bot" / "paper" / "manual_snapshot_import_source"


def _discover_inputs(source: Path):
    if source.is_file():
        return [source]
    if source.is_dir():
        return sorted(
            (item for item in source.iterdir() if not item.name.endswith(".fixture.json")),
            key=lambda item: item.name,
        )
    return [source]


def _record_base(path: Path, status, reason_code=None, reason=None, digest=None, snapshot_id=None, observed_at=None):
    return {
        "input_path": str(path),
        "file_name": path.name,
        "status": status,
        "reason_code": reason_code,
        "reason": reason,
        "sha256": digest,
        "snapshot_id": snapshot_id,
        "observed_at": observed_at,
    }


def _skip_record(path: Path, status, reason_code, reason, action_taken, digest=None, snapshot_id=None, observed_at=None):
    row = _record_base(path, status, reason_code, reason, digest, snapshot_id, observed_at)
    row["action_taken"] = action_taken
    return row


def _safe_snapshot_id(snapshot_id):
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", str(snapshot_id)).strip("._-")
    return value or "snapshot"


def _json_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return []
        return parsed if isinstance(parsed, list) else []
    return []


def _float_or_none(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _first_present(row, *keys):
    for key in keys:
        value = row.get(key)
        if value is not None:
            return value
    return None


def _polymarket_market_rows(payload):
    if isinstance(payload, list):
        return payload, {}
    if isinstance(payload, dict):
        for key in ("markets", "data", "results"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return rows, payload
    return None, None


def _looks_like_polymarket_markets_payload(payload):
    rows, _metadata = _polymarket_market_rows(payload)
    if not isinstance(rows, list) or not rows:
        return False
    for row in rows:
        if not isinstance(row, dict):
            continue
        has_identity = row.get("id") is not None or row.get("conditionId") is not None
        has_market_shape = any(key in row for key in ("question", "title", "outcomes", "outcomePrices", "clobTokenIds"))
        if has_identity and has_market_shape:
            return True
    return False


def _polymarket_timestamp(metadata, rows):
    for key in ("captured_at", "capturedAt", "observed_at", "observedAt"):
        value = metadata.get(key) if isinstance(metadata, dict) else None
        if value:
            return str(value)
    candidates = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key in ("updatedAt", "createdAt", "acceptingOrdersTimestamp"):
            value = row.get(key)
            if value:
                candidates.append(str(value))
    return sorted(candidates)[-1] if candidates else "1970-01-01T00:00:00Z"


def _polymarket_tags(market):
    tags = []
    for value in _json_list(market.get("tags")):
        if isinstance(value, dict):
            label = value.get("label") or value.get("name") or value.get("slug") or value.get("id")
            if label is not None:
                tags.append(str(label))
        elif value is not None:
            tags.append(str(value))
    return tags


def _polymarket_category(market):
    category = market.get("category")
    if category is not None:
        return str(category)
    events = _json_list(market.get("events"))
    for event in events:
        if isinstance(event, dict):
            title = event.get("title") or event.get("slug")
            if title:
                return str(title)
    return "polymarket"


def _polymarket_outcomes(market):
    names = _json_list(market.get("outcomes"))
    prices = _json_list(market.get("outcomePrices"))
    token_ids = _json_list(market.get("clobTokenIds"))
    outcome_count = max(len(names), len(prices), len(token_ids))
    outcomes = []
    tokens = []
    for index in range(outcome_count):
        name = names[index] if index < len(names) else f"Outcome {index + 1}"
        price = _float_or_none(prices[index]) if index < len(prices) else None
        token_id = token_ids[index] if index < len(token_ids) else None
        outcome = {"name": str(name)}
        token = {"name": str(name)}
        if price is not None:
            outcome["price"] = price
            token["price"] = price
        if token_id is not None:
            outcome["token_id"] = str(token_id)
            token["token_id"] = str(token_id)
        outcomes.append(outcome)
        tokens.append(token)
    return outcomes, tokens


def _polymarket_market_to_canonical(market):
    if not isinstance(market, dict):
        return None
    market_id = _first_present(market, "id", "marketId", "market_id", "conditionId", "condition_id")
    condition_id = _first_present(market, "conditionId", "condition_id", "id", "marketId", "market_id")
    question = _first_present(market, "question", "title")
    if market_id is None or condition_id is None or question is None:
        return None

    outcomes, tokens = _polymarket_outcomes(market)
    liquidity_num = _float_or_none(_first_present(market, "liquidityNum", "liquidity_num", "liquidity"))
    volume_num = _float_or_none(_first_present(market, "volumeNum", "volume_num", "volume"))
    best_bid = _float_or_none(_first_present(market, "bestBid", "best_bid"))
    best_ask = _float_or_none(_first_present(market, "bestAsk", "best_ask"))
    spread = _float_or_none(market.get("spread"))
    if spread is None and best_bid is not None and best_ask is not None:
        spread = round(best_ask - best_bid, 4)

    row = {
        "condition_id": str(condition_id),
        "market_id": str(market_id),
        "question": str(question),
        "title": str(_first_present(market, "title", "question")),
        "slug": str(market.get("slug")) if market.get("slug") is not None else None,
        "category": _polymarket_category(market),
        "tags": _polymarket_tags(market),
        "active": bool(market.get("active")) if market.get("active") is not None else None,
        "closed": bool(market.get("closed")) if market.get("closed") is not None else None,
        "end_date_iso": _first_present(market, "endDateIso", "end_date_iso", "endDate", "end_date"),
        "outcomes": outcomes,
        "tokens": tokens,
        "outcome_prices": [row["price"] for row in outcomes if row.get("price") is not None],
        "liquidity_num": liquidity_num,
        "volume_num": volume_num,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread": spread,
        "updated_at": market.get("updatedAt"),
        "created_at": market.get("createdAt"),
        "source_shape": "polymarket_gamma_markets_response",
    }
    if outcomes:
        for outcome in outcomes:
            if outcome["name"].lower() == "yes" and outcome.get("price") is not None:
                row["yes_price"] = outcome["price"]
                break
    return {key: value for key, value in row.items() if value is not None}


def _polymarket_markets_snapshot_entry(path: Path, payload):
    if not _looks_like_polymarket_markets_payload(payload):
        return None, None
    rows, metadata = _polymarket_market_rows(payload)
    markets = []
    unsupported = 0
    for row in rows:
        market = _polymarket_market_to_canonical(row)
        if market is None:
            unsupported += 1
        else:
            markets.append(market)
    if not markets:
        return None, {
            "source_shape": "polymarket_gamma_markets_response",
            "source_market_count": len(rows),
            "supported_market_count": 0,
            "unsupported_market_count": unsupported,
            "skipped_market_count": unsupported,
        }
    metadata_id = _first_present(metadata, "snapshot_id", "id") if isinstance(metadata, dict) else None
    source_id = metadata_id if metadata_id is not None else path.stem.removesuffix(".fixture")
    snapshot_id = _safe_snapshot_id(source_id)
    observed_at = _polymarket_timestamp(metadata, rows)
    summary = {
        "source_shape": "polymarket_gamma_markets_response",
        "source_market_count": len(rows),
        "supported_market_count": len(markets),
        "unsupported_market_count": unsupported,
        "skipped_market_count": unsupported,
        "captured_at": observed_at,
    }
    return {
        "snapshot_id": snapshot_id,
        "observed_at": observed_at,
        "captured_at": observed_at,
        "snapshot": {
            "schema_version": "v1",
            "fixture_id": f"{snapshot_id}_polymarket_gamma_markets",
            "source_shape": "polymarket_gamma_markets_response",
            "source_market_count": len(rows),
            "supported_market_count": len(markets),
            "unsupported_market_count": unsupported,
            "markets": markets,
        },
        "observed_prices": {
            row["condition_id"]: row["yes_price"]
            for row in markets
            if row.get("yes_price") is not None
        },
        "current_prices": {},
        "settlements": [],
    }, summary


def _existing_prefix_max(inbox: Path):
    maximum = 0
    if not inbox.exists():
        return maximum
    for path in inbox.iterdir():
        match = re.match(r"^(\d+)_", path.name)
        if match:
            maximum = max(maximum, int(match.group(1)))
    return maximum


def _canonical_inbox_name(index, snapshot_id):
    return f"{index:03d}_{_safe_snapshot_id(snapshot_id)}.json"


def _workspace_snapshot_ids(inbox: Path, workspace_helpers):
    snapshot_ids = set()
    if not inbox.exists():
        return snapshot_ids
    for path in sorted(inbox.glob("*.json"), key=lambda item: item.name):
        try:
            payload = _load_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        snapshot = workspace_helpers._extract_snapshot(payload)
        if snapshot is not None and snapshot.get("snapshot_id") is not None:
            snapshot_ids.add(str(snapshot["snapshot_id"]))
    return snapshot_ids


def _snapshot_market_count(snapshot_entry):
    snapshot = snapshot_entry.get("snapshot")
    markets = snapshot.get("markets") if isinstance(snapshot, dict) else None
    return len(markets) if isinstance(markets, list) else None


def _adapter_summary(adapter, snapshot_entry):
    snapshot = snapshot_entry.get("snapshot")
    markets = snapshot.get("markets") if isinstance(snapshot, dict) else None
    if not isinstance(markets, list):
        return {
            "checked": False,
            "snapshot_markets": 0,
            "adapted_raw_markets": 0,
            "adapter_rejections": 0,
            "rejection_reason_counts": {},
        }
    adapted = 0
    reason_counts = {}
    for market in markets:
        _raw, rejection = adapter._adapt_snapshot(market)
        if rejection is None:
            adapted += 1
        else:
            code = rejection["reason_code"]
            reason_counts[code] = reason_counts.get(code, 0) + 1
    return {
        "checked": True,
        "snapshot_markets": len(markets),
        "adapted_raw_markets": adapted,
        "adapter_rejections": len(markets) - adapted,
        "rejection_reason_counts": dict(sorted(reason_counts.items())),
    }


def _is_supported_snapshot(snapshot_entry):
    if not isinstance(snapshot_entry, dict):
        return False
    if not snapshot_entry.get("snapshot_id") or not snapshot_entry.get("observed_at"):
        return False
    snapshot = snapshot_entry.get("snapshot")
    if not isinstance(snapshot, dict):
        return False
    markets = snapshot.get("markets")
    return isinstance(markets, list)


def _reason_counts(records):
    counts = {}
    for record in records:
        reason_code = record["reason_code"]
        counts[reason_code] = counts.get(reason_code, 0) + 1
    return dict(sorted(counts.items()))


def _classify_source(root: Path, source: Path, inbox: Path):
    paper_dir = root / "pm_bot" / "paper"
    scoring_dir = root / "pm_bot" / "scoring"
    workspace_helpers = _load_module(paper_dir / "run_manual_paper_workspace.py", "pmbot_snapshot_import_workspace")
    adapter = _load_module(scoring_dir / "adapt_live_shaped_crypto_snapshot.py", "pmbot_snapshot_import_adapter")
    existing_ids = _workspace_snapshot_ids(inbox, workspace_helpers)
    discovered = []
    importable = []
    skipped = []
    seen_ids = set()

    for path in _discover_inputs(source):
        digest = None
        snapshot_id = None
        observed_at = None
        if not path.exists() or not path.is_file():
            skipped.append(_skip_record(
                path,
                "quarantined",
                "unreadable_input",
                "Manual snapshot input is not a readable regular file.",
                "No inbox file written.",
            ))
            discovered.append(_record_base(path, "quarantined", "unreadable_input", "Manual snapshot input is not a readable regular file."))
            continue
        try:
            digest = workspace_helpers._file_sha256(path)
        except OSError as exc:
            skipped.append(_skip_record(
                path,
                "quarantined",
                "unreadable_input",
                f"Unable to read manual snapshot input: {exc}",
                "No inbox file written.",
            ))
            discovered.append(_record_base(path, "quarantined", "unreadable_input", f"Unable to read manual snapshot input: {exc}"))
            continue
        if path.suffix.lower() != ".json":
            skipped.append(_skip_record(
                path,
                "skipped",
                "ignored_non_json_file",
                "Manual snapshot input is not a JSON file.",
                "Ignored before import.",
                digest,
            ))
            discovered.append(_record_base(path, "skipped", "ignored_non_json_file", "Manual snapshot input is not a JSON file.", digest))
            continue
        try:
            payload = _load_json(path)
        except json.JSONDecodeError as exc:
            reason = f"JSON parse failed at line {exc.lineno}, column {exc.colno}."
            skipped.append(_skip_record(path, "quarantined", "malformed_json", reason, "No inbox file written.", digest))
            discovered.append(_record_base(path, "quarantined", "malformed_json", reason, digest))
            continue
        conversion_summary = None
        snapshot_entry = workspace_helpers._extract_snapshot(payload)
        if snapshot_entry is None:
            snapshot_entry, conversion_summary = _polymarket_markets_snapshot_entry(path, payload)
        snapshot_id = workspace_helpers._snapshot_id_from_payload(payload)
        if snapshot_entry is not None:
            if snapshot_id is None:
                snapshot_id = snapshot_entry.get("snapshot_id")
            observed_at = snapshot_entry.get("observed_at")
        if snapshot_entry is None or not _is_supported_snapshot(snapshot_entry):
            skipped.append(_skip_record(
                path,
                "quarantined",
                "unsupported_snapshot_shape",
                "JSON payload is not a supported single manual snapshot file.",
                "No inbox file written.",
                digest,
                snapshot_id,
                observed_at,
            ))
            discovered.append(_record_base(path, "quarantined", "unsupported_snapshot_shape", "JSON payload is not a supported single manual snapshot file.", digest, snapshot_id, observed_at))
            continue
        snapshot_id = str(snapshot_entry["snapshot_id"])
        observed_at = snapshot_entry["observed_at"]
        if snapshot_id in seen_ids:
            skipped.append(_skip_record(
                path,
                "skipped",
                "duplicate_snapshot_id_in_source_batch",
                "Snapshot ID was already accepted from another source file in this import batch.",
                "No inbox file written.",
                digest,
                snapshot_id,
                observed_at,
            ))
            discovered.append(_record_base(path, "skipped", "duplicate_snapshot_id_in_source_batch", "Snapshot ID was already accepted from another source file in this import batch.", digest, snapshot_id, observed_at))
            continue
        seen_ids.add(snapshot_id)
        if snapshot_id in existing_ids:
            skipped.append(_skip_record(
                path,
                "skipped",
                "already_present_in_workspace_inbox",
                "Snapshot ID is already present in the workspace inbox.",
                "No inbox file written.",
                digest,
                snapshot_id,
                observed_at,
            ))
            discovered.append(_record_base(path, "skipped", "already_present_in_workspace_inbox", "Snapshot ID is already present in the workspace inbox.", digest, snapshot_id, observed_at))
            continue
        record = {
            **_record_base(path, "importable", None, None, digest, snapshot_id, observed_at),
            "snapshot_markets": _snapshot_market_count(snapshot_entry),
            "adapter_summary": _adapter_summary(adapter, snapshot_entry),
            "payload": snapshot_entry,
        }
        if conversion_summary is not None:
            record.update(conversion_summary)
        importable.append(record)
        discovered.append({key: value for key, value in record.items() if key != "payload"})

    importable.sort(key=lambda row: (row["observed_at"], row["snapshot_id"], row["file_name"]))
    return discovered, importable, skipped


def _public_import_record(record, inbox_path: Path, file_name, write_inbox, written):
    row = {
        "input_path": record["input_path"],
        "file_name": record["file_name"],
        "status": "imported" if written else "importable",
        "sha256": record["sha256"],
        "snapshot_id": record["snapshot_id"],
        "observed_at": record["observed_at"],
        "snapshot_markets": record["snapshot_markets"],
        "adapter_summary": record["adapter_summary"],
        "canonical_inbox_file_name": file_name,
        "canonical_inbox_path": str(inbox_path / file_name),
        "write_inbox": write_inbox,
        "written": written,
    }
    for key in (
        "source_shape",
        "source_market_count",
        "supported_market_count",
        "unsupported_market_count",
        "skipped_market_count",
        "captured_at",
    ):
        if key in record:
            row[key] = record[key]
    return row


def _materialize_imports(importable, inbox: Path, write_inbox):
    output_files = []
    imported_records = []
    skipped_late = []
    next_index = _existing_prefix_max(inbox) + 1
    reserved_names = set()

    for record in importable:
        file_name = _canonical_inbox_name(next_index, record["snapshot_id"])
        next_index += 1
        target = inbox / file_name
        if file_name in reserved_names or target.exists():
            skipped_late.append(_skip_record(
                Path(record["input_path"]),
                "skipped",
                "canonical_inbox_file_already_exists",
                "Canonical inbox file path already exists.",
                "No inbox file written.",
                record["sha256"],
                record["snapshot_id"],
                record["observed_at"],
            ))
            continue
        reserved_names.add(file_name)
        written = False
        if write_inbox:
            inbox.mkdir(parents=True, exist_ok=True)
            if target.exists():
                skipped_late.append(_skip_record(
                    Path(record["input_path"]),
                    "skipped",
                    "canonical_inbox_file_already_exists",
                    "Canonical inbox file path already exists.",
                    "No inbox file written.",
                    record["sha256"],
                    record["snapshot_id"],
                    record["observed_at"],
                ))
                continue
            _write_json(target, record["payload"])
            written = True
            output_files.append({
                "file_name": file_name,
                "path": str(target),
                "snapshot_id": record["snapshot_id"],
                "observed_at": record["observed_at"],
                "sha256": record["sha256"],
            })
        imported_records.append(_public_import_record(record, inbox, file_name, write_inbox, written))
    return imported_records, skipped_late, output_files


def build_manual_snapshot_workspace_import(root: Path, source_path=None, workspace_path=None, out_manifest_path=None, write_inbox=False):
    source = _source_path(root, source_path)
    paths = _workspace_paths(root, workspace_path)
    discovered, importable, skipped = _classify_source(root, source, paths["inbox"])
    imported_records, late_skipped, output_files = _materialize_imports(importable, paths["inbox"], write_inbox)
    skipped_records = skipped + late_skipped
    summary = {
        "discovered_inputs": len(discovered),
        "importable_snapshots": len(imported_records),
        "imported_snapshots": len([row for row in imported_records if row["written"]]),
        "skipped_or_quarantined_inputs": len(skipped_records),
        "reason_counts": _reason_counts(skipped_records),
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "workflow": WORKFLOW,
        "deterministic": True,
        "source_path": str(source),
        "workspace_path": str(paths["workspace"]),
        "inbox_path": str(paths["inbox"]),
        "write_inbox": bool(write_inbox),
        "discovered_inputs": discovered,
        "imported_records": imported_records,
        "skipped_quarantined_records": skipped_records,
        "reason_counts": summary["reason_counts"],
        "output_inbox_files": output_files,
        "summary": summary,
        "safety_flags": {
            **SAFETY_FLAGS,
            "default_read_only": not write_inbox,
            "manifest_write_requested": bool(out_manifest_path),
        },
        "limitations": [
            "Uses deterministic local manual snapshot files only; no live fetcher, network, external API, credentials, wallet access, real orders, or live trading is included.",
            "Default run is read-only and writes inbox files only when --write-inbox is provided.",
            "No runtime integration, command-routing changes, prompt automation, broad refactor, or new validation layer is included.",
        ],
    }
    if out_manifest_path:
        _write_json(Path(out_manifest_path), manifest)
    return {
        **manifest,
        "manifest_path": str(Path(out_manifest_path)) if out_manifest_path else None,
        "manifest_written": bool(out_manifest_path),
    }


def render_markdown(report):
    summary = report["summary"]
    lines = [
        "# Manual Snapshot Workspace Import",
        "",
        f"- Source: {report['source_path']}",
        f"- Workspace: {report['workspace_path']}",
        f"- Inbox: {report['inbox_path']}",
        f"- Write inbox: {str(report['write_inbox']).lower()}",
        f"- Manifest path: {report['manifest_path'] or ''}",
        f"- Manifest written: {str(report['manifest_written']).lower()}",
        f"- Inputs discovered: {summary['discovered_inputs']}",
        f"- Importable snapshots: {summary['importable_snapshots']}",
        f"- Imported snapshots: {summary['imported_snapshots']}",
        f"- Skipped/quarantined inputs: {summary['skipped_or_quarantined_inputs']}",
        f"- Reason counts: {json.dumps(summary['reason_counts'], sort_keys=True)}",
        "",
        "## Importable",
        "",
    ]
    if report["imported_records"]:
        for row in report["imported_records"]:
            lines.append(
                f"- {row['file_name']}: {row['snapshot_id']} -> {row['canonical_inbox_file_name']} "
                f"written={str(row['written']).lower()}"
            )
    else:
        lines.append("- None")
    lines.extend(["", "## Skipped And Quarantined", ""])
    if report["skipped_quarantined_records"]:
        for row in report["skipped_quarantined_records"]:
            lines.append(f"- {row['file_name']}: {row['status']} {row['reason_code']} ({row['action_taken']})")
    else:
        lines.append("- None")
    lines.extend(["", "## Output Inbox Files", ""])
    if report["output_inbox_files"]:
        for row in report["output_inbox_files"]:
            lines.append(f"- {row['file_name']}: {row['path']}")
    else:
        lines.append("- None written")
    lines.extend([
        "",
        "## Safety",
        "",
        "- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; prompt_automation_added=false",
        "",
    ])
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    report = build_manual_snapshot_workspace_import(
        root,
        args.source,
        args.workspace,
        args.out_manifest,
        args.write_inbox,
    )
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
