from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from pm_bot.dashboard.local_queue_paperlive_status_surface import (
    LOCAL_ONLY_SAFETY_BOUNDARIES,
    LOCAL_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    REQUEST_CONTRACT_VERSION,
    SAMPLE_STATUS_SURFACE_PATH,
    STATUS_SURFACE_CONTRACT_VERSION,
    QueuePaperliveStatusSurfaceValidationError,
    build_local_queue_paperlive_status_surface,
    build_operator_report,
    load_status_request,
    main,
    validate_local_queue_paperlive_status_surface,
    validate_status_request,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "dashboard"
VALID_REQUEST_PATH = FIXTURE_DIR / "local_queue_paperlive_status_request.valid.json"
DOC_PATH = Path("docs/PMBOT_DASHBOARD_002_QUEUE_AND_PAPERLIVE_STATUS_SURFACE.md")
TASK_ID = "PMBOT-DASHBOARD-002-QUEUE-AND-PAPERLIVE-STATUS-SURFACE"


def test_valid_fixture_request_builds_queue_paperlive_status_surface() -> None:
    request = load_status_request(VALID_REQUEST_PATH)
    validation = validate_status_request(request)
    surface = build_local_queue_paperlive_status_surface(request)

    assert validation.valid is True
    assert validation.errors == ()
    assert surface["contract_version"] == STATUS_SURFACE_CONTRACT_VERSION
    assert surface["surface_id"].startswith("local_queue_paperlive_status_surface_fixture_001-")
    assert surface["surface_label"] == "PMBOT queue and paperlive local status"
    assert surface["run_mode"] == LOCAL_RUN_MODE
    assert surface["local_only"] is True
    assert surface["operator_review_required"] is True
    assert surface["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert surface["summary_counts"] == {
        "operator_review_pending_records": 7,
        "paperlive_status_records": 2,
        "queue_status_records": 3,
        "validation_records": 2,
        "warnings": 0,
    }
    assert surface["queue_status_summary"][0] == {
        "local_reference": "tests/test_codex_queue_pmbot_templates.py",
        "notes": "Static queue coverage includes the queue and paperlive status surface task identifier.",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "queue_group": "next_twenty_template",
        "record_id": f"queue_status.{TASK_ID}",
        "runner_state": "ready_for_operator_review",
        "safety_class": "local_only_no_execution",
        "status_label": "template_listed_static_record",
        "task_id": TASK_ID,
        "task_template": "queue_and_paperlive_status_surface",
        "task_title": "PMBOT queue and paperlive status surface",
        "validation_profile": "pmbot_local_code_tests",
    }
    assert surface["paperlive_status_summary"][1] == {
        "artifact_id": "crypto_paperlive_observation_ledger_static_status",
        "contract_version": "pmbot_crypto_paperlive_observation_ledger.v1",
        "local_reference": "docs/PMBOT_CRYPTO_PILOT_003_CRYPTO_PAPERLIVE_OBSERVATION_LEDGER_LOCAL_ONLY.md",
        "notes": "Static crypto paperlive observation ledger fixture is available for operator inspection.",
        "operator_review_status": OPERATOR_REVIEW_STATUS,
        "paperlive_area": "crypto_observation_ledger",
        "record_count": 1,
        "record_id": "paperlive_status.crypto_paperlive_observation_ledger_static_status",
        "record_state": "ledger_only_static_sample",
        "run_mode": "local_descriptive_crypto_paperlive_observation_ledger",
        "runner_state": "ready_for_operator_review",
        "source_fixture_reference": (
            "pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/"
            "crypto_paperlive_observation_ledger.valid.json"
        ),
        "status_label": "static_local_reference_ready",
        "task_id": "PMBOT-CRYPTO-PILOT-003-CRYPTO-PAPERLIVE-OBSERVATION-LEDGER-LOCAL-ONLY",
    }
    assert surface["validation_status_summary"][0]["command_label"] == "python -m compileall pm_bot tests"
    assert surface["safety_boundaries"] == LOCAL_ONLY_SAFETY_BOUNDARIES


def test_status_surface_is_deterministic_for_same_request() -> None:
    request = load_status_request(VALID_REQUEST_PATH)

    first = build_local_queue_paperlive_status_surface(request)
    second = build_local_queue_paperlive_status_surface(deepcopy(request))

    assert first == second
    assert len(first["surface_id"]) == len("local_queue_paperlive_status_surface_fixture_001-") + 12


def test_static_sample_matches_builder_output() -> None:
    request = load_status_request(VALID_REQUEST_PATH)
    sample = json.loads(Path(SAMPLE_STATUS_SURFACE_PATH).read_text(encoding="utf-8"))

    assert build_local_queue_paperlive_status_surface(request) == sample


def test_static_sample_validates_as_status_surface_artifact() -> None:
    sample = json.loads(Path(SAMPLE_STATUS_SURFACE_PATH).read_text(encoding="utf-8"))

    validation = validate_local_queue_paperlive_status_surface(sample)

    assert validation.valid is True
    assert validation.errors == ()


def test_cli_writes_local_status_surface_and_operator_report(tmp_path: Path) -> None:
    surface_path = tmp_path / "local_queue_paperlive_status_surface.json"
    report_path = tmp_path / "local_queue_paperlive_status_surface.md"

    exit_code = main(
        [
            "--request",
            str(VALID_REQUEST_PATH),
            "--output-surface",
            str(surface_path),
            "--output-report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    surface = json.loads(surface_path.read_text(encoding="utf-8"))
    report = report_path.read_text(encoding="utf-8")
    assert surface["contract_version"] == STATUS_SURFACE_CONTRACT_VERSION
    assert surface["errors"] == []
    assert surface["warnings"] == []
    assert "# PMBOT Queue And Paperlive Status Surface" in report
    assert TASK_ID in report
    assert "crypto_paperlive_observation_ledger_static_status" in report
    assert "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py" in report
    assert "Makes no network, LLM, external market API, wallet, order, transaction endpoint, runtime, browser, scheduler, or worker calls." in report


def test_operator_report_is_deterministic() -> None:
    request = load_status_request(VALID_REQUEST_PATH)
    surface = build_local_queue_paperlive_status_surface(request)

    first = build_operator_report(surface)
    second = build_operator_report(deepcopy(surface))

    assert first == second
    assert "Operator review: `pending_operator_review`" in first
    assert "Descriptive status inventory only" in first


def test_request_rejects_network_like_local_reference() -> None:
    request = load_status_request(VALID_REQUEST_PATH)
    request["paperlive_status_records"][0]["source_fixture_reference"] = "https://example.invalid/static.json"

    validation = validate_status_request(request)

    assert validation.valid is False
    assert any("source_fixture_reference must be a local reference" in error for error in validation.errors)
    with pytest.raises(QueuePaperliveStatusSurfaceValidationError):
        build_local_queue_paperlive_status_surface(request)


def test_request_rejects_reference_outside_allowed_local_paths() -> None:
    request = load_status_request(VALID_REQUEST_PATH)
    request["queue_status_records"][0]["local_reference"] = "pm_bot/wallet/local_queue_status.json"

    validation = validate_status_request(request)

    assert validation.valid is False
    assert any("local_reference is outside the dashboard boundary" in error for error in validation.errors)


def test_request_rejects_scoring_or_selection_fields() -> None:
    request = load_status_request(VALID_REQUEST_PATH)
    request["queue_status_records"][0]["selection_note"] = "not allowed in local status surfaces"

    validation = validate_status_request(request)

    assert validation.valid is False
    assert any("forbidden status decision field detected" in error for error in validation.errors)


def test_status_surface_rejects_summary_count_drift() -> None:
    request = load_status_request(VALID_REQUEST_PATH)
    surface = build_local_queue_paperlive_status_surface(request)
    surface["summary_counts"]["queue_status_records"] = 99

    validation = validate_local_queue_paperlive_status_surface(surface)

    assert validation.valid is False
    assert any("summary_counts must match status rows" in error for error in validation.errors)


def test_output_contract_has_no_scoring_or_selection_fields() -> None:
    request = load_status_request(VALID_REQUEST_PATH)
    surface = build_local_queue_paperlive_status_surface(request)

    offending_paths = _find_output_decision_terms(surface)

    assert offending_paths == []


def test_status_request_contract_version_is_explicit() -> None:
    request = load_status_request(VALID_REQUEST_PATH)

    assert request["contract_version"] == REQUEST_CONTRACT_VERSION


def test_documentation_registers_surface_contract_fixtures_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Contract: `{STATUS_SURFACE_CONTRACT_VERSION}`" in document
    assert "pm_bot/dashboard/samples/local_queue_paperlive_status_surface.fixture.json" in document
    assert "pm_bot/tests/fixtures/dashboard/local_queue_paperlive_status_request.valid.json" in document
    assert "No forecast scoring, action guidance, or selection advice." in document
    assert "This status surface is not execution approval and is not runtime input." in document


def _find_output_decision_terms(value: object, path: str = "$") -> list[str]:
    forbidden_tokens = {
        "advice",
        "buy",
        "confidence",
        "edge",
        "enter",
        "ev",
        "exit",
        "forecast",
        "guidance",
        "hold",
        "odds",
        "pick",
        "probability",
        "recommendation",
        "recommendations",
        "score",
        "scoring",
        "selection",
        "sell",
        "side",
        "stake",
        "wager",
    }
    hits: list[str] = []
    if isinstance(value, dict):
        for key, nested_value in value.items():
            key_path = f"{path}.{key}"
            if _has_token(str(key), forbidden_tokens):
                hits.append(key_path)
            hits.extend(_find_output_decision_terms(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(_find_output_decision_terms(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_token(value, forbidden_tokens):
        hits.append(path)
    return hits


def _has_token(value: str, forbidden_tokens: set[str]) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & forbidden_tokens)
