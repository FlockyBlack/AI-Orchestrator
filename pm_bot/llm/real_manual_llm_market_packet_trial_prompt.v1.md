# PMBOT Manual LLM Paste-In Prompt v1

## Offline Boundary
This is offline analysis only and not trading advice. The packet below is sanitized local PMBOT review context. Use it only to draft review-supporting notes for a human operator.

PMBOT is not calling an LLM service from code. A human operator manually pasted this prompt into an LLM UI.

## Output Contract
Return only strict JSON matching `llm_analysis_response_schema.v1.json`.
Return exactly one raw JSON object.
The first character must be `{` and the last character must be `}`.
Do not wrap the JSON in Markdown. Do not use ```json fences or any other code fences.
Do not include prose before or after the JSON object. Any Markdown fencing makes the response invalid.
Use the packet_id from the packet. Use contract_version `llm_analysis_response.v1`.

Required response sections:
- concise_market_summary
- key_uncertainties
- missing_evidence
- contradiction_checks
- risk_notes
- operator_review_checklist
- suggested_research_questions
- citation_or_source_gap_notes
- safety_acknowledgement

## Forbidden Output Constraints
- Do not include probability estimates.
- Do not include EV.
- Do not include edge.
- Do not include scoring.
- Do not include recommended side.
- Do not include bet recommendations.
- Do not include order size.
- Do not include price target.
- Do not include execution instruction.
- Do not include wallet/private-key/credential handling.
- Do not include certainty claims.

Also do not include market decisions, side selection, trade instructions, autonomous actions, or claims of certainty.

## Response Schema
```json
{
  "$id": "PMBOT_LLM_ANALYSIS_RESPONSE.v1",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "additionalProperties": false,
  "contract_boundary": {
    "deterministic_validation": true,
    "llm_api_defined": false,
    "local_only": true,
    "operator_review_only": true,
    "outcome_estimation_defined": false,
    "runtime_integration_defined": false,
    "side_selection_defined": false,
    "strategy_defined": false,
    "trading_or_ordering_defined": false,
    "value_scoring_defined": false
  },
  "description": "Offline-only local contract for a manually supplied LLM analysis response. The response is limited to review-supporting notes and must not include side selection, outcome estimates, value scoring, execution instructions, wallet instructions, autonomous actions, or certainty claims.",
  "properties": {
    "citation_or_source_gap_notes": {
      "items": {
        "minLength": 1,
        "type": "string"
      },
      "minItems": 1,
      "type": "array"
    },
    "concise_market_summary": {
      "minLength": 1,
      "type": "string"
    },
    "contract_version": {
      "const": "llm_analysis_response.v1"
    },
    "contradiction_checks": {
      "items": {
        "additionalProperties": false,
        "properties": {
          "check_result": {
            "enum": [
              "no_conflict_seen",
              "possible_conflict",
              "needs_more_source_review",
              "not_checked"
            ]
          },
          "notes": {
            "minLength": 1,
            "type": "string"
          },
          "topic": {
            "minLength": 1,
            "type": "string"
          }
        },
        "required": [
          "topic",
          "check_result",
          "notes"
        ],
        "type": "object"
      },
      "minItems": 1,
      "type": "array"
    },
    "key_uncertainties": {
      "items": {
        "minLength": 1,
        "type": "string"
      },
      "minItems": 1,
      "type": "array"
    },
    "missing_evidence": {
      "items": {
        "minLength": 1,
        "type": "string"
      },
      "minItems": 1,
      "type": "array"
    },
    "operator_review_checklist": {
      "items": {
        "minLength": 1,
        "type": "string"
      },
      "minItems": 1,
      "type": "array"
    },
    "packet_id": {
      "minLength": 1,
      "pattern": "llm-analysis-packet-[a-z0-9-]+",
      "type": "string"
    },
    "response_id": {
      "minLength": 1,
      "pattern": "llm-analysis-response-[a-z0-9-]+",
      "type": "string"
    },
    "risk_notes": {
      "items": {
        "minLength": 1,
        "type": "string"
      },
      "minItems": 1,
      "type": "array"
    },
    "safety_acknowledgement": {
      "additionalProperties": false,
      "properties": {
        "local_only": {
          "const": true
        },
        "manual_review_only": {
          "const": true
        },
        "no_autonomous_actions": {
          "const": true
        },
        "no_outcome_estimates": {
          "const": true
        },
        "no_recommendations": {
          "const": true
        },
        "no_trade_or_wallet_instructions": {
          "const": true
        },
        "no_value_scoring": {
          "const": true
        },
        "offline_only": {
          "const": true
        },
        "uncertain_claims_marked": {
          "const": true
        }
      },
      "required": [
        "offline_only",
        "local_only",
        "manual_review_only",
        "no_recommendations",
        "no_outcome_estimates",
        "no_value_scoring",
        "no_trade_or_wallet_instructions",
        "no_autonomous_actions",
        "uncertain_claims_marked"
      ],
      "type": "object"
    },
    "suggested_research_questions": {
      "items": {
        "minLength": 1,
        "type": "string"
      },
      "minItems": 1,
      "type": "array"
    }
  },
  "required": [
    "contract_version",
    "response_id",
    "packet_id",
    "concise_market_summary",
    "key_uncertainties",
    "missing_evidence",
    "contradiction_checks",
    "risk_notes",
    "operator_review_checklist",
    "suggested_research_questions",
    "citation_or_source_gap_notes",
    "safety_acknowledgement"
  ],
  "schema_version": "llm_analysis_response_schema.v1",
  "title": "PMBOT LLM Analysis Response v1",
  "type": "object"
}
```

## Safe LLM Analysis Packet
Use only this packet content. Do not infer from unstated external data.

```json
{
  "contract_version": "llm_analysis_packet.v1",
  "evidence_summary": [
    {
      "claim_summary": "The trial packet is derived from the existing safe PMBOT-LLM example packet.",
      "evidence_id": "evidence-real-manual-trial-001",
      "limitation_note": "The source is not a live market packet and must not be treated as current market evidence.",
      "relevance_note": "The source keeps the first manual market packet trial deterministic and local.",
      "source_reference": "pm_bot/llm/example_llm_analysis_packet.v1.json",
      "source_type": "fixture"
    },
    {
      "claim_summary": "The operator review pack exists as a passive local workbench surface, but this trial does not transform it into a new decision artifact.",
      "evidence_id": "evidence-real-manual-trial-002",
      "limitation_note": "This packet does not import workbench runtime code and does not use accounting summaries for market guidance.",
      "relevance_note": "The workbench artifact can show prior manual LLM validation status without adding runtime behavior.",
      "source_reference": "pm_bot/workbench/operator_review_pack.v1.json",
      "source_type": "operator_artifact"
    }
  ],
  "forbidden_outputs": [
    "recommended_side",
    "bet_yes_or_no",
    "order_size",
    "price_target",
    "probability",
    "implied_probability",
    "fair_value",
    "ev",
    "edge",
    "expected_return",
    "kelly_sizing",
    "execution_instruction",
    "auto_trade_instruction",
    "wallet_instruction",
    "market_outcome_certainty_claim"
  ],
  "generated_at": "deterministic-real-manual-llm-market-packet-trial-packet.v1",
  "known_limitations": [
    "This trial is example_packet_trial_not_live_market and does not use live market data.",
    "The packet does not include executable commands or endpoint data.",
    "The packet is for manual review support only."
  ],
  "market_context": {
    "market_id": "example-pmbot-llm-007-market",
    "market_status": "unknown",
    "market_title": "Example fixture market for PMBOT-LLM-007 manual packet trial",
    "outcome_labels": [
      "Yes",
      "No"
    ],
    "public_resolution_context": "Fixture-only resolution context copied from the existing safe PMBOT-LLM example packet; this is not a live market artifact."
  },
  "normalized_market_summary": {
    "data_freshness_note": "Fixture timestamp is deterministic; no live data is fetched and no current market state is implied.",
    "excluded_fields_note": "No credentials, wallet data, executable commands, endpoint data, order placement fields, outcome estimates, value scoring, or side selection requests are included.",
    "outcome_labels": [
      "Yes",
      "No"
    ],
    "question_text": "Will the example fixture event satisfy the stated local resolution rule?",
    "resolution_rules_summary": "The local fixture says the event must be confirmed by the specified public source before the deadline.",
    "status": "unknown"
  },
  "operator_questions": [
    "Which evidence gaps should the operator review first?",
    "Which local claims need source-date verification?",
    "Where do local artifact summaries remain ambiguous?"
  ],
  "packet_id": "llm-analysis-packet-real-manual-market-packet-trial-001",
  "required_response_sections": [
    "concise_market_summary",
    "key_uncertainties",
    "missing_evidence",
    "contradiction_checks",
    "risk_notes",
    "operator_review_checklist",
    "suggested_research_questions",
    "citation_or_source_gap_notes",
    "safety_acknowledgement"
  ],
  "research_summary": {
    "completed_sections": [
      "safe example packet source selected",
      "manual trial boundaries recorded"
    ],
    "open_questions": [
      "Confirm which local evidence gaps matter before a real manually saved response is reviewed.",
      "Check whether any local artifact summaries are ambiguous or stale."
    ],
    "research_status": "partial_manual_review",
    "summary": "Manual notes identify the local fixture source and unresolved evidence checks for operator review."
  },
  "safety_constraints": {
    "local_files_only": true,
    "manual_review_only": true,
    "no_autonomous_paper_orders": true,
    "no_credentials": true,
    "no_dispatcher_changes": true,
    "no_live_trading": true,
    "no_llm_api_calls": true,
    "no_market_decisions": true,
    "no_network_calls": true,
    "no_outcome_estimates": true,
    "no_prompt_automation": true,
    "no_real_orders": true,
    "no_runtime_wiring": true,
    "no_side_selection": true,
    "no_trading_endpoints": true,
    "no_value_or_advantage_scoring": true,
    "no_wallet_or_key_material": true,
    "offline_only": true
  },
  "source_artifacts": [
    {
      "artifact_type": "llm_safe_example_packet",
      "description": "Existing PMBOT-LLM safe example packet used as the deterministic local source for the first manual market packet trial.",
      "path": "pm_bot/llm/example_llm_analysis_packet.v1.json",
      "sanitization_status": "fixture_only"
    }
  ]
}
```

## Final Instruction
Produce one JSON object that validates against the response schema and remains within the offline, manual-review-only boundary. Acceptance is operator-review readiness only, never trading approval.
