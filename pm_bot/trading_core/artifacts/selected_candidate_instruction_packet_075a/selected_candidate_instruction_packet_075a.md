# PMBOT Selected Candidate Instruction Packet 075A

- Status: `operator_selection_required`
- Market: `BTC`
- Strategy: `tiny-momentum`
- Mode: `selected candidate instruction packet / dry-run / review-only / no-live`
- allowed_for_live: `false`
- instruction_packet_executable_for_live: `false`
- selected_candidate_artifact_written: `false`
- selected_token_artifact_written: `false`
- candidate_index_base: `0`

## Why Manual Selection Is Required

- Multiple source-backed candidates are available for different outcomes; 075A must not infer operator intent or choose a candidate automatically.

## Candidates

- Candidate index `0`
  Market: `MicroStrategy sells any Bitcoin by December 31, 2026?`
  Outcome: `Yes`
  Token ID: `111128...7287`
  Evidence: `source candidate id operator-token-selection-candidate-073b-a289a2a3160e27ca; source-backed by public_market_token_discovery_071a, operator_token_selection_packet_073b; local artifact pm_bot/trading_core/artifacts/public_market_token_discovery_071a/public_market_token_discovery_071a_result.json; full token ID is present only in the source artifact and intentionally shortened here`
  Command: `python -m pm_bot.operator_runner.operator_token_selection_packet --market BTC --strategy tiny-momentum --dry-run --candidate-index 0`
- Candidate index `1`
  Market: `MicroStrategy sells any Bitcoin by December 31, 2026?`
  Outcome: `No`
  Token ID: `998075...8808`
  Evidence: `source candidate id operator-token-selection-candidate-073b-5917575ff7c9263d; source-backed by public_market_token_discovery_071a, operator_token_selection_packet_073b; local artifact pm_bot/trading_core/artifacts/public_market_token_discovery_071a/public_market_token_discovery_071a_result.json; full token ID is present only in the source artifact and intentionally shortened here`
  Command: `python -m pm_bot.operator_runner.operator_token_selection_packet --market BTC --strategy tiny-momentum --dry-run --candidate-index 1`

## Safe CLI Command

Run the existing 073B dry-run selector only after manually choosing the candidate index:

```powershell
python -m pm_bot.operator_runner.operator_token_selection_packet --market BTC --strategy tiny-momentum --dry-run --candidate-index N
```

For a concrete candidate, replace `N` with that candidate's zero-based index.

## Requested Candidate

- candidate_index_provided: `false`
- candidate_index_status: `missing_optional`
- requested_candidate_available: `false`
- safe_cli_command: `not available`

## Warnings

- 075A does not select a token automatically.
- 075A does not write selected-token or selected-candidate artifacts.
- Running the displayed 073B dry-run command is still not live trading and is not approval to trade.
- No order payload is generated, signed, submitted, or cancelled.
