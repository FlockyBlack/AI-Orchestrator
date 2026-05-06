# PMBOT Workbench 002 Operator Quickstart

Task ID: `PMBOT-WORKBENCH-002-OPERATOR-QUICKSTART-AND-REVIEW-PACK-USABILITY`

## Purpose

Operator Workbench / Review Pack v1 is a deterministic, local-only review surface for PMBOT operator review. It gathers existing local artifacts into a human-readable pack so an operator can check artifact presence, paper accounting audit state, dashboard audit state, manual command inbox state, quality warnings, and safety boundaries.

This workbench is not a trading system. It does not fetch live data, call network APIs, read credentials, use wallets, place orders, create autonomous paper orders, score markets, estimate probability, calculate EV, calculate edge, infer truth, recommend sides, or make market decisions.

## Open First

1. Open this quickstart first: `docs/PMBOT_WORKBENCH_002_OPERATOR_QUICKSTART.md`.
2. Then open the static operator HTML report: `pm_bot/dashboard/static_operator_report.v1.html`.
3. Then open the operator review pack Markdown: `pm_bot/workbench/operator_review_pack.v1.md`.
4. Use the JSON pack only when you need exact machine-readable fields: `pm_bot/workbench/operator_review_pack.v1.json`.

The static HTML report is the best first operator view because it is self-contained and summarizes the most important local artifacts without a dashboard server, frontend runtime, browser automation, live refresh, or network dependency.

## Reading Order

Read the current package in this order:

1. `pm_bot/dashboard/static_operator_report.v1.html`
2. `pm_bot/workbench/operator_review_pack.v1.md`
3. `pm_bot/quality/artifact_health_report.v1.md`
4. `pm_bot/operator/manual_command_inbox_review.v1.md`
5. `pm_bot/operator/review_pack_command_bridge_examples.v1.md`
6. `pm_bot/dashboard/portfolio_audit_state_preview.v1.md`
7. JSON versions of the same files only when you need exact fields for review notes.

## Quickstart Steps

1. Confirm the review pack safety posture.
   Check `Safety Flags` and `Warnings` in `pm_bot/workbench/operator_review_pack.v1.md`. Expected safe values include no runtime wiring, no network/API use, no credentials, no wallet, no trading, no autonomous paper orders, no recommendations, no truth inference, no probability/EV/edge scoring, and no command execution authority.

2. Review artifact inventory.
   Check `Artifact Inventory` and `Missing Artifacts`. The tracked review pack currently reports 20 tracked artifacts, 20 present, 0 missing, and 0 required artifacts missing.

3. Review paper audit status.
   Check `Paper Audits`. Current status shows `reconciliation_passed` and `batch_audit_passed`, with 0 audit warnings and 0 audit mismatches. This means the local paper accounting artifacts are internally consistent for the checked fixtures.

4. Review portfolio accounting.
   Check `Portfolio Accounting`. Current local fixture/manual accounting values include paper accounting cumulative PnL `6.00` and batch accounting cumulative PnL `-1.00`. These values are accounting-only local artifact outputs, not strategy profitability.

5. Review dashboard state.
   Check `Dashboard State` and then `pm_bot/dashboard/portfolio_audit_state_preview.v1.md`. Current dashboard audit status is `paper_017_reconciliation_available_with_dashboard_002_static_export`. The dashboard artifact is static and local; it is not a server, frontend runtime, browser automation, or live dashboard.

6. Review operator inbox.
   Check `Operator Inbox` and then `pm_bot/operator/manual_command_inbox_review.v1.md`. Current inbox review saw 7 records: 3 accepted, 3 rejected, and 1 needing human review. Accepted records are queued for human review or artifact lookup only. Rejected records include live-source, execution-authority, and scoring payload violations.

7. Review quality warnings.
   Check `pm_bot/quality/artifact_health_report.v1.md`. Current quality status is `health_passed`, with 0 warnings and 0 blockers. Documented exceptions remain visible in the report for intentional malformed fixtures, legacy audit references, accepted placeholder pointers, and intentional non-object JSON fixtures.

8. Record findings manually.
   Any operator note should stay a human review note. Do not turn review observations into commands, orders, recommendations, scoring, or runtime wiring.

## Major Artifacts

- `pm_bot/workbench/operator_review_pack.v1.md`: primary human-facing review pack. Open this first after the quickstart.
- `pm_bot/dashboard/static_operator_report.v1.html`: self-contained local static operator report. Open this first after the quickstart when you want one browser-readable view of workbench, PAPER-019, quality, artifact health, inbox, safety, and next manual actions.
- `pm_bot/dashboard/static_operator_report_summary.v1.json`: exact machine-readable summary used to render the static HTML report.
- `pm_bot/workbench/operator_review_pack.v1.json`: exact review pack data for deterministic inspection.
- `pm_bot/quality/artifact_health_report.v1.md`: human-readable health/staleness report. The current report is warning-clean and retains documented exception detail for traceability.
- `pm_bot/quality/artifact_health_report.v1.json`: exact health report data, including warning counts and safety flag summaries.
- `pm_bot/operator/manual_command_inbox_review.v1.md`: inert manual command inbox review. It classifies records but does not execute them.
- `pm_bot/operator/review_pack_command_bridge_examples.v1.md`: static examples for how future manual command records may map to review pack sections without execution authority.
- `pm_bot/dashboard/portfolio_audit_state_preview.v1.md`: static dashboard audit state export for local accounting review context.
- `docs/PMBOT_INTEGRATION_010_RESULT.json`: integration result proving Round003 merged to main with tests and safety checks.

## Accounting-Only PnL

Paper accounting PnL in the review pack is fixture/manual accounting only. It is useful for checking that local accounting records reconcile, but it is not:

- trading advice
- strategy profitability
- live market performance
- true resolution status
- expected value
- market edge
- probability
- a side, size, price, or order recommendation

Current values such as `6.00` and `-1.00` should be read as local deterministic accounting outputs from the existing fixture/manual records.

## Paper Audit Status

`reconciliation_passed` and `batch_audit_passed` mean deterministic local consistency checks passed for the audited artifacts. They do not mean that a market resolved correctly, that a trading strategy works, or that any market outcome is true.

If a future audit reports mismatches, failed checks, unexpected orders, autonomous actions, unsafe flags, or parse failures in required artifacts, pause and classify before using the review pack for operator review.

## Quality Warning Guidance

Current QUALITY-001 status:

- `report_status`: `health_passed`
- warnings: 0
- blockers: 0
- blocking warning detected by integration review: false

Current warning types are empty. Documented exceptions are not blocker warnings; they are retained for auditability and intentional fixture coverage.

Current warning breakdown:

- none

Current documented exception breakdown:

- 20 `accepted_missing_pointer_target`
- 23 `documented_legacy_reference`
- 4 `documented_non_object_json_artifact`
- 1 `known_intentional_malformed_fixture_parse_failure`

### Non-Blocking Warnings

There are no current quality warnings. If future warnings reappear, treat these categories as non-blocking only when the quality report has no blockers, tests pass, and safety summaries show no unexpected true or nonzero values:

- optional artifact missing, such as `docs/PMBOT_INFRA_009_RESULT.json`
- stale references in older context docs
- missing `schema_version` or `task_id` metadata in legacy or fixture artifacts
- embedded artifact pointers that point to missing local files
- expected fixture files whose corresponding actual output is absent because that feature is not currently materialized
- known intentional malformed fixture parse failure
- fixture alignment mismatch that is reported as a warning and not as a blocker

### Blocking Conditions

Block operator reliance on the pack and escalate for implementation review if any of these appear:

- required review pack artifact missing
- required JSON artifact cannot parse, except known intentional malformed fixtures outside the required path
- quality report has non-empty `blockers`
- quality report status changes to a failed or blocked status
- safety summary shows unexpected true or nonzero values for runtime wiring, network/API, credentials, wallet, trading, orders, autonomous paper orders, recommendations, truth inference, market decisions, command execution, or probability/EV/edge scoring
- review pack claims live fetches, live prices, API results, authenticated endpoints, wallets, signing, trading, recommendations, or scoring
- operator bridge grants execution authority or runtime trigger authority
- tests fail for new or unknown reasons

## Allowed Manual Actions

Allowed actions are local, manual, and review-only:

- read the review pack Markdown and JSON
- inspect artifact inventory and missing artifact warnings
- inspect paper reconciliation and batch audit artifacts
- inspect dashboard static audit state
- inspect accepted, rejected, and needs-human-review inbox records
- write human review notes in docs or task reports
- run existing local validation and test commands when explicitly performing a local review
- recommend a follow-up implementation task

## Forbidden Actions

Do not use the review pack to do any of the following:

- fetch live data
- call network APIs or authenticated endpoints
- read credentials, API keys, wallet files, or private keys
- sign wallet operations
- place real orders
- create live trading
- create autonomous paper orders
- recommend markets, sides, prices, sizes, trades, or orders
- infer truth or market resolution
- calculate probability, EV, edge, or market scores
- wire runtime dispatchers, `run_codex`, Telegram runtime, webhooks, polling, dashboard servers, or frontend runtimes
- execute manual command inbox records

## Existing Local Commands

Regenerate the full operator workbench package with one deterministic local command:

```powershell
python pm_bot\workbench\run_operator_workbench_export.py
```

The command runs local exporters only, writes `pm_bot/workbench/operator_workbench_export_run.v1.json` and `pm_bot/workbench/operator_workbench_export_run.v1.md`, and does not start automation, daemons, schedulers, Telegram runtime, dashboard runtime, network/API behavior, trading, scoring, or command execution.

Existing local scripts are available for individual artifacts:

```powershell
python pm_bot\workbench\export_operator_review_pack.py --write
python pm_bot\quality\export_artifact_health_report.py --write
python pm_bot\operator\validate_review_pack_command_bridge.py pm_bot\operator\review_pack_command_bridge_examples.v1.json --examples
```

Use these only as local deterministic review/validation commands. They should not be treated as runtime automation or trading behavior.

## Troubleshooting

If the operator does not know where to start, open `pm_bot/workbench/operator_review_pack.v1.md` and read only `Artifact Inventory`, `Paper Audits`, `Portfolio Accounting`, `Warnings`, `Safety Flags`, and `Next Safe Manual Actions`.

If the quality report feels too noisy, first check `report_status`, total warnings, blocker count, and safety flag summary. Then group the warnings by type. Do not read all 149 warnings linearly unless investigating artifact hygiene.

If PnL looks like strategy performance, stop and re-label it as fixture/manual accounting only. It is not live performance, profitability, EV, edge, or advice.

If a bridge or inbox record looks command-like, check `execution_authority`, `can_trigger_runtime`, `commands_executed`, `orders_created`, and `network_calls`. Expected values preserve inert review-only behavior.

If generated artifacts appear stale, rerun only the existing local exporters after confirming this is a local docs/artifact review task. Do not add new runtime wiring. If rerunning exporters changes optional artifact presence, inspect the diff and restore unrelated generated churn before committing docs-only work.

## Remaining Gaps

- The single-command runner now exists; future work should keep its scope manual, local, deterministic, and offline.
- The quality report is correct but too noisy for first-pass operator use.
- Warning severity is implicit; operators need a clearer blocking vs non-blocking summary in the pack itself.
- Optional infrastructure artifact state can appear stale: the tracked review pack reports INFRA-009 optional artifacts as missing, while the files are present in this workspace.
- The review pack does not yet include a compact "operator should open these 5 files" section.
- The review pack does not summarize quality warning categories directly.
- Stale pointer and expected fixture alignment warnings need a clearer owner/action path.

## Recommended Next Task

Recommend evaluating `PMBOT-WORKBENCH-004-QUALITY-WARNING-SEVERITY-SUMMARY`.

Purpose: add a clearer warning severity and category summary before the full quality warning detail, while keeping the workbench local-only, deterministic, non-trading, non-scoring, and free of runtime wiring.
