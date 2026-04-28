# PM Bot Read-Only Fetcher Approval Checklist V1

PMBOT-BATCH-008 is design-only. Any future implementation batch must satisfy every checklist item below before code is approved.

- [ ] human approval required before implementation starts
- [ ] Flocky validation required before implementation starts
- [ ] no wallet or private key access
- [ ] no signer or signature handling
- [ ] no execution or order imports
- [ ] no runtime, dispatcher, state, result, freeze, or checkpoint mutation
- [ ] raw snapshot artifact only as fetcher output
- [ ] normalized snapshot validation required before any replay import
- [ ] quarantine required for malformed data
- [ ] quarantine required for stale data
- [ ] quarantine required for unsafe or contradictory data
- [ ] paper replay only as downstream path
- [ ] no live trade path
- [ ] no watchlist execution
- [ ] no autonomous trading
- [ ] no runtime wiring or `run_codex` integration
- [ ] no network or API code merged before the test plan is accepted
