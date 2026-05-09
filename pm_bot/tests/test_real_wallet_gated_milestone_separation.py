from __future__ import annotations

import json
from pathlib import Path


DOC_PATH = Path("pm_bot/readiness/PMBOT_ROADMAP_004_REAL_WALLET_GATED_MILESTONE_SEPARATION_LOCAL_ONLY.md")
FIXTURE_PATH = Path("pm_bot/tests/fixtures/readiness/pmbot_real_wallet_gated_milestone_separation.valid.json")
TASK_ID = "PMBOT-ROADMAP-004-REAL-WALLET-GATED-MILESTONE-SEPARATION-LOCAL-ONLY"
CONTRACT_VERSION = "pmbot_real_wallet_gated_milestone_separation.v1"
RUN_MODE = "local_static_real_wallet_gated_milestone_separation"
MILESTONE_SET_ID = "pmbot-real-wallet-gated-milestone-separation-001"
MILESTONE_NAME = "pmbot-real-wallet-gated-milestone-separation"
OPERATOR_REVIEW_STATUS = "pending_operator_review"

EXPECTED_ALLOWED_PREFIXES = (
    "docs/",
    "pm_bot/readiness/",
    "pm_bot/tests/",
    "tests/",
)
EXPECTED_EXCLUDED_PREFIXES = (
    ".env",
    ".env.*",
    ".git/",
    ".codex/",
    "runtime/",
    "dispatcher/",
    "run_codex/",
    "pm_bot/llm/",
    "pm_bot/wallet/",
    "pm_bot/trading/",
    "pm_bot/orders/",
    "agent_tasks/running/",
)
EXPECTED_GATE_IDS = (
    "paper_mode_baseline_milestone",
    "supervised_review_boundary_milestone",
    "sensitive_scope_record_milestone",
    "credential_wallet_boundary_milestone",
    "runtime_wiring_boundary_milestone",
    "validation_replay_milestone",
)
EXPECTED_RULE_IDS = (
    "separation_rule_001",
    "separation_rule_002",
    "separation_rule_003",
    "separation_rule_004",
    "separation_rule_005",
    "separation_rule_006",
)
EXPECTED_SOURCE_ARTIFACT_IDS = (
    "real_wallet_blocker_matrix",
    "local_to_supervised_live_gap_matrix",
    "operator_approval_gate_record",
    "readiness_evidence_bundle",
    "sensitive_path_exclusion_audit",
    "queue_template_contract",
)
EXPECTED_SAFETY_BOUNDARIES = {
    "artifact_status_change_allowed": False,
    "authenticated_endpoint_calls_allowed": False,
    "automated_restart_allowed": False,
    "background_process_allowed": False,
    "browser_automation_allowed": False,
    "core_execution_wiring_changes_allowed": False,
    "credential_or_secret_access_allowed": False,
    "execution_endpoint_calls_allowed": False,
    "external_service_calls_allowed": False,
    "llm_provider_calls_allowed": False,
    "local_static_samples_only": True,
    "market_api_calls_allowed": False,
    "market_ranking_allowed": False,
    "network_calls_allowed": False,
    "numeric_prediction_metric_allowed": False,
    "operator_review_required": True,
    "order_or_trade_surface_changes_allowed": False,
    "paper_mode_only": True,
    "production_dependency_changes_allowed": False,
    "real_wallet_transition_allowed": False,
    "runtime_or_dispatcher_changes_allowed": False,
    "scheduler_or_worker_allowed": False,
    "sensitive_access_scope_expansion_allowed": False,
    "supervised_live_transition_allowed": False,
    "timed_automation_allowed": False,
    "trade_instruction_allowed": False,
    "transaction_endpoint_calls_allowed": False,
    "wallet_or_signing_material_access_allowed": False,
}


def test_static_gated_milestone_separation_fixture_has_expected_contract() -> None:
    record = _load_record()

    assert tuple(record.keys()) == tuple(sorted(record.keys()))
    assert record["task_id"] == TASK_ID
    assert record["milestone_set_id"] == MILESTONE_SET_ID
    assert record["milestone_name"] == MILESTONE_NAME
    assert record["contract_version"] == CONTRACT_VERSION
    assert record["run_mode"] == RUN_MODE
    assert record["created_at"] == "2026-05-09T00:00:00Z"
    assert record["local_only"] is True
    assert record["operator_review_required"] is True
    assert record["operator_review"] == {
        "reviewed_at": None,
        "reviewed_by": None,
        "status": OPERATOR_REVIEW_STATUS,
    }
    assert record["errors"] == []
    assert record["warnings"] == []


def test_allowed_and_excluded_prefixes_match_sensitive_access_scope() -> None:
    record = _load_record()

    assert tuple(record["allowed_path_prefixes"]) == EXPECTED_ALLOWED_PREFIXES
    assert tuple(record["excluded_path_prefixes"]) == EXPECTED_EXCLUDED_PREFIXES
    for prefix in record["excluded_path_prefixes"]:
        assert not prefix.startswith(EXPECTED_ALLOWED_PREFIXES)


def test_milestone_rows_are_fixed_local_pending_and_not_approved() -> None:
    record = _load_record()

    assert tuple(row["gate_id"] for row in record["milestone_rows"]) == EXPECTED_GATE_IDS
    for row in record["milestone_rows"]:
        assert tuple(row.keys()) == tuple(sorted(row.keys()))
        assert set(row) == {
            "approval_state",
            "gate_id",
            "human_record_required",
            "local_reference",
            "milestone_group",
            "operator_review_status",
            "separated_from",
            "transition_state",
        }
        assert row["approval_state"] == "not_approved"
        assert row["operator_review_status"] == OPERATOR_REVIEW_STATUS
        assert row["transition_state"] == "blocked_until_separate_operator_record"
        _assert_allowed_existing_local_reference(row["local_reference"])


def test_separation_rules_keep_milestones_independent_and_review_gated() -> None:
    record = _load_record()

    milestone_groups = {row["milestone_group"] for row in record["milestone_rows"]}
    assert tuple(rule["rule_id"] for rule in record["separation_rules"]) == EXPECTED_RULE_IDS
    for rule in record["separation_rules"]:
        assert tuple(rule.keys()) == tuple(sorted(rule.keys()))
        assert set(rule) == {
            "blocked_transition",
            "from_milestone_group",
            "required_human_record",
            "rule_id",
            "rule_state",
        }
        assert rule["from_milestone_group"] in milestone_groups
        assert rule["rule_state"] == "closed_pending_operator_review"
        assert rule["required_human_record"].startswith("Separate operator record")


def test_source_artifacts_reference_only_local_review_material() -> None:
    record = _load_record()

    assert tuple(artifact["artifact_id"] for artifact in record["source_artifacts"]) == EXPECTED_SOURCE_ARTIFACT_IDS
    for artifact in record["source_artifacts"]:
        assert tuple(artifact.keys()) == tuple(sorted(artifact.keys()))
        assert set(artifact) == {
            "artifact_id",
            "contract_version",
            "local_reference",
            "required_state",
        }
        assert artifact["required_state"] == OPERATOR_REVIEW_STATUS
        _assert_allowed_existing_local_reference(artifact["local_reference"])


def test_safety_boundaries_are_closed_for_gated_milestone_separation() -> None:
    record = _load_record()

    assert record["safety_boundaries"] == EXPECTED_SAFETY_BOUNDARIES
    assert record["safety_boundaries"]["local_static_samples_only"] is True
    assert record["safety_boundaries"]["operator_review_required"] is True
    assert record["safety_boundaries"]["paper_mode_only"] is True
    assert all(value is False for key, value in record["safety_boundaries"].items() if key.endswith("_allowed"))


def test_validation_commands_are_recorded_for_operator_run_local_checks() -> None:
    record = _load_record()

    assert record["required_validation_commands"] == [
        "python -m compileall pm_bot tests",
        "pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py",
    ]


def test_summary_counts_match_gated_milestone_separation_content() -> None:
    record = _load_record()
    local_references = {
        *(row["local_reference"] for row in record["milestone_rows"]),
        *(artifact["local_reference"] for artifact in record["source_artifacts"]),
    }

    assert record["summary_counts"] == {
        "allowed_path_prefixes": len(record["allowed_path_prefixes"]),
        "excluded_path_prefixes": len(record["excluded_path_prefixes"]),
        "local_references": len(local_references),
        "milestone_rows": len(record["milestone_rows"]),
        "milestone_rows_pending_operator_review": sum(
            1 for row in record["milestone_rows"] if row["operator_review_status"] == OPERATOR_REVIEW_STATUS
        ),
        "required_validation_commands": len(record["required_validation_commands"]),
        "separation_rules": len(record["separation_rules"]),
        "source_artifacts": len(record["source_artifacts"]),
        "warnings": len(record["warnings"]),
    }


def test_fixture_has_no_decision_scoring_or_selection_terms() -> None:
    record = _load_record()

    assert _find_disallowed_terms(record) == []


def test_documentation_registers_gated_milestone_fixture_and_safety_boundary() -> None:
    document = DOC_PATH.read_text(encoding="utf-8")

    assert f"Task: `{TASK_ID}`" in document
    assert f"Milestone set: `{MILESTONE_SET_ID}`" in document
    assert f"Contract: `{CONTRACT_VERSION}`" in document
    assert f"Run mode: `{RUN_MODE}`" in document
    assert str(FIXTURE_PATH).replace("\\", "/") in document
    assert "No forecast scoring, action guidance, market ranking, numeric prediction metric" in document
    assert "This record is not execution approval and is not runtime input." in document


def _load_record() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _assert_allowed_existing_local_reference(local_reference: str) -> None:
    assert "://" not in local_reference
    assert local_reference.startswith(EXPECTED_ALLOWED_PREFIXES)
    assert Path(local_reference).exists()


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
            if key in {"excluded_path_prefixes", "local_reference"}:
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
