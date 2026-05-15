from __future__ import annotations

import inspect
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping

from pm_bot.trading_core.live_account_readonly_state_probe import (
    LiveAccountSdkBinding,
    live_account_readonly_state_probe_artifact_paths,
    run_live_account_readonly_state_probe,
)
import pm_bot.trading_core.live_account_readonly_state_probe as probe_module
from pm_bot.trading_core.live_account_readonly_state_models import (
    FORCED_FALSE_EXECUTION_FIELDS,
    POLYMARKET_API_KEY_ENV,
    POLYMARKET_API_PASSPHRASE_ENV,
    POLYMARKET_API_SECRET_ENV,
    POLYMARKET_FUNDER_ADDRESS_ENV,
    POLYMARKET_SIGNATURE_TYPE_ENV,
    POLYMARKET_WALLET_ADDRESS_ENV,
)

GENERATED_AT = "2026-05-15T00:00:00+04:00"

FAKE_API_KEY = "fake-api-key-070c-redact-me"
FAKE_API_SECRET = "fake-api-secret-070c-redact-me"
FAKE_API_PASSPHRASE = "fake-api-passphrase-070c-redact-me"
FAKE_PRIVATE_KEY = "fake-private-key-070c-must-not-read"
FAKE_WALLET = "0x3006000000000000000000000000000000008989"
FAKE_FUNDER = "0x1111000000000000000000000000000000005555"
FAKE_BALANCE_VALUE = "fake-balance-value-070c-redact-me"
FAKE_ALLOWANCE_VALUE = "fake-allowance-value-070c-redact-me"


class GuardedEnviron(Mapping[str, str]):
    def __init__(self, values: Mapping[str, str]) -> None:
        self.values = dict(values)
        self.get_calls: list[str] = []
        self.forbidden_reads: list[str] = []

    def __contains__(self, key: object) -> bool:
        text = str(key)
        if _is_forbidden_env_read(text):
            self.forbidden_reads.append(text)
            raise AssertionError(f"forbidden env membership read: {text}")
        return text in self.values

    def __getitem__(self, key: str) -> str:
        if _is_forbidden_env_read(key):
            self.forbidden_reads.append(key)
            raise AssertionError(f"forbidden env value read: {key}")
        return self.values[key]

    def __iter__(self) -> Iterator[str]:
        raise AssertionError("environment iteration attempted")

    def __len__(self) -> int:
        raise AssertionError("environment length read attempted")

    def get(self, key: str, default: Any = None) -> str:
        if _is_forbidden_env_read(key):
            self.forbidden_reads.append(key)
            raise AssertionError(f"forbidden env get attempted: {key}")
        self.get_calls.append(key)
        return self.values.get(key, default)

    def items(self):  # type: ignore[no-untyped-def]
        raise AssertionError("environment items read attempted")

    def values(self):  # type: ignore[no-untyped-def]
        raise AssertionError("environment values read attempted")


@dataclass
class FakeApiCreds:
    api_key: str
    api_secret: str
    api_passphrase: str


class FakeOpenOrderParams:
    pass


class FakeAssetType:
    COLLATERAL = "COLLATERAL"


@dataclass
class FakeBalanceAllowanceParams:
    asset_type: str | None = None


class FakeReadOnlyClient:
    mode = 2

    def __init__(self, *, host: str, chain_id: int, creds: FakeApiCreds) -> None:
        self.host = host
        self.chain_id = chain_id
        self.creds = creds
        self.called_methods: list[str] = []

    def get_orders(self, params: FakeOpenOrderParams | None = None) -> list[dict[str, Any]]:
        self.called_methods.append("get_orders")
        return [{"id": "raw-order-row-redacted"}, {"id": "raw-order-row-redacted-2"}]

    def get_balance_allowance(self, params: FakeBalanceAllowanceParams | None = None) -> dict[str, str]:
        self.called_methods.append("get_balance_allowance")
        return {"balance": FAKE_BALANCE_VALUE, "allowance": FAKE_ALLOWANCE_VALUE}


class FakeMissingMethodsClient:
    mode = 2

    def __init__(self, *, host: str, chain_id: int, creds: FakeApiCreds) -> None:
        self.host = host
        self.chain_id = chain_id
        self.creds = creds


class FakeSignerRequiredClient(FakeReadOnlyClient):
    mode = 0
    signer = None


def _is_forbidden_env_read(key: str) -> bool:
    return key in {
        "POLYMARKET_PRIVATE_KEY",
        "POLYMARKET_WALLET_PRIVATE_KEY",
        "PMBOT_POLYMARKET_PRIVATE_KEY",
        "PRIVATE_KEY",
        "MNEMONIC",
        "SEED_PHRASE",
    }


def _env_with_l2_creds(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    env = {
        POLYMARKET_API_KEY_ENV: FAKE_API_KEY,
        POLYMARKET_API_SECRET_ENV: FAKE_API_SECRET,
        POLYMARKET_API_PASSPHRASE_ENV: FAKE_API_PASSPHRASE,
    }
    env.update(dict(extra or {}))
    return env


def _env_with_account_config(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    env = _env_with_l2_creds(
        {
            POLYMARKET_WALLET_ADDRESS_ENV: FAKE_WALLET,
            POLYMARKET_SIGNATURE_TYPE_ENV: "3",
            POLYMARKET_FUNDER_ADDRESS_ENV: FAKE_FUNDER,
        }
    )
    env.update(dict(extra or {}))
    return env


def _minimal_subprocess_env(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    env = {
        "PYTHONPATH": str(Path.cwd()),
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
        "COMSPEC": os.environ.get("COMSPEC", ""),
        "PATH": os.environ.get("PATH", ""),
    }
    env.update(dict(extra or {}))
    return env


def _dependency_missing_loader() -> LiveAccountSdkBinding:
    return LiveAccountSdkBinding(
        status="dependency_missing",
        attempted_modules=("py_clob_client_v2", "py_clob_client"),
        error_type="ImportError",
        error_message_sanitized="not importable",
    )


def _fake_readonly_loader() -> LiveAccountSdkBinding:
    return LiveAccountSdkBinding(
        status="available",
        module_name="fake_readonly_sdk",
        attempted_modules=("fake_readonly_sdk",),
        client_class=FakeReadOnlyClient,
        creds_class=FakeApiCreds,
        open_order_params_class=FakeOpenOrderParams,
        balance_allowance_params_class=FakeBalanceAllowanceParams,
        asset_type_class=FakeAssetType,
    )


def _fake_missing_methods_loader() -> LiveAccountSdkBinding:
    return LiveAccountSdkBinding(
        status="available",
        module_name="fake_missing_methods_sdk",
        attempted_modules=("fake_missing_methods_sdk",),
        client_class=FakeMissingMethodsClient,
        creds_class=FakeApiCreds,
    )


def _fake_signer_required_loader() -> LiveAccountSdkBinding:
    return LiveAccountSdkBinding(
        status="available",
        module_name="fake_signer_required_sdk",
        attempted_modules=("fake_signer_required_sdk",),
        client_class=FakeSignerRequiredClient,
        creds_class=FakeApiCreds,
        open_order_params_class=FakeOpenOrderParams,
        balance_allowance_params_class=FakeBalanceAllowanceParams,
        asset_type_class=FakeAssetType,
    )


def _artifact_text(paths: Mapping[str, Path]) -> str:
    chunks = []
    for key, path in paths.items():
        if key != "root" and Path(path).exists():
            chunks.append(Path(path).read_text(encoding="utf-8"))
    return "\n".join(chunks)


def _assert_forced_false_flags(value: Mapping[str, Any]) -> None:
    assert value["probe_is_readonly"] is True
    assert value["allowed_for_live"] is False
    for field in FORCED_FALSE_EXECUTION_FIELDS:
        assert value[field] is False, field
    assert value["resolved_blocker_count"] == 0


def test_private_key_env_is_not_read_and_account_config_is_redacted(tmp_path: Path) -> None:
    env = GuardedEnviron(
        _env_with_account_config(
            {
                "POLYMARKET_PRIVATE_KEY": FAKE_PRIVATE_KEY,
                "POLYMARKET_WALLET_PRIVATE_KEY": FAKE_PRIVATE_KEY,
            }
        )
    )

    result = run_live_account_readonly_state_probe(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        environ=env,
        sdk_loader=_dependency_missing_loader,
        generated_at=GENERATED_AT,
    )

    assert set(env.get_calls) == {
        POLYMARKET_API_KEY_ENV,
        POLYMARKET_API_SECRET_ENV,
        POLYMARKET_API_PASSPHRASE_ENV,
        POLYMARKET_WALLET_ADDRESS_ENV,
        POLYMARKET_SIGNATURE_TYPE_ENV,
        POLYMARKET_FUNDER_ADDRESS_ENV,
    }
    assert env.forbidden_reads == []
    assert result["private_key_read"] is False
    assert result["wallet_connection_attempted"] is False
    assert result["account_status"]["wallet_address_redacted"] == "0x3006...8989"
    assert result["account_status"]["signature_type_redacted"] == "3"
    assert result["account_status"]["funder_address_redacted"] == "0x1111...5555"
    assert result["status"] == "blocked_sdk_unavailable"


def test_missing_l2_credentials_blocks_without_sdk_probe(tmp_path: Path) -> None:
    result = run_live_account_readonly_state_probe(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        environ={POLYMARKET_WALLET_ADDRESS_ENV: FAKE_WALLET},
        sdk_loader=_fake_readonly_loader,
        generated_at=GENERATED_AT,
    )

    assert result["status"] == "blocked_missing_l2_credentials"
    assert result["credential_presence"]["missing_l2_count"] == 3
    assert result["account_state_probe_attempted"] is False
    assert result["account_state_probe_performed"] is False
    _assert_forced_false_flags(result)


def test_sdk_unavailable_fails_closed_without_fake_account_state(tmp_path: Path) -> None:
    result = run_live_account_readonly_state_probe(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        environ=_env_with_account_config(),
        sdk_loader=_dependency_missing_loader,
        generated_at=GENERATED_AT,
    )

    assert result["status"] == "blocked_sdk_unavailable"
    assert result["sdk_status"]["sdk_available"] is False
    assert result["open_order_count"] is None
    assert result["open_orders_status"] == "not_available"
    assert result["balance_allowance_status"] == "not_available"
    assert result["account_state_probe_performed"] is False
    _assert_forced_false_flags(result)


def test_method_unavailable_does_not_fake_data(tmp_path: Path) -> None:
    result = run_live_account_readonly_state_probe(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        environ=_env_with_l2_creds(),
        sdk_loader=_fake_missing_methods_loader,
        generated_at=GENERATED_AT,
    )
    attempts = result["diagnostics"]["probe_attempts"]

    assert result["status"] == "blocked_method_unavailable"
    assert result["open_order_count"] is None
    assert result["open_orders_status"] == "method_unavailable"
    assert result["balance_allowance_status"] == "method_unavailable"
    assert result["account_state_probe_performed"] is False
    assert {row["sdk_method"]: row["method_available"] for row in attempts} == {
        "get_orders": False,
        "get_balance_allowance": False,
    }


def test_sdk_that_requires_signer_fails_closed_without_private_key(tmp_path: Path) -> None:
    result = run_live_account_readonly_state_probe(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        environ=_env_with_account_config({"POLYMARKET_PRIVATE_KEY": FAKE_PRIVATE_KEY}),
        sdk_loader=_fake_signer_required_loader,
        generated_at=GENERATED_AT,
    )

    assert result["status"] == "blocked_sdk_requires_signer_without_private_key"
    assert result["sdk_status"]["sdk_requires_signer_without_private_key"] is True
    assert result["account_state_probe_performed"] is False
    assert result["private_key_read"] is False
    assert result["signer_instantiated"] is False


def test_successful_fake_sdk_probe_redacts_artifacts_and_keeps_live_disabled(tmp_path: Path) -> None:
    result = run_live_account_readonly_state_probe(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        environ=_env_with_account_config({"POLYMARKET_PRIVATE_KEY": FAKE_PRIVATE_KEY}),
        sdk_loader=_fake_readonly_loader,
        generated_at=GENERATED_AT,
    )
    artifact_text = _artifact_text(live_account_readonly_state_probe_artifact_paths(tmp_path))
    rendered = json.dumps(result, sort_keys=True)

    assert result["status"] == "account_state_probe_succeeded_live_blocked"
    assert result["probe_is_readonly"] is True
    assert result["allowed_for_live"] is False
    assert result["open_order_count"] == 2
    assert result["balance_allowance_status"] == "succeeded_redacted"
    assert result["balance_allowance_availability_status"] == "available_redacted:balance,allowance"
    assert result["account_state_probe_attempted"] is True
    assert result["account_state_probe_performed"] is True
    for raw in (
        FAKE_API_KEY,
        FAKE_API_SECRET,
        FAKE_API_PASSPHRASE,
        FAKE_PRIVATE_KEY,
        FAKE_WALLET,
        FAKE_FUNDER,
        FAKE_BALANCE_VALUE,
        FAKE_ALLOWANCE_VALUE,
    ):
        assert raw not in artifact_text
        assert raw not in rendered
    assert "0x3006...8989" in rendered
    assert "0x1111...5555" in rendered
    _assert_forced_false_flags(result)


def test_no_order_submit_cancel_signing_wallet_or_write_call_path_in_probe_source() -> None:
    source = inspect.getsource(probe_module).lower()
    forbidden_call_patterns = (
        r"\bcreate_order\s*\(",
        r"\bpost_order\s*\(",
        r"\bsubmit_order\s*\(",
        r"\bplace_order\s*\(",
        r"\bsend_order\s*\(",
        r"\bcancel_order\s*\(",
        r"\bcancel_all\s*\(",
        r"\bderive_api_key\s*\(",
        r"\bcreate_api_key\s*\(",
        r"\bsign_order\s*\(",
        r"\bsign_payload\s*\(",
        r"\bsign\s*\(",
        r"\bconnect_wallet\s*\(",
        r"\.post\s*\(",
        r"\.put\s*\(",
        r"\.patch\s*\(",
        r"\.delete\s*\(",
        r"requests\.",
        r"httpx\.",
        r"account\.from_key",
        r"eth_account",
        r"web3",
    )
    for pattern in forbidden_call_patterns:
        assert re.search(pattern, source) is None, pattern


def test_no_post_put_patch_delete_trading_calls_are_recorded(tmp_path: Path) -> None:
    result = run_live_account_readonly_state_probe(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        environ=_env_with_l2_creds(),
        sdk_loader=_fake_readonly_loader,
        generated_at=GENERATED_AT,
    )
    attempts = result["diagnostics"]["probe_attempts"]

    assert attempts
    assert all(row["request_method"] == "GET" for row in attempts)
    assert all(row["request_method_allowed"] is True for row in attempts)
    assert all(row["blocked_http_methods"] == ["POST", "PUT", "PATCH", "DELETE"] for row in attempts)
    assert result["post_put_patch_delete_attempted"] is False
    assert result["trading_endpoint_write_attempted"] is False


def test_runner_works_in_dry_run_and_does_not_print_secrets(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pm_bot.operator_runner.live_account_readonly_state_probe",
            "--market",
            "BTC",
            "--strategy",
            "tiny-momentum",
            "--dry-run",
            "--artifacts-dir",
            str(tmp_path),
        ],
        cwd=Path.cwd(),
        env=_minimal_subprocess_env(
            _env_with_account_config({"POLYMARKET_PRIVATE_KEY": FAKE_PRIVATE_KEY})
        ),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    artifacts = _artifact_text(live_account_readonly_state_probe_artifact_paths(tmp_path))

    assert completed.returncode == 0, completed.stderr
    assert "Live account read-only state probe completed." in completed.stdout
    assert "Probe read-only: true" in completed.stdout
    assert "Allowed for live: false" in completed.stdout
    assert "Private key read: false" in completed.stdout
    for raw in (FAKE_API_KEY, FAKE_API_SECRET, FAKE_API_PASSPHRASE, FAKE_PRIVATE_KEY, FAKE_WALLET, FAKE_FUNDER):
        assert raw not in completed.stdout
        assert raw not in completed.stderr
        assert raw not in artifacts
