from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from pm_bot.simulated_decisions.rehearsal_simulated_decision_replay_links import (
    EXPECTED_LINK_FIELDS,
    EXPECTED_SAFETY_BOUNDARIES,
    LINK_SET_ID,
    LINKS_CONTRACT_VERSION,
    LINKS_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    REQUIRED_VALIDATION_COMMANDS,
    SAMPLE_LINKS_PATH,
    SAMPLE_OPERATOR_REPORT_PATH,
    TASK_ID,
    build_operator_report,
    build_rehearsal_simulated_decision_replay_links,
    load_rehearsal_simulated_decision_replay_link_inputs,
    load_rehearsal_simulated_decision_replay_links,
    main,
    validate_rehearsal_simulated_decision_replay_links,
)

DOC_PATH = Path("docs/PMBOT_REHEARSAL_016_REHEARSAL_SIMULATED_DECISION_REPLAY_LINKS_LOCAL_ONLY.md")
LINKS_PATH = Path(SAMPLE_LINKS_PATH)
REPORT_PATH = Path(SAMPLE_OPERATOR_REPORT_PATH)
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/simulated_decisions/", "pm_bot/tests/", "tests/")
EXPECTED_REHEARSAL_ARTIFACT_IDS = (
    "rehearsal_validation_replay_packet_fixture",
    "rehearsal_ci_safe_validation_runner_fixture",
    "rehearsal_acceptance_report_document",
    "rehearsal_source_quality_links_document",
    "rehearsal_paperlive_accounting_links_document",
)
EXPECTED_SIMULATED_DECISION_ARTIFACT_IDS = (
    "simulated_decision_packet_sample",
    "simulated_decision_audit_ledger_sample",
    "simulated_decision_replay_summary_sample",
    "simulated_decision_outcome_replay_links_sample",
)


def test_static_rehearsal_simulated_decision_replay_links_has_expected_contract() -> None:
    link_set = _load_links()

    assert tuple(link_set.keys()) == tuple(sorted(link_set.keys()))
    assert link_set["task_id"] == TASK_ID
    assert link_set["link_set_id"] == LINK_SET_ID
    assert link_set["contract_version"] == LINKS_CONTRACT_VERSION
    assert link_set["run_mode"] == LINKS_RUN_MODE
    assert link_set["created_at"] == "2026-05-09T10:30:00Z"
    assert link_set["local_only"] is True
    assert link_set["operator_review_required"] is True
    assert link_set["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert link_set["warnings"] == []


def test_builder_output_matches_static_sample_and_is_deterministic() -> None:
    inputs = load_rehearsal_simulated_decision_replay_link_inputs()

    first = build_rehearsal_simulated_decision_replay_links(inputs)
    second = build_rehearsal_simulated_decision_replay_links(deepcopy(inputs))

    assert first == second
    assert first == _load_links()


def test_static_sample_validates_as_rehearsal_simulated_decision_replay_links() -> None:
    validation = validate_rehearsal_simulated_decision_replay_links(
        load_rehearsal_simulated_decision_replay_links(LINKS_PATH)
    )

    assert validation.valid is True
    assert validation.errors == ()


def test_link_rows_cover_rehearsal_and_simulated_decision_records() -> None:
    link_set = _load_links()
    links = link_set["simulated_decision_replay_links"]

    assert tuple(link_set["link_fields"]) == EXPECTED_LINK_FIELDS
    assert len(links) == 2
    for link in links:
        assert set(link) == set(EXPECTED_LINK_FIELDS)
        assert link["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert link["link_state"] == "descriptive_rehearsal_simulated_decision_replay_link"
        assert link["value_policy"] == "record_identifiers_only_values_remain_in_local_artifacts"
        assert len(link["review_checks"]) == 3
        assert all(check["operator_review_status"] == OPERATOR_REVIEW_STATUS for check in link["review_checks"])
        for pair in link["local_reference_pairs"]:
            assert pair["rehearsal_local_reference"].startswith(ALLOWED_LOCAL_PREFIXES)
            assert pair["simulated_decision_local_reference"].startswith(ALLOWED_LOCAL_PREFIXES)

    first = links[0]
    assert first["rehearsal_artifact_ids"] == [
        "rehearsal_validation_replay_packet_fixture",
        "rehearsal_ci_safe_validation_runner_fixture",
    ]
    assert first["simulated_decision_artifact_ids"] == [
        "simulated_decision_packet_sample",
        "simulated_decision_audit_ledger_sample",
    ]
    assert "simulated_decision_packet_fixture_001" in first["simulated_decision_record_ids"][
        "simulated_decision_packet_sample"
    ]
    assert "simulated_decision_audit_ledger_fixture_001" in first["simulated_decision_record_ids"][
        "simulated_decision_audit_ledger_sample"
    ]

    second = links[1]
    assert second["rehearsal_artifact_ids"] == [
        "rehearsal_acceptance_report_document",
        "rehearsal_source_quality_links_document",
        "rehearsal_paperlive_accounting_links_document",
    ]
    assert second["simulated_decision_artifact_ids"] == [
        "simulated_decision_replay_summary_sample",
        "simulated_decision_outcome_replay_links_sample",
    ]
    assert "simulated_decision_replay_summary_fixture_001" in second["simulated_decision_record_ids"][
        "simulated_decision_replay_summary_sample"
    ]
    assert "simulated_decision_outcome_replay_links_fixture_001" in second["simulated_decision_record_ids"][
        "simulated_decision_outcome_replay_links_sample"
    ]


def test_artifacts_reference_existing_local_files_with_matching_digests() -> None:
    link_set = _load_links()
    artifacts = link_set["rehearsal_artifacts"] + link_set["simulated_decision_artifacts"]

    assert tuple(artifact["artifact_id"] for artifact in link_set["rehearsal_artifacts"]) == (
        EXPECTED_REHEARSAL_ARTIFACT_IDS
    )
    assert tuple(artifact["artifact_id"] for artifact in link_set["simulated_decision_artifacts"]) == (
        EXPECTED_SIMULATED_DECISION_ARTIFACT_IDS
    )
    for artifact in artifacts:
        path = Path(artifact["local_reference"])
        data = path.read_bytes()

        assert artifact["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert artifact["present"] is True
        assert artifact["record_count"] == len(artifact["record_ids"])
        assert "://" not in artifact["local_reference"]
        assert artifact["local_reference"].startswith(ALLOWED_LOCAL_PREFIXES)
        assert path.exists()
        assert artifact["byte_count"] == len(data)
        assert artifact["content_sha256"] == hashlib.sha256(data).hexdigest()


def test_link_rows_reference_existing_local_record_ids() -> None:
    link_set = _load_links()
    artifact_records = {
        artifact["artifact_id"]: set(artifact["record_ids"])
        for artifact in link_set["rehearsal_artifacts"] + link_set["simulated_decision_artifacts"]
    }

    for link in link_set["simulated_decision_replay_links"]:
        for artifact_id, record_ids in link["rehearsal_record_ids"].items():
            assert set(record_ids) <= artifact_records[artifact_id]
        for artifact_id, record_ids in link["simulated_decision_record_ids"].items():
            assert set(record_ids) <= artifact_records[artifact_id]


def test_summary_counts_and_required_validation_commands_match_content() -> None:
    link_set = _load_links()
    local_references = set(_collect_values_for_key(link_set, "local_reference"))

    assert link_set["required_validation_commands"] == list(REQUIRED_VALIDATION_COMMANDS)
    assert link_set["summary_counts"] == {
        "link_fields": len(link_set["link_fields"]),
        "local_references": len(local_references),
        "operator_review_steps": len(link_set["operator_review_steps"]),
        "rehearsal_artifacts": len(link_set["rehearsal_artifacts"]),
        "rehearsal_record_links": sum(
            len(link["rehearsal_record_ids"]) for link in link_set["simulated_decision_replay_links"]
        ),
        "required_validation_commands": len(link_set["required_validation_commands"]),
        "review_checks": sum(len(link["review_checks"]) for link in link_set["simulated_decision_replay_links"]),
        "simulated_decision_artifacts": len(link_set["simulated_decision_artifacts"]),
        "simulated_decision_record_links": sum(
            len(record_ids)
            for link in link_set["simulated_decision_replay_links"]
            for record_ids in link["simulated_decision_record_ids"].values()
        ),
        "simulated_decision_replay_links": len(link_set["simulated_decision_replay_links"]),
        "validation_command_records": len(link_set["validation_command_records"]),
        "warnings": len(link_set["warnings"]),
    }


def test_safety_boundaries_are_closed_for_rehearsal_simulated_decision_replay_links() -> None:
    link_set = _load_links()

    assert link_set["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert link_set["safety_boundaries"]["local_static_samples_only"] is True
    assert link_set["safety_boundaries"]["operator_review_required"] is True
    assert link_set["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in link_set["safety_boundaries"].items() if key.endswith("_allowed"))


def test_operator_report_sample_matches_report_builder_output() -> None:
    link_set = _load_links()
    report = REPORT_PATH.read_text(encoding="utf-8")

    assert build_operator_report(link_set) == report
    assert "# PMBOT Rehearsal Simulated Decision Replay Links" in report
    assert "simulated_decision_replay_links: 2" in report
    assert "Not execution approval and not runtime input." in report


def test_cli_writes_local_rehearsal_simulated_decision_replay_links(tmp_path: Path) -> None:
    links_path = tmp_path / "rehearsal_simulated_decision_replay_links.json"
    report_path = tmp_path / "rehearsal_simulated_decision_replay_links.md"

    exit_code = main(
        [
            "--output-links",
            str(links_path),
            "--output-report",
            str(report_path),
        ]
    )

    assert exit_code == 0
    assert json.loads(links_path.read_text(encoding="utf-8")) == _load_links()
    assert build_operator_report(_load_links()) == report_path.read_text(encoding="utf-8")


def test_validation_rejects_record_and_digest_drift() -> None:
    link_set = _load_links()
    link_set["simulated_decision_replay_links"][0]["simulated_decision_record_ids"][
        "simulated_decision_packet_sample"
    ] = ["missing.local.record"]
    link_set["rehearsal_artifacts"][0]["content_sha256"] = "0" * 64

    validation = validate_rehearsal_simulated_decision_replay_links(link_set)

    assert validation.valid is False
    assert any("simulated_decision_record_ids must exist" in error for error in validation.errors)
    assert any("content_sha256 must match local bytes" in error for error in validation.errors)


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    assert _find_disallowed_terms(_load_links()) == []


def test_documentation_registers_rehearsal_simulated_decision_replay_links_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Link set: `{LINK_SET_ID}`" in document
    assert f"Contract: `{LINKS_CONTRACT_VERSION}`" in document
    assert f"Run mode: `{LINKS_RUN_MODE}`" in document
    assert SAMPLE_LINKS_PATH in document
    assert SAMPLE_OPERATOR_REPORT_PATH in document
    assert "pm_bot/simulated_decisions/samples/simulated_decision_replay_summary.fixture.json" in document
    assert "pm_bot/simulated_decisions/samples/simulated_decision_outcome_replay_links.fixture.json" in document
    assert "No market recommendation, forecast scoring, action guidance, or selection advice." in document
    assert "No probability, EV, edge, or confidence scoring." in document
    assert "This link set is not execution approval and is not runtime input." in document


def _load_links() -> dict:
    return json.loads(LINKS_PATH.read_text(encoding="utf-8"))


def _collect_values_for_key(value: object, key: str) -> list[str]:
    matches: list[str] = []
    if isinstance(value, dict):
        for nested_key, nested_value in value.items():
            if nested_key == key:
                matches.append(str(nested_value))
            matches.extend(_collect_values_for_key(nested_value, key))
    elif isinstance(value, list):
        for nested_value in value:
            matches.extend(_collect_values_for_key(nested_value, key))
    return matches


def _find_disallowed_terms(value: object, path: str = "$") -> list[str]:
    disallowed_tokens = {
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
            if _has_token(str(key), disallowed_tokens):
                hits.append(key_path)
            if key in {"command_label", "local_reference", "required_validation_commands"}:
                continue
            hits.extend(_find_disallowed_terms(nested_value, key_path))
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            hits.extend(_find_disallowed_terms(nested_value, f"{path}[{index}]"))
    elif isinstance(value, str) and _has_token(value, disallowed_tokens):
        hits.append(path)
    return hits


def _has_token(value: str, disallowed_tokens: set[str]) -> bool:
    normalized = "".join(character if character.isalnum() else "_" for character in value.lower())
    tokens = {token for token in normalized.split("_") if token}
    return bool(tokens & disallowed_tokens)
