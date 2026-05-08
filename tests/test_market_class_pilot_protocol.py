import ast
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_JSON = ROOT / "pm_bot" / "llm" / "market_class_pilot_taxonomy.v1.json"
SELECTION_JSON = ROOT / "pm_bot" / "llm" / "market_class_pilot_selection_criteria.v1.json"
CANDIDATE_CONTRACT = ROOT / "pm_bot" / "llm" / "market_class_pilot_candidate_contract.v1.json"
SOURCE_CAPTURE_CONTRACT = (
    ROOT / "pm_bot" / "llm" / "market_class_source_capture_candidate_contract.v1.json"
)
OPERATOR_REVIEW_CONTRACT = (
    ROOT / "pm_bot" / "llm" / "market_class_operator_review_contract.v1.json"
)
PIPELINE = ROOT / "pm_bot" / "llm" / "market_class_pilot_pipeline.py"
STATUS_JSON = ROOT / "pm_bot" / "llm" / "market_class_pilot_protocol_status.v1.json"
DRY_RUN_JSON = ROOT / "pm_bot" / "llm" / "market_class_pilot_dry_run_plan.v1.json"
RESULT_JSON = ROOT / "docs" / "PMBOT_SOURCE_008B_RESULT.json"

EXPECTED_CLASSES = ["esports", "weather", "crypto"]
BASE_REQUIRED_CAPTURE_FIELDS = {
    "market_id",
    "market_class",
    "market_title_or_question",
    "resolution_wording",
    "official_source_name",
    "official_source_reference",
    "source_checked_at_local",
    "captured_resolution_text",
    "source_reliability_review",
    "operator_notes",
    "capture_status",
}
FORBIDDEN_FIELD_TOKENS = [
    "probability",
    "ev",
    "edge",
    "confidence",
    "side_selection",
    "side-selection",
    "recommended_side",
    "recommendation",
    "trade_recommendation",
]


def _load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _iter_keys(payload):
    if isinstance(payload, dict):
        for key, value in payload.items():
            yield key
            yield from _iter_keys(value)
    elif isinstance(payload, list):
        for item in payload:
            yield from _iter_keys(item)


def test_taxonomy_has_exactly_expected_market_classes():
    taxonomy = _load_json(TAXONOMY_JSON)

    assert taxonomy["schema_version"] == "market_class_pilot_taxonomy.v1"
    assert taxonomy["class_order"] == EXPECTED_CLASSES
    assert list(taxonomy["classes"].keys()) == EXPECTED_CLASSES


def test_taxonomy_required_sections_and_checklist_fields_exist():
    taxonomy = _load_json(TAXONOMY_JSON)
    required_sections = {
        "description",
        "expected_resolution_source_types",
        "common_resolution_risks",
        "required_capture_fields",
        "operator_review_focus",
        "future_read_only_fetch_requirements",
    }

    for market_class in EXPECTED_CLASSES:
        class_spec = taxonomy["classes"][market_class]
        assert required_sections.issubset(class_spec.keys()), market_class
        assert BASE_REQUIRED_CAPTURE_FIELDS.issubset(
            set(class_spec["required_capture_fields"])
        ), market_class
        assert class_spec["expected_resolution_source_types"], market_class
        assert class_spec["common_resolution_risks"], market_class
        assert class_spec["operator_review_focus"], market_class
        assert class_spec["future_read_only_fetch_requirements"], market_class


def test_selection_criteria_order_and_required_rules():
    criteria = _load_json(SELECTION_JSON)
    labels = [item["label"] for item in criteria["criteria"]]

    assert criteria["selection_order"] == EXPECTED_CLASSES
    assert "prefer clear resolution wording" in labels
    assert "prefer identifiable official source" in labels
    assert "prefer near/mid-term markets" in labels
    assert (
        "avoid ambiguous/meme/private-person/legal/medical rumor-driven markets for first pilots"
        in labels
    )
    assert "order: esports, weather, crypto" in labels


def test_contracts_do_not_define_forbidden_market_prediction_or_action_fields():
    for path in [CANDIDATE_CONTRACT, SOURCE_CAPTURE_CONTRACT, OPERATOR_REVIEW_CONTRACT]:
        payload = _load_json(path)
        keys = {key.lower() for key in _iter_keys(payload)}
        for token in FORBIDDEN_FIELD_TOKENS:
            assert token not in keys, (path, token)


def test_cli_protocol_only_and_each_class_dry_run_work():
    status_result = subprocess.run(
        [sys.executable, "-m", "pm_bot.llm.market_class_pilot_pipeline", "--protocol-only"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    status = json.loads(status_result.stdout)
    assert status["status"] == "protocol_only_no_network"
    assert status["class_order"] == EXPECTED_CLASSES
    assert status["current_source_state"]["real_ingested_template_count"] >= 1
    assert status["current_source_state"]["draft_ingested_template_count"] >= 1
    assert status["current_source_state"]["ready_ingested_template_count"] == 0
    assert status["current_source_state"]["future_live_002_allowed"] is False

    for market_class in EXPECTED_CLASSES:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pm_bot.llm.market_class_pilot_pipeline",
                "--dry-run",
                "--class",
                market_class,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(result.stdout)
        assert payload["status"] == "dry_run_planned_not_fetched"
        assert payload["target_classes"] == [market_class]
        assert payload["target_class_count"] == 1
        assert payload["class_plans"][0]["market_class"] == market_class
        assert payload["class_plans"][0]["candidate_count"] == 0
        assert payload["class_plans"][0]["network_calls_performed"] == 0
        assert payload["validation"]["validator_status"] == "passed"


def test_cli_write_all_classes_writes_protocol_and_dry_run_artifacts():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.llm.market_class_pilot_pipeline",
            "--write",
            "--all-classes",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    status = _load_json(STATUS_JSON)
    plan = _load_json(DRY_RUN_JSON)

    assert payload["status"] == "written"
    assert status["class_order"] == EXPECTED_CLASSES
    assert plan["target_classes"] == EXPECTED_CLASSES
    assert [item["market_class"] for item in plan["class_plans"]] == EXPECTED_CLASSES
    assert plan["validation"]["validator_status"] == "passed"


def test_placeholder_module_has_no_network_or_browser_client_imports():
    tree = ast.parse(PIPELINE.read_text(encoding="utf-8"))
    forbidden_roots = {
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "selenium",
        "playwright",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_roots
        if isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            assert root not in forbidden_roots

    source = PIPELINE.read_text(encoding="utf-8").lower()
    for token in ("openrouter_api_key", "bearer ", "secret_key"):
        assert token not in source


def test_source_007_and_008_state_remains_preserved():
    ingest_result = _load_json(
        ROOT / "pm_bot" / "llm" / "manual_resolution_source_capture_ingest_result.v1.json"
    )
    gate = _load_json(ROOT / "pm_bot" / "llm" / "post_capture_batch_readiness_gate.v1.json")
    source_008 = _load_json(ROOT / "docs" / "PMBOT_SOURCE_008_RESULT.json")
    source_008b = _load_json(RESULT_JSON)

    assert ingest_result["real_ingested_template_count"] >= source_008b["real_ingested_template_count_preserved"]
    assert gate["real_ingested_template_count"] >= source_008b["real_ingested_template_count_preserved"]
    assert gate["draft_ingested_template_count"] >= source_008b["draft_ingested_template_count_preserved"]
    assert gate["ready_ingested_template_count"] == 0
    assert gate["future_live_002_allowed"] is False
    assert source_008["current_real_ingested_template_count_preserved"] == 1
    assert source_008["current_draft_ingested_template_count_preserved"] == 1
    assert source_008["future_live_002_allowed"] is False
    assert source_008b["real_ingested_template_count_preserved"] == 1
    assert source_008b["draft_ingested_template_count_preserved"] == 1
    assert source_008b["ready_ingested_template_count_preserved"] == 0
    assert source_008b["future_live_002_allowed"] is False


def test_protocol_artifacts_are_valid_json():
    paths = [
        TAXONOMY_JSON,
        SELECTION_JSON,
        CANDIDATE_CONTRACT,
        SOURCE_CAPTURE_CONTRACT,
        OPERATOR_REVIEW_CONTRACT,
        STATUS_JSON,
        DRY_RUN_JSON,
        RESULT_JSON,
    ]
    for path in paths:
        assert isinstance(_load_json(path), dict), path
