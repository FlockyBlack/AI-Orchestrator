# Practical Safety Boundary Reference 015

## Boundaries

- No wallet or private key access.
- No order placement.
- No trading endpoints.
- No real-money action.
- No authenticated endpoint.
- No OpenRouter call unless separately approved.
- No Polymarket API call unless separately approved.
- No scheduler, daemon, background worker, watcher, polling loop, or unattended automation.
- No market recommendations, probability, EV, edge, confidence, or side-selection output.
- Paper-only tracking only.

## Required false flags

- `live_network_used`: `false`
- `authenticated_endpoints_used`: `false`
- `wallet_or_private_key_access`: `false`
- `orders_or_trading_actions`: `false`
- `runtime_or_dispatcher_changes`: `false`
- `market_recommendation_generated`: `false`
- `probability_ev_edge_or_side_selection_generated`: `false`
- `outcome_resolution_invented`: `false`

## Required zero counts

- `openrouter_calls_performed`: `0`
- `new_polymarket_api_calls_performed`: `0`
