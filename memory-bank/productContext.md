# Product Context

## PMBOT User Workflow

Оператор ведет paper-only workflow: выбирает tracked markets, собирает evidence, отмечает unresolved ambiguity, проверяет симулированные решения и сохраняет outcome/source feedback только при наличии доказательств.

## Operator Panel

Панель показывает plans, runs, dashboard, artifacts, Codex handoff, Codex CLI readiness и app-server dry-run controls. В 028 она дополнительно подсвечивает наличие `AGENTS.md`, `memory-bank/`, subagent profiles и maintenance prompt.

## Plan Runner

Plan runner продолжает long supervised runs с queue state, checkpoints, recovery, artifact writing и acceptance gates.

## Codex Automation

Codex automation строится через execution packets, bounded prompts, result envelopes, auto-ingestion и short-lived supervised execution. Новая цель - multi-role workflow без потери контроля.

## Paper Trading Core

Paper trading core остается симуляционным. Любые real-money, wallet, signing, orders и live trading действия запрещены.
