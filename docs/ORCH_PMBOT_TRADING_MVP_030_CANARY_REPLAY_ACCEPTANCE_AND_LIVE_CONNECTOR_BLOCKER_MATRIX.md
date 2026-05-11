# ORCH-PMBOT Trading MVP 030 Canary Replay Acceptance And Live Connector Blocker Matrix

This task adds a deterministic PMBOT canary replay and dry-run acceptance layer without enabling any live execution path.

## What Was Built

- `pm_bot/trading_core/live_canary_replay_acceptance.py`
  - Replays live canary readiness packets and dry-run receipts.
  - Compares stored canary status and reason codes against replayed decisions.
  - Detects duplicate canary IDs and duplicate logical canary keys.
  - Detects missing references to source evidence, risk decision, wallet boundary packet, and signing simulator receipt.
  - Builds a deterministic 16-row dry-run acceptance matrix.
  - Builds a 10-row live connector blocker matrix.
  - Builds a future tiny live canary operator checklist.
  - Scans only named PMBOT canary/live-prep JSON artifacts for forbidden field names.
- `pm_bot/operator_runner/paper_daily_loop.py`
  - Surfaces canary replay status, acceptance matrix summary, live connector blocker count, critical blockers, next non-live task, and the dry-run-only assertion in the PMBOT paper daily dashboard.
- `docs/ORCH_PMBOT_TRADING_MVP_030_CANARY_REPLAY_ACCEPTANCE_AND_LIVE_CONNECTOR_BLOCKER_MATRIX_NIGHTLY_BATCH_PLAN.example.json`
  - Provides a fake-executor, plan-only nightly batch example for canary readiness dry-run, replay suite, and blocker matrix review.
- `pm_bot/tests/test_live_canary_replay_acceptance_030.py`
  - Covers replay determinism, missing references, duplicate canary IDs, reason-code drift, all acceptance cases, blocker matrix contents, checklist safety, dashboard smoke, nightly plan shape, forbidden field scanning, no external API calls, and no invented outcome/PnL.

## How To Run Locally

Run the existing dry-run readiness builder first if fresh artifacts are needed:

```powershell
python -m pm_bot.trading_core.live_canary_readiness
```

Then run replay, acceptance, blocker matrix, and checklist generation:

```powershell
python -m pm_bot.trading_core.live_canary_replay_acceptance `
  --packet pm_bot/trading_core/artifacts/night_020_021/live_canary_readiness_packet.json `
  --receipt pm_bot/trading_core/artifacts/night_020_021/live_canary_dry_run_acceptance_receipt.json
```

The command writes these dry-run-only artifacts under `pm_bot/trading_core/artifacts/night_020_021/`:

- `live_canary_replay_report.json`
- `live_canary_replay_report.md`
- `live_canary_acceptance_matrix.json`
- `live_canary_acceptance_matrix.md`
- `live_connector_blocker_matrix.json`
- `live_connector_blocker_matrix.md`
- `tiny_live_canary_operator_checklist.json`
- `tiny_live_canary_operator_checklist.md`

## Acceptance Matrix

The matrix is deterministic and includes these cases:

- all required artifacts present
- missing evidence
- stale evidence
- source gap present
- missing risk decision
- risk blocked
- kill switch enabled
- missing wallet boundary packet
- wallet boundary blocked
- missing signing simulator receipt
- signing simulator blocked
- missing operator dry-run approval
- rejected operator approval
- expired operator approval
- forbidden field present
- approved for dry-run only

Each row records expected canary status, actual replayed status, expected and actual reason codes, dry-run receipt acceptance status, whether a dry-run receipt can be accepted, and whether live execution remains forbidden.

## Live Connector Blocker Matrix

Current blocker count: 10.

Critical blockers before any future real live canary:

- real wallet connector absent
- secret handling policy absent or incomplete
- real signing adapter absent
- order adapter absent
- authenticated endpoint policy absent
- production kill switch not wired to real execution
- operator live approval flow absent
- post-trade audit absent
- real balance/exposure reconciliation absent
- emergency halt procedure absent

Every blocker is currently unresolved and blocks live execution. The next recommended non-live task is to draft local-only connector boundary and credential handling policy review artifacts without wiring wallet, signing, order, or authenticated endpoint code.

## Future Tiny Live Canary Readiness

Before any tiny operator-approved live canary can be considered in a separate future task:

- all canary dry-run artifacts must exist;
- replay status must pass;
- acceptance matrix status must pass;
- blocker matrix must remain explicit and reviewed;
- forbidden field scan must pass for relevant PMBOT canary/live-prep artifacts;
- dry-run-only operator approval must exist for the readiness packet;
- separate live approval flow, live connector design, signing boundary, endpoint policy, reconciliation, audit, kill switch wiring, and emergency halt procedure must be designed and reviewed.

Still forbidden now:

- real wallet access;
- private key, seed phrase, mnemonic, or credential material access;
- cryptographic signing;
- real order placement;
- authenticated endpoint calls;
- external API calls from this suite;
- autonomous live trading;
- real trading advice;
- invented market outcomes or PnL.

Real live execution is still unavailable.

## Validation Commands

```powershell
pytest pm_bot/tests
python -m compileall pm_bot
python -m pytest tests/test_codex_queue_nightly_lane_batch_runner.py tests/test_codex_worktree_lane_manager.py tests/test_subagent_routing.py tests/test_codex_queue_operator_cli.py
python -m compileall ai_orchestrator
git diff --check
```
