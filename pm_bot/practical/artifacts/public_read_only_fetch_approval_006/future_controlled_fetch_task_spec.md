# Future Controlled Public Read-Only Fetch Task Spec

- Proposed task: `ORCH-PMBOT-PRACTICAL-007-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-EXECUTION-OPERATOR-APPROVED`
- Prerequisite task: `ORCH-PMBOT-PRACTICAL-006-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-DRY-RUN-APPROVAL-PACKET`
- Manual approval required: `true`
- Approval artifact required: `pm_bot/practical/artifacts/public_read_only_fetch_approval_006/manual_operator_approval_template.json`
- Max markets: 5
- Max requests: 10

## Allowed Scope

- finite public read-only fetches only
- no auth
- no wallet
- no trading
- no orders
- no scheduler
- no automatic polling
- save evidence before use
- replay evidence before analysis update

## Blocked Scope

- Authenticated endpoints
- Private API key endpoints
- Browser session, cookie, login, KYC, or bypass-based sources
- Wallet, private key, signing, custody, order, or trading paths
- OpenRouter calls
- Polymarket API calls
- Schedulers, daemons, watchers, automatic polling, or unattended automation
- Market recommendations or executable quantitative market output
- Runtime, dispatcher, run_codex, browser automation, or autonomous execution changes

## Expected Outputs

- saved public evidence packet JSON and Markdown per request intent
- request execution summary with public-source capture metadata
- replay-ready source packet mapping
- post-fetch safety scan showing no auth, wallet, order, trading, scheduler, or OpenRouter/Polymarket API use

## Stop Conditions

- approval artifact missing or still pending
- source requires auth, login, cookies, private API key, wallet, signing, or KYC
- source category is not in the approved source category set
- request count would exceed the approved maximum
- evidence cannot be saved before replay
- operator asks for broad unrestricted fetch scope
