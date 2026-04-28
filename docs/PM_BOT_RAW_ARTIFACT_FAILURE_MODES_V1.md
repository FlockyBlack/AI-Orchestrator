# PM Bot Raw Artifact Failure Modes V1

## Scope

This document defines offline failure modes for raw market artifacts before any future normalization or replay flow can consume them.

## Failure modes

- stale snapshot: `captured_at` falls outside the deterministic freshness window and is quarantined
- malformed artifact: root payload is not an object or nested sections are not objects or lists as required
- missing required fields: required top-level, market, provenance, or safety fields are missing
- invalid prices: outcome prices are non-numeric or outside the accepted `[0, 1]` range
- invalid outcome sides: outcome sides violate the lowercase deterministic side format
- conflicting outcomes: duplicate outcome names or duplicate sides appear in one artifact
- unsafe safety flags: any safety flag claims network use, credentials use, wallet use, order capability, or trading capability
- provenance missing or unclear: collector, collection method, or source reference is absent or blank
- future live-source ambiguity: an artifact claims future fetcher provenance but still lacks the same offline-safe contract guarantees
- replay contamination: malformed or unsafe artifacts are blocked before they can contaminate normalization or replay inputs
- runtime wiring attempt: artifacts do not authorize any dispatcher, runtime, or orchestration mutation path
- network or API leakage: any artifact that claims network use is quarantined immediately
- wallet, order, or trading leakage: any artifact that claims wallet use or order/trading capability is quarantined immediately
