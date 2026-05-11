# PMBOT Paper Trade Intent Candidates

- Paper-only, non-executable candidate batch.
- Intent candidates: 6
- Simulated-entry candidates: 2
- Observe-only candidates: 4

## Candidates

### `563650`

- Title: SCOTUS accepts sports event contract case by July 31, 2026?
- Intent: `paper-intent-020-021-563650`
- Hypothesis: `563650.analysis.adc53630aa1f.paper_hypothesis`
- Paper action type: `simulated_entry`
- Side label: `track_yes` paper-tracking label only
- Intended paper notional: `$25.0`
- Saved local evidence paths: 1
- Rationale: Saved local public evidence exists for this market, so the paper simulator can create a small non-executable tracking fill for ledger plumbing.
- Missing evidence:
- outcome_unresolved

### `573656`

- Title: Will Bitcoin hit $150k by December 31, 2026?
- Intent: `paper-intent-020-021-573656`
- Hypothesis: `573656.analysis.ceab64191597.paper_hypothesis`
- Paper action type: `observe_only`
- Side label: `no_action` paper-tracking label only
- Intended paper notional: `$0.0`
- Saved local evidence paths: 0
- Rationale: Saved local public evidence is incomplete for this market, so the paper candidate stays in observe-only tracking.
- Missing evidence:
- saved_public_evidence_packet_missing
- new_market_public_fetch_approval_pending
- new_market_saved_fetch_evidence_missing
- outcome_unresolved

### `597964`

- Title: Macron out by June 30, 2026?
- Intent: `paper-intent-020-021-597964`
- Hypothesis: `597964.analysis.33643849e5db.paper_hypothesis`
- Paper action type: `observe_only`
- Side label: `no_action` paper-tracking label only
- Intended paper notional: `$0.0`
- Saved local evidence paths: 0
- Rationale: Saved local public evidence is incomplete for this market, so the paper candidate stays in observe-only tracking.
- Missing evidence:
- saved_public_evidence_packet_missing
- outcome_unresolved

### `598936`

- Title: Will the next UK election be called by June 30, 2026?
- Intent: `paper-intent-020-021-598936`
- Hypothesis: `598936.analysis.dceea0f50063.paper_hypothesis`
- Paper action type: `observe_only`
- Side label: `no_action` paper-tracking label only
- Intended paper notional: `$0.0`
- Saved local evidence paths: 0
- Rationale: Saved local public evidence is incomplete for this market, so the paper candidate stays in observe-only tracking.
- Missing evidence:
- saved_public_evidence_packet_missing
- outcome_unresolved

### `691547`

- Title: Kraken IPO by December 31, 2026?
- Intent: `paper-intent-020-021-691547`
- Hypothesis: `691547.analysis.56b3a68b9b94.paper_hypothesis`
- Paper action type: `simulated_entry`
- Side label: `track_yes` paper-tracking label only
- Intended paper notional: `$25.0`
- Saved local evidence paths: 1
- Rationale: Saved local public evidence exists for this market, so the paper simulator can create a small non-executable tracking fill for ledger plumbing.
- Missing evidence:
- outcome_unresolved

### `692258`

- Title: MicroStrategy sells any Bitcoin by June 30, 2026?
- Intent: `paper-intent-020-021-692258`
- Hypothesis: `692258.analysis.bed289c1494d.paper_hypothesis`
- Paper action type: `observe_only`
- Side label: `no_action` paper-tracking label only
- Intended paper notional: `$0.0`
- Saved local evidence paths: 0
- Rationale: Saved local public evidence is incomplete for this market, so the paper candidate stays in observe-only tracking.
- Missing evidence:
- saved_public_evidence_packet_missing
- outcome_unresolved

## Safety

- Every candidate is paper-only and non-executable.
- real_order_allowed remains `false`.
- wallet_required remains `false`.
- trading_endpoint_required remains `false`.
- operator_review_required remains `true`.
- Side labels are paper tracking labels only, not real trading instructions.
