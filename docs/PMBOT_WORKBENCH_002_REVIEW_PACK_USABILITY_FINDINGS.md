# PMBOT Workbench 002 Review Pack Usability Findings

Task ID: `PMBOT-WORKBENCH-002-OPERATOR-QUICKSTART-AND-REVIEW-PACK-USABILITY`

## Scope

This review inspected the local PMBOT Operator Workbench / Review Pack v1 artifacts created by WORKBENCH-001, QUALITY-001, and OPERATOR-003 after INTEGRATION-010 merged Round003 to `main`.

This is a docs/usability review only. No feature implementation, runtime wiring, automation, network/API behavior, trading, paper order creation, scoring, probability, EV, edge, truth inference, or market decision logic was added.

## Usability Strengths

- The main review pack Markdown is short enough for a human operator to open first.
- The review pack clearly states local-only behavior, no recommendations or decisions, and accounting-only PnL interpretation.
- The pack surfaces the most important operator review domains: artifact inventory, paper audits, portfolio accounting, dashboard state, operator inbox, warnings, safety flags, and next safe manual actions.
- Paper audit status is easy to find and currently clean: `reconciliation_passed`, `batch_audit_passed`, 0 audit warnings, and 0 audit mismatches.
- Operator inbox status is easy to understand: 7 records seen, 3 accepted, 3 rejected, and 1 needs human review, with no execution authority.
- OPERATOR-003 bridge examples are explicit about invalid cases for execution authority, runtime triggers, Telegram token fields, network/API fields, wallet/private-key fields, and probability/EV/edge/score fields.
- QUALITY-001 reports safety flag observations separately from artifact hygiene warnings, which makes safety review possible even when warning volume is high.

## Usability Weaknesses

- There is no single operator-facing quickstart in the generated workbench package itself.
- The review pack does not say loudly enough which file to open first.
- The quality report has 149 warnings and is too noisy for a first-pass operator review.
- Warning severity is implicit. Operators must infer from `report_status`, empty blockers, integration notes, and safety summaries which warnings are blocking.
- Quality warnings are not grouped in the Markdown report by warning type, so operators see a long mixed list.
- Optional infrastructure artifact state is confusing: the tracked review pack reports INFRA-009 optional artifacts as missing, while the files are present in this workspace and local exporter/test runs can flip generated artifacts to present.
- Accounting values are visible before the operator has a complete mental model of "fixture/manual accounting only."
- Dashboard state references known market IDs, which can distract operators unless the non-recommendation boundary is repeated nearby.
- The bridge examples are safe but command-shaped; an operator could skim them and mistake mappings for executable command behavior.
- There is no one-command local regeneration workflow for the full operator workbench package.

## Confusing Sections

- `Portfolio Accounting`: useful values are present, but PnL numbers need immediate context that they are accounting-only and not profitability.
- `Quality Warnings`: the warning list is accurate but hard to triage because fixture alignment, stale pointer, schema metadata, optional missing artifact, and intentional malformed fixture warnings are mixed together.
- `Dashboard State`: the status `paper_017_reconciliation_available_with_dashboard_002_static_export` is precise but dense for an operator. It needs a plain-language summary.
- `Review Pack Command Bridge Examples`: "valid bridge records" may sound operational even though they are static, inert, and require human review.

## Noisy Warnings

Current QUALITY-001 warning breakdown:

- 51 `expected_fixture_alignment_warning`
- 50 `fixture_alignment_actual_missing`
- 18 `schema_version_missing`
- 15 `embedded_artifact_pointer_warning`
- 6 `stale_reference_warning`
- 3 `json_top_level_not_object`
- 3 `task_id_missing`
- 1 `fixture_alignment_mismatch`
- 1 `known_intentional_malformed_fixture_parse_failure`
- 1 `missing_optional_artifact`

The noisiest groups are expected fixture alignment warnings and actual-missing fixture outputs. These are useful for artifact hygiene but not useful as the first thing an operator sees. The Markdown quality report should summarize counts first and place full detail later.

## Missing Or Stale Artifact Problems

- The tracked review pack inventory reports 2 missing optional infrastructure artifacts and 0 required missing artifacts:
  - `docs/PMBOT_INFRA_009_RESULT.json`
  - `docs/PMBOT_INFRA_009_ABC_ROUND003_WORKTREE_MATERIALIZATION.md`
- QUALITY-001 reports 1 missing artifact in its wider scan: optional `docs/PMBOT_INFRA_009_RESULT.json`.
- In this workspace both optional INFRA-009 files are present on disk and tracked by git. That makes the generated review pack and quality report stale relative to the current local filesystem.
- QUALITY-001 reports 111 stale pointer warnings, 90 missing embedded pointers, and 50 expected fixture alignments where actual outputs are missing.
- These are non-blocking for the current operator workbench review because the quality report status is `health_passed_with_warnings`, blockers are empty, and safety summaries show no unexpected true or nonzero values.
- They remain important cleanup signals before relying on older artifact families as operator-facing surfaces.

## Warning Classification

Blocking warning count for this task: 0.

Non-blocking warning count for this task: 149.

Blocking conditions should include required missing artifacts, required JSON parse failures, non-empty quality blockers, failed or blocked quality status, unsafe true/nonzero safety values, runtime/network/trading/scoring behavior, command execution authority, unexpected order creation, and new or unknown test failures.

Non-blocking conditions in the current report include optional missing infrastructure artifacts, legacy schema/task metadata gaps, stale references, missing embedded pointers, expected fixture outputs not materialized, known intentional malformed fixture parse failure, and fixture alignment mismatch reported as a warning rather than a blocker.

## Recommended Improvements

- Add an operator entrypoint section to the generated review pack that says what to open first and what to ignore on first pass.
- Add a warning severity summary directly to the review pack: blocker count, non-blocking count, top warning categories, and next action.
- Add a compact "quality warning cheat sheet" to the quality Markdown before the full warning list.
- Repeat the accounting-only PnL boundary immediately next to any PnL values.
- Add plain-language dashboard status text next to the current machine-readable status.
- Separate command bridge examples into "static mapping only" and "invalid executable behavior" sections.
- Include a generated list of top operator artifacts with exact paths.
- Add one local deterministic command to regenerate the full workbench package from existing local artifacts.
- Make optional artifact presence deterministic in regenerated workbench outputs, or document when committed generated artifacts are intentionally stale relative to local optional docs.

## Recommended Next Implementation Task

Recommend evaluating `PMBOT-WORKBENCH-003-SINGLE-COMMAND-LOCAL-EXPORT`.

The task should create one local deterministic command/script to regenerate the operator workbench package from existing local artifacts. It should not add network/API calls, credentials, wallet access, trading, real orders, live trading, autonomous paper orders, recommendations, truth inference, probability, EV, edge, scoring, market decisions, command execution authority, dispatcher changes, `run_codex` changes, dashboard runtime, or Telegram runtime.

## Safety Notes

The current review pack must not be interpreted as trading advice, strategy profitability, EV, edge, probability, truth inference, market scoring, side recommendation, market recommendation, order recommendation, or autonomous decision support.
