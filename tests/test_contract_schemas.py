from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
SCHEMAS = [
    "codex_result_envelope.schema.json",
    "plan_task.schema.json",
    "run_state.schema.json",
    "pmbot_paper_intent.schema.json",
    "pmbot_evidence_packet.schema.json",
]


def test_contract_schemas_are_valid_json() -> None:
    for schema_name in SCHEMAS:
        payload = json.loads((CONTRACTS / schema_name).read_text(encoding="utf-8"))
        assert payload["$schema"].startswith("https://json-schema.org/")
        assert payload["type"] == "object"
        assert payload["required"]
