import argparse
import json
import sys
from json import JSONDecodeError
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pm_bot.llm import evaluate_manual_llm_review_quality_gate as quality_gate  # noqa: E402
from pm_bot.llm import validate_llm_analysis_artifacts as validator  # noqa: E402
from pm_bot.llm import validate_manual_llm_paste_in_review as manual_review  # noqa: E402


TASK_ID = "PMBOT-LLM-009-REAL-MANUAL-LLM-TRIAL-OPERATOR-ACCEPTANCE"
CONTRACT_VERSION = "real_manual_llm_trial_operator_acceptance_contract.v1"
ACCEPTANCE_VERSION = "real_manual_llm_trial_operator_acceptance.v1"
ACCEPTANCE_ID = "pmbot-llm-009-real-manual-llm-trial-operator-acceptance"
DETERMINISTIC_GENERATED_AT = "deterministic-real-manual-llm-trial-operator-acceptance.v1"

REAL_LOCAL_MARKET_ARTIFACT = "real_local_market_artifact"
EXAMPLE_FIXTURE_RESPONSE = "example_fixture_response"
ACTUAL_OPERATOR_PASTED_RESPONSE = "actual_operator_pasted_response"
ACCEPTED = "accepted_for_operator_review"
PENDING = "pending_real_manual_response"
REJECTED = "rejected"
BLOCKED = "blocked"

QUALITY_PASS_STATUSES = {"quality_passed", "quality_passed_with_warnings"}
KNOWN_RESPONSE_SOURCE_TYPES = {EXAMPLE_FIXTURE_RESPONSE, ACTUAL_OPERATOR_PASTED_RESPONSE}

DEFAULT_TRIAL_PATH = validator.LLM_DIR / "real_local_market_llm_trial.v1.json"
DEFAULT_PACKET_PATH = validator.LLM_DIR / "real_local_market_llm_trial_packet.v1.json"
DEFAULT_PROMPT_PATH = validator.LLM_DIR / "real_local_market_llm_trial_prompt.v1.md"
DEFAULT_RESPONSE_PATH = validator.LLM_DIR / "real_local_market_llm_trial_response_example.v1.json"
DEFAULT_OUT_JSON_PATH = validator.LLM_DIR / "real_manual_llm_trial_operator_acceptance.v1.json"
DEFAULT_OUT_MD_PATH = validator.LLM_DIR / "real_manual_llm_trial_operator_acceptance.v1.md"

SAFETY_FLAGS = {
    **quality_gate.SAFETY_FLAGS,
    "runtime_wiring": False,
    "network_api": False,
    "llm_api": False,
    "browser_automation": False,
    "prompt_automation": False,
    "credentials_or_wallet": False,
    "real_orders_or_live_trading": False,
    "autonomous_paper_orders": False,
    "probability_ev_scoring_or_edge": False,
    "side_recommendations": False,
    "market_decision_logic": False,
    "truth_evaluation": False,
    "dispatcher_or_run_codex_changed": False,
}

OPERATOR_REQUIRED_ACTIONS_PENDING = [
    "Open pm_bot/llm/real_local_market_llm_trial_prompt.v1.md.",
    "Paste manually into ChatGPT/Claude/Gemini.",
    "Request strict JSON only.",
    "Save the returned JSON to pm_bot/llm/real_local_market_llm_trial_response_operator.v1.json.",
    (
        "Rerun this acceptance script with --response "
        "pm_bot\\llm\\real_local_market_llm_trial_response_operator.v1.json "
        "--response-source-type actual_operator_pasted_response."
    ),
    "Review the acceptance JSON and Markdown outputs.",
]

BOUNDARY_NOTICE = (
    "no API, no LLM API, no browser automation, no prompt automation, no runtime integration, "
    "no trading advice, no truth evaluation, no probability/EV/edge/scoring, no side recommendation, "
    "and no trading execution."
)


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Evaluate deterministic offline operator acceptance for the real manual LLM trial."
    )
    parser.add_argument("--trial", default=str(DEFAULT_TRIAL_PATH.relative_to(ROOT)))
    parser.add_argument("--packet", default=str(DEFAULT_PACKET_PATH.relative_to(ROOT)))
    parser.add_argument("--prompt", default=str(DEFAULT_PROMPT_PATH.relative_to(ROOT)))
    parser.add_argument("--response", default=str(DEFAULT_RESPONSE_PATH.relative_to(ROOT)))
    parser.add_argument("--response-source-type", default=EXAMPLE_FIXTURE_RESPONSE)
    parser.add_argument("--out-json", default=str(DEFAULT_OUT_JSON_PATH.relative_to(ROOT)))
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


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _issue(code, path, message):
    return {"code": code, "path": path, "message": message}


def _load_json_artifact(path, artifact):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), []
    except FileNotFoundError:
        return None, [
            _issue(f"{artifact}_file_missing", _display_path(path), f"{artifact} JSON file was not found.")
        ]
    except JSONDecodeError as exc:
        return None, [
            _issue(
                f"{artifact}_json_malformed",
                _display_path(path),
                f"{artifact} JSON is malformed at line {exc.lineno}, column {exc.colno}.",
            )
        ]
    except OSError as exc:
        return None, [
            _issue(
                f"{artifact}_load_error",
                _display_path(path),
                f"{artifact} JSON could not be loaded: {exc.__class__.__name__}.",
            )
        ]


def _validation_from_load_errors(errors):
    return {"status": "rejected", "errors": errors, "warnings": []}


def _not_run_validation():
    return {"status": "not_run", "errors": [], "warnings": []}


def _stage_messages(stage, messages):
    staged = []
    for message in messages:
        staged.append({"stage": stage, **message})
    return sorted(
        staged,
        key=lambda item: (
            item.get("stage", ""),
            item.get("artifact", ""),
            item.get("check", ""),
            item.get("path", ""),
            item.get("code", ""),
            item.get("message", ""),
        ),
    )


def _extract_used_example_packet_fallback(trial_payload):
    values = []
    if isinstance(trial_payload, dict) and "used_example_packet_fallback" in trial_payload:
        values.append(trial_payload["used_example_packet_fallback"])
    source_selection = trial_payload.get("source_selection") if isinstance(trial_payload, dict) else None
    if isinstance(source_selection, dict) and "used_example_packet_fallback" in source_selection:
        values.append(source_selection["used_example_packet_fallback"])
    if not values:
        return None, []
    if not all(value == values[0] for value in values):
        return values[0], [
            _issue(
                "used_example_packet_fallback_conflict",
                "trial.used_example_packet_fallback",
                "Trial result has conflicting used_example_packet_fallback values.",
            )
        ]
    return values[0], []


def _trial_source_summary(trial_payload):
    if not isinstance(trial_payload, dict):
        return {
            "trial_packet_source_type": "",
            "source_artifact_path": "",
            "market_id": "",
            "used_example_packet_fallback": None,
            "blocking_errors": [
                _issue("trial_result_malformed", "trial", "Trial result must be a JSON object.")
            ],
            "rejection_errors": [],
        }

    used_example_packet_fallback, fallback_errors = _extract_used_example_packet_fallback(trial_payload)
    blocking_errors = list(fallback_errors)
    rejection_errors = []
    trial_packet_source_type = trial_payload.get("trial_packet_source_type", "")
    source_artifact_path = trial_payload.get("source_artifact_path", "")
    market_id = trial_payload.get("market_id", "")

    if not trial_packet_source_type:
        blocking_errors.append(
            _issue(
                "trial_packet_source_type_missing",
                "trial.trial_packet_source_type",
                "Trial result must identify the trial packet source type.",
            )
        )
    elif trial_packet_source_type != REAL_LOCAL_MARKET_ARTIFACT:
        rejection_errors.append(
            _issue(
                "trial_packet_source_type_not_real_local_market_artifact",
                "trial.trial_packet_source_type",
                "Operator acceptance requires trial_packet_source_type == real_local_market_artifact.",
            )
        )

    if not source_artifact_path:
        blocking_errors.append(
            _issue(
                "source_artifact_path_missing",
                "trial.source_artifact_path",
                "Trial result must identify the source_artifact_path.",
            )
        )
    if not market_id:
        blocking_errors.append(
            _issue("market_id_missing", "trial.market_id", "Trial result must identify the market_id.")
        )

    if used_example_packet_fallback is None:
        blocking_errors.append(
            _issue(
                "used_example_packet_fallback_not_verifiable",
                "trial.source_selection.used_example_packet_fallback",
                "Acceptance must verify that example packet fallback was not used.",
            )
        )
    elif used_example_packet_fallback is not False:
        rejection_errors.append(
            _issue(
                "used_example_packet_fallback_true",
                "trial.source_selection.used_example_packet_fallback",
                "Operator acceptance rejects any trial that used an example packet fallback.",
            )
        )

    return {
        "trial_packet_source_type": trial_packet_source_type,
        "source_artifact_path": source_artifact_path,
        "market_id": market_id,
        "used_example_packet_fallback": used_example_packet_fallback,
        "blocking_errors": blocking_errors,
        "rejection_errors": rejection_errors,
    }


def _packet_source_verification(packet_payload, trial_source):
    if not isinstance(packet_payload, dict):
        return [
            _issue("packet_payload_malformed", "packet", "Packet must be a JSON object for source verification.")
        ], []

    blocking_errors = []
    rejection_errors = []
    packet_market_id = ""
    market_context = packet_payload.get("market_context")
    if isinstance(market_context, dict):
        packet_market_id = market_context.get("market_id", "")
    if packet_market_id and trial_source["market_id"] and packet_market_id != trial_source["market_id"]:
        blocking_errors.append(
            _issue(
                "packet_market_id_mismatch",
                "packet.market_context.market_id",
                "Packet market_id does not match the trial market_id.",
            )
        )

    source_paths = []
    fixture_sources = []
    for index, source in enumerate(packet_payload.get("source_artifacts", [])):
        if not isinstance(source, dict):
            continue
        path = source.get("path", "")
        if path:
            source_paths.append(path)
        if source.get("sanitization_status") == "fixture_only":
            fixture_sources.append(f"packet.source_artifacts[{index}].sanitization_status")

    if trial_source["source_artifact_path"] and trial_source["source_artifact_path"] not in source_paths:
        blocking_errors.append(
            _issue(
                "packet_source_artifact_path_mismatch",
                "packet.source_artifacts",
                "Packet source_artifacts must include the trial source_artifact_path.",
            )
        )
    for path in fixture_sources:
        rejection_errors.append(
            _issue(
                "packet_source_artifact_is_fixture",
                path,
                "Operator acceptance rejects fixture-only packet source artifacts.",
            )
        )

    return blocking_errors, rejection_errors


def _forbidden_content_detected(manual_review_result, quality_gate_result, combined_errors):
    manual_forbidden = manual_review_result.get("forbidden_content_detected", {})
    quality_forbidden = quality_gate_result.get("forbidden_content_check", {})
    if isinstance(manual_forbidden, dict) and manual_forbidden.get("detected"):
        return True
    if isinstance(quality_forbidden, dict) and quality_forbidden.get("forbidden_content_detected"):
        return True
    forbidden_prefixes = (
        "forbidden_packet_field",
        "forbidden_response_field",
        "forbidden_phrase",
        "forbidden_certainty",
        "missing_required_forbidden_output",
    )
    return any(error.get("code", "").startswith(forbidden_prefixes) for error in combined_errors)


def _unsafe_certainty_detected(quality_gate_result, combined_errors):
    unsafe_check = quality_gate_result.get("unsafe_certainty_check", {})
    if isinstance(unsafe_check, dict) and unsafe_check.get("unsafe_certainty_detected"):
        return True
    return any(error.get("code", "").startswith("unsafe_certainty") for error in combined_errors)


def _response_is_known_example_fixture(response_path):
    return _display_path(response_path) == _display_path(DEFAULT_RESPONSE_PATH)


def _status_reasons(status):
    if status == ACCEPTED:
        return [
            "The trial packet source is real_local_market_artifact.",
            "The trial did not use an example packet fallback.",
            "The response_source_type is actual_operator_pasted_response.",
            "Packet and response validation passed.",
            "Manual review accepted the response.",
            "The quality gate passed or passed with warnings.",
            "No forbidden content or unsafe certainty was detected.",
        ]
    if status == PENDING:
        return [
            "The packet is a verified real local market artifact.",
            "The response validates, but response_source_type is example_fixture_response.",
            "The example fixture response cannot be accepted as real operator acceptance.",
            "A manually pasted operator response is required before acceptance.",
        ]
    if status == BLOCKED:
        return [
            "A required artifact is missing, malformed, or cannot be used to verify source selection.",
            "No operator acceptance decision was made.",
        ]
    return [
        "One or more deterministic acceptance requirements failed.",
        "The response is not accepted for operator review.",
    ]


def _operator_required_actions(status):
    if status == PENDING:
        return list(OPERATOR_REQUIRED_ACTIONS_PENDING)
    if status == ACCEPTED:
        return [
            "Review the acceptance JSON and Markdown outputs.",
            "Compare the operator-pasted response against local source artifacts before using it as review context.",
            "Keep the result offline/manual only; do not treat it as truth, trading advice, or execution authority.",
        ]
    if status == BLOCKED:
        return [
            "Restore or regenerate the required local trial, packet, prompt, and response artifacts.",
            "Verify that the trial source selection proves real_local_market_artifact with no example fallback.",
            "Rerun this acceptance script after local artifacts are readable.",
        ]
    return [
        "Inspect the listed errors.",
        "Replace or correct only the local response/trial artifacts involved in the rejection.",
        "Rerun this acceptance script after the local artifacts satisfy the offline acceptance contract.",
    ]


def _next_safe_operator_action(status):
    if status == PENDING:
        return (
            "Manually paste pm_bot/llm/real_local_market_llm_trial_prompt.v1.md into an LLM UI, save the strict "
            "JSON response locally, and rerun with --response-source-type actual_operator_pasted_response."
        )
    if status == ACCEPTED:
        return "Review the accepted local artifacts as offline operator context only; do not execute or automate anything."
    if status == BLOCKED:
        return "Fix missing, malformed, or unverifiable local artifacts, then rerun the deterministic acceptance gate."
    return "Inspect rejection errors, correct the local artifact, and rerun the deterministic acceptance gate."


def _source_artifacts(trial_path, packet_path, prompt_path, response_path, trial_source, manual_review_result, gate_result):
    return {
        "trial_result": _display_path(trial_path),
        "packet": _display_path(packet_path),
        "prompt": _display_path(prompt_path),
        "response": _display_path(response_path),
        "known_example_response_fixture": _display_path(DEFAULT_RESPONSE_PATH),
        "source_artifact_path": trial_source["source_artifact_path"],
        "market_id": trial_source["market_id"],
        "contract_artifacts": [
            _display_path(validator.PACKET_SCHEMA_PATH),
            _display_path(validator.RESPONSE_SCHEMA_PATH),
        ],
        "component_artifacts": {
            "base_validator": _display_path(validator.LLM_DIR / "validate_llm_analysis_artifacts.py"),
            "manual_review_flow": _display_path(validator.LLM_DIR / "validate_manual_llm_paste_in_review.py"),
            "quality_gate": _display_path(validator.LLM_DIR / "evaluate_manual_llm_review_quality_gate.py"),
            "operator_acceptance_gate": _display_path(Path(__file__).resolve()),
        },
        "manual_review_source_artifacts": manual_review_result.get("source_artifacts", {}),
        "quality_gate_source_artifacts": gate_result.get("source_artifacts", {}),
    }


def _empty_trial_source():
    return {
        "trial_packet_source_type": "",
        "source_artifact_path": "",
        "market_id": "",
        "used_example_packet_fallback": None,
        "blocking_errors": [],
        "rejection_errors": [],
    }


def _build_result(
    trial_path,
    packet_path,
    prompt_path,
    response_path,
    response_source_type,
    trial_source,
    packet_validation,
    response_validation,
    manual_review_result,
    gate_result,
    acceptance_status,
    errors,
    warnings,
):
    return {
        "contract_version": CONTRACT_VERSION,
        "acceptance_version": ACCEPTANCE_VERSION,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": DETERMINISTIC_GENERATED_AT,
        "source_trial_path": _display_path(trial_path),
        "packet_path": _display_path(packet_path),
        "prompt_path": _display_path(prompt_path),
        "response_path": _display_path(response_path),
        "response_source_type": response_source_type,
        "market_id": trial_source["market_id"],
        "source_artifact_path": trial_source["source_artifact_path"],
        "trial_packet_source_type": trial_source["trial_packet_source_type"],
        "used_example_packet_fallback": trial_source["used_example_packet_fallback"],
        "packet_validation_status": packet_validation["status"],
        "response_validation_status": response_validation["status"],
        "manual_review_status": manual_review_result.get("validation_status", "not_run"),
        "quality_gate_status": gate_result.get("validation_status", "not_run"),
        "acceptance_status": acceptance_status,
        "acceptance_reasons": _status_reasons(acceptance_status),
        "errors": errors,
        "warnings": warnings,
        "safety_flags": dict(SAFETY_FLAGS),
        "operator_required_actions": _operator_required_actions(acceptance_status),
        "next_safe_operator_action": _next_safe_operator_action(acceptance_status),
        "source_artifacts": _source_artifacts(
            trial_path,
            packet_path,
            prompt_path,
            response_path,
            trial_source,
            manual_review_result,
            gate_result,
        ),
    }


def build_acceptance(
    trial_path=DEFAULT_TRIAL_PATH,
    packet_path=DEFAULT_PACKET_PATH,
    prompt_path=DEFAULT_PROMPT_PATH,
    response_path=DEFAULT_RESPONSE_PATH,
    response_source_type=EXAMPLE_FIXTURE_RESPONSE,
):
    trial_path = _resolve_path(trial_path)
    packet_path = _resolve_path(packet_path)
    prompt_path = _resolve_path(prompt_path)
    response_path = _resolve_path(response_path)

    errors = []
    warnings = []
    blocking_errors = []
    rejection_errors = []
    trial_source = _empty_trial_source()
    packet_validation = _not_run_validation()
    response_validation = _not_run_validation()
    manual_review_result = {"validation_status": "not_run"}
    gate_result = {"validation_status": "not_run"}

    trial_payload, trial_load_errors = _load_json_artifact(trial_path, "trial")
    if trial_load_errors:
        blocking_errors.extend(_stage_messages("trial_load", trial_load_errors))
    else:
        trial_source = _trial_source_summary(trial_payload)
        blocking_errors.extend(_stage_messages("trial_source_verification", trial_source["blocking_errors"]))
        rejection_errors.extend(_stage_messages("trial_source_verification", trial_source["rejection_errors"]))

    packet_payload, packet_load_errors = _load_json_artifact(packet_path, "packet")
    packet_schema, packet_schema_errors = _load_json_artifact(validator.PACKET_SCHEMA_PATH, "packet_schema")
    if packet_load_errors or packet_schema_errors:
        packet_validation = _validation_from_load_errors(packet_load_errors + packet_schema_errors)
        blocking_errors.extend(_stage_messages("packet_load", packet_validation["errors"]))
    else:
        packet_validation = validator.validate_packet_payload(packet_payload, packet_schema)
        if packet_validation["status"] != "accepted":
            blocking_errors.extend(_stage_messages("packet_validation", packet_validation["errors"]))
        packet_blocking, packet_rejection = _packet_source_verification(packet_payload, trial_source)
        blocking_errors.extend(_stage_messages("packet_source_verification", packet_blocking))
        rejection_errors.extend(_stage_messages("packet_source_verification", packet_rejection))

    response_payload, response_load_errors = _load_json_artifact(response_path, "response")
    response_schema, response_schema_errors = _load_json_artifact(validator.RESPONSE_SCHEMA_PATH, "response_schema")
    if response_load_errors or response_schema_errors:
        response_validation = _validation_from_load_errors(response_load_errors + response_schema_errors)
        blocking_errors.extend(_stage_messages("response_load", response_validation["errors"]))
    else:
        response_validation = validator.validate_response_payload(response_payload, response_schema)

    can_run_response_flows = not packet_load_errors and not packet_schema_errors and not response_load_errors
    can_run_response_flows = can_run_response_flows and not response_schema_errors
    if can_run_response_flows:
        manual_review_result = manual_review.build_manual_review(packet_path, response_path, prompt_path)
        gate_result = quality_gate.build_quality_gate(packet_path, response_path, None)

    errors.extend(_stage_messages("packet_validation", packet_validation.get("errors", [])))
    errors.extend(_stage_messages("response_validation", response_validation.get("errors", [])))
    errors.extend(_stage_messages("manual_review", manual_review_result.get("errors", [])))
    errors.extend(_stage_messages("quality_gate", gate_result.get("errors", [])))
    warnings.extend(_stage_messages("packet_validation", packet_validation.get("warnings", [])))
    warnings.extend(_stage_messages("response_validation", response_validation.get("warnings", [])))
    warnings.extend(_stage_messages("manual_review", manual_review_result.get("warnings", [])))
    warnings.extend(_stage_messages("quality_gate", gate_result.get("warnings", [])))

    if not response_source_type or response_source_type not in KNOWN_RESPONSE_SOURCE_TYPES:
        rejection_errors.append(
            {
                "stage": "response_source_verification",
                **_issue(
                    "response_source_type_unknown",
                    "response_source_type",
                    "response_source_type must be example_fixture_response or actual_operator_pasted_response.",
                ),
            }
        )
    if response_source_type == ACTUAL_OPERATOR_PASTED_RESPONSE and _response_is_known_example_fixture(response_path):
        rejection_errors.append(
            {
                "stage": "response_source_verification",
                **_issue(
                    "actual_operator_response_points_to_example_fixture",
                    _display_path(response_path),
                    "actual_operator_pasted_response cannot point to the known example fixture response path.",
                ),
            }
        )

    forbidden_content = _forbidden_content_detected(manual_review_result, gate_result, errors)
    unsafe_certainty = _unsafe_certainty_detected(gate_result, errors)
    if forbidden_content:
        rejection_errors.append(
            {
                "stage": "safety_content_check",
                **_issue(
                    "forbidden_content_detected",
                    "response",
                    "Forbidden response or packet content was detected by the offline validators.",
                ),
            }
        )
    if unsafe_certainty:
        rejection_errors.append(
            {
                "stage": "safety_content_check",
                **_issue(
                    "unsafe_certainty_detected",
                    "response",
                    "Unsafe certainty language was detected by the offline quality gate.",
                ),
            }
        )

    if response_validation["status"] != "accepted" and not response_load_errors and not response_schema_errors:
        rejection_errors.append(
            {
                "stage": "response_validation",
                **_issue(
                    "response_validation_rejected",
                    _display_path(response_path),
                    "Response validation must pass before operator acceptance.",
                ),
            }
        )
    if manual_review_result.get("validation_status") == "rejected":
        rejection_errors.append(
            {
                "stage": "manual_review",
                **_issue(
                    "manual_review_rejected",
                    "manual_review.validation_status",
                    "Manual review must be accepted before operator acceptance.",
                ),
            }
        )
    quality_gate_status = gate_result.get("validation_status", "not_run")
    if quality_gate_status not in QUALITY_PASS_STATUSES and quality_gate_status != "not_run":
        rejection_errors.append(
            {
                "stage": "quality_gate",
                **_issue(
                    "quality_gate_not_passed",
                    "quality_gate.validation_status",
                    "Quality gate must be quality_passed or quality_passed_with_warnings.",
                ),
            }
        )

    if blocking_errors:
        acceptance_status = BLOCKED
    elif rejection_errors:
        acceptance_status = REJECTED
    elif response_source_type == EXAMPLE_FIXTURE_RESPONSE:
        acceptance_status = PENDING
        warnings.append(
            {
                "stage": "response_source_verification",
                **_issue(
                    "example_fixture_response_pending_real_manual_response",
                    _display_path(response_path),
                    "The example fixture response validates but cannot be accepted as a real operator-pasted response.",
                ),
            }
        )
    elif (
        trial_source["trial_packet_source_type"] == REAL_LOCAL_MARKET_ARTIFACT
        and trial_source["used_example_packet_fallback"] is False
        and response_source_type == ACTUAL_OPERATOR_PASTED_RESPONSE
        and packet_validation["status"] == "accepted"
        and response_validation["status"] == "accepted"
        and manual_review_result.get("validation_status") == "accepted"
        and quality_gate_status in QUALITY_PASS_STATUSES
        and not forbidden_content
        and not unsafe_certainty
    ):
        acceptance_status = ACCEPTED
    else:
        acceptance_status = REJECTED
        rejection_errors.append(
            {
                "stage": "acceptance",
                **_issue(
                    "acceptance_requirements_not_satisfied",
                    "acceptance_status",
                    "The deterministic operator acceptance requirements were not all satisfied.",
                ),
            }
        )

    errors.extend(blocking_errors)
    errors.extend(rejection_errors)
    errors = sorted(
        errors,
        key=lambda item: (
            item.get("stage", ""),
            item.get("artifact", ""),
            item.get("check", ""),
            item.get("path", ""),
            item.get("code", ""),
            item.get("message", ""),
        ),
    )
    warnings = sorted(
        warnings,
        key=lambda item: (
            item.get("stage", ""),
            item.get("artifact", ""),
            item.get("check", ""),
            item.get("path", ""),
            item.get("code", ""),
            item.get("message", ""),
        ),
    )

    return _build_result(
        trial_path,
        packet_path,
        prompt_path,
        response_path,
        response_source_type,
        trial_source,
        packet_validation,
        response_validation,
        manual_review_result,
        gate_result,
        acceptance_status,
        errors,
        warnings,
    )


def _format_messages(messages):
    if not messages:
        return ["- none"]
    lines = []
    for message in messages:
        stage = f"[{message.get('stage', 'acceptance')}] "
        artifact = f"{message.get('artifact')}: " if message.get("artifact") else ""
        check = f"{message.get('check')}: " if message.get("check") else ""
        lines.append(
            f"- {stage}{artifact}{check}{message.get('path', '')}: "
            f"{message.get('code', 'message')} - {message.get('message', '')}"
        )
    return lines


def _format_list(items):
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]


def render_markdown_report(result):
    is_actual = result["response_source_type"] == ACTUAL_OPERATOR_PASTED_RESPONSE
    is_example = result["response_source_type"] == EXAMPLE_FIXTURE_RESPONSE
    lines = [
        "# PMBOT Real Manual LLM Trial Operator Acceptance v1",
        "",
        f"- Acceptance status: {result['acceptance_status']}",
        f"- Packet is real local market artifact: {result['trial_packet_source_type'] == REAL_LOCAL_MARKET_ARTIFACT}",
        f"- Market ID: {result['market_id'] or 'not available'}",
        f"- Source artifact path: {result['source_artifact_path'] or 'not available'}",
        f"- Response source type: {result['response_source_type']}",
        f"- Actual operator-pasted response: {is_actual}",
        f"- Example fixture response: {is_example}",
        f"- Packet validator status: {result['packet_validation_status']}",
        f"- Response validator status: {result['response_validation_status']}",
        f"- Manual review status: {result['manual_review_status']}",
        f"- Quality gate status: {result['quality_gate_status']}",
        "",
        "## Acceptance Reasons",
        *_format_list(result["acceptance_reasons"]),
        "",
        "## Errors",
        *_format_messages(result["errors"]),
        "",
        "## Warnings",
        *_format_messages(result["warnings"]),
        "",
        "## Operator Required Actions",
        *_format_list(result["operator_required_actions"]),
        "",
        "## Exact Steps If Pending",
        "1. Open pm_bot/llm/real_local_market_llm_trial_prompt.v1.md.",
        "2. Paste manually into ChatGPT/Claude/Gemini.",
        "3. Request strict JSON only.",
        "4. Save the returned JSON to pm_bot/llm/real_local_market_llm_trial_response_operator.v1.json.",
        (
            "5. Rerun with --response pm_bot\\llm\\real_local_market_llm_trial_response_operator.v1.json "
            "--response-source-type actual_operator_pasted_response."
        ),
        "6. Review the acceptance JSON and Markdown outputs.",
        "",
        "## Next Safe Operator Action",
        result["next_safe_operator_action"],
        "",
        "## Explicit Boundary Warning",
        BOUNDARY_NOTICE,
        "",
    ]
    return "\n".join(lines)


def export_acceptance(
    trial_path=DEFAULT_TRIAL_PATH,
    packet_path=DEFAULT_PACKET_PATH,
    prompt_path=DEFAULT_PROMPT_PATH,
    response_path=DEFAULT_RESPONSE_PATH,
    response_source_type=EXAMPLE_FIXTURE_RESPONSE,
    out_json_path=DEFAULT_OUT_JSON_PATH,
    out_md_path=DEFAULT_OUT_MD_PATH,
):
    result = build_acceptance(trial_path, packet_path, prompt_path, response_path, response_source_type)
    out_json_path = _resolve_path(out_json_path)
    out_md_path = _resolve_path(out_md_path)
    _write_json(out_json_path, result)
    _write_text(out_md_path, render_markdown_report(result))
    return result


def main(argv):
    args = _parse_args(argv)
    result = export_acceptance(
        args.trial,
        args.packet,
        args.prompt,
        args.response,
        args.response_source_type,
        args.out_json,
        args.out_md,
    )
    print(json.dumps(result, indent=2, ensure_ascii=True))
    return 0 if result["acceptance_status"] in {ACCEPTED, PENDING} else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
