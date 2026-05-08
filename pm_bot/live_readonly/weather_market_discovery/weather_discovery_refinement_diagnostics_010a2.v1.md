# PMBOT SOURCE-010A2 Weather Discovery Refinement Diagnostics

- task_id: PMBOT-SOURCE-010A2-WEATHER-DISCOVERY-QUERY-REFINEMENT-AND-SECOND-READONLY-ATTEMPT
- previous_attempt_status: completed_no_suitable_weather_market_found
- inspected_candidate_count: 2500
- weather_like_candidate_count: 15
- selected_market_id: 693869
- selected_market_title_or_question: Will the minimum Arctic sea ice extent this summer be less than 4m square kilometers?
- recommended_next_action: PMBOT-SOURCE-010B-WEATHER-DRAFT-CAPTURE-AUTOFILL-FROM-READONLY-CANDIDATE
- no_market_action_guidance: true
- no_trading_authority: true

## Refined Strategy

- Reused 010A active/open Gamma market pagination.
- Added keyword searches for weather, temperature, rain, snow, storms, wind, heat, cold, drought, air quality, and climate-event terms.
- Expanded local filtering for weather-adjacent direct measurement markets, including named storms, AQI, drought, and Arctic sea ice extent.
- Selected at most one candidate using weather metadata completeness only.

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
