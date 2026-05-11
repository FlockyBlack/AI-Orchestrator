# Ultra Context

- Repo: `C:/Users/OpenC/.openclaw/workspace`
- Branch: `master`
- Purpose: supervised AI-Orchestrator automation for Codex/PMBOT plans.
- Latest completed milestone: `ORCH-CODEX-AUTOMATION-027-ACTUAL-APP-SERVER-SESSION-DRY-RUN`
- Current milestone: `ORCH-CODEX-AUTOMATION-028-AGENTS-MD-SUBAGENTS-MEMORY-BANK-AND-MAINTENANCE`

Current automation stack:

- operator panel + plan-runner
- queue/state resume + recovery
- Codex execution packet + result ingestion
- real Codex CLI invocation + auto-ingestion path
- Symphony-style workspace/session model + app-server schema boundary
- real short-lived app-server dry-run succeeded

PMBOT boundaries:

- paper-only
- no wallet/private keys/signing
- no real orders
- no trading endpoints
- no real-money actions
- no autonomous real trading
- no authenticated endpoints
- no browser automation
- no OpenRouter unless explicitly approved
- no Polymarket API unless explicitly approved
- no actionable real trading signal

Git rules:

- no `git add .`
- no `git add -A`
- no `git add --all`
- no force push
- selective staging only

Validation expectations:

- `python -m compileall ai_orchestrator`
- targeted pytest files for changed behavior
- result JSON with safety flags
- remote HEAD verification after push when push is performed
