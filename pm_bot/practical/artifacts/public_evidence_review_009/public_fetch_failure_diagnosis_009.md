# Public fetch failure diagnosis

## Request summary

- Attempted: 5
- Succeeded: 1
- Failed: 4
- Blocked: 0

## Failed request table

| Market | Source URL | Category | Likely cause |
| --- | --- | --- | --- |
| `598936` | `https://www.parliament.uk/about/how/elections-and-voting/general/` | `http_error` | The public site denied this simple read-only request in PRACTICAL-008. |
| `597964` | `https://www.elysee.fr/emmanuel-macron` | `source_unavailable` | The URL may require certificate-chain handling or a different official page. |
| `691547` | `https://www.kraken.com/blog` | `source_unavailable` | The configured URL redirects to a different host/path and the fetcher intentionally blocked redirects. |
| `692258` | `https://www.microstrategy.com/press` | `http_error` | The public site denied this simple read-only request in PRACTICAL-008. |

## Likely causes

- `http_error`: 2
- `source_unavailable`: 2

## Safe recovery actions

- Verify the URL manually and prefer an alternative official public source if access remains denied.
- Replace or normalize the URL only after operator review of the source category and redirect/certificate behavior.
- Keep all recovery work non-executable until a later scoped task is approved.

## URL manifest fixes needed

- `https://www.parliament.uk/about/how/elections-and-voting/general/` -> `use_alternative_official_source`
- `https://www.elysee.fr/emmanuel-macron` -> `replace_url`
- `https://www.kraken.com/blog` -> `replace_url`
- `https://www.microstrategy.com/press` -> `use_alternative_official_source`

## What not to do

- Do not repeat these source requests until an operator reviews the URL/source fix candidates.
- Do not use authenticated endpoints, cookies, browser automation, API keys, wallet paths, order paths, or trading paths.
- Do not treat source accessibility failures as market outcome evidence.
