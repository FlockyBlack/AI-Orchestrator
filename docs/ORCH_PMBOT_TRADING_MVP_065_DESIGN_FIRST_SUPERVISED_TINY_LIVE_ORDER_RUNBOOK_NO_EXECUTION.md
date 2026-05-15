# ORCH-PMBOT-TRADING-MVP-065 Design First Supervised Tiny Live Order Runbook

## Purpose

This document defines the design and operator runbook for a future first supervised tiny live order task. It is documentation-only. It does not implement live execution, signing, wallet connection, order submission, cancellation, authenticated trading calls, runtime code, schedulers, daemons, background loops, or autonomous repetition.

The runbook exists to make one future action reviewable before any separately approved implementation task:

```text
Can an operator-supervised one-shot BTC tiny-momentum live order be prepared, signed, submitted, captured, reconciled, and cancelled or failed closed under a max notional of 1.00 USD, without exposing credentials or enabling autonomous live trading?
```

This 065 design is not authorization to place an order. It is not a trading recommendation, market recommendation, probability estimate, edge estimate, EV estimate, side-selection signal, or instruction to use real funds.

## Hard Scope Boundary

This task is limited to the two documentation artifacts:

- `docs/ORCH_PMBOT_TRADING_MVP_065_DESIGN_FIRST_SUPERVISED_TINY_LIVE_ORDER_RUNBOOK_NO_EXECUTION.md`
- `docs/ORCH_PMBOT_TRADING_MVP_065_DESIGN_FIRST_SUPERVISED_TINY_LIVE_ORDER_RUNBOOK_NO_EXECUTION_RESULT.json`

This task must not add or modify:

- runtime Python modules
- operator runners
- tests that execute live behavior
- adapters, clients, connectors, or signer code
- artifact generators
- Telegram controls
- scheduler, daemon, background worker, or loop code
- credential, wallet, `.env`, browser profile, or auth-store files

Any future task that adds live code must be separately authorized and must treat this document as a checklist, not as execution approval.

## Preconditions Before Any Future 065 Implementation

All items in this section are mandatory. Missing, stale, ambiguous, or contradictory evidence is an abort condition.

### Accepted Upstream Gates

- 063 supervised live enablement gate accepted in `master`.
- 064 explicit live credentials readiness gate accepted in `master`.
- 064 must be an implementation or accepted gate record, not only a design document.
- 064 status must remain redacted, presence-only, and live-blocked.
- The latest `master` used for a future implementation must be inspected before work starts.
- The future implementation result must record `head_before` and `head_after`.

### Operator Surfaces

- Telegram review panels must be available and confirmed safe, or Telegram review panels must be explicitly marked optional in the operator approval packet.
- If Telegram is optional, the replacement review surface must be named and must be human-operated.
- Telegram absence must not silently bypass manual approval.
- Telegram forbidden-control regression checks must remain clean before live order work starts.

### Explicit Operator Authorization

- The operator must separately authorize the future 065 implementation task.
- The authorization must be captured before any signing, submission, cancellation, or authenticated trading boundary is crossed.
- The authorization must be exact-text matched, not inferred from a summary, issue title, branch name, or chat context.
- The authorization must be one-shot and must not persist across days, retries, markets, strategies, or later tasks.

### Risk And Kill Planning

- Risk limits must be confirmed in a review artifact before construction of a live order intent.
- The maximum notional must be less than or equal to `1.00 USD`.
- Maximum orders per UTC day must be exactly `1`.
- The order must be one-shot only. No autonomous repeat is allowed.
- No scheduler, daemon, background loop, unattended retry loop, or recurring automation is allowed.
- Kill switch plan must be reviewed.
- Cancel plan must be reviewed.
- Failure plan must be reviewed.
- Reconciliation plan must be reviewed.

## Required Operator Authorization Text

The future implementation must require this exact authorization text:

```text
I AUTHORIZE ORCH-PMBOT-TRADING-MVP-065 TO ATTEMPT ONE SUPERVISED TINY LIVE BTC TINY-MOMENTUM ORDER WITH MAX NOTIONAL 1.00 USD, MAX ORDERS TODAY 1, NO AUTONOMOUS REPEAT, NO SCHEDULER, NO DAEMON, NO BACKGROUND LOOP, AND I ACCEPT THE DOCUMENTED KILL, CANCEL, FAILURE, REDACTION, AND LEDGER REQUIREMENTS.
```

Authorization rules:

- Exact text is required.
- Case, punctuation, market, strategy, notional, order count, and no-loop clauses must match.
- BTC is the only default market scope.
- `tiny-momentum` is the only default strategy scope.
- Any other market requires a separate approved task.
- Any other strategy requires a separate approved task.
- Any notional above `1.00 USD` is forbidden.
- Any daily order cap above `1` is forbidden.
- Any automatic repeat, retry-as-new-order, scheduler, daemon, or background loop is forbidden.
- The authorization expires after one attempt boundary, one abort, one completed submission, one cancellation, or the end of the operator-approved day, whichever happens first.

The future implementation must refuse weaker text such as "approved", "go", "run it", "place the order", or any paraphrase.

## Credential Handling

Credential handling must remain isolated and redacted:

- Do not print secrets.
- Do not store secrets.
- Do not serialize secrets.
- Do not hash, truncate, prefix, suffix, mask-with-length, or otherwise fingerprint secret-looking values.
- Do not enumerate broad environment state.
- Do not read `.env` files.
- Do not inspect wallet files, browser profiles, credential stores, auth stores, shell history, or password managers.
- Do not expose raw private keys, mnemonics, seed phrases, auth tokens, API secret values, passphrases, signatures, or signed payload values.
- Do not include raw authorization headers, API keys, signed request headers, or raw response bodies in commit-safe artifacts.
- Any future signer boundary must be isolated from the order runbook layer.
- Any future signer code must never log raw key material, signing inputs that include secret material, signatures, signed payloads, or raw transport payloads.
- The signer boundary must return only redacted status and an operator-controlled handoff result needed for the next boundary.
- If a future implementation cannot prove that raw material was not emitted, the run must abort and the artifacts must be marked unsafe for commit.

Credential readiness from 064 is necessary but not sufficient for live execution. The future 065 implementation must not treat "credential markers present" as permission to sign, submit, cancel, or call authenticated endpoints.

## First Live Order Flow

Every step below must be written as a forced sequential gate. A failed or skipped step must stop the run. No step may be retried as a new live order without a new operator-approved task or a new exact authorization, depending on where the failure occurs.

### 1. Preflight

Required inputs:

- current branch and HEAD
- `master` acceptance evidence for 063
- `master` acceptance evidence for 064
- static safety invariant report with zero critical findings
- Telegram review panel status or explicit optional status
- risk limit packet
- kill switch plan
- cancel plan
- failure plan
- reconciliation plan
- operator approval packet placeholder

Required checks:

- `market=BTC`
- `strategy=tiny-momentum`
- `max_notional_usd <= 1.00`
- `max_orders_per_day = 1`
- `orders_already_attempted_today = 0`
- no autonomous repeat flag
- no scheduler flag
- no daemon flag
- no background loop flag
- no live execution without exact operator authorization
- no unredacted credential or response artifact path

The preflight output must be commit-safe and must set `allowed_for_live=false` until exact operator authorization is captured.

### 2. Operator Confirmation

The future implementation must render a human-readable approval packet before constructing any signable or submittable payload. The packet must include:

- task ID
- market
- strategy
- max notional
- max orders today
- one-shot scope
- no autonomous repeat statement
- no scheduler, daemon, or background loop statement
- risk packet reference
- kill switch reference
- cancel plan reference
- failure plan reference
- redaction policy references
- exact authorization text

The operator confirmation gate must fail unless the captured text exactly matches the required authorization text. Approval from Telegram is acceptable only if the Telegram surface has no forbidden live-control regression and stores no secret material.

### 3. Order Construction

Order construction is the first future step that may create an intent that resembles a live order. It must still be non-secret until the signing boundary.

The live order intent snapshot must include:

- task ID
- market scope `BTC`
- strategy scope `tiny-momentum`
- notional cap `1.00 USD`
- requested notional
- order type
- side as operator-reviewed intent, not recommendation text
- price or limit parameters
- time-in-force or expiry
- source evidence references
- risk packet reference
- operator authorization reference
- construction timestamp
- non-executability flag before signing

It must not include:

- private keys
- signatures
- signed payloads
- auth headers
- raw response bodies
- fake fills
- fake PnL
- fake balances
- fake positions
- unreviewed market or strategy substitutions

Order construction must abort if the strategy tries to compute or present real trading advice beyond the operator-approved tiny intent.

### 4. Signing Boundary

The signing boundary must be isolated from the runbook/orchestrator layer. The runbook layer may request signing only after exact operator authorization and successful preflight.

Required signing boundary controls:

- signer boundary starts disabled by default
- signer boundary is unavailable unless exact authorization is present
- signer boundary receives only the minimum order payload needed for signing
- signer boundary does not log raw material
- signer boundary does not write raw signed payloads to commit-safe artifacts
- signer boundary returns only redacted success/failure status to the runbook layer
- any operator-private signed material needed for submission must remain outside committed artifacts

The signed payload redaction policy must record:

- whether signing was attempted
- whether signing succeeded
- signer boundary identifier
- redacted payload presence status
- signature presence status as boolean only
- no raw signature
- no payload hash derived from signed material
- no payload preview
- no length leak
- no replayable or copyable signed request material

### 5. Submission Boundary

The submission boundary must be separate from signing. It may be entered only after:

- exact operator authorization
- preflight pass
- order construction pass
- signing boundary pass
- submission-specific operator review if required by the future implementation

Submission controls:

- no automatic retry that creates another order
- no scheduler
- no daemon
- no background loop
- no fallback market
- no fallback strategy
- no silent notional increase
- no broad authenticated endpoint access
- no cancellation call unless the cancel plan is activated and separately logged

The submission response redaction policy must record:

- request attempt timestamp
- endpoint class, not raw authenticated URL if it carries sensitive query material
- HTTP status class or safe code
- success/failure category
- redacted response presence status
- redacted order reference status
- no auth headers
- no raw request body
- no raw response body
- no API key, secret, passphrase, token, signature, or signed payload
- no fake fill, fake PnL, fake balance, or fake position

If a raw response is operationally required for cancellation or reconciliation, it must be kept only in operator-controlled, non-committed storage and referenced by a non-derived local record ID.

### 6. Response Capture

Response capture must split operator-private material from commit-safe artifacts.

Commit-safe capture may include:

- timestamp
- attempt number
- redacted submission status
- redacted order reference presence
- redaction policy version
- reconciliation status
- cancellation eligibility status
- failure category

Commit-safe capture must not include:

- raw order IDs if the operator policy marks them private
- raw CLOB responses
- raw request payloads
- signatures
- signed payloads
- auth headers
- wallet addresses sourced from private material
- balances, positions, fills, or PnL unless separately redacted and approved

### 7. Post-Submit Ledger

The first live order ledger must be append-only and one-shot. It must include:

- task ID
- branch and HEAD
- exact authorization captured flag
- market and strategy
- notional cap and requested notional
- order attempt count for the day
- preflight result
- signing boundary result
- submission boundary result
- redaction policy versions
- reconciliation pending/completed state
- cancel/failure plan state
- final status

The ledger must not infer a fill. It must not invent PnL. It must not invent balances, positions, order IDs, or transaction hashes. Unknown execution state remains unknown until independently reconciled.

### 8. Reconciliation Plan

The future implementation must define reconciliation before submission. Reconciliation must answer only:

- was the order accepted, rejected, or unknown
- was any cancel action required
- was any operator-private follow-up needed
- were commit-safe ledgers updated
- did the run remain within one-shot scope

Reconciliation must not:

- fake fills
- fake balances
- fake positions
- fake PnL
- infer outcomes from missing data
- make new market decisions
- submit another order

If reconciliation is uncertain because of network, auth, response parsing, or redaction limits, the status must be `unknown_requires_operator_review`.

### 9. Cancel And Failure Plan

The cancel plan must be known before submission. The future implementation must define whether cancellation is:

- unavailable by design
- manual operator-only outside PMBOT
- available through a separate, explicitly approved cancel boundary

If any cancellation mechanism is implemented later, it must have its own safety gates and must not be triggered by a scheduler, daemon, background loop, or unattended retry path.

Failure handling must capture:

- abort point
- failure category
- whether any order may have reached the venue
- whether reconciliation is required
- whether cancellation is required
- whether operator-private material exists outside committed artifacts
- whether commit-safe artifacts remained redacted

Failure handling must not attempt a second order.

## Abort Conditions

The future implementation must abort before any signing, submission, cancellation, or authenticated trading call if any condition below is true:

- any 063 readiness or acceptance marker is missing
- any 064 readiness or acceptance marker is missing
- any required readiness marker is stale
- risk limit mismatch
- max notional exceeds `1.00 USD`
- max orders per day is not exactly `1`
- an order has already been attempted for the day
- market is not `BTC`
- strategy is not `tiny-momentum`
- exact operator approval is missing
- exact operator approval has expired
- static safety invariant report has a critical finding
- Telegram forbidden-control regression is present
- Telegram is unavailable and not explicitly optional
- replacement review surface is missing when Telegram is optional
- credential or private material could be exposed
- broad environment enumeration is requested
- `.env`, wallet, browser profile, credential store, or auth-store access is requested
- signer boundary is not isolated
- signer boundary logging cannot be proven safe
- signed payload redaction policy is missing
- submission response redaction policy is missing
- network endpoint behavior is uncertain
- authenticated request scope is uncertain
- response parsing is uncertain
- CLOB base URL or endpoint class is uncertain
- order construction includes an unexpected market, strategy, notional, side, price, or expiry
- runtime code introduces a scheduler, daemon, background loop, or autonomous repeat
- artifact path points to a sensitive location
- any artifact contains unredacted secret-looking or execution-sensitive material

Abort must preserve evidence. Do not overwrite or "repair" an unsafe artifact into a passing status without an explicit failure record.

## Required Artifacts For Future 065 Implementation

The future implementation must write commit-safe artifacts by default. Operator-private artifacts, if any are unavoidable for live operations, must stay outside the repository and must be referenced only by non-derived local record IDs.

Required commit-safe artifacts:

- operator approval packet
- live order intent snapshot
- signed payload redaction policy
- submission response redaction policy
- first live order ledger
- failure ledger
- kill switch record

### Operator Approval Packet

Required fields:

- task ID
- generated timestamp
- operator authorization status
- exact text match boolean
- authorization expiry
- market scope
- strategy scope
- max notional
- max orders today
- no autonomous repeat boolean
- no scheduler boolean
- no daemon boolean
- no background loop boolean
- Telegram or replacement review surface status
- risk packet reference
- kill/cancel/failure plan references
- redaction policy references

### Live Order Intent Snapshot

Required fields:

- schema version
- task ID
- branch and HEAD
- construction timestamp
- market `BTC`
- strategy `tiny-momentum`
- max notional `1.00`
- requested notional
- operator-reviewed order parameters
- risk packet reference
- exact authorization reference
- non-secret source evidence references
- pre-signing status

### Signed Payload Redaction Policy

Required fields:

- policy version
- signer boundary name
- signing attempted boolean
- signing success boolean
- raw signed payload emitted boolean, always false for commit-safe artifacts
- raw signature emitted boolean, always false for commit-safe artifacts
- payload preview emitted boolean, always false
- payload hash emitted boolean, always false unless a future approved policy proves it is non-replayable and non-sensitive
- operator-private material reference policy
- failure behavior

### Submission Response Redaction Policy

Required fields:

- policy version
- submission attempted boolean
- endpoint class
- response status category
- raw request emitted boolean, always false
- raw response emitted boolean, always false
- auth header emitted boolean, always false
- raw order reference emitted boolean, false unless a separate operator-approved policy classifies it commit-safe
- operator-private raw response handling
- failure behavior

### First Live Order Ledger

Required fields:

- task ID
- branch and HEAD
- operator authorization packet reference
- market
- strategy
- max notional
- requested notional
- orders attempted today before run
- orders attempted today after run
- preflight status
- order construction status
- signing boundary status
- submission boundary status
- response capture status
- reconciliation status
- cancellation status
- final status

### Failure Ledger

Required fields:

- task ID
- failure timestamp
- abort point
- failure category
- whether any order may have reached the venue
- reconciliation required boolean
- cancellation required boolean
- operator action required boolean
- artifact redaction status
- no-repeat confirmation

### Kill Switch Record

Required fields:

- task ID
- kill switch plan version
- operator-reviewed boolean
- trigger points
- manual stop instructions
- effect on signing boundary
- effect on submission boundary
- effect on cancellation boundary
- effect on retries
- final state

## Tests Required For Future 065 Implementation

A future implementation must add focused tests before any live order attempt. Required test coverage:

- no raw secret emission
- no raw secret storage
- no broad environment enumeration
- no order if approval missing
- no order if approval text is paraphrased
- no order if exact authorization is expired
- no order if risk limits exceed tiny cap
- no order if max orders per day is above one
- no order if an order was already attempted that day
- no order if market is not BTC
- no order if strategy is not tiny-momentum
- no repeated orders
- no automatic retry as a second order
- no scheduler
- no daemon
- no background loop
- no fake fill
- no fake PnL
- no fake balance
- no fake position
- no unredacted signed payload storage
- no unredacted submission response storage
- no auth header storage
- signed payload redaction policy enforced
- submission response redaction policy enforced
- cancel/failure paths documented
- reconciliation uncertainty remains unknown and operator-reviewed
- Telegram forbidden control regression blocks live path
- static safety critical finding blocks live path
- 063 missing marker blocks live path
- 064 missing marker blocks live path

All future tests must be deterministic and safe to run without real credentials.

## Validation Required For This Documentation Task

This documentation-only task must validate with:

```text
python -m compileall -q pm_bot
python -m compileall -q ai_orchestrator
python -m pm_bot.operator_runner.static_safety_invariant_report --scope pm_bot --dry-run
git diff --check
git diff --cached --check
```

These commands do not approve live trading. They only validate that this documentation-only change did not introduce runtime code changes and that the existing safety scanner remains clean for critical findings.

## Safety Statement

065 is a design-first runbook. It does not connect a wallet, read private keys, inspect secrets, instantiate a signer, generate signed payloads, submit orders, cancel orders, call authenticated trading endpoints, fetch balances, fetch positions, fetch fills, calculate PnL, enable live trading, add browser automation, add a scheduler, add a daemon, add a background loop, or create autonomous repetition.

The only acceptable result of this task is a reviewable design package for a later separately approved implementation.
