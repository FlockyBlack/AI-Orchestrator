from __future__ import annotations

import sys
from types import ModuleType
from typing import Any, Mapping

import pytest

import pm_bot.trading_core.live_account_readonly_state_probe as probe_module
from pm_bot.trading_core.live_account_readonly_state_models import (
    CLOB_SDK_IMPORT_CANDIDATES,
    EXPECTED_SDK_INSTALL_COMMAND,
    EXPECTED_SDK_MODULE,
)
from pm_bot.trading_core.live_account_readonly_state_probe import run_live_account_readonly_state_probe

GENERATED_AT = "2026-05-17T00:00:00+04:00"


class FakeApiCreds:
    def __init__(self, api_key: str, api_secret: str, api_passphrase: str) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase


class FakeOpenOrderParams:
    pass


class FakeAssetType:
    COLLATERAL = "COLLATERAL"


class FakeBalanceAllowanceParams:
    def __init__(self, asset_type: str | None = None) -> None:
        self.asset_type = asset_type


class FakeReadOnlyClient:
    mode = 2

    def __init__(self, *, host: str, chain_id: int, creds: FakeApiCreds) -> None:
        self.host = host
        self.chain_id = chain_id
        self.creds = creds

    def get_orders(self, params: FakeOpenOrderParams | None = None) -> list[dict[str, Any]]:
        return []

    def get_balance_allowance(self, params: FakeBalanceAllowanceParams | None = None) -> dict[str, Any]:
        return {}


def _env() -> dict[str, str]:
    return {
        "POLYMARKET_API_KEY": "fake-api-key-078c-never-output",
        "POLYMARKET_API_SECRET": "fake-api-secret-078c-never-output",
        "POLYMARKET_API_PASSPHRASE": "fake-passphrase-078c-never-output",
        "POLYMARKET_WALLET_ADDRESS": "0x300600000000000000000000000000000000078c",
        "POLYMARKET_SIGNATURE_TYPE": "2",
        "POLYMARKET_FUNDER_ADDRESS": "0x111100000000000000000000000000000000078c",
    }


def _module(name: str, **attrs: Any) -> ModuleType:
    module = ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    return module


def _install_fake_imports(
    monkeypatch: pytest.MonkeyPatch,
    modules: Mapping[str, ModuleType],
    versions: Mapping[str, str] | None = None,
) -> None:
    def import_module(name: str) -> ModuleType:
        if name in modules:
            return modules[name]
        raise ModuleNotFoundError(f"No module named {name}", name=name)

    def version(package_name: str) -> str:
        package_versions = dict(versions or {})
        if package_name in package_versions:
            return package_versions[package_name]
        raise probe_module.importlib_metadata.PackageNotFoundError(package_name)

    monkeypatch.setattr(probe_module.importlib, "import_module", import_module)
    monkeypatch.setattr(probe_module.importlib_metadata, "version", version)


def _run_probe(tmp_path: Any) -> dict[str, Any]:
    return run_live_account_readonly_state_probe(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        environ=_env(),
        generated_at=GENERATED_AT,
    )


def test_sdk_missing_reports_all_candidates_install_guidance_and_python(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
) -> None:
    _install_fake_imports(monkeypatch, {})

    result = _run_probe(tmp_path)
    sdk_status = result["sdk_status"]

    assert result["status"] == "blocked_sdk_unavailable"
    assert sdk_status["sdk_available"] is False
    assert sdk_status["selected_sdk_module"] == ""
    assert sdk_status["attempted_sdk_modules"] == list(CLOB_SDK_IMPORT_CANDIDATES)
    assert [row["module_name"] for row in sdk_status["sdk_import_reports"]] == list(CLOB_SDK_IMPORT_CANDIDATES)
    assert {row["import_status"] for row in sdk_status["sdk_import_reports"]} == {"missing"}
    assert all(row["installed"] is False for row in sdk_status["sdk_import_reports"])
    assert sdk_status["expected_sdk_module"] == EXPECTED_SDK_MODULE
    assert sdk_status["expected_install_command"] == EXPECTED_SDK_INSTALL_COMMAND
    assert sdk_status["python_executable"] == sys.executable
    assert sdk_status["pip_package_visibility"]
    assert all(row["visible"] is False for row in sdk_status["pip_package_visibility"])


def test_sdk_present_v1_selects_py_clob_client_client(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
) -> None:
    modules = {
        "py_clob_client": _module("py_clob_client"),
        "py_clob_client.client": _module("py_clob_client.client", ClobClient=FakeReadOnlyClient),
        "py_clob_client.clob_types": _module(
            "py_clob_client.clob_types",
            ApiCreds=FakeApiCreds,
            OpenOrderParams=FakeOpenOrderParams,
            BalanceAllowanceParams=FakeBalanceAllowanceParams,
            AssetType=FakeAssetType,
        ),
    }
    _install_fake_imports(monkeypatch, modules, {"py-clob-client": "1.2.3"})

    result = _run_probe(tmp_path)
    sdk_status = result["sdk_status"]

    assert result["status"] == "account_state_probe_succeeded_live_blocked"
    assert sdk_status["selected_sdk_module"] == "py_clob_client.client"
    assert sdk_status["client_class_available"] is True
    assert sdk_status["api_creds_class_available"] is True
    assert sdk_status["open_orders_method_available"] is True
    assert sdk_status["balance_allowance_method_available"] is True
    assert any(
        row["module_name"] == "py_clob_client.client" and row["selected"] is True
        for row in sdk_status["sdk_import_reports"]
    )
    assert any(
        row["package_name"] == "py-clob-client" and row["visible"] is True and row["version"] == "1.2.3"
        for row in sdk_status["pip_package_visibility"]
    )


def test_sdk_present_v2_selects_py_clob_client_v2(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
) -> None:
    modules = {
        "py_clob_client_v2": _module(
            "py_clob_client_v2",
            ClobClient=FakeReadOnlyClient,
            ApiCreds=FakeApiCreds,
            OpenOrderParams=FakeOpenOrderParams,
            BalanceAllowanceParams=FakeBalanceAllowanceParams,
            AssetType=FakeAssetType,
        ),
    }
    _install_fake_imports(monkeypatch, modules, {"py-clob-client-v2": "2.0.0"})

    result = _run_probe(tmp_path)
    sdk_status = result["sdk_status"]

    assert result["status"] == "account_state_probe_succeeded_live_blocked"
    assert sdk_status["selected_sdk_module"] == "py_clob_client_v2"
    assert any(
        row["module_name"] == "py_clob_client_v2" and row["import_status"] == "installed"
        for row in sdk_status["sdk_import_reports"]
    )
    assert any(
        row["package_name"] == "py-clob-client-v2" and row["visible"] is True and row["version"] == "2.0.0"
        for row in sdk_status["pip_package_visibility"]
    )


def test_sdk_import_error_reports_type_without_raw_error_message(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
) -> None:
    raw_import_error = "raw-secret-value-078c"

    def import_module(name: str) -> ModuleType:
        if name == "py_clob_client":
            raise RuntimeError(raw_import_error)
        raise ModuleNotFoundError(f"No module named {name}", name=name)

    monkeypatch.setattr(probe_module.importlib, "import_module", import_module)
    monkeypatch.setattr(
        probe_module.importlib_metadata,
        "version",
        lambda package_name: (_ for _ in ()).throw(
            probe_module.importlib_metadata.PackageNotFoundError(package_name)
        ),
    )

    result = _run_probe(tmp_path)
    rendered = str(result)
    py_clob_client_report = next(
        row for row in result["sdk_status"]["sdk_import_reports"] if row["module_name"] == "py_clob_client"
    )

    assert result["status"] == "blocked_sdk_unavailable"
    assert py_clob_client_report["import_status"] == "import_error"
    assert py_clob_client_report["import_error_type"] == "RuntimeError"
    assert raw_import_error not in rendered


def test_no_fake_balances_are_emitted_when_sdk_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
) -> None:
    _install_fake_imports(monkeypatch, {})

    result = _run_probe(tmp_path)

    assert result["open_order_count"] is None
    assert result["open_orders_status"] == "not_available"
    assert result["balance_allowance_status"] == "not_available"
    assert result["account_state_probe_performed"] is False
    assert result["balance_values_emitted"] is False
    assert result["fake_balances_emitted"] is False


def test_missing_l2_credentials_still_reports_sdk_detection(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Any,
) -> None:
    _install_fake_imports(monkeypatch, {})

    result = run_live_account_readonly_state_probe(
        market="BTC",
        strategy="tiny-momentum",
        dry_run=True,
        artifact_dir=tmp_path,
        environ={"POLYMARKET_WALLET_ADDRESS": "0x300600000000000000000000000000000000078c"},
        generated_at=GENERATED_AT,
    )

    assert result["status"] == "blocked_missing_l2_credentials"
    assert result["sdk_status"]["status"] == "dependency_missing"
    assert result["sdk_status"]["expected_install_command"] == EXPECTED_SDK_INSTALL_COMMAND
    assert result["sdk_status"]["python_executable"] == sys.executable
    assert result["account_state_probe_performed"] is False
