# PMBOT-LLM-004 Manual LLM Review Workbench Surface

Task: PMBOT-LLM-004-MANUAL-LLM-REVIEW-WORKBENCH-SURFACE

## Summary

This change surfaces the existing local manual LLM paste-in review artifact in the operator review pack and generated workbench-facing artifacts.

The integration is passive and read-only. It reads `pm_bot/llm/manual_llm_paste_in_review.v1.json` when present, summarizes only safe status/count/list fields, and does not infer, rewrite, or generate LLM conclusions.

## Surface Behavior

- Present artifact: `artifact_status` is `present`, `validation_status` is copied from the manual review artifact, and safe summary fields are surfaced.
- Missing artifact: `artifact_status` is `missing`, `validation_status` is `not_available`, and workbench export continues.
- Malformed or unreadable artifact: `artifact_status` is `invalid`, `validation_status` is `rejected_or_unreadable`, and workbench export continues with a safe error summary.

## Surfaced Fields

- `artifact_status`
- `validation_status`
- `errors_count`
- `warnings_count`
- `accepted_sections`
- `missing_sections`
- `forbidden_content_detected.detected`
- `forbidden_content_detected.findings_count`
- `next_safe_operator_action`
- `analysis_only_warning`

## Boundary

Manual LLM review is analysis-only and not trading advice. This task adds no LLM API calls, browser automation, prompt automation, runtime integration, credentials, wallet access, real orders, autonomous paper orders, probability estimates, EV, edge, scoring, side recommendations, or market decision logic.

## Verification

- `python -m pytest pm_bot\llm -q`
- `python -m pytest pm_bot\workbench -q`
- `python -m pytest pm_bot\quality pm_bot\dashboard pm_bot\operator -q`
- `python -m pytest pm_bot\paper -q`
- JSON parse check for changed JSON files
- `python -m py_compile pm_bot\workbench\export_operator_review_pack.py pm_bot\workbench\tests\test_operator_review_pack_export.py`
- `git diff --check`
- Forbidden path/runtime safety scan for changed files and the manual LLM surface
