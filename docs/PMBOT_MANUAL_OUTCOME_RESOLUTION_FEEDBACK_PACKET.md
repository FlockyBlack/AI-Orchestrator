# PMBOT Manual Outcome Resolution Feedback Packet

PRACTICAL-014 adds a paper-only feedback packet flow after PRACTICAL-013 created the outcome recheck queue and source learning scorecard update.

## Current Readiness

- Tracked markets: 5
- Unresolved outcomes: 5
- Feedback-ready markets: 0

Feedback readiness is zero because every tracked market still has unresolved local outcome status.

## Manual Outcome Resolution Later

An operator fills a market's manual outcome packet only after saved local resolution evidence exists. Resolved packets require an outcome summary, resolution time, source reference, evidence summary, and operator approval.

## Feedback Labels

- `pending` means outcome feedback is blocked.
- `aligned` means the paper hypothesis aligned with the approved local outcome packet.
- `not_aligned` means the paper hypothesis missed after approved local review.
- `ambiguous` means the outcome cannot fairly score the paper hypothesis.
- `void` means the outcome is excluded from scoring.

## Source Accuracy Feedback

Sources stay pending until a local outcome packet is approved. After resolution, source feedback can label sources as useful, insufficient, misleading, contradicted, or unknown.

## Synthetic Fixtures

Resolved examples under `pm_bot/tests/fixtures/manual_outcome_feedback/` are synthetic tests only. They are not real market outcomes and do not change current market state.

## Safety Boundary

- No outcome invention.
- No live network fetch.
- No OpenRouter call.
- No Polymarket API call.
- No scheduler, daemon, background worker, or polling loop.
- No autonomous trading.

## Source Learning Candidate

- Available: `false`
- Reason: no resolved local outcome records

## Next Recommended Action

- `ORCH-PMBOT-PRACTICAL-015-PRACTICAL-OPERATOR-DAILY-WORKFLOW-RUNBOOK`
