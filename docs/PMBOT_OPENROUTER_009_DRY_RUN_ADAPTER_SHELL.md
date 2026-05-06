# PMBOT OpenRouter 009 Dry-Run Adapter Shell

Task: `PMBOT-OPENROUTER-009-DRY-RUN-ADAPTER-SHELL`

## Purpose

This task adds a dry-run-only PMBOT OpenRouter adapter shell:

```text
pm_bot/llm/run_openrouter_adapter.py
```

The shell plans a future single-prompt adapter invocation and writes local operator artifacts. It does not call OpenRouter, does not read any environment key, does not import runtime/workbench/dispatcher modules, and does not write accepted LLM responses into review queues.

The boundary remains analysis-only, manual-review-only, operator-gated, validator-gated, and deterministic/local-first where possible.

## Non-Goals

This task explicitly excludes:

- No OpenRouter calls.
- No network behavior.
- No API key or environment key read.
- No runtime wiring.
- No workbench integration.
- No dispatcher integration.
- No automatic LLM loops.
- No background autonomous operation.
- No review queue writes.
- No wallet, private-key, credential, or order access.
- No market decisions.
- No trading recommendations.
- No side selection.
- No probabilities.
- No EV, edge, or scoring.
- No buy, sell, hold, enter, or exit instructions.

## CLI Examples

```powershell
python pm_bot/llm/run_openrouter_adapter.py --market-id 563650 --dry-run
python pm_bot/llm/run_openrouter_adapter.py --prompt-path pm_bot/llm/manual_packet_batch/563650_prompt.v1.md --dry-run
python pm_bot/llm/run_openrouter_adapter.py --market-id 563650 --dry-run --model-profile sonnet_gpt55_critic
python pm_bot/llm/run_openrouter_adapter.py --market-id 563650 --dry-run --out-dir pm_bot/llm/openrouter_adapter_dry_runs
```

`--dry-run` is required for accepted operation. `--manual-confirm-network` exists only as a future-looking boundary flag in this task and is rejected with `blocked_network_not_implemented`.

## Dry-Run Boundary

The adapter shell only resolves local prompt and packet paths, validates the inert model profile shape, and writes dry-run artifacts. It records the following safety facts in every summary:

- `network_calls_made: false`
- `api_key_read: false`
- `runtime_wiring: false`
- `dispatcher_integration: false`
- `wallet_or_orders: false`
- `trading_decision: false`
- `analysis_only: true`
- `manual_review_only: true`
- `operator_gated: true`
- `validator_gated: true`
- `no_runtime_wiring: true`
- `no_dispatcher_integration: true`
- `no_wallet_or_orders: true`
- `no_trading_decision: true`
- `no_network_calls: true`

## Relation To 008 Contract

Task 008 added `pm_bot/llm/openrouter_adapter_contract.v1.json` as a design-only, inert reference contract. The 009 shell reads that JSON only for dry-run validation of the selected model profile. The contract is still not runtime authority, is not imported into runtime paths, and does not enable network behavior.

For `sonnet_gpt55_critic`, the shell validates:

- Candidate model: `anthropic/claude-sonnet-4.5`
- Critic model: `openai/gpt-5.5`
- Critic contract version: `pmbot_openrouter_critic_response.v1`
- `manual_invocation_required: true`
- `single_prompt_per_invocation: true`

## Selection Rules

Prompt selection is deterministic:

1. If `--prompt-path` is provided, use it.
2. If `--market-id` is provided and `--prompt-path` is omitted, resolve `pm_bot/llm/manual_packet_batch/<market_id>_prompt.v1.md`.
3. If `--packet-path` is omitted and a market id is available, infer `pm_bot/llm/manual_packet_batch/<market_id>_packet.v1.json`.
4. If neither `--market-id` nor `--prompt-path` is provided, select the first sorted prompt from `pm_bot/llm/manual_packet_batch/*_prompt.v1.md`.
5. Never auto-select `pm_bot/llm/real_local_market_llm_trial_prompt.v1.md`.
6. If the selected prompt is missing, return `blocked_missing_prompt`.
7. If the packet is missing, keep the run non-fatal and record `selected_packet_path: null` with warning `missing_packet`.

## Artifact Outputs

Dry-run artifacts are written under:

```text
pm_bot/llm/openrouter_adapter_dry_runs/
```

That directory is ignored by git. The shell writes:

- `adapter_dry_run_summary_<market_id_or_timestamp>.v1.json`
- `operator_next_action_<market_id_or_timestamp>.md`

The planned future adapter outputs are listed in the summary for operator review only:

- `adapter_run_summary.v1.json`
- `candidate_raw.json`
- `candidate_content.json`
- `candidate_validation.json`
- `critic_raw.json`
- `critic_content.json`
- `critic_validation.json`
- `operator_next_action.md`

## Statuses

The 009 shell uses this terminal status set:

- `dry_run_ready`
- `blocked_missing_prompt`
- `blocked_invalid_contract`
- `blocked_invalid_args`
- `blocked_runtime_boundary`
- `blocked_network_not_implemented`

## Security Notes

No OpenRouter calls are made in this task. No env key is read, including `OPENROUTER_API_KEY`. No credential header is built. No API key, wallet, private key, credential store, browser profile, or auth file is read or touched.

The shell does not import or call `pm_bot/workbench/run_operator_workbench_export.py`, runtime dispatchers, the previous OpenRouter prompt harness, wallet/order modules, or any network library.

## Next Allowed Task

The next allowed task is one of:

```text
PMBOT-OPENROUTER-010-MANUAL-NETWORK-ADAPTER-PROPOSAL
PMBOT-OPENROUTER-010-MANUAL-NETWORK-ADAPTER-GATED-IMPLEMENTATION
```

Either requires explicit operator approval first. Runtime wiring, workbench integration, dispatcher integration, autonomous loops, trading decisions, wallet/order behavior, and review queue writes remain out of scope.
