# ORCH-PMBOT-TRADING-MVP-056 Supervised Live Connector Auth Network Preflight No Order Submission

## Scope

056 adds a supervised PMBOT live connector/auth/network preflight boundary.

The operator command is:

```text
python -m pm_bot.operator_runner.live_connector_preflight --market BTC --dry-run
```

Optional controls:

- `--network-check`
- `--auth-check`
- `--public-only`
- `--artifacts-dir`
- `--json`

The command is dry-run, review-only, and preflight-only. It verifies public connectivity and optional redacted auth configuration presence while preserving every live execution blocker.

## Default Behavior

Default execution is public-only unless `--auth-check` is explicitly requested.

The default preflight:

- checks public Gamma availability with a read-only `GET`
- records public network evidence
- skips auth presence checks unless requested
- writes operator-safe artifacts
- fails closed into unresolved blockers on missing config, timeout, or network error
- never enables live trading

`--network-check` additionally validates the configured CLOB base URL shape. It does not submit authenticated CLOB requests and does not call order, balance, position, or wallet endpoints.

## Optional Auth Presence Checks

`--auth-check` performs only redacted environment-presence checks. It may report whether explicitly named configuration markers are missing or present, but never prints, stores, hashes, truncates, or serializes raw values.

056 recognizes these preflight marker names:

- `PMBOT_POLYMARKET_LIVE_PREFLIGHT_ENABLED`
- `PMBOT_POLYMARKET_CLOB_BASE_URL`
- `PMBOT_POLYMARKET_AUTH_CONFIG_PRESENT`
- `PMBOT_POLYMARKET_API_KEY_CONFIGURED`
- `PMBOT_POLYMARKET_API_SECRET_CONFIGURED`
- `PMBOT_POLYMARKET_FUNDER_ADDRESS_CONFIGURED`

The report uses only `missing` and `present_redacted` value categories. The implementation does not ask operators to paste secrets into Codex, ChatGPT, docs, or artifacts.

## Forbidden Behavior

056 does not introduce or allow:

- private key reads beyond redacted presence checks
- API secret reads beyond redacted presence checks
- auth token reads beyond redacted presence checks
- raw credential logs or artifacts
- wallet connection
- wallet spend
- signer instantiation
- signed payload generation
- signed order generation
- order submission
- order cancellation
- balance reads
- position reads
- fake order IDs, transaction hashes, fills, balances, PnL, or positions
- scheduler, daemon, background worker, or autonomous loop
- browser automation

## Generated Artifacts

Default artifact directory:

```text
pm_bot/trading_core/artifacts/live_connector_preflight_056/
```

Required generated artifacts:

- `live_connector_preflight_056_result.json`
- `live_connector_preflight_056_operator.md`
- `latest_live_connector_preflight_status_056.json`
- `live_connector_network_evidence_056.json`
- `live_credentials_presence_056.json`
- `live_readiness_blockers_056.json`

Artifacts are safe to inspect and commit. They must not contain raw credentials, secrets, private keys, mnemonics, seed phrases, auth tokens, signed payloads, order IDs, transaction hashes, fills, balances, PnL, or positions.

## Passive UI And Telegram

The passive Operator UI and Telegram summaries surface latest live connector preflight status when supplied in dashboard/context data.

They show:

- preflight status
- public network status
- auth boundary status
- blockers
- order submission blocked
- signing blocked
- live execution blocked

They do not add approve-live buttons, wallet controls, signing controls, order controls, or trade execution controls.

## Safety Invariants

All 056 outputs preserve:

- `execution_mode=paper_or_preflight`
- `review_only=true`
- `preflight_only=true`
- `live_execution_approved=false`
- `canary_executable_now=false`
- `real_execution_available=false`
- `order_submission_enabled=false`
- `wallet_signing_enabled=false`
- `signing_enabled=false`
- `signed_payload_generation_enabled=false`
- `signed_order_generation_enabled=false`
- `authenticated_polymarket_enabled=false`
- `live_connector_enabled=false`
- `allowed_for_live=false`
- `resolved_blocker_count=0`

056 may report `auth_presence_check_performed=true` and redacted credential marker presence when `--auth-check` is requested. It does not report `authenticated_polymarket_enabled=true` and does not perform authenticated trading requests.

## Operator Next Steps

The only valid next action after 056 is:

```text
review preflight only, no live order available
```

This does not enable live trading because it has no wallet connection, no signing capability, no signed payload path, no order submission path, no cancellation path, no authenticated trading request path, and no operator approval field that can make `allowed_for_live=true`.
