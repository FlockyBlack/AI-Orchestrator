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
- Do not include numeric likelihood estimates.
- Do not include abbreviated value terms.
- Do not include value-comparison language.
- Do not include scoring or rating labels.
- Do not include outcome selection.
- Do not include betting guidance.
- Do not include order sizing.
- Do not include price targets.
- Do not include execution instructions.
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
      "claim_summary": "Local rule reference was copied into the packet for structural review.",
      "evidence_id": "evidence-real-local-market-824952-001",
      "limitation_note": "The trial does not fetch, refresh, resolve, or verify the referenced source.",
      "relevance_note": "This local dossier field gives the operator source-coverage context for manual review.",
      "source_reference": "pm_bot/research/selected_ingest_final_dossier_drafts.v1.json",
      "source_type": "official_source_reference"
    },
    {
      "claim_summary": "Official source placeholder was documented as source coverage context.",
      "evidence_id": "evidence-real-local-market-824952-002",
      "limitation_note": "The trial does not fetch, refresh, resolve, or verify the referenced source.",
      "relevance_note": "This local dossier field gives the operator source-coverage context for manual review.",
      "source_reference": "pm_bot/research/selected_ingest_final_dossier_drafts.v1.json",
      "source_type": "official_source_reference"
    },
    {
      "claim_summary": "Credible news placeholder was documented as source coverage context.",
      "evidence_id": "evidence-real-local-market-824952-003",
      "limitation_note": "The trial does not fetch, refresh, resolve, or verify the referenced source.",
      "relevance_note": "This local dossier field gives the operator source-coverage context for manual review.",
      "source_reference": "pm_bot/research/selected_ingest_final_dossier_drafts.v1.json",
      "source_type": "news_source_reference"
    },
    {
      "claim_summary": "Manual review still needs human judgment on source completeness.",
      "evidence_id": "evidence-real-local-market-824952-004",
      "limitation_note": "The note is not a source check, truth check, estimate, score, or decision.",
      "relevance_note": "This local uncertainty note keeps unresolved review context visible.",
      "source_reference": "pm_bot/research/selected_ingest_final_dossier_drafts.v1.json",
      "source_type": "manual_note"
    },
    {
      "claim_summary": "Artifact validation does not determine the market outcome.",
      "evidence_id": "evidence-real-local-market-824952-005",
      "limitation_note": "The note is not a source check, truth check, estimate, score, or decision.",
      "relevance_note": "This local uncertainty note keeps unresolved review context visible.",
      "source_reference": "pm_bot/research/selected_ingest_final_dossier_drafts.v1.json",
      "source_type": "manual_note"
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
  "generated_at": "deterministic-real-local-market-llm-trial-packet.v1",
  "known_limitations": [
    "The packet is derived from a local artifact only and does not fetch or refresh external data.",
    "The packet omits numeric market fields and accounting values to stay within manual review boundaries.",
    "The packet is a review aid only and does not evaluate truth, select outcomes, or authorize action."
  ],
  "market_context": {
    "market_id": "824952",
    "market_status": "unknown",
    "market_title": "MicroStrategy sells any Bitcoin by December 31, 2026?",
    "outcome_labels": [
      "Yes",
      "No"
    ],
    "public_resolution_context": "Stub-only local market description excerpt for 'MicroStrategy sells any Bitcoin by December 31, 2026?': This market will resolve to \"Yes\" if MicroStrategy sells any of its Bitcoin by 11:59 PM ET on the date specified in the title. Otherwise, this market will resolve to \"No\". Manual completion must review the full local criteria before use."
  },
  "normalized_market_summary": {
    "data_freshness_note": "Derived only from an existing local PMBOT artifact; no live data, API, or network refresh is used.",
    "excluded_fields_note": "Source numeric market fields and accounting fields are intentionally omitted. No credentials, wallet data, executable commands, endpoint data, order placement fields, outcome estimates, value metrics, or side selection requests are included.",
    "outcome_labels": [
      "Yes",
      "No"
    ],
    "question_text": "MicroStrategy sells any Bitcoin by December 31, 2026?",
    "resolution_rules_summary": "Stub-only local market description excerpt for 'MicroStrategy sells any Bitcoin by December 31, 2026?': This market will resolve to \"Yes\" if MicroStrategy sells any of its Bitcoin by 11:59 PM ET on the date specified in the title. Otherwise, this market will resolve to \"No\". Manual completion must review the full local criteria before use.",
    "status": "unknown"
  },
  "operator_questions": [
    "Which source gaps should the operator review first?",
    "Which local claims need source-date verification?",
    "Where do local artifact summaries remain ambiguous or incomplete?"
  ],
  "packet_id": "llm-analysis-packet-real-local-market-824952",
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
      "evidence_inventory",
      "human_review_summary",
      "market_overview",
      "resolution_rules",
      "source_coverage_notes",
      "uncertainty_notes",
      "unresolved_questions"
    ],
    "open_questions": [],
    "research_status": "manual_review_ready",
    "summary": "Local selected_ingest_final_dossier_draft artifact records market context, resolution notes, source coverage placeholders, uncertainty notes, and human-review notes for manual review only."
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
      "artifact_type": "selected_ingest_final_dossier_draft",
      "description": "Existing local PMBOT market/research artifact selected for the real-local-market manual LLM trial; safe summary fields only are copied into this packet.",
      "path": "pm_bot/research/selected_ingest_final_dossier_drafts.v1.json",
      "sanitization_status": "safe_public_or_local_artifact_reference_only"
    }
  ]
}
```

## Final Instruction
Produce one JSON object that validates against the response schema and remains within the offline, manual-review-only boundary. Acceptance is operator-review readiness only, never trading approval.
