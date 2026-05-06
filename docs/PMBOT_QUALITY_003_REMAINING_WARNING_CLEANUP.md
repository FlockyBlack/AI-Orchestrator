# PMBOT-QUALITY-003 Remaining Warning Cleanup

Task: `PMBOT-QUALITY-003-REMAINING-WARNING-CLEANUP`

Status: completed; pending commit/push reporting in final response.

## Summary

PMBOT warning hygiene was reduced from 8 total warnings to 0 total warnings without suppressing warnings by filter or changing severity for cosmetic reasons.

The cleanup added missing `schema_version` metadata to legacy result docs, marked historical commit/task references as explicit legacy audit references, kept the malformed paper fixture intentional, and surfaced documented exceptions in the artifact health report.

## Warning Counts

- Before: 8 total, 0 blocking, 3 action_required, 4 review_needed, 1 informational.
- After: 0 total, 0 blocking, 0 action_required, 0 review_needed, 0 informational.
- Documented exceptions after: 48.

## Documented Exception Types

- `accepted_missing_pointer_target`: 20
- `documented_legacy_reference`: 23
- `documented_non_object_json_artifact`: 4
- `known_intentional_malformed_fixture_parse_failure`: 1

## Safety

- No runtime wiring was changed.
- No network/API calls were added.
- No credentials, wallet, private keys, trading, real orders, autonomous paper orders, scoring, EV, edge, probability, side recommendation, dispatcher, run_codex, or prompt automation behavior was added.

## Verification

- `python -m pytest pm_bot\quality -q`: 27 passed.
- `python -m pytest pm_bot\workbench pm_bot\dashboard pm_bot\operator -q`: 87 passed, 48 subtests passed.
- `python -m pytest pm_bot\paper -q`: 331 passed, 39 subtests passed.
- JSON parse check for changed and new JSON files: passed.
- `python -m py_compile` for changed Python files: passed.
- `git diff --check`: passed.
- Forbidden path/runtime safety scan: passed.

## Notes

The paper suite exposed a stale checked-in SHA-256 fixture for `pm_bot/paper/manual_snapshot_import_source/006_unsupported.json`. The source file already hashed to `58b833609f772eee356c4168f485203908d470e01bb80c1aeb6a9e584eb8c0fc` in `HEAD`, so the corresponding generated current/expected manifest JSON values were aligned to that real source hash.
