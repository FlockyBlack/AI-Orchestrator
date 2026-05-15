# ORCH-PMBOT-TRADING-MVP-072E Signed Payload Diagnostic Adapter Scaffold

072E adds a guarded, local-artifact-only adapter between token selection, the guarded signer diagnostic status, and the signed payload dry-run status.

The default command is:

```bash
python -m pm_bot.operator_runner.signed_payload_diagnostic_adapter --market BTC --strategy tiny-momentum --dry-run
```

## Behavior

- Reads local selected-token, order-prep, guarded signer diagnostic, and signed payload dry-run artifacts.
- Validates required interface fields and source safety flags.
- Emits unsigned diagnostic readiness metadata only.
- Stores token identifiers only as presence and SHA-256 fingerprints in adapter-owned artifacts.
- Leaves future signing explicitly blocked as `not_implemented_blocked`.
- Performs no signing, no submission, no cancellation, no trading writes, no authenticated trading calls, and no secret reads.
- Keeps `allowed_for_live=false`.

## Generated Artifacts

Generated under `pm_bot/trading_core/artifacts/signed_payload_diagnostic_adapter_072e/`:

- `signed_payload_diagnostic_adapter_072e_result.json`
- `latest_signed_payload_diagnostic_adapter_status_072e.json`
- `signed_payload_diagnostic_adapter_contract_072e.json`
- `signed_payload_diagnostic_adapter_redaction_policy_072e.json`
- `signed_payload_diagnostic_adapter_safety_snapshot_072e.json`
- `signed_payload_diagnostic_adapter_operator_summary_072e.md`

## Default Status

The committed default artifacts report `blocked_selected_token_candidate_not_ready` because the current local selected-token artifact does not contain a selected source-backed token ID. This is intentional: 072E must not invent token IDs and must not convert readiness into execution.

## Safety Statement

072E is review-only, dry-run-only, paper-only, non-executable, and local-artifact-only. It does not read private keys or secret values, does not output raw private key material, does not output full signed payloads, does not create execution identifiers, and does not submit or cancel orders.
