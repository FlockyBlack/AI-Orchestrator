# ORCH PMBOT Trading MVP 073C: Selected Token Signed Payload Readiness Gate

Task ID: `ORCH-PMBOT-TRADING-MVP-073C-SELECTED-TOKEN-SIGNED-PAYLOAD-READINESS-GATE-NO-SUBMIT`

073C adds a local readiness gate for deciding whether existing artifacts are sufficient to proceed to a future signed payload diagnostic. It does not sign order payloads, submit orders, cancel orders, call CLOB trading write endpoints, or enable live trading.

## Command

```powershell
python -m pm_bot.operator_runner.selected_token_payload_readiness_gate --market BTC --strategy tiny-momentum --dry-run
```

The runner requires `--dry-run` and rejects live, wallet, signing, submit, cancel, auth, private-key, seed, mnemonic, API-secret, auth-token, and passphrase flags.

## Inputs

The gate reads local JSON artifacts only:

- `pm_bot/trading_core/artifacts/operator_token_selection_packet_073b/` when present
- `pm_bot/trading_core/artifacts/first_order_market_token_resolver_070b/first_order_market_token_contract_070b.json`
- `pm_bot/trading_core/artifacts/guarded_signer_diagnostic_smoke_069a/latest_guarded_signer_diagnostic_status_069a.json`
- `pm_bot/trading_core/artifacts/first_live_order_approval_contract_065d/latest_first_live_order_approval_contract_status_065d.json`
- `pm_bot/trading_core/artifacts/signed_order_payload_dry_run_070a/latest_signed_order_payload_dry_run_status_070a.json`
- `pm_bot/trading_core/artifacts/signed_payload_diagnostic_adapter_072e/latest_signed_payload_diagnostic_adapter_status_072e.json`

Missing sources remain missing in the sources artifact. The 072E adapter is reported as source context; its stale selected-token blocker does not create readiness by itself.

## Gate Rules

- Missing selected token blocks.
- Present but unverified selected token blocks.
- Missing signer diagnostic blocks.
- Signer diagnostic that is not `diagnostic_ok` blocks.
- Missing approval contract blocks.
- Approval contract that is not the non-executable 065D definition blocks.
- Missing signed payload dry-run contract blocks.
- Dry-run contract without a safe non-executable fingerprint or safe flags blocks.
- A ready status is only `ready_for_signed_payload_diagnostic`; it is never readiness for submit.

## Outputs

Artifacts are written under:

`pm_bot/trading_core/artifacts/selected_token_payload_readiness_gate_073c/`

- `selected_token_payload_readiness_gate_073c_result.json`
- `latest_selected_token_payload_readiness_status_073c.json`
- `selected_token_payload_readiness_sources_073c.json`
- `selected_token_payload_readiness_blockers_073c.json`
- `selected_token_payload_readiness_safety_snapshot_073c.json`
- `selected_token_payload_readiness_operator_summary_073c.md`

## Safety Invariants

- `allowed_for_live=false`
- `selected_token_payload_ready_for_submit=false`
- no order submission
- no order cancellation
- no trading write calls
- no authenticated trading writes
- no default signing
- no full signed payload output
- no raw private key, API secret, passphrase, seed phrase, or mnemonic output
- no fake token ID generation
- no fake balance, order, fill, or PnL generation
