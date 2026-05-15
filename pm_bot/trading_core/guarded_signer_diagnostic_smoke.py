from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from pm_bot.trading_core.guarded_signer_diagnostic_models import (
    DEFAULT_ALLOWED_MARKET,
    DEFAULT_ALLOWED_STRATEGY,
    DIAGNOSTIC_CHALLENGE,
    DIAGNOSTIC_STATUS_DEPENDENCY_MISSING,
    DIAGNOSTIC_STATUS_DIAGNOSTIC_FAILED,
    DIAGNOSTIC_STATUS_DIAGNOSTIC_OK,
    DIAGNOSTIC_STATUS_INVALID_KEY_FORMAT,
    DIAGNOSTIC_STATUS_MISSING_PRIVATE_KEY,
    DIAGNOSTIC_STATUS_MISSING_WALLET_ADDRESS,
    DIAGNOSTIC_STATUS_NOT_REQUESTED,
    DIAGNOSTIC_STATUS_WALLET_MISMATCH,
    EXECUTION_MODE,
    GUARDED_SIGNER_DIAGNOSTIC_LATEST_STATUS_CONTRACT,
    GUARDED_SIGNER_DIAGNOSTIC_RESULT_CONTRACT,
    GuardedSignerDiagnosticRedactionPolicy,
    GuardedSignerDiagnosticSafetyContract,
    MODE,
    REQUIRED_FALSE_FLAGS,
    TASK_ID,
    guarded_signer_diagnostic_safety_flags,
    validate_guarded_signer_diagnostic_result,
)
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/guarded_signer_diagnostic_smoke_069a")

KEY_ENV_NAME = "POLYMARKET_PRIVATE_KEY"
WALLET_ENV_NAME = "POLYMARKET_WALLET_ADDRESS"

PRIVATE_KEY_PATTERN = re.compile(r"^0x[0-9a-fA-F]{64}$")
ADDRESS_PATTERN = re.compile(r"^0x[0-9a-fA-F]{40}$")
ORDER_PAYLOAD_FIELD_PATTERN = re.compile(
    r'["\'](?:maker|taker|token_id|price|size|side|salt|nonce|expiration|signature|feeRateBps)["\']\s*:',
    re.IGNORECASE,
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
    "--order",
    "--order-payload",
    "--private-key",
    "--polymarket-private-key",
    "--seed",
    "--mnemonic",
    "--api-secret",
    "--auth-token",
    "--passphrase",
)


class DependencyMissingError(RuntimeError):
    pass


class SignerDiagnosticAdapter(Protocol):
    def derive_address(self, key_value: str) -> str:
        ...

    def sign_diagnostic_challenge(self, key_value: str, challenge: str) -> str:
        ...


class EthAccountSignerDiagnosticAdapter:
    def derive_address(self, key_value: str) -> str:
        account = _load_eth_account()
        return str(account.from_key(key_value).address)

    def sign_diagnostic_challenge(self, key_value: str, challenge: str) -> str:
        account = _load_eth_account()
        encode_defunct = _load_encode_defunct()
        message = encode_defunct(text=challenge)
        signed = account.sign_message(message, key_value)
        return _signature_to_text(signed.signature)


def guarded_signer_diagnostic_artifact_paths(
    artifact_dir: str | Path | None = None,
) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "guarded_signer_diagnostic_smoke_069a_result.json",
        "latest_status": root / "latest_guarded_signer_diagnostic_status_069a.json",
        "redaction_policy": root / "guarded_signer_diagnostic_redaction_policy_069a.json",
        "safety_contract": root / "guarded_signer_diagnostic_safety_contract_069a.json",
        "operator_md": root / "guarded_signer_diagnostic_operator_summary_069a.md",
    }


def run_guarded_signer_diagnostic_smoke(
    *,
    market: str = DEFAULT_ALLOWED_MARKET,
    strategy: str = DEFAULT_ALLOWED_STRATEGY,
    dry_run: bool = True,
    allow_private_key_diagnostic: bool = False,
    artifact_dir: str | Path | None = None,
    env: Mapping[str, str] | None = None,
    account_adapter: SignerDiagnosticAdapter | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("guarded signer diagnostic smoke is dry-run only; live execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_ALLOWED_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_ALLOWED_STRATEGY
    paths = guarded_signer_diagnostic_artifact_paths(artifact_dir)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}

    safety_contract = GuardedSignerDiagnosticSafetyContract(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()
    redaction_policy = GuardedSignerDiagnosticRedactionPolicy(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        generated_at=generated_at,
    ).to_dict()

    diagnostic = _run_diagnostic_path(
        allow_private_key_diagnostic=allow_private_key_diagnostic,
        env=env,
        account_adapter=account_adapter,
    )
    latest_status = _build_latest_status(
        market_symbol=market_symbol,
        strategy_name=strategy_name,
        diagnostic=diagnostic,
        path_refs=path_refs,
        generated_at=generated_at,
    )

    result = {
        "contract_version": GUARDED_SIGNER_DIAGNOSTIC_RESULT_CONTRACT,
        "task_id": TASK_ID,
        "status": diagnostic["status"],
        "diagnostic_status": diagnostic["diagnostic_status"],
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "review_only": True,
        "preflight_only": True,
        "dry_run": True,
        "dry_run_only": True,
        "paper_only": True,
        "non_executable": True,
        "diagnostic_requested": allow_private_key_diagnostic is True,
        "signer_diagnostic_executable": allow_private_key_diagnostic is True,
        "private_key_read": diagnostic["private_key_read"],
        "private_key_present": diagnostic["private_key_present"],
        "private_key_format_valid": diagnostic["private_key_format_valid"],
        "wallet_address_read": diagnostic["wallet_address_read"],
        "wallet_address_present": diagnostic["wallet_address_present"],
        "expected_wallet_address_redacted": diagnostic["expected_wallet_address_redacted"],
        "derived_wallet_address_redacted": diagnostic["derived_wallet_address_redacted"],
        "derived_wallet_matches_expected": diagnostic["derived_wallet_matches_expected"],
        "diagnostic_challenge_signing_enabled": allow_private_key_diagnostic is True,
        "diagnostic_challenge_signing_attempted": diagnostic["diagnostic_challenge_signing_attempted"],
        "diagnostic_challenge_signed": diagnostic["diagnostic_challenge_signed"],
        "diagnostic_challenge_id": "pmbot_signer_diagnostic_only_no_order_no_submit",
        "diagnostic_challenge_sha256": _sha256_text(DIAGNOSTIC_CHALLENGE),
        "diagnostic_challenge_is_order_payload": False,
        "diagnostic_signature_redacted": diagnostic["diagnostic_signature_redacted"],
        "dependency_status": diagnostic["dependency_status"],
        "block_reason": diagnostic["block_reason"],
        "no_order_payload_signing": True,
        "no_order_submission": True,
        "no_order_cancel": True,
        "no_authenticated_trading": True,
        "safety_contract": safety_contract,
        "redaction_policy": redaction_policy,
        "latest_status": latest_status,
        "artifact_paths": path_refs,
        "operator_summary": _operator_summary_for_status(diagnostic["diagnostic_status"]),
        "generated_at": generated_at,
    }
    result.update(guarded_signer_diagnostic_safety_flags())
    result["validation"] = validate_guarded_signer_diagnostic_result(result, generated_at=generated_at)

    write_json(paths["safety_contract"], safety_contract)
    write_json(paths["redaction_policy"], redaction_policy)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_guarded_signer_diagnostic_markdown(result))
    return result


def render_guarded_signer_diagnostic_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Guarded signer diagnostic smoke 069A completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Diagnostic requested: {str(value.get('diagnostic_requested') is True).lower()}",
            f"Private key read: {str(value.get('private_key_read') is True).lower()}",
            f"Derived wallet match: {clean_text(value.get('derived_wallet_matches_expected')) or 'unknown'}",
            f"Diagnostic challenge signed: {str(value.get('diagnostic_challenge_signed') is True).lower()}",
            "Order payload signing: blocked",
            "Order submission: blocked",
            "Order cancellation: blocked",
            "Authenticated trading: blocked",
            "Live trading: blocked",
            "Allowed for live: false",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_guarded_signer_diagnostic_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    paths = dict(value.get("artifact_paths", {}))
    lines = [
        "# PMBOT Guarded Signer Diagnostic Smoke 069A",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Diagnostic status: `{value.get('diagnostic_status')}`",
        f"- Market: `{value.get('market_symbol') or value.get('market')}`",
        f"- Strategy: `{value.get('strategy_name')}`",
        "- Default mode reads private key: `false`",
        f"- Diagnostic requested: `{str(value.get('diagnostic_requested') is True).lower()}`",
        f"- Private key read: `{str(value.get('private_key_read') is True).lower()}`",
        f"- Private key present: `{str(value.get('private_key_present') is True).lower()}`",
        f"- Private key format valid: `{str(value.get('private_key_format_valid') is True).lower()}`",
        f"- Wallet address present: `{str(value.get('wallet_address_present') is True).lower()}`",
        f"- Derived wallet match: `{value.get('derived_wallet_matches_expected')}`",
        f"- Diagnostic challenge signed: `{str(value.get('diagnostic_challenge_signed') is True).lower()}`",
        "- Order payload signing: `blocked`",
        "- Signed order generation: `blocked`",
        "- Order submission: `blocked`",
        "- Order cancellation: `blocked`",
        "- Authenticated trading: `blocked`",
        "- Live trading: `blocked`",
        "- Allowed for live: `false`",
        "- Private key value emitted: `false`",
        "- Raw secret values emitted: `false`",
        "- Full diagnostic signature emitted: `false`",
        "",
        "## Diagnostic Scope",
        "",
        "- the explicit diagnostic flag is required before reading `POLYMARKET_PRIVATE_KEY`",
        "- the diagnostic challenge is fixed and not an order payload",
        "- address values are redacted to prefix and suffix only",
        "- diagnostic signature output is limited to a redacted fingerprint and length",
        "- no order payload is signed, generated, submitted, or canceled",
        "- no authenticated trading endpoint is called",
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


def diagnostic_challenge_is_order_payload_safe(challenge: str) -> bool:
    text = clean_text(challenge)
    if text != DIAGNOSTIC_CHALLENGE:
        return False
    if "{" in text or "}" in text:
        return False
    return ORDER_PAYLOAD_FIELD_PATTERN.search(text) is None


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "guarded signer diagnostic smoke is no-order/no-submit; unsupported live/auth/wallet/order flag(s): "
            + ", ".join(requested)
        )


def _run_diagnostic_path(
    *,
    allow_private_key_diagnostic: bool,
    env: Mapping[str, str] | None,
    account_adapter: SignerDiagnosticAdapter | None,
) -> dict[str, Any]:
    base = {
        "status": "blocked_diagnostic_not_requested",
        "diagnostic_status": DIAGNOSTIC_STATUS_NOT_REQUESTED,
        "private_key_read": False,
        "private_key_present": False,
        "private_key_format_valid": False,
        "wallet_address_read": False,
        "wallet_address_present": False,
        "expected_wallet_address_redacted": "not_read",
        "derived_wallet_address_redacted": "not_derived",
        "derived_wallet_matches_expected": "unknown",
        "diagnostic_challenge_signing_attempted": False,
        "diagnostic_challenge_signed": False,
        "diagnostic_signature_redacted": "",
        "dependency_status": "not_loaded",
        "block_reason": DIAGNOSTIC_STATUS_NOT_REQUESTED,
    }
    if allow_private_key_diagnostic is not True:
        return base

    source = env if env is not None else _process_env()
    key_value = clean_text(source.get(KEY_ENV_NAME, ""))
    expected_address = clean_text(source.get(WALLET_ENV_NAME, ""))
    base.update(
        {
            "private_key_read": True,
            "private_key_present": bool(key_value),
            "wallet_address_read": True,
            "wallet_address_present": bool(expected_address),
            "expected_wallet_address_redacted": _redact_address(expected_address) if expected_address else "missing",
            "derived_wallet_address_redacted": "not_derived",
            "derived_wallet_matches_expected": "unknown",
        }
    )
    if not key_value:
        return _blocked(base, DIAGNOSTIC_STATUS_MISSING_PRIVATE_KEY)
    if not _valid_private_key_format(key_value):
        return _blocked(base, DIAGNOSTIC_STATUS_INVALID_KEY_FORMAT)
    base["private_key_format_valid"] = True
    if not expected_address:
        return _blocked(base, DIAGNOSTIC_STATUS_MISSING_WALLET_ADDRESS)
    if not diagnostic_challenge_is_order_payload_safe(DIAGNOSTIC_CHALLENGE):
        return _blocked(base, DIAGNOSTIC_STATUS_DIAGNOSTIC_FAILED)

    adapter = account_adapter or EthAccountSignerDiagnosticAdapter()
    try:
        derived_address = adapter.derive_address(key_value)
    except DependencyMissingError:
        base["dependency_status"] = DIAGNOSTIC_STATUS_DEPENDENCY_MISSING
        return _blocked(base, DIAGNOSTIC_STATUS_DEPENDENCY_MISSING)
    except Exception:
        return _blocked(base, DIAGNOSTIC_STATUS_DIAGNOSTIC_FAILED)

    base["dependency_status"] = "available"
    base["derived_wallet_address_redacted"] = _redact_address(derived_address)
    wallet_matches = _addresses_match(derived_address, expected_address)
    base["derived_wallet_matches_expected"] = wallet_matches
    if wallet_matches is not True:
        return _blocked(base, DIAGNOSTIC_STATUS_WALLET_MISMATCH)

    base["diagnostic_challenge_signing_attempted"] = True
    try:
        diagnostic_signature = adapter.sign_diagnostic_challenge(key_value, DIAGNOSTIC_CHALLENGE)
    except DependencyMissingError:
        base["dependency_status"] = DIAGNOSTIC_STATUS_DEPENDENCY_MISSING
        return _blocked(base, DIAGNOSTIC_STATUS_DEPENDENCY_MISSING)
    except Exception:
        return _blocked(base, DIAGNOSTIC_STATUS_DIAGNOSTIC_FAILED)

    base.update(
        {
            "status": DIAGNOSTIC_STATUS_DIAGNOSTIC_OK,
            "diagnostic_status": DIAGNOSTIC_STATUS_DIAGNOSTIC_OK,
            "diagnostic_challenge_signed": True,
            "diagnostic_signature_redacted": _redact_signature(diagnostic_signature),
            "block_reason": "live_trading_still_blocked",
        }
    )
    return base


def _build_latest_status(
    *,
    market_symbol: str,
    strategy_name: str,
    diagnostic: Mapping[str, Any],
    path_refs: Mapping[str, str],
    generated_at: str,
) -> dict[str, Any]:
    value = {
        "contract_version": GUARDED_SIGNER_DIAGNOSTIC_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": diagnostic["status"],
        "diagnostic_status": diagnostic["diagnostic_status"],
        "mode": MODE,
        "execution_mode": EXECUTION_MODE,
        "market": market_symbol,
        "market_symbol": market_symbol,
        "strategy_name": strategy_name,
        "diagnostic_requested": diagnostic["private_key_read"] is True,
        "private_key_read": diagnostic["private_key_read"],
        "private_key_present": diagnostic["private_key_present"],
        "private_key_format_valid": diagnostic["private_key_format_valid"],
        "wallet_address_present": diagnostic["wallet_address_present"],
        "expected_wallet_address_redacted": diagnostic["expected_wallet_address_redacted"],
        "derived_wallet_address_redacted": diagnostic["derived_wallet_address_redacted"],
        "derived_wallet_matches_expected": diagnostic["derived_wallet_matches_expected"],
        "diagnostic_challenge_signed": diagnostic["diagnostic_challenge_signed"],
        "diagnostic_signature_redacted": diagnostic["diagnostic_signature_redacted"],
        "order_payload_signing": "blocked",
        "order_submission": "blocked",
        "order_cancel": "blocked",
        "authenticated_trading": "blocked",
        "live_trading": "blocked",
        "allowed_for_live": False,
        "artifact_path": clean_text(path_refs.get("result")),
        "latest_status_path": clean_text(path_refs.get("latest_status")),
        "redaction_policy_path": clean_text(path_refs.get("redaction_policy")),
        "safety_contract_path": clean_text(path_refs.get("safety_contract")),
        "operator_markdown_path": clean_text(path_refs.get("operator_md")),
        "operator_summary": _operator_summary_for_status(diagnostic["diagnostic_status"]),
        "generated_at": generated_at,
    }
    value.update(guarded_signer_diagnostic_safety_flags())
    return value


def _blocked(value: dict[str, Any], diagnostic_status: str) -> dict[str, Any]:
    value.update(
        {
            "status": f"blocked_{diagnostic_status}",
            "diagnostic_status": diagnostic_status,
            "block_reason": diagnostic_status,
            "diagnostic_challenge_signed": False,
            "diagnostic_signature_redacted": "",
        }
    )
    return value


def _operator_summary_for_status(diagnostic_status: str) -> str:
    summaries = {
        DIAGNOSTIC_STATUS_NOT_REQUESTED: (
            "Default dry-run completed without reading POLYMARKET_PRIVATE_KEY. "
            "Use the explicit diagnostic flag for the guarded local signer check."
        ),
        DIAGNOSTIC_STATUS_DEPENDENCY_MISSING: (
            "The diagnostic was requested, but the optional eth-account dependency was unavailable. "
            "The runner failed closed before signing the diagnostic challenge."
        ),
        DIAGNOSTIC_STATUS_MISSING_PRIVATE_KEY: (
            "The diagnostic was requested, but POLYMARKET_PRIVATE_KEY was not present in the environment."
        ),
        DIAGNOSTIC_STATUS_INVALID_KEY_FORMAT: (
            "The diagnostic was requested, but POLYMARKET_PRIVATE_KEY did not match the required 0x-prefixed "
            "64-hex-character format."
        ),
        DIAGNOSTIC_STATUS_MISSING_WALLET_ADDRESS: (
            "The diagnostic was requested, but POLYMARKET_WALLET_ADDRESS was missing, so wallet matching "
            "remained blocked."
        ),
        DIAGNOSTIC_STATUS_WALLET_MISMATCH: (
            "The diagnostic derived a wallet address, but it did not match POLYMARKET_WALLET_ADDRESS. "
            "The challenge was not signed."
        ),
        DIAGNOSTIC_STATUS_DIAGNOSTIC_OK: (
            "The guarded diagnostic derived the expected wallet and signed only the fixed non-order challenge. "
            "Live trading remains blocked."
        ),
        DIAGNOSTIC_STATUS_DIAGNOSTIC_FAILED: (
            "The diagnostic failed closed before completing the guarded signer check."
        ),
    }
    return summaries.get(clean_text(diagnostic_status), summaries[DIAGNOSTIC_STATUS_DIAGNOSTIC_FAILED])


def _process_env() -> Mapping[str, str]:
    import os

    return os.environ


def _load_eth_account() -> Any:
    try:
        from eth_account import Account
    except ImportError as exc:
        raise DependencyMissingError("eth-account dependency missing") from exc
    return Account


def _load_encode_defunct() -> Any:
    try:
        from eth_account.messages import encode_defunct
    except ImportError as exc:
        raise DependencyMissingError("eth-account dependency missing") from exc
    return encode_defunct


def _valid_private_key_format(value: str) -> bool:
    return PRIVATE_KEY_PATTERN.fullmatch(clean_text(value)) is not None


def _addresses_match(left: str, right: str) -> bool | str:
    if ADDRESS_PATTERN.fullmatch(clean_text(left)) is None:
        return "unknown"
    if ADDRESS_PATTERN.fullmatch(clean_text(right)) is None:
        return "unknown"
    return clean_text(left).lower() == clean_text(right).lower()


def _redact_address(value: str) -> str:
    text = clean_text(value)
    if not text:
        return "missing"
    if ADDRESS_PATTERN.fullmatch(text) is None:
        return "present_invalid_address_format"
    return f"{text[:6]}...{text[-4:]}"


def _redact_signature(value: str) -> str:
    text = clean_text(value)
    if not text:
        return ""
    raw = _signature_bytes(text)
    digest = hashlib.sha256(raw).hexdigest()
    return f"redacted:sha256:{digest[:16]}:len:{len(raw)}"


def _signature_to_text(value: Any) -> str:
    if isinstance(value, bytes):
        return "0x" + value.hex()
    if hasattr(value, "hex"):
        rendered = value.hex()
        return rendered if str(rendered).startswith("0x") else "0x" + str(rendered)
    return clean_text(value)


def _signature_bytes(value: str) -> bytes:
    text = clean_text(value)
    hex_text = text[2:] if text.lower().startswith("0x") else text
    if hex_text and len(hex_text) % 2 == 0:
        try:
            return bytes.fromhex(hex_text)
        except ValueError:
            pass
    return text.encode("utf-8")


def _sha256_text(value: str) -> str:
    return hashlib.sha256(clean_text(value).encode("utf-8")).hexdigest()
