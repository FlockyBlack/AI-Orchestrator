# ORCH-PMBOT-TRADING-MVP-055 Paper Decision Ledger And Operator Performance Reporting

## Scope

055 adds a durable, append-only, review-only paper decision ledger for accepted 052, 053, and 054 PMBOT paper flows.

The operator command is:

```text
python -m pm_bot.operator_runner.paper_decision_ledger --market BTC --strategy tiny-momentum --dry-run
```

Optional controls:

- `--artifacts-dir`
- `--source latest`
- `--source public_market_loop_054`
- `--source paper_loop_053`
- `--source paper_canary_052`
- `--json`
- `--reset-for-test`

The command reads existing local paper artifacts and appends a new operator review entry. It does not fetch market data, connect to wallets, authenticate, sign, submit, cancel, or simulate execution.

## Ledger Flow

```text
Evidence snapshot
-> normalized market snapshot
-> strategy signal or no_signal
-> risk decision
-> paper intent or no_intent
-> operator review record
-> summary report
-> latest UI/Telegram ledger summary
```

The ledger is not portfolio tracking. It does not create execution results, account state, or financial performance metrics.

## Supported Sources

`latest` reads the first complete latest paper source in this priority order:

1. 054 public market paper loop
2. 053 fixture paper trading loop
3. 052 paper canary drill

Specific source selection is available with `--source`.

054 entries include the public market evidence pack path when available. 053 entries use the fixture market snapshot as the normalized snapshot reference. 052 entries are represented as paper canary review records.

## Outcomes

Ledger entries record exactly one review outcome:

- `paper_intent_review_ready`
- `no_signal`
- `risk_blocked`
- `incomplete_artifacts`

`ledger_entry_id` is an internal review ledger identifier only. It is explicitly marked as not an order id, not a transaction id, and not an execution id.

## Generated Artifacts

Default artifact directory:

```text
pm_bot/trading_core/artifacts/paper_decision_ledger_055/
```

Required generated artifacts:

- `paper_decision_ledger_055.json`
- `paper_decision_ledger_055_operator.md`
- `latest_paper_decision_ledger_status_055.json`
- `paper_decision_summary_055.json`
- `paper_decision_trace_055.json`
- `paper_decision_incomplete_artifacts_055.json` only when source artifacts are missing

If a ledger file already exists, the command preserves existing entries and appends one new entry. It does not rewrite prior entries except as part of serializing the same prior entry values into the updated JSON file.

## Operator Report

The Markdown report includes:

- latest run source
- market
- strategy
- source type, such as `public_gamma_live_read_only` or `fixture_fallback`
- evidence pack path when available
- signal/no-signal summary through the outcome field
- risk decision
- paper intent path when present
- no-intent reason when absent
- ledger entry count
- count by outcome
- live execution blocked
- review-only next action

The report intentionally excludes win rate, profit, PnL, balances, returns, Sharpe ratio, execution quality, fills, and positions.

## Passive UI And Telegram

The passive Operator UI and Telegram summaries now surface latest ledger status when supplied in dashboard/context data.

They show:

- latest outcome
- ledger entry count
- count by outcome
- evidence pack path when available
- live execution blocked

They do not add execution buttons, wallet controls, signing controls, auth controls, order controls, or approve-live controls.

## Safety Invariants

All 055 outputs preserve:

- `execution_mode=paper`
- `review_only=true`
- `live_execution_approved=false`
- `canary_executable_now=false`
- `real_execution_available=false`
- `order_submission_enabled=false`
- `wallet_signing_enabled=false`
- `signing_enabled=false`
- `signed_payload_generation_enabled=false`
- `signed_order_generation_enabled=false`
- `authenticated_polymarket_enabled=false`
- `live_connector_enabled=false`
- `allowed_for_live=false`
- `resolved_blocker_count=0`

055 runtime behavior does not add private key reads, API secret reads, auth token reads, wallet connection, signing, authenticated Polymarket endpoints, order submission, order cancellation, balance reads, position reads, scheduler, daemon, background worker, autonomous loop, continuous polling, browser automation, or live execution.
