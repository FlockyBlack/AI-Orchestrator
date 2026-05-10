# Next Task Decision Matrix 015

## Need more real markets

- Next task: `ORCH-PMBOT-PRACTICAL-016-ADD-NEXT-REAL-MARKET-PACKET-AND-RUN-DAILY-WORKFLOW`
- Why: The current loop tracks five markets; more local packets improve operator coverage without live access.
- Blocked until: A safe local packet exists with title, rules, source placeholders, and unresolved outcome placeholder.
- Safety: Local-only packet import and paper tracking only.

## Need outcome resolution feedback

- Next task: `ORCH-PMBOT-PRACTICAL-017-PROCESS-FIRST-RESOLVED-OUTCOME-FEEDBACK-PACKET`
- Why: Feedback is blocked until a saved local resolution record exists for at least one market.
- Blocked until: A real local resolution record is saved and manually reviewed.
- Safety: Never invent outcome fields.

## Need source URL repair

- Next task: `ORCH-PMBOT-PRACTICAL-018-SOURCE-URL-REPAIR-PACKET-LOCAL-ONLY`
- Why: Three source records still need manual replacement or alternate official sources.
- Blocked until: Operator provides local replacement candidates.
- Safety: No access-control workaround, cookies, profiles, or browser automation.

## Need another controlled public fetch

- Next task: `ORCH-PMBOT-PRACTICAL-019-CONTROLLED-PUBLIC-FETCH-PACKET-SEPARATE-APPROVAL`
- Why: Fetch work is outside the daily runbook and needs explicit separate approval.
- Blocked until: A scoped manifest and approval packet exist.
- Safety: Not part of the daily workflow.

## Need practical UI/report polishing

- Next task: `ORCH-PMBOT-PRACTICAL-020-LOCAL-REPORT-POLISHING`
- Why: The operator surface can be refined after this runbook is used.
- Blocked until: Operator identifies which report is confusing.
- Safety: Documentation and local artifact rendering only.

## Need risk engine design later

- Next task: `ORCH-PMBOT-PRACTICAL-LATER-RISK-ENGINE-DESIGN-PAPER-ONLY`
- Why: Risk design belongs after reliable source and outcome feedback loops exist.
- Blocked until: Several resolved outcome feedback packets exist.
- Safety: Design only; no execution path.

## Need execution mock later

- Next task: `ORCH-PMBOT-PRACTICAL-LATER-EXECUTION-MOCK-PAPER-ONLY`
- Why: A mock can test accounting language after risk design, without real execution.
- Blocked until: Risk design and paper-only accounting constraints are written.
- Safety: No wallet, signing, or real-money action.

## Do not start real trading yet

- Next task: `BLOCKED-REAL-TRADING-NOT-A-PRACTICAL-015-OUTCOME`
- Why: The current system has unresolved outcomes and no proven feedback loop.
- Blocked until: Separate explicit approval after many safety and validation milestones.
- Safety: Real autonomous trading progress remains 0%.
