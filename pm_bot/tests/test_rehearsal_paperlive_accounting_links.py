from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from pm_bot.paper_accounting.rehearsal_paperlive_accounting_links import (
    EXPECTED_LINK_FIELDS,
    EXPECTED_PAPERLIVE_ACCOUNTING_RECORD_ID_FIELDS,
    EXPECTED_REHEARSAL_RECORD_ID_FIELDS,
    EXPECTED_SAFETY_BOUNDARIES,
    LINK_SET_ID,
    LINKS_CONTRACT_VERSION,
    LINKS_RUN_MODE,
    OBSERVATION_REPLAY_PATH,
    OPERATOR_REVIEW_STATUS,
    PAPER_ACCOUNTING_LEDGER_PATH,
    PAPER_ACCOUNTING_SESSION_SUMMARY_PATH,
    PAPER_ACCOUNTING_VALIDATION_PATH,
    PAPERLIVE_RECONCILIATION_PATH,
    REHEARSAL_PACKET_PATH,
    REQUIRED_VALIDATION_COMMANDS,
    SAMPLE_LINKS_PATH,
    SAMPLE_OPERATOR_REPORT_PATH,
    TASK_ID,
    build_operator_report,
    build_rehearsal_paperlive_accounting_links,
    load_rehearsal_paperlive_accounting_link_inputs,
    load_rehearsal_paperlive_accounting_links,
    main,
    validate_rehearsal_paperlive_accounting_links,
)

DOC_PATH = Path("docs/PMBOT_REHEARSAL_015_REHEARSAL_PAPERLIVE_ACCOUNTING_LINKS_LOCAL_ONLY.md")
LINKS_PATH = Path(SAMPLE_LINKS_PATH)
REPORT_PATH = Path(SAMPLE_OPERATOR_REPORT_PATH)
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/paper_accounting/samples/", "pm_bot/tests/", "tests/")
EXPECTED_REHEARSAL_ARTIFACT_IDS = (
    "crypto_paperlive_rehearsal_packet_fixture",
    "crypto_paperlive_observation_replay_fixture",
)
EXPECTED_ACCOUNTING_ARTIFACT_IDS = (
    "paperlive_accounting_reconciliation_sample",
    "paper_accounting_ledger_sample",
    "paper_accounting_validation_sample",
    "paper_accounting_session_summary_sample",
)


def test_static_rehearsal_paperlive_accounting_links_has_expected_contract() -> None:
    link_set = _load_links()

    assert tuple(link_set.keys()) == tuple(sorted(link_set.keys()))
    assert link_set["task_id"] == TASK_ID
    assert link_set["link_set_id"] == LINK_SET_ID
    assert link_set["build_id"] == "pmbot-rehearsal-paperlive-accounting-links-001-43d69351f7da"
    assert link_set["contract_version"] == LINKS_CONTRACT_VERSION
    assert link_set["run_mode"] == LINKS_RUN_MODE
    assert link_set["created_at"] == "2026-05-09T10:00:00Z"
    assert link_set["local_only"] is True
    assert link_set["operator_review_required"] is True
    assert link_set["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert link_set["errors"] == []
    assert link_set["warnings"] == []


def test_builder_output_matches_static_sample_and_is_deterministic() -> None:
    inputs = load_rehearsal_paperlive_accounting_link_inputs()

    first = build_rehearsal_paperlive_accounting_links(inputs)
    second = build_rehearsal_paperlive_accounting_links(deepcopy(inputs))

    assert first == second
    assert first == _load_links()


def test_static_sample_validates_as_rehearsal_paperlive_accounting_links() -> None:
    link_set = load_rehearsal_paperlive_accounting_links(LINKS_PATH)

    validation = validate_rehearsal_paperlive_accounting_links(link_set)

    assert validation.valid is True
    assert validation.errors == ()


def test_link_rows_cover_rehearsal_and_accounting_record_ids() -> None:
    link_set = _load_links()
    link = link_set["paperlive_accounting_links"][0]
    packet_record = _load_json(Path(REHEARSAL_PACKET_PATH))["paperlive_rehearsal_records"][0]
    replay_record = _load_json(Path(OBSERVATION_REPLAY_PATH))["observation_replay_records"][0]
    reconciliation = _load_json(Path(PAPERLIVE_RECONCILIATION_PATH))
    reconciliation_row = reconciliation["paperlive_reconciliation_rows"][0]

    assert link_set["link_fields"] == list(EXPECTED_LINK_FIELDS)
    assert tuple(link.keys()) == tuple(sorted(EXPECTED_LINK_FIELDS))
    assert link["operator_review_status"] == OPERATOR_REVIEW_STATUS
    assert link["link_state"] == "descriptive_rehearsal_paperlive_accounting_link"
    assert link["rehearsal_artifact_ids"] == list(EXPECTED_REHEARSAL_ARTIFACT_IDS)
    assert link["accounting_artifact_ids"] == list(EXPECTED_ACCOUNTING_ARTIFACT_IDS)
    assert tuple(link["rehearsal_record_ids"].keys()) == EXPECTED_REHEARSAL_RECORD_ID_FIELDS
    assert tuple(link["paperlive_accounting_record_ids"].keys()) == EXPECTED_PAPERLIVE_ACCOUNTING_RECORD_ID_FIELDS
    assert link["rehearsal_record_ids"] == {
        "observation_record_id": packet_record["observation_record_id"],
        "observation_replay_record_id": replay_record["replay_record_id"],
        "packet_record_id": packet_record["packet_record_id"],
    }
    assert link["paperlive_accounting_record_ids"] == {
        "accounting_entry_ids": [],
        "accounting_ledger_id": reconciliation_row["accounting_ledger_id"],
        "paperlive_record_id": reconciliation_row["paperlive_record_id"],
        "reconciliation_id": reconciliation["reconciliation_id"],
        "reconciliation_row_id": reconciliation_row["row_id"],
        "session_review_entry_ids": [],
        "validation_row_ids": [],
    }
    assert link["accounting_entry_count"] == 0
    assert len(link["review_checks"]) == 4
    assert all(check["operator_review_status"] == OPERATOR_REVIEW_STATUS for check in link["review_checks"])


def test_artifacts_reference_existing_local_files_with_matching_digests() -> None:
    link_set = _load_links()
    artifacts = link_set["rehearsal_artifacts"] + link_set["accounting_artifacts"]

    assert tuple(artifact["artifact_id"] for artifact in link_set["rehearsal_artifacts"]) == EXPECTED_REHEARSAL_ARTIFACT_IDS
    assert tuple(artifact["artifact_id"] for artifact in link_set["accounting_artifacts"]) == EXPECTED_ACCOUNTING_ARTIFACT_IDS
    for artifact in artifacts:
        path = Path(artifact["local_reference"])
        data = path.read_bytes()

        assert tuple(artifact.keys()) == (
            "artifact_id",
            "artifact_role",
            "artifact_type",
            "byte_count",
            "content_sha256",
            "contract_version",
            "local_reference",
            "operator_review_status",
            "present",
            "record_collection",
            "record_count",
            "record_ids",
        )
        assert artifact["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert artifact["present"] is True
        assert artifact["record_count"] == len(artifact["record_ids"])
        assert "://" not in artifact["local_reference"]
        assert artifact["local_reference"].startswith(ALLOWED_LOCAL_PREFIXES)
        assert path.exists()
        assert artifact["byte_count"] == len(data)
        assert artifact["content_sha256"] == hashlib.sha256(data).hexdigest()


def test_link_rows_reference_existing_rehearsal_and_accounting_records() -> None:
    link = _load_links()["paperlive_accounting_links"][0]
    packet_ids = _ids(_load_json(Path(REHEARSAL_PACKET_PATH))["paperlive_rehearsal_records"], "packet_record_id")
    replay_ids = _ids(_load_json(Path(OBSERVATION_REPLAY_PATH))["observation_replay_records"], "replay_record_id")
    reconciliation_ids = _ids(_load_json(Path(PAPERLIVE_RECONCILIATION_PATH))["paperlive_reconciliation_rows"], "row_id")
    ledger_ids = _ids(_load_json(Path(PAPER_ACCOUNTING_LEDGER_PATH))["accounting_entries"], "entry_id")
    validation_ids = _ids(_load_json(Path(PAPER_ACCOUNTING_VALIDATION_PATH))["record_validation_rows"], "validation_row_id")
    session_ids = _ids(_load_json(Path(PAPER_ACCOUNTING_SESSION_SUMMARY_PATH))["session_review_rows"], "entry_id")

    assert link["rehearsal_record_ids"]["packet_record_id"] in packet_ids
    assert link["rehearsal_record_ids"]["observation_replay_record_id"] in replay_ids
    assert link["paperlive_accounting_record_ids"]["reconciliation_row_id"] in reconciliation_ids
    assert set(link["paperlive_accounting_record_ids"]["accounting_entry_ids"]) <= ledger_ids
    assert set(link["paperlive_accounting_record_ids"]["validation_row_ids"]) <= validation_ids
    assert set(link["paperlive_accounting_record_ids"]["session_review_entry_ids"]) <= session_ids


def test_link_set_retains_numeric_source_values_in_local_artifacts() -> None:
    link_set = _load_links()
    packet = _load_json(Path(REHEARSAL_PACKET_PATH))
    reconciliation = _load_json(Path(PAPERLIVE_RECONCILIATION_PATH))
    serialized_link_set = json.dumps(link_set, sort_keys=True)

    assert "threshold_value" not in serialized_link_set
    assert "reported_reference_value" not in serialized_link_set
    assert packet["paperlive_rehearsal_records"][0]["value_fields_retained_in_source_artifacts"] == [
        "threshold_value",
        "reported_reference_value",
    ]
    assert reconciliation["paperlive_reconciliation_rows"][0]["paperlive_reference_value"] not in serialized_link_set
    assert link_set["paperlive_accounting_links"][0]["value_policy"] == (
        "record_identifiers_only_values_remain_in_local_artifacts"
    )


def test_summary_counts_and_required_validation_commands_match_content() -> None:
    link_set = _load_links()
    local_references = set(_collect_values_for_key(link_set, "local_reference"))

    assert link_set["required_validation_commands"] == list(REQUIRED_VALIDATION_COMMANDS)
    assert link_set["summary_counts"] == {
        "accounting_artifacts": len(link_set["accounting_artifacts"]),
        "accounting_entry_links": 0,
        "link_fields": len(link_set["link_fields"]),
        "local_references": len(local_references),
        "operator_review_steps": len(link_set["operator_review_steps"]),
        "paperlive_accounting_links": len(link_set["paperlive_accounting_links"]),
        "rehearsal_artifacts": len(link_set["rehearsal_artifacts"]),
        "rehearsal_record_links": len(link_set["paperlive_accounting_links"][0]["rehearsal_record_ids"]),
        "required_validation_commands": len(link_set["required_validation_commands"]),
        "review_checks": len(link_set["paperlive_accounting_links"][0]["review_checks"]),
        "validation_command_records": len(link_set["validation_command_records"]),
        "warnings": len(link_set["warnings"]),
    }


def test_safety_boundaries_are_closed_for_rehearsal_paperlive_accounting_links() -> None:
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
    assert "# PMBOT Rehearsal Paperlive Accounting Links" in report
    assert "Paperlive accounting links: 1" in report
    assert "Accounting entry links: 0" in report
    assert "Not execution approval and not runtime input." in report


def test_cli_writes_local_rehearsal_paperlive_accounting_links(tmp_path: Path) -> None:
    links_path = tmp_path / "rehearsal_paperlive_accounting_links.json"
    report_path = tmp_path / "rehearsal_paperlive_accounting_links.md"

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


def test_validation_rejects_record_drift_and_digest_drift() -> None:
    link_set = _load_links()
    link_set["paperlive_accounting_links"][0]["rehearsal_record_ids"]["packet_record_id"] = "missing.local.record"
    link_set["rehearsal_artifacts"][0]["content_sha256"] = "0" * 64

    validation = validate_rehearsal_paperlive_accounting_links(link_set)

    assert validation.valid is False
    assert any("must exist in crypto_paperlive_rehearsal_packet_fixture" in error for error in validation.errors)
    assert any("content_sha256 must match local bytes" in error for error in validation.errors)


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    link_set = _load_links()

    assert _find_disallowed_terms(link_set) == []


def test_documentation_registers_rehearsal_paperlive_accounting_links_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Link set: `{LINK_SET_ID}`" in document
    assert f"Contract: `{LINKS_CONTRACT_VERSION}`" in document
    assert f"Run mode: `{LINKS_RUN_MODE}`" in document
    assert SAMPLE_LINKS_PATH in document
    assert SAMPLE_OPERATOR_REPORT_PATH in document
    assert REHEARSAL_PACKET_PATH in document
    assert OBSERVATION_REPLAY_PATH in document
    assert PAPERLIVE_RECONCILIATION_PATH in document
    assert PAPER_ACCOUNTING_LEDGER_PATH in document
    assert "No market recommendation, forecast scoring, action guidance, or selection advice." in document
    assert "No probability, EV, edge, or confidence scoring." in document
    assert "This link set is not execution approval and is not runtime input." in document


def _load_links() -> dict:
    return json.loads(LINKS_PATH.read_text(encoding="utf-8"))


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ids(records: list[dict], key: str) -> set[str]:
    return {record[key] for record in records}


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
