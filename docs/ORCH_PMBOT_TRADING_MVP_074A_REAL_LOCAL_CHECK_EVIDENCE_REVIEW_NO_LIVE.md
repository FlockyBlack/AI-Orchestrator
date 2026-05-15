# ORCH-PMBOT-TRADING-MVP-074A Real Local-Check Evidence Review

## Scope

074A adds a local-artifact-only review tool for diagnosing what still blocks the first supervised tiny order. It reads known PMBOT local JSON artifacts, including the 073A real-check snapshot when present, and emits a human-readable grouped diagnosis.

Command:

```bash
python -m pm_bot.operator_runner.real_local_check_evidence_review --market BTC --strategy tiny-momentum --dry-run
```

## Evidence Groups

The review output groups evidence into:

- L2 credentials/auth
- account/balance/allowance
- signer/private-key diagnostic
- token selection
- selected-token payload readiness
- approval
- final blockers

Each group records safe source references, source status, diagnosis text, unresolved blockers, and the local artifact paths used. Missing or unreadable inputs remain missing or unknown; 074A does not infer readiness from absent evidence.

## Behavior

- The tool reads local JSON artifacts only.
- It uses 073A snapshot status fields when the snapshot artifact exists.
- It falls back to commit-safe local status artifacts from 064, 065D, 067C, 069A, 070B, 070C, 071D, 072C, 072D, 073B, and 073C when present.
- It does not embed raw source payloads.
- It does not emit raw secrets, account values, signed payloads, order IDs, fills, balances, positions, PnL, or token IDs.
- It always keeps `allowed_for_live=false`, `review_executable_for_live=false`, and `resolved_blocker_count=0`.

## Artifacts

Default artifact directory:

```text
pm_bot/trading_core/artifacts/real_local_check_evidence_review_074a/
```

Files:

- `real_local_check_evidence_review_074a_result.json`
- `latest_real_local_check_evidence_review_status_074a.json`
- `real_local_check_evidence_review_groups_074a.json`
- `real_local_check_evidence_review_blockers_074a.json`
- `real_local_check_evidence_review_safety_snapshot_074a.json`
- `real_local_check_evidence_review_operator_diagnosis_074a.md`

## Current Default Run

On required base head `f9e7b4de6ea2afdc110ee5a2387e375f88e46f92`, 073A, 073B, and 073C artifacts are not present. The default 074A run therefore reports missing snapshot, token selection packet, and selected-token payload readiness evidence. Existing 072C and 072D artifacts are read and preserved as blocker evidence.

Default status:

- `status=blocked_first_supervised_tiny_order_not_ready`
- `remaining_blocker_count=18`
- `unknown_group_count=5`
- `blocking_group_count=7`

## Safety Statement

074A is a diagnosis-only local artifact reader. It does not run live checks, call network APIs, read environment secret values, read private material, instantiate signers, sign payloads, generate executable orders, submit orders, cancel orders, connect wallets, create browser automation, create schedulers, create daemons, or run background workers.
