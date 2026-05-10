# PMBOT Practical Architecture Summary

## Practical loop components

PMBOT now has a concrete local analysis-quality loop:

1. Local market packet import normalizes saved/hand-written packets into `pmbot_one_market_input.v1`.
2. One-market analysis creates source-attributed JSON/Markdown cards and a paper-only hypothesis.
3. Market queue summaries show each market state and next operator action.
4. Active paper hypothesis tracking surfaces unresolved outcome checks.
5. Local outcome records feed paper feedback.
6. Source learning batch and source scorecard aggregate which sources helped or hurt analysis quality.
7. Operator console, dashboard index, and next-action reports make the workflow inspectable.
8. Safety scan checks generated practical artifacts for unsafe wording and unsafe flags.

## Local-only and replay/static surfaces

All Night 002 modules read and write local JSON/Markdown files. They do not fetch public data, call APIs, use API keys, operate browser automation, or depend on live markets. Fixtures are synthetic static records designed for deterministic replay.

## Source learning

Source learning aggregates explicit feedback records into a ledger. Labels such as useful, stale, misleading, contradictory, insufficient, and unknown come from local paper feedback. The ledger remains transparent and reviewable.

This is not autonomous ML training. No weights, prompts, models, or runtime behavior are updated automatically.

## Not real trading

The practical loop does not produce real market instructions. It does not access wallets, private keys, signing, orders, balances, trading endpoints, authenticated endpoints, runtime dispatchers, or autonomous execution paths. Paper hypotheses are non-executable analysis-quality tracking records.

## Preparation for controlled public read-only fetch

This batch clarifies the local contracts needed before public read-only fetching:

- normalized packet shape,
- source attribution requirements,
- missing-evidence visibility,
- outcome feedback records,
- source-learning labels,
- operator console expectations,
- safety scan expectations.

Before controlled public read-only fetch, PMBOT still needs a gated fetch contract, source allowlist, captured evidence bundle, rate and provenance rules, and explicit tests proving no authenticated or trading path can be reached.
