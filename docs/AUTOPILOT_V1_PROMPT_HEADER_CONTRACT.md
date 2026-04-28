# AUTOPILOT V1 Prompt Header Contract

## Required Header Fields

Every routed Autopilot prompt should include these fields:

- `TARGET_AGENT`
- `TASK_OWNER`
- `TASK_TYPE`
- `CODE_CHANGES_ALLOWED_FOR_RECEIVER`
- `SESSIONS_SPAWN_ALLOWED`
- `RUNTIME_MUTATION_ALLOWED`
- `QUEUE_MUTATION_ALLOWED`
- `GOVERNANCE_MUTATION_ALLOWED`
- `APPROVAL_REQUIRED`
- `MISROUTE_BEHAVIOR`

## Why The Header Exists

The header gives the receiver a deterministic first-pass contract before any tool reasoning starts. This reduces the chance that a Flocky validation agent handles a Codex implementation prompt or that any receiver assumes permissions that were never granted.

## Codex Header Example

```text
TARGET_AGENT: Codex
TASK_OWNER: Codex
TASK_TYPE: code-changing
CODE_CHANGES_ALLOWED_FOR_RECEIVER: true
SESSIONS_SPAWN_ALLOWED: false
RUNTIME_MUTATION_ALLOWED: false
QUEUE_MUTATION_ALLOWED: false
GOVERNANCE_MUTATION_ALLOWED: false
APPROVAL_REQUIRED: true
MISROUTE_BEHAVIOR: IF_RECEIVED_BY_FLOCKY_RETURN_MISROUTED_CODEX_PROMPT_DETECTED_WITHOUT_TOOL_EXECUTION
```

## Flocky Header Example

```text
TARGET_AGENT: Flocky
TASK_OWNER: Flocky
TASK_TYPE: read-only validation
CODE_CHANGES_ALLOWED_FOR_RECEIVER: false
SESSIONS_SPAWN_ALLOWED: false
RUNTIME_MUTATION_ALLOWED: false
QUEUE_MUTATION_ALLOWED: false
GOVERNANCE_MUTATION_ALLOWED: false
APPROVAL_REQUIRED: true
MISROUTE_BEHAVIOR: RETURN_ROUTING_MISMATCH
```

## Misroute JSON Behavior

When a prompt is received by the wrong agent, the routing classifier returns a deterministic JSON decision instead of executing the prompt. For the accepted Flocky/Codex boundary, a Codex code-changing task received by Flocky must return `MISROUTED_CODEX_PROMPT_DETECTED`.

## Still Out Of Scope

- no runtime wiring
- no dispatcher or `run_codex` integration
- no active Flocky tool integration
- no queue mutation
- no final acceptance claims
