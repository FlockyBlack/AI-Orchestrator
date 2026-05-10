# PMBOT How To Process A Resolved Market Outcome

Use this workflow only after a market has saved local resolution evidence. Do not invent outcomes. Do not mark unresolved markets as resolved without local evidence.

## 1. Open the manual outcome packet

Per-market pending packets live under:

- `pm_bot/practical/artifacts/manual_outcome_feedback_014/markets/<market_id>/manual_outcome_resolution_packet.unresolved.json`
- `pm_bot/practical/artifacts/manual_outcome_feedback_014/markets/<market_id>/manual_outcome_resolution_packet.unresolved.md`

Create a new versioned resolved packet in a later task directory. Do not overwrite the unresolved 014 packet in place.

## 2. Fill required outcome fields

Fill only from saved local resolution evidence:

- `actual_outcome_summary`
- `resolved_at`
- `resolution_source_reference`
- `resolution_evidence_summary`
- `operator_approved`

If the evidence is incomplete, keep the packet unresolved.

## 3. Choose the paper result label

Choose one label after manual review:

- `aligned`
- `not_aligned`
- `ambiguous`
- `void`

Use `ambiguous` when the outcome cannot fairly score the paper hypothesis. Use `void` when the market outcome is excluded from feedback scoring.

## 4. Run the feedback evaluator

Use the existing paper feedback evaluator in a later paper-only task:

```powershell
python -m pm_bot.practical.paper_hypothesis_feedback_evaluator --help
```

Use the resolved manual outcome packet, the current paper tracking snapshot, and any applied paper update artifact.

## 5. Update source accuracy feedback

Use the existing source accuracy feedback module in the same paper-only task:

```powershell
python -m pm_bot.practical.source_accuracy_feedback --help
```

Source feedback can describe whether a source was useful, insufficient, misleading, contradicted, or unknown relative to the approved local outcome packet.

## 6. Update the source learning scorecard

After paper and source feedback exist, create a versioned source learning update candidate. Do not apply source learning automatically.

Open:

- `pm_bot/practical/artifacts/outcome_recheck_source_learning_013/source_learning_scorecard_update_013.md`
- `pm_bot/practical/artifacts/manual_outcome_feedback_014/source_learning_update_candidate_from_feedback_014.md`

## 7. Safety rules

- Never invent outcomes, resolution times, or source references.
- Never treat feedback as trading proof.
- Never change original analysis, hypothesis, evidence, dashboard, or tracking artifacts in place.
- Never use live network fetches in this workflow.
- Never call OpenRouter or Polymarket APIs in this workflow.
- Never use authenticated endpoints, cookies, browser profiles, wallet files, private keys, signing paths, or trading endpoints.

## Expected result

A later task should produce new versioned artifacts:

- resolved manual outcome packet
- paper hypothesis feedback
- source accuracy feedback
- manual feedback packet
- source learning update candidate
- safety scan

The original 014 unresolved packet remains preserved.
