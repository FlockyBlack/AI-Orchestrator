# PMBOT Future Real Adapter Boundary

The real adapter is not implemented in this milestone.

## Not implemented

- real adapter not implemented
- wallet not implemented
- signing not implemented
- orders not implemented
- authenticated endpoints not implemented

## Required before any supervised real execution

- Separate explicit approval task
- Wallet isolation design not implemented yet
- Signing isolation design not implemented yet
- Order adapter boundary not implemented yet
- Hard kill switch
- Post-order reconciliation not implemented yet
- Manual pre-trade approval gate
- Risk engine upgrade with tested caps and halt states

## Boundary flags

- real_adapter_implemented: `false`
- wallet_implemented: `false`
- signing_implemented: `false`
- orders_implemented: `false`
- authenticated_endpoints_implemented: `false`
- kill_switch_required: `true`
- reconciliation_required: `true`
- manual_approval_required: `true`
- risk_engine_upgrade_required: `true`
