from __future__ import annotations

import json
from pathlib import Path

from ai_orchestrator.symphony_adapter.codex_app_server_protocol import (
    inspect_schema_dir,
    list_approval_message_types,
    list_client_requests,
    list_server_notifications,
    list_session_message_types,
    load_protocol_schema,
)


def test_schema_dir_inspection_indexes_protocol_messages(tmp_path: Path) -> None:
    schema_dir = _write_schema_dir(tmp_path)

    index = inspect_schema_dir(schema_dir)

    assert not index.errors
    assert "ClientRequest.json" in index.client_request_path
    assert "initialize" in index.client_requests
    assert "thread/start" in index.session_message_types
    assert "item/commandExecution/requestApproval" in index.approval_message_types
    assert "turn/completed" in index.server_notifications


def test_protocol_helpers_list_expected_messages(tmp_path: Path) -> None:
    schema_dir = _write_schema_dir(tmp_path)

    assert "turn/start" in list_client_requests(schema_dir)
    assert "turn/completed" in list_server_notifications(schema_dir)
    assert "item/fileChange/requestApproval" in list_approval_message_types(schema_dir)
    assert "thread/started" in list_session_message_types(schema_dir)
    assert load_protocol_schema(schema_dir, version="v2")["title"] == "protocol"


def _write_schema_dir(tmp_path: Path) -> Path:
    schema_dir = tmp_path / "schema"
    schema_dir.mkdir()
    (schema_dir / "codex_app_server_protocol.v2.schemas.json").write_text(
        json.dumps({"title": "protocol"}),
        encoding="utf-8",
    )
    (schema_dir / "ClientRequest.json").write_text(
        json.dumps(
            {
                "oneOf": [
                    _variant("initialize", "InitializeParams"),
                    _variant("thread/start", "ThreadStartParams"),
                    _variant("turn/start", "TurnStartParams"),
                ]
            }
        ),
        encoding="utf-8",
    )
    (schema_dir / "ServerRequest.json").write_text(
        json.dumps(
            {
                "oneOf": [
                    _variant("item/commandExecution/requestApproval", "CommandExecutionRequestApprovalParams"),
                    _variant("item/fileChange/requestApproval", "FileChangeRequestApprovalParams"),
                ]
            }
        ),
        encoding="utf-8",
    )
    (schema_dir / "ServerNotification.json").write_text(
        json.dumps({"oneOf": [_notification("thread/started", "ThreadStartedNotification"), _notification("turn/completed", "TurnCompletedNotification")]}),
        encoding="utf-8",
    )
    return schema_dir


def _variant(method: str, ref: str) -> dict:
    return {
        "properties": {
            "method": {"enum": [method]},
            "params": {"$ref": f"#/definitions/{ref}"},
        }
    }


def _notification(method: str, ref: str) -> dict:
    return _variant(method, ref)
