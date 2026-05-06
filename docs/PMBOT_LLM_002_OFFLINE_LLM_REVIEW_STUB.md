# PMBOT-LLM-002 Offline LLM Review Stub

## Scope

PMBOT-LLM-002 adds a deterministic local review stub loop on top of the PMBOT-LLM-001 contract:

`LLM analysis packet JSON -> fixture/mock LLM response JSON -> PMBOT-LLM-001 validator -> accepted/rejected review result JSON -> Markdown operator summary`

The stub only loads local JSON artifacts, validates them, and exports deterministic operator-facing review files.

## What It Does

- Loads a local LLM analysis packet JSON.
- Loads a local fixture or mock LLM response JSON.
- Validates both artifacts with `pm_bot/llm/validate_llm_analysis_artifacts.py`.
- Writes `pm_bot/llm/offline_llm_review_stub.v1.json`.
- Writes `pm_bot/llm/offline_llm_review_stub.v1.md`.
- Uses a fixed deterministic generated marker instead of wall-clock time so fixture comparisons remain stable.
- Reports allowed response sections that are present.
- Reports forbidden response fields or forbidden language patterns found by the LLM-001 validator.

## What It Does Not Do

- No live API or network calls.
- No LLM API calls.
- No credentials, wallet material, private keys, signing, or trading endpoint access.
- No real orders, live trading, or autonomous paper orders.
- No probability estimates, value scoring, advantage scoring, strategy, side selection, or market decisions.
- No runtime wiring, dispatcher changes, run_codex changes, workbench entrypoint changes, or prompt automation.
- No LLM text generation. The response JSON must already exist as a local file.

## Validator Use

The exporter imports the existing PMBOT-LLM-001 validator module and calls:

- `validate_packet_payload`
- `validate_response_payload`

The same packet schema, response schema, allowed response sections, forbidden field names, forbidden phrase patterns, certainty phrase patterns, and safety flags from PMBOT-LLM-001 remain authoritative.

## Operator Reading

An `accepted` result means the packet and response passed deterministic local validation. It does not mean the response is correct, complete, fresh, useful, or safe for any trading decision. The operator should review the listed sections against local source artifacts and manually record unresolved evidence gaps.

A `rejected` result means the packet or response failed deterministic local validation. The operator should inspect the exported errors, correct or replace the local JSON artifact, and rerun the exporter before using the response downstream.

The Markdown summary is intended for quick operator review. The JSON result is the stable machine-readable artifact for tests and future tooling.

## Why Manual Paste-In Is Not Added Yet

Manual paste-in and API-assisted review are intentionally deferred. This task proves the offline validation and export boundary first, without adding prompt handling, runtime wiring, authentication surfaces, or accidental execution paths.

## Local Usage

```powershell
python pm_bot\llm\export_offline_llm_review_stub.py `
  --packet pm_bot\llm\example_llm_analysis_packet.v1.json `
  --response pm_bot\llm\example_llm_analysis_response_valid.v1.json `
  --out-json pm_bot\llm\offline_llm_review_stub.v1.json `
  --out-md pm_bot\llm\offline_llm_review_stub.v1.md
```

The command exits with `0` for an accepted result and `1` for a rejected result after writing the JSON and Markdown review artifacts.

## Next Recommended Task

`PMBOT-LLM-003-MANUAL-LLM-PASTE-IN-REVIEW`
