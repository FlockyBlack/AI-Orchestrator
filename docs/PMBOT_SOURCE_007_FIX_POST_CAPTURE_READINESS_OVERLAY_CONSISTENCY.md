# PMBOT SOURCE-007 Fix Post-Capture Readiness Overlay Consistency

SOURCE-007 fixes the SOURCE-006 exporter so post-capture readiness reads the already written SOURCE-005 manual capture overlay instead of rebuilding ingest state with default strict-ready behavior.

## Result

- task_id: PMBOT-SOURCE-007-FIX-POST-CAPTURE-READINESS-OVERLAY-CONSISTENCY
- status: completed_pushed
- overlay_read_by_readiness_exporter: true
- real_filled_template_count: 1
- real_ingested_template_count_before_fix: 0
- real_ingested_template_count_after_fix: 1
- draft_ingested_template_count_after_fix: 1
- ready_ingested_template_count_after_fix: 0
- markets_with_resolution_criteria_text_after_fix: 1
- markets_with_full_resolution_rules_after_fix: 1
- markets_with_official_source_references_after_fix: 1
- markets_still_missing_resolution_criteria_text_after_fix: 13
- markets_still_missing_full_resolution_rules_after_fix: 13
- markets_still_missing_official_source_references_after_fix: 13
- future_live_002_allowed: false
- live_readonly_api_discovery_readiness: source_overlay_present_but_not_ready

## Readiness Gate

The incorrect blocker `no real manually ingested source capture templates` was removed when the overlay contains market_id 597964.

Current blocker reasons remain operator-review blockers:

- ingested source capture exists only as draft
- no ready_for_local_review or reviewed source capture templates
- direct Polymarket rules verification still required
- no explicit operator override document exists

This is readiness accounting only. It does not approve future LIVE-002, runtime wiring, queue changes, or any market action.

## Validation

- python -m compileall pm_bot
- pytest tests/test_post_capture_readiness.py -q
- pytest tests/test_manual_resolution_source_capture_ingest.py -q
- pytest pm_bot/llm/tests -q
- python -m pm_bot.llm.ingest_manual_resolution_source_capture --dry-run --summary-only --include-drafts
- python -m pm_bot.llm.ingest_manual_resolution_source_capture --write --summary-only --include-drafts
- python -m pm_bot.llm.export_post_capture_readiness --write

## Safety Boundary

- no OpenRouter calls
- no Polymarket API calls
- no external network calls except git push
- no wallet or private-key access
- no orders
- no trading runtime changes
- no dispatcher changes
- no background worker changes
- no queue mutation
- no browser automation
- no canonical packet mutation
- no market action guidance
