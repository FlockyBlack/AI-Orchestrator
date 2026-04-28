# PMBOT Crypto Numeric Guardrail Coverage

Fixture-only coverage around the extension guard threshold.

## Summary

- Coverage cases: 6
- Guardrail triggered: 2
- Paper candidates preserved: 4
- Watchlist caps: 2
- Unexpected blocks: 0
- Unexpected allows: 0

## Coverage Rows

| case_id | gap | yes_price | expected_trigger | decision | action | unexpected_block | unexpected_allow |
| --- | --- | --- | --- | --- | --- | --- | --- |
| below_distance_below_yes | 0.0540 | 0.5900 | false | paper_candidate | paper_limit_order | false | false |
| above_distance_below_yes | 0.0560 | 0.5900 | false | paper_candidate | paper_limit_order | false | false |
| below_distance_above_yes | 0.0540 | 0.6100 | false | paper_candidate | paper_limit_order | false | false |
| above_distance_above_yes | 0.0560 | 0.6100 | true | watchlist | no_action | false | false |
| clear_bad_overextended_rich_price | 0.0600 | 0.6200 | true | watchlist | no_action | false | false |
| clear_legitimate_candidate | 0.0422 | 0.5900 | false | paper_candidate | no_action | false | false |

## Limitations

- Uses fixture coverage cases only; no live markets, prices, or APIs are fetched.
- Coverage characterizes the current extension rule and does not broaden it.
- No runtime integration, prompt automation, credentials, or wallet access is included.

- offline_only=true; paper_only=true; execution_allowed=false; trading_allowed=false
