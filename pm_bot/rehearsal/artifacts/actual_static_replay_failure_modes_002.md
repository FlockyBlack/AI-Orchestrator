# Actual Static Replay Failure Modes 002

Batch: `actual_static_replay_failure_modes_002`
Base rehearsal: `actual_static_replay_rehearsal_001`
Mode: static replay failure modes.
Live network used: false.
OpenRouter calls performed: 0.
Polymarket API calls performed: 0.
Authenticated endpoints used: false.
Wallet/private-key access: false.
Order or trading actions: false.
Runtime or dispatcher changes: false.

All failure modes behaved as expected: true.
Passed scenarios: 7.
Failed scenarios: 0.

## contradiction_detected

Expected behavior: two required evidence records disagree on a required static fact; replay detects and blocks
Observed behavior: scenario failed safely with contradiction_check_status=blocked, stop_condition_status=blocked
Pass/fail: pass

Blockers:
- contradiction:actual_static_replay_rehearsal_001.contradiction.subject_and_value_match
- stop_condition:rehearsal_source_contradiction_detected

Warnings:
- none

Safety notes:
- Contradictory required evidence is not resolved by inference.
- The result remains descriptive and pending operator review.

## forbidden_action_leakage_guard

Expected behavior: action-like noisy input is sanitized and blocked without being echoed as instruction text
Observed behavior: scenario failed safely with input_safety_status=blocked
Pass/fail: pass

Blockers:
- safety:forbidden_action_text_sanitized

Warnings:
- safety_sanitized_forbidden_action_text

Safety notes:
- The unsafe fixture text is not copied into result blockers, warnings, or summaries.
- No action instruction is produced by the replay result.

## malformed_market_packet

Expected behavior: market packet contract version is invalid; replay rejects the input as malformed
Observed behavior: scenario failed safely with market_packet_status=failed
Pass/fail: pass

Blockers:
- market_packet:market_packet.contract_version must be pmbot_actual_read_only_rehearsal_market_packet.v1

Warnings:
- none

Safety notes:
- Malformed local packets fail closed without falling back to live data.
- The failure does not open runtime, dispatcher, wallet, or order paths.

## missing_evidence

Expected behavior: source evidence lacks a required local record; replay hard-blocks before review
Observed behavior: scenario failed safely with source_evidence_status=failed, stop_condition_status=blocked
Pass/fail: pass

Blockers:
- source_evidence:missing_required_evidence_ids:evidence_station_static_log
- stop_condition:rehearsal_source_evidence_mismatch

Warnings:
- none

Safety notes:
- No live fetch was attempted to replace missing local evidence.
- Operator review remains required and no execution surface is opened.

## sensitive_path_leakage_guard

Expected behavior: fake sensitive-looking local strings are sanitized and blocked without credential use
Observed behavior: scenario failed safely with input_safety_status=blocked
Pass/fail: pass

Blockers:
- safety:sensitive_text_sanitized

Warnings:
- safety_sanitized_sensitive_text

Safety notes:
- The fake sensitive-looking string is treated as inert input text only.
- Only safe fixture references are checked for existence.

## stale_evidence

Expected behavior: stale local evidence exceeds the fixed freshness window; replay hard-blocks
Observed behavior: scenario failed safely with staleness_check_status=blocked, stop_condition_status=blocked
Pass/fail: pass

Blockers:
- staleness:actual_static_replay_rehearsal_001.staleness.official_report_current
- stop_condition:rehearsal_stale_source_evidence

Warnings:
- none

Safety notes:
- Staleness is treated as safety-sensitive in this static rehearsal.
- No network refresh is attempted inside the replay runner.

## stop_condition_triggered

Expected behavior: the local stop matrix intentionally trips a hard stop even with otherwise valid inputs
Observed behavior: scenario failed safely with stop_condition_status=blocked
Pass/fail: pass

Blockers:
- stop_condition:rehearsal_forced_matrix_block

Warnings:
- none

Safety notes:
- Stop conditions are honored as hard blockers in static replay.
- No operator approval is granted by the replay result.

## Still Blocked

- live network access
- OpenRouter calls
- Polymarket API calls
- authenticated endpoint use
- wallet or private-key access
- order or trading action paths
- runtime or dispatcher changes
- autonomous trading readiness claims

This artifact is local-only, deterministic, and pending operator review.
