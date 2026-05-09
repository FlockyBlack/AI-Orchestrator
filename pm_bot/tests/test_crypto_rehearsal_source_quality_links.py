from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from pm_bot.source_quality.crypto_rehearsal_source_quality_links import (
    EXPECTED_LINK_FIELDS,
    EXPECTED_SAFETY_BOUNDARIES,
    LINK_SET_ID,
    LINKS_CONTRACT_VERSION,
    LINKS_RUN_MODE,
    OPERATOR_REVIEW_STATUS,
    REQUIRED_VALIDATION_COMMANDS,
    SAMPLE_LINKS_PATH,
    SAMPLE_OPERATOR_REPORT_PATH,
    SOURCE_CONTRADICTION_LEDGER_PATH,
    SOURCE_EVIDENCE_LINK_MAP_PATH,
    SOURCE_QUALITY_CAPTURE_SURFACE_PATH,
    SOURCE_STALENESS_CHECK_SPEC_PATH,
    TASK_ID,
    build_crypto_rehearsal_source_quality_links,
    build_operator_report,
    load_crypto_rehearsal_link_inputs,
    load_crypto_rehearsal_source_quality_links,
    main,
    validate_crypto_rehearsal_source_quality_links,
)

DOC_PATH = Path("docs/PMBOT_CRYPTO_LIVE_019_CRYPTO_REHEARSAL_TO_SOURCE_QUALITY_LINKS_LOCAL_ONLY.md")
REHEARSAL_PACKET_PATH = Path("pm_bot/tests/fixtures/crypto_live/pmbot_crypto_paperlive_rehearsal_packet.valid.json")
MARKET_CAPTURE_PATH = Path(
    "pm_bot/tests/fixtures/crypto_market_class_capture/crypto_market_class_capture_template.valid.json"
)
SNAPSHOT_PATH = Path("pm_bot/tests/fixtures/crypto_paperlive_observation_ledger/static_crypto_reference_snapshot.valid.json")
LINKS_PATH = Path(SAMPLE_LINKS_PATH)
REPORT_PATH = Path(SAMPLE_OPERATOR_REPORT_PATH)

EXPECTED_SOURCE_IDS = (
    "crypto_market_class_capture_template",
    "crypto_operator_review_protocol",
    "crypto_paperlive_observation_ledger",
    "static_crypto_reference_snapshot_2026_05_09_btc",
)
EXPECTED_REHEARSAL_SOURCE_FIELDS = (
    "source_capture_record_id",
    "source_review_record_id",
    "observation_record_id",
    "local_snapshot_reference",
)
EXPECTED_ARTIFACT_IDS = (
    "crypto_source_quality_capture_surface_sample",
    "crypto_source_evidence_link_map_sample",
    "crypto_source_staleness_check_spec_sample",
    "crypto_source_contradiction_ledger_sample",
)
ALLOWED_LOCAL_PREFIXES = ("docs/", "pm_bot/source_quality/samples/", "pm_bot/tests/fixtures/")


def test_static_crypto_rehearsal_source_quality_links_has_expected_contract() -> None:
    link_set = _load_links()

    assert tuple(link_set.keys()) == tuple(sorted(link_set.keys()))
    assert link_set["task_id"] == TASK_ID
    assert link_set["link_set_id"] == LINK_SET_ID
    assert link_set["build_id"] == "pmbot-crypto-rehearsal-source-quality-links-001-c47d1d7b9791"
    assert link_set["contract_version"] == LINKS_CONTRACT_VERSION
    assert link_set["run_mode"] == LINKS_RUN_MODE
    assert link_set["created_at"] == "2026-05-09T07:30:00Z"
    assert link_set["local_only"] is True
    assert link_set["operator_review_required"] is True
    assert link_set["operator_review"]["status"] == OPERATOR_REVIEW_STATUS
    assert link_set["errors"] == []
    assert link_set["warnings"] == []


def test_builder_output_matches_static_sample_and_is_deterministic() -> None:
    inputs = load_crypto_rehearsal_link_inputs()

    first = build_crypto_rehearsal_source_quality_links(inputs)
    second = build_crypto_rehearsal_source_quality_links(deepcopy(inputs))

    assert first == second
    assert first == _load_links()


def test_static_sample_validates_as_rehearsal_source_quality_links() -> None:
    link_set = load_crypto_rehearsal_source_quality_links(LINKS_PATH)

    validation = validate_crypto_rehearsal_source_quality_links(link_set)

    assert validation.valid is True
    assert validation.errors == ()


def test_rehearsal_links_cover_packet_source_fields_and_source_quality_records() -> None:
    link_set = _load_links()
    packet = _load_json(REHEARSAL_PACKET_PATH)
    rehearsal_record = packet["paperlive_rehearsal_records"][0]
    links = link_set["rehearsal_source_quality_links"]

    assert tuple(link["source_id"] for link in links) == EXPECTED_SOURCE_IDS
    assert tuple(link["rehearsal_source_field"] for link in links) == EXPECTED_REHEARSAL_SOURCE_FIELDS
    assert tuple(link_set["link_fields"]) == EXPECTED_LINK_FIELDS

    for link in links:
        assert tuple(link.keys()) == EXPECTED_LINK_FIELDS
        assert link["packet_record_id"] == rehearsal_record["packet_record_id"]
        assert link["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert link["link_state"] == "descriptive_rehearsal_source_quality_link"
        assert link["source_quality_artifact_ids"] == list(EXPECTED_ARTIFACT_IDS)
        assert len(link["review_checks"]) == 4
        assert all(check["operator_review_status"] == OPERATOR_REVIEW_STATUS for check in link["review_checks"])

    assert links[0]["rehearsal_source_record_id"] == rehearsal_record["source_capture_record_id"]
    assert links[1]["rehearsal_source_record_id"] == rehearsal_record["source_review_record_id"]
    assert links[2]["rehearsal_source_record_id"] == rehearsal_record["observation_record_id"]
    assert links[3]["rehearsal_source_record_id"] == "static_crypto_reference_snapshot_2026_05_09_btc"


def test_source_quality_artifacts_reference_existing_local_files_with_matching_digests() -> None:
    link_set = _load_links()

    assert tuple(artifact["artifact_id"] for artifact in link_set["source_quality_artifacts"]) == EXPECTED_ARTIFACT_IDS
    for artifact in link_set["source_quality_artifacts"]:
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


def test_link_rows_reference_existing_source_quality_record_ids() -> None:
    link_set = _load_links()
    capture_ids = _record_ids(_load_json(Path(SOURCE_QUALITY_CAPTURE_SURFACE_PATH))["quality_capture_records"])
    evidence_ids = _record_ids(_load_json(Path(SOURCE_EVIDENCE_LINK_MAP_PATH))["source_evidence_links"])
    staleness_ids = _record_ids(_load_json(Path(SOURCE_STALENESS_CHECK_SPEC_PATH))["source_staleness_checks"])
    contradiction_ids = _record_ids(_load_json(Path(SOURCE_CONTRADICTION_LEDGER_PATH))["source_contradiction_rows"])

    for link in link_set["rehearsal_source_quality_links"]:
        record_ids = link["source_quality_record_ids"]
        assert record_ids["quality_capture_record_id"] in capture_ids
        assert record_ids["source_evidence_link_id"] in evidence_ids
        assert record_ids["source_staleness_check_id"] in staleness_ids
        assert set(record_ids["source_contradiction_row_ids"]) <= contradiction_ids


def test_link_set_retains_numeric_source_values_in_local_source_artifacts() -> None:
    link_set = _load_links()
    capture = _load_json(MARKET_CAPTURE_PATH)
    snapshot = _load_json(SNAPSHOT_PATH)
    serialized_link_set = json.dumps(link_set, sort_keys=True)

    assert capture["sample_records"][0]["threshold_value"] not in serialized_link_set
    assert snapshot["reported_reference_value"] not in serialized_link_set
    assert all(
        link["value_policy"] == "record_identifiers_only_source_values_remain_in_local_artifacts"
        for link in link_set["rehearsal_source_quality_links"]
    )


def test_summary_counts_and_required_validation_commands_match_content() -> None:
    link_set = _load_links()
    local_references = set(
        _collect_values_for_key(link_set, "local_reference")
        + _collect_values_for_key(link_set, "rehearsal_packet_reference")
    )

    assert link_set["required_validation_commands"] == list(REQUIRED_VALIDATION_COMMANDS)
    assert link_set["summary_counts"] == {
        "link_fields": len(link_set["link_fields"]),
        "local_references": len(local_references),
        "operator_review_steps": len(link_set["operator_review_steps"]),
        "packet_records": link_set["rehearsal_packet"]["paperlive_rehearsal_records"],
        "required_validation_commands": len(link_set["required_validation_commands"]),
        "review_checks": sum(len(link["review_checks"]) for link in link_set["rehearsal_source_quality_links"]),
        "rehearsal_source_quality_links": len(link_set["rehearsal_source_quality_links"]),
        "source_quality_artifacts": len(link_set["source_quality_artifacts"]),
        "source_quality_record_links": sum(
            3 + len(link["source_quality_record_ids"]["source_contradiction_row_ids"])
            for link in link_set["rehearsal_source_quality_links"]
        ),
        "warnings": len(link_set["warnings"]),
    }


def test_safety_boundaries_are_closed_for_rehearsal_source_quality_links() -> None:
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
    assert "# PMBOT Crypto Rehearsal To Source Quality Links" in report
    assert "Rehearsal source links: 4" in report
    assert "Source quality record links: 19" in report
    assert "Not execution approval and not runtime input." in report


def test_cli_writes_local_rehearsal_source_quality_links(tmp_path: Path) -> None:
    links_path = tmp_path / "crypto_rehearsal_source_quality_links.json"
    report_path = tmp_path / "crypto_rehearsal_source_quality_links.md"

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
    link_set["rehearsal_source_quality_links"][0]["source_quality_record_ids"]["source_evidence_link_id"] = (
        "missing.local.record"
    )
    link_set["source_quality_artifacts"][0]["content_sha256"] = "0" * 64

    validation = validate_crypto_rehearsal_source_quality_links(link_set)

    assert validation.valid is False
    assert any("must exist in crypto_source_evidence_link_map_sample" in error for error in validation.errors)
    assert any("content_sha256 must match local bytes" in error for error in validation.errors)


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    link_set = _load_links()

    assert _find_disallowed_terms(link_set) == []


def test_documentation_registers_rehearsal_source_quality_links_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Link set: `{LINK_SET_ID}`" in document
    assert f"Contract: `{LINKS_CONTRACT_VERSION}`" in document
    assert f"Run mode: `{LINKS_RUN_MODE}`" in document
    assert SAMPLE_LINKS_PATH in document
    assert SAMPLE_OPERATOR_REPORT_PATH in document
    assert SOURCE_QUALITY_CAPTURE_SURFACE_PATH in document
    assert SOURCE_EVIDENCE_LINK_MAP_PATH in document
    assert SOURCE_STALENESS_CHECK_SPEC_PATH in document
    assert SOURCE_CONTRADICTION_LEDGER_PATH in document
    assert "No forecast scoring, action guidance, market ranking" in document
    assert "This link set is not execution approval and is not runtime input." in document


def _load_links() -> dict:
    return json.loads(LINKS_PATH.read_text(encoding="utf-8"))


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _record_ids(records: list[dict]) -> set[str]:
    ids: set[str] = set()
    for record in records:
        for field in ("record_id", "row_id", "link_id", "check_id"):
            value = record.get(field)
            if isinstance(value, str) and value:
                ids.add(value)
                break
    return ids


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
            if key in {"local_reference", "rehearsal_packet_reference"}:
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
