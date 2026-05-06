# PMBOT Warning Hygiene Owner Action Paths v1

task_id: PMBOT-QUALITY-002-WARNING-HYGIENE-OWNER-ACTION-PATHS
schema_version: warning_hygiene_owner_action_paths.v1
source_report: pm_bot/quality/artifact_health_report.v1.json
total_warnings_processed: 0
documented_exceptions: 48

## Warning Policy

- Warnings are not hidden.
- Warnings are not suppressed.
- Warnings are not downgraded silently.
- Blocking warnings are not relabeled unless source evidence proves they are not blocking.

## Operator Summary

- local_mvp_blocked: false
- non_deferrable_warning_count: 0
- safety_relevant_warning_count: 0
- what_should_not_block_local_mvp_usage: The current source report has no blocking warnings, so these hygiene warnings should not block local MVP usage.
- safe_to_defer: Deferrable warnings may be postponed for local MVP use when blocking_count is zero; non-deferrable warnings remain visible as owner action queues.

## Summary Counts

- severity: {"action_required": 0, "blocking": 0, "informational": 0, "review_needed": 0}
- owner: {}
- category: {}
- expected_status: {"current": 0, "expected_gap": 0, "legacy": 0, "needs_cleanup": 0, "needs_review": 0, "stale": 0}
- action_type: {}
- safety_relevance: {"boundary_related": 0, "data_integrity_related": 0, "execution_related": 0, "none": 0, "operator_usability_related": 0}
- deferrable: {"false": 0, "true": 0}

## Top Warning Groups

- none

## Owner Action Queue

- none

## Cleanup Soon

- none
