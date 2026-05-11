from __future__ import annotations

import json
import signal
import sys
import time


STOP = False


def main(argv: list[str] | None = None) -> int:
    args = list(argv or sys.argv[1:])
    mode = args[0] if args and args[0] not in {"app-server", "--listen"} else "success"
    signal.signal(signal.SIGTERM, _stop)
    if mode == "startup_failure":
        print("fake app-server startup failure", file=sys.stderr, flush=True)
        return 2
    print(f"fake app-server mode={mode}", file=sys.stderr, flush=True)
    if mode == "hangs_until_timeout":
        while not STOP:
            time.sleep(0.1)
        return 0
    for line in sys.stdin:
        if mode == "invalid_json":
            print("{not-json", flush=True)
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            print(json.dumps({"id": None, "error": {"message": "invalid json"}}), flush=True)
            continue
        response = {
            "id": request.get("id"),
            "result": {
                "userAgent": "fake-codex-app-server/0.1",
                "codexHome": "/fake/codex-home",
                "platformFamily": "test",
                "platformOs": "test",
            },
        }
        print(json.dumps(response, separators=(",", ":")), flush=True)
    return 0


def _stop(signum: int, frame: object) -> None:
    global STOP
    STOP = True


if __name__ == "__main__":
    raise SystemExit(main())
