# PMBOT OpenRouter 028 First One-Market Live Call With Safe User Env Import

Task: `PMBOT-OPENROUTER-028-FIRST-ONE-MARKET-LIVE-CALL-WITH-SAFE-USER-ENV-IMPORT`

Status: `completed_live_call_passed`

Market: `563650`

Session: `pmbot_openrouter_028_first_live_call_with_safe_user_env_import`

Model: `anthropic/claude-sonnet-4.5`

## Summary

Exactly one OpenRouter network call was performed through the existing PMBOT gated prompt-test harness in Sonnet-only mode.

The call used restored local manual packet artifacts only:

- `pm_bot/llm/manual_packet_batch/563650_prompt.v1.md`
- `pm_bot/llm/manual_packet_batch/563650_packet.v1.json`

The harness completed with:

- `sonnet_called: true`
- `critic_called: false`
- `safety_boundary_passed: true`
- `no_trading_decision: true`
- `sonnet_valid: true`
- `sonnet_json_recovered: true`

The JSON-fence recovery was the existing local validation path and preserved the original raw model output in the raw artifact.

## Environment Handling

Only safe presence checks were performed.

- Process environment before import: present
- User environment: present
- Safe import performed: false
- Process environment after import: present
- API key printed: false
- API key written to disk: false

The key value was not printed, echoed, logged, written, or inspected.

## Live Artifacts

Approved ignored run artifact directory:

`pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_028_first_live_call_with_safe_user_env_import`

Artifacts:

- Raw response: `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_028_first_live_call_with_safe_user_env_import/openrouter_sonnet_563650_raw.json`
- Parsed content: `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_028_first_live_call_with_safe_user_env_import/openrouter_sonnet_563650_content.json`
- Validation: `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_028_first_live_call_with_safe_user_env_import/openrouter_sonnet_563650_validation.json`
- Metadata summary: `pm_bot/llm/openrouter_test_artifacts/pmbot_openrouter_028_first_live_call_with_safe_user_env_import/openrouter_test_summary_563650.json`

Usage and cost were recorded in the harness summary:

- Prompt tokens: `3178`
- Completion tokens: `1862`
- Total tokens: `5040`
- Cost: `0.037464`
- Returned model: `anthropic/claude-4.5-sonnet-20250929`
- Provider: `Amazon Bedrock`

## Safety Boundaries

No wallet/private keys, orders, trading, runtime wiring, dispatcher changes, background workers, browser automation, or Polymarket API calls were performed.

The harness validator accepted the candidate for operator review only. Acceptance does not mean trading approval.

## Validation

Checks run:

- `python -m compileall pm_bot`
- `python -m pytest tests pm_bot\llm\tests -q`
- `python -m json.tool docs/PMBOT_OPENROUTER_028_RESULT.json`
- Secret/no-key-leak scan over generated 028 docs and OpenRouter artifacts

Results:

- Compileall passed
- Pytest passed: `256 passed`
- Result JSON parsed successfully
- Secret scan passed

## Git

No commit was created.

Reason: the repo already had unrelated pre-existing untracked OpenRouter 010 and 026 docs before this task, and the OpenRouter run artifacts are intentionally ignored runtime artifacts.
