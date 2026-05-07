# PMBOT Source Evidence Enrichment Design

## Summary

This is a design-only local/read-only enrichment plan for PMBOT LLM market packets. It defines future adapter shapes that can improve packet evidence completeness without live data fetching, runtime wiring, queue mutation, wallet/order access, or market action guidance.

- schema_version: source_evidence_enrichment_design.v1
- task_id: PMBOT-SOURCE-001-EVIDENCE-ENRICHMENT-DESIGN-FROM-INVENTORY
- status: enrichment_design_created
- implementation_status: design_only
- live_adapters_implemented: false
- network_code_added: false
- openrouter_calls_performed: 0
- polymarket_api_calls_performed: 0
- network_calls_performed: 0

## Adapter Designs

### resolution_source_extractor_local

- purpose: Extract resolution/rule snippets from local packet fields and mark gaps explicitly.
- allowed_data_source_type: local_file
- current_implementation_status: design_only
- requires_network: false
- future_network_possible: false
- artifact_paths_it_would_produce: pm_bot/llm/future_resolution_source_extractor_output.v1.json
- category_applicability: company/business, crypto, elections, legal/courts, politics

### category_field_normalizer

- purpose: Normalize category-specific fields from title/question and local packet snippets.
- allowed_data_source_type: local_file
- current_implementation_status: design_only
- requires_network: false
- future_network_possible: false
- artifact_paths_it_would_produce: pm_bot/llm/future_category_field_normalizer_output.v1.json
- category_applicability: company/business, crypto, elections, legal/courts, politics

### packet_completeness_scorer

- purpose: Compute deterministic evidence readiness scores for local packet artifacts.
- allowed_data_source_type: local_file
- current_implementation_status: design_only
- requires_network: false
- future_network_possible: false
- artifact_paths_it_would_produce: pm_bot/llm/current_llm_packet_evidence_readiness_scores.v1.json
- category_applicability: company/business, crypto, elections, legal/courts, politics

### source_gap_normalizer

- purpose: Standardize missing evidence and source gap notes from local packet JSON.
- allowed_data_source_type: local_file
- current_implementation_status: design_only
- requires_network: false
- future_network_possible: false
- artifact_paths_it_would_produce: pm_bot/llm/future_source_gap_normalizer_output.v1.json
- category_applicability: company/business, crypto, elections, legal/courts, politics

### contradiction_context_builder

- purpose: Build local contradiction context sections from packet text only.
- allowed_data_source_type: local_file
- current_implementation_status: design_only
- requires_network: false
- future_network_possible: false
- artifact_paths_it_would_produce: pm_bot/llm/future_contradiction_context_builder_output.v1.json
- category_applicability: company/business, crypto, elections, legal/courts, politics

### operator_checklist_standardizer

- purpose: Create standardized operator checklist sections for local packet review.
- allowed_data_source_type: local_file
- current_implementation_status: design_only
- requires_network: false
- future_network_possible: false
- artifact_paths_it_would_produce: pm_bot/llm/future_operator_checklist_standardizer_output.v1.json
- category_applicability: company/business, crypto, elections, legal/courts, politics

### local_snapshot_evidence_reader

- purpose: Read manually exported local snapshots and attach provenance-only evidence notes.
- allowed_data_source_type: local_snapshot
- current_implementation_status: design_only
- requires_network: false
- future_network_possible: false
- artifact_paths_it_would_produce: pm_bot/llm/future_local_snapshot_evidence_reader_output.v1.json
- category_applicability: company/business, crypto, elections, legal/courts, politics

### future_read_only_polymarket_gamma_snapshot_importer

- purpose: Design-only importer for a future approved read-only Polymarket Gamma snapshot.
- allowed_data_source_type: future_read_only_api
- current_implementation_status: design_only
- requires_network: false
- future_network_possible: true
- artifact_paths_it_would_produce: pm_bot/llm/future_polymarket_gamma_snapshot_import_manifest.v1.json
- category_applicability: company/business, crypto, elections, legal/courts, politics

### future_category_specific_source_adapter

- purpose: Design-only category-specific adapter family for approved manually exported or future read-only sources.
- allowed_data_source_type: manually_exported_source
- current_implementation_status: design_only
- requires_network: false
- future_network_possible: true
- artifact_paths_it_would_produce: pm_bot/llm/future_category_specific_source_adapter_output.v1.json
- category_applicability: company/business, crypto, elections, legal/courts, politics

## Safety Constraints

- design only
- no live API adapters implemented
- no OpenRouter calls
- no Polymarket API calls
- no network calls
- no credentials, wallet, orders, queue, runtime, dispatcher, background workers, or browser automation
- no market action guidance
