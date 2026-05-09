# PMBOT Roadmap 001 Real Wallet Readiness Blocker Matrix

Task: `PMBOT-ROADMAP-001-REAL-WALLET-READINESS-BLOCKER-MATRIX`

## Scope

This document is a local sensitive-access review artifact. It records unresolved operator approval gates that continue to block any real wallet, credential, authenticated endpoint, transaction, order, runtime, dispatcher, scheduler, worker, browser, or production service activity.

The matrix is descriptive only. It is not execution approval, runtime input, market analysis, forecast scoring, action guidance, or selection advice.

## Source Basis

Reviewed local PMBOT artifacts:

- `docs/PMBOT_DASHBOARD_001_LOCAL_OPERATOR_DASHBOARD_SUMMARY.md`
- `docs/PMBOT_PAPER_ACCOUNTING_001_PAPER_ONLY_ACCOUNTING_LEDGER_LOCAL_ONLY.md`
- `docs/PMBOT_SOURCE_LEDGER_001_UNIFIED_SOURCE_QUALITY_LEDGER_LOCAL_ONLY.md`
- `docs/PMBOT_PAPERLIVE_DECISION_001_SIMULATED_DECISION_PACKET_SCHEMA_NO_RECOMMENDATIONS.md`
- `docs/PMBOT_PAPERLIVE_010W_005_WEATHER_OPERATOR_REVIEW_SURFACE_UPDATE_NO_TRADE.md`
- `pm_bot/tests/fixtures/dashboard/local_operator_dashboard_request.valid.json`
- `tests/test_codex_queue_pmbot_templates.py`

These sources keep PMBOT review surfaces local-only, fixture/static, and `pending_operator_review`.

## Blocker Matrix

| Blocker ID | Approval Gate | Current Recorded State | Sensitive Boundary Held Closed | Local Evidence Reference | Review Evidence Still Required |
| --- | --- | --- | --- | --- | --- |
| `PMBOT-RW-BLOCKER-001` | Real wallet access approval | `unresolved_operator_approval` | No wallet files, wallet modules, signing material, seed material, private keys, or credential stores may be read or changed. | `docs/PMBOT_PAPER_ACCOUNTING_001_PAPER_ONLY_ACCOUNTING_LEDGER_LOCAL_ONLY.md` | Separate explicit operator approval record for wallet access scope, named files/modules, allowed read mode, and stop conditions. |
| `PMBOT-RW-BLOCKER-002` | Secret and credential handling approval | `unresolved_operator_approval` | No `.env`, `.env.*`, API key, browser profile, auth store, or credential store access. | `docs/PMBOT_PAPERLIVE_DECISION_001_SIMULATED_DECISION_PACKET_SCHEMA_NO_RECOMMENDATIONS.md` | Separate explicit operator approval record for credential source, redaction rule, access duration, and audit location. |
| `PMBOT-RW-BLOCKER-003` | Authenticated endpoint approval | `unresolved_operator_approval` | No authenticated service, exchange, broker, Polymarket, market API, balance, position, transaction, or account endpoint calls. | `docs/PMBOT_SOURCE_LEDGER_001_UNIFIED_SOURCE_QUALITY_LEDGER_LOCAL_ONLY.md` | Separate explicit operator approval record for endpoint class, request limit, expected local output, and no-secret-print confirmation. |
| `PMBOT-RW-BLOCKER-004` | Transaction and signing approval | `unresolved_operator_approval` | No transaction construction, signing, broadcast, payment, order submission, or irreversible operation. | `docs/PMBOT_PAPERLIVE_010W_005_WEATHER_OPERATOR_REVIEW_SURFACE_UPDATE_NO_TRADE.md` | Separate explicit operator approval record for signing boundary, manual confirmation process, and rollback/non-reversibility acknowledgement. |
| `PMBOT-RW-BLOCKER-005` | Runtime execution wiring approval | `unresolved_operator_approval` | No dispatcher, runtime, scheduler, worker, resident process, browser automation, or app-server wiring changes. | `tests/test_codex_queue_pmbot_templates.py` | Separate explicit operator approval record for runtime path, process lifetime, operator stop mechanism, and log destination. |
| `PMBOT-RW-BLOCKER-006` | Paper-only boundary change approval | `unresolved_operator_approval` | PMBOT remains offline, local, static-fixture, and paper-only unless a separate task explicitly changes that boundary. | `docs/PMBOT_DASHBOARD_001_LOCAL_OPERATOR_DASHBOARD_SUMMARY.md` | Separate explicit operator approval record identifying the exact boundary change and confirming review artifacts remain non-runtime records. |
| `PMBOT-RW-BLOCKER-007` | Operator review status closure | `unresolved_operator_approval` | Existing local review rows remain `pending_operator_review`; no row is accepted, bypassed, or treated as execution-ready by this matrix. | `pm_bot/tests/fixtures/dashboard/local_operator_dashboard_request.valid.json` | Separate explicit operator review record for each artifact whose status changes from `pending_operator_review`. |

## Static Review Checklist

- Confirm every referenced artifact remains local, fixture/static, and review-only.
- Confirm all sensitive boundaries above remain closed unless a separate explicit approval record exists.
- Confirm any future approval record is outside this matrix and names the exact task, scope, files, endpoints, duration, and audit output.
- Confirm this matrix is not used as runtime configuration, queue input, endpoint input, wallet input, transaction input, order input, or model prompt for market selection.

## Safety

- Local files and static fixtures only.
- No network calls.
- No LLM provider calls.
- No external market API calls.
- No authenticated endpoint use.
- No credential, wallet, private-key, seed, signing, order, trading endpoint, payment, or transaction path access.
- No runtime, dispatcher, scheduler, worker, browser, resident process, timed automation, or app-server wiring.
- No forecast scoring, market ranking, numeric prediction metric, stance selection, or trade action guidance.
- This document is not execution approval and is not runtime input.
