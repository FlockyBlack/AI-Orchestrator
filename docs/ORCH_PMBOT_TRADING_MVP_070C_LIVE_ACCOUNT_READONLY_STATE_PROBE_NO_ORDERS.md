# ORCH-PMBOT-TRADING-MVP-070C Live Account Read-Only State Probe

## Purpose

This task adds a bounded live account state probe that extends the 067C CLOB L2 authentication check into redacted account diagnostics. It can inspect safe read-only SDK methods when available, but it does not submit orders, cancel orders, sign payloads, connect a wallet, read a private key, or emit raw account values.

Command:

```bash
python -m pm_bot.operator_runner.live_account_readonly_state_probe --market BTC --strategy tiny-momentum --dry-run
```

## Credential Boundary

The probe uses only these L2 env vars for SDK authentication:

- `POLYMARKET_API_KEY`
- `POLYMARKET_API_SECRET`
- `POLYMARKET_API_PASSPHRASE`

The probe may detect and redact these account config markers:

- `POLYMARKET_WALLET_ADDRESS`
- `POLYMARKET_SIGNATURE_TYPE`
- `POLYMARKET_FUNDER_ADDRESS`

It does not read private-key, wallet-private-key, mnemonic, or seed env vars. Full wallet and funder addresses, L2 credential values, raw SDK responses, raw order rows, and numeric balance/allowance values are not written to artifacts.

## Probe Behavior

The adapter tries supported official Python SDK modules in this order:

- `py_clob_client_v2`
- `py_clob_client`

If a supported SDK is unavailable, the probe fails closed. If the SDK requires signer/private-key-backed initialization, the probe fails closed with `blocked_sdk_requires_signer_without_private_key`. If a safe read-only SDK method is unavailable, the method is recorded as `method_unavailable`; the probe does not fabricate account data.

Allowlisted SDK methods:

- `get_orders` for open-order count only
- `get_balance_allowance` for balance/allowance availability with values redacted

The PMBOT code does not call POST, PUT, PATCH, DELETE, order submission, order cancellation, signing, wallet, API key creation, or API key derivation methods.

## Artifacts

Default artifact directory:

```text
pm_bot/trading_core/artifacts/live_account_readonly_state_probe_070c/
```

Files:

- `live_account_readonly_state_probe_070c_result.json`
- `latest_live_account_readonly_state_status_070c.json`
- `live_account_readonly_state_diagnostics_070c.json`
- `live_account_readonly_state_redaction_policy_070c.json`
- `live_account_readonly_state_operator_summary_070c.md`

Current generated status in this worktree will reflect the operator shell. If the shell does not expose the three L2 env vars, the generated status is expected to be `blocked_missing_l2_credentials`; no SDK dependency check or authenticated read-only network probe is performed in that case.

## Safety Statement

`allowed_for_live=false` and `probe_is_readonly=true` remain hard-coded. This task does not enable trading, order submission, order cancellation, signer instantiation, private-key reads, wallet connection, signed payload generation, autonomous loops, browser automation, schedulers, daemons, or background workers.
