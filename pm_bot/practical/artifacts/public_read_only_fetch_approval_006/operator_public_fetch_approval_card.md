# Operator Public Fetch Approval Card

- Current status: not approved
- Max requests: 10
- Evidence save required: `true`
- Replay required: `true`
- Approval artifact to change manually later: `pm_bot/practical/artifacts/public_read_only_fetch_approval_006/manual_operator_approval_template.json`

## Markets Covered

- `563650` SCOTUS accepts sports event contract case by July 31, 2026?
- `597964` Macron out by June 30, 2026?
- `598936` Will the next UK election be called by June 30, 2026?
- `691547` Kraken IPO by December 31, 2026?
- `692258` MicroStrategy sells any Bitcoin by June 30, 2026?

## What Would Be Fetched Later

- `public_court_government_page_placeholder`: 2
- `public_exchange_company_announcement_page_placeholder`: 1
- `public_issuer_company_news_page_placeholder`: 1
- `public_market_metadata_endpoint_placeholder`: 5
- `public_resolution_source_page_placeholder`: 1

## What Is Blocked

- Authenticated endpoints
- Private API key endpoints
- Browser session, cookie, login, KYC, or bypass-based sources
- Wallet, private key, signing, custody, order, or trading paths
- OpenRouter calls
- Polymarket API calls
- Schedulers, daemons, watchers, automatic polling, or unattended automation
- Market recommendations or executable quantitative market output
- Runtime, dispatcher, run_codex, browser automation, or autonomous execution changes

## Operator Must Review

- `approval_packet_5_markets.md`
- `fetch_request_manifest_5_markets.md`
- `evidence_save_plan_5_markets.md`
- `replay_before_update_plan_5_markets.md`
- `future_controlled_fetch_task_spec.md`
- `approval_blocker_scenarios.md`

## Next Safe Action

Review the packet. A future controlled public read-only fetch task is allowed only after manual approval.
