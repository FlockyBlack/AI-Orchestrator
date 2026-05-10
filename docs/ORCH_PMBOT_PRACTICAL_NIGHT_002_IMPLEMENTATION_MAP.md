# ORCH PMBOT Practical Night 002 Implementation Map

## Existing PRACTICAL-001 capabilities

- `pm_bot/practical/one_market_analysis.py`: validates local `pmbot_one_market_input.v1` packets, produces one-market JSON/Markdown cards, source attribution, stale/contradiction notes, and a paper-only hypothesis record.
- `pm_bot/practical/paper_feedback.py`: compares a local analysis result with a local outcome record, labels analysis quality, and records source contribution labels.
- `pm_bot/practical/source_learning.py`: aggregates feedback results into a transparent source learning ledger with no autonomous training.
- `pm_bot/tests/fixtures/practical_one_market/`: one-market inputs and outcome records for aligned, unresolved, stale, contradictory, and missing-evidence cases.
- `pm_bot/practical/artifacts/`: PRACTICAL-001 sample analysis, feedback, and source-learning artifacts.

## Night 002 additions

- Local queue handling: `market_queue.py` loads queue fixtures, validates items, counts statuses, detects missing linked artifacts, and computes next operator actions.
- Local packet import: `local_market_packet_import.py` normalizes seed/raw packets into `pmbot_one_market_input.v1` without fetching.
- Batch analysis and feedback: `batch_local_analysis.py` and `batch_paper_feedback.py` process finite local queues and exit.
- Active tracking: `active_paper_hypotheses.py` and `outcome_check_queue.py` show unresolved paper hypotheses and outcome checks.
- Operator surfaces: `operator_console.py`, `practical_dashboard_index.py`, and `operator_next_actions_5.*` summarize what the operator should inspect next.
- Source learning surfaces: `source_learning_batch.py`, `source_scorecard.py`, and `analysis_quality_summary.py` aggregate feedback into practical source and analysis-quality views.
- Safety scanning: `practical_safety_scan.py` scans selected local artifacts for unsafe action wording and unsafe artifact flags.
- Fixtures: `pm_bot/tests/fixtures/practical_market_queue_batch/` contains synthetic weather-like, crypto-like, politics-like, esports-like, and generic event-resolution samples.

## Safety boundaries preserved

- No scheduler, daemon, watcher, background worker, or autonomous loop.
- No OpenRouter, Polymarket API, authenticated endpoint, wallet, order, signing, or real-money path.
- No runtime, dispatcher, browser automation, or autonomous execution path changes.
- Paper hypotheses are non-executable analysis-quality tracking records only.
