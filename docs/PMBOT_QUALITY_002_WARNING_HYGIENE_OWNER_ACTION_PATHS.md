# PMBOT-QUALITY-002 Warning Hygiene Owner Action Paths

## Purpose

PMBOT-QUALITY-002 adds a deterministic local warning hygiene layer for artifact health warnings. It does not hide, suppress, or silently downgrade warnings. It groups the existing warnings into owner/action paths so an operator can route cleanup without losing the original warning detail.

## Scope

- Source report: `pm_bot/quality/artifact_health_report.v1.json`
- Hygiene report: `pm_bot/quality/warning_hygiene_owner_action_paths.v1.json`
- Operator Markdown: `pm_bot/quality/warning_hygiene_owner_action_paths.v1.md`
- Expected fixture: `pm_bot/quality/expected_warning_hygiene_owner_action_paths.v1.json`
- Result doc: `docs/PMBOT_QUALITY_002_RESULT.json`

## Required Metadata

Each warning record includes:

- deterministic `warning_id` and `bucket_id`
- `source_artifact` and exact `source_path`
- `warning_category` and `severity`
- `owner` and `owner_type`
- `action_path` and `action_type`
- `deferrable`
- `expected_status`
- `safety_relevance`
- recommended operator and maintainer actions
- rationale

## Operator Interpretation

- Blocking warnings still block local MVP usage.
- Non-blocking warnings remain visible and are routed to owners.
- Deferrable warnings can be postponed for local MVP usage when the source report has zero blocking warnings.
- Non-deferrable warnings are not automatically blockers; they are explicit cleanup queues that need owner action.
- Safety-relevant warnings are marked so operator usability and data integrity issues are easy to separate from execution boundaries.

## Safety

The builder is local and deterministic. It performs local file reads and writes only when `--write` is passed. It does not call network APIs, use wallets or private keys, create orders, trade, score markets, recommend sides, wire runtime systems, or execute operator inbox commands.
