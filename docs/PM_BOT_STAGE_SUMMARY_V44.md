# PM Bot Stage Summary V44

Task: PMBOT-BRAIN-032-REAL-GAMMA-CRYPTO-NUMERIC-ADAPTER

Status: passed

Summary:
- Added strict offline adapter support for real Gamma-shaped Yes/No crypto numeric markets only when the asset is unambiguous BTC, Bitcoin, ETH, or Ethereum.
- The adapter now rejects ambiguous supported assets, missing numeric targets, ambiguous above/below sides, and unsupported outcome shapes before returning crypto numeric raw records.
- The crypto numeric intake now honors validated adapter asset, side, and target candidates so adapted Gamma-style rows normalize into the existing scorer input shape deterministically.
- The real-market triage report now separates supported candidates from still-rejected candidates and reports real Gamma adapted/actionable counts after the adapter update.
- The minimized Gamma fixture covers one Bitcoin-above supported market, one Ethereum-below supported market, one non-crypto numeric rejection, one crypto missing-target rejection, and one crypto ambiguous-side rejection.

Real Snapshot Adapter Summary:
- Real local snapshot checked: `C:\Users\OpenC\Documents\AI-Orchestrator\local_snapshots\polymarket_markets_active_001.json`
- Markets seen: 100
- Previous crypto numeric actionable: 0
- New crypto numeric adapted: 0
- New crypto numeric actionable: 0
- Adapter rejection reasons: ambiguous_side=1, unsupported_asset=99
- Supported candidate examples: none
- Still rejected example: `Will bitcoin hit $1m before GTA VI?` was rejected as `ambiguous_side` because it has a numeric target but no explicit above/below side phrase.
- Still rejected examples: `MegaETH market cap (FDV) >$2B one day after launch?` and `MegaETH market cap (FDV) >$6B one day after launch?` were rejected as `unsupported_asset` because MegaETH is not treated as unambiguous ETH/Ethereum.

Safety:
- Offline only: true
- Paper only: true
- Live fetcher implemented: false
- API used: false
- Network used: false
- Wallet used: false
- Real order created: false
- Trading allowed: false
- Runtime wiring changed: false
- Dispatcher touched: false
- Prompt automation added: false

Checks:
- python -m pytest pm_bot\paper\tests\test_run_real_market_triage_report.py pm_bot\paper\tests\test_run_manual_snapshot_workspace_import.py pm_bot\scoring\tests\test_adapt_live_shaped_crypto_snapshot.py -q
- python -m pytest pm_bot\scoring\tests pm_bot\paper\tests -q
- python pm_bot\paper\run_real_market_triage_report.py
- python pm_bot\paper\run_real_market_triage_report.py --markdown
- python pm_bot\paper\run_real_market_triage_report.py --source C:\Users\OpenC\Documents\AI-Orchestrator\local_snapshots\polymarket_markets_active_001.json --markdown
- python pm_bot\paper\run_manual_snapshot_workspace_import.py --source C:\Users\OpenC\Documents\AI-Orchestrator\local_snapshots\polymarket_markets_active_001.json --markdown
- python pm_bot\paper\run_manual_paper_operator_cycle.py
- python pm_bot\paper\run_crypto_numeric_lifecycle_regression_gates.py
