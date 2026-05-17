# PMBOT Local Environment Self-Test Bundle 078G

- Status: `blocked_missing_funder_address`
- Market: `BTC`
- Strategy: `tiny-momentum`
- Passed checks: `1/10`
- Blockers: `9`
- Allowed for live: `false`
- Order submission: `blocked`
- Order cancellation: `blocked`
- Signing by default: `false`
- Signer instantiated by default: `false`
- Raw secret output: `false`

## Checks

- `runtime_credential_visibility` status=`blocked_missing_private_key` passed=`false` artifact=`pm_bot/trading_core/artifacts/local_environment_self_test_078g/runtime_credential_visibility_077c/runtime_credential_visibility_077c_result.json`
- `funder_wallet_context` status=`blocked_missing_wallet_address` passed=`false` artifact=`pm_bot/trading_core/artifacts/local_environment_self_test_078g/funder_wallet_context_077g/funder_wallet_context_077g_result.json`
- `clob_sdk_account_readonly_probe` status=`blocked_sdk_unavailable` passed=`false` artifact=`C:/pmbot_artifacts/live_account_readonly_state_probe_070c/latest_live_account_readonly_state_status_070c.json`
- `local_real_check_bundle` status=`missing` passed=`false` artifact=`C:/pmbot_artifacts/local_real_check_bundle_072c/latest_local_real_check_bundle_status_072c.json`
- `selected_candidate_artifact` status=`missing` passed=`false` artifact=`C:/pmbot_artifacts/selected_candidate_artifact_075d/latest_selected_candidate_artifact_075d.json`
- `selected_token_verification` status=`missing` passed=`false` artifact=`C:/pmbot_artifacts/selected_token_verification_bridge_076a/latest_selected_token_verification_076a_status.json`
- `signer_diagnostic_evidence` status=`missing` passed=`false` artifact=`C:/pmbot_artifacts/signer_diagnostic_evidence_bridge_076c/latest_signer_diagnostic_evidence_076c_status.json`
- `payload_dry_run_readiness` status=`missing` passed=`false` artifact=`C:/pmbot_artifacts/payload_dry_run_readiness_076d/latest_payload_dry_run_readiness_076d_status.json`
- `first_supervised_tiny_order_readiness` status=`missing` passed=`false` artifact=`C:/pmbot_artifacts/first_supervised_tiny_order_readiness_077a/latest_first_supervised_tiny_order_readiness_077a_status.json`
- `telegram_runtime_smoke` status=`telegram_runtime_ready` passed=`true` artifact=`pm_bot/trading_core/artifacts/local_environment_self_test_078g/telegram_runtime_smoke_078g.json`

## Top Blockers

- `runtime_credential_visibility` `blocked_missing_private_key` - Missing runtime env visibility: POLYMARKET_API_KEY, POLYMARKET_API_SECRET, POLYMARKET_API_PASSPHRASE, POLYMARKET_PRIVATE_KEY, POLYMARKET_WALLET_ADDRESS, POLYMARKET_SIGNATURE_TYPE, POLYMARKET_FUNDER_ADDRESS
- `funder_wallet_context` `blocked_missing_wallet_address` - Missing funder/wallet context: POLYMARKET_WALLET_ADDRESS, POLYMARKET_FUNDER_ADDRESS, POLYMARKET_SIGNATURE_TYPE
- `clob_sdk_account_readonly_probe` `blocked_sdk_unavailable` - No supported Polymarket CLOB SDK module is importable in this Python runtime.
- `local_real_check_bundle` `missing` - local_real_check_bundle artifact status is missing; success was not inferred.
- `selected_candidate_artifact` `missing` - selected_candidate_artifact artifact status is missing; success was not inferred.

## Exact Next Safe Commands

- `python -m pm_bot.operator_runner.runtime_credential_visibility_diagnostic --market BTC --strategy tiny-momentum --dry-run`
- `python -m pm_bot.operator_runner.funder_wallet_context_diagnostic --market BTC --strategy tiny-momentum --dry-run`
- `python -m pm_bot.operator_runner.live_account_readonly_state_probe --market BTC --strategy tiny-momentum --dry-run`
- `python -m pm_bot.operator_runner.local_real_check_bundle --market BTC --strategy tiny-momentum --dry-run`
- `python -m pm_bot.operator_runner.selected_candidate_artifact --market BTC --strategy tiny-momentum --dry-run --candidate-index 0`
- `python -m pm_bot.operator_runner.local_environment_self_test_bundle --market BTC --strategy tiny-momentum --dry-run`
- `python -m pm_bot.operator_runner.static_safety_invariant_report --scope pm_bot --dry-run`

## Safety

- this bundle does not submit or cancel orders
- it does not sign by default or instantiate a signer
- it does not add wallet UI, browser automation, daemon, scheduler, or background worker behavior
- it emits status summaries and artifact paths only; raw secrets are not emitted
- Telegram smoke is local-only by default and does not request a network check

## Artifacts

- `pm_bot/trading_core/artifacts/local_environment_self_test_078g/local_environment_self_test_078g_result.json`
- `pm_bot/trading_core/artifacts/local_environment_self_test_078g/latest_local_environment_self_test_078g_status.json`
- `pm_bot/trading_core/artifacts/local_environment_self_test_078g/local_environment_self_test_078g_checks.json`
- `pm_bot/trading_core/artifacts/local_environment_self_test_078g/local_environment_self_test_078g_blockers.json`
- `pm_bot/trading_core/artifacts/local_environment_self_test_078g/local_environment_self_test_078g_operator_summary.md`
- `pm_bot/trading_core/artifacts/local_environment_self_test_078g/telegram_runtime_smoke_078g.json`
