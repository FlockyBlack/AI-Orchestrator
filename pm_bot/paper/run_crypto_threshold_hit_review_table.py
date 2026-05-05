import argparse
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path


TASK_ID = "PMBOT-BRAIN-035-THRESHOLD-HIT-REFERENCE-CONTEXT"
POLICY_TASK_ID = "PMBOT-BRAIN-036-THRESHOLD-HIT-DECISION-POLICY"
SCHEMA_VERSION = "v1"
AS_OF_DATE = "2026-04-27"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = REPO_ROOT / "local_snapshots" / "polymarket_markets_active_500_001.json"
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
    "dispatcher_touched": False,
    "prompt_automation_added": False,
}

MIN_LIQUIDITY_FOR_PAPER_CANDIDATE = 10000.0
MAX_YES_PRICE_FOR_PAPER_CANDIDATE = 0.25
MIN_DISTANCE_TO_TARGET_PCT = 5.0
MIN_TIME_TO_DEADLINE_DAYS = 7
MAX_TIME_TO_DEADLINE_DAYS = 730
PAPER_CANDIDATE_DISABLED_CODE = "paper_candidate_disabled_pending_explicit_thresholds"
MISSING_ASSUMPTION_CODES = (
    "missing_reference_price",
    "missing_deadline",
    "before_event_requires_event_model",
)

_TRIAGE_MODULE = None


def _parse_args(argv):
    parser = argparse.ArgumentParser(description="Build an offline crypto threshold-hit review/scoring table.")
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--reference-context", default=None)
    parser.add_argument("--decision-policy", default=None)
    parser.add_argument("--markdown", action="store_true")
    return parser.parse_args(argv[1:])


def _load_triage_module():
    global _TRIAGE_MODULE
    if _TRIAGE_MODULE is None:
        path = Path(__file__).with_name("run_crypto_threshold_hit_triage_report.py")
        spec = importlib.util.spec_from_file_location("pmbot_crypto_threshold_hit_triage", path)
        module = importlib.util.module_from_spec(spec)
        if spec.loader is None:
            raise RuntimeError("Unable to load threshold-hit triage module.")
        spec.loader.exec_module(module)
        _TRIAGE_MODULE = module
    return _TRIAGE_MODULE


def _float_or_none(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _price_from_config(row, config):
    if not config:
        return None
    keys = [row.get("market_id"), row.get("condition_id"), row.get("asset")]
    for key in keys:
        if key is not None and key in config:
            return _float_or_none(config[key])
    return None


def _load_reference_context(path):
    reference_path = Path(path)
    payload = json.loads(reference_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("reference context must be a JSON object")
    if not isinstance(payload.get("assets"), dict):
        raise ValueError("reference context must include an assets object")
    return payload


def _load_decision_policy(path):
    policy_path = Path(path)
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("decision policy must be a JSON object")
    if not payload.get("decision_policy_version"):
        raise ValueError("decision policy must include decision_policy_version")
    thresholds = payload.get("thresholds")
    if not isinstance(thresholds, dict):
        raise ValueError("decision policy must include a thresholds object")
    required_thresholds = (
        "min_liquidity_for_review",
        "max_yes_price_for_watchlist",
        "min_days_to_deadline_for_review",
        "max_distance_to_target_pct_for_watchlist",
    )
    for key in required_thresholds:
        if _float_or_none(thresholds.get(key)) is None:
            raise ValueError(f"decision policy threshold is missing or invalid: {key}")
    return payload


def _reference_entry(reference_context, asset):
    if not reference_context or asset is None:
        return None
    assets = reference_context.get("assets", {})
    asset_text = str(asset)
    for key in (asset_text, asset_text.upper(), asset_text.lower()):
        if key in assets:
            return assets[key]
    return None


def _reference_info(row, reference_context, current_reference_prices):
    if reference_context is not None:
        entry = _reference_entry(reference_context, row.get("asset"))
        if not isinstance(entry, dict):
            return {
                "current_reference_price": None,
                "reference_price_captured_at": None,
                "reference_price_source": None,
            }
        return {
            "current_reference_price": _float_or_none(entry.get("reference_price")),
            "reference_price_captured_at": reference_context.get("captured_at"),
            "reference_price_source": entry.get("source"),
        }
    return {
        "current_reference_price": _price_from_config(row, current_reference_prices),
        "reference_price_captured_at": None,
        "reference_price_source": None,
    }


def _assets_with_reference_price(reference_context):
    if reference_context is None:
        return []
    assets = reference_context.get("assets", {})
    result = []
    for asset, entry in assets.items():
        if isinstance(entry, dict) and _float_or_none(entry.get("reference_price")) is not None:
            result.append(str(asset).upper())
    return sorted(set(result))


def _event_model_fixture_present(row, event_model_fixtures):
    if row["market_type"] != "threshold_hit_before_event":
        return False
    if not event_model_fixtures:
        return False
    keys = [row.get("market_id"), row.get("condition_id"), row.get("event_trigger")]
    for key in keys:
        if key is None:
            continue
        value = event_model_fixtures.get(key)
        if value:
            return True
        value = event_model_fixtures.get(str(key).lower())
        if value:
            return True
    return False


def _distance_to_target_pct(target, current_reference_price):
    target_value = _float_or_none(target)
    reference = _float_or_none(current_reference_price)
    if target_value is None or reference is None or reference <= 0:
        return None
    return round(((target_value / reference) - 1.0) * 100.0, 4)


def _target_multiple(target, current_reference_price):
    target_value = _float_or_none(target)
    reference = _float_or_none(current_reference_price)
    if target_value is None or reference is None or reference <= 0:
        return None
    return round(target_value / reference, 6)


def _time_to_deadline_days(deadline_date):
    if not deadline_date:
        return None
    try:
        return (date.fromisoformat(deadline_date) - date.fromisoformat(AS_OF_DATE)).days
    except ValueError:
        return None


def _missing_assumption_codes(row, current_reference_price, event_model_fixture_present):
    codes = []
    if current_reference_price is None:
        codes.append("missing_reference_price")
    if row["market_type"] == "threshold_hit_by_date" and row.get("deadline_date") is None:
        codes.append("missing_deadline")
    if row["market_type"] == "threshold_hit_before_event" and not event_model_fixture_present:
        codes.append("before_event_requires_event_model")
    return codes


def _model_assumption_status(missing_codes):
    if "before_event_requires_event_model" in missing_codes:
        return "before_event_requires_event_model"
    if "missing_deadline" in missing_codes:
        return "missing_deadline"
    if "missing_reference_price" in missing_codes:
        return "missing_reference_price"
    return "reviewable"


def _conservative_threshold_codes(row, distance_to_target_pct, time_to_deadline_days):
    codes = []
    yes_price = _float_or_none(row.get("yes_price"))
    liquidity = _float_or_none(row.get("liquidity"))
    if yes_price is None:
        codes.append("missing_yes_price")
    elif yes_price > MAX_YES_PRICE_FOR_PAPER_CANDIDATE:
        codes.append("yes_price_above_conservative_limit")
    if liquidity is None:
        codes.append("missing_liquidity")
    elif liquidity < MIN_LIQUIDITY_FOR_PAPER_CANDIDATE:
        codes.append("liquidity_below_conservative_minimum")
    if distance_to_target_pct is None:
        codes.append("target_distance_unavailable")
    elif distance_to_target_pct < MIN_DISTANCE_TO_TARGET_PCT:
        codes.append("target_distance_below_conservative_minimum")
    if row["market_type"] == "threshold_hit_by_date":
        if time_to_deadline_days is None:
            codes.append("missing_deadline")
        elif time_to_deadline_days <= 0:
            codes.append("deadline_not_future")
        elif time_to_deadline_days < MIN_TIME_TO_DEADLINE_DAYS:
            codes.append("deadline_too_near")
        elif time_to_deadline_days > MAX_TIME_TO_DEADLINE_DAYS:
            codes.append("deadline_too_far")
    if not codes:
        codes.append(PAPER_CANDIDATE_DISABLED_CODE)
    return codes


def _review_decision(missing_codes, threshold_codes):
    if "before_event_requires_event_model" in missing_codes or "missing_deadline" in missing_codes:
        return "no_action"
    if "missing_reference_price" in missing_codes:
        return "watchlist"
    if threshold_codes:
        return "watchlist"
    return "paper_candidate"


def _human_review_note(row, decision, missing_codes, threshold_codes):
    if "before_event_requires_event_model" in missing_codes:
        return "No action: before-event threshold market needs an explicit offline event model fixture before scoring."
    if "missing_deadline" in missing_codes:
        return "No action: deadline was not parsed; review the market rules before scoring."
    if "missing_reference_price" in missing_codes:
        return "Watchlist only: supply an offline reference price fixture before reviewing distance to target."
    if decision == "paper_candidate":
        return "Paper candidate label only: all offline assumptions are present and conservative review thresholds pass."
    if PAPER_CANDIDATE_DISABLED_CODE in threshold_codes:
        return "Watchlist only: offline reference context is present, but paper-candidate thresholds remain intentionally disabled."
    if threshold_codes:
        return "Watchlist only: offline assumptions are present, but conservative review thresholds did not pass."
    return "Watchlist only: operator review is required before any paper planning."


def _policy_check(name, passed, value, threshold, reason_code):
    return {
        "name": name,
        "passed": bool(passed),
        "value": value,
        "threshold": threshold,
        "reason_code": None if passed else reason_code,
    }


def _policy_thresholds(policy):
    thresholds = policy["thresholds"]
    return {
        "min_liquidity_for_review": _float_or_none(thresholds["min_liquidity_for_review"]),
        "max_yes_price_for_watchlist": _float_or_none(thresholds["max_yes_price_for_watchlist"]),
        "min_days_to_deadline_for_review": int(thresholds["min_days_to_deadline_for_review"]),
        "max_distance_to_target_pct_for_watchlist": _float_or_none(
            thresholds["max_distance_to_target_pct_for_watchlist"]
        ),
    }


def _build_policy_checks(row, policy):
    thresholds = _policy_thresholds(policy)
    checks = []
    current_reference_price = row["current_reference_price"]
    checks.append(
        _policy_check(
            "reference_price_present",
            current_reference_price is not None,
            current_reference_price,
            "present",
            "missing_reference_price",
        )
    )
    if row["market_type"] == "threshold_hit_before_event" and policy.get("block_before_event_without_event_model", True):
        checks.append(
            _policy_check(
                "before_event_event_model_present",
                row["event_model_fixture_present"],
                row["event_model_fixture_present"],
                True,
                "before_event_requires_event_model",
            )
        )
    if row["market_type"] == "threshold_hit_by_date":
        days_to_deadline = row["time_to_deadline_days"]
        checks.append(
            _policy_check(
                "deadline_present",
                days_to_deadline is not None,
                days_to_deadline,
                "present",
                "missing_deadline",
            )
        )
        if days_to_deadline is not None:
            if days_to_deadline <= 0:
                deadline_reason = "deadline_not_future"
            else:
                deadline_reason = "deadline_too_near"
            checks.append(
                _policy_check(
                    "min_days_to_deadline_for_review",
                    days_to_deadline >= thresholds["min_days_to_deadline_for_review"],
                    days_to_deadline,
                    thresholds["min_days_to_deadline_for_review"],
                    deadline_reason,
                )
            )
    liquidity = _float_or_none(row["liquidity"])
    checks.append(
        _policy_check(
            "min_liquidity_for_review",
            liquidity is not None and liquidity >= thresholds["min_liquidity_for_review"],
            liquidity,
            thresholds["min_liquidity_for_review"],
            "missing_liquidity" if liquidity is None else "liquidity_below_conservative_minimum",
        )
    )
    yes_price = _float_or_none(row["yes_price"])
    checks.append(
        _policy_check(
            "max_yes_price_for_watchlist",
            yes_price is not None and yes_price <= thresholds["max_yes_price_for_watchlist"],
            yes_price,
            thresholds["max_yes_price_for_watchlist"],
            "missing_yes_price" if yes_price is None else "yes_price_above_conservative_limit",
        )
    )
    distance_to_target_pct = row["distance_to_target_pct"]
    checks.append(
        _policy_check(
            "max_distance_to_target_pct_for_watchlist",
            distance_to_target_pct is not None
            and distance_to_target_pct <= thresholds["max_distance_to_target_pct_for_watchlist"],
            distance_to_target_pct,
            thresholds["max_distance_to_target_pct_for_watchlist"],
            "target_distance_unavailable"
            if distance_to_target_pct is None
            else "target_distance_above_watchlist_limit",
        )
    )
    allow_paper_candidates = bool(policy.get("allow_paper_candidates", False))
    checks.append(
        _policy_check(
            "allow_paper_candidates",
            allow_paper_candidates,
            allow_paper_candidates,
            True,
            "paper_candidates_disabled_by_policy",
        )
    )
    return checks


def _policy_reason_codes(policy_checks):
    return sorted(
        {
            check["reason_code"]
            for check in policy_checks
            if check["reason_code"] is not None
        }
    )


def _policy_human_review_note(row, decision, reason_codes):
    if "before_event_requires_event_model" in reason_codes:
        return "Policy blocked: before-event threshold markets require an explicit offline event model fixture."
    if "missing_deadline" in reason_codes:
        return "No action: deadline was not parsed; review the market rules before applying policy."
    if "missing_reference_price" in reason_codes:
        return "Watchlist only: supply an offline reference price fixture before applying policy thresholds."
    blocking_reasons = [code for code in reason_codes if code != "paper_candidates_disabled_by_policy"]
    if decision == "paper_candidate":
        return "Paper candidate label only: deterministic offline policy checks pass; no paper order is created."
    if blocking_reasons:
        return "Policy blocked: deterministic offline review checks did not pass."
    if "paper_candidates_disabled_by_policy" in reason_codes:
        return "Watchlist only: deterministic offline checks pass, but paper candidates are disabled by policy."
    if row["market_type"] != "threshold_hit_by_date":
        return "Watchlist only: non-by-date threshold markets require manual event-model review."
    return "Watchlist only: operator review is required before any paper planning."


def _apply_decision_policy(row, policy):
    policy_checks = _build_policy_checks(row, policy)
    passed_policy_checks = [check["name"] for check in policy_checks if check["passed"]]
    failed_policy_checks = [check["name"] for check in policy_checks if not check["passed"]]
    reason_codes = _policy_reason_codes(policy_checks)
    blocking_reason_codes = [code for code in reason_codes if code != "paper_candidates_disabled_by_policy"]
    if "before_event_requires_event_model" in reason_codes:
        decision = "policy_blocked"
    elif "missing_deadline" in reason_codes:
        decision = "no_action"
    elif "missing_reference_price" in reason_codes:
        decision = "watchlist"
    elif blocking_reason_codes:
        decision = "policy_blocked"
    elif row["market_type"] == "threshold_hit_by_date" and bool(policy.get("allow_paper_candidates", False)):
        decision = "paper_candidate"
    else:
        decision = "watchlist"
    row = dict(row)
    row.update(
        {
            "decision_policy_version": policy["decision_policy_version"],
            "policy_checks": policy_checks,
            "passed_policy_checks": passed_policy_checks,
            "failed_policy_checks": failed_policy_checks,
            "review_decision": decision,
            "conservative_thresholds_pass": not blocking_reason_codes,
            "reason_codes": reason_codes,
            "human_review_note": _policy_human_review_note(row, decision, reason_codes),
        }
    )
    return row


def _review_row(row, current_reference_prices, event_model_fixtures, reference_context):
    reference_info = _reference_info(row, reference_context, current_reference_prices)
    current_reference_price = reference_info["current_reference_price"]
    event_model_fixture_present = _event_model_fixture_present(row, event_model_fixtures)
    distance_pct = _distance_to_target_pct(row.get("target"), current_reference_price)
    target_multiple = _target_multiple(row.get("target"), current_reference_price)
    days_to_deadline = _time_to_deadline_days(row.get("deadline_date"))
    missing_codes = _missing_assumption_codes(row, current_reference_price, event_model_fixture_present)
    threshold_codes = [] if missing_codes else _conservative_threshold_codes(row, distance_pct, days_to_deadline)
    reason_codes = missing_codes + [code for code in threshold_codes if code not in missing_codes]
    decision = _review_decision(missing_codes, threshold_codes)
    return {
        "market_id": row["market_id"],
        "title": row["title"],
        "question": row["question"],
        "asset": row["asset"],
        "target": row["target"],
        "target_display": row["target_display"],
        "market_type": row["market_type"],
        "deadline_date": row["deadline_date"],
        "event_trigger": row["event_trigger"],
        "yes_price": row["yes_price"],
        "implied_probability": row["yes_price"],
        "liquidity": row["liquidity"],
        "current_reference_price": current_reference_price,
        "reference_price_captured_at": reference_info["reference_price_captured_at"],
        "reference_price_source": reference_info["reference_price_source"],
        "distance_to_target_pct": distance_pct,
        "target_multiple": target_multiple,
        "time_to_deadline_days": days_to_deadline,
        "event_model_fixture_present": event_model_fixture_present,
        "model_assumption_status": _model_assumption_status(missing_codes),
        "review_decision": decision,
        "conservative_thresholds_pass": not missing_codes and not threshold_codes,
        "reason_codes": reason_codes,
        "human_review_note": _human_review_note(row, decision, missing_codes, threshold_codes),
    }


def _count_values(rows, field, values):
    return {value: sum(1 for row in rows if row[field] == value) for value in values}


def _missing_reason_counts(rows):
    counts = {code: 0 for code in MISSING_ASSUMPTION_CODES}
    for row in rows:
        for code in row["reason_codes"]:
            if code in counts:
                counts[code] += 1
    return {key: counts[key] for key in sorted(counts) if counts[key]}


def _reason_counts(rows):
    counts = {}
    for row in rows:
        for code in row["reason_codes"]:
            counts[code] = counts.get(code, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def build_crypto_threshold_hit_review_table(
    root: Path,
    source_path=None,
    payload=None,
    current_reference_prices=None,
    event_model_fixtures=None,
    reference_context=None,
    decision_policy=None,
):
    triage = _load_triage_module()
    source = Path(source_path) if source_path else DEFAULT_SOURCE
    triage_report = triage.build_crypto_threshold_hit_triage_report(root, source, payload)
    rows = [
        _review_row(row, current_reference_prices or {}, event_model_fixtures or {}, reference_context)
        for row in triage_report["supported_triage_candidates"]
    ]
    if decision_policy is not None:
        rows = [_apply_decision_policy(row, decision_policy) for row in rows]
        decision_counts = _count_values(rows, "review_decision", ("no_action", "watchlist", "policy_blocked", "paper_candidate"))
    else:
        decision_counts = _count_values(rows, "review_decision", ("no_action", "watchlist", "paper_candidate"))
    summary = {
        "markets_seen": triage_report["summary"]["total_markets_seen"],
        "threshold_hit_candidates": len(rows),
        "reference_context_used": reference_context is not None,
        "assets_with_reference_price": _assets_with_reference_price(reference_context),
        "no_action_count": decision_counts["no_action"],
        "watchlist_count": decision_counts["watchlist"],
        "paper_candidate_count": decision_counts["paper_candidate"],
        "paper_orders_created": 0,
        "missing_assumption_reason_counts": _missing_reason_counts(rows),
        "safety_flags": SAFETY_FLAGS,
    }
    if decision_policy is not None:
        summary.update(
            {
                "decision_policy_used": True,
                "decision_policy_version": decision_policy["decision_policy_version"],
                "policy_blocked_count": decision_counts["policy_blocked"],
                "policy_reason_counts": _reason_counts(rows),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": POLICY_TASK_ID if decision_policy is not None else TASK_ID,
        "deterministic": True,
        "as_of_date": AS_OF_DATE,
        "source_path": str(source),
        "source_task_id": triage_report["task_id"],
        "source_shape": triage_report["source_shape"],
        "top_level_shape": triage_report["top_level_shape"],
        "gamma_market_list_detected": triage_report["gamma_market_list_detected"],
        "triage_summary": triage_report["summary"],
        "summary": summary,
        "rows": rows,
        "safety_flags": SAFETY_FLAGS,
        "limitations": [
            "Reads a local saved JSON file only; no live fetcher, network, external API, credentials, wallet access, orders, or trading are included.",
            "Threshold-hit review rows are not merged into the existing above/below crypto numeric scorer.",
            "No paper orders, runtime wiring, dispatcher changes, prompt automation, or workspace state writes are included.",
            "Default review uses no live reference price and no before-event timing model; missing assumptions prevent paper_candidate decisions.",
            "Reference context, when supplied, is read from a local fixture file only and does not enable paper candidates.",
        ],
    }


def _md(value):
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(report):
    summary = report["summary"]
    decision_policy_used = summary.get("decision_policy_used", False)
    lines = [
        "# Crypto Threshold-Hit Review Table",
        "",
        f"- Source: {report['source_path']}",
        f"- Source shape: {report['source_shape']}",
        f"- As of date: {report['as_of_date']}",
        f"- Markets seen: {summary['markets_seen']}",
        f"- Threshold-hit candidates: {summary['threshold_hit_candidates']}",
        f"- Reference context used: {str(summary['reference_context_used']).lower()}",
        f"- Assets with reference price: {json.dumps(summary['assets_with_reference_price'])}",
    ]
    if decision_policy_used:
        lines.extend(
            [
                f"- Decision policy used: {str(summary['decision_policy_used']).lower()}",
                f"- Decision policy version: {summary['decision_policy_version']}",
            ]
        )
    lines.extend(
        [
        f"- No action: {summary['no_action_count']}",
        f"- Watchlist: {summary['watchlist_count']}",
        ]
    )
    if decision_policy_used:
        lines.append(f"- Policy blocked: {summary['policy_blocked_count']}")
    lines.extend(
        [
        f"- Paper candidates: {summary['paper_candidate_count']}",
        f"- Missing assumption reason counts: {json.dumps(summary['missing_assumption_reason_counts'], sort_keys=True)}",
        ]
    )
    if decision_policy_used:
        lines.append(f"- Policy reason counts: {json.dumps(summary['policy_reason_counts'], sort_keys=True)}")
    lines.extend(
        [
        f"- Paper orders created: {summary['paper_orders_created']}",
        "",
        "## Review Rows",
        "",
        ]
    )
    if decision_policy_used:
        lines.extend(
            [
                "| market_id | question | asset | target | type | deadline | event | yes | implied_probability | liquidity | reference | reference_captured_at | reference_source | distance_pct | target_multiple | days | assumption_status | decision | policy_version | passed_policy_checks | failed_policy_checks | reason_codes | note |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
    else:
        lines.extend(
            [
        "| market_id | question | asset | target | type | deadline | event | yes | implied_probability | liquidity | reference | reference_captured_at | reference_source | distance_pct | target_multiple | days | assumption_status | decision | reason_codes | note |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
    if report["rows"]:
        for row in report["rows"]:
            base = (
                f"| {_md(row['market_id'])} | {_md(row['question'])} | {_md(row['asset'])} | {_md(row['target_display'] or row['target'])} | "
                f"{_md(row['market_type'])} | {_md(row['deadline_date'])} | {_md(row['event_trigger'])} | {_md(row['yes_price'])} | "
                f"{_md(row['implied_probability'])} | {_md(row['liquidity'])} | {_md(row['current_reference_price'])} | "
                f"{_md(row['reference_price_captured_at'])} | {_md(row['reference_price_source'])} | "
                f"{_md(row['distance_to_target_pct'])} | {_md(row['target_multiple'])} | {_md(row['time_to_deadline_days'])} | {_md(row['model_assumption_status'])} | "
                f"{_md(row['review_decision'])} | "
            )
            if decision_policy_used:
                lines.append(
                    base
                    + f"{_md(row['decision_policy_version'])} | {_md(json.dumps(row['passed_policy_checks']))} | "
                    + f"{_md(json.dumps(row['failed_policy_checks']))} | {_md(json.dumps(row['reason_codes']))} | {_md(row['human_review_note'])} |"
                )
            else:
                lines.append(base + f"{_md(json.dumps(row['reason_codes']))} | {_md(row['human_review_note'])} |")
    else:
        if decision_policy_used:
            lines.append("|  | None |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | [] | [] | [] |  |")
        else:
            lines.append("|  | None |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | [] |  |")
    lines.extend(["", "## Safety Flags", ""])
    lines.append(
        "- offline_only=true; paper_only=true; live_fetcher_implemented=false; api_used=false; network_used=false; wallet_used=false; real_order_created=false; trading_allowed=false; runtime_wiring_changed=false; dispatcher_touched=false; prompt_automation_added=false"
    )
    lines.extend(["", "## Limitations", ""])
    for item in report["limitations"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def main(argv):
    args = _parse_args(argv)
    root = Path(__file__).resolve().parents[2]
    reference_context = _load_reference_context(args.reference_context) if args.reference_context else None
    decision_policy = _load_decision_policy(args.decision_policy) if args.decision_policy else None
    report = build_crypto_threshold_hit_review_table(
        root,
        args.source,
        reference_context=reference_context,
        decision_policy=decision_policy,
    )
    if args.markdown:
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
