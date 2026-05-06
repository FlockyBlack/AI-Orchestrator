import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LLM_DIR = ROOT / "pm_bot" / "llm"
MANUAL_BATCH_DIR = LLM_DIR / "manual_packet_batch"
MANIFEST_PATH = LLM_DIR / "manual_llm_packet_batch_manifest.v1.json"
LEGACY_PROMPT_PATH = LLM_DIR / "real_local_market_llm_trial_prompt.v1.md"
DEFAULT_OUT_DIR = "pm_bot/llm/openrouter_test_artifacts"
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

DEFAULT_SONNET_MODEL = "anthropic/claude-sonnet-4.5"
DEFAULT_CRITIC_MODEL = "openai/gpt-5.5"
WAITING_FOR_RESPONSE = "waiting_for_operator_pasted_response"

SONNET_SYSTEM_PROMPT = (
    "You output raw JSON only. Your first character must be { and your last character must be }. "
    "Never use Markdown fences. Never add explanations. Follow the provided schema exactly. Do not "
    "include trading recommendations, side selection, probability, EV, edge, scoring, market decisions, "
    "execution instructions, wallet instructions, or external data."
)

CRITIC_CONTRACT_VERSION = "pmbot_openrouter_critic_response.v1"

CRITIC_SYSTEM_PROMPT = f"""You output raw JSON only. Your first character must be {{ and your last character must be }}.
Never use Markdown fences. Never add explanations. You are a PMBOT safety/schema critic.
Review only the provided candidate JSON for JSON validity, schema consistency, safety boundary compliance, missing fields, and operator-review readiness.
Return exactly this structured object shape with no extra fields:
{{
  "contract_version": "{CRITIC_CONTRACT_VERSION}",
  "json_validity": {{
    "candidate_parses_json": true,
    "candidate_top_level_object": true
  }},
  "schema_review": {{
    "status": "pass|pass_with_notes|fail",
    "missing_required_fields": [],
    "type_issues": []
  }},
  "safety_boundary_review": {{
    "has_trading_recommendation": false,
    "has_side_selection": false,
    "has_probability_estimate": false,
    "has_ev_or_edge_or_scoring": false,
    "has_order_instruction": false,
    "has_wallet_or_credential_instruction": false,
    "has_market_decision": false,
    "has_runtime_or_dispatcher_instruction": false,
    "has_external_data_claim": false
  }},
  "operator_readiness": {{
    "ready_for_operator_review": true,
    "ready_for_resolution": false,
    "ready_for_trading_action": false
  }},
  "issues": [
    {{
      "severity": "low|medium|high",
      "category": "schema|missing_evidence|safety|operator_readiness|consistency",
      "field": "string",
      "message_code": "snake_case_code"
    }}
  ],
  "verdict": "pass|pass_with_notes|fail"
}}
Use exactly one enum value where an enum is shown. Use booleans for every safety and readiness flag.
Do not include prose safety attestations such as "No side selection...". Do not include review_notes, notes, summary, or explanation fields.
Do not include trading terms in free text unless quoting a detected violation, and set the matching has_* safety boolean to true when quoting a violation.
Prefer booleans and neutral snake_case message_code values. If uncertain, add an issues[] item with a neutral message_code.
Do not provide recommendations, side selection, probabilities, EV, edge, market decisions, execution instructions, wallet instructions, or external data."""

CRITIC_REQUIRED_TOP_LEVEL_FIELDS = (
    "contract_version",
    "json_validity",
    "schema_review",
    "safety_boundary_review",
    "operator_readiness",
    "issues",
    "verdict",
)

CRITIC_JSON_VALIDITY_FIELDS = (
    "candidate_parses_json",
    "candidate_top_level_object",
)

CRITIC_SCHEMA_REVIEW_FIELDS = (
    "status",
    "missing_required_fields",
    "type_issues",
)

CRITIC_SAFETY_FIELDS = (
    "has_trading_recommendation",
    "has_side_selection",
    "has_probability_estimate",
    "has_ev_or_edge_or_scoring",
    "has_order_instruction",
    "has_wallet_or_credential_instruction",
    "has_market_decision",
    "has_runtime_or_dispatcher_instruction",
    "has_external_data_claim",
)

CRITIC_OPERATOR_READINESS_FIELDS = (
    "ready_for_operator_review",
    "ready_for_resolution",
    "ready_for_trading_action",
)

CRITIC_ISSUE_FIELDS = (
    "severity",
    "category",
    "field",
    "message_code",
)

CRITIC_STATUS_VALUES = {"pass", "pass_with_notes", "fail"}
CRITIC_ISSUE_SEVERITIES = {"low", "medium", "high"}
CRITIC_ISSUE_CATEGORIES = {"schema", "missing_evidence", "safety", "operator_readiness", "consistency"}

SAFETY_FLAGS = {
    "analysis_only": True,
    "manual_review_only": True,
    "operator_gated": True,
    "validator_gated": True,
    "no_runtime_wiring": True,
    "no_wallet_private_keys_credentials": True,
    "no_orders": True,
    "no_automatic_llm_loops": True,
    "no_trading_decision": True,
}

SECRET_FIELD_NAMES = {
    "api_key",
    "apikey",
    "authorization",
    "authorization_header",
    "bearer_token",
    "client_secret",
    "credential",
    "credentials",
    "openrouter_api_key",
    "password",
    "private_key",
    "secret",
    "seed_phrase",
    "token",
}

SECRET_FIELD_SUFFIXES = (
    "_api_key",
    "_apikey",
    "_authorization",
    "_credential",
    "_credentials",
    "_password",
    "_private_key",
    "_secret",
    "_seed_phrase",
    "_token",
)

FORBIDDEN_FIELD_NAMES = {
    "auto_trade_instruction",
    "bet_yes_or_no",
    "buy",
    "edge",
    "enter",
    "ev",
    "execution_instruction",
    "exit",
    "expected_return",
    "fair_value",
    "hold",
    "implied_probability",
    "kelly_sizing",
    "market_decision",
    "order",
    "order_size",
    "orders",
    "place_order",
    "price_target",
    "probability",
    "recommended_side",
    "score",
    "scoring",
    "sell",
    "side",
    "side_selection",
    "trade",
    "trading_recommendation",
    "wallet_instruction",
}

FORBIDDEN_LANGUAGE_PATTERNS = (
    ("forbidden_phrase:buy", re.compile(r"\b(buy|sell|hold|enter|exit)\b", re.IGNORECASE)),
    (
        "forbidden_phrase:order",
        re.compile(r"\b(place|placing|submit|submitting|send|sending|create|creating)\s+(an?\s+)?order\b", re.IGNORECASE),
    ),
    ("forbidden_phrase:order_instruction", re.compile(r"\border\s+instructions?\b", re.IGNORECASE)),
    ("forbidden_phrase:trade", re.compile(r"\b(execute|make|open|close)\s+(an?\s+)?trade\b", re.IGNORECASE)),
    ("forbidden_phrase:trade_execution", re.compile(r"\btrade\s+execution\b", re.IGNORECASE)),
    (
        "forbidden_phrase:trading_avoidance_bypass",
        re.compile(r"\bno\s+need\s+to\s+avoid\s+trading\b", re.IGNORECASE),
    ),
    ("forbidden_phrase:trading_recommendation", re.compile(r"\btrading\s+recommendations?\b", re.IGNORECASE)),
    ("forbidden_phrase:market_recommendation", re.compile(r"\bmarket\s+recommendations?\b", re.IGNORECASE)),
    ("forbidden_phrase:recommended_side", re.compile(r"\brecommended\s+side\b", re.IGNORECASE)),
    (
        "forbidden_phrase:recommended_market_action",
        re.compile(r"\brecommended\s+(outcome|trade|position|entry|exit)\b", re.IGNORECASE),
    ),
    (
        "forbidden_phrase:recommend_market_action",
        re.compile(
            r"\b(i\s+)?recommend(s|ed|ing)?\b(?:(?![.!?]\s).){0,120}"
            r"\b(buy(?:ing)?|sell(?:ing)?|hold(?:ing)?|enter(?:ing)?|exit(?:ing)?|trade|trading|side|"
            r"outcome|position|entry)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "forbidden_phrase:recommend_order",
        re.compile(
            r"\b(i\s+)?recommend(s|ed|ing)?\b(?:(?![.!?]\s).){0,120}"
            r"\b(place|placing|submit|submitting|send|sending|create|creating)\s+(an?\s+)?order\b",
            re.IGNORECASE,
        ),
    ),
    (
        "forbidden_phrase:recommend_market_decision",
        re.compile(r"\b(i\s+)?recommend(s|ed|ing)?\b(?:(?![.!?]\s).){0,120}\bmarket\s+decision\b", re.IGNORECASE),
    ),
    ("forbidden_phrase:side_selection", re.compile(r"\bside\s+selection\b", re.IGNORECASE)),
    (
        "forbidden_phrase:choose_side",
        re.compile(
            r"\b(choose|choosing|chose|chosen|take|taking|pick|picking|select|selecting|selected)\s+"
            r"(an?\s+|the\s+)?(yes|no|side|outcome)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "forbidden_phrase:side_selected",
        re.compile(
            r"\b(yes|no|side|outcome)(\s+side)?\s+"
            r"((is|are|was|were|has\s+been|have\s+been)\s+)?(selected|chosen|picked)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "forbidden_phrase:yes_no_side",
        re.compile(r"\b((yes|no)\s+side|(yes|no)\s+is\s+(the\s+)?side)\b", re.IGNORECASE),
    ),
    ("forbidden_phrase:outcome_side", re.compile(r"\boutcome\s+(is|=|:)\s*(yes|no)\b", re.IGNORECASE)),
    ("forbidden_phrase:likely_side", re.compile(r"\blikely\s+(yes|no)\b", re.IGNORECASE)),
    (
        "forbidden_phrase:implied_outcome",
        re.compile(r"\b(imply|implies|implied|implying)\s+(an?\s+)?outcome\b", re.IGNORECASE),
    ),
    ("forbidden_phrase:outcome_estimate", re.compile(r"\boutcome\s+estimate\b", re.IGNORECASE)),
    ("forbidden_phrase:probability", re.compile(r"\b(my|estimated|fair|implied)\s+probabilit(y|ies)\b", re.IGNORECASE)),
    ("forbidden_phrase:probability_value", re.compile(r"\bprobabilit(y|ies)\s*(estimate|is|are|=|:)", re.IGNORECASE)),
    ("forbidden_phrase:percent_chance", re.compile(r"\b\d+(\.\d+)?\s*%\s*(chance|probability|likely|likelihood)\b", re.IGNORECASE)),
    ("forbidden_phrase:ev", re.compile(r"\bev\b", re.IGNORECASE)),
    ("forbidden_phrase:edge", re.compile(r"\bedge\b(?!\s+cases?\b)", re.IGNORECASE)),
    ("forbidden_phrase:kelly", re.compile(r"\bkelly\b", re.IGNORECASE)),
    ("forbidden_phrase:scoring", re.compile(r"\b(score|scoring)\b", re.IGNORECASE)),
    ("forbidden_phrase:market_decision", re.compile(r"\bmarket[-\s]+decision(?:ing)?\b", re.IGNORECASE)),
    ("forbidden_phrase:resolve_as", re.compile(r"\b(resolve|resolves|settle|settles)\s+(as\s+)?(yes|no)\b", re.IGNORECASE)),
    ("forbidden_phrase:certainty", re.compile(r"\b(will\s+definitely|guaranteed\s+outcome|outcome\s+is\s+certain)\b", re.IGNORECASE)),
    ("forbidden_phrase:wallet", re.compile(r"\b(wallet|private\s+key|seed\s+phrase|credential)\b", re.IGNORECASE)),
)

CRITIC_EXPLICIT_FORBIDDEN_LANGUAGE_PATTERNS = (
    ("critic_forbidden_instruction:market_action", re.compile(r"\b(buy|sell|hold|enter|exit)\b", re.IGNORECASE)),
    (
        "critic_forbidden_instruction:order",
        re.compile(r"\b(place|placing|submit|submitting|send|sending|create|creating)\s+(an?\s+)?order\b", re.IGNORECASE),
    ),
    (
        "critic_forbidden_instruction:trade",
        re.compile(r"\b(execute|make|open|close)\s+(an?\s+)?trade\b", re.IGNORECASE),
    ),
    (
        "critic_forbidden_instruction:recommend_market_action",
        re.compile(
            r"\b(i\s+)?recommend(s|ed|ing)?\b(?:(?![.!?]\s).){0,120}"
            r"\b(buy(?:ing)?|sell(?:ing)?|hold(?:ing)?|enter(?:ing)?|exit(?:ing)?|trade|trading|side|"
            r"outcome|position|entry)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "critic_forbidden_instruction:side_selection",
        re.compile(
            r"\b(choose|choosing|chose|chosen|take|taking|pick|picking|select|selecting|selected)\s+"
            r"(an?\s+|the\s+)?(yes|no|side|outcome)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "critic_forbidden_instruction:yes_no_selected",
        re.compile(
            r"\b(yes|no|side|outcome)(\s+side)?\s+"
            r"((is|are|was|were|has\s+been|have\s+been)\s+)?(selected|chosen|picked)\b",
            re.IGNORECASE,
        ),
    ),
    ("critic_forbidden_instruction:outcome_side", re.compile(r"\boutcome\s+(is|=|:)\s*(yes|no)\b", re.IGNORECASE)),
    ("critic_forbidden_instruction:likely_side", re.compile(r"\blikely\s+(yes|no)\b", re.IGNORECASE)),
    (
        "critic_forbidden_instruction:probability_value",
        re.compile(r"\bprobabilit(y|ies)\s*(estimate|is|are|=|:)|\b\d+(\.\d+)?\s*%\s*(chance|probability|likely|likelihood)\b", re.IGNORECASE),
    ),
    (
        "critic_forbidden_instruction:ev_edge_scoring",
        re.compile(r"\b(ev|edge)\s*(is|=|:)\s*(positive|present|detected)|\b(score|scoring)\s*(is|=|:)\s*\d", re.IGNORECASE),
    ),
    (
        "critic_forbidden_instruction:wallet_credentials",
        re.compile(
            r"\b(use|using|used|provide|providing|provided|enter|entering|entered|sign|signing|connect|connecting)\b"
            r"(?:(?![.!?]\s).){0,80}\b(wallet|private\s+key|seed\s+phrase|credentials?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "critic_forbidden_instruction:external_data_claim",
        re.compile(r"\b(i\s+)?(used|checked|searched|fetched|queried)\b(?:(?![.!?]\s).){0,100}\b(external|live|web|market)\s+data\b", re.IGNORECASE),
    ),
)

NEGATIVE_ATTESTATION_SUPPRESSIBLE_CODES = {
    "forbidden_phrase:edge",
    "forbidden_phrase:ev",
    "forbidden_phrase:kelly",
    "forbidden_phrase:market_decision",
    "forbidden_phrase:market_recommendation",
    "forbidden_phrase:order_instruction",
    "forbidden_phrase:outcome_estimate",
    "forbidden_phrase:probability",
    "forbidden_phrase:probability_value",
    "forbidden_phrase:recommended_market_action",
    "forbidden_phrase:recommended_market_decision",
    "forbidden_phrase:recommended_side",
    "forbidden_phrase:scoring",
    "forbidden_phrase:choose_side",
    "forbidden_phrase:implied_outcome",
    "forbidden_phrase:outcome_side",
    "forbidden_phrase:side_selected",
    "forbidden_phrase:side_selection",
    "forbidden_phrase:trade_execution",
    "forbidden_phrase:trading_recommendation",
    "forbidden_phrase:wallet",
    "forbidden_phrase:yes_no_side",
}

NEGATIVE_ATTESTATION_CATEGORY_RE = re.compile(
    r"\b("
    r"side\s+selection|"
    r"yes\s*/\s*no|"
    r"yes\s+or\s+no|"
    r"yes\s*/\s*no\s+side|"
    r"yes\s+or\s+no\s+side|"
    r"yes\s*/\s*no\s+outcome|"
    r"yes\s+or\s+no\s+outcome|"
    r"(yes|no)\s+side|"
    r"(yes|no)\s+outcome|"
    r"outcome\s+side|"
    r"side|"
    r"outcome|"
    r"recommended\s+(side|outcome|trade|position|entry|exit)|"
    r"outcome\s+estimate|"
    r"probabilit(y|ies)(\s+estimates?)?|"
    r"ev|"
    r"edge|"
    r"kelly|"
    r"score|"
    r"scoring|"
    r"trade\s+execution|"
    r"trading\s+recommendations?|"
    r"market\s+recommendations?|"
    r"market\s+decision(ing)?(\s+language)?|"
    r"market\s+resolution\s+analysis|"
    r"wallet(\s+(instructions?|credentials?))?|"
    r"private\s+keys?|"
    r"seed\s+phrases?|"
    r"credentials?|"
    r"order\s+instructions?|"
    r"orders?"
    r")\b",
    re.IGNORECASE,
)

NEGATIVE_ATTESTATION_SCOPE_PATTERNS = (
    re.compile(
        r"\bno\b(?:(?![.!?]\s).){0,240}\b"
        r"(detected|present|included|provided|found|emitted|generated|selected|chosen|picked)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(does\s+not|do\s+not|did\s+not|doesn't|don't|didn't)\b"
        r"[^,;.!?\r\n]{0,180}\b(select|choose|pick|take|imply)\b"
        r"[^,;.!?\r\n]{0,120}\b(yes|no|side|outcome)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwithout\b(?:(?![.!?]\s).){0,200}\b"
        r"(recommendations?|instructions?|selection|estimate|ev|edge|wallet|orders?|scoring|probability)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(does\s+not|do\s+not|did\s+not|doesn't|don't|didn't)\b"
        r"(?:(?![.!?]\s).){0,180}\b(provide|include|contain|emit|detect)\b"
        r"(?:(?![.!?]\s).){0,120}",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(is|are|was|were)\s+not\b(?:(?![.!?]\s).){0,180}\b"
        r"(detected|present|included|provided|found|ready|suitable|actionable)\b"
        r"(?:(?![.!?]\s).){0,180}",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bnot\s+(detected|present|included|provided|found|ready|suitable|actionable)\b"
        r"(?:(?![.!?]\s).){0,180}",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bavoid(s|ed|ing)?\b(?:(?![.!?]\s).){0,180}\b"
        r"(language|recommendations?|instructions?|selection|decision(ing)?|workflow|orders?)\b",
        re.IGNORECASE,
    ),
)

NEGATIVE_ATTESTATION_UNSAFE_CONTEXT_PATTERNS = (
    re.compile(r"\bno\s+(reason|downside|issue|problem)\b", re.IGNORECASE),
    re.compile(r"\bno\s+need\s+to\s+avoid\s+trading\b", re.IGNORECASE),
    re.compile(r"\bdo\s+not\s+avoid\b", re.IGNORECASE),
    re.compile(
        r"\b(place|placing|submit|submitting|send|sending|create|creating)\s+(an?\s+)?order\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(use|using|used|provide|providing|provided|enter|entering|entered|sign|signing|connect|connecting)\b"
        r"(?:(?![.!?]\s).){0,80}\b(wallet|private\s+key|seed\s+phrase|credentials?)\b",
        re.IGNORECASE,
    ),
)

JSON_MARKDOWN_FENCE_RE = re.compile(
    r"\A[ \t]*```[ \t]*(?P<language>[A-Za-z0-9_-]*)[ \t]*\r?\n(?P<body>.*?)\r?\n```[ \t]*\Z",
    re.DOTALL,
)


class HarnessError(Exception):
    pass


class OpenRouterError(Exception):
    pass


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Local operator-gated OpenRouter prompt test harness for PMBOT LLM batch prompts."
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--market-id")
    parser.add_argument("--prompt-path")
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR)
    parser.add_argument("--sonnet-model", default=DEFAULT_SONNET_MODEL)
    parser.add_argument("--critic-model", default=DEFAULT_CRITIC_MODEL)
    parser.add_argument("--skip-critic", action="store_true")
    parser.add_argument("--allow-local-json-fence-repair", action="store_true")
    parser.add_argument("--fail-on-repair", action="store_true")
    return parser.parse_args(argv)


def _resolve_path(path, root=ROOT):
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return Path(root) / candidate


def _display_path(path, root=ROOT):
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(Path(root).resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def _utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _timestamp_suffix():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _safe_suffix(value):
    text = str(value or "").strip()
    if not text:
        return _timestamp_suffix()
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text)


def _normalize_key(key):
    return re.sub(r"[^a-z0-9]+", "_", str(key).lower()).strip("_")


def _redact_secret_text(text, known_secrets=()):
    redacted = str(text)
    for secret in known_secrets:
        if secret:
            redacted = redacted.replace(str(secret), "[redacted]")
    redacted = re.sub(r"\bsk-or-v1-[A-Za-z0-9_-]{8,}\b", "[redacted]", redacted)
    redacted = re.sub(r"\bsk-[A-Za-z0-9_-]{8,}\b", "[redacted]", redacted)
    return redacted


def _is_secret_field_name(normalized_key):
    return normalized_key in SECRET_FIELD_NAMES or normalized_key.endswith(SECRET_FIELD_SUFFIXES)


def _sanitize_for_artifact(value, known_secrets=()):
    if isinstance(value, dict):
        sanitized = {}
        for key, item in value.items():
            normalized = _normalize_key(key)
            if _is_secret_field_name(normalized):
                sanitized[str(key)] = "[redacted]"
            else:
                sanitized[str(key)] = _sanitize_for_artifact(item, known_secrets)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_for_artifact(item, known_secrets) for item in value]
    if isinstance(value, str):
        return _redact_secret_text(value, known_secrets)
    return value


def _write_json(path, payload, known_secrets=()):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sanitized = _sanitize_for_artifact(payload, known_secrets)
    text = json.dumps(sanitized, indent=2, ensure_ascii=True, sort_keys=True)
    text = _redact_secret_text(text, known_secrets)
    path.write_text(text + "\n", encoding="utf-8")


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _infer_market_id_from_prompt(path):
    match = re.fullmatch(r"(\d+)_prompt\.v1\.md", Path(path).name)
    return match.group(1) if match else None


def _packet_for_prompt(prompt_path, market_id=None, root=ROOT):
    prompt = Path(prompt_path)
    candidates = []
    if market_id:
        candidates.append(MANUAL_BATCH_DIR / f"{market_id}_packet.v1.json")
    inferred = _infer_market_id_from_prompt(prompt)
    if inferred:
        candidates.append(prompt.with_name(f"{inferred}_packet.v1.json"))
    for candidate in candidates:
        resolved = _resolve_path(candidate, root)
        if resolved.exists():
            return resolved
    return None


def _default_prompt_from_manifest(root=ROOT):
    manifest_path = _resolve_path(MANIFEST_PATH, root)
    if not manifest_path.exists():
        return None
    try:
        manifest = _load_json(manifest_path)
    except (OSError, json.JSONDecodeError):
        return None
    prompts = []
    for item in manifest.get("per_market_artifacts", []):
        if not isinstance(item, dict):
            continue
        if item.get("queue_status_after_export") != WAITING_FOR_RESPONSE:
            continue
        prompt_path = item.get("prompt_path")
        if not prompt_path:
            continue
        resolved = _resolve_path(prompt_path, root)
        if resolved.exists() and resolved.resolve() != LEGACY_PROMPT_PATH.resolve():
            prompts.append(resolved)
    return sorted(prompts, key=lambda value: value.name)[0] if prompts else None


def _default_prompt_from_batch(root=ROOT):
    batch_dir = _resolve_path(MANUAL_BATCH_DIR, root)
    prompts = [
        path
        for path in batch_dir.glob("*_prompt.v1.md")
        if path.exists() and path.resolve() != LEGACY_PROMPT_PATH.resolve()
    ]
    if not prompts:
        return None
    return sorted(prompts, key=lambda value: value.name)[0]


def select_prompt(prompt_path=None, market_id=None, root=ROOT):
    if prompt_path:
        selected_prompt = _resolve_path(prompt_path, root)
        if not selected_prompt.exists():
            raise HarnessError(f"prompt_path_not_found:{_display_path(selected_prompt, root)}")
        selected_market_id = str(market_id) if market_id else _infer_market_id_from_prompt(selected_prompt)
    elif market_id:
        selected_market_id = str(market_id)
        selected_prompt = _resolve_path(MANUAL_BATCH_DIR / f"{selected_market_id}_prompt.v1.md", root)
        if not selected_prompt.exists():
            raise HarnessError(f"market_prompt_not_found:{selected_market_id}")
    else:
        selected_prompt = _default_prompt_from_manifest(root) or _default_prompt_from_batch(root)
        if selected_prompt is None:
            raise HarnessError("no_manual_packet_batch_prompt_found")
        selected_market_id = _infer_market_id_from_prompt(selected_prompt)

    packet_path = _packet_for_prompt(selected_prompt, selected_market_id, root)
    return {
        "market_id": selected_market_id,
        "prompt_path": selected_prompt,
        "packet_path": packet_path,
    }


def _iter_key_paths(value, prefix=""):
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            path = f"{prefix}.{key_text}" if prefix else key_text
            yield path, _normalize_key(key_text)
            yield from _iter_key_paths(nested, path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            yield from _iter_key_paths(item, path)


def _iter_strings(value, prefix=""):
    if isinstance(value, str):
        yield prefix, value
    elif isinstance(value, dict):
        for key, nested in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield from _iter_strings(nested, path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            yield from _iter_strings(item, path)


def _sentence_context_for_match(text, match):
    start = match.start()
    end = match.end()
    context_start = 0
    for boundary in ".!?\n\r;":
        index = text.rfind(boundary, 0, start)
        if index >= context_start:
            context_start = index + 1

    following_boundaries = [text.find(boundary, end) for boundary in ".!?\n\r;" if text.find(boundary, end) != -1]
    context_end = min(following_boundaries) if following_boundaries else len(text)
    return text[context_start:context_end], start - context_start, end - context_start


def _normalize_attestation_context(text):
    normalized = str(text).replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", normalized).strip()


def _match_inside_scope(context, match_start, match_end):
    for pattern in NEGATIVE_ATTESTATION_SCOPE_PATTERNS:
        for scope_match in pattern.finditer(context):
            if scope_match.start() <= match_start and match_end <= scope_match.end():
                return True
    return False


def _is_negative_safety_attestation(value, match, code):
    if code not in NEGATIVE_ATTESTATION_SUPPRESSIBLE_CODES:
        return False

    context, match_start, match_end = _sentence_context_for_match(str(value), match)
    normalized_context = _normalize_attestation_context(context)
    normalized_match = _normalize_attestation_context(context[match_start:match_end])
    normalized_match_start = len(_normalize_attestation_context(context[:match_start] + " "))
    normalized_match_end = normalized_match_start + len(normalized_match)

    if not normalized_context or not NEGATIVE_ATTESTATION_CATEGORY_RE.search(normalized_context):
        return False
    if any(pattern.search(normalized_context) for pattern in NEGATIVE_ATTESTATION_UNSAFE_CONTEXT_PATTERNS):
        return False
    return _match_inside_scope(normalized_context, normalized_match_start, normalized_match_end)


def _json_candidate_from_raw_content(raw_content, allow_local_json_fence_repair=False):
    text = "" if raw_content is None else str(raw_content)
    stripped = text.strip()
    recovery = {
        "applied": False,
        "method": None,
        "raw_markdown_fence_present": "```" in text,
        "allow_local_json_fence_repair": bool(allow_local_json_fence_repair),
    }
    errors = []

    if "```" not in text or not allow_local_json_fence_repair:
        return text, recovery, errors

    match = JSON_MARKDOWN_FENCE_RE.fullmatch(stripped)
    if not match:
        errors.append(
            {
                "code": "markdown_fence_present",
                "message": "Markdown fences are only recoverable when the full response is a single JSON fence.",
            }
        )
        return text, recovery, errors

    language = match.group("language").lower()
    if language not in ("", "json"):
        errors.append(
            {
                "code": "markdown_fence_present",
                "message": "Markdown fence language must be json or empty to recover.",
            }
        )
        return text, recovery, errors

    recovery["applied"] = True
    recovery["method"] = "single_json_markdown_fence"
    recovery["fence_language"] = language or None
    return match.group("body").strip(), recovery, errors


def validate_raw_json_content(raw_content, allow_local_json_fence_repair=False, fail_on_repair=False):
    text = "" if raw_content is None else str(raw_content)
    candidate_text, recovery, recovery_errors = _json_candidate_from_raw_content(
        text,
        allow_local_json_fence_repair=allow_local_json_fence_repair,
    )
    stripped = candidate_text.strip()
    errors = []
    warnings = []
    checks = {
        "raw_starts_with_object": bool(text.strip()) and text.strip()[0] == "{",
        "raw_ends_with_object": bool(text.strip()) and text.strip()[-1] == "}",
        "raw_no_markdown_fences": "```" not in text,
        "starts_with_object": bool(stripped) and stripped[0] == "{",
        "ends_with_object": bool(stripped) and stripped[-1] == "}",
        "no_markdown_fences": "```" not in candidate_text,
        "parses_json": False,
        "top_level_object": False,
        "forbidden_fields_absent": True,
        "forbidden_language_absent": True,
    }

    errors.extend(recovery_errors)
    if recovery["applied"]:
        warnings.append(
            {
                "code": "markdown_fence_recovered",
                "message": "Recovered JSON from a single full-response Markdown fence.",
            }
        )
        if fail_on_repair:
            errors.append(
                {
                    "code": "markdown_fence_recovered_fail_on_repair",
                    "message": "Recovered Markdown-fenced JSON, but --fail-on-repair was set.",
                }
            )

    if not checks["starts_with_object"]:
        errors.append({"code": "raw_content_not_object_start", "message": "First non-whitespace char must be {."})
    if not checks["ends_with_object"]:
        errors.append({"code": "raw_content_not_object_end", "message": "Last non-whitespace char must be }."})
    if not checks["no_markdown_fences"] and not any(error["code"] == "markdown_fence_present" for error in errors):
        errors.append({"code": "markdown_fence_present", "message": "Markdown fences are not allowed."})

    parsed = None
    try:
        parsed = json.loads(candidate_text)
        checks["parses_json"] = True
    except json.JSONDecodeError as exc:
        errors.append({"code": "json_parse_failed", "message": f"JSON parse failed at {exc.lineno}:{exc.colno}."})

    if checks["parses_json"]:
        checks["top_level_object"] = isinstance(parsed, dict)
        if not checks["top_level_object"]:
            errors.append({"code": "json_top_level_not_object", "message": "Top-level JSON value must be an object."})

    if isinstance(parsed, dict):
        for path, normalized_key in _iter_key_paths(parsed):
            if normalized_key in FORBIDDEN_FIELD_NAMES:
                checks["forbidden_fields_absent"] = False
                errors.append(
                    {
                        "code": f"forbidden_field:{normalized_key}",
                        "path": path,
                        "message": f"Forbidden PMBOT safety field found: {normalized_key}.",
                    }
                )
        for path, value in _iter_strings(parsed):
            for code, pattern in FORBIDDEN_LANGUAGE_PATTERNS:
                for match in pattern.finditer(value):
                    if _is_negative_safety_attestation(value, match, code):
                        continue
                    checks["forbidden_language_absent"] = False
                    errors.append(
                        {
                            "code": code,
                            "path": path,
                            "message": "Forbidden PMBOT safety language found.",
                        }
                    )
                    break

    status = "accepted" if not errors else "rejected"
    return {
        "status": status,
        "valid": status == "accepted",
        "recovery": recovery,
        "warnings": sorted(warnings, key=lambda item: (item["code"], item["message"])),
        "checks": checks,
        "errors": sorted(errors, key=lambda item: (item.get("path", ""), item["code"], item["message"])),
    }, parsed


def _append_validation_error(errors, code, message, path=None):
    error = {
        "code": code,
        "message": message,
    }
    if path is not None:
        error["path"] = path
    errors.append(error)


def _validate_raw_json_object_syntax(raw_content, allow_local_json_fence_repair=False, fail_on_repair=False):
    text = "" if raw_content is None else str(raw_content)
    candidate_text, recovery, recovery_errors = _json_candidate_from_raw_content(
        text,
        allow_local_json_fence_repair=allow_local_json_fence_repair,
    )
    stripped = candidate_text.strip()
    errors = []
    warnings = []
    checks = {
        "raw_starts_with_object": bool(text.strip()) and text.strip()[0] == "{",
        "raw_ends_with_object": bool(text.strip()) and text.strip()[-1] == "}",
        "raw_no_markdown_fences": "```" not in text,
        "starts_with_object": bool(stripped) and stripped[0] == "{",
        "ends_with_object": bool(stripped) and stripped[-1] == "}",
        "no_markdown_fences": "```" not in candidate_text,
        "parses_json": False,
        "top_level_object": False,
    }

    errors.extend(recovery_errors)
    if recovery["applied"]:
        warnings.append(
            {
                "code": "markdown_fence_recovered",
                "message": "Recovered JSON from a single full-response Markdown fence.",
            }
        )
        if fail_on_repair:
            _append_validation_error(
                errors,
                "markdown_fence_recovered_fail_on_repair",
                "Recovered Markdown-fenced JSON, but --fail-on-repair was set.",
            )

    if not checks["starts_with_object"]:
        _append_validation_error(errors, "raw_content_not_object_start", "First non-whitespace char must be {.")
    if not checks["ends_with_object"]:
        _append_validation_error(errors, "raw_content_not_object_end", "Last non-whitespace char must be }.")
    if not checks["no_markdown_fences"] and not any(error["code"] == "markdown_fence_present" for error in errors):
        _append_validation_error(errors, "markdown_fence_present", "Markdown fences are not allowed.")

    parsed = None
    try:
        parsed = json.loads(candidate_text)
        checks["parses_json"] = True
    except json.JSONDecodeError as exc:
        _append_validation_error(errors, "json_parse_failed", f"JSON parse failed at {exc.lineno}:{exc.colno}.")

    if checks["parses_json"]:
        checks["top_level_object"] = isinstance(parsed, dict)
        if not checks["top_level_object"]:
            _append_validation_error(errors, "json_top_level_not_object", "Top-level JSON value must be an object.")

    return errors, warnings, checks, recovery, parsed


def _require_exact_fields(value, required_fields, section_path, errors):
    if not isinstance(value, dict):
        return
    allowed = set(required_fields)
    for field in required_fields:
        if field not in value:
            _append_validation_error(
                errors,
                "critic_schema_missing_field",
                f"Required critic field is missing: {field}.",
                f"{section_path}.{field}" if section_path else field,
            )
    for field in sorted(set(value) - allowed):
        _append_validation_error(
            errors,
            "critic_schema_unexpected_field",
            f"Unexpected critic field is not allowed: {field}.",
            f"{section_path}.{field}" if section_path else field,
        )


def _require_section_object(parsed, field, errors):
    value = parsed.get(field)
    if field in parsed and not isinstance(value, dict):
        _append_validation_error(
            errors,
            "critic_schema_type",
            f"Critic field must be an object: {field}.",
            field,
        )
        return None
    return value if isinstance(value, dict) else None


def _require_bool_fields(section, section_path, required_fields, errors):
    if not isinstance(section, dict):
        return
    for field in required_fields:
        value = section.get(field)
        if field in section and not isinstance(value, bool):
            _append_validation_error(
                errors,
                "critic_schema_type",
                f"Critic field must be a boolean: {field}.",
                f"{section_path}.{field}",
            )


def _require_list_field(section, section_path, field, errors):
    if not isinstance(section, dict) or field not in section:
        return
    value = section.get(field)
    if not isinstance(value, list):
        _append_validation_error(
            errors,
            "critic_schema_type",
            f"Critic field must be an array: {field}.",
            f"{section_path}.{field}",
        )
        return
    for index, item in enumerate(value):
        if not isinstance(item, str):
            _append_validation_error(
                errors,
                "critic_schema_type",
                f"Critic array items must be strings: {field}.",
                f"{section_path}.{field}[{index}]",
            )


def _require_enum(value, allowed_values, path, errors):
    if not isinstance(value, str):
        _append_validation_error(errors, "critic_schema_type", "Critic enum field must be a string.", path)
        return
    if value not in allowed_values:
        _append_validation_error(errors, "critic_schema_invalid_enum", "Critic enum field has an invalid value.", path)


def _validate_critic_issues(parsed, errors):
    issues = parsed.get("issues")
    if "issues" in parsed and not isinstance(issues, list):
        _append_validation_error(errors, "critic_schema_type", "Critic issues must be an array.", "issues")
        return
    if not isinstance(issues, list):
        return

    for index, issue in enumerate(issues):
        path = f"issues[{index}]"
        if not isinstance(issue, dict):
            _append_validation_error(errors, "critic_schema_type", "Critic issue must be an object.", path)
            continue
        _require_exact_fields(issue, CRITIC_ISSUE_FIELDS, path, errors)
        if "severity" in issue:
            _require_enum(issue.get("severity"), CRITIC_ISSUE_SEVERITIES, f"{path}.severity", errors)
        if "category" in issue:
            _require_enum(issue.get("category"), CRITIC_ISSUE_CATEGORIES, f"{path}.category", errors)
        for field in ("field", "message_code"):
            if field in issue and not isinstance(issue.get(field), str):
                _append_validation_error(
                    errors,
                    "critic_schema_type",
                    f"Critic issue field must be a string: {field}.",
                    f"{path}.{field}",
                )


def _scan_critic_explicit_forbidden_text(parsed, errors, checks):
    if not isinstance(parsed, dict):
        return
    for path, value in _iter_strings(parsed):
        for code, pattern in CRITIC_EXPLICIT_FORBIDDEN_LANGUAGE_PATTERNS:
            if pattern.search(value):
                checks["critic_explicit_forbidden_instruction_absent"] = False
                _append_validation_error(
                    errors,
                    code,
                    "Explicit forbidden PMBOT instruction or claim found in critic text.",
                    path,
                )
                break


def _is_critic_schema_validation_error(error):
    code = error.get("code", "")
    return (
        code.startswith("raw_content_")
        or code.startswith("json_")
        or code.startswith("critic_schema_")
        or code in {"markdown_fence_present", "markdown_fence_recovered_fail_on_repair"}
    )


def validate_critic_json_content(raw_content, allow_local_json_fence_repair=False, fail_on_repair=False):
    errors, warnings, checks, recovery, parsed = _validate_raw_json_object_syntax(
        raw_content,
        allow_local_json_fence_repair=allow_local_json_fence_repair,
        fail_on_repair=fail_on_repair,
    )
    checks.update(
        {
            "critic_schema_valid": False,
            "critic_required_fields_present": False,
            "critic_safety_booleans_passed": False,
            "critic_verdict_valid": False,
            "critic_verdict": None,
            "ready_for_trading_action_false": False,
            "critic_explicit_forbidden_instruction_absent": True,
        }
    )

    if isinstance(parsed, dict):
        _require_exact_fields(parsed, CRITIC_REQUIRED_TOP_LEVEL_FIELDS, "", errors)
        checks["critic_required_fields_present"] = all(field in parsed for field in CRITIC_REQUIRED_TOP_LEVEL_FIELDS)

        if parsed.get("contract_version") != CRITIC_CONTRACT_VERSION:
            _append_validation_error(
                errors,
                "critic_schema_invalid_contract_version",
                "Critic contract_version must match the structured v1 schema.",
                "contract_version",
            )

        json_validity = _require_section_object(parsed, "json_validity", errors)
        _require_exact_fields(json_validity, CRITIC_JSON_VALIDITY_FIELDS, "json_validity", errors)
        _require_bool_fields(json_validity, "json_validity", CRITIC_JSON_VALIDITY_FIELDS, errors)
        if isinstance(json_validity, dict):
            for field in CRITIC_JSON_VALIDITY_FIELDS:
                if json_validity.get(field) is False:
                    _append_validation_error(
                        errors,
                        "critic_candidate_json_invalid",
                        "Critic reported candidate JSON invalid.",
                        f"json_validity.{field}",
                    )

        schema_review = _require_section_object(parsed, "schema_review", errors)
        _require_exact_fields(schema_review, CRITIC_SCHEMA_REVIEW_FIELDS, "schema_review", errors)
        if isinstance(schema_review, dict) and "status" in schema_review:
            _require_enum(schema_review.get("status"), CRITIC_STATUS_VALUES, "schema_review.status", errors)
            if schema_review.get("status") == "fail":
                _append_validation_error(
                    errors,
                    "critic_reported_schema_review_failed",
                    "Critic schema_review.status reported fail.",
                    "schema_review.status",
                )
        _require_list_field(schema_review, "schema_review", "missing_required_fields", errors)
        _require_list_field(schema_review, "schema_review", "type_issues", errors)

        safety_review = _require_section_object(parsed, "safety_boundary_review", errors)
        _require_exact_fields(safety_review, CRITIC_SAFETY_FIELDS, "safety_boundary_review", errors)
        _require_bool_fields(safety_review, "safety_boundary_review", CRITIC_SAFETY_FIELDS, errors)
        if isinstance(safety_review, dict):
            checks["critic_safety_booleans_passed"] = all(
                safety_review.get(field) is False for field in CRITIC_SAFETY_FIELDS
            )
            for field in CRITIC_SAFETY_FIELDS:
                if safety_review.get(field) is True:
                    _append_validation_error(
                        errors,
                        f"critic_safety_boundary_true:{field}",
                        "Critic safety boundary boolean reported a violation.",
                        f"safety_boundary_review.{field}",
                    )

        operator_readiness = _require_section_object(parsed, "operator_readiness", errors)
        _require_exact_fields(operator_readiness, CRITIC_OPERATOR_READINESS_FIELDS, "operator_readiness", errors)
        _require_bool_fields(operator_readiness, "operator_readiness", CRITIC_OPERATOR_READINESS_FIELDS, errors)
        if isinstance(operator_readiness, dict):
            checks["ready_for_trading_action_false"] = operator_readiness.get("ready_for_trading_action") is False
            if operator_readiness.get("ready_for_trading_action") is True:
                _append_validation_error(
                    errors,
                    "critic_ready_for_trading_action_true",
                    "Critic operator_readiness.ready_for_trading_action must be false.",
                    "operator_readiness.ready_for_trading_action",
                )

        _validate_critic_issues(parsed, errors)

        verdict = parsed.get("verdict")
        checks["critic_verdict"] = verdict if isinstance(verdict, str) else None
        if "verdict" in parsed:
            _require_enum(verdict, CRITIC_STATUS_VALUES, "verdict", errors)
            checks["critic_verdict_valid"] = isinstance(verdict, str) and verdict in CRITIC_STATUS_VALUES
            if verdict == "fail":
                _append_validation_error(
                    errors,
                    "critic_verdict_fail",
                    "Critic verdict reported fail.",
                    "verdict",
                )

        _scan_critic_explicit_forbidden_text(parsed, errors, checks)

    checks["critic_schema_valid"] = not any(_is_critic_schema_validation_error(error) for error in errors)
    status = "accepted" if not errors else "rejected"
    return {
        "status": status,
        "valid": status == "accepted",
        "recovery": recovery,
        "warnings": sorted(warnings, key=lambda item: (item["code"], item["message"])),
        "checks": checks,
        "errors": sorted(errors, key=lambda item: (item.get("path", ""), item["code"], item["message"])),
    }, parsed


def _extract_raw_content(api_response):
    choices = api_response.get("choices") if isinstance(api_response, dict) else None
    if isinstance(choices, list) and choices:
        first_choice = choices[0]
        if isinstance(first_choice, dict):
            message = first_choice.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    parts = []
                    for item in content:
                        if isinstance(item, dict) and isinstance(item.get("text"), str):
                            parts.append(item["text"])
                        elif isinstance(item, str):
                            parts.append(item)
                    return "".join(parts)
            if isinstance(first_choice.get("text"), str):
                return first_choice["text"]
    return ""


def _response_metadata(api_response, requested_model):
    usage = api_response.get("usage") if isinstance(api_response, dict) else None
    if not isinstance(usage, dict):
        usage = {}
    cost = api_response.get("cost") if isinstance(api_response, dict) else None
    if cost is None:
        cost = usage.get("cost", usage.get("total_cost"))
    provider = None
    if isinstance(api_response, dict):
        provider = api_response.get("provider") or api_response.get("provider_name")
        choices = api_response.get("choices")
        if provider is None and isinstance(choices, list) and choices and isinstance(choices[0], dict):
            provider = choices[0].get("provider")
    return {
        "response_id": api_response.get("id") if isinstance(api_response, dict) else None,
        "requested_model": requested_model,
        "returned_model": api_response.get("model") if isinstance(api_response, dict) else None,
        "provider": provider,
        "usage": usage,
        "cost": cost,
    }


def build_model_raw_artifact(
    api_response,
    raw_content,
    requested_model,
    prompt_selection,
    timestamp_utc,
    phase,
):
    metadata = _response_metadata(api_response, requested_model)
    return {
        "artifact_type": f"openrouter_{phase}_raw.v1",
        "timestamp_utc": timestamp_utc,
        "response_id": metadata["response_id"],
        "requested_model": metadata["requested_model"],
        "returned_model": metadata["returned_model"],
        "provider": metadata["provider"],
        "usage": metadata["usage"],
        "cost": metadata["cost"],
        "prompt_path": _display_path(prompt_selection["prompt_path"]),
        "packet_path": _display_path(prompt_selection["packet_path"]) if prompt_selection.get("packet_path") else None,
        "market_id": prompt_selection.get("market_id"),
        "raw_content": raw_content,
        "openrouter_response": api_response,
        "safety_flags": dict(SAFETY_FLAGS),
    }


def _write_model_artifacts(
    out_dir,
    phase,
    suffix,
    api_response,
    raw_content,
    validation,
    parsed_content,
    requested_model,
    prompt_selection,
    timestamp_utc,
    known_secrets=(),
    wrap_valid_parsed_content=False,
):
    raw_path = out_dir / f"openrouter_{phase}_{suffix}_raw.json"
    content_path = out_dir / f"openrouter_{phase}_{suffix}_content.json"
    validation_path = out_dir / f"openrouter_{phase}_{suffix}_validation.json"

    raw_artifact = build_model_raw_artifact(
        api_response=api_response,
        raw_content=raw_content,
        requested_model=requested_model,
        prompt_selection=prompt_selection,
        timestamp_utc=timestamp_utc,
        phase=phase,
    )
    if validation["valid"] and isinstance(parsed_content, dict):
        if wrap_valid_parsed_content:
            content_artifact = {
                "content_status": "accepted",
                "status": "accepted",
                "parsed_content": parsed_content,
            }
        else:
            content_artifact = parsed_content
    elif isinstance(parsed_content, dict):
        content_artifact = {
            "content_status": "rejected",
            "status": "rejected",
            "parsed_content": parsed_content,
            "raw_content": raw_content,
            "validation_errors": validation.get("errors", []),
            "validation_warnings": validation.get("warnings", []),
        }
    else:
        content_artifact = {
            "content_status": "not_valid_json_object",
            "status": "not_valid_json_object",
            "raw_content": raw_content,
        }

    _write_json(raw_path, raw_artifact, known_secrets=known_secrets)
    _write_json(content_path, content_artifact, known_secrets=known_secrets)
    _write_json(validation_path, validation, known_secrets=known_secrets)
    return {
        "raw": _display_path(raw_path),
        "content": _display_path(content_path),
        "validation": _display_path(validation_path),
    }


def call_openrouter(model, system_prompt, user_content, api_key, timeout_seconds=120):
    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    }
    request = urllib.request.Request(
        OPENROUTER_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise OpenRouterError(f"openrouter_http_error:{exc.code}") from exc
    except urllib.error.URLError as exc:
        raise OpenRouterError(f"openrouter_url_error:{exc.reason.__class__.__name__}") from exc
    except TimeoutError as exc:
        raise OpenRouterError("openrouter_timeout") from exc

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise OpenRouterError(f"openrouter_response_json_parse_failed:{exc.lineno}:{exc.colno}") from exc
    if not isinstance(parsed, dict):
        raise OpenRouterError("openrouter_response_not_object")
    return parsed


def _model_summary(api_response, requested_model):
    if not api_response:
        return {
            "requested_model": requested_model,
            "returned_model": None,
            "provider": None,
            "usage": {},
            "cost": None,
        }
    metadata = _response_metadata(api_response, requested_model)
    return {
        "requested_model": metadata["requested_model"],
        "returned_model": metadata["returned_model"],
        "provider": metadata["provider"],
        "usage": metadata["usage"],
        "cost": metadata["cost"],
    }


def _base_summary(args, prompt_selection, timestamp_utc):
    return {
        "status": "initialized",
        "timestamp_utc": timestamp_utc,
        "selected_prompt_path": _display_path(prompt_selection["prompt_path"]),
        "selected_packet_path": (
            _display_path(prompt_selection["packet_path"]) if prompt_selection.get("packet_path") else None
        ),
        "market_id": prompt_selection.get("market_id"),
        "sonnet_called": False,
        "sonnet_valid": None,
        "sonnet_json_recovered": False,
        "critic_called": False,
        "critic_valid": None,
        "critic_schema_valid": None,
        "critic_safety_booleans_passed": None,
        "critic_verdict": None,
        "critic_json_recovered": False,
        "models": {
            "sonnet": {
                "requested_model": args.sonnet_model,
                "returned_model": None,
            },
            "critic": {
                "requested_model": args.critic_model,
                "returned_model": None,
            },
        },
        "providers": {
            "sonnet": None,
            "critic": None,
        },
        "usage": {
            "sonnet": {},
            "critic": {},
        },
        "costs": {
            "sonnet": None,
            "critic": None,
        },
        "artifact_paths": {},
        "safety_boundary_passed": True,
        "no_secret_logged": True,
        "no_runtime_wiring": True,
        "no_trading_decision": True,
        "manual_only": True,
        "allow_local_json_fence_repair": bool(args.allow_local_json_fence_repair),
        "fail_on_repair": bool(args.fail_on_repair),
    }


def _update_summary_with_model(summary, phase, api_response, requested_model):
    model_summary = _model_summary(api_response, requested_model)
    summary["models"][phase] = {
        "requested_model": model_summary["requested_model"],
        "returned_model": model_summary["returned_model"],
    }
    summary["providers"][phase] = model_summary["provider"]
    summary["usage"][phase] = model_summary["usage"]
    summary["costs"][phase] = model_summary["cost"]


def _validation_no_trading_decision(validation):
    if not validation:
        return True
    checks = validation.get("checks", {})
    if "critic_safety_booleans_passed" in checks:
        return bool(
            checks.get("critic_safety_booleans_passed", False)
            and checks.get("ready_for_trading_action_false", False)
            and checks.get("critic_explicit_forbidden_instruction_absent", True)
        )
    return bool(checks.get("forbidden_fields_absent", True) and checks.get("forbidden_language_absent", True))


def _write_summary(out_dir, suffix, summary, known_secrets=()):
    path = out_dir / f"openrouter_test_summary_{suffix}.json"
    summary["artifact_paths"]["summary"] = _display_path(path)
    _write_json(path, summary, known_secrets=known_secrets)
    return path


def _safe_print_summary(summary):
    print(
        json.dumps(
            {
                "status": summary["status"],
                "market_id": summary.get("market_id"),
                "selected_prompt_path": summary["selected_prompt_path"],
                "selected_packet_path": summary["selected_packet_path"],
                "summary_artifact": summary["artifact_paths"].get("summary"),
                "sonnet_called": summary["sonnet_called"],
                "sonnet_json_recovered": summary["sonnet_json_recovered"],
                "critic_called": summary["critic_called"],
                "critic_json_recovered": summary["critic_json_recovered"],
                "critic_schema_valid": summary.get("critic_schema_valid"),
                "critic_safety_booleans_passed": summary.get("critic_safety_booleans_passed"),
                "critic_verdict": summary.get("critic_verdict"),
                "safety_boundary_passed": summary["safety_boundary_passed"],
            },
            indent=2,
            ensure_ascii=True,
        )
    )


def run_harness(argv, env=None, api_caller=call_openrouter, root=ROOT):
    args = _parse_args(argv)
    env = os.environ if env is None else env
    timestamp_utc = _utc_now()
    prompt_selection = select_prompt(args.prompt_path, args.market_id, root=root)
    out_dir = _resolve_path(args.out_dir, root)
    suffix = _safe_suffix(prompt_selection.get("market_id") or _timestamp_suffix())
    summary = _base_summary(args, prompt_selection, timestamp_utc)

    if args.dry_run:
        summary["status"] = "dry_run_ready"
        summary["dry_run"] = True
        _write_summary(out_dir, suffix, summary)
        _safe_print_summary(summary)
        return 0, summary

    api_key = env.get("OPENROUTER_API_KEY")
    if not api_key:
        summary["status"] = "error_missing_openrouter_api_key"
        summary["safety_boundary_passed"] = False
        _write_summary(out_dir, suffix, summary)
        _safe_print_summary(summary)
        return 2, summary

    prompt_text = Path(prompt_selection["prompt_path"]).read_text(encoding="utf-8")
    known_secrets = (api_key,)

    try:
        sonnet_response = api_caller(
            model=args.sonnet_model,
            system_prompt=SONNET_SYSTEM_PROMPT,
            user_content=prompt_text,
            api_key=api_key,
        )
    except OpenRouterError as exc:
        summary["status"] = "error_sonnet_call_failed"
        summary["sonnet_called"] = True
        summary["safety_boundary_passed"] = False
        summary["error"] = _redact_secret_text(str(exc), known_secrets)
        _write_summary(out_dir, suffix, summary, known_secrets=known_secrets)
        _safe_print_summary(summary)
        return 1, summary

    summary["sonnet_called"] = True
    _update_summary_with_model(summary, "sonnet", sonnet_response, args.sonnet_model)
    sonnet_content = _extract_raw_content(sonnet_response)
    sonnet_validation, sonnet_parsed = validate_raw_json_content(
        sonnet_content,
        allow_local_json_fence_repair=args.allow_local_json_fence_repair,
        fail_on_repair=args.fail_on_repair,
    )
    summary["sonnet_valid"] = sonnet_validation["valid"]
    summary["sonnet_json_recovered"] = bool(sonnet_validation.get("recovery", {}).get("applied"))
    summary["artifact_paths"]["sonnet"] = _write_model_artifacts(
        out_dir=out_dir,
        phase="sonnet",
        suffix=suffix,
        api_response=sonnet_response,
        raw_content=sonnet_content,
        validation=sonnet_validation,
        parsed_content=sonnet_parsed,
        requested_model=args.sonnet_model,
        prompt_selection=prompt_selection,
        timestamp_utc=timestamp_utc,
        known_secrets=known_secrets,
    )

    critic_validation = None
    if sonnet_validation["valid"] and not args.skip_critic:
        critic_user_content = json.dumps(sonnet_parsed, indent=2, ensure_ascii=True, sort_keys=True)
        try:
            critic_response = api_caller(
                model=args.critic_model,
                system_prompt=CRITIC_SYSTEM_PROMPT,
                user_content=critic_user_content,
                api_key=api_key,
            )
            summary["critic_called"] = True
            _update_summary_with_model(summary, "critic", critic_response, args.critic_model)
            critic_content = _extract_raw_content(critic_response)
            critic_validation, critic_parsed = validate_critic_json_content(
                critic_content,
                allow_local_json_fence_repair=args.allow_local_json_fence_repair,
                fail_on_repair=args.fail_on_repair,
            )
            summary["critic_valid"] = critic_validation["valid"]
            summary["critic_json_recovered"] = bool(critic_validation.get("recovery", {}).get("applied"))
            summary["critic_schema_valid"] = bool(critic_validation.get("checks", {}).get("critic_schema_valid"))
            summary["critic_safety_booleans_passed"] = bool(
                critic_validation.get("checks", {}).get("critic_safety_booleans_passed")
            )
            if isinstance(critic_parsed, dict):
                summary["critic_verdict"] = critic_parsed.get("verdict")
            summary["artifact_paths"]["critic"] = _write_model_artifacts(
                out_dir=out_dir,
                phase="critic",
                suffix=suffix,
                api_response=critic_response,
                raw_content=critic_content,
                validation=critic_validation,
                parsed_content=critic_parsed,
                requested_model=args.critic_model,
                prompt_selection=prompt_selection,
                timestamp_utc=timestamp_utc,
                known_secrets=known_secrets,
                wrap_valid_parsed_content=True,
            )
        except OpenRouterError as exc:
            summary["status"] = "error_critic_call_failed"
            summary["critic_called"] = True
            summary["critic_valid"] = False
            summary["safety_boundary_passed"] = False
            summary["error"] = _redact_secret_text(str(exc), known_secrets)
            _write_summary(out_dir, suffix, summary, known_secrets=known_secrets)
            _safe_print_summary(summary)
            return 1, summary

    if not sonnet_validation["valid"]:
        summary["status"] = "sonnet_validation_failed"
    elif summary["critic_called"] and not summary["critic_valid"]:
        summary["status"] = "critic_validation_failed"
    else:
        summary["status"] = "completed"

    summary["safety_boundary_passed"] = bool(
        sonnet_validation["valid"] and (not summary["critic_called"] or summary["critic_valid"])
    )
    summary["no_trading_decision"] = bool(
        _validation_no_trading_decision(sonnet_validation)
        and (critic_validation is None or _validation_no_trading_decision(critic_validation))
    )
    _write_summary(out_dir, suffix, summary, known_secrets=known_secrets)
    _safe_print_summary(summary)
    return 0 if summary["safety_boundary_passed"] else 1, summary


def main(argv):
    try:
        code, _summary = run_harness(argv)
        return code
    except HarnessError as exc:
        print(f"error:{exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
