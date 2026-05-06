import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PROFILE = "sonnet_gpt55_critic"
DEFAULT_OUT_DIR = "pm_bot/llm/openrouter_adapter_dry_runs"
CONTRACT_PATH = "pm_bot/llm/openrouter_adapter_contract.v1.json"
MANUAL_BATCH_DIR = "pm_bot/llm/manual_packet_batch"
PLANNED_OUTPUTS = [
    "adapter_run_summary.v1.json",
    "candidate_raw.json",
    "candidate_content.json",
    "candidate_validation.json",
    "critic_raw.json",
    "critic_content.json",
    "critic_validation.json",
    "operator_next_action.md",
]
NEXT_ACTION = "operator_may_request_manual_network_adapter_in_future_after_approval"
VALID_STATUSES = {
    "dry_run_ready",
    "blocked_missing_prompt",
    "blocked_invalid_contract",
    "blocked_invalid_args",
    "blocked_runtime_boundary",
    "blocked_network_not_implemented",
}


def build_parser():
    parser = argparse.ArgumentParser(
        description="Dry-run-only PMBOT OpenRouter adapter shell.",
        allow_abbrev=False,
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--market-id")
    parser.add_argument("--prompt-path")
    parser.add_argument("--packet-path")
    parser.add_argument("--model-profile", default=DEFAULT_MODEL_PROFILE)
    parser.add_argument("--allow-local-json-fence-repair", action="store_true")
    parser.add_argument("--max-prompt-tokens", default="20000")
    parser.add_argument("--max-completion-tokens", default="4000")
    parser.add_argument("--max-cost-usd", default="0.25")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--manual-confirm-network", action="store_true")
    return parser


def _resolve_path(value, root):
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def _display_path(path, root):
    if path is None:
        return None
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _extract_market_id_from_prompt(prompt_path):
    suffix = "_prompt.v1.md"
    name = prompt_path.name
    if not name.endswith(suffix):
        return None
    candidate = name[: -len(suffix)]
    if candidate.isdigit():
        return candidate
    return None


def _validate_positive_int(raw_value, field_name, errors):
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        errors.append(f"{field_name}_must_be_positive_int")
        return None
    if value <= 0:
        errors.append(f"{field_name}_must_be_positive_int")
        return None
    return value


def _validate_positive_decimal_string(raw_value, field_name, errors):
    try:
        value = Decimal(str(raw_value))
    except (InvalidOperation, ValueError):
        errors.append(f"{field_name}_must_be_positive_decimal")
        return str(raw_value)
    if value <= 0:
        errors.append(f"{field_name}_must_be_positive_decimal")
    return str(raw_value)


def _load_profile(root, model_profile):
    contract_path = root / CONTRACT_PATH
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, ["contract_unreadable_or_invalid_json", exc.__class__.__name__]

    if contract.get("contract_version") != "pmbot_openrouter_adapter_contract.v1":
        return None, ["unexpected_contract_version"]
    if contract.get("status") != "design_only_inert_reference":
        return None, ["contract_not_inert_reference"]
    if contract.get("runtime_import_allowed") is not False:
        return None, ["runtime_import_allowed_not_false"]
    if contract.get("network_behavior") != "none":
        return None, ["contract_network_behavior_not_none"]

    profiles = contract.get("model_profiles")
    if not isinstance(profiles, dict):
        return None, ["model_profiles_missing"]
    profile = profiles.get(model_profile)
    if profile is None:
        return None, ["unknown_model_profile"]

    required_values = {
        "candidate_model": "anthropic/claude-sonnet-4.5",
        "critic_model": "openai/gpt-5.5",
        "critic_contract_version": "pmbot_openrouter_critic_response.v1",
        "manual_invocation_required": True,
        "single_prompt_per_invocation": True,
    }
    for key, expected in required_values.items():
        if profile.get(key) != expected:
            return None, [f"model_profile_{key}_mismatch"]
    return profile, []


def _select_paths(args, root):
    batch_dir = root / MANUAL_BATCH_DIR
    prompt_path = None
    market_id = args.market_id
    warnings = []

    if market_id is not None:
        market_id = market_id.strip()
        if not market_id or not market_id.isdigit():
            return {
                "market_id": market_id,
                "prompt_path": None,
                "packet_path": None,
                "warnings": warnings,
                "errors": ["market_id_must_be_digits"],
            }

    if args.prompt_path:
        prompt_path = _resolve_path(args.prompt_path, root)
        prompt_market_id = _extract_market_id_from_prompt(prompt_path)
        if prompt_market_id is not None:
            market_id = prompt_market_id
    elif market_id:
        prompt_path = batch_dir / f"{market_id}_prompt.v1.md"
    else:
        prompts = sorted(batch_dir.glob("*_prompt.v1.md"))
        if prompts:
            prompt_path = prompts[0]
            market_id = _extract_market_id_from_prompt(prompt_path)

    packet_path = None
    if args.packet_path:
        candidate_packet_path = _resolve_path(args.packet_path, root)
        if candidate_packet_path.exists():
            packet_path = candidate_packet_path
        else:
            warnings.append("missing_packet")
    elif market_id:
        candidate_packet_path = batch_dir / f"{market_id}_packet.v1.json"
        if candidate_packet_path.exists():
            packet_path = candidate_packet_path
        else:
            warnings.append("missing_packet")

    return {
        "market_id": market_id,
        "prompt_path": prompt_path,
        "packet_path": packet_path,
        "warnings": warnings,
        "errors": [],
    }


def _artifact_label(market_id):
    if market_id and str(market_id).isdigit():
        return market_id
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _base_summary(args, selection, profile, limits, status, warnings, root):
    prompt_path = selection.get("prompt_path")
    packet_path = selection.get("packet_path")
    summary = {
        "artifact_type": "pmbot_openrouter_adapter_dry_run_summary.v1",
        "status": status,
        "dry_run": bool(args.dry_run),
        "network_calls_made": False,
        "api_key_read": False,
        "runtime_wiring": False,
        "dispatcher_integration": False,
        "wallet_or_orders": False,
        "trading_decision": False,
        "market_id": selection.get("market_id"),
        "selected_prompt_path": _display_path(prompt_path, root),
        "selected_packet_path": _display_path(packet_path, root),
        "model_profile": args.model_profile,
        "candidate_model": profile.get("candidate_model") if profile else None,
        "critic_model": profile.get("critic_model") if profile else None,
        "critic_contract_version": profile.get("critic_contract_version") if profile else None,
        "limits": limits,
        "planned_outputs": PLANNED_OUTPUTS,
        "warnings": warnings,
        "allow_local_json_fence_repair": bool(args.allow_local_json_fence_repair),
        "manual_confirm_network_requested": bool(args.manual_confirm_network),
        "analysis_only": True,
        "manual_review_only": True,
        "operator_gated": True,
        "validator_gated": True,
        "no_runtime_wiring": True,
        "no_dispatcher_integration": True,
        "no_wallet_or_orders": True,
        "no_trading_decision": True,
        "no_network_calls": True,
        "next_action": NEXT_ACTION,
    }
    return summary


def _operator_next_action_markdown(summary):
    packet_path = summary["selected_packet_path"] if summary["selected_packet_path"] else "null"
    return (
        "# PMBOT OpenRouter Adapter Dry Run\n\n"
        f"Status: `{summary['status']}`\n\n"
        "This adapter shell is dry-run only. No network call was made. "
        "No API key was read.\n\n"
        "No runtime wiring, workbench integration, dispatcher integration, wallet access, "
        "orders, or market decisions were performed.\n\n"
        f"Selected prompt: `{summary['selected_prompt_path']}`\n\n"
        f"Selected packet: `{packet_path}`\n\n"
        f"Model profile: `{summary['model_profile']}`\n\n"
        f"Candidate model: `{summary['candidate_model']}`\n\n"
        f"Critic model: `{summary['critic_model']}`\n\n"
        f"Critic contract version: `{summary['critic_contract_version']}`\n\n"
        "Next allowed task: manual operator approval for a future network adapter proposal "
        "or gated implementation, not runtime wiring.\n"
    )


def _write_artifacts(summary, out_dir, root):
    output_dir = _resolve_path(out_dir, root)
    output_dir.mkdir(parents=True, exist_ok=True)

    label = _artifact_label(summary.get("market_id"))
    summary_path = output_dir / f"adapter_dry_run_summary_{label}.v1.json"
    next_action_path = output_dir / f"operator_next_action_{label}.md"

    summary["artifact_paths"] = {
        "summary": _display_path(summary_path, root),
        "operator_next_action": _display_path(next_action_path, root),
    }
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    next_action_path.write_text(_operator_next_action_markdown(summary), encoding="utf-8")
    return summary


def run_adapter(argv, root=ROOT):
    parser = build_parser()
    try:
        args, unknown = parser.parse_known_args(argv)
    except SystemExit:
        args = parser.parse_args([])
        unknown = ["argparse_parse_failed"]

    warnings = []
    arg_errors = []
    if unknown:
        arg_errors.extend(f"unknown_arg:{item}" for item in unknown)

    max_prompt_tokens = _validate_positive_int(
        args.max_prompt_tokens, "max_prompt_tokens", arg_errors
    )
    max_completion_tokens = _validate_positive_int(
        args.max_completion_tokens, "max_completion_tokens", arg_errors
    )
    max_cost_usd = _validate_positive_decimal_string(
        args.max_cost_usd, "max_cost_usd", arg_errors
    )
    limits = {
        "max_prompt_tokens": max_prompt_tokens,
        "max_completion_tokens": max_completion_tokens,
        "max_cost_usd": max_cost_usd,
    }

    selection = _select_paths(args, root)
    warnings.extend(selection["warnings"])
    arg_errors.extend(selection["errors"])

    profile = None
    contract_errors = []
    if not arg_errors:
        profile, contract_errors = _load_profile(root, args.model_profile)

    if args.manual_confirm_network:
        status = "blocked_network_not_implemented"
        warnings.append("manual_confirm_network_not_implemented_in_009")
    elif not args.dry_run:
        status = "blocked_runtime_boundary"
        warnings.append("dry_run_flag_required")
    elif arg_errors:
        status = "blocked_invalid_args"
        warnings.extend(arg_errors)
    elif contract_errors:
        if "unknown_model_profile" in contract_errors:
            status = "blocked_invalid_args"
        else:
            status = "blocked_invalid_contract"
        warnings.extend(contract_errors)
    elif selection["prompt_path"] is None or not selection["prompt_path"].exists():
        status = "blocked_missing_prompt"
        warnings.append("missing_prompt")
    else:
        status = "dry_run_ready"

    if status not in VALID_STATUSES:
        status = "blocked_invalid_args"
        warnings.append("unexpected_status_guard")

    summary = _base_summary(args, selection, profile, limits, status, warnings, root)
    summary = _write_artifacts(summary, args.out_dir, root)
    if status == "dry_run_ready":
        return 0, summary
    if status == "blocked_invalid_args":
        return 2, summary
    return 1, summary


def main(argv=None):
    code, summary = run_adapter(sys.argv[1:] if argv is None else argv)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
