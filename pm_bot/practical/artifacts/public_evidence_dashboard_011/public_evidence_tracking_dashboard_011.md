# PMBOT Public Evidence Tracking Dashboard

- Dashboard ID: `public-evidence-tracking-dashboard-011`
- Tracked markets: 5
- Public evidence packets: 2
- Pending update candidates: 1
- Unresolved outcomes: 5

## Tracked Markets

- `563650` - SCOTUS accepts sports event contract case by July 31, 2026?
- `597964` - Macron out by June 30, 2026?
- `598936` - Will the next UK election be called by June 30, 2026?
- `691547` - Kraken IPO by December 31, 2026?
- `692258` - MicroStrategy sells any Bitcoin by June 30, 2026?

## Active Paper Hypotheses

- `563650.analysis.adc53630aa1f.paper_hypothesis` - Track whether the local source-backed analysis remains useful after the market outcome is reviewed.
- `597964.analysis.33643849e5db.paper_hypothesis` - Track whether the local source-backed analysis remains useful after the market outcome is reviewed.
- `598936.analysis.dceea0f50063.paper_hypothesis` - Track whether the local source-backed analysis remains useful after the market outcome is reviewed.
- `691547.analysis.56b3a68b9b94.paper_hypothesis` - Track whether the local source-backed analysis remains useful after the market outcome is reviewed.
- `692258.analysis.bed289c1494d.paper_hypothesis` - Track whether the local source-backed analysis remains useful after the market outcome is reviewed.

## Public Evidence Collected

- `public_fetch_008_563650_public_fetch_request_intent_006_02_563650_563650_domain_public_evidence_a6d1969391feeee9` -> market `563650` via public court/government page placeholder
- `public_fetch_010_public_fetch_request_intent_006_08_691547_691547_domain_public_evidence_293c511e51a6fac6` -> market `691547` via public exchange/company announcement page placeholder

## Evidence Links

- `public_fetch_008_563650_public_fetch_request_intent_006_02_563650_563650_domain_public_evidence_a6d1969391feeee9` -> `563650` -> `563650.analysis.adc53630aa1f.paper_hypothesis`
- `public_fetch_010_public_fetch_request_intent_006_08_691547_691547_domain_public_evidence_293c511e51a6fac6` -> `691547` -> `691547.analysis.56b3a68b9b94.paper_hypothesis`

## Pending Paper Update Candidates

- `paper-hypothesis-update-candidate-009` for market `563650`

## Source Status Board

- Reachable: 2
- Failed or blocked: 3
- Repaired: 1

## Source Repair Summary

- source_url_repair_result_summary_path: pm_bot/practical/artifacts/public_source_url_fixes_010/source_url_repair_result_summary_010.json
- repaired_executable_count: 1
- no_retry_count: 1
- replacement_missing_count: 1
- blocked_count: 1
- second_fetch_succeeded: 1
- second_fetch_failed: 0

## Outcome Feedback Pending

- `563650` - unresolved
- `597964` - unresolved
- `598936` - unresolved
- `691547` - unresolved
- `692258` - unresolved

## Next Operator Actions

- Review the pending paper update candidate in a later operator-approved paper task.
- Use the source URL backlog for manual URL collection before any future scoped public-source task.
- Keep all five outcomes unresolved until saved resolution evidence is available.

## Safety Boundary

- Dashboard merge only; no new live public fetch was performed.
- Original paper hypotheses and unresolved outcome records were not overwritten.
- No autonomous trading, scheduler, daemon, background worker, or polling loop was created.
