import argparse
import json
from pathlib import Path


TASK_ID = "PMBOT-LIVE-001-READONLY-POLYMARKET-API-DISCOVERY-PROTOCOL-ONLY"
ROOT = Path(__file__).resolve().parents[2]
PROTOCOL_PATH = "pm_bot/live_readonly/polymarket_readonly_api_discovery_protocol.v1.json"


def _parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Report PMBOT LIVE-001 protocol-only read-only discovery status."
    )
    parser.add_argument(
        "--protocol-only",
        action="store_true",
        help="Print local protocol status without network behavior.",
    )
    return parser.parse_args(argv)


def _resolve(path, root=ROOT):
    value = Path(path)
    return value if value.is_absolute() else Path(root) / value


def _load_protocol(root=ROOT):
    with _resolve(PROTOCOL_PATH, root=root).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_protocol_only_status(root=ROOT):
    protocol = _load_protocol(root=root)
    safety = protocol["required_future_safety_fields"]
    return {
        "task_id": TASK_ID,
        "status": "protocol_only_no_network",
        "protocol_path": PROTOCOL_PATH,
        "network_allowed_explicitly": False,
        "polymarket_api_calls_performed": 0,
        "authenticated_endpoints_used": False,
        "wallet_or_private_key_accessed": False,
        "orders_created": False,
        "runtime_wiring_changed": False,
        "dispatcher_changed": False,
        "background_worker_created": False,
        "queue_mutated": False,
        "browser_automation_used": False,
        "operator_review_only": safety["operator_review_only"],
        "analysis_only": safety["analysis_only"],
    }


def main(argv):
    args = _parse_args(argv)
    if not args.protocol_only:
        raise SystemExit("--protocol-only is required; LIVE-001 has no live mode")
    print(json.dumps(build_protocol_only_status(ROOT), indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
