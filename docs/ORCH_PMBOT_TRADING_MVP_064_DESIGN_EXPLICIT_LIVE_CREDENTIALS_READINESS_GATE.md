# ORCH-PMBOT-TRADING-MVP-064 Explicit Live Credentials Readiness Gate Design

## Purpose

This document defines a design-only plan for a future explicit live credentials readiness gate. It is documentation only. It does not add runtime code, read environment values, validate real credentials, print secrets, store secrets, connect wallets, sign payloads, submit orders, cancel orders, or call authenticated Polymarket endpoints.

The gate exists to make one question reviewable before any later live-enabling work:

```text
Are the operator-controlled live credential prerequisites explicitly present as redacted markers while every execution path remains blocked?
```

The answer must never include raw private keys, seed phrases, mnemonics, browser wallet data, wallet files, API secrets, auth tokens, passphrases, signatures, signed payloads, or raw credential values.

## Non-Goals And Prohibited Scope

This task and its proposed gate do not authorize:

- credential value reads
- broad environment dumps
- `.env` file reads
- secret store reads
- browser wallet inspection
- wallet connection
- signer instantiation
- API key derivation
- HMAC generation
- EIP-712 signing
- signed order payload generation
- order submission
- order cancellation
- balance reads
- position reads
- authenticated Polymarket requests
- autonomous trading loops
- schedulers, daemons, or background workers

Any future implementation must fail closed if a requested flag, CLI option, config field, or artifact attempts to cross one of these boundaries.

## Gate Model

The future gate should be a single explicit readiness report with these properties:

- `execution_mode=preflight`
- `review_only=true`
- `preflight_only=true`
- `design_reference=ORCH-PMBOT-TRADING-MVP-064`
- `credentials_values_read=false`
- `credentials_values_serialized=false`
- `secrets_printed=false`
- `secrets_persisted=false`
- `wallet_connection_attempted=false`
- `signing_attempted=false`
- `signed_payload_generated=false`
- `authenticated_request_performed=false`
- `order_submission_attempted=false`
- `order_cancellation_attempted=false`
- `allowed_for_live=false`
- `canary_executable_now=false`
- `live_execution_approved=false`
- `resolved_blocker_count=0`

The gate may summarize only marker presence and blocker state. It must not decide that PMBOT is ready to trade live. The maximum positive result is `REDACTED_PRESENCE_REVIEW_READY`, which means "operator can review marker coverage", not "live-ready".

## Redacted Presence-Only Env Readiness

The future implementation should inspect only an explicit allowlist of non-secret marker names. It should not scan all environment variables. It should not accept raw credential values. It should not store raw marker values when a marker value is unsafe-looking.

Allowed marker result categories:

- `missing`
- `present_redacted`
- `invalid_marker_value_redacted`
- `conflicting_execution_flag_blocked`
- `not_checked`

Disallowed result categories:

- any raw value
- value hash
- value prefix
- value suffix
- masked value that preserves length
- bearer token preview
- wallet address if sourced from a secret wallet file
- signed payload preview
- API key preview
- passphrase preview

Marker values, if a future implementation reads marker variables, should be limited to simple non-secret assertions such as boolean or marker words. Any other value should be treated as unsafe and not serialized.

## Required Future Env Marker Names

The future gate should use marker names only. These names are symbolic readiness markers and execution flags. They are not secret values.

Presence and credential-source markers:

- `PMBOT_LIVE_CREDENTIALS_READINESS_GATE_ENABLED`
- `PMBOT_POLYMARKET_AUTH_CONFIG_PRESENT`
- `PMBOT_POLYMARKET_CLOB_BASE_URL`
- `PMBOT_POLYMARKET_L2_API_KEY_PRESENT`
- `PMBOT_POLYMARKET_L2_API_SECRET_PRESENT`
- `PMBOT_POLYMARKET_L2_PASSPHRASE_PRESENT`
- `PMBOT_POLYMARKET_FUNDER_ADDRESS_CONFIGURED`
- `PMBOT_WALLET_ADDRESS_CONFIGURED`
- `PMBOT_SIGNING_PROVIDER_CONFIGURED`
- `PMBOT_SIGNING_DRY_RUN_ONLY`

Manual control and kill-switch markers:

- `PMBOT_REQUIRE_MANUAL_OPERATOR_APPROVAL`
- `PMBOT_REQUIRE_KILL_SWITCH_READY`
- `PMBOT_LIVE_CREDENTIALS_OPERATOR_REVIEW_RECORD_PRESENT`
- `PMBOT_LIVE_CREDENTIALS_DUAL_CONTROL_REVIEW_PRESENT`

Execution flags that must remain blocked by this gate:

- `PMBOT_LIVE_MODE`
- `PMBOT_LIVE_CANARY_ENABLED`
- `PMBOT_AUTHENTICATED_POLYMARKET_ENABLED`
- `PMBOT_WALLET_SIGNING_ENABLED`
- `PMBOT_ORDER_SUBMISSION_ENABLED`

Risk and market-scope config names already used by earlier review-only gates may be referenced as non-secret readiness context:

- `PMBOT_MAX_ORDER_NOTIONAL_USD`
- `PMBOT_DAILY_LOSS_CAP_USD`
- `PMBOT_TOTAL_EXPOSURE_CAP_USD`
- `PMBOT_MAX_LIVE_TRADES_PER_DAY`
- `PMBOT_ALLOWED_MARKET_SLUGS`
- `PMBOT_ALLOWED_MARKET_IDS`

The gate must not introduce required raw secret env names for PMBOT runtime consumption. If a later operator process uses an external secret store, that source remains outside this gate and must be covered by a separate approval task.

## Operator Approval Boundaries

The readiness gate may record that an operator review marker exists. It must not convert that marker into live execution approval.

Required approval boundaries:

- One approval for reviewing redacted credential marker coverage.
- A separate approval for any future implementation that reads marker env values.
- A separate approval for any authenticated no-order network request.
- A separate approval for any wallet or signer boundary work.
- A separate approval for signed payload generation.
- A separate approval for order submission or cancellation.
- A separate approval for any first tiny live order runbook.

No approval marker in this gate may set `allowed_for_live=true`. Operator review of credentials is necessary for later work, but it is not sufficient for live trading.

## Credential Safety Policy

The future gate must enforce these rules:

- Read only explicitly named marker variables, never broad environment state.
- Never read private keys, seed phrases, mnemonics, browser wallets, wallet files, raw API secrets, auth tokens, passphrases, or raw credentials.
- Never write raw secret values to JSON, Markdown, logs, console output, UI payloads, Telegram summaries, test fixtures, snapshots, diffs, or result files.
- Never hash, truncate, prefix, suffix, length-leak, or otherwise fingerprint secret-looking values.
- Treat unexpected marker values as unsafe and record only the marker name plus `invalid_marker_value_redacted`.
- Keep `.env`, credential stores, auth stores, wallet directories, and browser profiles out of scope.
- Keep all generated artifacts safe to commit and inspect.
- Reject any field name that attempts to carry `private_key`, `seed_phrase`, `mnemonic`, `api_secret_value`, `auth_token`, `passphrase_value`, `signature`, `signed_payload`, or equivalent raw secret material.

## What Remains Blocked

After this design and after any future presence-only implementation, these blockers remain unresolved:

- `live_execution_not_approved`
- `credentials_not_value_verified_by_pmbot`
- `operator_review_does_not_enable_execution`
- `authenticated_polymarket_requests_blocked`
- `wallet_connection_blocked`
- `signer_instantiation_blocked`
- `private_key_reads_blocked`
- `api_secret_reads_blocked`
- `signed_payload_generation_blocked`
- `order_submission_blocked`
- `order_cancellation_blocked`
- `balance_reads_blocked`
- `position_reads_blocked`
- `kill_switch_not_bound_to_live_adapter`
- `rollback_cancel_plan_not_implemented`
- `first_live_order_task_not_present`

The gate should make these blockers visible, not resolve them.

## Later Task Required Before Any Live Order

Before any live order can be considered, later separately approved tasks must exist for all of the following:

- implementation of the redacted presence-only readiness gate from this design
- validation that gate artifacts contain no secret values
- operator-reviewed credential source process outside Codex artifacts
- authenticated endpoint allowlist and no-order boundary review
- wallet/signing boundary review without accidental signing
- signed payload generation boundary with explicit manual approval
- order submission and cancellation adapter design with disabled-first defaults
- kill-switch wiring to any future live adapter
- one-market, one-micro-order runbook
- rollback, cancellation, and failure handling checklist
- final supervised go/no-go record that still requires manual operator action

This design is not that later task and cannot be used as live authorization.

## Failure Modes

The future implementation should fail closed for these cases:

- required marker missing
- marker value looks like raw credential material
- marker value is not in the allowed non-secret marker set
- execution flag is true in a design/preflight-only gate
- both market slug and market ID scope are provided when exactly one is required
- risk limit config is missing, invalid, negative, zero, or non-finite
- CLOB base URL is missing, malformed, or includes userinfo/query/fragment
- operator review marker is missing or stale
- dual-control review marker is missing
- artifact path points to a sensitive location
- generated artifact contains forbidden field names
- generated artifact contains secret-looking values
- static safety scan reports critical findings
- code path attempts wallet, signing, order, balance, position, or authenticated request behavior

In every failure mode, the output should preserve `allowed_for_live=false` and include unresolved blockers only.

## Audit Artifacts For Future Implementation

A later implementation should write review-only artifacts similar to:

- `pm_bot/trading_core/artifacts/live_credentials_readiness_gate_064/live_credentials_readiness_gate_064_result.json`
- `pm_bot/trading_core/artifacts/live_credentials_readiness_gate_064/live_credentials_readiness_gate_064_operator.md`
- `pm_bot/trading_core/artifacts/live_credentials_readiness_gate_064/latest_live_credentials_readiness_gate_status_064.json`
- `pm_bot/trading_core/artifacts/live_credentials_readiness_gate_064/redacted_marker_presence_064.json`
- `pm_bot/trading_core/artifacts/live_credentials_readiness_gate_064/operator_approval_boundary_064.json`
- `pm_bot/trading_core/artifacts/live_credentials_readiness_gate_064/credential_safety_policy_validation_064.json`
- `pm_bot/trading_core/artifacts/live_credentials_readiness_gate_064/live_credentials_readiness_blockers_064.json`

Each artifact must include:

- contract name and schema version
- generated timestamp
- source command and dry-run status
- marker names checked
- marker result categories
- missing marker list
- unsafe marker name list without values
- operator approval boundary state
- forced-false execution flags
- unresolved blockers
- secret safety validation summary

Artifacts must be safe for commit. If an artifact cannot prove that it avoided secret values, the gate must fail closed and the artifact must not be treated as review-ready.

## Future Tests

A later implementation should add targeted tests for:

- default run is blocked and does not read broad environment state
- allowlisted marker names are the only accepted names
- raw-looking marker values are rejected without serialization
- no hashes, prefixes, suffixes, lengths, or previews are emitted
- missing markers produce unresolved blockers
- true execution flags are reported as conflicts and keep live blocked
- operator review marker presence does not enable live execution
- artifact schema includes forced-false execution flags
- generated JSON and Markdown contain no forbidden secret field names
- generated artifacts contain no raw fake secret sentinel strings
- CLI requires `--dry-run`
- CLI rejects live, submit, cancel, sign, wallet, balance, position, and auth execution flags
- CLOB base URL validation records only safe non-secret URL shape metadata
- static safety invariant report remains at zero critical findings
- documentation references marker names only and no secret values

## Current Task Result

This task adds only this design document and its result JSON. It performs no runtime implementation and no credential inspection.
