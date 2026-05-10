# Approval Blocker Scenarios

- Scenarios: 10

## Scenarios

- `approval_missing` approval missing
  Expected behavior: `block`
  Reason: No manual approval artifact grants the future task.
  Safe recovery action: Keep fetch blocked and create a reviewed approval artifact.
- `auth_required_by_source` auth required by source
  Expected behavior: `block`
  Reason: Public read-only scope cannot use login, cookies, credentials, or private API keys.
  Safe recovery action: Replace the source with a public no-auth source or keep it out of scope.
- `source_category_blocked` source category blocked
  Expected behavior: `block`
  Reason: The source category is blocked by the registry.
  Safe recovery action: Choose an allowed source category and update the manifest locally.
- `request_count_exceeds_limit` request count exceeds limit
  Expected behavior: `block`
  Reason: The request total is greater than the approved maximum.
  Safe recovery action: Reduce request intents or create a narrower approval artifact.
- `evidence_save_disabled` evidence save disabled
  Expected behavior: `block`
  Reason: Future public evidence must be saved before replay.
  Safe recovery action: Restore evidence saving and validate the save plan.
- `replay_before_update_disabled` replay-before-update disabled
  Expected behavior: `block`
  Reason: Saved evidence must be replayed before PMBOT analysis changes.
  Safe recovery action: Restore replay-before-update and run replay validation.
- `trading_endpoint_detected` trading endpoint detected
  Expected behavior: `block`
  Reason: Execution-related endpoints are out of scope.
  Safe recovery action: Remove the endpoint and keep the source public read-only.
- `wallet_signing_required` wallet/signing required
  Expected behavior: `block`
  Reason: Wallet, private-key, signing, custody, and KYC paths are blocked.
  Safe recovery action: Use only public no-wallet evidence sources.
- `scheduler_background_fetch_requested` scheduler/background fetch requested
  Expected behavior: `block`
  Reason: This approval path allows only a finite operator-approved task.
  Safe recovery action: Use a one-time manually approved task with no scheduler or polling.
- `broad_unrestricted_fetch_requested` operator tries to approve broad unrestricted fetch
  Expected behavior: `block`
  Reason: Approval must be limited to named markets, source categories, and request count.
  Safe recovery action: Replace with a narrow approval artifact for the listed scope only.
