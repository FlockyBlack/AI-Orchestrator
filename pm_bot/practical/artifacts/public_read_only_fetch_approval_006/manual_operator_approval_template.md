# Manual Operator Approval Template

- Approval for task: `ORCH-PMBOT-PRACTICAL-007-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-EXECUTION-OPERATOR-APPROVED`
- Approval status: `pending`
- Operator must set manually: `true`
- Approved by: `None`
- Approved at: `None`
- Approved max requests: 10

## Approved Markets

- `563650`
- `597964`
- `598936`
- `691547`
- `692258`

## Approved Source Categories

- `public_court_government_page_placeholder`
- `public_exchange_company_announcement_page_placeholder`
- `public_issuer_company_news_page_placeholder`
- `public_market_metadata_endpoint_placeholder`
- `public_resolution_source_page_placeholder`

## Blocked Source Categories

- `authenticated_endpoint`
- `browser_session_cookie_based_source`
- `forum_rumor_only_unlabeled_source`
- `order_endpoint`
- `private_api_key_endpoint`
- `source_requiring_bypass_or_automation`
- `source_requiring_kyc_or_login`
- `trading_endpoint`
- `wallet_signing_endpoint`

## Required Acknowledgements

- I reviewed the approval packet and request manifest.
- I approve only the listed markets, request count, and source categories.
- No auth, credentials, cookies, wallet, signing, orders, trading, scheduler, or polling are approved.
- Evidence must be saved before replay.
- Replay must happen before any analysis update.

## Non-Approval Notice

This template is pending and does not grant approval until a future separate operator action changes approval_status to approved with approved_by and approved_at.
