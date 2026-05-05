# PMBOT Warning Hygiene Owner Action Paths v1

task_id: PMBOT-QUALITY-002-WARNING-HYGIENE-OWNER-ACTION-PATHS
schema_version: warning_hygiene_owner_action_paths.v1
source_report: pm_bot/quality/artifact_health_report.v1.json
total_warnings_processed: 59

## Warning Policy

- Warnings are not hidden.
- Warnings are not suppressed.
- Warnings are not downgraded silently.
- Blocking warnings are not relabeled unless source evidence proves they are not blocking.

## Operator Summary

- local_mvp_blocked: false
- non_deferrable_warning_count: 22
- safety_relevant_warning_count: 58
- what_should_not_block_local_mvp_usage: The current source report has no blocking warnings, so these hygiene warnings should not block local MVP usage.
- safe_to_defer: Deferrable warnings may be postponed for local MVP use when blocking_count is zero; non-deferrable warnings remain visible as owner action queues.

## Summary Counts

- severity: {"action_required": 21, "blocking": 0, "informational": 1, "review_needed": 37}
- owner: {"dashboard": 9, "docs": 2, "infra": 1, "operator": 2, "paper": 43, "product": 2}
- category: {"embedded_artifact_pointer_warning": 26, "json_top_level_not_object": 4, "known_intentional_malformed_fixture_parse_failure": 1, "schema_version_missing": 19, "stale_reference_warning": 6, "task_id_missing": 3}
- expected_status: {"current": 0, "expected_gap": 23, "legacy": 0, "needs_cleanup": 0, "needs_review": 4, "stale": 32}
- action_type: {"add_missing_metadata": 22, "archive_or_mark_legacy": 6, "document_exception": 5, "normalize_legacy_artifact": 26}
- safety_relevance: {"boundary_related": 0, "data_integrity_related": 4, "execution_related": 0, "none": 1, "operator_usability_related": 54}
- deferrable: {"false": 22, "true": 37}

## Top Warning Groups

- embedded_artifact_pointer_warning | owner=paper | severity=review_needed | count=23 | action=normalize_legacy_artifact | status=stale | deferrable=true
  operator_action: Defer for MVP use unless it repeats in a current decision path.
  maintainer_action: Remove stale embedded artifact pointers or update them to current paths.
  example_path: pm_bot/paper/expected_local_snapshot_inbox_paper_portfolio.v1.json
- schema_version_missing | owner=paper | severity=action_required | count=12 | action=add_missing_metadata | status=expected_gap | deferrable=false
  operator_action: Route to the artifact owner; local MVP usage can continue if no blocking warnings exist.
  maintainer_action: Add schema_version metadata or document why this artifact predates the convention.
  example_path: docs/PMBOT_PAPER_018_RESULT.json
- json_top_level_not_object | owner=paper | severity=review_needed | count=4 | action=document_exception | status=needs_review | deferrable=true
  operator_action: Inspect only if this artifact is needed for the current operator review.
  maintainer_action: Document the non-object JSON shape or normalize the artifact.
  example_path: pm_bot/paper/expected_manual_paper_workspace_quarantine.v1.json
- embedded_artifact_pointer_warning | owner=dashboard | severity=review_needed | count=3 | action=normalize_legacy_artifact | status=stale | deferrable=true
  operator_action: Defer for MVP use unless it repeats in a current decision path.
  maintainer_action: Remove stale embedded artifact pointers or update them to current paths.
  example_path: pm_bot/dashboard/expected_portfolio_audit_state_preview.v1.json
- schema_version_missing | owner=dashboard | severity=action_required | count=3 | action=add_missing_metadata | status=expected_gap | deferrable=false
  operator_action: Route to the artifact owner; local MVP usage can continue if no blocking warnings exist.
  maintainer_action: Add schema_version metadata or document why this artifact predates the convention.
  example_path: docs/PMBOT_DASHBOARD_002_RESULT.json
- stale_reference_warning | owner=dashboard | severity=review_needed | count=3 | action=archive_or_mark_legacy | status=stale | deferrable=true
  operator_action: Defer if the referenced artifact is not part of the current MVP path.
  maintainer_action: Archive, mark legacy, or update stale references.
  example_path: docs/PMBOT_DASHBOARD_002_RESULT.json
- task_id_missing | owner=paper | severity=action_required | count=3 | action=add_missing_metadata | status=expected_gap | deferrable=false
  operator_action: Route to the artifact owner for metadata cleanup.
  maintainer_action: Add task_id metadata or document the legacy exception.
  example_path: pm_bot/paper/crypto_numeric_execution_fixture.v1.json
- schema_version_missing | owner=docs | severity=action_required | count=1 | action=add_missing_metadata | status=expected_gap | deferrable=false
  operator_action: Route to the artifact owner; local MVP usage can continue if no blocking warnings exist.
  maintainer_action: Add schema_version metadata or document why this artifact predates the convention.
  example_path: docs/PMBOT_INTEGRATION_008_RESULT.json
- stale_reference_warning | owner=docs | severity=review_needed | count=1 | action=archive_or_mark_legacy | status=stale | deferrable=true
  operator_action: Defer if the referenced artifact is not part of the current MVP path.
  maintainer_action: Archive, mark legacy, or update stale references.
  example_path: docs/PMBOT_INTEGRATION_008_RESULT.json
- schema_version_missing | owner=infra | severity=review_needed | count=1 | action=add_missing_metadata | status=expected_gap | deferrable=false
  operator_action: Route to the artifact owner; local MVP usage can continue if no blocking warnings exist.
  maintainer_action: Add schema_version metadata or document why this artifact predates the convention.
  example_path: docs/PMBOT_INFRA_009_RESULT.json

## Owner Action Queue

- owner=paper action=normalize_legacy_artifact count=23
- owner=paper action=add_missing_metadata count=15
- owner=paper action=document_exception count=5
- owner=dashboard action=add_missing_metadata count=3
- owner=dashboard action=archive_or_mark_legacy count=3

## Cleanup Soon

- schema_version_missing owned_by=paper count=12 maintainer_action=Add schema_version metadata or document why this artifact predates the convention.
- json_top_level_not_object owned_by=paper count=4 maintainer_action=Document the non-object JSON shape or normalize the artifact.
- schema_version_missing owned_by=dashboard count=3 maintainer_action=Add schema_version metadata or document why this artifact predates the convention.
- task_id_missing owned_by=paper count=3 maintainer_action=Add task_id metadata or document the legacy exception.
- schema_version_missing owned_by=docs count=1 maintainer_action=Add schema_version metadata or document why this artifact predates the convention.
