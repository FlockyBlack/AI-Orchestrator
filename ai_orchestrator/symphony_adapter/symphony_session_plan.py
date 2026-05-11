from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from .symphony_task_contract import SymphonyTask
from .symphony_workspace_plan import SymphonyWorkspacePlan


SESSION_PLAN_SCHEMA_VERSION = "symphony_session_plan.v1"
DEFAULT_FORBIDDEN_TOOLS = (
    "browser_automation",
    "web_search",
    "openrouter",
    "polymarket_api",
    "authenticated_endpoint",
    "wallet",
    "private_key",
    "signing",
    "real_orders",
    "scheduler",
    "daemon",
    "background_worker",
)


@dataclass(frozen=True)
class SymphonySessionPlan:
    session_id: str
    task_id: str
    workspace_path: str
    prompt_path: str
    expected_result_path: str
    approval_policy: str | Mapping[str, Any]
    sandbox_policy: Mapping[str, Any]
    allowed_tools: tuple[str, ...]
    forbidden_tools: tuple[str, ...]
    result_contract: Mapping[str, Any]
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    schema_version: str = SESSION_PLAN_SCHEMA_VERSION

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "SymphonySessionPlan":
        return cls(
            session_id=str(payload.get("session_id") or ""),
            task_id=str(payload.get("task_id") or ""),
            workspace_path=str(payload.get("workspace_path") or ""),
            prompt_path=str(payload.get("prompt_path") or ""),
            expected_result_path=str(payload.get("expected_result_path") or ""),
            approval_policy=payload.get("approval_policy", "on-request"),
            sandbox_policy=dict(payload.get("sandbox_policy", {})) if isinstance(payload.get("sandbox_policy", {}), Mapping) else {},
            allowed_tools=tuple(str(value) for value in payload.get("allowed_tools", [])),
            forbidden_tools=tuple(str(value) for value in payload.get("forbidden_tools", [])),
            result_contract=dict(payload.get("result_contract", {})) if isinstance(payload.get("result_contract", {}), Mapping) else {},
            errors=tuple(str(value) for value in payload.get("errors", [])),
            warnings=tuple(str(value) for value in payload.get("warnings", [])),
            schema_version=str(payload.get("schema_version") or SESSION_PLAN_SCHEMA_VERSION),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["approval_policy"] = self.approval_policy
        payload["sandbox_policy"] = dict(self.sandbox_policy)
        payload["allowed_tools"] = list(self.allowed_tools)
        payload["forbidden_tools"] = list(self.forbidden_tools)
        payload["result_contract"] = dict(self.result_contract)
        payload["errors"] = list(self.errors)
        payload["warnings"] = list(self.warnings)
        return payload


@dataclass(frozen=True)
class CodexAppServerSessionPlan(SymphonySessionPlan):
    app_server_transport: str = "stdio"
    app_server_listen: str = "stdio://"
    app_server_schema_dir: str = ""
    protocol_version: str = "v2"
    thread_start_method: str = "thread/start"
    turn_start_method: str = "turn/start"
    initialize_method: str = "initialize"

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "CodexAppServerSessionPlan":
        base = SymphonySessionPlan.from_dict(payload)
        return cls(
            session_id=base.session_id,
            task_id=base.task_id,
            workspace_path=base.workspace_path,
            prompt_path=base.prompt_path,
            expected_result_path=base.expected_result_path,
            approval_policy=base.approval_policy,
            sandbox_policy=base.sandbox_policy,
            allowed_tools=base.allowed_tools,
            forbidden_tools=base.forbidden_tools,
            result_contract=base.result_contract,
            errors=base.errors,
            warnings=base.warnings,
            schema_version=base.schema_version,
            app_server_transport=str(payload.get("app_server_transport") or "stdio"),
            app_server_listen=str(payload.get("app_server_listen") or "stdio://"),
            app_server_schema_dir=str(payload.get("app_server_schema_dir") or ""),
            protocol_version=str(payload.get("protocol_version") or "v2"),
            thread_start_method=str(payload.get("thread_start_method") or "thread/start"),
            turn_start_method=str(payload.get("turn_start_method") or "turn/start"),
            initialize_method=str(payload.get("initialize_method") or "initialize"),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload.update(
            {
                "app_server_transport": self.app_server_transport,
                "app_server_listen": self.app_server_listen,
                "app_server_schema_dir": self.app_server_schema_dir,
                "protocol_version": self.protocol_version,
                "thread_start_method": self.thread_start_method,
                "turn_start_method": self.turn_start_method,
                "initialize_method": self.initialize_method,
            }
        )
        return payload


def build_session_plan(
    task: SymphonyTask | Mapping[str, Any],
    workspace_plan: SymphonyWorkspacePlan | Mapping[str, Any],
    app_server_schema_dir: str | Path,
) -> CodexAppServerSessionPlan:
    task_obj = task if isinstance(task, SymphonyTask) else SymphonyTask.from_dict(task)
    workspace_obj = (
        workspace_plan
        if isinstance(workspace_plan, SymphonyWorkspacePlan)
        else SymphonyWorkspacePlan.from_dict(workspace_plan)
    )
    workspace_path = Path(workspace_obj.workspace_path).resolve(strict=False)
    session_id = f"symphony_{_safe_id(task_obj.task_id)}"
    session_root = workspace_path / ".ai_orchestrator" / "symphony" / task_obj.task_id
    result_contract = _result_contract(task_obj)
    plan = CodexAppServerSessionPlan(
        session_id=session_id,
        task_id=task_obj.task_id,
        workspace_path=str(workspace_path),
        app_server_transport="stdio",
        app_server_listen="stdio://",
        prompt_path=str(session_root / "prompt.md"),
        expected_result_path=str(session_root / "expected_result.json"),
        approval_policy="on-request",
        sandbox_policy={
            "type": "workspaceWrite",
            "writableRoots": [str(workspace_path)],
            "networkAccess": False,
            "excludeTmpdirEnvVar": True,
            "excludeSlashTmp": True,
        },
        allowed_tools=("shell_readonly", "apply_patch", "file_read", "targeted_tests"),
        forbidden_tools=DEFAULT_FORBIDDEN_TOOLS,
        result_contract=result_contract,
        app_server_schema_dir=str(Path(app_server_schema_dir).resolve(strict=False)),
        protocol_version="v2",
    )
    validation = validate_session_plan(plan)
    return CodexAppServerSessionPlan.from_dict({**plan.to_dict(), "errors": validation["errors"], "warnings": validation["warnings"]})


def validate_session_plan(plan: CodexAppServerSessionPlan | SymphonySessionPlan | Mapping[str, Any]) -> dict[str, Any]:
    plan_obj = plan if isinstance(plan, CodexAppServerSessionPlan) else CodexAppServerSessionPlan.from_dict(plan)
    errors: list[str] = []
    warnings: list[str] = list(plan_obj.warnings)
    if not plan_obj.session_id:
        errors.append("missing session_id")
    if not plan_obj.task_id:
        errors.append("missing task_id")
    if not Path(plan_obj.workspace_path).is_absolute():
        errors.append("workspace_path must be absolute")
    if plan_obj.app_server_transport not in {"stdio", "websocket"}:
        errors.append(f"unsupported app_server_transport: {plan_obj.app_server_transport}")
    if plan_obj.app_server_transport == "stdio" and plan_obj.app_server_listen != "stdio://":
        errors.append("stdio transport must use stdio:// listen URL")
    if plan_obj.app_server_transport == "websocket" and not plan_obj.app_server_listen.startswith("ws://127.0.0.1:"):
        errors.append("websocket transport must bind to ws://127.0.0.1:<port>")
    schema_dir = Path(plan_obj.app_server_schema_dir)
    if not schema_dir.exists():
        errors.append(f"app_server_schema_dir does not exist: {schema_dir}")
    elif not (schema_dir / "ClientRequest.json").exists():
        errors.append("app_server_schema_dir missing ClientRequest.json")
    if plan_obj.approval_policy == "never":
        errors.append("approval_policy must not be never for planned supervised sessions")
    forbidden = {value.lower() for value in plan_obj.forbidden_tools}
    for required in ("browser_automation", "openrouter", "polymarket_api", "wallet", "daemon", "scheduler"):
        if required not in forbidden:
            errors.append(f"forbidden_tools missing {required}")
    if not isinstance(plan_obj.result_contract, Mapping) or not plan_obj.result_contract:
        errors.append("missing result_contract")
    elif not plan_obj.result_contract.get("safety_flags_must_be_false"):
        errors.append("result_contract must require unsafe safety flags to be false")
    if "web_search" in {value.lower() for value in plan_obj.allowed_tools}:
        errors.append("allowed_tools must not include web_search")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors)), "warnings": list(dict.fromkeys(warnings))}


def _result_contract(task: SymphonyTask) -> dict[str, Any]:
    unsafe_flags = [
        "real_trading",
        "real_order_submitted",
        "wallet_used",
        "signing_used",
        "private_key_used",
        "trading_endpoint_used",
        "real_money_used",
        "autonomous_trading_enabled",
        "openrouter_used",
        "polymarket_api_used",
        "authenticated_endpoint_used",
        "browser_automation_used",
        "unsafe_git_staging_used",
        "force_push_used",
        "daemon_created",
        "scheduler_created",
        "background_worker_created",
        "invented_outcomes",
    ]
    return {
        "schema_version": "symphony_result_contract.v1",
        "task_id": task.task_id,
        "required_fields": ["task_id", "status", "validation_passed", "safety_ok", "summary"],
        "allowed_statuses": ["completed", "blocked", "failed", "needs_retry"],
        "expected_artifacts": list(task.expected_artifacts),
        "acceptance_gates": list(task.acceptance_gates),
        "safety_flags_must_be_false": unsafe_flags,
        "forbidden_actions": list(task.forbidden_actions),
    }


def _safe_id(value: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "_" for ch in value).strip("_") or "task"
