# PMBOT Warning Hygiene Owner Action Paths v1

task_id: PMBOT-QUALITY-002-WARNING-HYGIENE-OWNER-ACTION-PATHS
schema_version: warning_hygiene_owner_action_paths.v1
source_report: pm_bot/quality/artifact_health_report.v1.json
total_warnings_processed: 8

## Warning Policy

- Warnings are not hidden.
- Warnings are not suppressed.
- Warnings are not downgraded silently.
- Blocking warnings are not relabeled unless source evidence proves they are not blocking.

## Operator Summary

- local_mvp_blocked: false
- non_deferrable_warning_count: 4
- safety_relevant_warning_count: 7
- what_should_not_block_local_mvp_usage: The current source report has no blocking warnings, so these hygiene warnings should not block local MVP usage.
- safe_to_defer: Deferrable warnings may be postponed for local MVP use when blocking_count is zero; non-deferrable warnings remain visible as owner action queues.

## Summary Counts

- severity: {"action_required": 3, "blocking": 0, "informational": 1, "review_needed": 4}
- owner: {"docs": 2, "infra": 1, "operator": 2, "paper": 1, "product": 2}
- category: {"known_intentional_malformed_fixture_parse_failure": 1, "schema_version_missing": 4, "stale_reference_warning": 3}
- expected_status: {"current": 0, "expected_gap": 5, "legacy": 0, "needs_cleanup": 0, "needs_review": 0, "stale": 3}
- action_type: {"add_missing_metadata": 4, "archive_or_mark_legacy": 3, "document_exception": 1}
- safety_relevance: {"boundary_related": 0, "data_integrity_related": 0, "execution_related": 0, "none": 1, "operator_usability_related": 7}
- deferrable: {"false": 4, "true": 4}

## Top Warning Groups

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
- schema_version_missing | owner=operator | severity=action_required | count=1 | action=add_missing_metadata | status=expected_gap | deferrable=false
  operator_action: Route to the artifact owner; local MVP usage can continue if no blocking warnings exist.
  maintainer_action: Add schema_version metadata or document why this artifact predates the convention.
  example_path: docs/PMBOT_OPERATOR_002_RESULT.json
- stale_reference_warning | owner=operator | severity=review_needed | count=1 | action=archive_or_mark_legacy | status=stale | deferrable=true
  operator_action: Defer if the referenced artifact is not part of the current MVP path.
  maintainer_action: Archive, mark legacy, or update stale references.
  example_path: docs/PMBOT_OPERATOR_002_RESULT.json
- known_intentional_malformed_fixture_parse_failure | owner=paper | severity=informational | count=1 | action=document_exception | status=expected_gap | deferrable=true
  operator_action: No operator action is expected unless the fixture stops being intentional.
  maintainer_action: Keep the intentional malformed fixture documented in tests.
  example_path: pm_bot/paper/manual_snapshot_import_source/005_malformed.json
- schema_version_missing | owner=product | severity=action_required | count=1 | action=add_missing_metadata | status=expected_gap | deferrable=false
  operator_action: Route to the artifact owner; local MVP usage can continue if no blocking warnings exist.
  maintainer_action: Add schema_version metadata or document why this artifact predates the convention.
  example_path: docs/PMBOT_PRODUCT_001_RESULT.json
- stale_reference_warning | owner=product | severity=review_needed | count=1 | action=archive_or_mark_legacy | status=stale | deferrable=true
  operator_action: Defer if the referenced artifact is not part of the current MVP path.
  maintainer_action: Archive, mark legacy, or update stale references.
  example_path: docs/PMBOT_PRODUCT_001_RESULT.json

## Owner Action Queue

- owner=docs action=add_missing_metadata count=1
- owner=docs action=archive_or_mark_legacy count=1
- owner=infra action=add_missing_metadata count=1
- owner=operator action=add_missing_metadata count=1
- owner=operator action=archive_or_mark_legacy count=1

## Cleanup Soon

- schema_version_missing owned_by=docs count=1 maintainer_action=Add schema_version metadata or document why this artifact predates the convention.
- schema_version_missing owned_by=infra count=1 maintainer_action=Add schema_version metadata or document why this artifact predates the convention.
- schema_version_missing owned_by=operator count=1 maintainer_action=Add schema_version metadata or document why this artifact predates the convention.
- known_intentional_malformed_fixture_parse_failure owned_by=paper count=1 maintainer_action=Keep the intentional malformed fixture documented in tests.
- schema_version_missing owned_by=product count=1 maintainer_action=Add schema_version metadata or document why this artifact predates the convention.
