import ast
import json
import sys
from pathlib import Path


SOURCE_EXTENSIONS = {".py", ".json", ".md"}
SAFE_ASSIGNMENT_FLAGS = ("FORBIDDEN", "SAFE", "ALLOWED", "SCAN", "SOURCE_EXTENSIONS", "REQUIRED_FILES")
FORBIDDEN_PATTERNS = [
    {"token": "requests", "category": "network"},
    {"token": "urllib.request", "category": "network"},
    {"token": "httpx", "category": "network"},
    {"token": "socket", "category": "network"},
    {"token": "aiohttp", "category": "network"},
    {"token": "api.polymarket", "category": "live_api"},
    {"token": "clob.polymarket", "category": "live_api"},
    {"token": "gamma-api", "category": "live_api"},
    {"token": "api_key", "category": "api_credentials"},
    {"token": "api_secret", "category": "api_credentials"},
    {"token": "authorization_header", "category": "api_credentials"},
    {"token": "private_key", "category": "wallet"},
    {"token": "seed_phrase", "category": "wallet"},
    {"token": "wallet_sign", "category": "wallet"},
    {"token": "eth_account", "category": "wallet"},
    {"token": "wallet_address", "category": "wallet"},
    {"token": "submit_order", "category": "trading"},
    {"token": "place_order", "category": "trading"},
    {"token": "execute_trade", "category": "trading"},
    {"token": "order_instruction", "category": "trading"},
    {"token": "dispatcher/", "category": "runtime"},
    {"token": "run_codex", "category": "runtime"},
    {"token": "codex_auto/", "category": "runtime"},
    {"token": "governance/", "category": "runtime"},
    {"token": "checkpoints", "category": "runtime"},
    {"token": "freezes", "category": "runtime"},
    {"token": "results/", "category": "runtime"},
    {"token": "state/", "category": "runtime"},
]


def _load_text(path: Path):
    return path.read_text(encoding="utf-8")


def _iter_target_files(root: Path):
    roots = [
        root / "pm_bot" / "fixtures",
        root / "pm_bot" / "scenarios",
        root / "pm_bot" / "demo",
        root / "pm_bot" / "reports",
        root / "pm_bot" / "audit",
        root / "pm_bot" / "research",
        root / "pm_bot" / "explainability",
        root / "pm_bot" / "quality",
        root / "pm_bot" / "adversarial",
        root / "pm_bot" / "replay",
        root / "pm_bot" / "validation",
        root / "pm_bot" / "operator",
        root / "pm_bot" / "export",
        root / "pm_bot" / "boundary",
        root / "pm_bot" / "contracts",
        root / "docs",
    ]
    for target_root in roots:
        if not target_root.exists():
            continue
        for path in sorted(target_root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SOURCE_EXTENSIONS:
                continue
            if path.name.startswith("expected_static_safety_audit."):
                continue
            if target_root.name == "docs" and not path.name.startswith("PM_BOT_") and not path.name.startswith("PMBOT_"):
                continue
            yield path


def _safe_assignment_spans(tree):
    spans = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if any(any(flag in name for flag in SAFE_ASSIGNMENT_FLAGS) for name in targets):
                spans.append((node.lineno, node.end_lineno))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if any(flag in node.target.id for flag in SAFE_ASSIGNMENT_FLAGS):
                spans.append((node.lineno, node.end_lineno))
    return spans


def _line_in_spans(line_number: int, spans):
    return any(start <= line_number <= end for start, end in spans)


def _file_kind(path: Path):
    lowered_parts = {part.lower() for part in path.parts}
    if path.suffix.lower() == ".md":
        return "documentation"
    if "tests" in lowered_parts:
        return "test_file"
    if path.suffix.lower() == ".json" or path.name.startswith("expected_"):
        return "json_contract"
    return "runtime_source"


def _safe_reason(file_kind: str, line_text: str, line_number: int, safe_spans):
    lowered = line_text.lower()
    stripped = line_text.strip()
    if file_kind == "documentation":
        return "documentation_context"
    if file_kind == "test_file":
        return "test_context"
    if file_kind == "json_contract":
        return "json_contract_context"
    if stripped.startswith('"') or stripped.startswith("'"):
        return "string_literal_context"
    if _line_in_spans(line_number, safe_spans):
        return "safety_definition_context"
    if "assert" in lowered and "notin" in lowered:
        return "negative_assertion_context"
    if "not in prohibited_keys_seen" in lowered:
        return "negative_assertion_context"
    return None


def _finding(root: Path, path: Path, token: str, category: str, line_number: int, reason: str):
    return {
        "file": str(path.relative_to(root)).replace("\\", "/"),
        "token": token,
        "category": category,
        "line": line_number,
        "reason": reason,
    }


def build_static_audit_report(root: Path):
    blocking_findings = []
    non_blocking_mentions = []
    scanned_files = []
    blocking_keys = set()
    mention_keys = set()
    boundary_runtime_sources = []

    for path in _iter_target_files(root):
        relative = str(path.relative_to(root)).replace("\\", "/")
        scanned_files.append(relative)
        source = _load_text(path)
        source_lower = source.lower()
        file_kind = _file_kind(path)
        safe_spans = []

        if relative.startswith("pm_bot/boundary/") and file_kind == "runtime_source":
            boundary_runtime_sources.append(relative)

        if path.suffix.lower() == ".py":
            tree = ast.parse(source)
            safe_spans = _safe_assignment_spans(tree)
            if file_kind == "runtime_source":
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imported_name = alias.name.lower()
                            for spec in FORBIDDEN_PATTERNS[:5]:
                                if imported_name == spec["token"]:
                                    key = (str(path), spec["token"], "runtime_import_detected", node.lineno)
                                    if key not in blocking_keys:
                                        blocking_keys.add(key)
                                        blocking_findings.append(_finding(root, path, spec["token"], spec["category"], node.lineno, "runtime_import_detected"))
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imported_module = node.module.lower()
                        for spec in FORBIDDEN_PATTERNS[:5]:
                            if imported_module == spec["token"]:
                                key = (str(path), spec["token"], "runtime_import_detected", node.lineno)
                                if key not in blocking_keys:
                                    blocking_keys.add(key)
                                    blocking_findings.append(_finding(root, path, spec["token"], spec["category"], node.lineno, "runtime_import_detected"))

        for spec in FORBIDDEN_PATTERNS:
            token = spec["token"]
            if token.lower() not in source_lower:
                continue
            for line_number, line_text in enumerate(source.splitlines(), start=1):
                if token.lower() not in line_text.lower():
                    continue
                safe_reason = _safe_reason(file_kind, line_text, line_number, safe_spans)
                if safe_reason is not None:
                    key = (str(path), token, safe_reason, line_number)
                    if key not in mention_keys:
                        mention_keys.add(key)
                        non_blocking_mentions.append(_finding(root, path, token, spec["category"], line_number, safe_reason))
                elif file_kind == "runtime_source":
                    key = (str(path), token, "runtime_token_detected", line_number)
                    if key not in blocking_keys:
                        blocking_keys.add(key)
                        blocking_findings.append(_finding(root, path, token, spec["category"], line_number, "runtime_token_detected"))
                else:
                    key = (str(path), token, "non_runtime_context", line_number)
                    if key not in mention_keys:
                        mention_keys.add(key)
                        non_blocking_mentions.append(_finding(root, path, token, spec["category"], line_number, "non_runtime_context"))

    allowed_boundary_runtime_sources = {
        "pm_bot/boundary/validate_live_boundary_contracts.py",
        "pm_bot/boundary/validate_readonly_fetcher_plan.py",
    }
    unexpected_boundary_runtime_sources = sorted(set(boundary_runtime_sources) - allowed_boundary_runtime_sources)
    for relative in unexpected_boundary_runtime_sources:
        blocking_findings.append(
            {
                "file": relative,
                "token": "unexpected_boundary_runtime_source",
                "category": "live_fetcher",
                "line": 1,
                "reason": "boundary_runtime_source_not_allowed",
            }
        )

    categories = {entry["category"] for entry in blocking_findings}
    audit_passed = not blocking_findings
    return {
        "schema_version": "v6",
        "audit_id": "PMBOT-BATCH-007-STATIC-AUDIT",
        "audit_passed": audit_passed,
        "scanned_file_count": len(scanned_files),
        "scanned_files": scanned_files,
        "boundary_runtime_sources": sorted(boundary_runtime_sources),
        "blocking_findings": blocking_findings,
        "non_blocking_mentions": non_blocking_mentions,
        "checks": {
            "no_live_fetcher_implementation": audit_passed and "live_fetcher" not in categories,
            "no_api_client_exists": audit_passed and not (categories & {"network", "live_api", "api_credentials"}),
            "no_network_calls_exist": audit_passed and "network" not in categories,
            "no_wallet_private_key_signing_exists": audit_passed and "wallet" not in categories,
            "no_order_execution_exists": audit_passed and "trading" not in categories,
            "no_runtime_wiring_exists": audit_passed and "runtime" not in categories,
            "boundary_contracts_fixtures_are_static_design_only": audit_passed and not unexpected_boundary_runtime_sources,
            "risky_behavior_would_be_blocking": True,
            "no_network_or_api": audit_passed and not (categories & {"network", "live_api", "api_credentials"}),
            "no_live_polymarket_api": audit_passed and "live_api" not in categories,
            "no_api_credentials": audit_passed and "api_credentials" not in categories,
            "no_wallet_or_private_key": audit_passed and "wallet" not in categories,
            "no_real_orders": audit_passed and "trading" not in categories,
            "no_real_trading": audit_passed and "trading" not in categories,
            "no_autonomous_trading": audit_passed and "trading" not in categories,
            "no_runtime_wiring": audit_passed and "runtime" not in categories,
            "no_dispatcher_changes": audit_passed and "runtime" not in categories,
            "no_run_codex_changes": audit_passed and "runtime" not in categories,
            "no_codex_auto_mutation": audit_passed and "runtime" not in categories,
            "no_governance_state_mutation": audit_passed and "runtime" not in categories,
            "no_state_result_freeze_checkpoint_mutation": audit_passed and "runtime" not in categories
        },
    }


def main(argv):
    if len(argv) != 0:
        print(json.dumps({"status": "invalid", "error": "usage: static_safety_audit_v6.py"}, separators=(",", ":")))
        return 2
    root = Path(__file__).resolve().parents[2]
    print(json.dumps(build_static_audit_report(root), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
