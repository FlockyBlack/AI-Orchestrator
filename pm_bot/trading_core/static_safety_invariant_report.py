from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from pm_bot.trading_core.schemas import GENERATED_AT, bullet_lines, clean_text, normalize_path, write_json, write_text
from pm_bot.trading_core.static_safety_invariant_report_models import (
    EXECUTION_ARTIFACT_FIELDS,
    EXECUTION_MODE,
    FORCED_FALSE_EXECUTION_FIELDS,
    SAFE_FALSE_FLAGS,
    SCAN_MODE,
    SENSITIVE_NAME_TERMS,
    SEVERITY_ALLOWED_REFERENCE,
    SEVERITY_CRITICAL,
    SEVERITY_WARNING,
    STATIC_SAFETY_INVARIANT_ALLOWLIST_CONTRACT,
    STATIC_SAFETY_INVARIANT_FINDING_CONTRACT,
    STATIC_SAFETY_INVARIANT_LATEST_STATUS_CONTRACT,
    STATIC_SAFETY_INVARIANT_REPORT_CONTRACT,
    TASK_ID,
    UNSAFE_TRUE_FIELDS,
    StaticSafetyInvariantFinding,
    StaticSafetyInvariantReportConfig,
    severity_counts,
    static_safety_invariant_safety_flags,
)

DEFAULT_ARTIFACT_DIR = Path("pm_bot/trading_core/artifacts/static_safety_invariant_report_060q")
DEFAULT_SCOPE = "pm_bot"
TRADING_CORE_ARTIFACT_SCOPE = Path("pm_bot/trading_core/artifacts")

SCANNED_SUFFIXES = {".py", ".json", ".md", ".txt", ".toml", ".yaml", ".yml"}
EXCLUDED_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
}
SENSITIVE_FILE_NAMES = {
    ".env",
    "wallet.dat",
    "wallet.json",
    "keystore",
    "keystore.json",
    "private_key",
    "private_key.txt",
    "seed_phrase",
    "seed_phrase.txt",
    "mnemonic",
    "mnemonic.txt",
}
SENSITIVE_FILE_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
FORBIDDEN_RUNTIME_FLAGS = (
    "--live",
    "--live-execution",
    "--execute",
    "--trade",
    "--wallet",
    "--signing",
    "--sign",
    "--order",
    "--submit",
    "--cancel",
    "--approve-live",
)

TRUE_ASSIGNMENT_VALUES = ("true", "1", "yes", "enabled", "active", "approved", "performed", "submitted")
SAFE_REFERENCE_TOKENS = (
    " false",
    "=false",
    ":false",
    " false,",
    " false)",
    "blocked",
    "redacted",
    "forbidden",
    "disallowed",
    "not ",
    " no ",
    "never",
    "mock",
    "presence",
    "missing",
    "skipped",
    "boundary",
    "denylist",
    "allowlist",
    "disabled",
    "requires",
    "must",
    "may be",
    "only when",
)
ALLOWED_DOC_TEST_PARTS = {"docs", "tests"}

ORDER_SUBMISSION_CALL_PATTERN = re.compile(
    r"\b(?:create_order|post_order|submit_order|place_order|send_order|execute_order)\s*\(",
    re.IGNORECASE,
)
ORDER_CANCELLATION_CALL_PATTERN = re.compile(
    r"\b(?:cancel_order|delete_order|submit_cancel|cancel_all_orders)\s*\(",
    re.IGNORECASE,
)
SIGNING_CALL_PATTERN = re.compile(
    r"\b(?:sign_order|sign_payload|generate_signed_payload|create_signed_order|derive_api_key)\s*\(",
    re.IGNORECASE,
)
WALLET_CALL_PATTERN = re.compile(
    r"\b(?:connect_wallet|wallet_connect|load_wallet|wallet\.connect|wallet\.sign)\s*\(",
    re.IGNORECASE,
)
ACCOUNT_RUNTIME_CALL_PATTERN = re.compile(
    r"\b(?:get_balance|get_balances|get_position|get_positions|get_fill|get_fills|get_pnl|get_pnl_report)\s*\(",
    re.IGNORECASE,
)
AUTONOMY_RUNTIME_PATTERN = re.compile(
    r"time\.sleep\s*\(|threading\.|asyncio\.|sched\.|daemon\s*=\s*True",
    re.IGNORECASE,
)
SENSITIVE_NAME_ASSIGNMENT_PATTERN = re.compile(
    r"\b(?:private[_-]?key|privatekey|api[_-]?secret|secret[_-]?key|passphrase|mnemonic|seed[_-]?phrase)\b\s*(?:=|:)",
    re.IGNORECASE,
)


def static_safety_invariant_report_artifact_paths(artifact_dir: str | Path | None = None) -> dict[str, Path]:
    root = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
    return {
        "root": root,
        "result": root / "static_safety_invariant_report_060q_result.json",
        "operator_md": root / "static_safety_invariant_report_060q_operator.md",
        "latest_status": root / "latest_static_safety_invariant_report_status_060q.json",
        "findings": root / "static_safety_invariant_findings_060q.json",
        "allowlist": root / "static_safety_invariant_allowlist_060q.json",
    }


def run_static_safety_invariant_report(
    *,
    scope: str | Path = DEFAULT_SCOPE,
    dry_run: bool = True,
    include_artifacts: bool = False,
    strict: bool = False,
    artifact_dir: str | Path | None = None,
    repository_root: str | Path | None = None,
    generated_at: str = GENERATED_AT,
) -> dict[str, Any]:
    if dry_run is not True:
        raise ValueError("static safety invariant report requires --dry-run; live execution is blocked")

    repo_root = Path(repository_root) if repository_root is not None else Path.cwd()
    repo_root = repo_root.resolve()
    paths = static_safety_invariant_report_artifact_paths(artifact_dir)
    scope_root = _resolve_inside_repo(repo_root, scope)
    artifact_scope = _resolve_inside_repo(repo_root, TRADING_CORE_ARTIFACT_SCOPE)
    output_root = (repo_root / paths["root"]).resolve() if not paths["root"].is_absolute() else paths["root"].resolve()

    config = StaticSafetyInvariantReportConfig(
        scope=normalize_path(_relative_path(scope_root, repo_root)),
        dry_run=True,
        include_artifacts=include_artifacts is True,
        strict=strict is True,
        artifact_dir=normalize_path(paths["root"]),
        repository_root=normalize_path(repo_root),
        generated_at=generated_at,
    ).to_dict()
    collect_result = _collect_scan_paths(
        repo_root=repo_root,
        scope_root=scope_root,
        artifact_scope=artifact_scope,
        output_root=output_root,
        include_artifacts=include_artifacts,
        strict=strict,
    )
    findings: list[dict[str, Any]] = []
    counters = {"safe_false_reference_count": 0}
    finding_index = {"value": 0}

    def next_index() -> int:
        finding_index["value"] += 1
        return finding_index["value"]

    for scan_path in collect_result["paths"]:
        findings.extend(
            _scan_path(
                repo_root=repo_root,
                path=scan_path,
                strict=strict,
                counters=counters,
                next_index=next_index,
            )
        )

    counts = severity_counts(findings)
    status = _report_status(counts)
    path_refs = {key: normalize_path(path) for key, path in paths.items() if key != "root"}
    latest_status = {
        "contract_version": STATIC_SAFETY_INVARIANT_LATEST_STATUS_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "safety_ok": counts[SEVERITY_CRITICAL] == 0,
        "scope": config["scope"],
        "strict": strict is True,
        "artifacts_included": include_artifacts is True,
        "scanned_file_count": len(collect_result["paths"]),
        "skipped_file_count": len(collect_result["skipped"]),
        "critical_count": counts[SEVERITY_CRITICAL],
        "warning_count": counts[SEVERITY_WARNING],
        "allowed_reference_count": counts[SEVERITY_ALLOWED_REFERENCE],
        "safe_false_reference_count": counters["safe_false_reference_count"],
        "live_execution": "blocked",
        "order_submission": "blocked",
        "signing": "blocked",
        "wallet": "blocked",
        "artifact_path": path_refs["result"],
        "latest_status_path": path_refs["latest_status"],
        "operator_markdown_path": path_refs["operator_md"],
        "findings_path": path_refs["findings"],
        "allowlist_path": path_refs["allowlist"],
        "generated_at": generated_at,
        **static_safety_invariant_safety_flags(),
    }
    report = {
        "contract_version": STATIC_SAFETY_INVARIANT_REPORT_CONTRACT,
        "task_id": TASK_ID,
        "status": status,
        "safety_ok": counts[SEVERITY_CRITICAL] == 0,
        "config": config,
        "scan_scope": config["scope"],
        "strict": strict is True,
        "artifacts_included": include_artifacts is True,
        "scanned_file_count": len(collect_result["paths"]),
        "scanned_runtime_file_count": collect_result["runtime_count"],
        "scanned_artifact_file_count": collect_result["artifact_count"],
        "skipped_file_count": len(collect_result["skipped"]),
        "skipped_paths": collect_result["skipped"],
        "severity_counts": counts,
        "critical_count": counts[SEVERITY_CRITICAL],
        "warning_count": counts[SEVERITY_WARNING],
        "allowed_reference_count": counts[SEVERITY_ALLOWED_REFERENCE],
        "safe_false_reference_count": counters["safe_false_reference_count"],
        "findings": findings,
        "latest_status": latest_status,
        "artifact_paths": path_refs,
        "allowlist": build_static_safety_invariant_allowlist(generated_at=generated_at),
        "safety_invariant_confirmation": static_safety_invariant_safety_flags(),
        "generated_at": generated_at,
        **static_safety_invariant_safety_flags(),
    }

    write_json(paths["allowlist"], report["allowlist"])
    write_json(
        paths["findings"],
        {
            "contract_version": STATIC_SAFETY_INVARIANT_FINDING_CONTRACT + ".list",
            "task_id": TASK_ID,
            "finding_count": len(findings),
            "severity_counts": counts,
            "findings": findings,
            "generated_at": generated_at,
        },
    )
    write_json(paths["latest_status"], latest_status)
    write_json(paths["result"], report)
    write_text(paths["operator_md"], render_static_safety_invariant_report_markdown(report))
    return report


def build_static_safety_invariant_allowlist(*, generated_at: str = GENERATED_AT) -> dict[str, Any]:
    return {
        "contract_version": STATIC_SAFETY_INVARIANT_ALLOWLIST_CONTRACT,
        "task_id": TASK_ID,
        "safe_false_flags": list(SAFE_FALSE_FLAGS),
        "forced_false_execution_fields": list(FORCED_FALSE_EXECUTION_FIELDS),
        "allowed_reference_rules": [
            "docs/tests references are allowed only as examples or assertions and are reported as allowed_reference",
            "explicit false safety flags are counted as safe references and never escalated",
            "blocked/redacted/forbidden/boundary wording is treated as safety context, not activation",
            "paper/simulated fields are not treated as live execution artifacts",
        ],
        "excluded_default_dirs": sorted(EXCLUDED_DIR_NAMES),
        "sensitive_file_name_exclusions": sorted(SENSITIVE_FILE_NAMES),
        "sensitive_file_suffix_exclusions": sorted(SENSITIVE_FILE_SUFFIXES),
        "generated_at": generated_at,
        **static_safety_invariant_safety_flags(),
    }


def render_static_safety_invariant_cli_summary(status: Mapping[str, Any]) -> str:
    value = dict(status or {})
    return "\n".join(
        [
            "Static safety invariant report completed.",
            f"Scope: {clean_text(value.get('scope'))}",
            f"Strict: {str(value.get('strict') is True).lower()}",
            f"Artifacts included: {str(value.get('artifacts_included') is True).lower()}",
            f"Scanned files: {int(value.get('scanned_file_count', 0) or 0)}",
            f"Critical findings: {int(value.get('critical_count', 0) or 0)}",
            f"Warnings: {int(value.get('warning_count', 0) or 0)}",
            f"Allowed references: {int(value.get('allowed_reference_count', 0) or 0)}",
            "Live execution: blocked",
            "Order submission: blocked",
            "Signing: blocked",
            "Wallet: blocked",
            f"Artifact: {clean_text(value.get('artifact_path'))}",
        ]
    )


def render_static_safety_invariant_report_markdown(report: Mapping[str, Any]) -> str:
    value = dict(report or {})
    counts = dict(value.get("severity_counts", {}))
    findings = [dict(row) for row in value.get("findings", []) if isinstance(row, Mapping)]
    rendered_findings = findings[:25]
    lines = [
        "# PMBOT Static Safety Invariant Report 060Q",
        "",
        f"- Status: `{value.get('status')}`",
        f"- Scope: `{value.get('scan_scope')}`",
        f"- Mode: `{SCAN_MODE}`",
        f"- Strict: `{str(value.get('strict') is True).lower()}`",
        f"- Artifacts included: `{str(value.get('artifacts_included') is True).lower()}`",
        f"- Scanned files: `{value.get('scanned_file_count')}`",
        f"- Critical findings: `{counts.get(SEVERITY_CRITICAL, 0)}`",
        f"- Warnings: `{counts.get(SEVERITY_WARNING, 0)}`",
        f"- Allowed references: `{counts.get(SEVERITY_ALLOWED_REFERENCE, 0)}`",
        "",
        "## Safety Invariants",
        "",
        "- live execution blocked",
        "- order submission blocked",
        "- order cancellation blocked",
        "- signing blocked",
        "- signed payload generation blocked",
        "- wallet usage blocked",
        "- authenticated trading blocked",
        "- resolved_blocker_count remains `0`",
        "",
        "## Scanner Boundary",
        "",
        "- repository worktree files only",
        "- environment variables not read",
        "- user home directories not read",
        "- wallet files not read",
        "- browser wallets not inspected",
        "- network access not performed",
        "- credential values not printed, hashed, stored, or transformed",
        "",
        "## Findings",
        "",
        *bullet_lines(
            f"`{row.get('severity')}` `{row.get('category')}` `{row.get('path')}`"
            + (f":{row.get('line')}" if int(row.get("line", 0) or 0) else "")
            + f" - {row.get('detail')}"
            for row in rendered_findings
        ),
    ]
    if len(findings) > len(rendered_findings):
        lines.extend(["", f"- {len(findings) - len(rendered_findings)} additional findings are in the JSON artifact."])
    lines.extend(
        [
            "",
            "## Operator Action",
            "",
            "- review critical findings before any merge if `critical_count` is nonzero",
            "- warning entries do not enable live/order/signing/wallet behavior",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def fail_closed_for_forbidden_flags(argv: Sequence[str]) -> None:
    lowered = {clean_text(item).lower().split("=", 1)[0] for item in argv}
    requested = sorted(flag for flag in FORBIDDEN_RUNTIME_FLAGS if flag in lowered)
    if requested:
        raise SystemExit(
            "static safety invariant report is review-only; unsupported live/wallet/signing/order flag(s): "
            + ", ".join(requested)
        )


def _collect_scan_paths(
    *,
    repo_root: Path,
    scope_root: Path,
    artifact_scope: Path,
    output_root: Path,
    include_artifacts: bool,
    strict: bool,
) -> dict[str, Any]:
    runtime_paths: list[Path] = []
    artifact_paths: list[Path] = []
    skipped: list[dict[str, str]] = []
    for path in _walk_files(scope_root):
        if not _is_inside(path, repo_root):
            continue
        if _is_inside(path, output_root):
            skipped.append(_skipped(path, repo_root, "output_artifact_directory"))
            continue
        if _is_sensitive_file_name(path):
            skipped.append(_skipped(path, repo_root, "sensitive_file_name_not_read"))
            continue
        if _is_docs_or_tests(path, repo_root) and strict is not True:
            skipped.append(_skipped(path, repo_root, "docs_tests_excluded_by_default"))
            continue
        if _is_inside(path, artifact_scope):
            if include_artifacts:
                artifact_paths.append(path)
            else:
                skipped.append(_skipped(path, repo_root, "trading_core_artifacts_require_artifacts_flag"))
            continue
        if _is_artifact_dir_path(path):
            skipped.append(_skipped(path, repo_root, "non_trading_core_artifacts_excluded"))
            continue
        runtime_paths.append(path)
    if include_artifacts and artifact_scope.exists():
        for path in _walk_files(artifact_scope):
            if _is_inside(path, output_root):
                skipped.append(_skipped(path, repo_root, "output_artifact_directory"))
                continue
            if _is_sensitive_file_name(path):
                skipped.append(_skipped(path, repo_root, "sensitive_file_name_not_read"))
                continue
            if _is_docs_or_tests(path, repo_root) and strict is not True:
                skipped.append(_skipped(path, repo_root, "docs_tests_excluded_by_default"))
                continue
            artifact_paths.append(path)
    all_paths = sorted({path.resolve(): path for path in runtime_paths + artifact_paths}.values(), key=normalize_path)
    return {
        "paths": all_paths,
        "runtime_count": len({path.resolve() for path in runtime_paths if path in all_paths}),
        "artifact_count": len({path.resolve() for path in artifact_paths if path in all_paths}),
        "skipped": skipped,
    }


def _walk_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix.lower() in SCANNED_SUFFIXES else []
    if not root.exists() or not root.is_dir():
        return []
    result: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in SCANNED_SUFFIXES:
            continue
        try:
            relative_parts = path.relative_to(root).parts
        except ValueError:
            relative_parts = path.parts
        if any(part in EXCLUDED_DIR_NAMES for part in relative_parts):
            continue
        result.append(path)
    return result


def _scan_path(
    *,
    repo_root: Path,
    path: Path,
    strict: bool,
    counters: dict[str, int],
    next_index,
) -> list[dict[str, Any]]:
    relative = normalize_path(_relative_path(path, repo_root))
    allowed_reference = _is_docs_or_tests(path, repo_root)
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [
            _finding(
                next_index(),
                severity=SEVERITY_WARNING,
                category="scan_io",
                pattern_id="read_failed",
                path=relative,
                line=0,
                json_path="",
                detail=f"file could not be read: {type(exc).__name__}",
                allowed_reference=allowed_reference,
            )
        ]

    findings: list[dict[str, Any]] = []
    if path.suffix.lower() == ".json":
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            findings.append(
                _finding(
                    next_index(),
                    severity=SEVERITY_WARNING,
                    category="artifact_parse",
                    pattern_id="invalid_json",
                    path=relative,
                    line=0,
                    json_path="$",
                    detail="JSON file could not be parsed",
                    allowed_reference=allowed_reference,
                )
            )
        else:
            findings.extend(
                _scan_json_value(
                    value=value,
                    file_path=path,
                    repo_root=repo_root,
                    relative=relative,
                    json_path="$",
                    allowed_reference=allowed_reference,
                    counters=counters,
                    next_index=next_index,
                )
            )
        return findings

    for line_no, line in enumerate(text.splitlines(), start=1):
        findings.extend(
            _scan_text_line(
                line=line,
                line_no=line_no,
                relative=relative,
                allowed_reference=allowed_reference,
                counters=counters,
                next_index=next_index,
            )
        )
    return findings


def _scan_text_line(
    *,
    line: str,
    line_no: int,
    relative: str,
    allowed_reference: bool,
    counters: dict[str, int],
    next_index,
) -> list[dict[str, Any]]:
    stripped = line.strip()
    if not stripped:
        return []
    findings: list[dict[str, Any]] = []
    lowered = stripped.lower().replace(" ", "")
    if _line_is_safe_false_flag(stripped):
        counters["safe_false_reference_count"] += 1
        return []
    if _is_safe_reference_line(stripped) and not allowed_reference:
        return []

    for field in UNSAFE_TRUE_FIELDS:
        match = re.search(rf"\b{re.escape(field)}\b\s*(?:=|:)\s*([A-Za-z0-9_\"']+)", stripped, re.IGNORECASE)
        if match and _truthy_assignment_token(match.group(1)):
            findings.append(
                _finding(
                    next_index(),
                    severity=SEVERITY_CRITICAL,
                    category=_field_category(field),
                    pattern_id="unsafe_true_assignment",
                    path=relative,
                    line=line_no,
                    json_path="",
                    detail=f"{field} is assigned an unsafe activation value",
                    allowed_reference=allowed_reference,
                )
            )
    call_patterns = (
        ("order_submission_activation", "order_submission_call", ORDER_SUBMISSION_CALL_PATTERN),
        ("order_cancellation_activation", "order_cancellation_call", ORDER_CANCELLATION_CALL_PATTERN),
        ("signer_activation", "signing_call", SIGNING_CALL_PATTERN),
        ("wallet_activation", "wallet_call", WALLET_CALL_PATTERN),
        ("account_runtime_path", "account_runtime_call", ACCOUNT_RUNTIME_CALL_PATTERN),
        ("autonomy_runtime_path", "scheduler_daemon_background_loop", AUTONOMY_RUNTIME_PATTERN),
    )
    for category, pattern_id, pattern in call_patterns:
        if pattern.search(stripped):
            findings.append(
                _finding(
                    next_index(),
                    severity=SEVERITY_CRITICAL,
                    category=category,
                    pattern_id=pattern_id,
                    path=relative,
                    line=line_no,
                    json_path="",
                    detail=f"{category.replace('_', ' ')} detected",
                    allowed_reference=allowed_reference,
                )
            )
    if SENSITIVE_NAME_ASSIGNMENT_PATTERN.search(stripped) and not _sensitive_assignment_is_marker(stripped):
        findings.append(
            _finding(
                next_index(),
                severity=SEVERITY_WARNING,
                category="credential_name_reference",
                pattern_id="sensitive_variable_name_assignment",
                path=relative,
                line=line_no,
                json_path="",
                detail="private key, API secret, passphrase, mnemonic, or seed variable name detected",
                allowed_reference=allowed_reference,
            )
        )
    match = re.search(r"\bresolved_blocker_count\b\s*(?:=|:)\s*([A-Za-z0-9_\"']+)", stripped, re.IGNORECASE)
    if match and clean_text(match.group(1)).strip("\"'") != "0":
        findings.append(
            _finding(
                next_index(),
                severity=SEVERITY_CRITICAL,
                category="live_blocker_boundary",
                pattern_id="resolved_blocker_count_nonzero_or_unknown",
                path=relative,
                line=line_no,
                json_path="",
                detail="resolved_blocker_count must remain 0",
                allowed_reference=allowed_reference,
            )
        )
    return findings


def _scan_json_value(
    *,
    value: Any,
    file_path: Path,
    repo_root: Path,
    relative: str,
    json_path: str,
    allowed_reference: bool,
    counters: dict[str, int],
    next_index,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = clean_text(key)
            key_norm = _normalize_key(key_text)
            nested_path = f"{json_path}.{key_text}"
            if _is_safe_false_json_field(key_norm, nested):
                counters["safe_false_reference_count"] += 1
            elif key_norm == "resolved_blocker_count":
                findings.append(
                    _finding(
                        next_index(),
                        severity=SEVERITY_CRITICAL,
                        category="live_blocker_boundary",
                        pattern_id="resolved_blocker_count_nonzero",
                        path=relative,
                        line=0,
                        json_path=nested_path,
                        detail="resolved_blocker_count must remain 0",
                        allowed_reference=allowed_reference,
                    )
                )
            elif key_norm in UNSAFE_TRUE_FIELDS and _is_truthy_unsafe(nested):
                findings.append(
                    _finding(
                        next_index(),
                        severity=SEVERITY_CRITICAL,
                        category=_field_category(key_norm),
                        pattern_id="unsafe_json_flag_true",
                        path=relative,
                        line=0,
                        json_path=nested_path,
                        detail=f"{key_norm} is true or active",
                        allowed_reference=allowed_reference,
                    )
                )
            elif _is_sensitive_json_name(key_norm, nested):
                findings.append(
                    _finding(
                        next_index(),
                        severity=SEVERITY_WARNING,
                        category="credential_name_reference",
                        pattern_id="sensitive_json_field_name",
                        path=relative,
                        line=0,
                        json_path=nested_path,
                        detail="private key, API secret, passphrase, mnemonic, or seed field name detected",
                        allowed_reference=allowed_reference,
                    )
                )
            elif _is_execution_artifact_field(key_norm, nested):
                findings.append(
                    _finding(
                        next_index(),
                        severity=SEVERITY_CRITICAL,
                        category="runtime_account_or_execution_artifact",
                        pattern_id="tx_order_fill_balance_pnl_field",
                        path=relative,
                        line=0,
                        json_path=nested_path,
                        detail="transaction, order, fill, balance, position, or PnL runtime field detected",
                        allowed_reference=allowed_reference,
                    )
                )
            findings.extend(
                _scan_json_value(
                    value=nested,
                    file_path=file_path,
                    repo_root=repo_root,
                    relative=relative,
                    json_path=nested_path,
                    allowed_reference=allowed_reference,
                    counters=counters,
                    next_index=next_index,
                )
            )
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            findings.extend(
                _scan_json_value(
                    value=nested,
                    file_path=file_path,
                    repo_root=repo_root,
                    relative=relative,
                    json_path=f"{json_path}[{index}]",
                    allowed_reference=allowed_reference,
                    counters=counters,
                    next_index=next_index,
                )
            )
    return findings


def _finding(
    index: int,
    *,
    severity: str,
    category: str,
    pattern_id: str,
    path: str,
    line: int,
    json_path: str,
    detail: str,
    allowed_reference: bool,
) -> dict[str, Any]:
    effective_severity = SEVERITY_ALLOWED_REFERENCE if allowed_reference else severity
    allowlist_reason = "docs_tests_reference" if allowed_reference else ""
    return StaticSafetyInvariantFinding(
        finding_id=f"static-safety-060q-{index:05d}",
        severity=effective_severity,
        category=category,
        pattern_id=pattern_id,
        path=path,
        line=line,
        json_path=json_path,
        detail=detail if not allowed_reference else f"allowed docs/tests reference: {detail}",
        evidence="pattern name only; source line/value redacted",
        allowlist_reason=allowlist_reason,
    ).to_dict()


def _report_status(counts: Mapping[str, int]) -> str:
    if int(counts.get(SEVERITY_CRITICAL, 0) or 0) > 0:
        return "blocked_critical_findings"
    if int(counts.get(SEVERITY_WARNING, 0) or 0) > 0:
        return "passed_with_warnings"
    return "passed"


def _field_category(field: str) -> str:
    if "wallet" in field or "private_key" in field:
        return "wallet_activation"
    if "sign" in field or "payload" in field or "hmac" in field:
        return "signer_activation"
    if "cancel" in field:
        return "order_cancellation_activation"
    if "order" in field:
        return "order_submission_activation"
    if "balance" in field or "position" in field or "fill" in field:
        return "account_runtime_path"
    if "scheduler" in field or "daemon" in field or "background" in field or "autonomous" in field:
        return "autonomy_runtime_path"
    return "live_activation"


def _line_is_safe_false_flag(line: str) -> bool:
    for flag in SAFE_FALSE_FLAGS:
        if re.search(rf"\b{re.escape(flag)}\b.*(?:=|:)\s*(?:False|false|0)\b", line):
            return True
    return False


def _truthy_assignment_token(value: str) -> bool:
    normalized = clean_text(value).strip("\"'").lower()
    return normalized in TRUE_ASSIGNMENT_VALUES


def _is_safe_reference_line(line: str) -> bool:
    normalized = " " + line.lower().strip()
    return any(token in normalized for token in SAFE_REFERENCE_TOKENS)


def _sensitive_assignment_is_marker(line: str) -> bool:
    lowered = line.lower()
    return any(token in lowered for token in ("_present", "_configured", "redacted", "presence", "missing", "false"))


def _normalize_key(key: str) -> str:
    return clean_text(key).strip("\"'").lower().replace("-", "_")


def _is_safe_false_json_field(key_norm: str, value: Any) -> bool:
    if key_norm in SAFE_FALSE_FLAGS:
        if key_norm == "resolved_blocker_count":
            return value == 0
        return value is False or clean_text(value).lower() in {"false", "0"}
    if key_norm in FORCED_FALSE_EXECUTION_FIELDS and (value is False or clean_text(value).lower() in {"false", "0"}):
        return True
    return False


def _is_truthy_unsafe(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value > 0
    if isinstance(value, str):
        return clean_text(value).lower() in TRUE_ASSIGNMENT_VALUES
    return False


def _is_sensitive_json_name(key_norm: str, value: Any) -> bool:
    if _is_safe_false_json_field(key_norm, value):
        return False
    if any(token in key_norm for token in ("present", "configured", "redacted", "missing", "boundary")):
        return False
    return any(term in key_norm for term in SENSITIVE_NAME_TERMS)


def _is_execution_artifact_field(key_norm: str, value: Any) -> bool:
    if not _value_present(value):
        return False
    if key_norm.startswith(("paper_", "simulated_", "mock_", "redacted_", "no_")):
        return False
    if key_norm.endswith(("_present", "_blocked", "_missing", "_redacted", "_allowed", "_path", "_paths")):
        return False
    if key_norm in FORCED_FALSE_EXECUTION_FIELDS:
        return False
    if key_norm in {"fill", "fills", "balance", "balances", "position", "positions", "pnl"}:
        if _value_is_paper_or_simulated(value):
            return False
    return key_norm in EXECUTION_ARTIFACT_FIELDS


def _value_present(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return clean_text(value).lower() not in {"", "false", "blocked", "missing", "redacted", "none", "null"}
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value != 0
    if isinstance(value, (list, tuple, dict)):
        return len(value) > 0
    return value is True


def _value_is_paper_or_simulated(value: Any) -> bool:
    if isinstance(value, Mapping):
        if value.get("paper_only") is True or value.get("simulated_fill") is True:
            return True
        return any(_normalize_key(key).startswith(("paper_", "simulated_")) for key in value)
    if isinstance(value, list) and value:
        return all(_value_is_paper_or_simulated(item) for item in value if isinstance(item, Mapping))
    return False


def _resolve_inside_repo(repo_root: Path, target: str | Path) -> Path:
    target_path = Path(target)
    resolved = target_path.resolve() if target_path.is_absolute() else (repo_root / target_path).resolve()
    if not _is_inside(resolved, repo_root):
        raise ValueError(f"scan path must stay inside repository worktree: {target}")
    return resolved


def _is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _relative_path(path: Path, repo_root: Path) -> str:
    try:
        return normalize_path(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return normalize_path(path)


def _is_docs_or_tests(path: Path, repo_root: Path) -> bool:
    relative_parts = Path(_relative_path(path, repo_root)).parts
    return any(part.lower() in ALLOWED_DOC_TEST_PARTS for part in relative_parts)


def _is_artifact_dir_path(path: Path) -> bool:
    return any(part.lower() == "artifacts" for part in path.parts)


def _is_sensitive_file_name(path: Path) -> bool:
    name = path.name.lower()
    if name in SENSITIVE_FILE_NAMES:
        return True
    if any(name.startswith(".env.") or name == ".env" for _ in (0,)):
        return True
    return path.suffix.lower() in SENSITIVE_FILE_SUFFIXES


def _skipped(path: Path, repo_root: Path, reason: str) -> dict[str, str]:
    return {"path": normalize_path(_relative_path(path, repo_root)), "reason": reason}
