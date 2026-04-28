# PM Bot Raw Artifact Ingestion Manifest V1

## Purpose

PMBOT-BATCH-010 sits directly after the PMBOT-BATCH-009 raw artifact validator. The validator decides whether a local fixture payload satisfies the raw artifact contract. The new manifest layer converts that validation result into a deterministic offline handoff artifact with two explicit buckets:

- accepted artifacts
- quarantined artifacts

This layer is offline-only, fixture-only, local-only, paper-only, and deterministic.

## What The Manifest Records

The manifest builder inspects local fixture JSON files and emits:

- manifest version and source contract version
- normalized fixtures directory metadata
- accepted artifact summaries for fixtures that are ready to hand off to a future normalization design
- quarantined artifact summaries for fixtures that must not move forward
- quarantine reasons with code, severity, and deterministic message text
- count totals for checked, accepted, quarantined, unexpected failures, and unexpected passes
- safety summary flags copied from the offline validator
- a next-stage marker showing that only normalization contract design is allowed next

## Accepted Versus Quarantined

Accepted artifacts are fixtures that pass the existing raw artifact validator and are marked `handoff_ready_for_normalization=true`.

Quarantined artifacts are fixtures that produce validator findings and are marked `handoff_ready_for_normalization=false`.

Expected invalid fixtures are intentionally quarantined artifacts. They are part of the offline fixture suite and are not treated as test failures when their failures match expectation.

## Quarantine Reason Model

Each quarantined artifact contains:

- `file`
- `artifact_id` when available, otherwise `null`
- `reasons`

Each reason contains:

- `code`
- `severity`
- `message`

This preserves the validator outcome in a grouped, artifact-centric format that is easier to review before any later approved stage.

## Handoff Readiness

The manifest does not normalize data. It does not transform artifacts into replay payloads. It only states whether a local artifact is safe to hand off to a future normalization layer design.

Current meaning:

- accepted artifact: structurally ready for a future approved normalization layer
- quarantined artifact: blocked from normalization handoff until its issues are resolved

## Explicit Non-Goals

PMBOT-BATCH-010 does not implement:

- normalization
- replay integration
- live fetcher logic
- Polymarket API access
- network or external API calls
- credential handling
- wallet or private-key handling
- signing
- orders
- trading
- runtime wiring
- dispatcher integration
- `run_codex` integration

Any future normalization implementation, live read-only fetcher work, or runtime wiring still requires separate approval.
