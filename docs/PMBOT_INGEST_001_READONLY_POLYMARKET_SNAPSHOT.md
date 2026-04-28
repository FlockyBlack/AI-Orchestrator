# PMBOT INGEST 001 Read-Only Polymarket Snapshot

## Scope

This tool is a standalone, manually invoked capture step for public Polymarket market data. It is read-only and isolated under `pm_bot/ingest`.

Allowed:

- public Polymarket Gamma markets data
- public Polymarket Gamma events data with nested markets
- active, non-closed market query parameters
- local raw snapshot artifacts
- local validation reports
- quarantine of malformed captures

Forbidden:

- credentials or API keys
- wallet or private key access
- authenticated CLOB endpoints
- trading endpoints
- order placement or cancellation
- scoring, paper execution, recommendations, probabilities, expected value, side selection, or market decisions
- dispatcher, runtime, prompt automation, `run_codex`, task state, or run state wiring

## Manual Capture

Run from the repository root:

```powershell
python pm_bot\ingest\capture_polymarket_readonly_snapshot.py --source events --limit 25
```

The default source is `events`, which uses:

```text
https://gamma-api.polymarket.com/events?active=true&closed=false&limit=...
```

The default limit is conservative. The script clamps `--limit` to `1..100` and uses `active=true&closed=false`.

To preserve the original markets path explicitly:

```powershell
python pm_bot\ingest\capture_polymarket_readonly_snapshot.py --source markets --limit 25
```

The markets source uses:

```text
https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=...
```

## Output

When validation passes, the raw artifact is written under:

```text
pm_bot/ingest/raw_snapshots/
```

The artifact contains:

- `fetched_at`
- source URL and method metadata
- source name metadata: `polymarket_gamma_events` or `polymarket_gamma_markets`
- public read-only network boundary flags
- the raw provider payload
- a SHA-256 hash of the raw payload
- deterministic normalized summary fields for offline inspection
- validation status

When validation fails, the artifact and validation report are written under:

```text
pm_bot/ingest/quarantine/
```

Quarantined data is not connected to research, scoring, paper, runtime, or any downstream PMBOT flow by this task.

For events payloads, the normalized summary stays shallow and does not flatten markets into downstream records. It records event count, nested market count, and active non-closed nested market count for offline validation only.

## Offline Validation

Validate any captured artifact manually:

```powershell
python pm_bot\ingest\validate_polymarket_raw_snapshot.py pm_bot\ingest\raw_snapshots\<artifact>.json
```

Tests use only local fixtures and mocks. They do not require live network access.
