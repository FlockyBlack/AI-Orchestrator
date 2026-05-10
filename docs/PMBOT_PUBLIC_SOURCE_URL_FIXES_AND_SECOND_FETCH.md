# PMBOT Public Source URL Fixes And Second Fetch

PRACTICAL-008 proved the controlled public read-only fetch path could run with a concrete manifest. PRACTICAL-009 replayed the one saved packet and diagnosed the four failed source requests. PRACTICAL-010 repairs those failed URL intents without browsing or search and then uses a scoped approval/preflight gate before any second public GET.

## Why Requests Failed

- UK Parliament page: HTTP 403 in the controlled fetcher.
- Elysee page: local certificate-chain validation failure.
- Kraken page: redirect blocked from `https://www.kraken.com/blog` to `https://blog.kraken.com/`.
- MicroStrategy page: HTTP 403 in the controlled fetcher.

## URL Repair Strategy

- Use only local PRACTICAL-008/PRACTICAL-009 artifacts and the curated manual fixture.
- Retry or replace only when a concrete public URL is already known locally.
- Keep missing, no-retry, and blocked source intents non-executable.
- Do not browse, search, crawl, or call APIs during repair.

## Repaired Manifest Result

- Executable repaired requests: 1
- No-retry requests: 1
- Replacement-missing requests: 1
- Blocked requests: 1

## Second Fetch Preflight

- Ready: `true`
- Blockers: none

## Second Fetch Result

- Live fetch occurred: `true`
- Attempted: 1
- Succeeded: 1
- Failed: 0
- Evidence packets created: 1

## Replay Result

- Replay status: `replayed_saved_public_evidence`
- Replay performed: `true`

## Source Accessibility Learning

- 010 records: 4
- No autonomous training was performed.
- No real trade decision was made.

## What This Proves

- Failed source URLs can be repaired deterministically from local artifacts and a curated fixture.
- The approval, safety, preflight, fetch, save, replay, and operator-review loop remains bounded and auditable.

## What This Does Not Prove

- It does not prove the market outcome.
- It does not prove PMBOT is ready for autonomous trading.
- It does not permit automatic analysis updates or executable market actions.

## Next Action

- Operator review should inspect any evidence packet created by the second fetch.
