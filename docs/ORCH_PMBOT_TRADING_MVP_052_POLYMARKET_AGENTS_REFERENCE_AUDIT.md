# ORCH-PMBOT-TRADING-MVP-052 Polymarket Agents Reference Audit

## Scope

This audit covers the public archived donor repository:

- Repository: https://github.com/Polymarket/agents
- Local donor commit inspected: `081f2b5594c37edeb9d3780a778c084d5b6f2743`
- License observed: MIT

The donor was used as a reference for field shapes, operator workflow ideas, and architecture patterns only. No donor live execution, wallet, signing, or order submission code was imported into PMBOT.

## Files Inspected

- `agents/polymarket/gamma.py`
- `agents/polymarket/polymarket.py`
- `agents/utils/objects.py`
- `agents/application/trade.py`
- `agents/application/executor.py`
- `agents/application/prompts.py`
- `agents/connectors/news.py`
- `agents/connectors/search.py`
- `agents/connectors/chroma.py`
- `scripts/python/cli.py`
- `requirements.txt`
- `.env.example`
- `LICENSE.md`

## safe_to_adapt_now

- `agents/polymarket/gamma.py`: Gamma public market/event metadata patterns, including public market/event shape, active/closed/order-book filters, event grouping, and market selection metadata.
- `agents/utils/objects.py`: Market/event normalization ideas, object boundaries, and explicit field mapping patterns. PMBOT adapted these as local dataclasses and dictionaries, not as copied donor models.
- `scripts/python/cli.py`: CLI/operator command structure ideas such as an explicit operator command entry point and concise terminal output.
- `agents/application/prompts.py`: High-level separation between context preparation and action review, adapted only as review-only paper drill structure.

Safe PMBOT adaptation in this task:

- deterministic BTC Polymarket-style fixture
- normalized market model
- read-only fixture snapshot contract
- simulated paper order intent
- readiness/risk/gate summaries
- operator UI and Telegram-visible passive status

## adapt_as_fixture_only

- `agents/polymarket/gamma.py`: Public Gamma metadata fetch shape can inform fixtures and future explicit unauthenticated read-only fetch tasks. This task remains fixture-only by default.
- `agents/connectors/news.py`: RAG/search/news architecture ideas are fixture or future review-only architecture references only. No NewsAPI key or live news call is used.
- `agents/connectors/search.py`: Search connector architecture is fixture or future offline-search reference only. No Tavily, OpenAI, or external search call is used.
- `agents/connectors/chroma.py`: Vector-store/RAG organization ideas can be used for future local evidence storage, but no live RAG backend is added here.
- `requirements.txt`: Dependency shape was reviewed only. No new production dependency was added.
- `.env.example`: Secret and environment names were reviewed only to identify boundaries and forbidden paths.

Fixture-only rules applied:

- network calls are off by default
- `--network-check` records a fixture-only status in this task
- no authenticated endpoint is called
- no API key is loaded
- no wallet is connected
- no signature or signed payload is generated

## reference_only_for_future_live_enablement

- `agents/polymarket/polymarket.py`: Future live connector design may refer to the separation between market lookup, CLOB access, balances, approvals, and order posting, but none of those paths are implemented or imported here.
- `agents/application/trade.py`: Future human-supervised trade workflow may refer to the concept of staging an action from analysis, but this task only creates a simulated paper order intent and blocks live execution.
- `agents/application/executor.py`: Future orchestration design may refer to executor separation, but no recursive live loop, retry loop, scheduler, or daemon is added.
- `.env.example`: Future live enablement would require a separate operator-approved secret boundary task before any credential loading could exist.

Any future live-enabling work must be a separate explicit operator-approved task with disabled-first adapters, refusal tests, audit logging, kill-switch coverage, redaction policy, and dual-control review.

## forbidden_in_this_task

The following donor concepts and names are forbidden in this PMBOT task:

- `POLYGON_WALLET_PRIVATE_KEY`
- CLOB API credential derivation
- Web3 wallet connection
- approvals
- `sign_transaction`
- `send_raw_transaction`
- `Signer`
- `OrderBuilder`
- `build_signed_order`
- `create_and_post_order`
- `create_market_order`
- `post_order`
- `execute_market_order`
- raw secret printing
- autonomous recursive retry trading loop
- background scheduler
- daemon
- browser automation
- authenticated Polymarket calls
- real order submission
- signed payload generation
- signed order generation

Forbidden boundaries verified for this task:

- no wallet/private-key read
- no signing
- no signed payload
- no signed order
- no order ID
- no transaction hash
- no fill
- no balance
- no PnL
- no authenticated endpoint
- no live connector
- no real trading action

## Attribution

PMBOT task 052 uses the public archived Polymarket agents repository as a reference/donor project under its MIT license. The implementation adapts concepts and field-shape ideas into new PMBOT code and does not vendor-drop the donor repository.
