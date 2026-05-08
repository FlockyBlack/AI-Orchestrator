# PMBOT Source Quality Ledger Protocol

SOURCE-009A adds only a protocol placeholder for future source-quality tracking. This is not trading performance learning.

## Purpose

The future ledger should track whether a source helps PMBOT capture rules and resolution evidence accurately. It should not rank a source just because a trade later made money.

Allowed future fields:

- source_id
- source_type
- market_class
- markets_used_count
- resolved_markets_count
- resolution_alignment_count
- misleading_count
- timeliness_notes
- source_reliability_notes
- operator_review_notes

## Quality Basis

A source should be reviewed by:

- resolution alignment
- timeliness
- official/source hierarchy
- contradiction rate
- usefulness for rules/source capture
- usefulness for operator review

## Forbidden Uses

- no trade profit as sole source quality score
- no buy or sell recommendation
- no edge, EV, probability, or confidence scoring
- no side selection
- no autonomous execution authority
- no wallet or order authority
