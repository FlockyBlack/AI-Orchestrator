# PMBOT Public Source Registry

- Contract: `pmbot_public_source_registry.v1`
- Generated at: `2026-05-10T00:00:00Z`

## Allowed Source Categories

- `low_quality_forum_or_rumor_labeled_source`
  Reason: May be retained only when explicitly labeled low quality and not used as decisive evidence.
  Boundary: Low-quality context label only; never an executable market instruction.
- `public_court_government_page_placeholder`
  Reason: Future public court, government, parliament, or regulator page for official evidence.
  Boundary: Public official page only; no account, KYC, or session cookies.
- `public_exchange_company_announcement_page_placeholder`
  Reason: Future public exchange, listing, IPO, or company announcement page for evidence.
  Boundary: Public read-only announcement source only; no broker, order, or trading API.
- `public_issuer_company_news_page_placeholder`
  Reason: Future public issuer or company news page for source evidence.
  Boundary: Public web page only; no investor portal login or private API key.
- `public_market_metadata_endpoint_placeholder`
  Reason: Future public metadata lookup for market title, rules, status, and resolution terms.
  Boundary: Public read-only placeholder only; no authenticated or trading endpoint.
- `public_resolution_source_page_placeholder`
  Reason: Future public page used to capture outcome or resolution evidence.
  Boundary: Static public page capture only; no login, bypass, or private feed.
- `public_static_web_page_placeholder`
  Reason: Future public static web page used as a low-risk source reference.
  Boundary: Public static page only; no browser profile, cookies, or automation bypass.

## Blocked Source Categories

- `authenticated_endpoint`
  Reason: Requires identity, session, token, or account access.
  Boundary: Blocked for this public read-only preparation layer.
- `browser_session_cookie_based_source`
  Reason: Depends on browser profile state, session cookies, or logged-in context.
  Boundary: Browser sessions and cookies are not used.
- `forum_rumor_only_unlabeled_source`
  Reason: Rumor-only material is too weak unless explicitly labeled low quality.
  Boundary: Unlabeled rumor sources are blocked.
- `order_endpoint`
  Reason: Could create, cancel, or inspect executable order paths.
  Boundary: Order endpoints remain out of scope.
- `private_api_key_endpoint`
  Reason: Requires private credentials or API keys.
  Boundary: Credentials are not required or used.
- `source_requiring_bypass_or_automation`
  Reason: Requires bypassing controls, bot detection, or automated interactive access.
  Boundary: Bypass and unattended automation are blocked.
- `source_requiring_kyc_or_login`
  Reason: Requires KYC, login, or account identity.
  Boundary: Login and KYC sources are blocked.
- `trading_endpoint`
  Reason: Could expose execution or market-taking behavior.
  Boundary: Trading endpoints remain out of scope.
- `wallet_signing_endpoint`
  Reason: Touches wallet, signing, private key, or custody boundaries.
  Boundary: Wallet and signing paths remain out of scope.

## Rules

- Allowed categories are placeholders for future public read-only sources.
- Blocked categories must not be used in fetch plans.
- No source category may require auth, credentials, wallet access, signing, orders, trading, KYC, cookies, or bypass automation.
- Forum or rumor-only material is blocked unless explicitly labeled low quality.

## Safety Boundary

- Registry validation only; no network calls, browser sessions, credentials, wallet access, orders, or trading actions.
