# PMBOT Runtime Credential Visibility Runbook 077C

This runbook diagnoses whether the PowerShell process that starts PMBOT can see the same credential environment variables as the operator expects. It never prints raw secrets, does not collect secrets in Telegram, and does not enable live trading.

## Safe Diagnostic Command

Run this from the same PowerShell window that will run Telegram or local readiness checks:

```powershell
python -m pm_bot.operator_runner.runtime_credential_visibility_diagnostic --market BTC --strategy tiny-momentum --dry-run
```

The output records `present`, `length`, and a short redacted fingerprint. It does not print raw private keys, API secrets, passphrases, Telegram tokens, wallet addresses, or signed payloads.

The committed sample artifacts are written under:

```text
pm_bot/trading_core/artifacts/runtime_credential_visibility_077c/
```

## PowerShell Redacted Env Check

Use this only in the local shell. It prints presence, length, and a short fingerprint, never the value.

```powershell
function Get-RedactedEnvStatus {
  param([string[]]$Names)

  foreach ($Name in $Names) {
    $Value = [Environment]::GetEnvironmentVariable($Name, "Process")
    if ([string]::IsNullOrWhiteSpace($Value)) {
      "$Name present=false length=0 fingerprint=missing"
      continue
    }

    $Payload = "$Name`0$($Value.Length)`0$Value"
    $Bytes = [System.Text.Encoding]::UTF8.GetBytes($Payload)
    $Sha = [System.Security.Cryptography.SHA256]::Create()
    $Hash = ([System.BitConverter]::ToString($Sha.ComputeHash($Bytes)) -replace "-", "").ToLowerInvariant().Substring(0, 12)
    "$Name present=true length=$($Value.Length) fingerprint=sha256:$Hash"
  }
}

Get-RedactedEnvStatus @(
  "POLYMARKET_API_KEY",
  "POLYMARKET_API_SECRET",
  "POLYMARKET_API_PASSPHRASE",
  "POLYMARKET_PRIVATE_KEY",
  "POLYMARKET_WALLET_ADDRESS",
  "POLYMARKET_SIGNATURE_TYPE",
  "POLYMARKET_FUNDER_ADDRESS",
  "TELEGRAM_BOT_TOKEN",
  "TELEGRAM_ALLOWED_OPERATOR_IDS",
  "PMBOT_TELEGRAM_BOT_TOKEN",
  "PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS"
)
```

## Telegram Runtime Shell

The current repo Telegram runtime reads the `PMBOT_` names:

```text
PMBOT_TELEGRAM_BOT_TOKEN
PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS
```

Start Telegram from the same PowerShell window after verifying those variables are present:

```powershell
python -m pm_bot.operator_runner.telegram_runtime_smoke
python -m pm_bot.operator_runner.telegram_operator_runtime
```

Do not paste Polymarket secrets, private keys, Telegram tokens, or operator IDs into Telegram chat. Telegram is an operator control surface, not a secret collection channel.

## Windows User-Level Variables

Set user-level variables from a local PowerShell session only. Replace placeholders locally and do not paste real values into docs, Git, Telegram, or issue comments.

```powershell
[Environment]::SetEnvironmentVariable("POLYMARKET_API_KEY", "<paste-api-key-locally>", "User")
[Environment]::SetEnvironmentVariable("POLYMARKET_API_SECRET", "<paste-api-secret-locally>", "User")
[Environment]::SetEnvironmentVariable("POLYMARKET_API_PASSPHRASE", "<paste-api-passphrase-locally>", "User")
[Environment]::SetEnvironmentVariable("POLYMARKET_PRIVATE_KEY", "<paste-private-key-locally>", "User")
[Environment]::SetEnvironmentVariable("POLYMARKET_WALLET_ADDRESS", "<paste-wallet-address-locally>", "User")
[Environment]::SetEnvironmentVariable("POLYMARKET_SIGNATURE_TYPE", "<paste-signature-type-locally>", "User")
[Environment]::SetEnvironmentVariable("POLYMARKET_FUNDER_ADDRESS", "<paste-funder-address-locally>", "User")
[Environment]::SetEnvironmentVariable("PMBOT_TELEGRAM_BOT_TOKEN", "<paste-telegram-token-locally>", "User")
[Environment]::SetEnvironmentVariable("PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS", "<paste-operator-ids-locally>", "User")
```

Open a new PowerShell window after setting user-level variables. Windows does not reliably update already-open shells.

If you must update the current shell from user-level variables without printing them:

```powershell
$Names = @(
  "POLYMARKET_API_KEY",
  "POLYMARKET_API_SECRET",
  "POLYMARKET_API_PASSPHRASE",
  "POLYMARKET_PRIVATE_KEY",
  "POLYMARKET_WALLET_ADDRESS",
  "POLYMARKET_SIGNATURE_TYPE",
  "POLYMARKET_FUNDER_ADDRESS",
  "PMBOT_TELEGRAM_BOT_TOKEN",
  "PMBOT_TELEGRAM_ALLOWED_OPERATOR_IDS"
)

foreach ($Name in $Names) {
  $Value = [Environment]::GetEnvironmentVariable($Name, "User")
  if (-not [string]::IsNullOrWhiteSpace($Value)) {
    Set-Item -Path "Env:$Name" -Value $Value
  }
}
```

Then rerun the 077C diagnostic.

## Local `.env` Loader

At this revision, the PMBOT operator runners do not provide a supported `.env` loader for these credentials. The 077C diagnostic and Telegram runtime read process environment variables only. Do not assume `.env` files are loaded automatically.

If a future separately approved task adds a repo-supported `.env` loader, use it only in the same PowerShell process before the Python command, keep `.env` out of Git, and rerun the 077C diagnostic immediately after loading. This task does not add or read `.env` files.

## Rerun Signer Diagnostics

After the 077C diagnostic shows `POLYMARKET_PRIVATE_KEY` and wallet context are visible, rerun the signer evidence bridge:

```powershell
python -m pm_bot.operator_runner.signer_diagnostic_evidence_bridge --market BTC --strategy tiny-momentum --dry-run
```

If the guarded signer smoke must be rerun, it requires the explicit diagnostic flag and still does not submit, cancel, or create order payloads:

```powershell
python -m pm_bot.operator_runner.guarded_signer_diagnostic_smoke --market BTC --strategy tiny-momentum --dry-run --allow-private-key-diagnostic
python -m pm_bot.operator_runner.signer_diagnostic_evidence_bridge --market BTC --strategy tiny-momentum --dry-run
```

## Expected Safe Commands

```powershell
python -m pm_bot.operator_runner.runtime_credential_visibility_diagnostic --market BTC --strategy tiny-momentum --dry-run
python -m pm_bot.operator_runner.signer_diagnostic_evidence_bridge --market BTC --strategy tiny-momentum --dry-run
python -m pm_bot.operator_runner.first_supervised_tiny_order_readiness_packet --market BTC --strategy tiny-momentum --dry-run
python -m pm_bot.operator_runner.static_safety_invariant_report --scope pm_bot --dry-run
python -m pm_bot.operator_runner.telegram_runtime_smoke
python -m pm_bot.operator_runner.telegram_operator_runtime
```

Expected 077C statuses:

- `runtime_credentials_visible`: all blocking credential groups are visible in the current process.
- `blocked_missing_private_key`: `POLYMARKET_PRIVATE_KEY` is not visible.
- `blocked_missing_polymarket_l2_credentials`: one or more L2 credentials are not visible.
- `blocked_missing_wallet_address`: wallet address, signature type, or funder address context is not visible.
- `blocked_missing_telegram_credentials`: neither the prompt Telegram aliases nor the PMBOT runtime aliases are complete.

All statuses remain no-live. They do not authorize real orders, order cancellation, signing by default, wallet connection, or authenticated trading calls.
