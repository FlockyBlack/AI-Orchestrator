# ORCH-SYMPHONY-000 Reference Spike Result

Task: `ORCH-SYMPHONY-000-REFERENCE-SPIKE-NO-INTEGRATION`

Official repository inspected: https://github.com/openai/symphony

Commit inspected: `58cf97da06d556c019ccea20c67f4f77da124bf3`

External clone location: `C:\Users\OpenC\.openclaw\external_research\openai_symphony`

## Executive Summary

OpenAI Symphony is real and directly relevant, but it is only a partial fit for the AI-Orchestrator / PMBOT local workflow as-is.

The repository contains a language-agnostic `SPEC.md` plus an experimental Elixir/OTP reference implementation. The reference implementation is a long-running orchestration service that polls Linear, creates per-issue workspaces, launches Codex in app-server mode, sends issue-specific prompts, observes session state, retries stalled work, and exposes logs plus an optional dashboard/API.

It can reduce manual Ctrl-C/Ctrl-V prompting because it turns issue records into Codex app-server sessions automatically. It does not require ChatGPT desktop. It does require a Codex CLI/app-server-capable environment for real Codex runs.

The main mismatch is the work source. Official Symphony is Linear-first. It does not ship a GitHub Issues adapter or a durable file-based task queue. The Elixir implementation includes an in-memory tracker adapter for tests/local development, but that is not a file queue and is not enough to make AI-Orchestrator the source of truth without adaptation.

Recommended next task: `ORCH-SYMPHONY-001-ADAPT-SPEC-LOCAL-QUEUE`.

## What Symphony Actually Is

Symphony is a scheduler/runner for coding agents, not a planner and not a general task manager.

Its core shape:

- Read eligible work from an issue tracker.
- Normalize each issue into a stable issue model.
- Create or reuse one isolated workspace per issue.
- Render a prompt from repository-owned `WORKFLOW.md`.
- Start Codex through `codex app-server` in the issue workspace.
- Stream Codex app-server events back into orchestrator state.
- Retry failed, timed-out, or stalled work with backoff.
- Stop sessions when tracker state changes make the issue ineligible.
- Provide proof-of-work surfaces through logs, session state, token/rate-limit telemetry, and optional dashboard/API.

The official repo frames Symphony as a spec first. The Elixir implementation is explicitly described as prototype/evaluation software.

## What Problem It Solves

Symphony solves the manual supervision bottleneck for coding-agent work:

- No need to manually copy issue context into many Codex chats.
- No need to manually create one local workspace per task.
- No need to babysit every turn if the workflow and safety posture are trusted.
- Work state lives in the issue tracker and `WORKFLOW.md`.
- Operators can manage issues and review outputs instead of steering every Codex prompt.

For AI-Orchestrator, the strongest reusable pieces are:

- `WORKFLOW.md` as a versioned prompt/config contract.
- Per-task workspace isolation.
- Codex app-server invocation model.
- Stuck-session timeout and retry concepts.
- Proof-of-work expectations.
- Human handoff state semantics.

## How Close It Is To The Video Workflow

It is very close to the video workflow described in the OpenAI README:

- It monitors a Linear board.
- It spawns separate Codex-backed workers.
- Agents work in isolated per-issue workspaces.
- The workflow prompt tells agents how to move through states such as `Todo`, `In Progress`, `Human Review`, `Merging`, and `Done`.
- Proof-of-work is expected before human review.
- Human review is represented as an issue state, not as a manual chat loop.

The gap is that the video workflow is Linear-centered and assumes trusted automation. PMBOT's desired workflow is local/offline/analysis-only with AI-Orchestrator as source of truth.

## Can It Reduce Manual Ctrl-C/Ctrl-V?

Yes, conceptually.

Symphony renders prompts automatically from issue records and `WORKFLOW.md`, then sends those prompts to Codex app-server. That removes the manual task of opening many Codex chats and pasting task prompts.

For the current AI-Orchestrator target, this benefit is not available out of the box because the work queue is not Linear. A local queue adapter is needed before approved AI-Orchestrator tasks can become isolated Codex runs.

## Can It Open Or Manage Separate Codex Runs Or Workspaces?

Yes.

The Elixir implementation creates deterministic per-issue workspaces under `workspace.root`, sanitizes issue identifiers for directory names, validates workspace root containment, and starts Codex with the per-issue workspace as cwd.

Codex is invoked as:

```text
bash -lc <codex.command>
```

The default `codex.command` is:

```text
codex app-server
```

The app-server client initializes a Codex thread, starts turns, extracts `thread_id` and `turn_id`, emits a combined `session_id`, and reuses the same thread for continuation turns during one worker run.

It does not use ChatGPT desktop.

## Install And Runtime Requirements

Official repo structure inspected:

- `README.md`
- `SPEC.md`
- `elixir/README.md`
- `elixir/WORKFLOW.md`
- `elixir/mise.toml`
- `elixir/mix.exs`
- `elixir/lib/symphony_elixir/*`
- `elixir/docs/*`

Runtime:

- Spec: language-agnostic.
- Reference implementation: Elixir/OTP.
- `elixir/mix.exs`: `elixir: "~> 1.19"`.
- `elixir/mise.toml`: `erlang = "28"`, `elixir = "1.19.5-otp-28"`.
- Build tool: Mix, with optional `mise` recommended by docs.
- Web dashboard: Phoenix/LiveView/Bandit dependencies.
- Codex integration: Codex CLI with `app-server` support.
- Shell assumption: local app-server launch uses `bash -lc`.

Primary package/dependency commands in docs:

- `mise install`
- `mise exec -- mix setup`
- `mise exec -- mix build`
- `mise exec -- ./bin/symphony ./WORKFLOW.md`

No install or build command was run in this spike.

## Work Source Compatibility

Linear:

- Supported and primary.
- `tracker.kind: linear`.
- Uses Linear GraphQL endpoint, default `https://api.linear.app/graphql`.
- Requires `LINEAR_API_KEY` or configured `tracker.api_key`.
- Requires `tracker.project_slug`.

GitHub Issues:

- Not supported out of the box in the official reference implementation.
- The spec allows non-Linear implementations if they produce the same normalized issue model.
- A GitHub Issues adapter would be a new adaptation task.

File-based queue:

- Not supported out of the box.
- The reference implementation includes `tracker.kind: memory`, but it is in-memory and configured via application environment, not a durable queue file.
- A local JSON/Markdown/task-file queue can be adapted from the tracker adapter boundary but is not already present.

## Task Representation

The normalized issue model includes:

- `id`
- `identifier`
- `title`
- `description`
- `priority`
- `state`
- `branch_name`
- `url`
- `labels`
- `blocked_by`
- timestamps

This maps well to AI-Orchestrator task files, but a local adapter must translate AI-Orchestrator task JSON/Markdown into the normalized issue model.

## Prompt Configuration And WORKFLOW.md

`WORKFLOW.md` is the central repo-owned contract.

It contains optional YAML front matter plus a Markdown prompt body. The front matter controls:

- tracker configuration
- polling interval
- workspace root
- workspace lifecycle hooks
- agent concurrency and turn limits
- Codex command, approval policy, sandbox policy, and timeouts
- optional server/dashboard settings

The Markdown body is a strict template rendered with:

- `issue`
- `attempt`

The Elixir implementation uses strict template variables and filters. Unknown variables fail rendering instead of silently producing weak prompts.

`WORKFLOW.md` is watched and reloaded. Invalid reloads keep the last known good workflow and log the error.

## Stuck Sessions And Retry Behavior

Stuck handling exists.

Relevant controls:

- `codex.read_timeout_ms`
- `codex.turn_timeout_ms`
- `codex.stall_timeout_ms`
- `agent.max_retry_backoff_ms`
- `agent.max_turns`

The orchestrator tracks last Codex activity. If a running session has no activity beyond `codex.stall_timeout_ms`, it terminates that worker and schedules a retry with backoff.

Normal worker exit while an issue remains active schedules a continuation retry. Abnormal exits schedule failure retries.

Scheduler state is intentionally in-memory. Restart recovery is tracker/filesystem-driven, not durable job recovery.

## Proof Of Work And Human Review

Symphony itself reports proof-of-work through:

- structured logs with `issue_id`, `issue_identifier`, and `session_id`
- Codex app-server event state
- token totals
- rate-limit telemetry when available
- running/retry snapshots
- optional dashboard/API

The sample workflow prompt expects agents to maintain a Linear workpad comment, run validation, attach PRs, resolve review comments, and move issues to `Human Review`.

Human review is a tracker state. In the sample workflow:

- `Human Review` means PR is attached and validated, waiting on human approval.
- The agent should not code while in `Human Review`.
- A human moves approved work to `Merging`.
- The agent then follows a `land` skill flow.

For AI-Orchestrator, this should become a local task status and proof bundle, not automatic PR landing.

## Credentials And Network

Credentials needed for real official workflow:

- `LINEAR_API_KEY` or `tracker.api_key` for Linear.
- Authenticated Codex CLI/app-server environment for real Codex runs.
- GitHub/Git credentials if hooks or workflow prompts clone private repos, push branches, or create PRs.
- SSH credentials only when remote workers are configured.

Credentials can be avoided for a constrained local dry-run only if:

- `tracker.kind: memory` or a future local queue adapter is used,
- no real issues are dispatched, or a fake/no-op Codex app-server command is used,
- hooks do not access private remotes or secrets.

Network usage:

- Real Linear mode requires network to Linear.
- Real Codex app-server runs require whatever network/auth Codex needs.
- The default Codex turn sandbox policy sets `networkAccess: false`, but that is Codex turn sandboxing, not a guarantee that the whole orchestration process is offline.
- Hooks can run arbitrary shell and can perform network actions unless the workflow and host environment prevent it.

## Safety Controls Found

Controls present:

- Per-issue workspaces.
- Workspace path canonicalization and root containment checks.
- Sanitized workspace directory names.
- Codex cwd set to issue workspace.
- Default Codex approval policy rejects approval requests when omitted.
- Default Codex thread sandbox is `workspace-write`.
- Default turn sandbox policy is workspace-rooted and sets `networkAccess: false`.
- CLI requires an explicit acknowledgement flag before starting the daemon.
- Hook timeout default is `60000 ms`.
- Codex read, turn, and stall timeouts.
- Stalled sessions are retried with backoff.
- Unsupported dynamic tools return structured failures.
- Optional observability dashboard/API binds to loopback by default.

Controls that remain external or deployment-specific:

- OS/container/VM sandboxing.
- Network egress policy.
- Durable queue safety.
- Credential minimization.
- Approval policy choice.
- Review gates before merge/landing.

## Integration Risks

Major risks for AI-Orchestrator / PMBOT:

- The reference implementation is a daemon that polls and dispatches work. It should not be started casually in the PMBOT runtime.
- Linear-first architecture does not match AI-Orchestrator source-of-truth files.
- No shipped GitHub Issues adapter.
- No shipped durable file queue.
- Elixir/OTP is a new runtime stack for this workspace.
- Real runs require Codex app-server auth and likely network.
- The sample `elixir/WORKFLOW.md` is high-trust and sets `approval_policy: never`.
- Hooks are arbitrary shell scripts.
- Workspace cleanup can delete workspaces under `workspace.root`; root configuration must be treated as safety-critical.
- The optional `linear_graphql` dynamic tool exposes raw Linear GraphQL access when configured.
- The sample workflow includes PR push/land behavior that is outside PMBOT's current local/offline/analysis-only boundary.

## Fit For AI-Orchestrator

Fit: partial.

Use directly:

- Specification and architecture concepts.
- `WORKFLOW.md` contract model.
- Workspace isolation rules.
- Codex app-server invocation model.
- Stuck-session/retry model.
- Proof-of-work model.

Do not use directly yet:

- Long-running daemon in PMBOT runtime.
- Linear polling.
- High-trust sample workflow.
- PR landing flow.
- Raw tracker mutation tools.

Needs adaptation:

- Local file-based task queue adapter.
- Local task state model.
- Explicit approval gate before each Codex run.
- No-op or fake runner profile for dry-run validation.
- Hardening profile with network disabled where possible.
- Proof bundle written to AI-Orchestrator docs/logs.

## Recommended Next Task

Recommended next task: `ORCH-SYMPHONY-001-ADAPT-SPEC-LOCAL-QUEUE`

Scope for that task:

- Do not integrate runtime yet.
- Draft a local queue adapter spec that maps AI-Orchestrator task files to Symphony's normalized issue model.
- Define local states equivalent to `Todo`, `In Progress`, `Human Review`, `Done`, and blocked states.
- Define a dry-run profile using a fake/no-op Codex app-server command.
- Define a strict safety profile for PMBOT: no wallet/trading/payment paths, no credentials, no OpenRouter, no Polymarket, no Telegram/OpenClaw.
- Decide whether to adapt the Elixir implementation later or build a smaller local runner from the official spec.

`ORCH-SYMPHONY-001-INSTALL-LOCAL-DRY-RUN` should wait until the local queue and safety profile are specified, because installing the official reference as-is only proves the Elixir stack, not compatibility with AI-Orchestrator as the source of truth.

## Validation

Safe validation requested:

- `python -m json.tool docs/ORCH_SYMPHONY_000_REFERENCE_SPIKE_RESULT.json` - passed.
- `git status --short` - completed; workspace already had many pre-existing untracked files, and this spike added only the two `docs/ORCH_SYMPHONY_000_REFERENCE_SPIKE*` files.

No package install, daemon start, unattended agent run, Codex run, Linear auth, GitHub auth, OpenAI/OpenRouter credential access, Polymarket API access, or destructive command was performed.
