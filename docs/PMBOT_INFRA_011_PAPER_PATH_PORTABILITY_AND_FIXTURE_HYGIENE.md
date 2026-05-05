# PMBOT-INFRA-011 Paper Path Portability and Fixture Hygiene

Task: `PMBOT-INFRA-011-PAPER-PATH-PORTABILITY-AND-FIXTURE-HYGIENE`

Status: completed locally.

## Summary

- Paper runners now derive default local snapshot paths from the repository root instead of `C:\Users\OpenC\Documents\AI-Orchestrator`.
- Paper workspace tests copy fixture workspaces without copying the read-only `runs` directory, avoiding Windows temp cleanup `PermissionError` failures.
- Expected paper/operator fixture counterparts were materialized as deterministic local artifacts.
- `local_snapshot_series_risk_scenarios.v1.json` is now the deterministic output artifact; the source fixture moved to `local_snapshot_series_risk_scenarios_source.v1.json`.
- Artifact health and warning hygiene reports were regenerated from local files only.

## Warning Hygiene Result

- Total warnings: 59
- Blocking warnings: 0
- Action required: 21
- Review needed: 37
- Informational: 1
- `update_fixture` warnings remaining: 0

## Safety

No network/API calls, live fetching, wallets, credentials, real orders, live trading, autonomous decisions, runtime wiring, command execution, scoring, probability, EV, edge, side recommendations, market decisions, or truth inference were added.
