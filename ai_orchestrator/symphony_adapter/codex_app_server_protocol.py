from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class CodexAppServerSchemaIndex:
    schema_dir: str
    version: str
    protocol_schema_path: str
    client_request_path: str
    server_request_path: str
    server_notification_path: str
    client_requests: tuple[str, ...]
    server_requests: tuple[str, ...]
    server_notifications: tuple[str, ...]
    approval_message_types: tuple[str, ...]
    session_message_types: tuple[str, ...]
    auth_message_types: tuple[str, ...]
    git_review_message_types: tuple[str, ...]
    request_param_refs: Mapping[str, str]
    server_request_param_refs: Mapping[str, str]
    notification_param_refs: Mapping[str, str]
    json_files: tuple[str, ...]
    ts_files: tuple[str, ...]
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CodexAppServerSchemaIndex":
        return cls(
            schema_dir=str(payload.get("schema_dir") or ""),
            version=str(payload.get("version") or "v2"),
            protocol_schema_path=str(payload.get("protocol_schema_path") or ""),
            client_request_path=str(payload.get("client_request_path") or ""),
            server_request_path=str(payload.get("server_request_path") or ""),
            server_notification_path=str(payload.get("server_notification_path") or ""),
            client_requests=tuple(str(value) for value in payload.get("client_requests", [])),
            server_requests=tuple(str(value) for value in payload.get("server_requests", [])),
            server_notifications=tuple(str(value) for value in payload.get("server_notifications", [])),
            approval_message_types=tuple(str(value) for value in payload.get("approval_message_types", [])),
            session_message_types=tuple(str(value) for value in payload.get("session_message_types", [])),
            auth_message_types=tuple(str(value) for value in payload.get("auth_message_types", [])),
            git_review_message_types=tuple(str(value) for value in payload.get("git_review_message_types", [])),
            request_param_refs=dict(payload.get("request_param_refs", {})) if isinstance(payload.get("request_param_refs", {}), Mapping) else {},
            server_request_param_refs=(
                dict(payload.get("server_request_param_refs", {}))
                if isinstance(payload.get("server_request_param_refs", {}), Mapping)
                else {}
            ),
            notification_param_refs=(
                dict(payload.get("notification_param_refs", {}))
                if isinstance(payload.get("notification_param_refs", {}), Mapping)
                else {}
            ),
            json_files=tuple(str(value) for value in payload.get("json_files", [])),
            ts_files=tuple(str(value) for value in payload.get("ts_files", [])),
            errors=tuple(str(value) for value in payload.get("errors", [])),
            warnings=tuple(str(value) for value in payload.get("warnings", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for key in (
            "client_requests",
            "server_requests",
            "server_notifications",
            "approval_message_types",
            "session_message_types",
            "auth_message_types",
            "git_review_message_types",
            "json_files",
            "ts_files",
            "errors",
            "warnings",
        ):
            payload[key] = list(payload[key])
        payload["request_param_refs"] = dict(self.request_param_refs)
        payload["server_request_param_refs"] = dict(self.server_request_param_refs)
        payload["notification_param_refs"] = dict(self.notification_param_refs)
        return payload


def inspect_schema_dir(schema_dir: str | Path) -> CodexAppServerSchemaIndex:
    root = Path(schema_dir)
    errors: list[str] = []
    warnings: list[str] = []
    if not root.exists():
        errors.append(f"schema_dir does not exist: {root}")
    protocol_path = _protocol_schema_path(root, "v2")
    client_path = root / "ClientRequest.json"
    server_request_path = root / "ServerRequest.json"
    notification_path = root / "ServerNotification.json"
    for label, path in (
        ("protocol schema", protocol_path),
        ("ClientRequest", client_path),
        ("ServerRequest", server_request_path),
        ("ServerNotification", notification_path),
    ):
        if not path.exists():
            errors.append(f"missing {label}: {path}")
    client_refs = _method_param_refs(client_path)
    server_request_refs = _method_param_refs(server_request_path)
    notification_refs = _method_param_refs(notification_path)
    client_requests = tuple(client_refs)
    server_requests = tuple(server_request_refs)
    notifications = tuple(notification_refs)
    if "initialize" not in client_requests:
        errors.append("ClientRequest index missing initialize")
    if "thread/start" not in client_requests:
        warnings.append("ClientRequest index missing thread/start")
    if "turn/start" not in client_requests:
        warnings.append("ClientRequest index missing turn/start")
    json_files = tuple(str(path.relative_to(root)) for path in sorted(root.rglob("*.json"))) if root.exists() else ()
    ts_files = tuple(str(path.relative_to(root)) for path in sorted(root.rglob("*.ts"))) if root.exists() else ()
    return CodexAppServerSchemaIndex(
        schema_dir=str(root),
        version="v2",
        protocol_schema_path=str(protocol_path),
        client_request_path=str(client_path),
        server_request_path=str(server_request_path),
        server_notification_path=str(notification_path),
        client_requests=client_requests,
        server_requests=server_requests,
        server_notifications=notifications,
        approval_message_types=tuple(_approval_methods(server_requests, server_request_refs)),
        session_message_types=tuple(_session_methods(client_requests, server_requests, notifications)),
        auth_message_types=tuple(_contains_methods(client_requests + server_requests + notifications, ("auth", "login", "account/"))),
        git_review_message_types=tuple(_git_review_methods(root, client_requests + server_requests + notifications)),
        request_param_refs=client_refs,
        server_request_param_refs=server_request_refs,
        notification_param_refs=notification_refs,
        json_files=json_files,
        ts_files=ts_files,
        errors=tuple(dict.fromkeys(errors)),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def load_protocol_schema(schema_dir: str | Path, version: str = "v2") -> dict[str, Any]:
    path = _protocol_schema_path(Path(schema_dir), version)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"protocol schema must be an object: {path}")
    return dict(payload)


def list_client_requests(schema_dir: str | Path) -> tuple[str, ...]:
    return tuple(_method_param_refs(Path(schema_dir) / "ClientRequest.json"))


def list_server_notifications(schema_dir: str | Path) -> tuple[str, ...]:
    return tuple(_method_param_refs(Path(schema_dir) / "ServerNotification.json"))


def list_approval_message_types(schema_dir: str | Path) -> tuple[str, ...]:
    refs = _method_param_refs(Path(schema_dir) / "ServerRequest.json")
    return tuple(_approval_methods(tuple(refs), refs))


def list_session_message_types(schema_dir: str | Path) -> tuple[str, ...]:
    root = Path(schema_dir)
    client = tuple(_method_param_refs(root / "ClientRequest.json"))
    server = tuple(_method_param_refs(root / "ServerRequest.json"))
    notifications = tuple(_method_param_refs(root / "ServerNotification.json"))
    return tuple(_session_methods(client, server, notifications))


def find_initialize_request_schema(schema_dir: str | Path) -> dict[str, Any]:
    root = Path(schema_dir)
    client_path = root / "ClientRequest.json"
    if not client_path.exists():
        return {
            "available": False,
            "schema_dir": str(root),
            "client_request_path": str(client_path),
            "errors": [f"missing ClientRequest.json: {client_path}"],
        }
    try:
        payload = json.loads(client_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "available": False,
            "schema_dir": str(root),
            "client_request_path": str(client_path),
            "errors": [f"invalid ClientRequest.json: {exc}"],
        }
    if not isinstance(payload, Mapping):
        return {
            "available": False,
            "schema_dir": str(root),
            "client_request_path": str(client_path),
            "errors": ["ClientRequest schema must be an object"],
        }
    for variant in payload.get("oneOf", []):
        if not isinstance(variant, Mapping):
            continue
        properties = variant.get("properties", {})
        if not isinstance(properties, Mapping):
            continue
        method = properties.get("method", {})
        if not isinstance(method, Mapping):
            continue
        enum = method.get("enum", [])
        if isinstance(enum, list) and enum and enum[0] == "initialize":
            params = properties.get("params", {})
            params_ref = ""
            if isinstance(params, Mapping):
                params_ref = str(params.get("$ref") or "")
                if not params_ref:
                    all_of = params.get("allOf", [])
                    if isinstance(all_of, list) and all_of and isinstance(all_of[0], Mapping):
                        params_ref = str(all_of[0].get("$ref") or "")
            return {
                "available": True,
                "schema_dir": str(root),
                "client_request_path": str(client_path),
                "method": "initialize",
                "title": str(variant.get("title") or "InitializeRequest"),
                "required": list(variant.get("required", [])) if isinstance(variant.get("required", []), list) else [],
                "params_ref": params_ref.replace("#/definitions/", ""),
                "params_schema_file": str(root / "InitializeParams.ts") if (root / "InitializeParams.ts").exists() else "",
                "errors": [],
                "warnings": [],
            }
    return {
        "available": False,
        "schema_dir": str(root),
        "client_request_path": str(client_path),
        "errors": ["ClientRequest schema does not define initialize"],
    }


def build_minimal_initialize_request(schema_dir: str | Path) -> dict[str, Any] | None:
    initialize = find_initialize_request_schema(schema_dir)
    if not initialize.get("available"):
        return None
    return {
        "id": "ai-orchestrator-dry-run-initialize",
        "method": "initialize",
        "params": {
            "clientInfo": {
                "name": "ai-orchestrator",
                "title": "AI-Orchestrator app-server dry-run",
                "version": "0.1.0",
            },
            "capabilities": {
                "experimentalApi": False,
                "optOutNotificationMethods": [],
            },
        },
    }


def validate_client_request_against_schema(
    request: Mapping[str, Any] | Any,
    schema_dir: str | Path,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(request, Mapping):
        return {"valid": False, "errors": ["client request must be a JSON object"], "warnings": []}
    if "id" not in request:
        errors.append("client request missing id")
    if not request.get("method"):
        errors.append("client request missing method")
    if "jsonrpc" in request and request.get("jsonrpc") != "2.0":
        errors.append("jsonrpc field must be 2.0 when present")
    method = str(request.get("method") or "")
    known = set(list_client_requests(schema_dir))
    if method and method not in known:
        errors.append(f"unknown client request method: {method}")
    required_by_method = _request_required_fields(Path(schema_dir) / "ClientRequest.json", method)
    if "params" in required_by_method and "params" not in request:
        errors.append(f"client request {method} missing params")
    if method == "initialize":
        params = request.get("params")
        if not isinstance(params, Mapping):
            errors.append("initialize params must be an object")
        else:
            client_info = params.get("clientInfo")
            if not isinstance(client_info, Mapping):
                errors.append("initialize params missing clientInfo")
            else:
                for field in ("name", "version"):
                    if not client_info.get(field):
                        errors.append(f"initialize clientInfo missing {field}")
            capabilities = params.get("capabilities")
            if capabilities is not None and not isinstance(capabilities, Mapping):
                errors.append("initialize capabilities must be object or null")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors)), "warnings": list(dict.fromkeys(warnings))}


def validate_server_message_against_schema(
    message: Mapping[str, Any] | Any,
    schema_dir: str | Path,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(message, Mapping):
        return {"valid": False, "errors": ["server message must be a JSON object"], "warnings": []}
    if "jsonrpc" in message and message.get("jsonrpc") != "2.0":
        errors.append("jsonrpc field must be 2.0 when present")
    if "id" in message and ("result" in message or "error" in message):
        return {"valid": not errors, "errors": list(dict.fromkeys(errors)), "warnings": []}
    method = str(message.get("method") or "")
    if not method:
        errors.append("server message missing method or response result/error")
        return {"valid": False, "errors": list(dict.fromkeys(errors)), "warnings": list(dict.fromkeys(warnings))}
    root = Path(schema_dir)
    server_requests = set(_method_param_refs(root / "ServerRequest.json"))
    notifications = set(_method_param_refs(root / "ServerNotification.json"))
    if method not in server_requests and method not in notifications:
        errors.append(f"unknown server message method: {method}")
    if method in server_requests and "id" not in message:
        errors.append(f"server request {method} missing id")
    if method in notifications and "id" in message:
        warnings.append(f"server notification {method} unexpectedly included id")
    required = _request_required_fields(root / ("ServerRequest.json" if method in server_requests else "ServerNotification.json"), method)
    if "params" in required and "params" not in message:
        errors.append(f"server message {method} missing params")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors)), "warnings": list(dict.fromkeys(warnings))}


def describe_protocol_capabilities(schema_dir: str | Path) -> dict[str, Any]:
    index = inspect_schema_dir(schema_dir)
    initialize = find_initialize_request_schema(schema_dir)
    initialize_request = build_minimal_initialize_request(schema_dir)
    initialize_validation = (
        validate_client_request_against_schema(initialize_request, schema_dir)
        if initialize_request is not None
        else {"valid": False, "errors": ["minimal initialize request unavailable"], "warnings": []}
    )
    return {
        "schema_dir": index.schema_dir,
        "version": index.version,
        "schema_index_valid": not index.errors,
        "protocol_schema_path": index.protocol_schema_path,
        "client_request_path": index.client_request_path,
        "server_request_path": index.server_request_path,
        "server_notification_path": index.server_notification_path,
        "client_request_count": len(index.client_requests),
        "server_request_count": len(index.server_requests),
        "server_notification_count": len(index.server_notifications),
        "client_requests": list(index.client_requests),
        "server_requests": list(index.server_requests),
        "server_notifications": list(index.server_notifications),
        "initialize_request_schema": initialize,
        "minimal_initialize_request_available": initialize_request is not None,
        "minimal_initialize_request": initialize_request,
        "minimal_initialize_request_validation": initialize_validation,
        "session_message_types": list(index.session_message_types),
        "approval_message_types": list(index.approval_message_types),
        "auth_message_types": list(index.auth_message_types),
        "git_review_message_types": list(index.git_review_message_types),
        "known_json_files": list(index.json_files),
        "known_ts_files": list(index.ts_files),
        "errors": list(index.errors) + list(initialize.get("errors", [])),
        "warnings": list(index.warnings) + list(initialize.get("warnings", [])),
        "network_used": False,
        "app_server_started": False,
    }


def _protocol_schema_path(root: Path, version: str) -> Path:
    if version == "v2":
        return root / "codex_app_server_protocol.v2.schemas.json"
    return root / "codex_app_server_protocol.schemas.json"


def _method_param_refs(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, Mapping):
        return {}
    refs: dict[str, str] = {}
    for variant in payload.get("oneOf", []):
        if not isinstance(variant, Mapping):
            continue
        properties = variant.get("properties", {})
        if not isinstance(properties, Mapping):
            continue
        method_props = properties.get("method", {})
        if not isinstance(method_props, Mapping):
            continue
        enum = method_props.get("enum", [])
        if not isinstance(enum, list) or not enum:
            continue
        method = str(enum[0])
        params = properties.get("params", {})
        ref = ""
        if isinstance(params, Mapping):
            if params.get("$ref"):
                ref = str(params["$ref"])
            else:
                all_of = params.get("allOf", [])
                if isinstance(all_of, list) and all_of and isinstance(all_of[0], Mapping):
                    ref = str(all_of[0].get("$ref") or "")
        refs[method] = ref.replace("#/definitions/", "")
    return refs


def _request_required_fields(path: Path, method_name: str) -> list[str]:
    if not path.exists() or not method_name:
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, Mapping):
        return []
    for variant in payload.get("oneOf", []):
        if not isinstance(variant, Mapping):
            continue
        properties = variant.get("properties", {})
        if not isinstance(properties, Mapping):
            continue
        method = properties.get("method", {})
        if not isinstance(method, Mapping):
            continue
        enum = method.get("enum", [])
        if isinstance(enum, list) and enum and enum[0] == method_name:
            required = variant.get("required", [])
            return [str(value) for value in required] if isinstance(required, list) else []
    return []


def _approval_methods(methods: tuple[str, ...], refs: Mapping[str, str]) -> list[str]:
    result: list[str] = []
    for method in methods:
        joined = f"{method} {refs.get(method, '')}".lower()
        if "approval" in joined or "permission" in joined or method in {"applyPatchApproval", "execCommandApproval"}:
            result.append(method)
    return result


def _session_methods(client: tuple[str, ...], server: tuple[str, ...], notifications: tuple[str, ...]) -> list[str]:
    result = ["initialize"]
    for method in [*client, *server, *notifications]:
        if method.startswith(("thread/", "turn/")) or method in {"initialized"}:
            result.append(method)
    return list(dict.fromkeys(result))


def _contains_methods(methods: tuple[str, ...], tokens: tuple[str, ...]) -> list[str]:
    result: list[str] = []
    for method in methods:
        lowered = method.lower()
        if any(token in lowered for token in tokens):
            result.append(method)
    return list(dict.fromkeys(result))


def _git_review_methods(root: Path, methods: tuple[str, ...]) -> list[str]:
    result = _contains_methods(methods, ("git", "diff", "review"))
    if root.exists():
        for path in sorted(root.rglob("*.ts")):
            name = path.stem
            lowered = name.lower()
            if any(token in lowered for token in ("git", "diff", "review")):
                result.append(name)
    return list(dict.fromkeys(result))
