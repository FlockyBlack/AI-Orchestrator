from __future__ import annotations

from pathlib import Path

from ai_orchestrator.symphony_adapter.codex_app_server_protocol import (
    build_minimal_initialize_request,
    describe_protocol_capabilities,
    find_initialize_request_schema,
    validate_client_request_against_schema,
    validate_server_message_against_schema,
)
from test_codex_app_server_protocol_index import _write_schema_dir


def test_schema_probe_finds_client_request_and_server_notification(tmp_path: Path) -> None:
    schema_dir = _write_schema_dir(tmp_path)

    capabilities = describe_protocol_capabilities(schema_dir)

    assert capabilities["schema_index_valid"] is True
    assert "initialize" in capabilities["client_requests"]
    assert "turn/completed" in capabilities["server_notifications"]
    assert capabilities["app_server_started"] is False
    assert capabilities["network_used"] is False


def test_minimal_initialize_request_builds_and_validates(tmp_path: Path) -> None:
    schema_dir = _write_schema_dir(tmp_path)

    schema = find_initialize_request_schema(schema_dir)
    request = build_minimal_initialize_request(schema_dir)
    validation = validate_client_request_against_schema(request, schema_dir)

    assert schema["available"] is True
    assert request is not None
    assert request["method"] == "initialize"
    assert validation["valid"] is True


def test_server_message_validator_accepts_jsonrpc_response(tmp_path: Path) -> None:
    schema_dir = _write_schema_dir(tmp_path)

    validation = validate_server_message_against_schema({"id": "1", "result": {"ok": True}}, schema_dir)

    assert validation["valid"] is True


def test_minimal_initialize_request_reports_unavailable(tmp_path: Path) -> None:
    schema_dir = tmp_path / "schema"
    schema_dir.mkdir()
    (schema_dir / "ClientRequest.json").write_text('{"oneOf":[]}', encoding="utf-8")
    (schema_dir / "ServerRequest.json").write_text('{"oneOf":[]}', encoding="utf-8")
    (schema_dir / "ServerNotification.json").write_text('{"oneOf":[]}', encoding="utf-8")
    (schema_dir / "codex_app_server_protocol.v2.schemas.json").write_text("{}", encoding="utf-8")

    capabilities = describe_protocol_capabilities(schema_dir)

    assert capabilities["minimal_initialize_request_available"] is False
    assert any("initialize" in error for error in capabilities["errors"])
