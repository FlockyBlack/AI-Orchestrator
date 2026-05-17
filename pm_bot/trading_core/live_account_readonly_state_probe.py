from __future__ import annotations

import importlib
from importlib import metadata as importlib_metadata
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from pm_bot.trading_core.live_account_readonly_state_models import (
    ACCOUNT_CONFIG_ENV_VARS,
    BLOCKED_HTTP_METHODS,
    CLOB_SDK_IMPORT_CANDIDATES,
    DEFAULT_CLOB_HOST,
    DEFAULT_MARKET,
    DEFAULT_STRATEGY,
    EXECUTION_MODE,
    EXPECTED_PIP_PACKAGE,
    EXPECTED_SDK_INSTALL_COMMAND,
    EXPECTED_SDK_MODULE,
    POLYGON_CHAIN_ID,
    POLYMARKET_API_KEY_ENV,
    POLYMARKET_API_PASSPHRASE_ENV,
    POLYMARKET_API_SECRET_ENV,
    POLYMARKET_FUNDER_ADDRESS_ENV,
    POLYMARKET_SIGNATURE_TYPE_ENV,
    POLYMARKET_WALLET_ADDRESS_ENV,
    READONLY_HTTP_METHOD,
    REQUIRED_L2_CREDENTIAL_ENV_VARS,
    STATUS_BLOCKED_CLIENT_INIT_ERROR,
    STATUS_BLOCKED_CREDENTIAL_OBJECT_ERROR,
    STATUS_BLOCKED_DEPENDENCY_MISSING,
    STATUS_BLOCKED_METHOD_UNAVAILABLE,
    STATUS_BLOCKED_MISSING_CREDENTIALS,
    STATUS_BLOCKED_PROBE_FAILED,
    STATUS_BLOCKED_SDK_REQUIRES_SIGNER,
    STATUS_SUCCEEDED_LIVE_BLOCKED,
    SUPPORTED_SDK_MODULES,
    TASK_ID,
    LiveAccountCredentialPresence,
    LiveAccountReadOnlyDiagnostics,
    LiveAccountReadOnlyLatestStatus,
    LiveAccountReadOnlyProbeAttempt,
    LiveAccountReadOnlyProbeResult,
    LiveAccountRedactedStatus,
    LiveAccountSdkStatus,
    build_blocker,
    build_redaction_policy,
    live_account_readonly_state_safety_flags,
)
from pm_bot.trading_core.artifact_resolution import resolve_artifact_subdir
from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text

ARTIFACT_DIR_NAME = "live_account_readonly_state_probe_070c"
DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts") / ARTIFACT_DIR_NAME

FORBIDDEN_RUNTIME_FLAGS = (
    "--live",
    "--live-execution",
    "--execute",
    "--trade",
    "--wallet",
    "--wallet-connect",
    "--private-key",
    "--signing",
    "--sign",
    "--submit",
    "--cancel",
    "--order",
    "--post",
    "--put",
    "--patch",
    "--delete",
    "--derive-api-key",
    "--create-api-key",
)

_ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
_CANDIDATE_PIP_PACKAGES = {
    "py_clob_client": ("py-clob-client",),
    "py_clob_client.client": ("py-clob-client",),
    "py_clob_client_v2": ("py-clob-client-v2", "py-clob-client"),
}


@dataclass(frozen=True)
class LiveAccountSdkBinding:
    status: str
    module_name: str = ""
    attempted_modules: tuple[str, ...] = SUPPORTED_SDK_MODULES
    expected_sdk_module: str = EXPECTED_SDK_MODULE
    expected_pip_package: str = EXPECTED_PIP_PACKAGE
    expected_install_command: str = EXPECTED_SDK_INSTALL_COMMAND
    python_executable: str = ""
    sdk_import_reports: tuple[Mapping[str, Any], ...] = ()
    pip_package_visibility: tuple[Mapping[str, Any], ...] = ()
    client_class: Any = None
    creds_class: Any = None
    open_order_params_class: Any = None
    balance_allowance_params_class: Any = None
    asset_type_class: Any = None
    error_type: str = ""
    error_message_sanitized: str = ""


SdkLoader = Callable[[], LiveAccountSdkBinding]


def live_account_readonly_state_probe_artifact_paths(
    artifact_dir: str | Path | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Path]:
    root = resolve_artifact_subdir(
        ARTIFACT_DIR_NAME,
        artifact_dir=artifact_dir,
        environ=environ,
    )
    return {
        "root": root,
        "result": root / "live_account_readonly_state_probe_070c_result.json",
        "latest_status": root / "latest_live_account_readonly_state_status_070c.json",
        "diagnostics": root / "live_account_readonly_state_diagnostics_070c.json",
        "redaction_policy": root / "live_account_readonly_state_redaction_policy_070c.json",
        "operator_md": root / "live_account_readonly_state_operator_summary_070c.md",
    }


def run_live_account_readonly_state_probe(
    *,
    market: str = DEFAULT_MARKET,
    strategy: str = DEFAULT_STRATEGY,
    dry_run: bool = True,
    artifact_dir: str | Path | None = None,
    environ: Mapping[str, str] | None = None,
    sdk_loader: SdkLoader | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("live account read-only state probe requires --dry-run; order execution is blocked")

    market_symbol = clean_text(market).upper() or DEFAULT_MARKET
    strategy_name = clean_text(strategy) or DEFAULT_STRATEGY
    active_environ = _active_environ(environ)
    paths = live_account_readonly_state_probe_artifact_paths(artifact_dir, environ=active_environ)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    credential_presence, credential_values, account_config_values = _read_presence_and_account_config(
        active_environ,
        generated_at=generated_at,
    )
    account_status = _build_account_status(account_config_values, generated_at=generated_at)
    blockers: list[dict[str, Any]] = []
    probe_attempts: list[dict[str, Any]] = []
    redaction_policy = build_redaction_policy(generated_at=generated_at)
    binding = (sdk_loader or load_polymarket_clob_sdk)()

    if credential_presence.get("missing_l2_count", 0):
        status = STATUS_BLOCKED_MISSING_CREDENTIALS
        blockers.append(
            build_blocker(
                "missing_l2_api_credentials",
                "credential_presence",
                "One or more required L2 API credential env vars are missing; private key fallback is forbidden.",
            )
        )
        if binding.status != "available":
            blockers.append(
                build_blocker(
                    "polymarket_clob_sdk_dependency_missing",
                    "dependency",
                    "No supported official Polymarket Python CLOB SDK module is importable in this environment.",
                )
            )
        sdk_status = _sdk_status_from_binding(
            binding,
            l2_credentials_object_created=False,
            sdk_client_created=False,
            sdk_requires_signer_without_private_key=False,
            open_orders_method_available=False,
            balance_allowance_method_available=False,
            status_override="not_checked_missing_credentials" if binding.status == "available" else "",
            generated_at=generated_at,
        )
    else:
        if binding.status != "available":
            status = STATUS_BLOCKED_DEPENDENCY_MISSING
            blockers.append(
                build_blocker(
                    "polymarket_clob_sdk_dependency_missing",
                    "dependency",
                    "No supported official Polymarket Python CLOB SDK module is importable in this environment.",
                )
            )
            sdk_status = _sdk_status_from_binding(
                binding,
                l2_credentials_object_created=False,
                sdk_client_created=False,
                sdk_requires_signer_without_private_key=False,
                open_orders_method_available=False,
                balance_allowance_method_available=False,
                generated_at=generated_at,
            )
        else:
            sdk_status, probe_attempts, blockers, status = _run_sdk_probe(
                binding=binding,
                credential_values=credential_values,
                account_config_values=account_config_values,
                generated_at=generated_at,
            )

    attempted = any(row.get("attempted") is True for row in probe_attempts)
    performed = any(row.get("succeeded") is True for row in probe_attempts)
    open_orders_status = _probe_status(probe_attempts, "open_orders_count")
    open_order_count = _first_open_order_count(probe_attempts)
    balance_allowance_status = _probe_status(probe_attempts, "balance_allowance_availability")
    balance_allowance_availability_status = _balance_allowance_availability_status(probe_attempts)

    diagnostics = LiveAccountReadOnlyDiagnostics(
        market=market_symbol,
        strategy=strategy_name,
        credential_presence=credential_presence,
        account_status=account_status,
        sdk_status=sdk_status,
        probe_attempts=tuple(probe_attempts),
        blockers=tuple(blockers),
        generated_at=generated_at,
    ).to_dict()
    latest_status = LiveAccountReadOnlyLatestStatus(
        market=market_symbol,
        strategy=strategy_name,
        status=status,
        credential_presence_status=clean_text(credential_presence.get("status")),
        sdk_status=clean_text(sdk_status.get("status")),
        selected_sdk_module=clean_text(sdk_status.get("selected_sdk_module")),
        expected_sdk_module=clean_text(sdk_status.get("expected_sdk_module")),
        expected_install_command=clean_text(sdk_status.get("expected_install_command")),
        python_executable=clean_text(sdk_status.get("python_executable")),
        sdk_import_reports=tuple(
            row for row in sdk_status.get("sdk_import_reports", []) if isinstance(row, Mapping)
        ),
        pip_package_visibility=tuple(
            row for row in sdk_status.get("pip_package_visibility", []) if isinstance(row, Mapping)
        ),
        account_status=clean_text(account_status.get("status")),
        wallet_address_status=clean_text(account_status.get("wallet_address_status")),
        signature_type_status=clean_text(account_status.get("signature_type_status")),
        funder_address_status=clean_text(account_status.get("funder_address_status")),
        wallet_address_redacted=clean_text(account_status.get("wallet_address_redacted")),
        signature_type_redacted=clean_text(account_status.get("signature_type_redacted")),
        funder_address_redacted=clean_text(account_status.get("funder_address_redacted")),
        open_orders_status=open_orders_status,
        open_order_count=open_order_count,
        balance_allowance_status=balance_allowance_status,
        balance_allowance_availability_status=balance_allowance_availability_status,
        account_state_probe_attempted=attempted,
        account_state_probe_performed=performed,
        blocker_count=len(blockers),
        blockers=tuple(blockers),
        artifact_path=path_refs["result"],
        latest_status_path=path_refs["latest_status"],
        diagnostics_path=path_refs["diagnostics"],
        redaction_policy_path=path_refs["redaction_policy"],
        operator_summary_path=path_refs["operator_md"],
        generated_at=generated_at,
    ).to_dict()
    result = LiveAccountReadOnlyProbeResult(
        market=market_symbol,
        strategy=strategy_name,
        status=status,
        credential_presence=credential_presence,
        account_status=account_status,
        sdk_status=sdk_status,
        diagnostics=diagnostics,
        redaction_policy=redaction_policy,
        latest_status=latest_status,
        blockers=tuple(blockers),
        artifact_paths=path_refs,
        operator_summary=_operator_summary(latest_status),
        generated_at=generated_at,
    ).to_dict()

    write_json(paths["diagnostics"], diagnostics)
    write_json(paths["redaction_policy"], redaction_policy)
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], result)
    write_text(paths["operator_md"], render_live_account_readonly_state_probe_markdown(result))
    return result


def load_polymarket_clob_sdk() -> LiveAccountSdkBinding:
    imported_modules: dict[str, Any] = {}
    reports: list[dict[str, Any]] = []
    for module_name in CLOB_SDK_IMPORT_CANDIDATES:
        module, report = _import_sdk_candidate(module_name)
        if module is not None:
            imported_modules[module_name] = module
        reports.append(report)
    pip_visibility = _pip_package_visibility()
    selected = _select_sdk_binding(
        imported_modules=imported_modules,
        reports=reports,
        pip_visibility=pip_visibility,
    )
    if selected is not None:
        return selected
    errors = [
        f"{row['module_name']}:{row['import_error_type'] or row['import_status']}"
        for row in reports
        if row.get("import_status") != "installed"
    ]
    return LiveAccountSdkBinding(
        status="dependency_missing",
        attempted_modules=tuple(CLOB_SDK_IMPORT_CANDIDATES),
        python_executable=sys.executable,
        sdk_import_reports=tuple(reports),
        pip_package_visibility=tuple(pip_visibility),
        error_type="ImportError",
        error_message_sanitized=", ".join(errors) or "supported_sdk_modules_not_importable",
    )


def _import_sdk_candidate(module_name: str) -> tuple[Any | None, dict[str, Any]]:
    package_names = _CANDIDATE_PIP_PACKAGES.get(module_name, (EXPECTED_PIP_PACKAGE,))
    base_report: dict[str, Any] = {
        "module_name": module_name,
        "installed": False,
        "import_status": "missing",
        "import_error_type": "ModuleNotFoundError",
        "import_error_message_sanitized": "",
        "pip_package_candidates": list(package_names),
        "selected": False,
        "safe_for_artifacts": True,
    }
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if _module_not_found_matches_candidate(exc, module_name):
            return None, base_report
        report = dict(base_report)
        report["import_status"] = "import_error"
        report["import_error_type"] = type(exc).__name__
        report["import_error_message_sanitized"] = (
            f"{module_name} import failed because dependency {clean_text(exc.name)} is missing"
        )
        return None, report
    except Exception as exc:  # pragma: no cover - exact third-party import errors vary by environment.
        report = dict(base_report)
        report["import_status"] = "import_error"
        report["import_error_type"] = type(exc).__name__
        report["import_error_message_sanitized"] = f"{module_name} import raised {type(exc).__name__}; message redacted"
        return None, report
    report = dict(base_report)
    report["installed"] = True
    report["import_status"] = "installed"
    report["import_error_type"] = ""
    return module, report


def _module_not_found_matches_candidate(exc: ModuleNotFoundError, module_name: str) -> bool:
    missing_name = clean_text(getattr(exc, "name", ""))
    if not missing_name:
        return True
    return module_name == missing_name or module_name.startswith(missing_name + ".")


def _pip_package_visibility() -> tuple[dict[str, Any], ...]:
    package_names = _dedupe_text(
        [EXPECTED_PIP_PACKAGE]
        + [package for packages in _CANDIDATE_PIP_PACKAGES.values() for package in packages]
    )
    rows: list[dict[str, Any]] = []
    for package_name in package_names:
        row = {
            "package_name": package_name,
            "visible": False,
            "version": "",
            "error_type": "PackageNotFoundError",
            "safe_for_artifacts": True,
        }
        try:
            version = importlib_metadata.version(package_name)
        except importlib_metadata.PackageNotFoundError:
            rows.append(row)
            continue
        except Exception as exc:  # pragma: no cover - metadata backend errors vary by environment.
            row["error_type"] = type(exc).__name__
            rows.append(row)
            continue
        row["visible"] = True
        row["version"] = clean_text(version)
        row["error_type"] = ""
        rows.append(row)
    return tuple(rows)


def _dedupe_text(values: Sequence[Any]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = clean_text(value)
        if text and text not in result:
            result.append(text)
    return result


def _select_sdk_binding(
    *,
    imported_modules: Mapping[str, Any],
    reports: Sequence[Mapping[str, Any]],
    pip_visibility: Sequence[Mapping[str, Any]],
) -> LiveAccountSdkBinding | None:
    if "py_clob_client.client" in imported_modules:
        package = imported_modules.get("py_clob_client")
        client_module = imported_modules["py_clob_client.client"]
        types_module = _import_supporting_module("py_clob_client.clob_types")
        return _sdk_binding_from_modules(
            selected_module_name="py_clob_client.client",
            reports=reports,
            pip_visibility=pip_visibility,
            package_module=package,
            client_module=client_module,
            types_module=types_module,
        )
    if "py_clob_client_v2" in imported_modules:
        package = imported_modules["py_clob_client_v2"]
        types_module = _import_supporting_module("py_clob_client_v2.clob_types")
        return _sdk_binding_from_modules(
            selected_module_name="py_clob_client_v2",
            reports=reports,
            pip_visibility=pip_visibility,
            package_module=package,
            client_module=package,
            types_module=types_module,
        )
    package = imported_modules.get("py_clob_client")
    if package is not None and getattr(package, "ClobClient", None) is not None:
        types_module = _import_supporting_module("py_clob_client.clob_types")
        return _sdk_binding_from_modules(
            selected_module_name="py_clob_client",
            reports=reports,
            pip_visibility=pip_visibility,
            package_module=package,
            client_module=package,
            types_module=types_module,
        )
    return None


def _import_supporting_module(module_name: str) -> Any | None:
    try:
        return importlib.import_module(module_name)
    except Exception:
        return None


def _sdk_binding_from_modules(
    *,
    selected_module_name: str,
    reports: Sequence[Mapping[str, Any]],
    pip_visibility: Sequence[Mapping[str, Any]],
    package_module: Any | None,
    client_module: Any | None,
    types_module: Any | None,
) -> LiveAccountSdkBinding:
    selected_reports = []
    for row in reports:
        report = dict(row)
        report["selected"] = clean_text(row.get("module_name")) == selected_module_name
        selected_reports.append(report)
    client_class = _first_attr(client_module, package_module, "ClobClient")
    return LiveAccountSdkBinding(
        status="available",
        module_name=selected_module_name,
        attempted_modules=tuple(CLOB_SDK_IMPORT_CANDIDATES),
        python_executable=sys.executable,
        sdk_import_reports=tuple(selected_reports),
        pip_package_visibility=tuple(pip_visibility),
        client_class=client_class,
        creds_class=_first_attr(package_module, client_module, types_module, "ApiCreds"),
        open_order_params_class=_first_attr(package_module, client_module, types_module, "OpenOrderParams"),
        balance_allowance_params_class=_first_attr(
            package_module,
            client_module,
            types_module,
            "BalanceAllowanceParams",
        ),
        asset_type_class=_first_attr(package_module, client_module, types_module, "AssetType"),
    )


def _first_attr(*modules_and_name: Any) -> Any:
    *modules, attr_name = modules_and_name
    for module in modules:
        if module is not None and getattr(module, attr_name, None) is not None:
            return getattr(module, attr_name)
    return None


def render_live_account_readonly_state_probe_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    open_count = value.get("open_order_count")
    open_count_text = "not_available" if open_count is None else str(open_count)
    return "\n".join(
        [
            "Live account read-only state probe completed.",
            f"Status: {clean_text(value.get('status'))}",
            f"Market: {clean_text(value.get('market'))}",
            f"Strategy: {clean_text(value.get('strategy'))}",
            f"Probe read-only: {str(value.get('probe_is_readonly') is True).lower()}",
            "Allowed for live: false",
            "Private key read: false",
            "Signer instantiated: false",
            "Order submission: blocked",
            "Order cancellation: blocked",
            "Wallet connection: blocked",
            f"Wallet status: {clean_text(value.get('wallet_address_status')) or 'missing'}",
            f"Signature type: {clean_text(value.get('signature_type_redacted')) or 'missing'}",
            f"Funder status: {clean_text(value.get('funder_address_status')) or 'missing'}",
            f"SDK status: {clean_text(value.get('sdk_status'))}",
            f"Selected SDK: {clean_text(value.get('selected_sdk_module')) or 'not_available'}",
            f"Expected SDK: {clean_text(value.get('expected_sdk_module')) or EXPECTED_SDK_MODULE}",
            f"Expected install command: {clean_text(value.get('expected_install_command')) or EXPECTED_SDK_INSTALL_COMMAND}",
            f"Python executable: {clean_text(value.get('python_executable')) or sys.executable}",
            f"Open orders status: {clean_text(value.get('open_orders_status')) or 'not_available'}",
            f"Open order count: {open_count_text}",
            f"Balance allowance status: {clean_text(value.get('balance_allowance_status')) or 'not_available'}",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_live_account_readonly_state_probe_markdown(result: Mapping[str, Any]) -> str:
    value = dict(result or {})
    latest = dict(value.get("latest_status", {}))
    diagnostics = dict(value.get("diagnostics", {}))
    credential_presence = dict(value.get("credential_presence", {}))
    account_status = dict(value.get("account_status", {}))
    sdk_status = dict(value.get("sdk_status", {}))
    attempts = [dict(row) for row in diagnostics.get("probe_attempts", []) if isinstance(row, Mapping)]
    sdk_import_reports = [dict(row) for row in sdk_status.get("sdk_import_reports", []) if isinstance(row, Mapping)]
    pip_visibility = [dict(row) for row in sdk_status.get("pip_package_visibility", []) if isinstance(row, Mapping)]
    blockers = [dict(row) for row in value.get("blockers", []) if isinstance(row, Mapping)]
    open_count = latest.get("open_order_count")
    open_count_text = "not_available" if open_count is None else str(open_count)
    lines = [
        "# PMBOT Live Account Read-Only State Probe 070C",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Market: `{value.get('market')}`",
        f"- Strategy: `{value.get('strategy')}`",
        f"- execution_mode: `{EXECUTION_MODE}`",
        "- probe_is_readonly: `true`",
        "- allowed_for_live: `false`",
        "- private_key_read: `false`",
        "- signer_instantiated: `false`",
        "",
        "## Credential Boundary",
        "",
        f"- L2 credential presence status: `{credential_presence.get('status')}`",
        f"- Configured L2 env count: `{credential_presence.get('configured_l2_count')}`",
        f"- Missing L2 env count: `{credential_presence.get('missing_l2_count')}`",
        "- Env vars used for auth: `POLYMARKET_API_KEY`, `POLYMARKET_API_SECRET`, `POLYMARKET_API_PASSPHRASE`",
        "- Wallet, signature type, and funder are presence/redaction diagnostics only",
        "- Private key and wallet private-key env vars read: `false`",
        "- Raw credential values emitted: `false`",
        "",
        "## Redacted Account Status",
        "",
        f"- Wallet address: `{account_status.get('wallet_address_status')}`",
        f"- Signature type: `{account_status.get('signature_type_redacted') or 'missing'}`",
        f"- Funder address: `{account_status.get('funder_address_status')}`",
        "",
        "## SDK Account State Probe",
        "",
        f"- SDK status: `{sdk_status.get('status')}`",
        f"- Selected SDK: `{sdk_status.get('selected_sdk_module') or 'not_available'}`",
        f"- Expected SDK: `{sdk_status.get('expected_sdk_module') or EXPECTED_SDK_MODULE}`",
        f"- Expected install command: `{sdk_status.get('expected_install_command') or EXPECTED_SDK_INSTALL_COMMAND}`",
        f"- Python executable: `{sdk_status.get('python_executable') or sys.executable}`",
        f"- Read-only probe attempted: `{str(latest.get('account_state_probe_attempted') is True).lower()}`",
        f"- Read-only probe performed: `{str(latest.get('account_state_probe_performed') is True).lower()}`",
        f"- Open orders status: `{latest.get('open_orders_status') or 'not_available'}`",
        f"- Open order count: `{open_count_text}`",
        f"- Balance/allowance status: `{latest.get('balance_allowance_status') or 'not_available'}`",
        f"- Balance/allowance availability: `{latest.get('balance_allowance_availability_status') or 'not_available'}`",
        "",
        "## SDK Import Candidates",
        "",
        *bullet_lines(
            f"`{row.get('module_name')}`: `{row.get('import_status')}`"
            + (
                f" error=`{row.get('import_error_type')}`"
                if row.get("import_error_type")
                else ""
            )
            + (" selected=`true`" if row.get("selected") is True else "")
            for row in sdk_import_reports
        ),
        "",
        "## Pip Package Visibility",
        "",
        *bullet_lines(
            f"`{row.get('package_name')}`: `{'visible' if row.get('visible') is True else 'missing'}`"
            + (f" version=`{row.get('version')}`" if row.get("version") else "")
            + (f" error=`{row.get('error_type')}`" if row.get("error_type") else "")
            for row in pip_visibility
        ),
        "",
        "## Attempts",
        "",
        *bullet_lines(
            f"`{row.get('probe_name')}` via `{row.get('sdk_method')}`: `{row.get('status')}`"
            for row in attempts
        ),
        "",
        "## Safety",
        "",
        "- no order submission",
        "- no order cancellation",
        "- no order signing",
        "- no signer instantiation",
        "- no private-key read",
        "- no wallet connection",
        "- no POST/PUT/PATCH/DELETE trading call from PMBOT code",
        "- SDK responses are summarized and redacted",
        "- allowed_for_live remains `false`",
        "",
        "## Blockers",
        "",
        *bullet_lines(f"`{row.get('blocker_id')}` - {row.get('reason')}" for row in blockers),
    ]
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "live account read-only state probe blocks live/wallet/signing/order/write flags: "
            + ", ".join(requested)
        )


def _run_sdk_probe(
    *,
    binding: LiveAccountSdkBinding,
    credential_values: Mapping[str, str],
    account_config_values: Mapping[str, str],
    generated_at: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], str]:
    blockers: list[dict[str, Any]] = []
    probe_attempts: list[dict[str, Any]] = []
    l2_credentials_object_created = False
    sdk_client_created = False
    sdk_requires_signer_without_private_key = False
    open_method_available = False
    balance_method_available = False
    secret_values = tuple(credential_values.values()) + tuple(account_config_values.values())

    client_class = binding.client_class
    creds_class = binding.creds_class
    if client_class is None or creds_class is None:
        blockers.append(
            build_blocker(
                "sdk_missing_required_classes",
                "dependency",
                "The selected SDK is importable but does not expose the expected client or API credentials class.",
            )
        )
        sdk_status = _sdk_status_from_binding(
            binding,
            l2_credentials_object_created=False,
            sdk_client_created=False,
            sdk_requires_signer_without_private_key=False,
            open_orders_method_available=False,
            balance_allowance_method_available=False,
            status_override=STATUS_BLOCKED_METHOD_UNAVAILABLE,
            generated_at=generated_at,
        )
        return sdk_status, probe_attempts, blockers, STATUS_BLOCKED_METHOD_UNAVAILABLE

    try:
        creds_obj = _build_api_creds_object(creds_class, credential_values)
        l2_credentials_object_created = True
    except Exception as exc:
        blockers.append(
            build_blocker(
                "sdk_credentials_object_creation_failed",
                "sdk_credentials",
                "The SDK API credentials object could not be created from the configured L2 env vars.",
            )
        )
        sdk_status = _sdk_status_from_binding(
            binding,
            l2_credentials_object_created=False,
            sdk_client_created=False,
            sdk_requires_signer_without_private_key=False,
            open_orders_method_available=False,
            balance_allowance_method_available=False,
            status_override=STATUS_BLOCKED_CREDENTIAL_OBJECT_ERROR,
            error_type=type(exc).__name__,
            error_message_sanitized=_redact_text(str(exc), secret_values),
            generated_at=generated_at,
        )
        return sdk_status, probe_attempts, blockers, STATUS_BLOCKED_CREDENTIAL_OBJECT_ERROR

    try:
        client = _build_sdk_client(client_class, creds_obj)
        sdk_client_created = True
    except Exception as exc:
        blockers.append(
            build_blocker(
                "sdk_client_creation_failed",
                "sdk_client",
                "The SDK client could not be initialized without a private key or signer.",
            )
        )
        sdk_status = _sdk_status_from_binding(
            binding,
            l2_credentials_object_created=l2_credentials_object_created,
            sdk_client_created=False,
            sdk_requires_signer_without_private_key=False,
            open_orders_method_available=False,
            balance_allowance_method_available=False,
            status_override=STATUS_BLOCKED_CLIENT_INIT_ERROR,
            error_type=type(exc).__name__,
            error_message_sanitized=_redact_text(str(exc), secret_values),
            generated_at=generated_at,
        )
        return sdk_status, probe_attempts, blockers, STATUS_BLOCKED_CLIENT_INIT_ERROR

    open_method_available = callable(getattr(client, "get_orders", None))
    balance_method_available = callable(getattr(client, "get_balance_allowance", None))
    if _client_requires_signer_without_private_key(client):
        sdk_requires_signer_without_private_key = True
        blockers.append(
            build_blocker(
                "sdk_requires_signer_or_wallet_address_for_l2_headers",
                "sdk_auth_boundary",
                "The SDK requires a signer/address-backed client; this task is forbidden from reading private keys or instantiating signers.",
            )
        )
        sdk_status = _sdk_status_from_binding(
            binding,
            l2_credentials_object_created=l2_credentials_object_created,
            sdk_client_created=sdk_client_created,
            sdk_requires_signer_without_private_key=True,
            open_orders_method_available=open_method_available,
            balance_allowance_method_available=balance_method_available,
            status_override=STATUS_BLOCKED_SDK_REQUIRES_SIGNER,
            generated_at=generated_at,
        )
        return sdk_status, probe_attempts, blockers, STATUS_BLOCKED_SDK_REQUIRES_SIGNER

    if open_method_available:
        probe_attempts.append(
            _attempt_open_orders_probe(
                client=client,
                params_class=binding.open_order_params_class,
                secret_values=secret_values,
                generated_at=generated_at,
            )
        )
    else:
        probe_attempts.append(
            _method_unavailable_attempt(
                probe_name="open_orders_count",
                sdk_method="get_orders",
                generated_at=generated_at,
            )
        )
    if balance_method_available:
        probe_attempts.append(
            _attempt_balance_allowance_probe(
                client=client,
                params_class=binding.balance_allowance_params_class,
                asset_type_class=binding.asset_type_class,
                secret_values=secret_values,
                generated_at=generated_at,
            )
        )
    else:
        probe_attempts.append(
            _method_unavailable_attempt(
                probe_name="balance_allowance_availability",
                sdk_method="get_balance_allowance",
                generated_at=generated_at,
            )
        )

    if not open_method_available and not balance_method_available:
        blockers.append(
            build_blocker(
                "safe_readonly_sdk_methods_unavailable",
                "sdk_method",
                "The SDK client does not expose get_orders or get_balance_allowance; no account data is fabricated.",
            )
        )
        status = STATUS_BLOCKED_METHOD_UNAVAILABLE
    elif any(row.get("succeeded") is True for row in probe_attempts):
        status = STATUS_SUCCEEDED_LIVE_BLOCKED
    else:
        status = STATUS_BLOCKED_PROBE_FAILED
        blockers.append(
            build_blocker(
                "account_state_readonly_probe_failed",
                "sdk_readonly_probe",
                "All attempted SDK read-only account state probes failed; no success is inferred.",
            )
        )
    sdk_status = _sdk_status_from_binding(
        binding,
        l2_credentials_object_created=l2_credentials_object_created,
        sdk_client_created=sdk_client_created,
        sdk_requires_signer_without_private_key=sdk_requires_signer_without_private_key,
        open_orders_method_available=open_method_available,
        balance_allowance_method_available=balance_method_available,
        status_override="available_readonly_methods_checked",
        generated_at=generated_at,
    )
    return sdk_status, probe_attempts, blockers, status


def _read_presence_and_account_config(
    environ: Mapping[str, str],
    *,
    generated_at: str,
) -> tuple[dict[str, Any], dict[str, str], dict[str, str]]:
    l2_rows: list[dict[str, Any]] = []
    account_rows: list[dict[str, Any]] = []
    credential_values: dict[str, str] = {}
    account_config_values: dict[str, str] = {}
    missing: list[str] = []
    for env_name in REQUIRED_L2_CREDENTIAL_ENV_VARS:
        text = clean_text(environ.get(env_name))
        present = bool(text)
        if present:
            credential_values[env_name] = text
        else:
            missing.append(env_name)
        l2_rows.append(
            {
                "env_var_name": env_name,
                "present": present,
                "presence_status": "present_redacted" if present else "missing",
                "raw_value_emitted": False,
                "actual_secret_value_exposed": False,
                "value_hash_emitted": False,
                "value_prefix_emitted": False,
                "value_suffix_emitted": False,
                "safe_for_artifacts": True,
            }
        )
    for env_name in ACCOUNT_CONFIG_ENV_VARS:
        text = clean_text(environ.get(env_name))
        present = bool(text)
        if present:
            account_config_values[env_name] = text
        account_rows.append(
            {
                "env_var_name": env_name,
                "present": present,
                "presence_status": "present_redacted" if present else "missing",
                "redacted_display": _redacted_config_display(env_name, text),
                "raw_value_emitted": False,
                "actual_secret_value_exposed": False,
                "value_hash_emitted": False,
                "value_prefix_emitted": False,
                "value_suffix_emitted": False,
                "safe_for_artifacts": True,
            }
        )
    report = LiveAccountCredentialPresence(
        l2_env_presence_items=tuple(l2_rows),
        account_config_presence_items=tuple(account_rows),
        configured_l2_count=len(credential_values),
        missing_l2_count=len(missing),
        missing_l2_env_vars=tuple(missing),
        generated_at=generated_at,
    ).to_dict()
    return report, credential_values, account_config_values


def _build_account_status(
    account_config_values: Mapping[str, str],
    *,
    generated_at: str,
) -> dict[str, Any]:
    wallet = clean_text(account_config_values.get(POLYMARKET_WALLET_ADDRESS_ENV))
    signature_type = clean_text(account_config_values.get(POLYMARKET_SIGNATURE_TYPE_ENV))
    funder = clean_text(account_config_values.get(POLYMARKET_FUNDER_ADDRESS_ENV))
    return LiveAccountRedactedStatus(
        wallet_address_present=bool(wallet),
        wallet_address_redacted=_redact_address(wallet),
        signature_type_present=bool(signature_type),
        signature_type_redacted=_redact_signature_type(signature_type),
        funder_address_present=bool(funder),
        funder_address_redacted=_redact_address(funder),
        generated_at=generated_at,
    ).to_dict()


def _sdk_status_from_binding(
    binding: LiveAccountSdkBinding,
    *,
    l2_credentials_object_created: bool,
    sdk_client_created: bool,
    sdk_requires_signer_without_private_key: bool,
    open_orders_method_available: bool,
    balance_allowance_method_available: bool,
    status_override: str = "",
    error_type: str = "",
    error_message_sanitized: str = "",
    generated_at: str,
) -> dict[str, Any]:
    status = clean_text(status_override) or clean_text(binding.status) or "unknown"
    return LiveAccountSdkStatus(
        status=status,
        sdk_available=binding.status == "available",
        selected_sdk_module=binding.module_name,
        attempted_sdk_modules=tuple(binding.attempted_modules),
        expected_sdk_module=clean_text(binding.expected_sdk_module) or EXPECTED_SDK_MODULE,
        expected_pip_package=clean_text(binding.expected_pip_package) or EXPECTED_PIP_PACKAGE,
        expected_install_command=clean_text(binding.expected_install_command) or EXPECTED_SDK_INSTALL_COMMAND,
        python_executable=clean_text(binding.python_executable) or sys.executable,
        sdk_import_reports=tuple(binding.sdk_import_reports),
        pip_package_visibility=tuple(binding.pip_package_visibility),
        client_class_available=binding.client_class is not None,
        api_creds_class_available=binding.creds_class is not None,
        open_orders_method_available=open_orders_method_available,
        balance_allowance_method_available=balance_allowance_method_available,
        l2_credentials_object_created=l2_credentials_object_created,
        sdk_client_created=sdk_client_created,
        sdk_requires_signer_without_private_key=sdk_requires_signer_without_private_key,
        error_type=clean_text(error_type or binding.error_type),
        error_message_sanitized=clean_text(error_message_sanitized or binding.error_message_sanitized),
        generated_at=generated_at,
    ).to_dict()


def _build_api_creds_object(creds_class: Any, credential_values: Mapping[str, str]) -> Any:
    kwargs = {
        "api_" + "key": credential_values[POLYMARKET_API_KEY_ENV],
        "api_" + "secret": credential_values[POLYMARKET_API_SECRET_ENV],
        "api_" + "passphrase": credential_values[POLYMARKET_API_PASSPHRASE_ENV],
    }
    try:
        return creds_class(**kwargs)
    except TypeError:
        return creds_class(
            credential_values[POLYMARKET_API_KEY_ENV],
            credential_values[POLYMARKET_API_SECRET_ENV],
            credential_values[POLYMARKET_API_PASSPHRASE_ENV],
        )


def _build_sdk_client(client_class: Any, creds_obj: Any) -> Any:
    try:
        return client_class(host=DEFAULT_CLOB_HOST, chain_id=POLYGON_CHAIN_ID, creds=creds_obj)
    except TypeError:
        return client_class(DEFAULT_CLOB_HOST, POLYGON_CHAIN_ID, None, creds_obj)


def _client_requires_signer_without_private_key(client: Any) -> bool:
    mode = clean_text(getattr(client, "mode", ""))
    if hasattr(client, "signer") and getattr(client, "signer") is None:
        return mode not in {"2", "L2", "l2"}
    return False


def _attempt_open_orders_probe(
    *,
    client: Any,
    params_class: Any,
    secret_values: Sequence[str],
    generated_at: str,
) -> dict[str, Any]:
    method = getattr(client, "get_orders")
    params = _optional_params(params_class)
    try:
        response = _call_sdk_method(method, params)
        summary = _summarize_open_orders_response(response)
        count_available = summary["open_order_count"] is not None
        return LiveAccountReadOnlyProbeAttempt(
            probe_name="open_orders_count",
            sdk_method="get_orders",
            status="succeeded" if count_available else "succeeded_count_unavailable",
            attempted=True,
            succeeded=True,
            method_available=True,
            open_order_count=summary["open_order_count"],
            open_order_count_available=count_available,
            response_shape=summary["response_shape"],
            generated_at=generated_at,
        ).to_dict()
    except Exception as exc:
        return LiveAccountReadOnlyProbeAttempt(
            probe_name="open_orders_count",
            sdk_method="get_orders",
            status="failed",
            attempted=True,
            succeeded=False,
            method_available=True,
            error_type=type(exc).__name__,
            error_message_sanitized=_redact_text(str(exc), secret_values),
            generated_at=generated_at,
        ).to_dict()


def _attempt_balance_allowance_probe(
    *,
    client: Any,
    params_class: Any,
    asset_type_class: Any,
    secret_values: Sequence[str],
    generated_at: str,
) -> dict[str, Any]:
    method = getattr(client, "get_balance_allowance")
    params = _balance_allowance_params(params_class, asset_type_class)
    try:
        response = _call_sdk_method(method, params)
        summary = _summarize_balance_allowance_response(response)
        return LiveAccountReadOnlyProbeAttempt(
            probe_name="balance_allowance_availability",
            sdk_method="get_balance_allowance",
            status="succeeded_redacted",
            attempted=True,
            succeeded=True,
            method_available=True,
            response_shape=summary["response_shape"],
            account_value_fields_available=tuple(summary["account_value_fields_available"]),
            response_value_fields_redacted=tuple(summary["response_value_fields_redacted"]),
            generated_at=generated_at,
        ).to_dict()
    except Exception as exc:
        return LiveAccountReadOnlyProbeAttempt(
            probe_name="balance_allowance_availability",
            sdk_method="get_balance_allowance",
            status="failed",
            attempted=True,
            succeeded=False,
            method_available=True,
            error_type=type(exc).__name__,
            error_message_sanitized=_redact_text(str(exc), secret_values),
            generated_at=generated_at,
        ).to_dict()


def _method_unavailable_attempt(
    *,
    probe_name: str,
    sdk_method: str,
    generated_at: str,
) -> dict[str, Any]:
    return LiveAccountReadOnlyProbeAttempt(
        probe_name=probe_name,
        sdk_method=sdk_method,
        status="method_unavailable",
        attempted=False,
        succeeded=False,
        method_available=False,
        generated_at=generated_at,
    ).to_dict()


def _call_sdk_method(method: Any, params: Any) -> Any:
    if params is _NO_PARAMS:
        return method()
    try:
        return method(params)
    except TypeError as exc:
        message = clean_text(exc)
        if "positional" in message or "argument" in message:
            return method()
        raise


def _optional_params(params_class: Any) -> Any:
    if params_class is None:
        return _NO_PARAMS
    try:
        return params_class()
    except Exception:
        return _NO_PARAMS


def _balance_allowance_params(params_class: Any, asset_type_class: Any) -> Any:
    if params_class is None:
        return _NO_PARAMS
    asset_type = getattr(asset_type_class, "COLLATERAL", None) if asset_type_class is not None else None
    try:
        return params_class(asset_type=asset_type)
    except Exception:
        try:
            return params_class()
        except Exception:
            return _NO_PARAMS


def _summarize_open_orders_response(response: Any) -> dict[str, Any]:
    count: int | None = None
    if isinstance(response, list):
        count = len(response)
    elif isinstance(response, Mapping):
        data = response.get("data")
        if isinstance(data, list):
            count = len(data)
        elif isinstance(response.get("orders"), list):
            count = len(response.get("orders", []))
        elif isinstance(response.get("open_orders"), list):
            count = len(response.get("open_orders", []))
    return {
        "open_order_count": count,
        "response_shape": _response_shape(response),
    }


def _summarize_balance_allowance_response(response: Any) -> dict[str, Any]:
    available_fields: list[str] = []
    if isinstance(response, Mapping):
        for field in ("balance", "allowance"):
            if field in response:
                available_fields.append(field)
    else:
        for field in ("balance", "allowance"):
            if hasattr(response, field):
                available_fields.append(field)
    return {
        "response_shape": _response_shape(response),
        "account_value_fields_available": available_fields,
        "response_value_fields_redacted": available_fields,
    }


def _response_shape(response: Any) -> str:
    if isinstance(response, list):
        return "list"
    if isinstance(response, Mapping):
        return "mapping"
    if response is None:
        return "none"
    return type(response).__name__


def _first_open_order_count(attempts: Sequence[Mapping[str, Any]]) -> int | None:
    for row in attempts:
        if row.get("probe_name") == "open_orders_count":
            value = row.get("open_order_count")
            return value if isinstance(value, int) else None
    return None


def _probe_status(attempts: Sequence[Mapping[str, Any]], probe_name: str) -> str:
    for row in attempts:
        if row.get("probe_name") == probe_name:
            return clean_text(row.get("status"))
    return "not_available"


def _balance_allowance_availability_status(attempts: Sequence[Mapping[str, Any]]) -> str:
    for row in attempts:
        if row.get("probe_name") != "balance_allowance_availability":
            continue
        fields = [clean_text(item) for item in row.get("account_value_fields_available", [])]
        fields = [item for item in fields if item]
        if fields:
            return "available_redacted:" + ",".join(fields)
        return clean_text(row.get("status")) or "not_available"
    return "not_available"


def _redact_text(value: Any, secret_values: Sequence[str]) -> str:
    text = clean_text(value)
    if not text:
        return ""
    redacted = text
    for item in secret_values:
        item_text = clean_text(item)
        if item_text:
            redacted = redacted.replace(item_text, "[REDACTED]")
    return redacted[:500]


def _redacted_config_display(env_name: str, value: str) -> str:
    text = clean_text(value)
    if not text:
        return ""
    if env_name in {POLYMARKET_WALLET_ADDRESS_ENV, POLYMARKET_FUNDER_ADDRESS_ENV}:
        return _redact_address(text)
    if env_name == POLYMARKET_SIGNATURE_TYPE_ENV:
        return _redact_signature_type(text)
    return "present_redacted"


def _redact_address(value: str) -> str:
    text = clean_text(value)
    if not text:
        return ""
    if _ADDRESS_RE.match(text):
        return f"{text[:6]}...{text[-4:]}"
    return "present_redacted"


def _redact_signature_type(value: str) -> str:
    text = clean_text(value)
    if not text:
        return ""
    if text.isdigit() and len(text) <= 2:
        return text
    return "present_redacted"


def _operator_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return (
        "Live account read-only state probe completed with status="
        + clean_text(value.get("status"))
        + "; account_state_probe_performed="
        + str(value.get("account_state_probe_performed") is True).lower()
        + "; probe_is_readonly=true; allowed_for_live=false; no order submission, cancellation, signing, signer, wallet connection, private-key read, or write endpoint was used."
    )


def _active_environ(environ: Mapping[str, str] | None) -> Mapping[str, str]:
    if environ is not None:
        return environ
    import os

    return os.environ


class _NoParams:
    pass


_NO_PARAMS = _NoParams()
