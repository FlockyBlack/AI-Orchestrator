# PM Bot Master Plan V1

## A. Goal

Build a research-first Polymarket bot inside the existing AI-Orchestrator safety architecture.

The bot is intended to support structured market research, transparent signal scoring, hedge relationship discovery, paper simulation, reporting, and postmortem analysis. It is not an execution engine in the current stage.

## B. Core Principle

- Research and signal bot first.
- Paper-mode only.
- No real trading until separate explicit approval.

Every module must be able to operate with local fixtures or explicitly quarantined read-only data sources before any future execution discussion is allowed.

## C. Layers

- AI-Orchestrator: local runtime and safety-loop source of truth.
- OpenClaw/OpenFlow: governance, critic, and review layer.
- Codex: code executor for approved code-slice tasks only.
- Critic: validation gate for done-state approval.
- Obsidian: knowledge and summary layer.
- Future Polymarket bot modules: research, signal scoring, hedge discovery, paper simulation, dashboard, and postmortem.

The runtime authority remains inside AI-Orchestrator. Governance artifacts may summarize or review runtime outputs, but they must not replace runtime truth.

## D. Future Bot Modules

1. Market intake module
   - Loads fixture snapshots now and can later accept quarantined read-only fetch outputs.
2. Market normalization module
   - Converts raw snapshots into a deterministic internal shape.
3. Research and event context module
   - Associates markets with event metadata, timelines, and hypotheses.
4. Signal scoring module
   - Produces transparent research scores with reasons and safety labels.
5. Hedge and logical relationship discovery module
   - Detects mutually exclusive or correlated fixture markets.
6. Paper-position simulator
   - Simulates entries, exits, and exposure without execution authority.
7. Risk limits module
   - Applies paper-only position caps, scenario constraints, and stop rules.
8. Fees and slippage accounting
   - Models simulated costs for paper outcomes.
9. Dashboard and report module
   - Summarizes signals, simulated exposure, and research state.
10. Postmortem module
   - Records what worked, what failed, and what changed.
11. Governance adapter module
   - Packages bot outputs into critic-reviewable governance artifacts.

## E. Safety Gates

- No wallet or private key handling.
- No real order execution.
- No live trading.
- No auto-execution.
- No dependency on random third-party trading repos.
- Paper-only by default.
- All decisions logged.
- All final done states remain critic-gated.

Accepted conservative warnings remain visible when present:

- `network_risk:mixed`
- `api_risk:mixed`
- `wallet_risk:mixed`
- `private_key_risk:mixed`
- `execution_risk:mixed`
- `live_trading_risk:mixed`
- `dependency_risk:docs_only`

## F. Implementation Roadmap

Stage 1: governance dry-run artifacts

Stage 2: fixture-based Polymarket market model

Stage 3: local paper signal scoring

Stage 4: hedge relationship discovery from fixtures

Stage 5: paper portfolio simulation

Stage 6: dashboard and reporting

Stage 7: live data read-only fetcher behind quarantine

Stage 8: dry-run decision engine

Stage 9: only after explicit future approval, consider execution architecture

Stage 10: real trading remains forbidden until separately approved

## G. Non-Goals

- No live betting.
- No wallet integration.
- No private key handling.
- No copy-trading.
- No uncontrolled external skills.
- No random GitHub repo execution.
- No network fetcher in the current stage.

## H. Next Safe Tasks

1. `PMBOT-005`
   - Design a fixture batch loader for multiple local market snapshots.
2. `PMBOT-006`
   - Define a normalization schema revision plan for non-binary paper markets.
3. `PMBOT-007`
   - Design a research note format for event context capture.
4. `PMBOT-008`
   - Design paper-only confidence scoring rules and calibration notes.
5. `PMBOT-009`
   - Design fixture-based hedge clustering heuristics.
6. `PMBOT-010`
   - Design a paper portfolio simulator state model.
7. `PMBOT-011`
   - Design risk limits for paper exposure and scenario caps.
8. `PMBOT-012`
   - Design fee and slippage accounting inputs for paper simulation.
9. `PMBOT-013`
   - Design a local dashboard report layout and artifact contract.
10. `PMBOT-014`
   - Design a postmortem schema for paper-only runs.
11. `PMBOT-015`
   - Define the quarantine boundary for a future read-only market fetcher.
12. `PMBOT-016`
   - Perform read-only validation after each approved coding slice.

Each task above is limited to paper-only, fixture-only, design-only, or read-only validation work.
