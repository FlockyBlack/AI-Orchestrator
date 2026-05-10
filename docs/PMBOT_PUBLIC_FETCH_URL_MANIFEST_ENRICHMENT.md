# PMBOT Public Fetch URL Manifest Enrichment

## Purpose

PRACTICAL-007 proved that the controlled public read-only fetch executor blocks unsafe or incomplete manifests before network access. It blocked because the approved manifest contained placeholder source references instead of concrete HTTP(S) URLs, and because the manifest had 10 request intents while the scoped approval allowed at most 5.

PRACTICAL-007B prepares the next manifest locally. It does not fetch, browse, call OpenRouter, call Polymarket APIs, or use authenticated endpoints.

## What Changed

- The executable manifest now contains 5 concrete public HTTP(S) URL candidates.
- The request count is capped at 5.
- Placeholder-only market metadata references are separated into `missing_url_request_intents`.
- Auth, wallet, order, trading, credential, cookie, login, and unsafe URL shapes remain blocked by local validation.
- Operator approval for the next controlled fetch remains pending.

## Concrete URL Selection

Concrete URLs come only from the manual local fixture:

`pm_bot/tests/fixtures/public_read_only_fetch_url_enrichment/public_url_mapping.manual_fixture.json`

The fixture is intentionally conservative. It uses explicit public URLs only when the URL is a stable official or public source candidate matching the local market source category. It does not infer opaque Polymarket market URLs, use APIs, or construct URLs from vague text.

Selected executable URLs:

- `563650`: `https://www.supremecourt.gov/docket/docket.aspx`
- `597964`: `https://www.elysee.fr/emmanuel-macron`
- `598936`: `https://www.parliament.uk/about/how/elections-and-voting/general/`
- `691547`: `https://www.kraken.com/blog`
- `692258`: `https://www.microstrategy.com/press`

These are future read-only source candidates only. They do not verify outcomes by themselves and do not create a market recommendation.

## What Remains Missing

The 5 public market metadata request intents remain missing because the local artifacts contain only market IDs and placeholder metadata references. No stable concrete public market metadata URL can be safely inferred without browsing or using a Polymarket API.

## Preflight Status

The enriched manifest passes URL safety and request-count checks for the executable subset. It is still not ready to execute now because operator approval is pending.

After operator approval, the current preflight says the next controlled public read-only fetch would be ready to attempt.

## Next Operator Action

Review:

- `pm_bot/practical/artifacts/public_read_only_fetch_url_enrichment_007b/enriched_fetch_request_manifest.md`
- `pm_bot/practical/artifacts/public_read_only_fetch_url_enrichment_007b/enriched_manifest_url_safety_report.md`
- `pm_bot/practical/artifacts/public_read_only_fetch_url_enrichment_007b/scoped_approval_for_enriched_manifest.pending.md`
- `pm_bot/practical/artifacts/public_read_only_fetch_url_enrichment_007b/enriched_manifest_execution_preflight.md`
- `pm_bot/practical/artifacts/public_read_only_fetch_url_enrichment_007b/concrete_url_manifest_operator_card.md`

If approved in a separate task, run:

`ORCH-PMBOT-PRACTICAL-008-FIRST-CONTROLLED-PUBLIC-READ-ONLY-FETCH-EXECUTION-WITH-CONCRETE-URL-MANIFEST`
