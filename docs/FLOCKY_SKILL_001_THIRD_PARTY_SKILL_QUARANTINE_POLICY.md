# FLOCKY-SKILL-001 Third-Party Skill Quarantine Policy

## Scope

This policy defines how Flocky/OpenClaw treats third-party skills, plugins, tools, adapters, and helper code before any installation or activation.

For this policy, third-party includes:
- external OpenClaw skill
- npm package used as a skill
- downloaded script
- cloned repo
- browser automation extension
- Telegram or operator helper
- MCP/ACP/adapter-style tool
- any code that can read or write files, execute shell commands, access network, or touch credentials

## Non-Goals

This policy is not:
- an installer
- a skill registry
- a runtime permission system
- approval to execute code
- a replacement for operator approval
- a second source of truth

## Default Stance

Default stance: **QUARANTINED_BY_DEFAULT**

Until explicitly reviewed and approved:
- no install
- no enablement
- no runtime wiring
- no credentials
- no network access
- no shell access
- no write access

No exceptions should be inferred from convenience, popularity, or claimed usefulness.

## Risk Classes

### LOW_RISK_REFERENCE_ONLY
Reference material only.
Examples:
- static docs
- read-only examples
- non-executable schemas

### MEDIUM_RISK_LOCAL_TOOL
Locally usable helper with bounded behavior, but still requiring review.
Examples:
- local formatter
- local parser
- offline utility without credential or network access

### HIGH_RISK_EXECUTION_CAPABLE
Anything that can execute commands, mutate files, access network, load dependencies, or affect runtime behavior.
Examples:
- installable plugin
- adapter with shell access
- automation helper with write capability
- browser extension with active control

### BLOCKED_UNSAFE
Candidate is unsafe by design, too opaque to trust, or requests prohibited capability.
Examples:
- wallet/private key access
- hidden network behavior
- broad write access without need
- runtime mutation without explicit approval path

## Required Review Checklist

Before any approval decision, capture:
- source URL or local path known
- maintainer known or unknown
- license noted if available
- install method known
- permissions requested
- file write behavior
- shell execution behavior
- network behavior
- credential or token access
- telemetry or exfiltration risk
- dependency tree risk
- update mechanism
- rollback or removal path
- sandbox plan
- operator approval status

Unknown answers increase risk class.

## Approval Statuses

Use exactly:
- `QUARANTINED`
- `APPROVED_FOR_REVIEW_ONLY`
- `APPROVED_FOR_LOCAL_SANDBOX_TEST`
- `APPROVED_FOR_LIMITED_USE`
- `REJECTED`
- `BLOCKED`

## Hard Blockers

Approval must be `BLOCKED` if any of these apply:
- asks for wallet, private key, or seed phrase
- can place real orders or trades
- can access payment credentials
- hidden network behavior
- unclear source or opaque binary
- broad filesystem write access without need
- modifies `dispatcher.py`, `run_codex.py`, or runtime behavior
- enables background execution
- enables Telegram or operator bot without approval
- creates second source of truth
- attempts to auto-update without approval
- requires admin privileges without a specific reason

## Quarantine Workflow

Manual workflow:
1. identify the candidate
2. capture source and claimed purpose
3. classify risk
4. inspect requested permissions and implied capabilities
5. decide approval status
6. if sandbox test is approved, create a separate future task
7. never install in the policy task itself

The quarantine step ends only with a documented status, not with execution.

## Sandbox Requirements

For any future approved sandbox:
- isolated folder
- no secrets
- no wallet or API keys
- no production config write
- no AI-Orchestrator runtime mutation
- no PMBOT live behavior
- no Telegram enablement
- explicit rollback or removal notes

Sandbox approval is not production approval.

## Review Record Template

Reference-only template:

```json
{
  "review_id": "manual-review-id",
  "skill_name": "candidate-name",
  "source": "url-or-path",
  "claimed_purpose": "short plain-language purpose",
  "risk_class": "LOW_RISK_REFERENCE_ONLY | MEDIUM_RISK_LOCAL_TOOL | HIGH_RISK_EXECUTION_CAPABLE | BLOCKED_UNSAFE",
  "requested_permissions": [],
  "network_access": "none | limited | broad | unknown",
  "filesystem_access": "none | read_only | bounded_write | broad_write | unknown",
  "shell_access": "none | bounded | broad | unknown",
  "credential_access": "none | limited | broad | unknown",
  "approval_status": "QUARANTINED | APPROVED_FOR_REVIEW_ONLY | APPROVED_FOR_LOCAL_SANDBOX_TEST | APPROVED_FOR_LIMITED_USE | REJECTED | BLOCKED",
  "reason": "short review reason",
  "required_conditions": [],
  "forbidden_actions": [],
  "reviewed_at_manual": "YYYY-MM-DD HH:MM local"
}
```

## PMBOT-Specific Overlay

For PMBOT-related use:
- no live API
- no wallet or private key
- no real order
- no trading execution
- no payment credentials
- no `dispatcher.py`, `run_codex.py`, or runtime modification
- any violation is `BLOCKED`

## Source-of-Truth Boundary

AI-Orchestrator remains the only source of truth and runtime workspace.

This policy is a review boundary only.
It must not:
- approve execution by implication
- replace canonical task artifacts
- mutate runtime state
- turn Flocky/OpenClaw into an executor

## Recommended Use

Use this policy before any third-party skill, plugin, tool, adapter, helper, or downloaded code is installed, enabled, or trusted.

Suggested flow:
1. quarantine first
2. document source and claims
3. classify risk
4. review permissions and blockers
5. assign one approval status only
6. if needed, open a separate sandbox-review task
7. keep this policy and its review records reference-only
