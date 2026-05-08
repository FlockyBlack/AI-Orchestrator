# PMBOT SOURCE-010A Weather Raw Fetch

- task_id: PMBOT-SOURCE-010A-WEATHER-MARKET-CLASS-PILOT-READONLY-DISCOVERY
- fetch_status: no_suitable_weather_market_found
- selected_market_id: None
- selected_market_title_or_question: None
- network_call_count: 5
- inspected_candidate_count: 2500
- network_allowed_explicitly: true
- public_readonly_only: true
- authenticated_endpoints_used: false
- auth_headers_used: false
- wallet_or_private_key_accessed: false
- orders_created: false
- no_market_action_guidance: true

## Endpoints

- https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=500&offset=0
- https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=500&offset=500
- https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=500&offset=1000
- https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=500&offset=1500
- https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=500&offset=2000

## Safety

- no trading decision
- no probability, EV, edge, confidence, or side selection guidance
- no wallet, order, runtime, dispatcher, background worker, queue, browser, or canonical packet changes
