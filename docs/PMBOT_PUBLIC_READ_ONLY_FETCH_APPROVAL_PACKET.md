# PMBOT Public Read-Only Fetch Approval Packet

## Why This Exists

PRACTICAL-006 creates one operator-facing approval packet for the first controlled public read-only fetch dry run. It does not fetch public data. It turns the PRACTICAL-005 fetch prep artifacts into a single review surface that explains the future request plan, limits, evidence-save requirements, replay requirements, blockers, and approval boundary.

The operator can inspect one packet and decide whether a separate future task may perform a finite public read-only fetch.

## Relation To PRACTICAL-005

PRACTICAL-005 created the local-only preparation layer:

- Fetch plan
- Dry-run preview
- Public source registry
- Pending operator approval record
- Readiness gate
- Fetch-plan-to-active-hypotheses link map
- Saved evidence packet and replay adapter contracts

PRACTICAL-006 reuses those artifacts. It does not rewrite the PRACTICAL-005 contracts and does not grant approval.

## Approval Packet Contents

`pm_bot/practical/artifacts/public_read_only_fetch_approval_006/approval_packet_5_markets.md` shows:

- The five covered market IDs and titles
- The public source categories that would be used later
- Why each source category is needed
- Max request count, timeout, and retry policy
- Evidence-save and replay requirements
- Current readiness blockers
- Safety boundary and blocked scope
- The exact future task allowed only after manual approval

Current status remains:

- `operator_approval_required: true`
- `operator_approval_granted: false`
- `ready_for_controlled_public_fetch: false`
- `live_fetch_performed: false`

## Request Manifest

`fetch_request_manifest_5_markets.json` and `.md` define deterministic request intents. Each intent includes market ID, source category, source placeholder, reason, expected evidence type, linked paper hypothesis, evidence save path, registry status, and explicit no-auth/no-wallet/no-trading flags.

The manifest is not execution. It is only a local plan for a future manually approved task.

## Evidence-Save Plan

`evidence_save_plan_5_markets.json` and `.md` specify how future public evidence must be saved before replay:

- Evidence directory
- Filename pattern
- Required metadata fields
- Raw capture policy
- Normalized claim policy
- No-overwrite policy
- Redaction policy
- Validation-before-use requirement

## Replay-Before-Update Plan

`replay_before_update_plan_5_markets.json` and `.md` define the requirement that saved public evidence must be replayed into PMBOT before any practical analysis or hypothesis update.

The replay plan requires:

- Replay adapter
- Source packet mapping
- Contradiction check
- Staleness check
- Operator review after replay
- No automatic analysis update
- No automatic trading

## Manual Approval Template

`manual_operator_approval_template.json` and `.md` are pending templates. They are not approval.

The future task remains blocked unless a later separate operator action changes the approval artifact manually and supplies `approved_by` and `approved_at`.

## Blocker Scenarios

`approval_blocker_scenarios.json` and `.md` list expected block behavior for:

- Missing approval
- Auth-required source
- Blocked source category
- Request count above limit
- Evidence save disabled
- Replay-before-update disabled
- Trading endpoint detected
- Wallet/signing required
- Scheduler or background fetch requested
- Broad unrestricted fetch approval attempted

## Why No Live Fetch Was Performed

This task is an approval-packet task only. It reads local artifacts and writes local JSON/Markdown. It does not call OpenRouter, Polymarket APIs, authenticated endpoints, wallet/signing paths, order paths, trading paths, schedulers, daemons, watchers, browser automation, or public data sources.

## Future Allowed Task After Manual Approval

The only future task described by this packet is:

`ORCH-PMBOT-PRACTICAL-007-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-EXECUTION-OPERATOR-APPROVED`

That task would still be limited to finite public read-only fetches for the listed markets and source categories. It would need to save evidence before use and replay saved evidence before any analysis update.

## Why This Is Still Not Trading

The packet does not produce market action recommendations, does not touch wallet or signing paths, does not use order or trading endpoints, and does not enable autonomous operation. It only prepares a reviewable approval boundary for future public evidence capture.

## Remaining Gaps

Before controlled public read-only fetch execution:

- Manual operator approval remains pending.
- The future task must honor the manifest, limits, save plan, replay plan, and blocker scenarios.
- Evidence must be saved and validated before replay.

Before any real-money activity:

- Real-money execution remains out of scope.
- Wallet/key policy, audited execution design, source-quality history, outcome feedback, risk controls, and separate explicit approvals would still be required.
