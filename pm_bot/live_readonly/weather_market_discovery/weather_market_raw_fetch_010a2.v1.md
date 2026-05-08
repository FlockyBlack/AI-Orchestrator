# PMBOT SOURCE-010A2 Weather Refined Raw Fetch

- task_id: PMBOT-SOURCE-010A2-WEATHER-DISCOVERY-QUERY-REFINEMENT-AND-SECOND-READONLY-ATTEMPT
- fetch_status: selected
- refinement_attempt: true
- previous_attempt_status: completed_no_suitable_weather_market_found
- selected_market_id: 693869
- selected_market_title_or_question: Will the minimum Arctic sea ice extent this summer be less than 4m square kilometers?
- network_call_count: 15
- inspected_candidate_count: 2500
- weather_like_candidate_count: 15
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
- https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset=0&search=weather
- https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset=0&search=temperature
- https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset=0&search=rain
- https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset=0&search=rainfall
- https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset=0&search=precipitation
- https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset=0&search=snow
- https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset=0&search=snowfall
- https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset=0&search=hurricane
- https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset=0&search=tropical+storm
- https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=100&offset=0&search=storm

## Rejection Reasons

- 577294: weather_word_false_positive_or_sports_context
- 664045: long_horizon_climate_or_policy_not_direct_weather_pilot
- 678686: long_horizon_climate_or_policy_not_direct_weather_pilot
- 678687: long_horizon_climate_or_policy_not_direct_weather_pilot
- 678688: long_horizon_climate_or_policy_not_direct_weather_pilot
- 678689: long_horizon_climate_or_policy_not_direct_weather_pilot
- 678690: long_horizon_climate_or_policy_not_direct_weather_pilot
- 678691: long_horizon_climate_or_policy_not_direct_weather_pilot
- 693870: suitable_weather_market_candidate
- 693871: suitable_weather_market_candidate
- 693872: suitable_weather_market_candidate
- 693873: suitable_weather_market_candidate
- 693874: suitable_weather_market_candidate
- 693875: suitable_weather_market_candidate

## Safety

- source/rules discovery only
- no trading decision
- no probability, EV, edge, confidence, or side selection guidance
- no wallet, order, runtime, dispatcher, background worker, queue, browser, or canonical packet changes
