import ast
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"

REQUIRED_DOCS = {
    "implementation_plan": DOCS_DIR / "PM_BOT_READONLY_FETCHER_IMPLEMENTATION_PLAN_V1.md",
    "approval_checklist": DOCS_DIR / "PM_BOT_READONLY_FETCHER_APPROVAL_CHECKLIST_V1.md",
    "failure_modes": DOCS_DIR / "PM_BOT_READONLY_FETCHER_FAILURE_MODES_V1.md",
    "boundary_doc": DOCS_DIR / "PM_BOT_LIVE_READONLY_BOUNDARY_V1.md",
    "approval_gates_doc": DOCS_DIR / "PM_BOT_LIVE_READONLY_APPROVAL_GATES_V1.md",
    "paper_replay_contract": ROOT / "pm_bot" / "contracts" / "paper_replay_import_contract.v1.json",
}

REQUIRED_PLAN_PHRASES = {
    "implementation_plan": [
        "design-only planning task",
        "does not implement a live fetcher",
        "future module names only",
        "future raw snapshot flow",
        "future normalized snapshot flow",
        "future quarantine flow",
        "future paper replay import flow",
        "future tests required before network or api approval",
        "future approval gates",
        "separate human approval and flocky validation",
    ],
    "approval_checklist": [
        "human approval required",
        "flocky validation required",
        "no wallet or private key access",
        "no execution or order imports",
        "raw snapshot artifact only",
        "normalized snapshot validation required",
        "quarantine required",
        "paper replay only",
        "no live trade path",
        "no autonomous trading",
    ],
    "failure_modes": [
        "api unavailable",
        "malformed payload",
        "stale data",
        "missing market status",
        "wrong outcome mapping",
        "price and liquidity contradiction",
        "duplicate snapshot",
        "resolved market returned as active",
        "rate limit",
        "partial capture",
        "schema drift",
        "quarantine handling",
        "no direct execution response",
    ],
}

FORBIDDEN_RUNTIME_MODULES = [
    ROOT / "pm_bot" / "live_readonly",
    ROOT / "pm_bot" / "boundary" / "fetch_market_snapshots.py",
    ROOT / "pm_bot" / "boundary" / "normalize_snapshot.py",
    ROOT / "pm_bot" / "boundary" / "quarantine_snapshot.py",
]

FORBIDDEN_CODE_TOKENS = [
    "requests",
    "urllib.request",
    "httpx",
    "aiohttp",
    "socket",
    "api.polymarket",
    "clob.polymarket",
    "gamma-api",
]

FORBIDDEN_FIELD_TOKENS = {
    "credentials": ["api_key", "api_secret", "authorization_header"],
    "wallet": ["wallet", "wallet_address", "private_key", "seed_phrase", "signer", "signature"],
    "execution": ["submit_order", "place_order", "execute_trade", "order_instruction"],
}


def load_text(path: Path):
    return path.read_text(encoding="utf-8")


def load_json(path: Path):
    return json.loads(load_text(path))


def required_docs(root: Path):
    docs_dir = root / "docs"
    return {
        "implementation_plan": docs_dir / "PM_BOT_READONLY_FETCHER_IMPLEMENTATION_PLAN_V1.md",
        "approval_checklist": docs_dir / "PM_BOT_READONLY_FETCHER_APPROVAL_CHECKLIST_V1.md",
        "failure_modes": docs_dir / "PM_BOT_READONLY_FETCHER_FAILURE_MODES_V1.md",
        "boundary_doc": docs_dir / "PM_BOT_LIVE_READONLY_BOUNDARY_V1.md",
        "approval_gates_doc": docs_dir / "PM_BOT_LIVE_READONLY_APPROVAL_GATES_V1.md",
        "paper_replay_contract": root / "pm_bot" / "contracts" / "paper_replay_import_contract.v1.json",
    }


def missing_required_files(root: Path):
    missing = []
    for path in required_docs(root).values():
        if not path.exists():
            missing.append(str(path.relative_to(root)).replace("\\", "/"))
    return missing


def phrase_report(root: Path):
    docs = required_docs(root)
    report = {}
    for name, phrases in REQUIRED_PLAN_PHRASES.items():
        text = load_text(docs[name]).lower()
        report[name] = {phrase: phrase in text for phrase in phrases}
    return report


def live_fetcher_modules_exist(root: Path):
    found = []
    runtime_modules = [
        root / "pm_bot" / "live_readonly",
        root / "pm_bot" / "boundary" / "fetch_market_snapshots.py",
        root / "pm_bot" / "boundary" / "normalize_snapshot.py",
        root / "pm_bot" / "boundary" / "quarantine_snapshot.py",
    ]
    for path in runtime_modules:
        if path.exists():
            found.append(str(path.relative_to(root)).replace("\\", "/"))
    return found


def network_code_findings(root: Path):
    findings = []
    for path in (root / "pm_bot").rglob("*.py"):
        relative = str(path.relative_to(root)).replace("\\", "/")
        if relative.startswith("pm_bot/audit/"):
            continue
        if "/tests/" in relative or relative.startswith("pm_bot/boundary/tests/"):
            continue
        if relative in {
            "pm_bot/boundary/validate_live_boundary_contracts.py",
            "pm_bot/boundary/validate_readonly_fetcher_plan.py",
        }:
            continue
        text = load_text(path).lower()
        for token in FORBIDDEN_CODE_TOKENS:
            if token in text:
                findings.append({"file": relative, "token": token})
    return findings


def collect_key_names(payload):
    keys = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            keys.add(str(key))
            keys.update(collect_key_names(value))
    elif isinstance(payload, list):
        for item in payload:
            keys.update(collect_key_names(item))
    return keys


def contract_field_report(root: Path):
    contract = load_json(required_docs(root)["paper_replay_contract"])
    keys = {key.lower() for key in collect_key_names(contract)}
    return {
        category: {token: token in keys for token in tokens}
        for category, tokens in FORBIDDEN_FIELD_TOKENS.items()
    }


def paper_replay_is_no_execution(root: Path):
    contract = load_json(required_docs(root)["paper_replay_contract"])
    text = json.dumps(contract, sort_keys=True).lower()
    required_phrases = [
        "paper",
        "replay",
        "no_execution",
        "no_live_order",
    ]
    return {phrase: phrase in text for phrase in required_phrases}


def validate_standard_library_only():
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    return imports <= {"ast", "json", "sys", "pathlib"}


def build_report(root: Path):
    missing_files = missing_required_files(root)
    phrase_checks = phrase_report(root) if not missing_files else {}
    live_fetcher_modules = live_fetcher_modules_exist(root)
    network_findings = network_code_findings(root)
    field_report = contract_field_report(root) if not missing_files else {}
    paper_replay_report = paper_replay_is_no_execution(root) if not missing_files else {}

    plan_design_only = bool(phrase_checks) and all(
        all(phrase_checks[doc].values()) for doc in REQUIRED_PLAN_PHRASES
    )
    no_credentials_fields = bool(field_report) and not any(field_report["credentials"].values())
    no_wallet_fields = bool(field_report) and not any(field_report["wallet"].values())
    no_execution_fields = bool(field_report) and not any(field_report["execution"].values())
    future_approval_required = bool(phrase_checks) and (
        phrase_checks["implementation_plan"]["separate human approval and flocky validation"]
        and phrase_checks["approval_checklist"]["human approval required"]
        and phrase_checks["approval_checklist"]["flocky validation required"]
    )
    paper_replay_no_execution = bool(paper_replay_report) and all(paper_replay_report.values())

    checks = {
        "design_only_plan_confirmed": plan_design_only,
        "no_live_fetcher_module_exists": not live_fetcher_modules,
        "no_network_or_api_implementation_exists": not network_findings,
        "no_credentials_fields_introduced": no_credentials_fields,
        "no_wallet_private_key_fields_introduced": no_wallet_fields,
        "no_order_execution_fields_introduced": no_execution_fields,
        "future_implementation_requires_approval": future_approval_required,
        "paper_replay_remains_no_execution": paper_replay_no_execution,
        "standard_library_only": validate_standard_library_only(),
    }

    return {
        "schema_version": "v1",
        "artifact_type": "readonly_fetcher_plan_validation_report",
        "design_only": True,
        "planning_only": True,
        "fixture_only": True,
        "paper_only": True,
        "local_only": True,
        "deterministic": True,
        "missing_files": missing_files,
        "phrase_checks": phrase_checks,
        "forbidden_live_fetcher_modules": live_fetcher_modules,
        "network_findings": network_findings,
        "contract_field_report": field_report,
        "paper_replay_report": paper_replay_report,
        "checks": checks,
        "validation_passed": not missing_files and all(checks.values()),
    }


def main(argv):
    if len(argv) != 0:
        print(json.dumps({"status": "invalid", "error": "usage: validate_readonly_fetcher_plan.py"}, separators=(",", ":")))
        return 2
    report = build_report(ROOT)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["validation_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
