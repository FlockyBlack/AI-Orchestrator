# PMBOT-LLM-001 Analysis Packet Contract

## Scope

PMBOT-LLM-001 adds a deterministic local contract layer for future manual LLM review loops:

`PMBOT artifact -> safe LLM packet -> LLM response -> validator -> operator review pack`

This task does not connect an LLM API, does not add runtime integration, and does not change the operator workbench entrypoint.

## Added Artifacts

- `pm_bot/llm/llm_analysis_packet_schema.v1.json`
- `pm_bot/llm/llm_analysis_response_schema.v1.json`
- `pm_bot/llm/example_llm_analysis_packet.v1.json`
- `pm_bot/llm/example_llm_analysis_response_valid.v1.json`
- `pm_bot/llm/example_llm_analysis_response_invalid_forbidden_recommendation.v1.json`
- `pm_bot/llm/validate_llm_analysis_artifacts.py`
- `pm_bot/llm/llm_analysis_contract.v1.md`
- `pm_bot/llm/tests/test_validate_llm_analysis_artifacts.py`

## Safety Boundary

The contract is offline-only and local-file-only. It explicitly excludes:

- live API calls
- LLM API calls
- credentials and wallet material
- trading endpoint data
- real orders and live trading
- autonomous paper orders
- outcome estimates
- value scoring
- side selection
- market decisions
- runtime wiring
- dispatcher or run_codex changes
- prompt automation

## Validation Behavior

The validator:

- validates packet JSON against the packet schema
- validates response JSON against the response schema
- rejects forbidden response fields
- rejects deterministic forbidden language patterns
- rejects packet response-directing fields that request prohibited outputs
- returns structured `accepted` or `rejected` reports with errors, warnings, safety flags, and artifact paths

The validator is standard-library-only and does not import network, LLM, wallet, trading, runtime, or subprocess clients.

## Runtime Integration

No runtime integration was added. `pm_bot/workbench/run_operator_workbench_export.py`, dispatcher files, and run_codex files are intentionally untouched.
