# ORCH-PMBOT-TRADING-MVP-067C CLOB L2 Auth Read-Only Probe

## Purpose

This task adds a bounded Polymarket CLOB L2 authenticated read-only probe. It is designed to verify whether L2 API credentials can authenticate against safe account read methods without submitting orders, cancelling orders, signing order payloads, connecting a wallet, reading a private key, or emitting raw credentials.

Command:

```bash
python -m pm_bot.operator_runner.clob_l2_auth_readonly_probe --market BTC --strategy tiny-momentum --dry-run
```

## Credential Boundary

The probe reads only these env vars:

- `POLYMARKET_API_KEY`
- `POLYMARKET_API_SECRET`
- `POLYMARKET_API_PASSPHRASE`

It does not read:

- `POLYMARKET_PRIVATE_KEY`
- `POLYMARKET_WALLET_ADDRESS`
- `POLYMARKET_SIGNATURE_TYPE`
- `POLYMARKET_FUNDER_ADDRESS`

The API credential values are used only in memory when constructing the SDK API credentials object. Artifacts record presence booleans and redacted diagnostics only. Raw values, hashes, prefixes, suffixes, account balance values, allowance values, order rows, and SDK raw responses are not written.

## Probe Behavior

The adapter tries supported official Python SDK modules in this order:

- `py_clob_client_v2`
- `py_clob_client`

If a supported SDK is unavailable, or if the SDK does not expose an allowlisted read-only method, the probe fails closed. If the SDK requires signer/private-key-backed initialization for L2 calls, the probe fails closed with `blocked_sdk_requires_signer_without_private_key`; it does not read `POLYMARKET_PRIVATE_KEY` as a fallback.

Allowlisted SDK methods:

- `get_orders` for open-order count only
- `get_balance_allowance` with balance/allowance values redacted

The PMBOT code does not call POST, PUT, PATCH, or DELETE methods and does not call order submission, cancellation, signing, wallet, API key creation, or API key derivation methods.

## Artifacts

Default artifact directory:

```text
pm_bot/trading_core/artifacts/clob_l2_auth_readonly_probe_067c/
```

Files:

- `clob_l2_auth_readonly_probe_067c_result.json`
- `latest_clob_l2_auth_readonly_probe_status_067c.json`
- `clob_l2_auth_readonly_probe_diagnostics_067c.json`
- `clob_l2_auth_readonly_probe_redaction_policy_067c.json`
- `clob_l2_auth_readonly_probe_operator_summary_067c.md`

Current generated status in this worktree:

- `status=blocked_missing_l2_credentials`
- `auth_verified=false`
- `l2_authenticated_readonly_probe_attempted=false`
- `probe_is_readonly=true`
- `allowed_for_live=false`

This means the shell used for validation did not expose the three L2 env vars. No SDK probe or network authenticated read was performed, and no success was inferred.

## Safety Statement

`allowed_for_live=false` remains hard-coded. This task does not enable trading, order submission, order cancellation, signer instantiation, private-key reads, wallet connection, signed payload generation, autonomous loops, browser automation, schedulers, daemons, or background workers.
