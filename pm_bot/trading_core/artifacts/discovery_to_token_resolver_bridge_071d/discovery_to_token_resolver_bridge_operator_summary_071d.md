# PMBOT Discovery to Token Resolver Bridge 071D

- Status: `blocked_no_latest_discovery_artifact`
- Market: `BTC`
- Strategy: `tiny-momentum`
- Mode: `discovery to token resolver bridge / dry-run / no-trading`
- target_contract_only: `true`
- target_contract_executable: `false`
- allowed_for_live: `false`

## Source Discovery

- artifact_present: `false`
- discovery_result_path: `missing`
- source_backed_candidate_count: `0`
- valid_source_backed_candidate_count: `0`

## Target Candidate Contract

- market_slug: `blocked`
- condition_id: `missing_optional`
- token_id: `blocked`
- outcome_name: `missing`
- token_id_source: `blocked_no_selected_source_backed_token_id`
- token_id_generated: `false`
- fake_token_id_generated: `false`

## Valid Source-Backed Candidates

- none

## Safety

- no order payload generated
- no signing attempted
- no order submission attempted
- no order cancellation attempted
- no wallet connection attempted
- no authenticated trading call attempted
- no browser automation added
- no scheduler, daemon, background worker, or autonomous loop added
- token IDs are copied only from source-backed discovery candidates

## Blockers

- No latest 071A public discovery artifact was present.
- allowed_for_live=false and this task does not authorize live execution.
- Only a target candidate contract may be produced; no order payload is generated.
- Signing and signed payload generation remain blocked.
- Order submission and cancellation remain blocked.
- Authenticated trading calls are not performed by this bridge.
