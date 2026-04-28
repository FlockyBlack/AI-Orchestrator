import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "1.0"
DECISION_TYPE = "AUTOPILOT_PROMPT_ROUTING_DECISION"

HEADER_FIELDS = [
    "TARGET_AGENT",
    "TASK_OWNER",
    "TASK_TYPE",
    "CODE_CHANGES_ALLOWED_FOR_RECEIVER",
    "SESSIONS_SPAWN_ALLOWED",
    "RUNTIME_MUTATION_ALLOWED",
    "QUEUE_MUTATION_ALLOWED",
    "GOVERNANCE_MUTATION_ALLOWED",
    "APPROVAL_REQUIRED",
    "MISROUTE_BEHAVIOR",
]

ROUTING_CLASSES = {
    "FLOCKY_VALIDATION_TASK",
    "FLOCKY_GOVERNANCE_TASK",
    "CODEX_CODE_CHANGING_TASK",
    "CODEX_REPAIR_TASK",
    "CHATGPT_PLANNING_TASK",
    "AMBIGUOUS_OR_MISROUTED_TASK",
    "UNSAFE_OR_APPROVAL_REQUIRED_TASK",
}

STRONG_CODEX_SIGNALS = [
    "задание codex",
    "task type: code-changing",
    "task_type: code-changing",
    "implement",
    "create module",
    "modify files",
    "allowed write paths",
    "files_created",
    "files_modified",
    "run pytest",
    "return implementation json",
    "task_owner: codex",
    "target_agent: codex",
    "owner: codex",
]

REPAIR_CODEX_SIGNALS = [
    "task type: repair",
    "task_type: repair",
    "repair task",
    "fix failing tests",
    "bugfix",
    "repair",
]

STRONG_FLOCKY_SIGNALS = [
    "задание flocky",
    "task type: read-only validation",
    "task_type: read-only validation",
    "task type: governance",
    "task_type: governance",
    "read-only validation",
    "governance design",
    "critic check",
    "allowed write paths: none",
    "final json report only in chat/stdout",
    "target_agent: flocky",
    "task_owner: flocky",
]

FLOCKY_GOVERNANCE_SIGNALS = [
    "task type: governance",
    "task_type: governance",
    "governance design",
    "governance-only",
    "policy review",
]

CHATGPT_SIGNALS = [
    "target_agent: chatgpt",
    "task_owner: chatgpt",
    "task type: planning",
    "task_type: planning",
    "brainstorm",
    "outline options",
    "planning task",
]

UNSAFE_TERMS = [
    "sessions_spawn",
    "spawn subagent",
    "external codex execution",
    "runtime wiring",
    "dispatcher changes",
    "run_codex changes",
    "active task mutation",
    "queue mutation",
    "state writeback",
    "final accepted",
    "execution_allowed_now=true",
    "runtime_wiring_allowed=true",
    "wallet",
    "private key",
    "real orders",
    "trading",
]

FORBIDDEN_CONTEXT_MARKERS = [
    "forbidden",
    "stop conditions",
    "blocking conditions",
    "blocking_reasons",
    "must not",
    "no ",
]

REQUEST_MARKERS = [
    "allow",
    "allowed",
    "execute",
    "run",
    "spawn",
    "modify",
    "implement",
    "create",
    "enable",
    "=true",
]


def _normalize_receiver(value: str) -> str:
    normalized = (value or "").strip().lower()
    mapping = {
        "flocky": "Flocky",
        "codex": "Codex",
        "chatgpt": "ChatGPT",
    }
    return mapping.get(normalized, value.strip() if value else "")


def _read_prompt(prompt_path: str) -> str:
    if prompt_path == "-":
        return sys.stdin.read()

    candidate = Path(prompt_path)
    if not candidate.is_absolute():
        candidate = (PROJECT_ROOT / candidate).resolve()
    else:
        candidate = candidate.resolve()
    return candidate.read_text(encoding="utf-8")


def _parse_headers(prompt_text: str):
    headers = {}
    for raw_line in prompt_text.splitlines():
        line = raw_line.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key in HEADER_FIELDS:
            headers[key] = value.strip()
    return headers


def _truthy(value: str) -> bool:
    return str(value).strip().lower() == "true"


def _scan_strong_signals(prompt_text: str):
    lowered = prompt_text.lower()
    detected = []
    for signal in STRONG_CODEX_SIGNALS:
        if signal == "allowed write paths" and "allowed write paths: none" in lowered:
            continue
        if signal in lowered:
            detected.append(f"codex_signal:{signal}")
    for signal in REPAIR_CODEX_SIGNALS:
        if signal in lowered:
            detected.append(f"repair_signal:{signal}")
    for signal in STRONG_FLOCKY_SIGNALS:
        if signal in lowered:
            detected.append(f"flocky_signal:{signal}")
    for signal in FLOCKY_GOVERNANCE_SIGNALS:
        if signal in lowered:
            detected.append(f"governance_signal:{signal}")
    for signal in CHATGPT_SIGNALS:
        if signal in lowered:
            detected.append(f"chatgpt_signal:{signal}")
    return sorted(set(detected))


def _scan_unsafe_signals(prompt_text: str):
    forbidden_context = []
    requested_actions = []
    current_context_forbidden = False

    for raw_line in prompt_text.splitlines():
        line = raw_line.strip().lower()
        if not line:
            current_context_forbidden = False
            continue

        line_forbidden = any(marker in line for marker in FORBIDDEN_CONTEXT_MARKERS)
        if line_forbidden:
            current_context_forbidden = True

        for term in UNSAFE_TERMS:
            if term not in line:
                continue
            if current_context_forbidden or line_forbidden:
                forbidden_context.append(f"forbidden_context_signal:{term}")
            elif ": false" in line or "=false" in line or "not allowed" in line:
                forbidden_context.append(f"forbidden_context_signal:{term}")
            elif any(marker in line for marker in REQUEST_MARKERS):
                requested_actions.append(f"requested_action_signal:{term}")
            else:
                requested_actions.append(f"requested_action_signal:{term}")

    return sorted(set(forbidden_context)), sorted(set(requested_actions))


def _infer_detected_agents(headers, signals):
    target = headers.get("TARGET_AGENT", "")
    owner = headers.get("TASK_OWNER", "")
    task_type = headers.get("TASK_TYPE", "")

    detected_target = target or ""
    detected_owner = owner or ""
    detected_task_type = task_type or ""

    if not detected_target:
        if any(item.startswith("codex_signal:") for item in signals):
            detected_target = "Codex"
        elif any(item.startswith("flocky_signal:") for item in signals):
            detected_target = "Flocky"
        elif any(item.startswith("chatgpt_signal:") for item in signals):
            detected_target = "ChatGPT"

    if not detected_owner:
        if any(item.startswith("codex_signal:") for item in signals):
            detected_owner = "Codex"
        elif any(item.startswith("flocky_signal:") for item in signals):
            detected_owner = "Flocky"
        elif any(item.startswith("chatgpt_signal:") for item in signals):
            detected_owner = "ChatGPT"

    if not detected_task_type:
        if any(item.startswith("repair_signal:") for item in signals):
            detected_task_type = "repair"
        elif any(item.startswith("governance_signal:") for item in signals):
            detected_task_type = "governance"
        elif any(item == "flocky_signal:task type: read-only validation" for item in signals):
            detected_task_type = "read-only validation"
        elif any(item == "chatgpt_signal:task type: planning" for item in signals):
            detected_task_type = "planning"
        elif any(item == "codex_signal:task type: code-changing" for item in signals):
            detected_task_type = "code-changing"

    return detected_target, detected_owner, detected_task_type


def _classify(headers, detected_target, detected_owner, detected_task_type, strong_signals, requested_unsafe):
    lowered_target = detected_target.lower()
    lowered_owner = detected_owner.lower()
    lowered_type = detected_task_type.lower()

    if requested_unsafe:
        return "UNSAFE_OR_APPROVAL_REQUIRED_TASK"

    mixed_owner = (
        lowered_target == "flocky" and lowered_owner == "codex"
    ) or (
        lowered_target == "codex" and lowered_owner == "flocky"
    ) or (
        any(item.startswith("codex_signal:") for item in strong_signals)
        and any(item.startswith("flocky_signal:") for item in strong_signals)
    )
    if mixed_owner:
        return "AMBIGUOUS_OR_MISROUTED_TASK"

    if lowered_target == "codex" or lowered_owner == "codex" or any(item.startswith("codex_signal:") for item in strong_signals):
        if "repair" in lowered_type or any(item.startswith("repair_signal:") for item in strong_signals):
            return "CODEX_REPAIR_TASK"
        return "CODEX_CODE_CHANGING_TASK"

    if lowered_target == "flocky" or lowered_owner == "flocky" or any(item.startswith("flocky_signal:") for item in strong_signals):
        if "governance" in lowered_type or any(item.startswith("governance_signal:") for item in strong_signals):
            return "FLOCKY_GOVERNANCE_TASK"
        return "FLOCKY_VALIDATION_TASK"

    if lowered_target == "chatgpt" or lowered_owner == "chatgpt" or any(item.startswith("chatgpt_signal:") for item in strong_signals):
        return "CHATGPT_PLANNING_TASK"

    return "AMBIGUOUS_OR_MISROUTED_TASK"


def classify_prompt_route(receiver: str, prompt_text: str):
    receiver_agent = _normalize_receiver(receiver)
    headers = _parse_headers(prompt_text)
    strong_signals = _scan_strong_signals(prompt_text)
    forbidden_context_signals, requested_unsafe = _scan_unsafe_signals(prompt_text)
    detected_target, detected_owner, detected_task_type = _infer_detected_agents(headers, strong_signals)
    routing_class = _classify(
        headers=headers,
        detected_target=detected_target,
        detected_owner=detected_owner,
        detected_task_type=detected_task_type,
        strong_signals=strong_signals,
        requested_unsafe=requested_unsafe,
    )

    detected_signals = sorted(set(strong_signals + forbidden_context_signals + requested_unsafe))
    warnings = []
    missing_headers = [field for field in HEADER_FIELDS if field not in headers]
    if missing_headers:
        warnings.extend(f"missing_header:{field}" for field in missing_headers)

    misroute_detected = False
    safe_for_receiver = False
    sessions_spawn_allowed = False
    code_changes_allowed = False
    runtime_mutation_allowed = False
    queue_mutation_allowed = False
    governance_mutation_allowed = False
    requires_human_or_correct_agent = True
    blocking_reasons = []
    required_behavior = "RETURN_ROUTING_MISMATCH"

    if routing_class == "UNSAFE_OR_APPROVAL_REQUIRED_TASK":
        required_behavior = "BLOCK_UNSAFE_OR_APPROVAL_REQUIRED"
        blocking_reasons.extend(item.replace("requested_action_signal:", "unsafe_requested_action:") for item in requested_unsafe)
    elif routing_class in {"CODEX_CODE_CHANGING_TASK", "CODEX_REPAIR_TASK"}:
        if receiver_agent == "Flocky":
            misroute_detected = True
            required_behavior = "MISROUTED_CODEX_PROMPT_DETECTED"
            blocking_reasons.append("codex_task_received_by_flocky")
            warnings.append("original_prompt_not_executed")
        elif receiver_agent == "Codex":
            safe_for_receiver = not _truthy(headers.get("APPROVAL_REQUIRED", "true"))
            code_changes_allowed = safe_for_receiver
            requires_human_or_correct_agent = not safe_for_receiver
            required_behavior = "BLOCK_UNSAFE_OR_APPROVAL_REQUIRED" if requires_human_or_correct_agent else "RETURN_ROUTING_MISMATCH"
            if requires_human_or_correct_agent:
                blocking_reasons.append("approval_required_before_code_changes")
        else:
            misroute_detected = True
            required_behavior = "RETURN_ROUTING_MISMATCH"
            blocking_reasons.append("routing_target_mismatch")
    elif routing_class == "FLOCKY_VALIDATION_TASK":
        if receiver_agent == "Flocky":
            safe_for_receiver = True
            requires_human_or_correct_agent = False
            required_behavior = "PROCEED_READ_ONLY_VALIDATION"
        else:
            misroute_detected = True
            required_behavior = "RETURN_ROUTING_MISMATCH"
            blocking_reasons.append("routing_target_mismatch")
    elif routing_class == "FLOCKY_GOVERNANCE_TASK":
        if receiver_agent == "Flocky":
            safe_for_receiver = True
            requires_human_or_correct_agent = False
            required_behavior = "PROCEED_GOVERNANCE_DESIGN"
        else:
            misroute_detected = True
            required_behavior = "RETURN_ROUTING_MISMATCH"
            blocking_reasons.append("routing_target_mismatch")
    elif routing_class == "CHATGPT_PLANNING_TASK":
        if receiver_agent == "ChatGPT":
            safe_for_receiver = True
            requires_human_or_correct_agent = False
        else:
            misroute_detected = True
            required_behavior = "RETURN_ROUTING_MISMATCH"
            blocking_reasons.append("routing_target_mismatch")
    else:
        misroute_detected = True
        required_behavior = "RETURN_ROUTING_MISMATCH"
        blocking_reasons.append("mixed_or_ambiguous_routing_signals")

    if receiver_agent == "Flocky":
        sessions_spawn_allowed = False
        code_changes_allowed = False
        runtime_mutation_allowed = False
        queue_mutation_allowed = False
        governance_mutation_allowed = False

    if headers.get("SESSIONS_SPAWN_ALLOWED", "").strip().lower() == "true":
        blocking_reasons.append("sessions_spawn_not_allowed_by_guardrail")
        safe_for_receiver = False
        requires_human_or_correct_agent = True
        required_behavior = "BLOCK_UNSAFE_OR_APPROVAL_REQUIRED"
        routing_class = "UNSAFE_OR_APPROVAL_REQUIRED_TASK"

    decision = {
        "type": DECISION_TYPE,
        "schema_version": SCHEMA_VERSION,
        "receiver_agent": receiver_agent,
        "detected_target_agent": detected_target or "unknown",
        "detected_task_owner": detected_owner or "unknown",
        "detected_task_type": detected_task_type or "unknown",
        "routing_class": routing_class,
        "misroute_detected": misroute_detected,
        "safe_for_receiver_to_execute": safe_for_receiver,
        "sessions_spawn_allowed": sessions_spawn_allowed,
        "code_changes_allowed_for_receiver": code_changes_allowed,
        "runtime_mutation_allowed": runtime_mutation_allowed,
        "queue_mutation_allowed": queue_mutation_allowed,
        "governance_mutation_allowed": governance_mutation_allowed,
        "requires_human_or_correct_agent": requires_human_or_correct_agent,
        "required_behavior": required_behavior,
        "detected_signals": sorted(set(detected_signals)),
        "blocking_reasons": sorted(set(blocking_reasons)),
        "warnings": sorted(set(warnings)),
    }
    return decision


def classify_prompt_route_path(receiver: str, prompt_path: str):
    return classify_prompt_route(receiver=receiver, prompt_text=_read_prompt(prompt_path))


def load_schema():
    schema_path = PROJECT_ROOT / "codex_auto" / "autopilot" / "autopilot_prompt_route_decision.schema.v1.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Classify a prompt into a deterministic Autopilot routing decision.")
    parser.add_argument("--receiver", required=True)
    parser.add_argument("--prompt-path", required=True, help="Path to prompt text or '-' for stdin.")
    args = parser.parse_args(argv)

    try:
        decision = classify_prompt_route_path(receiver=args.receiver, prompt_path=args.prompt_path)
    except OSError as exc:
        print(json.dumps({"type": DECISION_TYPE, "schema_version": SCHEMA_VERSION, "error": str(exc)}, separators=(",", ":")))
        return 1

    print(json.dumps(decision, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
