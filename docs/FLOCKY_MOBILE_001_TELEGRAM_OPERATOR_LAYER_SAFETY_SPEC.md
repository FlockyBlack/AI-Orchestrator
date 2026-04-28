# FLOCKY-MOBILE-001 Telegram Operator Layer Safety Spec

## Scope

This is a compact, reference-only safety specification for a future Telegram/mobile operator layer.

Allowed future use cases:
- read-only status summaries
- operator notifications
- compact task and result summaries
- manual approval or rejection capture
- prompt handoff display
- artifact pointer display
- escalation alerts
- `needs human` summaries

## Non-Goals

This layer is not:
- a runtime executor
- a task runner
- autonomous execution
- background execution
- command shell access
- wallet, API, trading, or order control
- a replacement for AI-Orchestrator
- a replacement for local review artifacts
- permission to enable Telegram now

## Source-of-Truth Boundary

AI-Orchestrator remains the only source of truth and runtime workspace.

Telegram may only mirror or summarize approved reference artifacts.

Telegram messages must not become authoritative runtime state, and must not replace local review artifacts.

## Authority Model

- AI-Orchestrator remains the source of truth.
- Telegram may mirror only approved summaries, pointers, and review-safe status.
- Operator decisions captured through Telegram are provisional until written or reviewed through approved local artifacts.
- No Telegram message alone should mutate runtime state.
- No command should execute just because it was sent from mobile.

## Allowed Command Classes

Future-safe command classes:
- `READ_STATUS`
- `SHOW_SUMMARY`
- `SHOW_ARTIFACT_POINTERS`
- `PREPARE_PROMPT`
- `RECORD_OPERATOR_INTENT_REFERENCE_ONLY`
- `ESCALATE_TO_MANUAL_REVIEW`

These are viewing, preparation, or reference-capture classes only.

## Forbidden Command Classes

Explicitly forbidden:
- `RUN_CODEX`
- `RUN_SHELL`
- `MODIFY_RUNTIME`
- `START_BACKGROUND_TASK`
- `ENABLE_TELEGRAM_BOT`
- `CHANGE_CONFIG`
- `PLACE_ORDER`
- `TRADE`
- `WALLET_ACTION`
- `API_KEY_ACTION`
- `INSTALL_SKILL`
- `FETCH_REMOTE_CODE`
- `WRITE_TO_SOURCE_OF_TRUTH_WITHOUT_REVIEW`

## Approval Model

Required approvals:
- enabling Telegram requires a separate approved implementation task
- bot token creation requires explicit operator approval
- command parser requires separate review
- any writeback requires separate review
- any runtime mutation requires separate review
- any PMBOT-related command defaults to offline, local, paper-only unless explicitly approved otherwise

## Message and Output Safety

- never expose tokens or secrets
- never expose dashboard auth URL or token
- mask credentials
- avoid full raw logs unless explicitly requested
- prefer compact summaries and artifact pointers
- include safety status in result summaries
- mark stale status clearly

## Failure and Abuse Cases

Handle these as safety-sensitive cases:
- stolen phone or stolen session
- accidental command send
- ambiguous operator message
- stale dashboard or stale status info
- duplicate approval
- replayed message
- Telegram outage
- bot token leak
- malicious prompt injection through chat messages

Default handling:
- do not execute
- degrade to manual review
- require explicit local confirmation where ambiguity or abuse risk exists

## Review Record Template

Reference-only template:

```json
{
  "review_id": "manual-review-id",
  "mobile_request_id": "telegram-or-mobile-message-id",
  "operator_message_summary": "short summary",
  "interpreted_intent": "plain-language intent",
  "command_class": "READ_STATUS | SHOW_SUMMARY | SHOW_ARTIFACT_POINTERS | PREPARE_PROMPT | RECORD_OPERATOR_INTENT_REFERENCE_ONLY | ESCALATE_TO_MANUAL_REVIEW",
  "approval_status": "provisional | needs_local_review | blocked",
  "source_artifact_pointer": "path/to/local/artifact",
  "allowed_next_action": "safe next step",
  "forbidden_next_action": "disallowed next step",
  "safety_flags": {
    "stale_status": false,
    "ambiguous_message": false,
    "duplicate_or_replay_risk": false,
    "credential_exposure_risk": false,
    "runtime_mutation_requested": false,
    "pmbot_live_behavior_risk": false
  },
  "reviewed_at_manual": "YYYY-MM-DD HH:MM local"
}
```

## PMBOT-Specific Overlay

For PMBOT:
- no live API
- no wallet or private key
- no real order
- no trading execution
- no payment credentials
- no `dispatcher.py`, `run_codex.py`, or runtime modification
- Telegram cannot approve live trading behavior
- any violation is `BLOCKED`

## Recommended Use

Use this spec only as a safety boundary for future design and review of a mobile operator layer.

Safe future shape:
- show compact status
- show pointers
- capture provisional operator intent
- route anything sensitive back to local manual review

Unsafe future shape:
- executing commands from chat
- mutating runtime from Telegram
- approving sensitive behavior from mobile alone
- treating Telegram as source of truth
