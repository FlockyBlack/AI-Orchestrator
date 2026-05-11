from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .codex_executor_contract import CodexExecutionPacket, validate_execution_result_envelope


DEFAULT_CODEX_CLI_EXECUTOR_CONFIG = {
    "enabled": False,
    "codex_command": "codex",
    "mode": "cli",
    "working_directory_mode": "repo_root",
    "result_contract": "result_json_file",
    "result_json_relative_path": "agent_tasks/generated/<plan_id>/<run_id>/codex_packets/<task_id>/codex_result.json",
    "timeout_seconds": 1800,
    "max_steps_per_invocation": 1,
    "allow_network": False,
    "allow_browser": False,
    "allow_auth": False,
    "allow_real_trading": False,
    "require_clean_worktree": False,
    "write_logs": True,
}


@dataclass(frozen=True)
class CodexCliExecutorConfig:
    enabled: bool = False
    codex_command: str | tuple[str, ...] = "codex"
    mode: str = "cli"
    working_directory_mode: str = "repo_root"
    result_contract: str = "result_json_file"
    result_json_relative_path: str = DEFAULT_CODEX_CLI_EXECUTOR_CONFIG["result_json_relative_path"]
    timeout_seconds: int = 1800
    max_steps_per_invocation: int = 1
    allow_network: bool = False
    allow_browser: bool = False
    allow_auth: bool = False
    allow_real_trading: bool = False
    require_clean_worktree: bool = False
    write_logs: bool = True
    config_path: str = ""
    config_file_exists: bool = True

    @classmethod
    def from_dict(
        cls,
        payload: Mapping[str, Any],
        *,
        config_path: str | Path = "",
        config_file_exists: bool = True,
    ) -> "CodexCliExecutorConfig":
        merged = dict(DEFAULT_CODEX_CLI_EXECUTOR_CONFIG)
        merged.update(dict(payload))
        command = merged.get("codex_command", "codex")
        if isinstance(command, list | tuple):
            command_value: str | tuple[str, ...] = tuple(str(part) for part in command if str(part).strip())
        else:
            command_value = str(command or "")
        return cls(
            enabled=bool(merged.get("enabled", False)),
            codex_command=command_value,
            mode=str(merged.get("mode") or "cli"),
            working_directory_mode=str(merged.get("working_directory_mode") or "repo_root"),
            result_contract=str(merged.get("result_contract") or "result_json_file"),
            result_json_relative_path=str(
                merged.get("result_json_relative_path")
                or DEFAULT_CODEX_CLI_EXECUTOR_CONFIG["result_json_relative_path"]
            ),
            timeout_seconds=int(merged.get("timeout_seconds") or 0),
            max_steps_per_invocation=int(merged.get("max_steps_per_invocation") or 0),
            allow_network=bool(merged.get("allow_network", False)),
            allow_browser=bool(merged.get("allow_browser", False)),
            allow_auth=bool(merged.get("allow_auth", False)),
            allow_real_trading=bool(merged.get("allow_real_trading", False)),
            require_clean_worktree=bool(merged.get("require_clean_worktree", False)),
            write_logs=bool(merged.get("write_logs", False)),
            config_path=str(config_path),
            config_file_exists=config_file_exists,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if isinstance(self.codex_command, tuple):
            payload["codex_command"] = list(self.codex_command)
        return payload


@dataclass
class CodexCliInvocationResult:
    status: str
    packet_id: str
    task_id: str
    run_id: str
    plan_id: str
    command: list[str]
    display_command: str
    cwd: str
    prompt_path: str
    packet_path: str
    result_json_path: str
    started_at: str
    ended_at: str
    timeout_seconds: int
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    stdout_log_path: str = ""
    stderr_log_path: str = ""
    invocation_log_path: str = ""
    invocation_markdown_path: str = ""
    codex_invoked: bool = False
    result_json_exists: bool = False
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "codex_cli_invocation_result.v1",
            "status": self.status,
            "packet_id": self.packet_id,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "plan_id": self.plan_id,
            "command": list(self.command),
            "display_command": self.display_command,
            "cwd": self.cwd,
            "prompt_path": self.prompt_path,
            "packet_path": self.packet_path,
            "result_json_path": self.result_json_path,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "timeout_seconds": self.timeout_seconds,
            "exit_code": self.exit_code,
            "stdout_log_path": self.stdout_log_path,
            "stderr_log_path": self.stderr_log_path,
            "invocation_log_path": self.invocation_log_path,
            "invocation_markdown_path": self.invocation_markdown_path,
            "codex_invoked": self.codex_invoked,
            "result_json_exists": self.result_json_exists,
            "stdout_captured": bool(self.stdout_log_path and Path(self.stdout_log_path).exists()),
            "stderr_captured": bool(self.stderr_log_path and Path(self.stderr_log_path).exists()),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
        }


def load_codex_cli_executor_config(path: str | Path) -> CodexCliExecutorConfig:
    config_path = Path(path)
    if not config_path.exists():
        return CodexCliExecutorConfig.from_dict(
            {},
            config_path=config_path,
            config_file_exists=False,
        )
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("Codex CLI executor config must be a JSON object")
    return CodexCliExecutorConfig.from_dict(
        payload,
        config_path=config_path,
        config_file_exists=True,
    )


def validate_codex_cli_executor_config(config: CodexCliExecutorConfig | Mapping[str, Any]) -> dict[str, Any]:
    config_obj = _config(config)
    errors: list[str] = []
    warnings: list[str] = []
    if not config_obj.config_file_exists:
        errors.append(f"Codex CLI executor config file does not exist: {config_obj.config_path or '<unknown>'}")
    if config_obj.enabled is not True:
        errors.append("config.enabled must be true for real Codex CLI invocation")
    if not _command_parts(config_obj.codex_command):
        errors.append("codex_command must be configured")
    if config_obj.mode != "cli":
        errors.append(f"mode must be cli, got: {config_obj.mode}")
    if config_obj.working_directory_mode != "repo_root":
        errors.append(f"working_directory_mode must be repo_root, got: {config_obj.working_directory_mode}")
    if config_obj.result_contract != "result_json_file":
        errors.append(f"result_contract must be result_json_file, got: {config_obj.result_contract}")
    result_path = Path(config_obj.result_json_relative_path)
    if not config_obj.result_json_relative_path.strip():
        errors.append("result_json_relative_path must be configured")
    if result_path.is_absolute():
        errors.append("result_json_relative_path must be relative, not absolute")
    if any(part == ".." for part in result_path.parts):
        errors.append("result_json_relative_path must not contain parent traversal")
    if config_obj.timeout_seconds <= 0:
        errors.append("timeout_seconds must be greater than zero")
    if config_obj.max_steps_per_invocation != 1:
        errors.append("max_steps_per_invocation must be 1 for the first real Codex executor")
    if config_obj.allow_network:
        errors.append("allow_network must be false")
    if config_obj.allow_browser:
        errors.append("allow_browser must be false")
    if config_obj.allow_auth:
        errors.append("allow_auth must be false")
    if config_obj.allow_real_trading:
        errors.append("allow_real_trading must be false")
    if not config_obj.write_logs:
        errors.append("write_logs must be true so stdout/stderr/invocation logs are captured")
    if config_obj.require_clean_worktree:
        warnings.append("require_clean_worktree is enabled; uncommitted or untracked files will block invocation")
    return {
        "valid": not errors,
        "safety_ok": not errors,
        "errors": list(dict.fromkeys(errors)),
        "warnings": list(dict.fromkeys(warnings)),
        "config": config_obj.to_dict(),
    }


def build_codex_cli_command(
    packet: CodexExecutionPacket | Mapping[str, Any],
    config: CodexCliExecutorConfig | Mapping[str, Any],
) -> list[str]:
    packet_obj = _packet(packet)
    config_obj = _config(config)
    base = _command_parts(config_obj.codex_command)
    if not base:
        return []
    command_name = Path(base[0]).name.lower()
    if command_name in {"codex", "codex.exe", "codex.cmd", "codex.bat"}:
        return [
            *base,
            "exec",
            "--cd",
            str(_working_directory(packet_obj, config_obj)),
            "--color",
            "never",
            "-",
        ]
    return [
        *base,
        "exec",
        "--cd",
        str(_working_directory(packet_obj, config_obj)),
        "--prompt-file",
        str(packet_obj.prompt_path),
        "--result-json",
        str(result_json_path_for_packet(packet_obj, config_obj)),
        "--packet-path",
        str(_packet_path(packet_obj)),
    ]


def invoke_codex_cli(
    packet: CodexExecutionPacket | Mapping[str, Any],
    config: CodexCliExecutorConfig | Mapping[str, Any],
    timeout_seconds: int,
) -> CodexCliInvocationResult:
    packet_obj = _packet(packet)
    config_obj = _config(config)
    started = _utc_iso()
    packet_dir = _packet_dir(packet_obj)
    result_path = result_json_path_for_packet(packet_obj, config_obj)
    result_path.parent.mkdir(parents=True, exist_ok=True)
    log_paths = _invocation_log_paths(packet_obj)
    command = build_codex_cli_command(packet_obj, config_obj)
    cwd = _working_directory(packet_obj, config_obj)
    errors: list[str] = []
    warnings: list[str] = []

    validation = validate_codex_cli_executor_config(config_obj)
    errors.extend(validation["errors"])
    warnings.extend(validation["warnings"])
    executable_error = _executable_error(command)
    if executable_error:
        errors.append(executable_error)
    if config_obj.require_clean_worktree:
        clean_error = _clean_worktree_error(cwd)
        if clean_error:
            errors.append(clean_error)

    prompt_text = _prepare_invocation_prompt(packet_obj, config_obj, result_path)
    if errors:
        result = CodexCliInvocationResult(
            status="blocked",
            packet_id=packet_obj.packet_id,
            task_id=packet_obj.task_id,
            run_id=packet_obj.run_id,
            plan_id=packet_obj.plan_id,
            command=command,
            display_command=_format_command(command),
            cwd=str(cwd),
            prompt_path=packet_obj.prompt_path,
            packet_path=str(_packet_path(packet_obj)),
            result_json_path=str(result_path),
            started_at=started,
            ended_at=_utc_iso(),
            timeout_seconds=timeout_seconds,
            stdout_log_path=str(log_paths["stdout"]),
            stderr_log_path=str(log_paths["stderr"]),
            invocation_log_path=str(log_paths["json"]),
            invocation_markdown_path=str(log_paths["markdown"]),
            result_json_exists=result_path.exists(),
            errors=tuple(dict.fromkeys(errors)),
            warnings=tuple(dict.fromkeys(warnings)),
        )
        write_invocation_log(result)
        return result

    env = dict(os.environ)
    env.update(
        {
            "AI_ORCHESTRATOR_CODEX_PROMPT_PATH": str(packet_obj.prompt_path),
            "AI_ORCHESTRATOR_CODEX_PACKET_PATH": str(_packet_path(packet_obj)),
            "AI_ORCHESTRATOR_CODEX_RESULT_PATH": str(result_path),
            "AI_ORCHESTRATOR_CODEX_TASK_ID": packet_obj.task_id,
            "AI_ORCHESTRATOR_CODEX_RUN_ID": packet_obj.run_id,
            "AI_ORCHESTRATOR_CODEX_PLAN_ID": packet_obj.plan_id,
            "AI_ORCHESTRATOR_CODEX_PACKET_ID": packet_obj.packet_id,
        }
    )
    start_time = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            input=prompt_text,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = _coerce_output(exc.stdout)
        stderr = _coerce_output(exc.stderr)
        if stderr:
            stderr += "\n"
        stderr += f"Timed out after {timeout_seconds} seconds."
        result = CodexCliInvocationResult(
            status="failed",
            packet_id=packet_obj.packet_id,
            task_id=packet_obj.task_id,
            run_id=packet_obj.run_id,
            plan_id=packet_obj.plan_id,
            command=command,
            display_command=_format_command(command),
            cwd=str(cwd),
            prompt_path=packet_obj.prompt_path,
            packet_path=str(_packet_path(packet_obj)),
            result_json_path=str(result_path),
            started_at=started,
            ended_at=_utc_iso(),
            timeout_seconds=timeout_seconds,
            exit_code=None,
            stdout=stdout,
            stderr=stderr,
            stdout_log_path=str(log_paths["stdout"]),
            stderr_log_path=str(log_paths["stderr"]),
            invocation_log_path=str(log_paths["json"]),
            invocation_markdown_path=str(log_paths["markdown"]),
            codex_invoked=True,
            result_json_exists=result_path.exists(),
            errors=(f"Codex CLI timed out after {timeout_seconds} seconds",),
            warnings=tuple(dict.fromkeys(warnings)),
        )
        write_invocation_log(result)
        return result
    except OSError as exc:
        result = CodexCliInvocationResult(
            status="blocked",
            packet_id=packet_obj.packet_id,
            task_id=packet_obj.task_id,
            run_id=packet_obj.run_id,
            plan_id=packet_obj.plan_id,
            command=command,
            display_command=_format_command(command),
            cwd=str(cwd),
            prompt_path=packet_obj.prompt_path,
            packet_path=str(_packet_path(packet_obj)),
            result_json_path=str(result_path),
            started_at=started,
            ended_at=_utc_iso(),
            timeout_seconds=timeout_seconds,
            stdout_log_path=str(log_paths["stdout"]),
            stderr_log_path=str(log_paths["stderr"]),
            invocation_log_path=str(log_paths["json"]),
            invocation_markdown_path=str(log_paths["markdown"]),
            result_json_exists=result_path.exists(),
            errors=(f"failed to invoke Codex CLI: {exc}",),
            warnings=tuple(dict.fromkeys(warnings)),
        )
        write_invocation_log(result)
        return result

    elapsed = time.monotonic() - start_time
    if completed.returncode == 0:
        status = "completed"
        errors_out: tuple[str, ...] = ()
    elif _looks_codex_exec_unavailable(completed.stderr):
        status = "blocked"
        errors_out = ("Codex CLI is available, but the configured command/subcommand appears unavailable",)
    else:
        status = "failed"
        errors_out = (f"Codex CLI exited with code {completed.returncode}",)
    result = CodexCliInvocationResult(
        status=status,
        packet_id=packet_obj.packet_id,
        task_id=packet_obj.task_id,
        run_id=packet_obj.run_id,
        plan_id=packet_obj.plan_id,
        command=command,
        display_command=_format_command(command),
        cwd=str(cwd),
        prompt_path=packet_obj.prompt_path,
        packet_path=str(_packet_path(packet_obj)),
        result_json_path=str(result_path),
        started_at=started,
        ended_at=_utc_iso(),
        timeout_seconds=timeout_seconds,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        stdout_log_path=str(log_paths["stdout"]),
        stderr_log_path=str(log_paths["stderr"]),
        invocation_log_path=str(log_paths["json"]),
        invocation_markdown_path=str(log_paths["markdown"]),
        codex_invoked=True,
        result_json_exists=result_path.exists(),
        errors=errors_out,
        warnings=tuple([*dict.fromkeys(warnings), f"elapsed_seconds={elapsed:.3f}"]),
    )
    write_invocation_log(result)
    return result


def collect_codex_result(
    packet: CodexExecutionPacket | Mapping[str, Any],
    config: CodexCliExecutorConfig | Mapping[str, Any],
) -> dict[str, Any]:
    packet_obj = _packet(packet)
    config_obj = _config(config)
    result_path = result_json_path_for_packet(packet_obj, config_obj)
    if not result_path.exists():
        return {
            "status": "missing",
            "result_json_path": str(result_path),
            "exists": False,
            "payload": None,
            "validation": None,
            "errors": [f"Codex result JSON was not written at expected path: {result_path}"],
            "warnings": [],
        }
    try:
        payload = json.loads(result_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "status": "invalid",
            "result_json_path": str(result_path),
            "exists": True,
            "payload": None,
            "validation": None,
            "errors": [f"Codex result JSON is invalid: {exc}"],
            "warnings": [],
        }
    if not isinstance(payload, Mapping):
        return {
            "status": "invalid",
            "result_json_path": str(result_path),
            "exists": True,
            "payload": None,
            "validation": None,
            "errors": ["Codex result JSON must be an object"],
            "warnings": [],
        }
    validation = validate_execution_result_envelope(payload, packet_obj).to_dict()
    return {
        "status": "found" if validation["valid"] else "invalid",
        "result_json_path": str(result_path),
        "exists": True,
        "payload": dict(payload),
        "validation": validation,
        "errors": list(validation["errors"]),
        "warnings": list(validation["warnings"]),
    }


def write_invocation_log(result: CodexCliInvocationResult) -> dict[str, Any]:
    stdout_path = Path(result.stdout_log_path) if result.stdout_log_path else _packet_dir_from_path(result.prompt_path) / "codex_cli_stdout.log"
    stderr_path = Path(result.stderr_log_path) if result.stderr_log_path else _packet_dir_from_path(result.prompt_path) / "codex_cli_stderr.log"
    json_path = Path(result.invocation_log_path) if result.invocation_log_path else _packet_dir_from_path(result.prompt_path) / "codex_cli_invocation.json"
    markdown_path = (
        Path(result.invocation_markdown_path)
        if result.invocation_markdown_path
        else _packet_dir_from_path(result.prompt_path) / "codex_cli_invocation.md"
    )
    _write_text(stdout_path, result.stdout)
    _write_text(stderr_path, result.stderr)
    result.stdout_log_path = str(stdout_path)
    result.stderr_log_path = str(stderr_path)
    result.invocation_log_path = str(json_path)
    result.invocation_markdown_path = str(markdown_path)
    result.result_json_exists = Path(result.result_json_path).exists() if result.result_json_path else False
    payload = result.to_dict()
    _write_json(json_path, payload)
    _write_text(markdown_path, _render_invocation_markdown(payload))
    return payload


def result_json_path_for_packet(
    packet: CodexExecutionPacket | Mapping[str, Any],
    config: CodexCliExecutorConfig | Mapping[str, Any],
) -> Path:
    packet_obj = _packet(packet)
    config_obj = _config(config)
    rendered = _render_result_relative_path(config_obj.result_json_relative_path, packet_obj)
    relative_path = Path(rendered)
    if relative_path.is_absolute():
        return relative_path
    queue_root = _queue_root_from_packet(packet_obj)
    if queue_root and relative_path.parts and relative_path.parts[0].lower() == queue_root.name.lower():
        return queue_root.parent.joinpath(*relative_path.parts)
    repo_root = Path(packet_obj.repo_root or ".").resolve(strict=False)
    return repo_root / relative_path


def _config(config: CodexCliExecutorConfig | Mapping[str, Any]) -> CodexCliExecutorConfig:
    if isinstance(config, CodexCliExecutorConfig):
        return config
    return CodexCliExecutorConfig.from_dict(config)


def _packet(packet: CodexExecutionPacket | Mapping[str, Any]) -> CodexExecutionPacket:
    if isinstance(packet, CodexExecutionPacket):
        return packet
    return CodexExecutionPacket.from_dict(packet)


def _command_parts(command: str | tuple[str, ...]) -> list[str]:
    if isinstance(command, tuple):
        return [str(part) for part in command if str(part).strip()]
    text = str(command or "").strip()
    if not text:
        return []
    if os.name == "nt":
        return [_strip_outer_quotes(part) for part in shlex.split(text, posix=False)]
    return shlex.split(text)


def _strip_outer_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _working_directory(packet: CodexExecutionPacket, config: CodexCliExecutorConfig) -> Path:
    if config.working_directory_mode != "repo_root":
        return Path(".").resolve(strict=False)
    return Path(packet.repo_root or ".").resolve(strict=False)


def _packet_dir(packet: CodexExecutionPacket) -> Path:
    return Path(packet.prompt_path).parent if packet.prompt_path else Path(packet.state_path).parent / "codex_packets" / packet.task_id


def _packet_dir_from_path(prompt_path: str | Path) -> Path:
    return Path(prompt_path).parent if str(prompt_path) else Path(".")


def _packet_path(packet: CodexExecutionPacket) -> Path:
    return _packet_dir(packet) / "packet.json"


def _queue_root_from_packet(packet: CodexExecutionPacket) -> Path | None:
    state_path = Path(packet.state_path)
    parts = state_path.parts
    index = -1
    for candidate_index, part in enumerate(parts):
        if part != "generated":
            continue
        if len(parts) > candidate_index + 2 and parts[candidate_index + 1] == packet.plan_id and parts[candidate_index + 2] == packet.run_id:
            index = candidate_index
            break
    if index <= 0:
        return None
    return Path(*parts[:index])


def _render_result_relative_path(template: str, packet: CodexExecutionPacket) -> str:
    return (
        template.replace("<plan_id>", packet.plan_id)
        .replace("<run_id>", packet.run_id)
        .replace("<task_id>", packet.task_id)
        .replace("<packet_id>", packet.packet_id)
    )


def _prepare_invocation_prompt(
    packet: CodexExecutionPacket,
    config: CodexCliExecutorConfig,
    result_path: Path,
) -> str:
    prompt_path = Path(packet.prompt_path)
    prompt_text = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
    marker = "## Real Codex CLI Result Contract"
    if marker not in prompt_text:
        prompt_text = "\n".join(
            [
                prompt_text.rstrip(),
                "",
                marker,
                "",
                f"- Write the final result JSON file to: `{result_path}`",
                "- The executor will reject missing, malformed, unsafe, or mismatched result JSON.",
                "- Do not wait for manual copy/paste. Write the JSON file before exiting.",
                "- The same path is also available in `AI_ORCHESTRATOR_CODEX_RESULT_PATH`.",
                "",
            ]
        )
        _write_text(prompt_path, prompt_text)
    return prompt_text


def _invocation_log_paths(packet: CodexExecutionPacket) -> dict[str, Path]:
    packet_dir = _packet_dir(packet)
    return {
        "stdout": packet_dir / "codex_cli_stdout.log",
        "stderr": packet_dir / "codex_cli_stderr.log",
        "json": packet_dir / "codex_cli_invocation.json",
        "markdown": packet_dir / "codex_cli_invocation.md",
    }


def _executable_error(command: list[str]) -> str:
    if not command:
        return "codex_command is not configured"
    executable = command[0]
    if Path(executable).exists():
        return ""
    if shutil.which(executable):
        return ""
    return f"Codex CLI executable was not found or configured command is missing: {executable}"


def _clean_worktree_error(cwd: Path) -> str:
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(cwd),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"failed to inspect git worktree cleanliness: {exc}"
    if completed.returncode != 0:
        return f"failed to inspect git worktree cleanliness: {completed.stderr.strip()}"
    if completed.stdout.strip():
        return "require_clean_worktree is true and git status is not clean"
    return ""


def _format_command(argv: list[str]) -> str:
    return subprocess.list2cmdline([str(part) for part in argv])


def _coerce_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _looks_codex_exec_unavailable(stderr: str) -> bool:
    text = stderr.lower()
    markers = (
        "unrecognized subcommand",
        "unknown command",
        "invalid subcommand",
        "no such subcommand",
        "command not found",
    )
    return any(marker in text for marker in markers)


def _render_invocation_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        f"# Real Codex CLI Invocation: {report.get('task_id', '')}",
        "",
        f"- status: `{report.get('status', '')}`",
        f"- exit_code: `{report.get('exit_code')}`",
        f"- command: `{report.get('display_command', '')}`",
        f"- cwd: `{report.get('cwd', '')}`",
        f"- prompt_path: `{report.get('prompt_path', '')}`",
        f"- packet_path: `{report.get('packet_path', '')}`",
        f"- result_json_path: `{report.get('result_json_path', '')}`",
        f"- stdout_log_path: `{report.get('stdout_log_path', '')}`",
        f"- stderr_log_path: `{report.get('stderr_log_path', '')}`",
        f"- result_json_exists: `{report.get('result_json_exists')}`",
        "",
    ]
    errors = list(report.get("errors", []))
    warnings = list(report.get("warnings", []))
    if errors:
        lines.extend(["## Errors", ""])
        lines.extend(f"- {error}" for error in errors)
        lines.append("")
    if warnings:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
        lines.append("")
    lines.extend(
        [
            "## Safety",
            "",
            "This adapter is operator-invoked and bounded to one task packet per Codex process. It does not create a daemon, scheduler, browser automation, wallet/signing flow, trading endpoint call, authenticated endpoint call, OpenRouter call, or Polymarket API call.",
            "",
        ]
    )
    return "\n".join(lines)


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    _write_text(path, json.dumps(dict(payload), indent=2, sort_keys=True) + "\n")


def _write_text(path: Path, content: str) -> None:
    target = _io_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _io_path(path: Path) -> Path:
    if os.name != "nt":
        return path
    resolved = path.resolve(strict=False)
    text = str(resolved)
    if text.startswith("\\\\?\\"):
        return resolved
    return Path("\\\\?\\" + text)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
