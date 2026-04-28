# Autopilot V1 Preflight Prompt Pack Templates

## Purpose

`codex_auto/autopilot/prompt_packs/` provides reusable prompt templates for future ChatGPT-generated or manually prepared Autopilot V1 tasks.

The goal is to standardize prompt headers and safe receiver behavior before any prompt is sent to Flocky, Codex, or ChatGPT.

## Why prompt packs exist

The accepted Autopilot V1 architecture now has a validated classifier and a validated routing preflight simulator. Prompt packs sit one layer earlier than both.

They help authors produce prompts that already declare:
- intended receiver
- task owner
- task type
- mutation and spawn limits
- approval expectation
- misroute behavior

That reduces ambiguity before a prompt ever reaches a receiver.

## How they prevent ORCH-006-style misroute

ORCH-006 showed that a Codex implementation prompt can arrive at Flocky and trigger the wrong behavior before a strong local stop.

These prompt packs reduce that risk in two ways:
- every template includes a full routing header that the existing classifier can interpret
- Codex templates explicitly encode Flocky misroute behavior so the routing preflight simulator can block them before tool execution

This does not eliminate the need for preflight. It makes preflight more deterministic because the prompt format is standardized.

## How to choose the right template

Use `flocky_read_only_validation.template.txt` for:
- read-only validation
- artifact review
- contract verification

Use `flocky_governance_design.template.txt` for:
- governance design
- policy critique
- approval-gate analysis

Use `codex_code_changing.template.txt` for:
- isolated implementation work
- bounded file creation or modification
- tasks that require local verification commands

Use `codex_focused_repair.template.txt` for:
- narrow bugfix work
- failing-test repair
- smallest-scope corrective changes

Use `chatgpt_planning.template.txt` for:
- planning
- decomposition
- option comparison
- specification drafting without execution

## How to send prompts to the right agent

Before sending a prompt:
- pick the template that matches the actual task type
- fill in the task ID, read paths, write paths, and validation commands
- keep the mutation flags aligned with the accepted architecture

Receiver rules remain:
- Flocky is validation-only and governance-only
- Codex is approved code execution only
- ChatGPT planning is planning only

If there is uncertainty, run the routing preflight simulator first.

## How to run optional preflight simulator

Example for a Codex template being checked as if it were misrouted to Flocky:

```bash
python codex_auto/autopilot/run_routing_preflight.py \
  --receiver Flocky \
  --prompt-path codex_auto/autopilot/prompt_packs/templates/codex_code_changing.template.txt \
  --out -
```

Example for a valid Flocky validation template:

```bash
python codex_auto/autopilot/run_routing_preflight.py \
  --receiver Flocky \
  --prompt-path codex_auto/autopilot/prompt_packs/templates/flocky_read_only_validation.template.txt \
  --out -
```

## What each template is for

`flocky_read_only_validation.template.txt`
- standard Flocky validation prompt
- no project writes
- final JSON only in chat/stdout

`flocky_governance_design.template.txt`
- standard Flocky governance-design prompt
- no project writes
- final JSON only in chat/stdout

`codex_code_changing.template.txt`
- standard Codex implementation prompt
- explicit approved write scope required
- explicit validation commands required

`codex_focused_repair.template.txt`
- standard Codex repair prompt
- tight repair scope
- no dispatcher, runtime, queue, or governance expansion

`chatgpt_planning.template.txt`
- planning-only prompt
- no code changes
- no execution
- structured planning output only

## What remains manual

Prompt packs do not automate sending, gating, or approval.

Manual work still remains:
- selecting the right template
- filling in the task-specific scope
- deciding whether to run preflight
- human approval where required
- Flocky read-only validation of implementation tasks

## What is not implemented

This layer does not implement:
- active Flocky tool integration
- runtime wiring
- dispatcher integration
- `run_codex` integration
- queue bridge behavior
- automatic prompt transport
- automatic approval
- final acceptance authority

## Boundary reminder

The accepted architecture is unchanged:
- AI-Orchestrator remains the only authoritative runtime and source of truth
- `codex_auto` remains preview, dry-run, adapter, guardrail, simulator, and template support only
- these prompt packs do not grant execution authority on their own
