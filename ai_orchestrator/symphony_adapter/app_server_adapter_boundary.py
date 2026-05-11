from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Mapping

from .codex_app_server_protocol import CodexAppServerSchemaIndex
from .symphony_session_plan import CodexAppServerSessionPlan


APP_SERVER_ADAPTER_PLAN_SCHEMA_VERSION = "app_server_adapter_plan.v1"


class AppServerAdapterMode(str, Enum):
    SCHEMA_ONLY = "schema_only"
    DRY_RUN = "dry_run"
    LOCAL_STDIO_PLANNED = "local_stdio_planned"
    WEBSOCKET_PLANNED = "websocket_planned"
    DISABLED = "disabled"


@dataclass(frozen=True)
class AppServerAdapterPlan:
    mode: str
    session_id: str
    task_id: str
    app_server_transport: str
    app_server_listen: str
    start_command: tuple[str, ...]
    schema_index_summary: Mapping[str, Any]
    will_start_server: bool = False
    real_app_server_started: bool = False
    persistent_server: bool = False
    daemon_created: bool = False
    scheduler_created: bool = False
    background_worker_created: bool = False
    external_network_allowed: bool = False
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    schema_version: str = APP_SERVER_ADAPTER_PLAN_SCHEMA_VERSION

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AppServerAdapterPlan":
        return cls(
            mode=str(payload.get("mode") or AppServerAdapterMode.SCHEMA_ONLY.value),
            session_id=str(payload.get("session_id") or ""),
            task_id=str(payload.get("task_id") or ""),
            app_server_transport=str(payload.get("app_server_transport") or ""),
            app_server_listen=str(payload.get("app_server_listen") or ""),
            start_command=tuple(str(value) for value in payload.get("start_command", [])),
            schema_index_summary=(
                dict(payload.get("schema_index_summary", {}))
                if isinstance(payload.get("schema_index_summary", {}), Mapping)
                else {}
            ),
            will_start_server=bool(payload.get("will_start_server", False)),
            real_app_server_started=bool(payload.get("real_app_server_started", False)),
            persistent_server=bool(payload.get("persistent_server", False)),
            daemon_created=bool(payload.get("daemon_created", False)),
            scheduler_created=bool(payload.get("scheduler_created", False)),
            background_worker_created=bool(payload.get("background_worker_created", False)),
            external_network_allowed=bool(payload.get("external_network_allowed", False)),
            errors=tuple(str(value) for value in payload.get("errors", [])),
            warnings=tuple(str(value) for value in payload.get("warnings", [])),
            schema_version=str(payload.get("schema_version") or APP_SERVER_ADAPTER_PLAN_SCHEMA_VERSION),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["start_command"] = list(self.start_command)
        payload["schema_index_summary"] = dict(self.schema_index_summary)
        payload["errors"] = list(self.errors)
        payload["warnings"] = list(self.warnings)
        return payload


def build_app_server_adapter_plan(
    session_plan: CodexAppServerSessionPlan | Mapping[str, Any],
    schema_index: CodexAppServerSchemaIndex | Mapping[str, Any],
) -> AppServerAdapterPlan:
    session = session_plan if isinstance(session_plan, CodexAppServerSessionPlan) else CodexAppServerSessionPlan.from_dict(session_plan)
    index = schema_index if isinstance(schema_index, CodexAppServerSchemaIndex) else CodexAppServerSchemaIndex.from_dict(schema_index)
    mode = (
        AppServerAdapterMode.LOCAL_STDIO_PLANNED.value
        if session.app_server_transport == "stdio"
        else AppServerAdapterMode.WEBSOCKET_PLANNED.value
    )
    command = ("codex", "app-server", "--listen", session.app_server_listen)
    plan = AppServerAdapterPlan(
        mode=mode,
        session_id=session.session_id,
        task_id=session.task_id,
        app_server_transport=session.app_server_transport,
        app_server_listen=session.app_server_listen,
        start_command=command,
        schema_index_summary={
            "schema_dir": index.schema_dir,
            "version": index.version,
            "client_request_count": len(index.client_requests),
            "server_notification_count": len(index.server_notifications),
            "approval_message_types": list(index.approval_message_types),
            "session_message_types": list(index.session_message_types),
            "errors": list(index.errors),
        },
        will_start_server=False,
        real_app_server_started=False,
        persistent_server=False,
        external_network_allowed=False,
    )
    validation = validate_app_server_adapter_plan(plan)
    return AppServerAdapterPlan.from_dict({**plan.to_dict(), "errors": validation["errors"], "warnings": validation["warnings"]})


def validate_app_server_adapter_plan(plan: AppServerAdapterPlan | Mapping[str, Any]) -> dict[str, Any]:
    plan_obj = plan if isinstance(plan, AppServerAdapterPlan) else AppServerAdapterPlan.from_dict(plan)
    errors: list[str] = []
    warnings: list[str] = list(plan_obj.warnings)
    if plan_obj.mode not in {mode.value for mode in AppServerAdapterMode}:
        errors.append(f"unsupported adapter mode: {plan_obj.mode}")
    if plan_obj.mode != AppServerAdapterMode.DISABLED.value:
        if tuple(plan_obj.start_command[:3]) != ("codex", "app-server", "--listen"):
            errors.append("start_command must render codex app-server --listen")
        if len(plan_obj.start_command) != 4:
            errors.append("start_command must contain exactly four argv elements")
    if plan_obj.app_server_transport == "stdio" and plan_obj.app_server_listen != "stdio://":
        errors.append("stdio transport must use stdio://")
    if plan_obj.app_server_transport == "websocket" and not plan_obj.app_server_listen.startswith("ws://127.0.0.1:"):
        errors.append("websocket listen must bind to 127.0.0.1")
    if plan_obj.will_start_server or plan_obj.real_app_server_started:
        errors.append("adapter boundary must not start the app-server in this milestone")
    for flag_name in ("persistent_server", "daemon_created", "scheduler_created", "background_worker_created"):
        if getattr(plan_obj, flag_name):
            errors.append(f"adapter boundary must not set {flag_name}")
    if plan_obj.external_network_allowed:
        errors.append("adapter boundary must not allow external network")
    summary_errors = plan_obj.schema_index_summary.get("errors", []) if isinstance(plan_obj.schema_index_summary, Mapping) else []
    if summary_errors:
        warnings.extend(str(error) for error in summary_errors)
    return {"valid": not errors, "errors": list(dict.fromkeys(errors)), "warnings": list(dict.fromkeys(warnings))}


def render_app_server_start_command(plan: AppServerAdapterPlan | Mapping[str, Any]) -> str:
    plan_obj = plan if isinstance(plan, AppServerAdapterPlan) else AppServerAdapterPlan.from_dict(plan)
    validation = validate_app_server_adapter_plan(plan_obj)
    if not validation["valid"]:
        raise ValueError("invalid app-server adapter plan: " + "; ".join(validation["errors"]))
    return " ".join(plan_obj.start_command)
