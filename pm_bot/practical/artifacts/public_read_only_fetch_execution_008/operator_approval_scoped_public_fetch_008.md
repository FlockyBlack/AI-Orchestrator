# PMBOT PRACTICAL-008 Scoped Public Fetch Approval

- Approval ID: `operator-scoped-public-fetch-008-20260510`
- Task: `ORCH-PMBOT-PRACTICAL-008-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-EXECUTION-WITH-CONCRETE-URL-MANIFEST`
- Status: `approved_for_scoped_public_read_only_fetch_only`
- Manifest: `pm_bot/practical/artifacts/public_read_only_fetch_url_enrichment_007b/enriched_fetch_request_manifest.json`
- Max requests: 5
- Method allowed: `GET`
- Approved request intents: 5
- Approved markets: `563650`, `597964`, `598936`, `691547`, `692258`

## Safety Scope

- Public HTTP(S) GET only.
- No authentication, API keys, cookies, browser automation, wallet access, orders, or trading.
- Evidence must be saved before replay or review use.
- Automatic analysis update is not allowed.
- This approval is non-reusable and expires after this task.

## Blocked Scope

- OpenRouter calls
- authenticated endpoints
- API keys, cookies, browser profiles, and browser automation
- wallets, private keys, signing, order placement, and trading endpoints
- POST, PUT, PATCH, DELETE, request bodies, crawling, search, or arbitrary link following
- scheduler, daemon, background worker, polling loop, autonomous execution, run-codex-once, and run-codex-batch
- runtime, dispatcher, run_codex, wallet, order, or trading execution path changes
- automatic market analysis mutation and executable market action output
- disallowed probability, EV, edge, confidence, or side-selection output category
