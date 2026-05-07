import argparse
import json
import sys
from json import JSONDecodeError
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import validate_llm_analysis_artifacts as validator  # noqa: E402


MANUAL_PROMPT_VERSION = "manual_llm_prompt.v1"
DETERMINISTIC_GENERATED_AT = "deterministic-manual-llm-prompt.v1"

DEFAULT_PACKET_PATH = validator.DEFAULT_PACKET_PATH
DEFAULT_OUT_MD_PATH = validator.LLM_DIR / "manual_llm_prompt.v1.md"

FORBIDDEN_OUTPUT_CONSTRAINTS = (
    "numeric likelihood estimates",
    "abbreviated value terms",
    "value-comparison language",
    "scoring or rating labels",
    "outcome selection",
    "betting guidance",
    "order sizing",
    "price targets",
    "execution instructions",
    "wallet/private-key/credential handling",
    "certainty claims",
)


class ManualPromptExportError(Exception):
    def __init__(self, errors):
        super().__init__("manual LLM prompt export failed validation")
        self.errors = errors


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Export a deterministic manual paste-in LLM prompt from a safe PMBOT packet."
    )
    parser.add_argument("--packet", default=str(DEFAULT_PACKET_PATH.relative_to(ROOT)))
    parser.add_argument("--out-md", default=str(DEFAULT_OUT_MD_PATH.relative_to(ROOT)))
    return parser.parse_args(argv)


def _resolve_path(path):
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return ROOT / candidate


def _display_path(path):
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def _load_json_artifact(path, artifact):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), []
    except FileNotFoundError:
        return None, [
            {
                "code": f"{artifact}_file_missing",
                "path": _display_path(path),
                "message": f"{artifact} JSON file was not found.",
            }
        ]
    except JSONDecodeError as exc:
        return None, [
            {
                "code": f"{artifact}_json_malformed",
                "path": _display_path(path),
                "message": f"{artifact} JSON is malformed at line {exc.lineno}, column {exc.colno}.",
            }
        ]
    except OSError as exc:
        return None, [
            {
                "code": f"{artifact}_load_error",
                "path": _display_path(path),
                "message": f"{artifact} JSON could not be loaded: {exc.__class__.__name__}.",
            }
        ]


def _load_schema(path, artifact):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), []
    except (OSError, JSONDecodeError) as exc:
        return None, [
            {
                "code": f"{artifact}_schema_load_error",
                "path": _display_path(path),
                "message": f"{artifact} schema could not be loaded: {exc.__class__.__name__}.",
            }
        ]


def _validation_from_load_errors(errors):
    return {
        "status": "rejected",
        "errors": errors,
        "warnings": [],
    }


def _load_validated_packet(packet_path):
    packet_path = _resolve_path(packet_path)
    packet_schema, packet_schema_errors = _load_schema(validator.PACKET_SCHEMA_PATH, "packet")
    packet_payload, packet_load_errors = _load_json_artifact(packet_path, "packet")

    if packet_load_errors or packet_schema_errors:
        packet_validation = _validation_from_load_errors(packet_load_errors + packet_schema_errors)
    else:
        packet_validation = validator.validate_packet_payload(packet_payload, packet_schema)

    packet_validation = {
        "status": packet_validation["status"],
        "errors": packet_validation["errors"],
        "warnings": packet_validation["warnings"],
        "artifact_paths": {
            "packet": _display_path(packet_path),
            "packet_schema": _display_path(validator.PACKET_SCHEMA_PATH),
        },
    }
    if packet_validation["status"] != "accepted":
        raise ManualPromptExportError(packet_validation["errors"])
    return packet_payload, packet_validation


def _json_block(payload):
    return json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True)


def render_manual_prompt(packet_path=DEFAULT_PACKET_PATH):
    packet_path = _resolve_path(packet_path)
    packet_payload, packet_validation = _load_validated_packet(packet_path)
    response_schema = json.loads(validator.RESPONSE_SCHEMA_PATH.read_text(encoding="utf-8"))
    constraints = "\n".join(f"- Do not include {item}." for item in FORBIDDEN_OUTPUT_CONSTRAINTS)
    required_sections = "\n".join(f"- {section}" for section in validator.ALLOWED_RESPONSE_SECTIONS)

    lines = [
        "# PMBOT Manual LLM Paste-In Prompt v1",
        "",
        "## Offline Boundary",
        (
            "This is offline analysis only and not trading advice. The packet below is sanitized local PMBOT "
            "review context. Use it only to draft review-supporting notes for a human operator."
        ),
        "",
        "PMBOT is not calling an LLM service from code. A human operator manually pasted this prompt into an LLM UI.",
        "",
        "## Output Contract",
        "Return only strict JSON matching `llm_analysis_response_schema.v1.json`.",
        "Return exactly one raw JSON object.",
        "The first character must be `{` and the last character must be `}`.",
        "Do not wrap the JSON in Markdown. Do not use ```json fences or any other code fences.",
        "Do not include prose before or after the JSON object. Any Markdown fencing makes the response invalid.",
        "Use the packet_id from the packet. Use contract_version `llm_analysis_response.v1`.",
        "",
        "Required response sections:",
        required_sections,
        "",
        "## Forbidden Output Constraints",
        constraints,
        "",
        "Also do not include market decisions, side selection, trade instructions, autonomous actions, or claims of certainty.",
        "",
        "## Response Schema",
        "```json",
        _json_block(response_schema),
        "```",
        "",
        "## Safe LLM Analysis Packet",
        "Use only this packet content. Do not infer from unstated external data.",
        "",
        "```json",
        _json_block(packet_payload),
        "```",
        "",
        "## Final Instruction",
        (
            "Produce one JSON object that validates against the response schema and remains within the offline, "
            "manual-review-only boundary. Acceptance is operator-review readiness only, never trading approval."
        ),
        "",
    ]
    return "\n".join(lines), packet_validation


def export_manual_prompt(packet_path=DEFAULT_PACKET_PATH, out_md_path=DEFAULT_OUT_MD_PATH):
    prompt, packet_validation = render_manual_prompt(packet_path)
    out_md_path = _resolve_path(out_md_path)
    out_md_path.parent.mkdir(parents=True, exist_ok=True)
    out_md_path.write_text(prompt, encoding="utf-8")
    return {
        "status": "accepted",
        "manual_prompt_version": MANUAL_PROMPT_VERSION,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "packet_path": packet_validation["artifact_paths"]["packet"],
        "out_md_path": _display_path(out_md_path),
        "packet_validation": packet_validation,
        "safety_flags": dict(validator.SAFETY_FLAGS),
    }


def main(argv):
    args = _parse_args(argv)
    try:
        result = export_manual_prompt(args.packet, args.out_md)
    except ManualPromptExportError as exc:
        result = {
            "status": "rejected",
            "manual_prompt_version": MANUAL_PROMPT_VERSION,
            "generated_at": DETERMINISTIC_GENERATED_AT,
            "packet_path": _display_path(_resolve_path(args.packet)),
            "out_md_path": _display_path(_resolve_path(args.out_md)),
            "errors": exc.errors,
            "warnings": [],
            "safety_flags": dict(validator.SAFETY_FLAGS),
        }
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
