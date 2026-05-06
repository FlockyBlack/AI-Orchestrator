# PMBOT LLM Analysis Contract v1

This directory defines an offline-only contract layer for future manual LLM review of sanitized PMBOT market, research, and operator artifacts.

## Non-goals

- No live API or network calls.
- No LLM API calls.
- No credentials, wallet material, private keys, signing, or trading endpoint data.
- No real orders, live trading, or autonomous paper orders.
- No outcome estimates, value scoring, advantage scoring, strategy, side selection, or market decision.
- No runtime wiring, dispatcher changes, run_codex changes, or prompt automation.

## Packet

`llm_analysis_packet_schema.v1.json` describes the local input packet shape. A valid packet contains:

- `contract_version`
- `packet_id`
- `generated_at`
- `source_artifacts`
- `market_context`
- `normalized_market_summary`
- `research_summary`
- `evidence_summary`
- `operator_questions`
- `known_limitations`
- `forbidden_outputs`
- `required_response_sections`
- `safety_constraints`

The packet may reference local artifact paths and sanitized market context. It must not contain credentials, wallet data, executable commands, endpoint details, order placement fields, autonomous action requests, outcome-estimation requests, value-scoring requests, or side-selection requests.

## Response

`llm_analysis_response_schema.v1.json` allows only these response sections:

- `concise_market_summary`
- `key_uncertainties`
- `missing_evidence`
- `contradiction_checks`
- `risk_notes`
- `operator_review_checklist`
- `suggested_research_questions`
- `citation_or_source_gap_notes`
- `safety_acknowledgement`

Any extra field is rejected. The validator also rejects explicit forbidden fields such as `recommended_side`, `bet_yes_or_no`, `order_size`, `price_target`, `probability`, `implied_probability`, `fair_value`, `EV`, `edge`, `expected_return`, `Kelly sizing`, `execution_instruction`, `auto_trade_instruction`, and `wallet_instruction`.

## Deterministic Pattern Scan

`validate_llm_analysis_artifacts.py` performs a deterministic case-insensitive regex scan over response strings and over packet response-directing fields (`operator_questions` and `required_response_sections`). The packet field `forbidden_outputs` is intentionally not scanned for phrase hits because it is the place where prohibited outputs are listed.

Forbidden phrase patterns include:

- `recommended side`
- `bet on`
- `place order`
- `buy YES`
- `buy NO`
- `sell YES`
- `sell NO`
- `EV`
- `edge`
- `Kelly`
- `fair probability`
- `my probability`
- `autotrade`
- `execute trade`

The scan uses word boundaries for short tokens such as `EV` and `edge`, so ordinary words such as `evidence` are not rejected. The validator also rejects a small set of certainty-claim phrases such as `outcome is certain`, `market outcome is certain`, `will definitely`, and `guaranteed outcome`.

Unsupported factual claims cannot be fully proven by deterministic local validation. The v1 contract handles that boundary by requiring `citation_or_source_gap_notes` and `safety_acknowledgement.uncertain_claims_marked`.

## Validator Output

The validator returns structured JSON:

- `status`: `accepted` or `rejected`
- `errors`
- `warnings`
- `safety_flags`
- `artifact_paths`
- `checks`

Default local validation:

```powershell
python pm_bot\llm\validate_llm_analysis_artifacts.py
```

Explicit local files:

```powershell
python pm_bot\llm\validate_llm_analysis_artifacts.py --packet pm_bot\llm\example_llm_analysis_packet.v1.json --response pm_bot\llm\example_llm_analysis_response_valid.v1.json
```
