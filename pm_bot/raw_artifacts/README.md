# PM Bot Raw Artifacts

This package provides a deterministic offline validation gate for local raw market artifact fixtures.

It accepts only local JSON files, validates the raw artifact contract, and produces quarantine findings for malformed, stale, conflicting, and unsafe artifacts before any future normalization or replay flow could consume them.

What this package does:

- validates fixture-only raw market artifacts
- rejects stale, malformed, conflicting, and unsafe artifacts
- emits a deterministic JSON validation report
- stays local-only and standard-library-only

What this package does not do:

- no network or API calls
- no live Polymarket integration
- no credentials
- no wallet handling
- no order or trading flow
- no runtime wiring
