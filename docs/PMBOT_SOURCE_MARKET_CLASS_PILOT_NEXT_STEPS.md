# PMBOT SOURCE Market Class Pilot Next Steps

Recommended follow-up sequence after SOURCE-008B:

1. PMBOT-SOURCE-009A-ESPORTS-MARKET-CLASS-PILOT-READONLY-PROTOCOL
2. PMBOT-SOURCE-009B-WEATHER-MARKET-CLASS-PILOT-READONLY-PROTOCOL
3. PMBOT-SOURCE-009C-CRYPTO-MARKET-CLASS-PILOT-READONLY-PROTOCOL

Each follow-up must be a separate task. Any public read-only source fetch requires explicit network approval in that task. Future pilot work must write raw artifacts first, normalize locally, keep capture templates as draft unless reviewed by the operator, and preserve SOURCE-007 and SOURCE-008 safety state.

## Required Guardrails

- no OpenRouter calls unless a separate future task explicitly allows them
- no Polymarket API calls unless a separate future task explicitly allows public read-only calls
- no wallet or private key access
- no orders
- no runtime wiring
- no dispatcher, background worker, queue, or browser automation
- no canonical packet mutation
- no probability, EV, edge, confidence, side selection, trade recommendation, buy, sell, hold, enter, exit, guaranteed win, free money, or sure bet labels
