# PMBOT Batch Local Analysis

- Generated at: `2026-05-10T00:00:00Z`
- Processed: 1
- Skipped: 5

## Processed markets

- `synthetic-weather-rain-001` -> `pm_bot/practical/artifacts/night_002/batch_analysis/synthetic-weather-rain-001.analysis.result.json`

## Skipped items

- `queue-crypto-001`: status is analysis_ready
- `queue-politics-001`: status is hypothesis_active
- `queue-esports-001`: status is outcome_pending
- `queue-generic-001`: status is feedback_complete
- `queue-blocked-001`: status is blocked

## Safety boundary

- Finite local queue processing only.
- The original queue file is not modified unless an explicit output queue path is provided.
- No live fetch, external API, wallet, order, or trading action is used.
