# ORCH-PMBOT-TRADING-MVP-071D Discovery to Token Resolver Bridge No Trading

## Scope

071D adds a dry-run bridge between 071A public market token discovery artifacts and a review-only 070B target candidate contract.

The bridge reads local 071A-style public discovery artifacts only. It does not call public or authenticated networks, does not read credentials, does not use wallets, does not sign, does not create orders, and does not submit or cancel anything.

## Command

```powershell
python -m pm_bot.operator_runner.discovery_to_token_resolver_bridge --market BTC --strategy tiny-momentum --dry-run
```

Optional operator selection after reviewing multiple candidates:

```powershell
python -m pm_bot.operator_runner.discovery_to_token_resolver_bridge --market BTC --strategy tiny-momentum --dry-run --select-candidate-id <bridge_candidate_id>
```

## Behavior

- If a latest 071A discovery result exists, the bridge reads it from `pm_bot/trading_core/artifacts/public_market_token_discovery_071a/public_market_token_discovery_071a_result.json`.
- If a single source-backed valid token candidate exists, it emits `discovery_to_token_candidate_contract_071d.json` as a 070B-compatible review-only target candidate.
- If multiple valid candidates exist, it writes `discovery_to_token_operator_selection_required_071d.json` and leaves the target token ID blank.
- If no source-backed token ID exists, it blocks and leaves the target token ID blank.
- Placeholder, fixture, fake, mock, sample, or generated token IDs are not accepted.
- `allowed_for_live=false` in all outputs.

## Artifacts

The bridge writes:

- `pm_bot/trading_core/artifacts/discovery_to_token_resolver_bridge_071d/discovery_to_token_resolver_bridge_071d_result.json`
- `pm_bot/trading_core/artifacts/discovery_to_token_resolver_bridge_071d/latest_discovery_to_token_resolver_bridge_status_071d.json`
- `pm_bot/trading_core/artifacts/discovery_to_token_resolver_bridge_071d/discovery_to_token_candidate_contract_071d.json`
- `pm_bot/trading_core/artifacts/discovery_to_token_resolver_bridge_071d/discovery_to_token_operator_selection_required_071d.json`
- `pm_bot/trading_core/artifacts/discovery_to_token_resolver_bridge_071d/discovery_to_token_resolver_bridge_safety_snapshot_071d.json`
- `pm_bot/trading_core/artifacts/discovery_to_token_resolver_bridge_071d/discovery_to_token_resolver_bridge_operator_summary_071d.md`

## Safety Statement

071D is non-executable. It produces a target candidate contract only. Live execution, order generation, signing, submission, cancellation, wallet use, authenticated trading, browser automation, schedulers, daemons, background workers, and autonomous trading remain blocked.
