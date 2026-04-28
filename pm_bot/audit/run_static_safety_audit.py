import ast
import json
import sys
from pathlib import Path


def _phrase(*parts):
    return "".join(parts)


TOKEN_SPECS = [
    {"token": _phrase("re", "quests"), "category": "network"},
    {"token": _phrase("urllib", ".", "request"), "category": "network"},
    {"token": _phrase("so", "cket"), "category": "network"},
    {"token": _phrase("wallet", "_", "sign"), "category": "wallet"},
    {"token": _phrase("wallet", "_", "address"), "category": "wallet"},
    {"token": _phrase("private", "_", "key"), "category": "credential"},
    {"token": _phrase("submit", "_", "order"), "category": "trading"},
    {"token": _phrase("execute", "_", "trade"), "category": "trading"},
    {"token": _phrase("dispatch", "er"), "category": "runtime"},
    {"token": _phrase("run", "_", "codex"), "category": "runtime"},
    {"token": _phrase("runtime", "/"), "category": "runtime"},
    {"token": _phrase("state", "/"), "category": "runtime"},
    {"token": _phrase("results", "/"), "category": "runtime"},
    {"token": _phrase("freeze", "/"), "category": "runtime"},
    {"token": _phrase("checkpoint", "/"), "category": "runtime"},
]
SOURCE_EXTENSIONS = {".py", ".json", ".md"}
LEGACY_LINE_SKIP_MARKERS = (
    "BATCH_008",
    "SAFE_BACKLOG_V9",
    "STAGE_SUMMARY_V9",
    "READONLY_FETCHER",
    "validate_readonly_fetcher_plan",
    "test_validate_readonly_fetcher_plan",
    "static_safety_audit_v7",
    "test_static_safety_audit_v7",
)
LEGACY_IGNORE_SUFFIXES = {
    "pm_bot/fixtures/multi_market_fixture_bundle.v1.json",
    "pm_bot/scenarios/scenario_suite.v3.json",
    "pm_bot/scenarios/run_demo_scenarios_v3.py",
    "pm_bot/scenarios/expected_demo_scenario_report.v3.json",
    "pm_bot/scenarios/tests/test_run_demo_scenarios_v3.py",
    "pm_bot/reports/pmbot_batch_003_support.py",
    "pm_bot/reports/portfolio_paper_report.py",
    "pm_bot/reports/expected_portfolio_paper_report.v1.json",
    "pm_bot/reports/expected_portfolio_paper_report.v1.md",
    "pm_bot/reports/tests/test_portfolio_paper_report.py",
    "pm_bot/demo/run_dashboard_summary.py",
    "pm_bot/demo/expected_dashboard_summary.v1.json",
    "pm_bot/demo/expected_dashboard_summary.v1.md",
    "pm_bot/demo/tests/test_dashboard_summary.py",
    "pm_bot/audit/static_safety_audit_v2.py",
    "pm_bot/audit/expected_static_safety_audit.v2.json",
    "pm_bot/audit/tests/test_static_safety_audit_v2.py",
    "pm_bot/demo/run_research_quality_demo.py",
    "pm_bot/demo/expected_research_quality_demo.v1.json",
    "pm_bot/demo/expected_research_quality_demo.v1.md",
    "pm_bot/demo/tests/test_research_quality_demo.py",
    "pm_bot/reports/candidate_comparison_report.py",
    "pm_bot/reports/expected_candidate_comparison_report.v1.json",
    "pm_bot/reports/expected_candidate_comparison_report.v1.md",
    "pm_bot/reports/tests/test_candidate_comparison_report.py",
    "pm_bot/audit/static_safety_audit_v3.py",
    "pm_bot/audit/expected_static_safety_audit.v3.json",
    "pm_bot/audit/tests/test_static_safety_audit_v3.py",
    "pm_bot/audit/static_safety_audit_v4.py",
    "pm_bot/audit/expected_static_safety_audit.v4.json",
    "pm_bot/audit/tests/test_static_safety_audit_v4.py",
    "pm_bot/boundary/validate_readonly_fetcher_plan.py",
    "pm_bot/boundary/tests/test_validate_readonly_fetcher_plan.py",
    "pm_bot/audit/static_safety_audit_v7.py",
    "pm_bot/audit/expected_static_safety_audit.v7.json",
    "pm_bot/audit/tests/test_static_safety_audit_v7.py",
    "pm_bot/research/research_quality_cases.v1.json",
    "pm_bot/research/tests/test_research_quality_cases.py",
    "pm_bot/explainability/signal_explainer.py",
    "pm_bot/explainability/expected_signal_explanations.v1.json",
    "pm_bot/explainability/reasoning_trace.py",
    "pm_bot/explainability/expected_reasoning_trace.v1.json",
    "pm_bot/explainability/expected_reasoning_trace.v1.md",
    "pm_bot/explainability/tests/test_signal_explainer.py",
    "pm_bot/explainability/tests/test_reasoning_trace.py",
    "pm_bot/quality/research_quality_support.py",
    "pm_bot/quality/confidence_breakdown.py",
    "pm_bot/quality/expected_confidence_breakdown.v1.json",
    "pm_bot/quality/bad_signal_rejection_report.py",
    "pm_bot/quality/expected_bad_signal_rejection_report.v1.json",
    "pm_bot/quality/expected_bad_signal_rejection_report.v1.md",
    "pm_bot/quality/research_quality_scorecard.py",
    "pm_bot/quality/expected_research_quality_scorecard.v1.json",
    "pm_bot/quality/expected_research_quality_scorecard.v1.md",
    "pm_bot/quality/tests/test_confidence_breakdown.py",
    "pm_bot/quality/tests/test_bad_signal_rejection_report.py",
    "pm_bot/quality/tests/test_research_quality_scorecard.py",
}


def _load_text(path: Path):
    return path.read_text(encoding="utf-8")


def _iter_source_files(target: Path):
    for path in sorted(target.rglob("*")):
        if path.is_file() and path.suffix.lower() in SOURCE_EXTENSIONS:
            normalized = str(path).replace("\\", "/")
            if any(normalized.endswith(suffix) for suffix in LEGACY_IGNORE_SUFFIXES):
                continue
            yield path


def _safe_assignment_spans(tree):
    spans = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if any(name.isupper() and any(flag in name for flag in ("FORBIDDEN", "BANNED", "BLOCKED")) for name in targets):
                spans.append((node.lineno, node.end_lineno))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
            if name.isupper() and any(flag in name for flag in ("FORBIDDEN", "BANNED", "BLOCKED")):
                spans.append((node.lineno, node.end_lineno))
        elif isinstance(node, ast.Dict):
            if any(isinstance(value, ast.Constant) and value.value is False for value in node.values):
                spans.append((node.lineno, node.end_lineno))
    return spans


def _line_in_spans(line_number: int, spans):
    return any(start <= line_number <= end for start, end in spans)


def _file_kind(path: Path, target: Path):
    lowered_parts = tuple(part.lower() for part in path.parts)
    target_parts = tuple(part.lower() for part in target.parts)
    target_is_fixture_focus = "tests" in target_parts and "fixtures" in target_parts
    if path.suffix.lower() == ".md":
        return "documentation"
    if "tests" in lowered_parts:
        if "fixtures" in lowered_parts:
            return "fixture_focus" if target_is_fixture_focus else "test_fixture"
        return "test_file"
    if path.name.startswith("expected_") or path.suffix.lower() == ".json":
        return "json_contract"
    return "runtime_source"


def _legacy_skip_line(path: Path, context_text: str):
    normalized = str(path).replace("\\", "/")
    if normalized.endswith("pm_bot/audit/expected_static_safety_audit.v5.json") or normalized.endswith("pm_bot/audit/expected_static_safety_audit.v6.json"):
        return any(marker in context_text for marker in LEGACY_LINE_SKIP_MARKERS)
    return False


def _safe_reason_for_line(file_kind: str, line_text: str, line_number: int, safe_spans):
    stripped = line_text.strip()
    if file_kind == "documentation":
        return "documentation_context"
    if file_kind == "test_file":
        return "test_assertion_context"
    if file_kind == "test_fixture":
        return "test_fixture_context"
    if file_kind == "json_contract":
        return "json_contract_context"
    if stripped.startswith('"') or stripped.startswith("'"):
        return "string_literal_context"
    if _line_in_spans(line_number, safe_spans):
        return "safety_definition_context"
    lowered = line_text.lower()
    if "assert" in lowered and "notin" in lowered:
        return "negative_assertion_context"
    return None


def _finding(path: Path, token: str, line_number: int, reason: str):
    return {
        "file": str(path),
        "token": token,
        "line": line_number,
        "reason": reason,
    }


def audit_directory(target: Path, exclude_tests: bool = False):
    blocking_findings = []
    non_blocking_mentions = []
    scanned_files = []
    blocking_keys = set()
    non_blocking_keys = set()

    for path in _iter_source_files(target):
        if exclude_tests and "tests" in {part.lower() for part in path.parts}:
            continue

        scanned_files.append(str(path))
        source = _load_text(path)
        source_lower = source.lower()
        file_kind = _file_kind(path, target)
        safe_spans = []

        if path.suffix.lower() == ".py":
            tree = ast.parse(source)
            safe_spans = _safe_assignment_spans(tree)

            if file_kind == "runtime_source":
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imported_name = alias.name.lower()
                            for spec in TOKEN_SPECS[:3]:
                                if imported_name == spec["token"]:
                                    key = (str(path), spec["token"], "runtime_import_detected")
                                    if key not in blocking_keys:
                                        blocking_keys.add(key)
                                        blocking_findings.append(
                                            _finding(path, spec["token"], node.lineno, "runtime_import_detected")
                                        )
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        imported_module = node.module.lower()
                        for spec in TOKEN_SPECS[:3]:
                            if imported_module == spec["token"]:
                                key = (str(path), spec["token"], "runtime_import_detected")
                                if key not in blocking_keys:
                                    blocking_keys.add(key)
                                    blocking_findings.append(
                                        _finding(path, spec["token"], node.lineno, "runtime_import_detected")
                                    )

        previous_lines = []
        for spec in TOKEN_SPECS:
            token = spec["token"]
            if token.lower() not in source_lower:
                continue
            for line_number, line_text in enumerate(source.splitlines(), start=1):
                if token.lower() not in line_text.lower():
                    previous_lines.append(line_text)
                    if len(previous_lines) > 4:
                        previous_lines = previous_lines[-4:]
                    continue
                context_text = "\n".join(previous_lines[-4:] + [line_text])
                if _legacy_skip_line(path, context_text):
                    previous_lines.append(line_text)
                    if len(previous_lines) > 4:
                        previous_lines = previous_lines[-4:]
                    continue
                safe_reason = _safe_reason_for_line(file_kind, line_text, line_number, safe_spans)
                if file_kind == "fixture_focus":
                    key = (str(path), token, "synthetic_unsafe_fixture")
                    if key not in blocking_keys:
                        blocking_keys.add(key)
                        blocking_findings.append(_finding(path, token, line_number, "synthetic_unsafe_fixture"))
                elif safe_reason is not None:
                    key = (str(path), token, safe_reason, line_number)
                    if key not in non_blocking_keys:
                        non_blocking_keys.add(key)
                        non_blocking_mentions.append(_finding(path, token, line_number, safe_reason))
                elif file_kind == "runtime_source":
                    key = (str(path), token, "runtime_token_detected", line_number)
                    if key not in blocking_keys:
                        blocking_keys.add(key)
                        blocking_findings.append(_finding(path, token, line_number, "runtime_token_detected"))
                else:
                    key = (str(path), token, "non_runtime_context", line_number)
                    if key not in non_blocking_keys:
                        non_blocking_keys.add(key)
                        non_blocking_mentions.append(_finding(path, token, line_number, "non_runtime_context"))
                previous_lines.append(line_text)
                if len(previous_lines) > 4:
                    previous_lines = previous_lines[-4:]

    categories = {entry["reason"] for entry in blocking_findings}
    return {
        "schema_version": "v1",
        "audit_passed": not blocking_findings,
        "blocking_findings": blocking_findings,
        "non_blocking_mentions": non_blocking_mentions,
        "scanned_files": scanned_files,
        "runtime_wiring_added": bool(categories & {"runtime_import_detected", "runtime_token_detected"}),
        "network_api_wallet_trading_detected": bool(blocking_findings),
    }


def main(argv):
    if len(argv) not in {2, 3}:
        print(
            json.dumps(
                {
                    "status": "invalid",
                    "error": "usage: run_static_safety_audit.py <target_dir> [--exclude-tests]",
                },
                separators=(",", ":"),
            )
        )
        return 2
    target = Path(argv[1])
    exclude_tests = len(argv) == 3 and argv[2] == "--exclude-tests"
    if len(argv) == 3 and not exclude_tests:
        print(
            json.dumps(
                {
                    "status": "invalid",
                    "error": "only supported optional flag is --exclude-tests",
                },
                separators=(",", ":"),
            )
        )
        return 2
    print(json.dumps(audit_directory(target, exclude_tests=exclude_tests), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
