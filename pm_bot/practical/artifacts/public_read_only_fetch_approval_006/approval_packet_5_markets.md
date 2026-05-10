# PMBOT Public Read-Only Fetch Approval Packet

## Approval packet summary

- Approval packet ID: `public-read-only-fetch-approval-006-5-markets`
- Source task: `ORCH-PMBOT-PRACTICAL-005-CONTROLLED-PUBLIC-READ-ONLY-FETCH-PREP-FOR-MARKET-PACKETS`
- Markets: 5
- Max requests: 10
- Operator approval required: `true`
- Operator approval granted: `false`
- Ready for controlled public fetch: `false`
- Live fetch performed: `false`

## Markets included

- `563650` SCOTUS accepts sports event contract case by July 31, 2026?
- `597964` Macron out by June 30, 2026?
- `598936` Will the next UK election be called by June 30, 2026?
- `691547` Kraken IPO by December 31, 2026?
- `692258` MicroStrategy sells any Bitcoin by June 30, 2026?

## What would be fetched later

- `563650` `public_market_metadata_endpoint_placeholder`
  Source: public market metadata endpoint placeholder
  Evidence: public market metadata snapshot
  Why needed: Fresh public metadata would help verify that the saved local packet still matches public market terms before replay.
- `563650` `public_court_government_page_placeholder`
  Source: public court/government page placeholder
  Evidence: official docket or resolution page snapshot
  Why needed: The paper hypothesis depends on later checking whether public court records support the saved local packet.
- `597964` `public_market_metadata_endpoint_placeholder`
  Source: public market metadata endpoint placeholder
  Evidence: public market metadata snapshot
  Why needed: Fresh public metadata would help verify that the saved local packet still matches public market terms before replay.
- `597964` `public_resolution_source_page_placeholder`
  Source: public resolution source page placeholder
  Evidence: public official status or resolution page snapshot
  Why needed: The paper hypothesis depends on later checking public status evidence against the saved local packet.
- `598936` `public_market_metadata_endpoint_placeholder`
  Source: public market metadata endpoint placeholder
  Evidence: public market metadata snapshot
  Why needed: Fresh public metadata would help verify that the saved local packet still matches public market terms before replay.
- `598936` `public_court_government_page_placeholder`
  Source: public government or parliament page placeholder
  Evidence: public election or parliament page snapshot
  Why needed: The paper hypothesis depends on later checking public election timing evidence against the saved local packet.
- `691547` `public_market_metadata_endpoint_placeholder`
  Source: public market metadata endpoint placeholder
  Evidence: public market metadata snapshot
  Why needed: Fresh public metadata would help verify that the saved local packet still matches public market terms before replay.
- `691547` `public_exchange_company_announcement_page_placeholder`
  Source: public exchange/company announcement page placeholder
  Evidence: public listing or company announcement snapshot
  Why needed: The paper hypothesis depends on later checking public listing or company announcement evidence against the saved local packet.
- `692258` `public_market_metadata_endpoint_placeholder`
  Source: public market metadata endpoint placeholder
  Evidence: public market metadata snapshot
  Why needed: Fresh public metadata would help verify that the saved local packet still matches public market terms before replay.
- `692258` `public_issuer_company_news_page_placeholder`
  Source: public issuer/company news page placeholder
  Evidence: public issuer news or filing summary snapshot
  Why needed: The paper hypothesis depends on later checking public company evidence against the saved local packet.

## What will not be fetched

- Authenticated endpoints
- Private API key endpoints
- Browser session, cookie, login, KYC, or bypass-based sources
- Wallet, private key, signing, custody, order, or trading paths
- OpenRouter calls
- Polymarket API calls
- Schedulers, daemons, watchers, automatic polling, or unattended automation
- Market recommendations or executable quantitative market output
- Runtime, dispatcher, run_codex, browser automation, or autonomous execution changes

## Limits

- Max requests: 10
- Timeout seconds: 10
- Retry policy: `{'backoff_seconds': 0, 'max_attempts': 0, 'reason': 'Retries are disabled for this local-only preparation task.', 'retry_enabled': False}`

## Evidence-save and replay plan

- Evidence save required: `true`
- Replay required before analysis update: `true`
- Request manifest ID: `public-read-only-fetch-prep-005-5-markets.request_manifest.006`
- Evidence save plan ID: `public-read-only-fetch-prep-005-5-markets.evidence_save_plan.006`
- Replay plan ID: `public-read-only-fetch-prep-005-5-markets.replay_before_update_plan.006`

## Operator checklist

- Review the five market IDs and titles.
- Review each request intent and source category.
- Confirm the maximum request count remains 10.
- Confirm evidence save is required before replay.
- Confirm replay is required before any analysis update.
- Confirm blocked scope remains blocked.
- If approval is later intended, update only the manual approval artifact in a separate explicit task.

## Current readiness: blocked until approval

- Operator approval has not been granted.
- Approval record does not enable live fetch after approval.

## Safety boundary

- Live fetch from this task.
- Any authenticated or credentialed source.
- Wallet, signing, custody, orders, or trading paths.
- Scheduler, daemon, watcher, automatic polling, or unattended background fetch.
- OpenRouter or Polymarket API calls.
- Market action recommendations or executable quantitative output.

## Future allowed task if approved

- `ORCH-PMBOT-PRACTICAL-007-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-EXECUTION-OPERATOR-APPROVED`
- Manual approval artifact required: `pm_bot/practical/artifacts/public_read_only_fetch_approval_006/manual_operator_approval_template.json`
