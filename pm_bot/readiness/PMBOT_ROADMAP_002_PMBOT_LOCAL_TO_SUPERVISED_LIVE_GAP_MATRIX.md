# PMBOT Roadmap 002 Local To Supervised Live Gap Matrix

Task: `PMBOT-ROADMAP-002-PMBOT-LOCAL-TO-SUPERVISED-LIVE-GAP-MATRIX`

Matrix: `pmbot-local-to-supervised-live-gap-matrix`
Contract: `pmbot_local_to_supervised_live_gap_matrix.v1`
Run mode: `local_static_supervised_live_gap_matrix`
Operator review: `pending_operator_review`

## Purpose

This matrix records the local review gaps that remain before any separately approved supervised live PMBOT review gate could be considered. It is a deterministic local operator review artifact only, using local docs, fixtures, and tests.

The matrix is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Static Fixture

The local fixture is:

`pm_bot/tests/fixtures/readiness/pmbot_local_to_supervised_live_gap_matrix.valid.json`

The fixture records fixed gate rows, local evidence references, required review evidence descriptions, validation commands, and closed safety boundaries. It is not runtime input and does not approve execution.

## Source Basis

Reviewed local PMBOT artifacts:

- `pm_bot/readiness/PMBOT_ROADMAP_001_REAL_WALLET_READINESS_BLOCKER_MATRIX.md`
- `docs/PMBOT_DASHBOARD_002_QUEUE_AND_PAPERLIVE_STATUS_SURFACE.md`
- `docs/PMBOT_SOURCE_LEDGER_001_UNIFIED_SOURCE_QUALITY_LEDGER_LOCAL_ONLY.md`
- `docs/PMBOT_PAPER_ACCOUNTING_002_PAPER_ONLY_ACCOUNTING_VALIDATOR_LOCAL_ONLY.md`
- `docs/PMBOT_PAPERLIVE_DECISION_001_SIMULATED_DECISION_PACKET_SCHEMA_NO_RECOMMENDATIONS.md`
- `docs/PMBOT_SAFETY_001_AUTONOMY_GATE_CHECKLIST_LOCAL_ONLY.md`
- `docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md`
- `pm_bot/tests/test_simulated_decision_packet_schema.py`
- `tests/test_codex_queue_pmbot_templates.py`

These sources keep PMBOT review surfaces local-only, static, paper-mode, and `pending_operator_review`.

## Gap Matrix

| Gate ID | Current Local State | Supervised Live Gap | Local Evidence Reference | Required Review Evidence |
| --- | --- | --- | --- | --- |
| `source_inventory_gate` | PMBOT task templates and dashboard records identify local docs, fixtures, and tests only. | Supervised review needs a human-checked source inventory naming every local file used for the session. | `tests/test_codex_queue_pmbot_templates.py` | Review record confirming source inventory, static inputs, and excluded paths. |
| `static_sample_boundary_gate` | Queue and paperlive status surfaces are static local records with pending operator review. | Supervised review needs a bounded sample record showing which static records are in scope and which are excluded. | `docs/PMBOT_DASHBOARD_002_QUEUE_AND_PAPERLIVE_STATUS_SURFACE.md` | Review record confirming sample scope, local references, and static-only status. |
| `source_quality_evidence_gate` | Source quality records are descriptive local artifacts with no endpoint calls. | Supervised review needs a human-reviewed source quality record tied to local evidence references. | `docs/PMBOT_SOURCE_LEDGER_001_UNIFIED_SOURCE_QUALITY_LEDGER_LOCAL_ONLY.md` | Review record confirming source quality rows, evidence paths, and no endpoint access. |
| `paper_accounting_reconciliation_gate` | Paper accounting validation remains local, paper-only, and operator-reviewed. | Supervised review needs a local reconciliation report tying paper-only ledger rows to observed local records. | `docs/PMBOT_PAPER_ACCOUNTING_002_PAPER_ONLY_ACCOUNTING_VALIDATOR_LOCAL_ONLY.md` | Review record confirming ledger row coverage, local references, and unresolved disputes. |
| `simulated_decision_audit_gate` | Simulated decision packet checks remain offline records with blocked market instruction fields. | Supervised review needs an audit packet confirming no ranking, numeric prediction metrics, or market instruction fields. | `pm_bot/tests/test_simulated_decision_packet_schema.py` | Review record confirming audit row coverage and blocked instruction fields. |
| `autonomy_status_gate` | Autonomy checklist rows remain `pending_operator_review`. | Supervised review needs separate human review records for any status change. | `docs/PMBOT_SAFETY_001_AUTONOMY_GATE_CHECKLIST_LOCAL_ONLY.md` | Review record naming each row, prior state, new state, reviewer, and timestamp. |
| `runtime_boundary_gate` | Forbidden action scan keeps runtime, dispatcher, scheduler, worker, browser, and background process boundaries closed. | Supervised review needs explicit process-boundary review with no wiring changes in this task. | `docs/PMBOT_SAFETY_003_FORBIDDEN_ACTION_SCAN_LOCAL_ONLY.md` | Review record confirming process boundary, stop conditions, and log destination for any later task. |
| `sensitive_access_boundary_gate` | Real wallet, credential, signing, transaction, order, and authenticated endpoint gates remain unresolved. | Supervised review needs a separate explicit approval record for any sensitive-access scope; this matrix grants none. | `pm_bot/readiness/PMBOT_ROADMAP_001_REAL_WALLET_READINESS_BLOCKER_MATRIX.md` | Review record naming exact files, modules, endpoints, duration, redaction rules, and stop conditions. |
| `validation_replay_gate` | Local compile and pytest commands are recorded as operator-run acceptance checks. | Supervised review needs current local validation output after the matrix and fixture are reviewed. | `tests/test_codex_queue_pmbot_templates.py` | Review record confirming `python -m compileall pm_bot tests` and `pytest pm_bot/tests tests/test_codex_queue_pmbot_templates.py` results. |

## Operator Review Boundary

Operators review whether the listed local references, gate states, and review evidence expectations match the handoff. This matrix does not approve a live run, choose a market, resolve an outcome, change review status, open external services, access credentials, access wallets, call endpoints, or change runtime, dispatcher, scheduler, worker, browser, or app-server wiring.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, action guidance, market ranking, numeric prediction metric, stance selection, or trade action guidance.
- This matrix is not execution approval and is not runtime input.
