from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def main() -> int:
    mode = os.environ.get("FAKE_CODEX_MODE", "success")
    result_path = Path(os.environ["AI_ORCHESTRATOR_CODEX_RESULT_PATH"])
    packet_path = Path(os.environ["AI_ORCHESTRATOR_CODEX_PACKET_PATH"])
    packet = json.loads(packet_path.read_text(encoding="utf-8"))

    if mode == "nonzero":
        print("fake codex nonzero", file=sys.stderr)
        return 9
    if mode == "missing_result":
        print("fake codex skipped result")
        return 0

    template_path = Path(packet["expected_result_path"])
    envelope = json.loads(template_path.read_text(encoding="utf-8"))
    status = "completed"
    if mode in {"blocked", "failed", "needs_retry"}:
        status = mode
    envelope["received_at"] = "2026-05-11T00:00:00Z"
    envelope["status"] = status
    envelope["validation_passed"] = True
    envelope["safety_ok"] = True
    envelope["acceptance_status"] = "pending_ingestion"
    envelope["result_path"] = str(result_path)
    envelope["result_payload"]["status"] = status
    envelope["result_payload"]["validation_passed"] = True
    envelope["result_payload"]["safety_ok"] = True
    envelope["result_payload"]["summary"] = f"fake codex {status}"
    envelope["result_payload"]["commands_run"] = ["fake_codex_command"]
    if mode == "unsafe":
        envelope["result_payload"]["wallet_used"] = True
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"fake codex wrote {result_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
