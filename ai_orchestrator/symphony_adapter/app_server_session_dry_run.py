from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, TextIO

from .codex_app_server_protocol import (
    build_minimal_initialize_request,
    describe_protocol_capabilities,
    validate_client_request_against_schema,
    validate_server_message_against_schema,
)


APP_SERVER_DRY_RUN_SCHEMA_VERSION = "app_server_dry_run.v1"
ALLOWED_LISTEN_MODES = {"stdio", "ws_loopback", "disabled"}
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


@dataclass(frozen=True)
class AppServerDryRunConfig:
    repo_root: str
    workspace_path: str
    schema_dir: str
    codex_command: tuple[str, ...] = ("codex",)
    listen_mode: str = "stdio"
    ws_host: str = "127.0.0.1"
    ws_port: int = 0
    timeout_seconds: float = 30
    startup_timeout_seconds: float = 10
    shutdown_timeout_seconds: float = 5
    allow_network: bool = False
    allow_auth: bool = False
    allow_browser: bool = False
    allow_real_task_execution: bool = False
    write_logs: bool = True
    dry_run_only: bool = True
    operator_approved: bool = False
    schema_version: str = APP_SERVER_DRY_RUN_SCHEMA_VERSION

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "AppServerDryRunConfig":
        command = payload.get("codex_command", ("codex",))
        if isinstance(command, str):
            command_tuple = (command,)
        else:
            command_tuple = tuple(str(part) for part in command)
        return cls(
            repo_root=str(payload.get("repo_root") or ""),
            workspace_path=str(payload.get("workspace_path") or payload.get("repo_root") or ""),
            schema_dir=str(payload.get("schema_dir") or ""),
            codex_command=command_tuple,
            listen_mode=str(payload.get("listen_mode") or "stdio"),
            ws_host=str(payload.get("ws_host") or "127.0.0.1"),
            ws_port=int(payload.get("ws_port") or 0),
            timeout_seconds=float(payload.get("timeout_seconds", 30)),
            startup_timeout_seconds=float(payload.get("startup_timeout_seconds", 10)),
            shutdown_timeout_seconds=float(payload.get("shutdown_timeout_seconds", 5)),
            allow_network=bool(payload.get("allow_network", False)),
            allow_auth=bool(payload.get("allow_auth", False)),
            allow_browser=bool(payload.get("allow_browser", False)),
            allow_real_task_execution=bool(payload.get("allow_real_task_execution", False)),
            write_logs=bool(payload.get("write_logs", True)),
            dry_run_only=bool(payload.get("dry_run_only", True)),
            operator_approved=bool(payload.get("operator_approved", False)),
            schema_version=str(payload.get("schema_version") or APP_SERVER_DRY_RUN_SCHEMA_VERSION),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["codex_command"] = list(self.codex_command)
        return payload


@dataclass
class AppServerProcessHandle:
    command: tuple[str, ...]
    process: subprocess.Popen[str]
    started_at: str
    stdout_lines: list[str] = field(default_factory=list)
    stderr_lines: list[str] = field(default_factory=list)
    reader_threads: tuple[threading.Thread, threading.Thread] = field(default_factory=tuple)

    @property
    def pid(self) -> int:
        return int(self.process.pid or 0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": list(self.command),
            "pid": self.pid,
            "started_at": self.started_at,
            "returncode": self.process.poll(),
            "stdout_line_count": len(self.stdout_lines),
            "stderr_line_count": len(self.stderr_lines),
        }


@dataclass(frozen=True)
class AppServerDryRunRequest:
    config: Mapping[str, Any]
    command: tuple[str, ...]
    created_at: str
    schema_version: str = APP_SERVER_DRY_RUN_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": dict(self.config),
            "command": list(self.command),
            "created_at": self.created_at,
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True)
class AppServerProtocolProbeResult:
    status: str
    protocol_probe_attempted: bool
    protocol_probe_succeeded: bool
    schema_only: bool
    initialize_request_available: bool
    initialize_request_valid: bool
    request: Mapping[str, Any] | None = None
    response_messages: tuple[Mapping[str, Any], ...] = ()
    raw_stdout_lines_seen: int = 0
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "protocol_probe_attempted": self.protocol_probe_attempted,
            "protocol_probe_succeeded": self.protocol_probe_succeeded,
            "schema_only": self.schema_only,
            "initialize_request_available": self.initialize_request_available,
            "initialize_request_valid": self.initialize_request_valid,
            "request": dict(self.request) if isinstance(self.request, Mapping) else None,
            "response_messages": [dict(message) for message in self.response_messages],
            "raw_stdout_lines_seen": self.raw_stdout_lines_seen,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class AppServerShutdownResult:
    process_stopped: bool
    exit_code: int | None
    terminate_sent: bool = False
    kill_sent: bool = False
    timed_out: bool = False
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AppServerDryRunResult:
    status: str
    config: Mapping[str, Any]
    command: tuple[str, ...]
    process_started: bool
    protocol_probe_attempted: bool
    protocol_probe_succeeded: bool
    schema_only: bool
    process_stopped: bool
    blocked: bool
    started_at: str
    ended_at: str
    process_exit_code: int | None = None
    protocol_probe: Mapping[str, Any] | None = None
    shutdown: Mapping[str, Any] | None = None
    stdout: str = ""
    stderr: str = ""
    artifact_dir: str = ""
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    schema_version: str = APP_SERVER_DRY_RUN_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "config": dict(self.config),
            "command": list(self.command),
            "process_started": self.process_started,
            "protocol_probe_attempted": self.protocol_probe_attempted,
            "protocol_probe_succeeded": self.protocol_probe_succeeded,
            "schema_only": self.schema_only,
            "process_stopped": self.process_stopped,
            "blocked": self.blocked,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "process_exit_code": self.process_exit_code,
            "protocol_probe": dict(self.protocol_probe) if isinstance(self.protocol_probe, Mapping) else None,
            "shutdown": dict(self.shutdown) if isinstance(self.shutdown, Mapping) else None,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "artifact_dir": self.artifact_dir,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "schema_version": self.schema_version,
        }


def build_default_dry_run_config(
    repo_root: str | Path,
    schema_dir: str | Path,
    workspace_path: str | Path | None = None,
) -> AppServerDryRunConfig:
    repo = Path(repo_root).resolve(strict=False)
    workspace = Path(workspace_path).resolve(strict=False) if workspace_path else repo
    return AppServerDryRunConfig(
        repo_root=str(repo),
        workspace_path=str(workspace),
        schema_dir=str(Path(schema_dir).resolve(strict=False)),
    )


def validate_dry_run_config(config: AppServerDryRunConfig | Mapping[str, Any]) -> dict[str, Any]:
    config_obj = config if isinstance(config, AppServerDryRunConfig) else AppServerDryRunConfig.from_dict(config)
    errors: list[str] = []
    warnings: list[str] = []
    if config_obj.listen_mode not in ALLOWED_LISTEN_MODES:
        errors.append(f"unsupported listen_mode: {config_obj.listen_mode}")
    if config_obj.allow_network:
        errors.append("allow_network must be false for app-server dry-run")
    if config_obj.allow_auth:
        errors.append("allow_auth must be false for app-server dry-run")
    if config_obj.allow_browser:
        errors.append("allow_browser must be false for app-server dry-run")
    if config_obj.allow_real_task_execution:
        errors.append("allow_real_task_execution must be false for app-server dry-run")
    if not config_obj.dry_run_only:
        errors.append("dry_run_only must be true")
    if config_obj.timeout_seconds > 120:
        errors.append("timeout_seconds must be <= 120")
    if config_obj.timeout_seconds <= 0:
        errors.append("timeout_seconds must be positive")
    if config_obj.startup_timeout_seconds <= 0:
        errors.append("startup_timeout_seconds must be positive")
    if config_obj.shutdown_timeout_seconds <= 0:
        errors.append("shutdown_timeout_seconds must be positive")
    if config_obj.listen_mode == "ws_loopback":
        if config_obj.ws_host not in LOOPBACK_HOSTS:
            errors.append("ws_host must be loopback-only")
        if config_obj.ws_port < 0 or config_obj.ws_port > 65535:
            errors.append("ws_port must be between 0 and 65535")
    schema_dir = Path(config_obj.schema_dir)
    if not schema_dir.exists():
        errors.append(f"schema_dir does not exist: {schema_dir}")
    elif not (schema_dir / "ClientRequest.json").exists():
        errors.append("schema_dir missing ClientRequest.json")
    if not Path(config_obj.workspace_path).exists():
        warnings.append(f"workspace_path does not exist yet: {config_obj.workspace_path}")
    if not config_obj.codex_command:
        errors.append("codex_command is missing")
    elif config_obj.operator_approved and config_obj.listen_mode != "disabled":
        executable = config_obj.codex_command[0]
        resolved = str(Path(executable).resolve(strict=False)) if Path(executable).exists() else shutil.which(executable)
        if not resolved:
            errors.append(f"codex command executable was not found: {executable}")
    if config_obj.listen_mode == "disabled" and config_obj.operator_approved:
        warnings.append("listen_mode=disabled means no app-server process will be started")
    return {"valid": not errors, "errors": list(dict.fromkeys(errors)), "warnings": list(dict.fromkeys(warnings))}


def build_app_server_command(config: AppServerDryRunConfig | Mapping[str, Any]) -> tuple[str, ...]:
    config_obj = config if isinstance(config, AppServerDryRunConfig) else AppServerDryRunConfig.from_dict(config)
    if config_obj.listen_mode == "disabled":
        return tuple(config_obj.codex_command)
    listen = "stdio://" if config_obj.listen_mode == "stdio" else f"ws://{config_obj.ws_host}:{config_obj.ws_port}"
    return (*config_obj.codex_command, "app-server", "--listen", listen)


def start_app_server_process(config: AppServerDryRunConfig | Mapping[str, Any]) -> AppServerProcessHandle:
    config_obj = config if isinstance(config, AppServerDryRunConfig) else AppServerDryRunConfig.from_dict(config)
    validation = validate_dry_run_config(config_obj)
    if not validation["valid"]:
        raise ValueError("invalid app-server dry-run config: " + "; ".join(validation["errors"]))
    if config_obj.listen_mode == "disabled":
        raise ValueError("listen_mode=disabled does not start app-server")
    command = build_app_server_command(config_obj)
    cwd = config_obj.workspace_path or config_obj.repo_root
    process = subprocess.Popen(
        list(command),
        cwd=str(cwd),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    stdout_lines: list[str] = []
    stderr_lines: list[str] = []
    stdout_thread = threading.Thread(target=_read_pipe_lines, args=(process.stdout, stdout_lines), daemon=True)
    stderr_thread = threading.Thread(target=_read_pipe_lines, args=(process.stderr, stderr_lines), daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    return AppServerProcessHandle(
        command=command,
        process=process,
        started_at=_utc_iso(),
        stdout_lines=stdout_lines,
        stderr_lines=stderr_lines,
        reader_threads=(stdout_thread, stderr_thread),
    )


def probe_app_server_stdio(
    process_handle: AppServerProcessHandle,
    config: AppServerDryRunConfig | Mapping[str, Any],
) -> AppServerProtocolProbeResult:
    config_obj = config if isinstance(config, AppServerDryRunConfig) else AppServerDryRunConfig.from_dict(config)
    capabilities = describe_protocol_capabilities(config_obj.schema_dir)
    request = build_minimal_initialize_request(config_obj.schema_dir)
    if not request:
        return AppServerProtocolProbeResult(
            status="schema_inspection_only",
            protocol_probe_attempted=False,
            protocol_probe_succeeded=False,
            schema_only=True,
            initialize_request_available=False,
            initialize_request_valid=False,
            warnings=("initialize request shape is unavailable from schema",),
        )
    request_validation = validate_client_request_against_schema(request, config_obj.schema_dir)
    if not request_validation["valid"]:
        return AppServerProtocolProbeResult(
            status="schema_inspection_only",
            protocol_probe_attempted=False,
            protocol_probe_succeeded=False,
            schema_only=True,
            initialize_request_available=True,
            initialize_request_valid=False,
            request=request,
            errors=tuple(request_validation["errors"]),
            warnings=tuple(request_validation["warnings"]),
        )
    if process_handle.process.poll() is not None:
        return AppServerProtocolProbeResult(
            status="failed",
            protocol_probe_attempted=False,
            protocol_probe_succeeded=False,
            schema_only=False,
            initialize_request_available=True,
            initialize_request_valid=True,
            request=request,
            errors=(f"app-server exited before protocol probe with code {process_handle.process.returncode}",),
        )
    attempted = False
    errors: list[str] = []
    warnings: list[str] = []
    response_messages: list[Mapping[str, Any]] = []
    try:
        if process_handle.process.stdin is None:
            raise BrokenPipeError("app-server stdin is unavailable")
        process_handle.process.stdin.write(json.dumps(request, separators=(",", ":")) + "\n")
        process_handle.process.stdin.flush()
        attempted = True
    except (BrokenPipeError, OSError) as exc:
        return AppServerProtocolProbeResult(
            status="failed",
            protocol_probe_attempted=attempted,
            protocol_probe_succeeded=False,
            schema_only=False,
            initialize_request_available=True,
            initialize_request_valid=True,
            request=request,
            errors=(f"failed to write initialize request: {exc}",),
        )

    deadline = time.monotonic() + min(config_obj.startup_timeout_seconds, config_obj.timeout_seconds)
    seen_count = 0
    while time.monotonic() < deadline:
        if process_handle.process.poll() is not None and len(process_handle.stdout_lines) == seen_count:
            break
        while seen_count < len(process_handle.stdout_lines):
            raw_line = process_handle.stdout_lines[seen_count].strip()
            seen_count += 1
            if not raw_line:
                continue
            try:
                message = json.loads(raw_line)
            except json.JSONDecodeError:
                errors.append(f"non-json stdout line during protocol probe: {raw_line[:200]}")
                continue
            if not isinstance(message, Mapping):
                errors.append("protocol response must be a JSON object")
                continue
            response_messages.append(dict(message))
            validation = validate_server_message_against_schema(message, config_obj.schema_dir)
            if not validation["valid"]:
                warnings.extend(str(error) for error in validation["errors"])
            if message.get("id") == request.get("id") and ("result" in message or "error" in message):
                if "result" in message:
                    return AppServerProtocolProbeResult(
                        status="succeeded",
                        protocol_probe_attempted=True,
                        protocol_probe_succeeded=True,
                        schema_only=False,
                        initialize_request_available=True,
                        initialize_request_valid=True,
                        request=request,
                        response_messages=tuple(response_messages),
                        raw_stdout_lines_seen=seen_count,
                        warnings=tuple(dict.fromkeys(warnings + list(capabilities.get("warnings", [])))),
                    )
                errors.append(f"initialize response returned error: {message.get('error')}")
                return AppServerProtocolProbeResult(
                    status="failed",
                    protocol_probe_attempted=True,
                    protocol_probe_succeeded=False,
                    schema_only=False,
                    initialize_request_available=True,
                    initialize_request_valid=True,
                    request=request,
                    response_messages=tuple(response_messages),
                    raw_stdout_lines_seen=seen_count,
                    errors=tuple(dict.fromkeys(errors)),
                    warnings=tuple(dict.fromkeys(warnings)),
                )
        time.sleep(0.05)
    if not errors:
        errors.append("timed out waiting for initialize response")
    return AppServerProtocolProbeResult(
        status="failed",
        protocol_probe_attempted=True,
        protocol_probe_succeeded=False,
        schema_only=False,
        initialize_request_available=True,
        initialize_request_valid=True,
        request=request,
        response_messages=tuple(response_messages),
        raw_stdout_lines_seen=seen_count,
        errors=tuple(dict.fromkeys(errors)),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def probe_app_server_ws(config: AppServerDryRunConfig | Mapping[str, Any]) -> AppServerProtocolProbeResult:
    config_obj = config if isinstance(config, AppServerDryRunConfig) else AppServerDryRunConfig.from_dict(config)
    capabilities = describe_protocol_capabilities(config_obj.schema_dir)
    return AppServerProtocolProbeResult(
        status="schema_inspection_only",
        protocol_probe_attempted=False,
        protocol_probe_succeeded=False,
        schema_only=True,
        initialize_request_available=bool(build_minimal_initialize_request(config_obj.schema_dir)),
        initialize_request_valid=False,
        warnings=(
            "ws_loopback protocol probe is intentionally schema-only until a no-network websocket client is wired",
            *tuple(str(value) for value in capabilities.get("warnings", [])),
        ),
    )


def stop_app_server_process(
    process_handle: AppServerProcessHandle,
    timeout_seconds: float,
) -> AppServerShutdownResult:
    process = process_handle.process
    terminate_sent = False
    kill_sent = False
    errors: list[str] = []
    warnings: list[str] = []
    try:
        if process.stdin and not process.stdin.closed:
            process.stdin.close()
    except OSError as exc:
        warnings.append(f"failed to close stdin: {exc}")
    try:
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        if process.poll() is None:
            try:
                process.terminate()
                terminate_sent = True
            except OSError as exc:
                errors.append(f"failed to terminate app-server: {exc}")
        try:
            process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            if process.poll() is None:
                try:
                    process.kill()
                    kill_sent = True
                except OSError as exc:
                    errors.append(f"failed to kill app-server: {exc}")
            try:
                process.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                errors.append("app-server did not stop after kill")
                return AppServerShutdownResult(
                    process_stopped=False,
                    exit_code=process.poll(),
                    terminate_sent=terminate_sent,
                    kill_sent=kill_sent,
                    timed_out=True,
                    errors=tuple(errors),
                    warnings=tuple(warnings),
                )
    for thread in process_handle.reader_threads:
        thread.join(timeout=0.2)
    return AppServerShutdownResult(
        process_stopped=process.poll() is not None,
        exit_code=process.poll(),
        terminate_sent=terminate_sent,
        kill_sent=kill_sent,
        timed_out=False,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )


def run_app_server_dry_run(config: AppServerDryRunConfig | Mapping[str, Any]) -> AppServerDryRunResult:
    config_obj = config if isinstance(config, AppServerDryRunConfig) else AppServerDryRunConfig.from_dict(config)
    started_at = _utc_iso()
    command = build_app_server_command(config_obj)
    validation = validate_dry_run_config(config_obj)
    if not config_obj.operator_approved:
        errors = ["operator approval is required to start codex app-server"]
        return AppServerDryRunResult(
            status="requires_operator_approval",
            config=config_obj.to_dict(),
            command=command,
            process_started=False,
            protocol_probe_attempted=False,
            protocol_probe_succeeded=False,
            schema_only=True,
            process_stopped=True,
            blocked=True,
            started_at=started_at,
            ended_at=_utc_iso(),
            errors=tuple(errors),
            warnings=tuple(validation["warnings"]),
        )
    if not validation["valid"]:
        return AppServerDryRunResult(
            status="blocked",
            config=config_obj.to_dict(),
            command=command,
            process_started=False,
            protocol_probe_attempted=False,
            protocol_probe_succeeded=False,
            schema_only=True,
            process_stopped=True,
            blocked=True,
            started_at=started_at,
            ended_at=_utc_iso(),
            errors=tuple(validation["errors"]),
            warnings=tuple(validation["warnings"]),
        )
    if config_obj.listen_mode == "disabled":
        return AppServerDryRunResult(
            status="blocked",
            config=config_obj.to_dict(),
            command=command,
            process_started=False,
            protocol_probe_attempted=False,
            protocol_probe_succeeded=False,
            schema_only=True,
            process_stopped=True,
            blocked=True,
            started_at=started_at,
            ended_at=_utc_iso(),
            errors=("listen_mode=disabled does not start app-server",),
            warnings=tuple(validation["warnings"]),
        )

    process_handle: AppServerProcessHandle | None = None
    probe = AppServerProtocolProbeResult(
        status="not_attempted",
        protocol_probe_attempted=False,
        protocol_probe_succeeded=False,
        schema_only=True,
        initialize_request_available=False,
        initialize_request_valid=False,
    )
    shutdown = AppServerShutdownResult(process_stopped=True, exit_code=None)
    errors: list[str] = []
    warnings: list[str] = list(validation["warnings"])
    process_started = False
    try:
        process_handle = start_app_server_process(config_obj)
        process_started = True
        time.sleep(0.1)
        if config_obj.listen_mode == "stdio":
            probe = probe_app_server_stdio(process_handle, config_obj)
        else:
            probe = probe_app_server_ws(config_obj)
        errors.extend(probe.errors)
        warnings.extend(probe.warnings)
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
    finally:
        if process_handle is not None:
            shutdown = stop_app_server_process(process_handle, config_obj.shutdown_timeout_seconds)
            errors.extend(shutdown.errors)
            warnings.extend(shutdown.warnings)

    stdout = "".join(process_handle.stdout_lines) if process_handle else ""
    stderr = "".join(process_handle.stderr_lines) if process_handle else ""
    process_exit_code = process_handle.process.poll() if process_handle else None
    status = "ok" if process_started and shutdown.process_stopped and not errors else "failed"
    return AppServerDryRunResult(
        status=status,
        config=config_obj.to_dict(),
        command=command,
        process_started=process_started,
        protocol_probe_attempted=probe.protocol_probe_attempted,
        protocol_probe_succeeded=probe.protocol_probe_succeeded,
        schema_only=probe.schema_only,
        process_stopped=shutdown.process_stopped,
        blocked=False,
        started_at=started_at,
        ended_at=_utc_iso(),
        process_exit_code=process_exit_code,
        protocol_probe=probe.to_dict(),
        shutdown=shutdown.to_dict(),
        stdout=stdout,
        stderr=stderr,
        errors=tuple(dict.fromkeys(errors)),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def write_app_server_dry_run_artifacts(
    result: AppServerDryRunResult | Mapping[str, Any],
    output_dir: str | Path,
) -> dict[str, str]:
    result_payload = result.to_dict() if isinstance(result, AppServerDryRunResult) else dict(result)
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    config = result_payload.get("config", {}) if isinstance(result_payload.get("config", {}), Mapping) else {}
    command = [str(part) for part in result_payload.get("command", [])]
    probe = result_payload.get("protocol_probe") if isinstance(result_payload.get("protocol_probe"), Mapping) else {}
    paths = {
        "dry_run_config": str(target / "dry_run_config.json"),
        "app_server_command": str(target / "app_server_command.txt"),
        "protocol_probe": str(target / "protocol_probe.json"),
        "stdout": str(target / "stdout.log"),
        "stderr": str(target / "stderr.log"),
        "result": str(target / "result.json"),
        "readme": str(target / "README.md"),
    }
    _write_json(target / "dry_run_config.json", dict(config))
    _write_text(target / "app_server_command.txt", _render_command(command) + "\n")
    _write_json(target / "protocol_probe.json", dict(probe))
    _write_text(target / "stdout.log", str(result_payload.get("stdout") or ""))
    _write_text(target / "stderr.log", str(result_payload.get("stderr") or ""))
    result_with_artifact = dict(result_payload)
    result_with_artifact["artifact_dir"] = str(target)
    _write_json(target / "result.json", result_with_artifact)
    _write_text(target / "README.md", _render_artifact_readme(result_with_artifact))
    return paths


def _read_pipe_lines(pipe: TextIO | None, sink: list[str]) -> None:
    if pipe is None:
        return
    try:
        for line in iter(pipe.readline, ""):
            sink.append(line)
    finally:
        try:
            pipe.close()
        except OSError:
            return


def _render_artifact_readme(result: Mapping[str, Any]) -> str:
    return "\n".join(
        [
            "# Codex app-server dry-run",
            "",
            f"- status: `{result.get('status', '')}`",
            f"- process_started: `{result.get('process_started', False)}`",
            f"- protocol_probe_attempted: `{result.get('protocol_probe_attempted', False)}`",
            f"- protocol_probe_succeeded: `{result.get('protocol_probe_succeeded', False)}`",
            f"- schema_only: `{result.get('schema_only', False)}`",
            f"- process_stopped: `{result.get('process_stopped', False)}`",
            "",
            "This artifact records one explicit, short-lived local dry-run. It is not a daemon, scheduler, background worker, browser automation run, authenticated flow, or trading execution.",
            "",
        ]
    )


def _render_command(command: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(command)
    return " ".join(_shell_quote(part) for part in command)


def _shell_quote(value: str) -> str:
    if not value:
        return "''"
    if all(ch.isalnum() or ch in "-_./:=\\" for ch in value):
        return value
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    _write_text(path, json.dumps(dict(payload), indent=2, sort_keys=True) + "\n")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
