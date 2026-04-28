# PM Bot Read-Only Fetcher Failure Modes V1

## Status

PMBOT-BATCH-008 defines failure handling only. It does not implement a fetcher or any live API behavior.

## Failure Modes

### API unavailable

- Future behavior: stop capture, emit a deterministic failure record, and produce no replay import.
- Required response: no direct execution response.

### Malformed payload

- Future behavior: quarantine the snapshot as malformed.
- Required response: block normalization and replay import.

### Stale data

- Future behavior: quarantine the snapshot when freshness limits are exceeded.
- Required response: no direct execution response.

### Missing market status

- Future behavior: quarantine because open, closed, halted, and resolved states cannot be trusted.
- Required response: require manual review before any contract change.

### Wrong outcome mapping

- Future behavior: quarantine when outcome order or semantic mapping cannot be proved.
- Required response: block replay import to avoid paper replay distortion.

### Price and liquidity contradiction

- Future behavior: quarantine when prices or liquidity fields fail consistency checks.
- Required response: no direct execution response.

### Duplicate snapshot

- Future behavior: quarantine or de-duplicate according to approved deterministic policy.
- Required response: do not import duplicate research inputs.

### Resolved market returned as active

- Future behavior: quarantine because market status is unsafe for replay assumptions.
- Required response: require manual review.

### Rate limit

- Future behavior: stop the capture batch and emit a non-executing failure record.
- Required response: no retry policy without explicit approval.

### Partial capture

- Future behavior: quarantine incomplete payloads and block normalization completion.
- Required response: no direct execution response.

### Schema drift

- Future behavior: quarantine the payload and freeze parser expansion until contracts are reviewed.
- Required response: revert to fixture-only validation until approved.

## Quarantine Handling

- Every malformed, stale, partial, contradictory, duplicate, or drifted snapshot must generate a quarantine record.
- Quarantined data must not enter paper replay import.
- Quarantine must not trigger any live trade path, watchlist execution path, or runtime mutation path.

## Execution Boundary

- No failure mode may trigger order creation, live trading, wallet access, or runtime wiring.
- The only allowed downstream behavior is static reporting, quarantine, and paper replay import after validation.
