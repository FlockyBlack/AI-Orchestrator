# ORCH-PMBOT-TRADING-MVP-040 Live Credentials/Auth Boundary

## Purpose

This task adds the review-only live credentials/auth boundary needed before a future BTC tiny live canary task.

The boundary answers whether symbolic credential names are configured through an injected provider, whether live mode was explicitly requested for review, and whether any report is safe to show in artifacts. It does not connect a wallet, inspect real secrets by default, call authenticated endpoints, sign payloads, submit orders, or make the canary executable.

## Why This Is Required Before A Tiny Canary

The BTC MVP chain now has:

- BTC market snapshot
- BTC market analysis
- dry-run order intent
- risk decision
- operator UI
- live credentials/auth boundary status

A future one-market one-micro-order canary cannot safely proceed until the operator can review credential readiness without exposing values and without accidentally enabling authenticated endpoint usage, signing, or order submission.

## Credential Requirement Schema

The boundary defines credential requirements as metadata only:

- `requirement_id`
- `env_var_name`
- `description`
- `required_for_future_tiny_canary_auth_review`

Default symbolic names:

- `POLYMARKET_PRIVATE_KEY`
- `POLYMARKET_FUNDER_ADDRESS`
- `POLYMARKET_CLOB_API_KEY`
- `POLYMARKET_CLOB_SECRET`
- `POLYMARKET_CLOB_PASSPHRASE`
- `POLYMARKET_CHAIN_ID`
- `POLYMARKET_NETWORK`

These are names only. They are not values, and the core logic does not read real environment values unless an explicitly enabled provider is supplied in a future task.

## Provider Abstraction

`LiveAuthBoundaryProvider` is the boundary interface. The default evaluation path uses a fake/injected provider, not the real environment.

Implemented providers:

- `FakeLiveCredentialProvider`: deterministic test/provider shim that accepts fake injected values and reports only present/missing.
- `EnvironmentLiveCredentialProvider`: optional and disabled by default. When disabled, it reports `env_provider_disabled`. When enabled by explicit injection, it reports only present/missing/redacted status and does not return values.

Tests use fake providers only.

## Redaction Rules

Status reports contain only:

- `requirement_id`
- `env_var_name`
- `present`
- `redacted_preview`
- `source`
- `safe_for_artifacts`

`redacted_preview` is one of:

- `<configured:redacted>`
- `<missing>`

Actual credential values are never included in status reports, UI panel data, daily loop artifacts, evidence bundle items, result artifacts, or logs.

## No-Secret Artifact Rule

The secret boundary policy rejects forbidden field names and actual-looking secret values, including raw private keys, mnemonics, bearer tokens, signed payloads, raw transactions, auth headers, API key values, and order submission payloads.

Symbolic credential names are allowed only when used as requirement IDs, config keys, or environment variable names. For example, `POLYMARKET_CLOB_API_KEY` may appear as a required symbolic name, but an API key value may not appear anywhere.

## Boundary Decision

`evaluate_live_auth_boundary_for_tiny_canary` returns a review decision:

- `AUTH_BOUNDARY_REVIEW_READY`
- `MISSING_REQUIRED_CREDENTIALS`
- `LIVE_MODE_NOT_EXPLICITLY_ENABLED`
- `AUTHENTICATED_ENDPOINTS_STILL_DISABLED`
- `SIGNING_STILL_DISABLED`
- `ORDER_SUBMISSION_STILL_DISABLED`
- `SECRET_POLICY_VIOLATION`

Even when fake injected credentials are all present and live mode is explicitly requested:

- `authenticated_endpoints_enabled` remains `false`
- `order_submission_enabled` remains `false`
- `cryptographic_signing_enabled` remains `false`
- `wallet_signing_enabled` remains `false`
- `allowed_for_live` remains `false`
- `canary_executable_now` remains `false`
- `live_execution_approved` remains `false`
- `real_execution_available` remains `false`
- `live_connector_enabled` remains `false`

## UI Auth Boundary Display

The operator UI panel now includes a live credentials/auth boundary section with:

- boundary status
- credentials configured flag
- required credential count
- missing credential count
- redacted credential statuses
- disabled authenticated endpoint/signing/order-submission flags
- live execution flags fixed to false
- warning: `Credentials status is redacted. This panel never displays secrets.`

The UI remains a review surface only. It exposes no action that can submit orders, reveal secrets, sign payloads, or enable live execution.

## Risk Gate Integration

The risk limit control plane consumes the auth boundary state as live blockers. Dry-run intents may still receive `ALLOW_DRY_RUN` when other dry-run gates pass.

Live allowance remains blocked by:

- missing or unverified credentials
- live mode not explicitly requested
- authenticated endpoints disabled
- signing disabled
- order submission disabled
- live connector disabled
- live execution not approved
- canary not executable
- real execution unavailable

## Evidence Bundle And Blocker Matrix

The readiness evidence bundle includes `live_credentials_auth_boundary` as review evidence. This evidence item has:

- `review_ready`: true when the boundary artifact is valid
- `execution_enabling`: false
- `secrets_redacted`: true
- authenticated endpoints disabled
- signing disabled
- order submission disabled

The blocker matrix adds unresolved critical blockers for:

- `live_credentials_boundary_review_only`
- `live_credentials_not_operator_verified_for_live`
- `authenticated_endpoints_still_disabled`
- `signing_still_disabled`
- `order_submission_still_disabled`
- `live_wallet_funding_not_verified`
- `real_order_adapter_not_enabled`

No existing live blocker is resolved.

## Paper Daily Loop Artifact

The paper daily loop writes:

- `live_credentials_auth_boundary_040.json`

This artifact is redacted and passive. It is also summarized in the dashboard and fed to the operator UI panel.

## Why Order Submission Remains Disabled

This task does not add an order adapter, order payload, order endpoint, order submission CLI, or UI action. The dry-run BTC order intent remains an intent artifact only and has no executable submission payload.

## Why Signing Remains Disabled

This task does not add private key handling, mnemonic handling, wallet signing, cryptographic signing, transaction signing, or signed payload generation. Signing readiness remains a future blocker.

## What Must Happen In 041 Before Any Real Micro-Order

Before a real tiny canary can be considered, a separate operator-approved task must:

- verify credentials out-of-band without exposing values
- keep secret values out of artifacts and logs
- explicitly approve authenticated endpoint usage
- explicitly approve a disabled-first order adapter path
- explicitly approve signing boundaries if signing is required
- verify wallet funding/balance readiness out-of-band
- verify kill-switch behavior for the live boundary
- keep a one-market, one-micro-order canary scope
- preserve operator supervision and audit evidence

## Manual Operator Checklist

Operators may verify credentials without exposing values by checking:

- each required symbolic name exists in the approved secret store or runtime environment
- no credential value is pasted into issues, docs, logs, UI, JSON artifacts, or test fixtures
- the UI shows only `<configured:redacted>` or `<missing>`
- authenticated endpoints still show disabled
- signing still shows disabled
- order submission still shows disabled
- `allowed_for_live` remains false
- `canary_executable_now` remains false
- `live_execution_approved` remains false
- `real_execution_available` remains false
- `live_connector_enabled` remains false

This checklist is for review only and does not authorize live execution.
