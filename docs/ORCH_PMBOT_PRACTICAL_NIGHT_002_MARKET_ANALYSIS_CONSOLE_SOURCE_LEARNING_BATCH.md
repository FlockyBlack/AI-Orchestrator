# ORCH PMBOT Practical Night 002 Market Analysis Console Source Learning Batch

## Summary

This batch shifts PMBOT from abstract readiness work into a concrete local operator workflow for practical analysis-quality testing. It adds a market queue, local packet import, batch analysis, active paper-hypothesis tracking, outcome checks, paper feedback batching, source learning aggregation, source scorecards, analysis quality summaries, an operator console, dashboard index, and a practical safety scanner.

## Why this batch exists

The operator needs to see whether PMBOT analysis is useful on concrete markets before any controlled live read-only work is considered. Night 002 makes the loop inspectable with local synthetic markets and deterministic artifacts.

## Relation to PRACTICAL-001

PRACTICAL-001 created one-market analysis, paper feedback, and source-learning ledger primitives. Night 002 composes those primitives into a multi-market queue and operator workflow.

## Modules created

- `pm_bot/practical/practical_io.py`
- `pm_bot/practical/market_queue.py`
- `pm_bot/practical/local_market_packet_import.py`
- `pm_bot/practical/active_paper_hypotheses.py`
- `pm_bot/practical/outcome_check_queue.py`
- `pm_bot/practical/batch_local_analysis.py`
- `pm_bot/practical/batch_paper_feedback.py`
- `pm_bot/practical/source_learning_batch.py`
- `pm_bot/practical/source_scorecard.py`
- `pm_bot/practical/analysis_quality_summary.py`
- `pm_bot/practical/operator_console.py`
- `pm_bot/practical/practical_dashboard_index.py`
- `pm_bot/practical/practical_safety_scan.py`

## CLI commands added

- `python -m pm_bot.practical.market_queue --queue ... --out-json ... --out-md ...`
- `python -m pm_bot.practical.local_market_packet_import --input ... --out-json ... --out-md ...`
- `python -m pm_bot.practical.active_paper_hypotheses --queue ... --out-json ... --out-md ...`
- `python -m pm_bot.practical.outcome_check_queue --queue ... --out-json ... --out-md ...`
- `python -m pm_bot.practical.batch_local_analysis --queue ... --out-dir ... --out-summary-json ... --out-summary-md ...`
- `python -m pm_bot.practical.batch_paper_feedback --queue ... --out-dir ... --out-summary-json ... --out-summary-md ...`
- `python -m pm_bot.practical.source_learning_batch --queue ... --out-json ... --out-md ...`
- `python -m pm_bot.practical.source_scorecard --ledger ... --out-json ... --out-md ...`
- `python -m pm_bot.practical.analysis_quality_summary --feedback-dir ... --out-json ... --out-md ...`
- `python -m pm_bot.practical.operator_console --queue ... --out-json ... --out-md ...`
- `python -m pm_bot.practical.practical_dashboard_index --artifact-dir ... --out-json ... --out-md ...`
- `python -m pm_bot.practical.practical_safety_scan --artifact-dir ... --out-json ... --out-md ...`

## Sample artifacts generated

Night 002 artifacts live under `pm_bot/practical/artifacts/night_002/` and include queue summaries, active hypotheses, operator console, packet import sample, batch analysis summary, outcome queue, batch feedback summary, source learning batch, source scorecard, analysis quality summary, safety scan, dashboard index, and operator next actions.

## Tests run

- `python -m compileall ai_orchestrator pm_bot tests`
- Practical pytest suite listed in `docs/ORCH_PMBOT_PRACTICAL_NIGHT_002_RESULT.json`
- Required JSON validation commands
- `git diff --check`
- `git diff --cached --check`

## What this proves

- PMBOT can run a finite local multi-market analysis-quality workflow.
- Queue state, active paper hypotheses, outcome checks, feedback state, source learning, blockers, and next practical actions are visible in JSON/Markdown.
- Synthetic source labels cover useful, stale, misleading, contradictory, insufficient, and unknown cases.
- The practical artifacts pass the local no-trading safety scan.

## What this does not prove

- It does not prove live market fetching is safe.
- It does not prove analysis quality on real markets.
- It does not prove readiness for autonomous operation.
- It does not prove readiness for wallet, order, signing, or real-money workflows.

## How this helps real analysis

The operator can now import a local packet, run one-market or batch analysis, track active paper hypotheses, add local outcome records, run feedback, inspect which sources helped or failed, and see a concise next-action surface before any live data is introduced.

## Remaining gap before controlled public read-only fetch

- Add an explicit public read-only fetch contract.
- Add source allowlists and provenance capture.
- Add saved evidence bundle validation.
- Add tests proving no authenticated, wallet, order, or runtime path can be reached.

## Remaining gap before real trading

Real trading remains out of scope. It would require separate human-approved work for safety, custody, signing, compliance, operational monitoring, and risk controls. Night 002 does not implement or imply any such readiness.

## Next recommended action

`ORCH-PMBOT-PRACTICAL-003-REAL-MARKET-LOCAL-PACKET-IMPORT-AND-ANALYSIS-RUN`
