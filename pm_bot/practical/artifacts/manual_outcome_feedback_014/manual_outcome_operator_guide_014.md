# Manual Outcome Operator Guide 014

This guide is for later paper-only outcome feedback after a valid local resolution record exists.

## Required Fields For Resolved Markets

- actual_outcome_summary
- resolved_at
- resolution_source_reference
- resolution_evidence_summary
- operator_approved

## Paper Hypothesis Result Labels

- `pending` - Outcome is unresolved and feedback is not ready.
- `aligned` - Approved local outcome review found the paper hypothesis directionally aligned with the result.
- `not_aligned` - Approved local outcome review found the paper hypothesis did not align with the result.
- `ambiguous` - Approved local outcome review found the result cannot fairly score the paper hypothesis.
- `void` - Approved local outcome review found the market was void or excluded from scoring.

## Source Accuracy Feedback

- `pending` - Outcome unresolved; no source accuracy claim.
- `useful` - Source helped the approved local outcome review.
- `insufficient` - Source did not provide enough resolution evidence.
- `misleading` - Source framing led analysis away from the approved local outcome record.
- `contradicted` - Source was contradicted by the approved local outcome record.
- `unknown` - Local packet does not support a source accuracy claim.

## Do Not Put In The Packet

- Invented outcomes or guessed resolution dates.
- Live lookup results that were not saved as local evidence.
- Secrets, cookies, wallet material, or authenticated data.
- Real-money actions or market-side instructions.

## Safety Rules

- No outcome invention.
- No live network fetch.
- No OpenRouter call.
- No Polymarket API call.
- No scheduler, daemon, background worker, or polling loop.
- No autonomous trading.
