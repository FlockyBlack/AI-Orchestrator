# Weather Outcome Tracking Contract - 693869

This contract defines how future weather outcome tracking may work for market `693869`.

This is not profit/loss tracking. It is not a trading recommendation. It records only weather outcome evidence, source alignment, and operator review notes when the future outcome evidence becomes available.

## Scope

- Tracking scope: weather outcome and source alignment only
- Outcome known: false
- Outcome source: null
- Outcome source timestamp: null
- Final measurement value: null
- Operator review required: true

## Weather Fields

- Weather metric: minimum Arctic sea ice extent
- Threshold or condition: less than 4 million square kilometers
- Official dataset or source candidate: National Snow and Ice Data Center Sea Ice Index Daily Extent data set
- Source hierarchy candidate: NH-Daily-Extent tab, minimum value for any day in the market window
- Unit: million square kilometers
- Date or time window: between August 1, 2026 and October 1, 2026

## Future Review Fields

- Source alignment review
- Source helpfulness review
- Contradictions found
- Operator usefulness notes
- Official source status
- Measurement alignment

## Forbidden Inputs

- no profit as primary learning score
- no stake
- no PnL
- no ROI
- no EV
- no edge
- no probability
- no trade recommendation
- no side selection

## Safety Boundary

This contract has no market action guidance, no trading authority, no execution authority, no wallet authority, and no order authority. It does not use OpenRouter, Polymarket API calls, external network calls, authenticated endpoints, browser automation, runtime wiring, dispatcher changes, queue mutation, or canonical packet mutation.
