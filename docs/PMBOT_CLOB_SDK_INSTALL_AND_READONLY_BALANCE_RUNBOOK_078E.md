# PMBOT CLOB SDK Install And Read-Only Balance Runbook 078E

This runbook explains how an operator can install and verify the Polymarket CLOB Python SDK for the PMBOT read-only balance path. It does not install packages automatically, does not modify the user environment by itself, and does not enable live trading.

The PMBOT balance path remains no-live: no order submission, no order cancellation, no signing by default, no signer instantiation, no wallet-connect UI, no fake balances, and no raw secrets in terminal output or artifacts.

## 1. Check The Python That Will Run PMBOT

Run these commands in the same PowerShell window that will run the PMBOT probe:

```powershell
where python
python --version
python -m pip --version
```

`where python` may print more than one path. The first path is usually the interpreter that `python` will run. `python -m pip --version` should show a `pip` path that belongs to the same Python installation.

## 2. Check Installed SDK Packages

Run both package checks. A missing package is expected before installation and is not an error by itself.

```powershell
python -m pip show py-clob-client
python -m pip show py-clob-client-v2
```

Do not paste API keys, API secrets, passphrases, private keys, wallet addresses, Telegram tokens, or `.env` contents into terminal output shared with anyone. These commands do not require secrets.

## 3. Install The Supported SDK

Install into the same Python reported above:

```powershell
python -m pip install py-clob-client
```

This task does not run that command automatically. The operator chooses whether to run it.

Optional v2 note: only install v2 if a separate operator decision requires testing that package in this same no-live read-only path:

```powershell
python -m pip install py-clob-client-v2
```

The expected primary package remains `py-clob-client`, with the import path `py_clob_client.client`.

## 4. Verify Imports Without Printing Secrets

Run this PowerShell here-string in the same shell. It imports candidate modules and prints only import status, module names, and the current Python executable.

```powershell
@'
import importlib
import sys

modules = (
    "py_clob_client",
    "py_clob_client.client",
    "py_clob_client_v2",
)

print(f"python_executable={sys.executable}")
for module_name in modules:
    try:
        importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        status = "missing" if exc.name == module_name or module_name.startswith(f"{exc.name}.") else "dependency_missing"
        print(f"{module_name}={status}")
    except Exception as exc:
        print(f"{module_name}=import_error:{type(exc).__name__}:message_redacted")
    else:
        print(f"{module_name}=installed")
'@ | python -
```

The output must not include raw SDK responses, balances, allowances, API credentials, private keys, or wallet secrets.

## 5. Avoid Installing Into The Wrong Python

- Use `python -m pip ...`, not a standalone `pip ...` command.
- Run all commands from the same PowerShell window or the same activated virtual environment.
- If `where python` shows multiple interpreters, compare the first `where python` path with `python -m pip --version`.
- If the wrong interpreter is first, activate the intended virtual environment or run the full interpreter path explicitly, for example: `C:\Path\To\Python\python.exe -m pip install py-clob-client`.
- After installation, rerun `python -m pip show py-clob-client` and the import verification here-string using the same `python`.

## 6. Rerun The Read-Only Balance Probe

After the SDK is visible in the intended Python and the operator has separately configured the required PMBOT environment, rerun the no-live read-only probe:

```powershell
python -m pm_bot.operator_runner.live_account_readonly_state_probe --market BTC --strategy tiny-momentum --dry-run
```

Expected safety properties:

- `--dry-run` is required.
- `allowed_for_live` remains `false`.
- `trading_requested` remains `false`.
- no submit/cancel/write endpoint is enabled.
- no signer is instantiated by default.
- no wallet connect UI is used.
- no private key, API secret, passphrase, raw balance, raw allowance, or raw SDK response is printed.

If the Telegram Balance screen says the SDK is missing, install and verify in the exact Python used to run the PMBOT process, then rerun the probe above.
