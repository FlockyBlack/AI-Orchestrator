# ORCH-PMBOT-TRADING-MVP-073B Operator Token Selection Packet No Trading

## Summary

073B adds a local, non-executable operator token selection packet for the first supervised tiny-order preparation path. It reads the latest local 071A public discovery artifacts and 071D discovery-to-token bridge artifacts when present, lists source-backed public outcome token candidates, and records how an operator selected or manually supplied a token ID.

The packet never auto-selects for live execution. It never invents token IDs, generates order payloads, signs, submits, cancels, connects a wallet, reads secrets, or calls authenticated trading endpoints. It always emits `allowed_for_live=false` and `token_selection_executable=false`.

## Operator Command

```powershell
python -m pm_bot.operator_runner.operator_token_selection_packet --market BTC --strategy tiny-momentum --dry-run
```

Optional selection inputs:

```powershell
python -m pm_bot.operator_runner.operator_token_selection_packet --market BTC --strategy tiny-momentum --dry-run --candidate-index 0
python -m pm_bot.operator_runner.operator_token_selection_packet --market BTC --strategy tiny-momentum --dry-run --token-id <TOKEN_ID>
python -m pm_bot.operator_runner.operator_token_selection_packet --market BTC --strategy tiny-momentum --dry-run --token-id <TOKEN_ID> --market-slug <SLUG> --condition-id <CONDITION_ID>
```

`candidate-index` is zero-based and must match the emitted candidate list. A manually supplied `token-id` is format-validated. It is marked `source_backed=false` and `operator_provided_unverified=true` unless it matches one of the source-backed candidates.

## Generated Artifacts

Default output directory:

```text
pm_bot/trading_core/artifacts/operator_token_selection_packet_073b/
```

Artifacts:

- `operator_token_selection_packet_073b_result.json`
- `latest_operator_token_selection_status_073b.json`
- `operator_token_selection_candidates_073b.json`
- `operator_token_selection_packet_073b.json`
- `operator_token_selection_instructions_073b.md`
- `operator_token_selection_safety_snapshot_073b.json`

## Status Semantics

- `no_candidates`: no source-backed public candidate is available and no valid manual token was supplied.
- `selection_required`: one or more source-backed candidates are listed, but the operator has not selected one.
- `selected_source_backed_candidate`: `candidate-index` or a matching manual `token-id` selected a source-backed candidate.
- `selected_operator_provided_unverified`: a valid manual `token-id` was supplied but did not match a source-backed candidate.
- `invalid_selection`: candidate index, token ID format, market slug, condition ID, or provided metadata did not validate.

## Safe CLI Path

When a token is selected, the packet emits a review-only downstream CLI path:

```powershell
python -m pm_bot.operator_runner.first_order_market_token_resolver --market BTC --strategy tiny-momentum --dry-run --token-id <SELECTED_TOKEN_ID>
python -m pm_bot.operator_runner.order_prep_packet --market BTC --strategy tiny-momentum --dry-run
```

These commands remain dry-run review steps. They do not approve live execution.

## Safety Snapshot

The packet always records:

- `allowed_for_live=false`
- `token_selection_executable=false`
- `token_id_generated=false`
- `fake_token_id_generated=false`
- `order_payload_generated=false`
- `signing_attempted=false`
- `order_submission_attempted=false`
- `order_cancellation_attempted=false`
- `wallet_connection_attempted=false`
- `authenticated_trading_call_performed=false`
- `environment_secrets_read=false`

073B stores only sanitized source summaries, candidate metadata, selected token review state, blockers, and operator instructions. It does not persist full source payloads, secrets, account values, order IDs, signatures, fills, PnL, or transaction hashes.
