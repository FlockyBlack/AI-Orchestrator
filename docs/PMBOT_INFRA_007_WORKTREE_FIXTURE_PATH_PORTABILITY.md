# PMBOT INFRA-007 Worktree Fixture Path Portability

Task: PMBOT-INFRA-007-FIX-WORKTREE-FIXTURE-PATH-PORTABILITY

Status: completed_ready_for_review

## Root Confirmation

- Canonical root confirmed: `C:\Users\OpenC\Documents\AI-Orchestrator`
- Starting branch: `main`
- Starting status: clean
- Starting HEAD: `5592c5b8be98e79c1f173551212638934cee33d8`
- `origin/main`: `5592c5b8be98e79c1f173551212638934cee33d8`

## Problem Summary

Prior isolated worktrees could not run the paper suite cleanly because some tests depended on ignored `local_snapshots` files that existed only in the canonical root, and several expected fixtures embedded canonical absolute paths. Clean worktree validation also exposed byte-level fixture hash instability from checkout line-ending conversion and an empty fixture `runs` directory that Git could not preserve.

## Portability Issues Found

- Untracked fixture dependency: threshold-hit tests and operator threshold review exercised `local_snapshots\polymarket_markets_active_500_001.json`.
- Canonical absolute path expectations: paper expected JSON/Markdown fixtures stored `C:\Users\OpenC\Documents\AI-Orchestrator` in source, workspace, inbox, manifest, and artifact path fields.
- Generated result path instability: tests compared raw machine-specific root paths instead of normalizing the active repo root.
- Fixture byte hash instability: SHA checks over fixture inputs changed in clean worktrees when Git converted fixture line endings.
- Empty fixture directory instability: `pm_bot\paper\manual_paper_workspace\runs` existed in the canonical root but was absent in fresh worktrees.

## Files Changed

- Added `.gitattributes` entries for hashed PMBOT paper fixture files.
- Added `pm_bot/paper/fixtures/polymarket_markets_active_threshold_hit.fixture.json`.
- Added `pm_bot/paper/manual_paper_workspace/runs/.gitkeep`.
- Added `pm_bot/paper/tests/_path_normalization.py`.
- Updated affected paper expected JSON/Markdown fixtures to use `<REPO_ROOT>`.
- Updated paper tests to normalize generated repo-root paths before expected comparisons.
- Updated threshold-hit tests to use the tracked synthetic fixture instead of ignored local snapshots.
- Added a narrow `--threshold-source` option to `pm_bot/paper/run_manual_paper_operator_cycle.py` so the existing offline threshold review can be tested against a tracked deterministic source while preserving existing defaults.

## Determinism

The new threshold-hit fixture is synthetic, tracked, static JSON. Expected fixtures now use the stable `<REPO_ROOT>` placeholder, and tests normalize the active checkout path before comparison. `.gitattributes` pins hashed fixture inputs to LF checkout bytes so SHA expectations are stable across clean worktrees with `core.autocrlf=true`. `.gitkeep` preserves the expected empty `runs` directory without introducing run artifacts.

## Safety

No live fetchers, network/API calls, credentials, wallet access, trading endpoints, real orders, autonomous paper orders, scoring/probability/EV/edge logic, market decisions, dispatcher changes, `run_codex` changes, Telegram/dashboard runtime changes, prompt automation, or Codex copy roots were added. The only paper-script change is an optional local source path override for an already-offline threshold review path.

## Canonical-Root Validation

- `python -m pytest pm_bot\paper\tests\test_run_crypto_threshold_hit_review_table.py pm_bot\paper\tests\test_run_crypto_threshold_hit_triage_report.py pm_bot\paper\tests\test_run_crypto_threshold_hit_policy_scenarios.py pm_bot\paper\tests\test_run_manual_paper_operator_cycle.py -q`: `69 passed`
- `python -m pytest pm_bot\paper\tests\test_run_local_snapshot_inbox_paper_portfolio.py pm_bot\paper\tests\test_run_local_snapshot_paper_portfolio_state.py pm_bot\paper\tests\test_run_manual_paper_inbox_bundle.py pm_bot\paper\tests\test_run_manual_paper_workspace.py pm_bot\paper\tests\test_run_manual_snapshot_workspace_import.py -q`: `65 passed`
- `python -m pytest pm_bot\paper\tests\test_run_local_snapshot_inbox_paper_portfolio.py pm_bot\paper\tests\test_run_manual_paper_inbox_bundle.py pm_bot\paper\tests\test_run_manual_paper_operator_cycle.py pm_bot\paper\tests\test_run_manual_paper_workspace.py pm_bot\paper\tests\test_run_manual_snapshot_workspace_import.py -q`: `75 passed`
- `python -m pytest pm_bot\paper\tests -q`: `310 passed, 39 subtests passed`
- `python -m pytest pm_bot\dashboard\tests pm_bot\operator\tests -q`: `33 passed, 14 subtests passed`
- Changed Python file `py_compile`: passed
- Changed/new JSON parse checks: passed
- `git diff --check`: passed

The full paper test run rewrote `docs/PMBOT_PAPER_017_RESULT.json` by changing `missing_optional_docs`; that generated churn was restored and is not part of this task.

## Isolated Worktree Validation

- Temporary path: `C:\Users\OpenC\Documents\AI-Orchestrator-worktrees\INFRA_007_PORTABILITY_VALIDATE`
- Temporary branch: `infra/infra007-portability-validate-temp`
- Safe method: clean worktree from `HEAD`, final portability changes committed on the temporary validation branch, worktree recreated from that temp commit so `.gitattributes` checkout rules were applied, then full paper suite run outside the canonical root.
- Command: `python -m pytest pm_bot\paper\tests -q`
- Result: `309 passed, 1 skipped, 39 subtests passed`
- Skip: existing optional real local `polymarket_markets_active_001.json` check in `test_run_real_market_triage_report.py`; not introduced by INFRA-007 and not a failure.
- Cleanup: temporary validation worktree removed and temporary branch deleted after restoring generated doc churn.

## Remaining Warnings

- Historical docs still mention the prior warning for traceability.
- Paper CLI defaults that point at canonical local snapshots were not changed to avoid changing existing default behavior. Tests that require portability now pass tracked fixtures explicitly.
