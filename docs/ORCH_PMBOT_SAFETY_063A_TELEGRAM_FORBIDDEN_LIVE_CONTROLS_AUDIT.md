# ORCH-PMBOT-SAFETY-063A Telegram Forbidden Live Controls Audit

## Scope

This audit adds a focused regression check for the Telegram operator surfaces present after the 062TB master fix and the 063 live-enablement gate work. It does not add Telegram runtime features, live execution, signing, wallet access, order submission, or order cancellation.

Replay note: this 063A audit was replayed onto 063B master head `ee2363b75209b3ba9375ea0cd6a8dd5780a456e1` from source head `b9273a37234f16e2304874b2731d32dfad7729a2` without carrying unrelated older-base deletions.

The tested Telegram control surfaces are:

- Telegram console button labels and callback data
- home, fallback, language, and panel launch button labels
- supported command names and callback routing
- Telegram command menu entries
- safe action registry identifiers, callback data, labels, modules, and command argv
- generated 062T pre-live gate controls manifest fields that explicitly record forbidden controls as absent

## Forbidden Controls

The focused test verifies no Telegram control identifier, callback, label, command, module, or allowed dry-run command exposes these forbidden live/sign/wallet controls:

- `run_signer`
- `pmbot:run:signer`
- `Run Signer`
- `approve-live`
- `send-order`
- `submit-order`
- `cancel-order`
- `sign`
- `signer`
- `wallet`
- `connect-wallet`
- `unlock-wallet`
- `live-enable`
- `live-execute`

Safety text may still state that signing, wallet access, and order submission are blocked. The audit treats that as non-executable safety documentation, not as a control.

## Result

The new regression file is `pm_bot/tests/test_telegram_forbidden_live_controls_063a.py`.

It proves:

- no forbidden live/sign/wallet terms appear in Telegram control identifiers, labels, callback data, command names, command menu entries, safe action modules, or safe action command argv
- `run_signer` and `pmbot:run:signer` do not resolve to safe actions
- every Telegram safe action remains `--dry-run`
- no safe action command includes live, sign, wallet, submit, cancel, approve-live, or execute flags
- generated 062T controls keep all forbidden control-added flags false
- the only allowed 062T run command remains `python -m pm_bot.operator_runner.pre_live_tiny_order_gate --market BTC --strategy tiny-momentum --dry-run`

Full validation is recorded in `docs/ORCH_PMBOT_SAFETY_063A_TELEGRAM_FORBIDDEN_LIVE_CONTROLS_AUDIT_RESULT.json`.
