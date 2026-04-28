# Autopilot V1 Prompt Pack Renderer

## Purpose

`codex_auto/autopilot/prompt_packs/render_prompt_pack.py` converts a structured render request JSON into a ready-to-send prompt using the existing prompt-pack templates.

It is a local helper only. It renders text, runs local routing preflight, and returns a deterministic JSON report.

## How the renderer reduces manual prompt assembly

Before this renderer, prompt authors had to:
- choose a template manually
- preserve all routing headers by hand
- fill allowed and forbidden path sections manually
- remember the right misroute behavior
- optionally run preflight as a separate step

The renderer keeps that process deterministic:
- the request supplies the structured task details
- the template and manifest supply the receiver contract
- the renderer produces a full prompt body and inline preflight report

## How it uses prompt packs

The renderer loads:
- `prompt_pack_manifest.v1.json` to resolve the template record
- the selected template from `codex_auto/autopilot/prompt_packs/templates/`
- the request JSON from `codex_auto/autopilot/prompt_packs/fixtures/` or another allowed local path

It uses the template header as the contract source and renders a task-specific body from the request fields:
- task ID
- task title
- context
- goal
- allowed read paths
- allowed write paths
- forbidden write paths
- forbidden behavior
- validation commands
- expected final JSON
- notes
- custom sections

## How it uses the routing preflight simulator

The renderer does not invent a separate routing system.

After rendering the prompt, it calls the existing local routing preflight simulator and embeds the resulting preflight report inline.

That means every render report already states whether the rendered prompt is:
- safe for the declared preflight receiver
- misrouted
- blocked
- governance-only
- validation-only

## Why it does not execute prompts

The renderer is render-only by design.

Its report explicitly enforces:
- `render_only=true`
- `original_prompt_executed=false`
- `rendered_prompt_executed=false`
- `sessions_spawn_allowed=false`
- `runtime_wiring_allowed=false`
- `queue_mutation_allowed=false`
- `active_flocky_tool_integration=false`
- `single_runtime_source_rule_preserved=true`

No sending, execution, shelling, or autonomous continuation is part of this step.

## Why this is not active Flocky integration

The renderer does not contact Flocky or invoke any Flocky tool surface.

It only produces:
- a rendered prompt string
- a local deterministic preflight report
- a render report envelope

There is no transport, no queue bridge, and no active receiver-side integration.

## Why this is not runtime wiring

The renderer does not modify:
- `scripts/dispatcher.py`
- `scripts/run_codex.py`
- runtime ledgers
- state, result, freeze, or checkpoint artifacts

It operates only inside `codex_auto/autopilot/prompt_packs/` and approved docs/tests output paths.

## Why this is not queue mutation

The renderer does not enqueue or move tasks.

It rejects output paths under queue and runtime surfaces and does not claim queue ownership or runtime source-of-truth authority.

## CLI usage

Render a Codex implementation prompt and print the render report:

```bash
python codex_auto/autopilot/prompt_packs/render_prompt_pack.py \
  --request-path codex_auto/autopilot/prompt_packs/fixtures/render_request_codex_code_changing.v1.json \
  --out -
```

Render a Flocky validation prompt and print the render report:

```bash
python codex_auto/autopilot/prompt_packs/render_prompt_pack.py \
  --request-path codex_auto/autopilot/prompt_packs/fixtures/render_request_flocky_validation.v1.json \
  --out -
```

Optional safe write:

```bash
python codex_auto/autopilot/prompt_packs/render_prompt_pack.py \
  --request-path codex_auto/autopilot/prompt_packs/fixtures/render_request_flocky_validation.v1.json \
  --out codex_auto/autopilot/prompt_packs/output/render_report.json
```

## Test commands

```bash
python -m pytest -q codex_auto/autopilot/tests/test_prompt_pack_renderer.py
python -m pytest -q codex_auto/autopilot/tests
python codex_auto/autopilot/prompt_packs/render_prompt_pack.py --request-path codex_auto/autopilot/prompt_packs/fixtures/render_request_codex_code_changing.v1.json --out -
python codex_auto/autopilot/prompt_packs/render_prompt_pack.py --request-path codex_auto/autopilot/prompt_packs/fixtures/render_request_flocky_validation.v1.json --out -
python -m pytest -q codex_auto
```

## What remains manual

The renderer does not:
- decide final approval
- send the prompt to any agent
- execute the rendered prompt
- apply runtime state
- bridge anything into queues or dispatcher

Manual and gated work still remains:
- choosing the right request content
- reviewing the preflight report
- obtaining human approval where needed
- later receiver-side validation in a separately gated step

## Next gated step after Flocky validation

After Flocky validates this renderer read-only, any future step that actually transports rendered prompts or binds them to runtime behavior would require a separate approval-controlled task. That work is outside ORCH-013.
