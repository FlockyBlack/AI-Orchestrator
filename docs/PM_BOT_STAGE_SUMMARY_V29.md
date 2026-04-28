# PM Bot Stage Summary V29

Status: `local_snapshot_file_lifecycle_input_ready_for_review`

`PMBOT-BRAIN-017-LOCAL-SNAPSHOT-FILE-LIFECYCLE-INPUT` adds an optional local JSON input path to the existing live-shaped snapshot paper lifecycle command.

Default fixture mode remains unchanged:

```powershell
python pm_bot\paper\run_live_shaped_snapshot_paper_lifecycle.py
```

Explicit local snapshot mode:

```powershell
python pm_bot\paper\run_live_shaped_snapshot_paper_lifecycle.py --snapshot pm_bot\scoring\crypto_numeric_live_shaped_snapshot_fixture.v1.json
```

Markdown still works:

```powershell
python pm_bot\paper\run_live_shaped_snapshot_paper_lifecycle.py --markdown
```

## Input Scope

- `--snapshot <path>` reads a local JSON file only
- input must be a JSON object
- input must contain a `markets` list
- each `markets[]` entry must be a JSON object
- missing path, directory path, invalid JSON, or invalid shape exits cleanly with code 2
- per-market validation and rejection reasons remain in the existing live-shaped adapter and intake lifecycle paths

## Current Fixture Summary

- default fixture still passes: true
- explicit snapshot file passes: true
- markdown still passes: true
- invalid snapshot path fails cleanly: true
- lifecycle regression gates still pass: true

## Safety Boundary

- offline-only
- paper-only
- no live fetcher implemented
- no network/API
- no credentials
- no wallet/private keys/signing
- no real orders
- no live trading
- no runtime wiring
- no dispatcher/run_codex
- no prompt automation

## Verification

- `python -m pytest pm_bot\scoring\tests pm_bot\paper\tests -q`
- `python pm_bot\paper\run_live_shaped_snapshot_paper_lifecycle.py`
- `python pm_bot\paper\run_live_shaped_snapshot_paper_lifecycle.py --markdown`
- `python pm_bot\paper\run_live_shaped_snapshot_paper_lifecycle.py --snapshot pm_bot\scoring\crypto_numeric_live_shaped_snapshot_fixture.v1.json`
- `python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py`

## Next Step

Add small documented examples of acceptable local snapshot JSON shapes and expected rejection behavior for manual operator review.
