# PMBOT Scoped Public Read-Only Fetch Approval 007

- Contract: `pmbot_scoped_public_read_only_fetch_approval.v1`
- Approval ID: `operator-scoped-public-fetch-007`
- Approval status: `approved_for_scoped_public_read_only_fetch_only`
- Approval for task: `ORCH-PMBOT-PRACTICAL-007-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-EXECUTION-OPERATOR-APPROVED`
- Approved by: `operator`
- Approved at: `2026-05-10T12:44:03Z`
- Reusable: `false`
- Expires after task: `true`

## Approved Scope

- Finite public read-only fetch only.
- Maximum request count: `5`
- Approved market IDs: `563650`, `597964`, `598936`, `691547`, `692258`
- Save evidence before use: `true`
- Replay before analysis update: `true`
- No authentication, API keys, wallet access, orders, trading, scheduler, background worker, or browser automation.

## Blocked Scope

- Authenticated endpoints
- Trading endpoints
- Order endpoints
- Wallet/signing/private key access
- OpenRouter
- Market recommendations
- Probability/EV/edge/side-selection as blocked trading-signal category
- Autonomous execution
- Polling/scheduler/background worker

## Safety Boundary

This approval exists only for the exact finite public read-only fetch execution task. It does not approve broad source discovery, browser automation, authenticated access, wallet/signing paths, order paths, trading paths, schedulers, background workers, market action recommendations, or executable quantitative market output.
