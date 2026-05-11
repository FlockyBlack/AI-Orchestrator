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
