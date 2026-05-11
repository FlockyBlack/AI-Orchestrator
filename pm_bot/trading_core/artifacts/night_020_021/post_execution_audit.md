# PMBOT Post-Execution Audit

- Audit passed: `true`
- Violations: 0
- Warnings: 0

## Checks

### Intent to risk gate consistency

- Status: `passed`
- risk result exists for all 6 intent candidates

### Risk gate to execution consistency

- Status: `passed`
- risk gate results align with execution statuses

### Execution to ledger consistency

- Status: `passed`
- ledger has one position for each of 2 paper fills

### Portfolio to ledger consistency

- Status: `passed`
- portfolio exposure matches ledger exposure: 50.0

### Paper trading safety flags

- Status: `passed`
- all audited real-money and endpoint flags remain false

## Safety flags

- real_order_submitted: `false`
- wallet_used: `false`
- trading_endpoint_used: `false`
- real_money_used: `false`
- autonomous_trading_enabled: `false`
