# Fake Codex app-server

This fixture simulates the process boundary used by the app-server dry-run tests.

Modes:

- `success` starts, accepts newline-delimited JSON on stdin, and emits a JSON response with the same `id`.
- `startup_failure` exits immediately with a non-zero code.
- `invalid_json` emits invalid JSON after receiving input.
- `hangs_until_timeout` stays alive until the test dry-run terminates it.

The fixture does not call network services, access credentials, start workers, or run Codex.
