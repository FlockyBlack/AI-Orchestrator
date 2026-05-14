# ORCH PMBOT Safety 060Q: Static Safety Invariant Report

## Purpose

Task 060Q adds a static PMBOT safety invariant report command:

```powershell
python -m pm_bot.operator_runner.static_safety_invariant_report --scope pm_bot --dry-run
```

The command scans repository files under the selected worktree scope and, when requested, committed PMBOT trading-core artifacts. It is review-only and writes report artifacts; it does not enable live execution.

## Boundary

The scanner is local-only and repository-scoped:

- reads only files under the repository worktree scan scope
- does not read environment variables
- does not read user home directories outside the worktree
- skips sensitive-looking file names such as `.env`, wallet stores, private key files, seed phrase files, and key material suffixes
- does not inspect browser wallets
- does not access network
- does not print, hash, store, or transform credential values

Findings redact source line contents and report only pattern categories, paths, line numbers, and JSON paths.

## Runtime Scan

By default, the command scans runtime files under `pm_bot/` and excludes docs, tests, and artifact directories:

```powershell
python -m pm_bot.operator_runner.static_safety_invariant_report --scope pm_bot --dry-run
```

Docs and tests are excluded by default so prohibited examples and assertions do not fail the runtime scan.

## Artifact Scan

Use `--artifacts` to include committed generated artifacts under:

```text
pm_bot/trading_core/artifacts/
```

Example:

```powershell
python -m pm_bot.operator_runner.static_safety_invariant_report --scope pm_bot --dry-run --artifacts --json
```

The scanner excludes its own output directory from the current scan to avoid recursive self-reporting.

## Strict Mode

Use `--strict` to include docs/tests as scan inputs. Findings from docs/tests are reported with severity `allowed_reference`, not `critical`, because they are expected to contain prohibited examples and safety assertions.

In strict CLI mode, the command exits nonzero only when critical findings exist outside allowed-reference paths.

## Detected Pattern Groups

The report detects:

- private key, API secret, passphrase, mnemonic, and seed variable or field names
- live/order/signing/wallet flags set to active values
- signed payload or signer activation
- wallet activation
- order submission activation
- order cancellation activation
- balance, position, fill, transaction, order, and PnL runtime artifact fields
- scheduler, daemon, background worker, or autonomous runtime primitives

## Safe False Flags

These explicit false/zero safety flags are counted as safe references and never escalated:

- `live_execution_approved=false`
- `order_submission_enabled=false`
- `wallet_signing_enabled=false`
- `signing_enabled=false`
- `signed_payload_generation_enabled=false`
- `signed_order_generation_enabled=false`
- `authenticated_polymarket_enabled=false`
- `live_connector_enabled=false`
- `allowed_for_live=false`
- `resolved_blocker_count=0`

## Severities

The report uses:

- `critical`: unsafe activation or runtime execution/account artifact pattern outside allowed-reference paths
- `warning`: sensitive credential-name references or parse/read warnings that do not prove activation
- `allowed_reference`: docs/tests examples or assertions included by `--strict`

Warnings do not enable live trading and do not change runtime flags.

## Artifacts

Task 060Q writes:

- `pm_bot/trading_core/artifacts/static_safety_invariant_report_060q/static_safety_invariant_report_060q_result.json`
- `pm_bot/trading_core/artifacts/static_safety_invariant_report_060q/static_safety_invariant_report_060q_operator.md`
- `pm_bot/trading_core/artifacts/static_safety_invariant_report_060q/latest_static_safety_invariant_report_status_060q.json`
- `pm_bot/trading_core/artifacts/static_safety_invariant_report_060q/static_safety_invariant_findings_060q.json`
- `pm_bot/trading_core/artifacts/static_safety_invariant_report_060q/static_safety_invariant_allowlist_060q.json`

## Manual Results

Runtime-only scan:

```text
Critical findings: 0
Warnings: 7
Live execution: blocked
Order submission: blocked
Signing: blocked
Wallet: blocked
```

Runtime plus artifacts scan:

```text
critical_count: 0
warning_count: 58
safety_ok: true
live_execution: blocked
order_submission: blocked
signing: blocked
wallet: blocked
```

## Safety Invariants

Task 060Q preserves:

- `live_execution_approved=false`
- `order_submission_enabled=false`
- `wallet_signing_enabled=false`
- `signing_enabled=false`
- `signed_payload_generation_enabled=false`
- `signed_order_generation_enabled=false`
- `authenticated_polymarket_enabled=false`
- `live_connector_enabled=false`
- `allowed_for_live=false`
- `resolved_blocker_count=0`

No scheduler, daemon, background worker, autonomous trading loop, browser automation, wallet access, signing, order submission, order cancellation, balance read, position read, fill read, or PnL runtime path is added.
