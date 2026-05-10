# PMBOT Manual Public URL Collection

PRACTICAL-017 created the public evidence plan for the new Bitcoin $150k market, but it had no concrete public URLs.

- Market: `573656` Will Bitcoin hit $150k by December 31, 2026?
- Missing URL rows: 3
- Filled URLs now: 0
- Future manifest executable requests now: 0
- Future fetch ready: `false`

## Why Fetch Is Blocked

- The packet has three null `operator_supplied_url` fields.
- Local validation reports missing operator-supplied URLs.
- A future manifest preview from this unfilled packet has zero executable request intents.

## URLs To Collect Manually

- `public_market_metadata_endpoint_placeholder` public market metadata page/reference: public market metadata, rules, status, and linked reference snapshot
- `public_static_web_page_placeholder` public Bitcoin price reference category: public Bitcoin price threshold reference snapshot
- `public_resolution_source_page_placeholder` public resolution source reference category: public resolution rules or resolution-source reference snapshot

## How To Fill The Packet

- Edit only the `operator_supplied_url` value for each candidate row.
- Keep the URL public, read-only, and directly related to the expected evidence type.
- Leave approval for a separate future task after validation passes.

## How Validation Works

- Null URLs stay missing.
- Supplied URLs are checked locally for HTTP(S), public host shape, credential-like query keys, and prohibited path hints.
- Validation does not fetch the URL.

## Future Manifest Creation

- A filled, validated packet can be converted into capped request intents.
- The manifest builder does not approve or perform the future fetch.

## Why This Is Not Trading

- The artifacts collect public evidence URLs only.
- They do not resolve outcomes, generate market instructions, or touch wallet/order/trading paths.

## Next Recommended Action

- `ORCH-PMBOT-PRACTICAL-017C-FILL-NEW-MARKET-PUBLIC-URL-PACKET-MANUALLY` if operator provides URLs; otherwise continue daily workflow/outcome tracking.
