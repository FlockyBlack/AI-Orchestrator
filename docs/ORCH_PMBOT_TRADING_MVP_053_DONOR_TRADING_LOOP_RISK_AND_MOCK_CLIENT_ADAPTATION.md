# ORCH-PMBOT-TRADING-MVP-053 Donor Trading Loop Risk And Mock Client Adaptation

## Scope

This audit covers donor architecture ideas from public Polymarket bot repositories reviewed for PMBOT task 053:

- Polymarket agents: https://github.com/Polymarket/agents/tree/main/agents
- jaredzwick polymarket-trading-bot: https://github.com/jaredzwick/polymarket-trading-bot
- MrFadiAi Polymarket-bot: https://github.com/MrFadiAi/Polymarket-bot
- Panca2341 polymarket-trading-bot: https://github.com/Panca2341/polymarket-trading-bot
- aulekator Polymarket-BTC-15-Minute-Trading-Bot: https://github.com/aulekator/Polymarket-BTC-15-Minute-Trading-Bot

053 adapts architecture only. It does not vendor, import, copy, wrap, or enable donor live execution code. PMBOT remains one-shot, operator-triggered, fixture-driven, paper-only, and review-only.

## safe_to_adapt_now

- Polymarket agents:
  - Public Gamma metadata shape ideas for market/event normalization.
  - Typed model and explicit field mapping style.
  - CLI/operator documentation style.
- jaredzwick polymarket-trading-bot:
  - High-level pipeline: market data -> strategy -> risk check -> paper intent artifact.
  - Mock client pattern, adapted as PMBOT read-only fixture client.
  - Strategy interface concept: `BasePaperStrategy.evaluate(snapshot) -> signal | None`.
  - Risk-first intent construction, adapted without live client calls.
  - Halt/review status vocabulary for blocked risk results.
- MrFadiAi Polymarket-bot:
  - Operator dashboard/status section vocabulary.
  - Strategy toggle/status concept, adapted as a named deterministic strategy.
  - Passive emergency-stop vocabulary, adapted only as blocked/review-only status wording.
  - Dynamic sizing concept, adapted only as an explanatory paper field with fixed bounds.
- Panca2341 polymarket-trading-bot:
  - BTC/ETH/SOL/XRP short-window market fixture idea, narrowed here to BTC fixture category.
  - Event slug/window normalization concept.
  - `clobTokenIds` and `outcomePrices` parsing concept for offline fixtures only.
  - Orderbook snapshot shape ideas for local fixture models only.
- aulekator Polymarket-BTC-15-Minute-Trading-Bot:
  - Pipeline labels: ingestion, validation, signal processor, risk gate, artifact/status output, monitoring.
  - BTC 15-minute specialization as a fixture category idea.
  - Risk-first gate concept.
  - Paper intent viewer concept, renamed and constrained as non-execution paper intent review.

Safe PMBOT adaptation in this task:

- `MarketSnapshot`
- `StrategySignal`
- `PaperExecutionRisk`
- `PaperOrderIntent`
- `PaperLoopArtifact`
- `LatestPaperTradingStatus`
- fixture/mock read-only market client
- deterministic tiny-momentum paper strategy
- one-shot risk-first paper intent builder
- JSON/Markdown artifacts
- passive latest status for operator UI and Telegram

## adapt_as_fixture_only

- Polymarket agents:
  - Gamma public market/event field names inform local normalized fixture shapes only.
  - Market/event filters inform paper tradeability checks only.
- jaredzwick polymarket-trading-bot:
  - Event bus and order manager concepts are collapsed into a one-shot local function call.
  - Mock client pattern is fixture-only; PMBOT does not expose any live client methods.
  - Risk manager concepts are used only for dry-run, paper-mode validation gates.
- MrFadiAi Polymarket-bot:
  - Dashboard sections are adapted as passive latest-status fields only.
  - Strategy enablement language is adapted as strategy name/status only, with no live mode switch.
- Panca2341 polymarket-trading-bot:
  - Token and outcome price parsing shapes are used only for local JSON fixtures.
  - Orderbook and last-trade message shapes are allowed only as offline fixture model ideas.
- aulekator Polymarket-BTC-15-Minute-Trading-Bot:
  - Monitoring/status layout is adapted as JSON/Markdown artifact output only.
  - Signal fusion remains a future paper-only design idea; 053 uses a single deterministic strategy.

Fixture-only constraints applied:

- no network market polling
- no authenticated endpoint
- no API credential handling
- no wallet
- no signing
- no order submission
- no fake execution result
- no continuous loop

## reference_only_for_future_live_enablement

The following donor concepts are reference-only and must require a separate future operator-approved task before any implementation:

- Polymarket agents:
  - CLOB access, wallet connection, signer usage, approvals, order building, and trade execution flow.
- jaredzwick polymarket-trading-bot:
  - Real client, order execution service, open intent tracking, position lookups, and graceful shutdown behavior that cancels open orders.
- MrFadiAi Polymarket-bot:
  - Wallet service, trading service, onchain service, smart money following, arbitrage execution, and live dashboard mode switching.
- Panca2341 polymarket-trading-bot:
  - CLOB authentication, relayer authentication, HMAC/key derivation, safe address handling, gasless order flow, deployment, approvals, and order/cancel operations.
- aulekator Polymarket-BTC-15-Minute-Trading-Bot:
  - Redis control plane, live mode, py-clob-client execution, signed/post orders, learning loop, auto-recovery, performance claims, and live monitoring stack.

Any future live-enabling task must be separately approved and must add disabled-first adapters, redaction, dual-control review, kill-switch verification, audit replay, and refusal tests before live capability exists.

## forbidden_in_this_task

The following are forbidden in 053 runtime code and behavior:

- `PRIVATE_KEY`
- `API_SECRET`
- `PASSPHRASE`
- `POLYMARKET_PK`
- `POLYMARKET_PRIVATE_KEY`
- `POLYGON_WALLET_PRIVATE_KEY`
- `Wallet(`
- `Signer`
- `OrderBuilder`
- `createAndPostOrder`
- `placeOrder`
- `postOrder`
- `cancelOrder`
- `sign_order`
- `signed_payload`
- `tx_hash`
- `fill_id`
- `filled_size`
- `fill_price`
- `balance`
- `pnl`
- wallet connection
- private-key or raw credential reads
- API secret reads
- authenticated Polymarket calls
- signing
- signed payload or signed order generation
- real order submission
- cancels
- fake order identifiers
- fake transaction hashes
- fake fills
- fake balances
- fake PnL
- autonomous trading
- scheduler
- daemon
- background worker
- browser automation
- continuous polling
- retry loop around live endpoints

Forbidden boundaries verified by design:

- 053 adds no production dependency.
- 053 adds no donor source import.
- 053 adds no live client method to the fixture client.
- 053 writes only local JSON/Markdown artifacts.
- 053 reports live execution as blocked.
- 053 keeps all live/auth/signing/order/wallet flags false.

## 053 Adaptation Statement

PMBOT 053 adapts reusable architecture ideas only:

```text
MarketSnapshot
-> StrategySignal or no-signal
-> PaperExecutionRisk
-> PaperOrderIntent only when paper risk passes
-> PaperLoopArtifact
-> LatestStatus
-> Operator UI / Telegram passive summaries
```

The implementation is one-shot and operator-triggered only. It does not submit, sign, simulate, or fake-execute anything.
