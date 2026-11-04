"""A small app that shows what the desk says back, without Slack.

    SWITCH_SIGNING_SECRET=<signing secret> python scripts/receiver.py

Connect a "Custom app (webhook)" in Switch with the outbound URL
http://localhost:8081/switch and the same signing secret. Every message the
agents post to the room is printed here. Standard library only.
"""

import hashlib
import hmac
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAX_CLOCK_SKEW = 300


def signature_is_valid(headers, body: bytes, secret: str, now: float | None = None) -> bool:
    stamp = headers.get("X-Switch-Timestamp", "")
    if not stamp.isdigit():
        return False
    if abs((time.time() if now is None else now) - int(stamp)) > MAX_CLOCK_SKEW:
        return False
    digest = hmac.new(secret.encode(), stamp.encode() + b"." + body, hashlib.sha256)
    return hmac.compare_digest(
        "v1=" + digest.hexdigest(), headers.get("X-Switch-Signature", "")
    )


def describe(event: dict) -> str | None:
    kind = event.get("type")
    stamp = time.strftime("%H:%M:%S")
    if kind == "message.created":
        sender = event.get("sender", {}).get("name", "?")
        return f"[{stamp}] {sender}:\n{event.get('text', '')}\n"
    if kind == "message.updated":
        return f"[{stamp}] (edited {event['message_id']}):\n{event.get('text', '')}\n"
    return None


def make_handler(secret: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args) -> None:
            pass

        def do_POST(self) -> None:
            body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
            if self.path != "/switch":
                return self._status(404)
            if not signature_is_valid(self.headers, body, secret):
                return self._status(401)
            line = describe(json.loads(body))
            if line:
                print(line, flush=True)
            self._status(200)

        def _status(self, code: int) -> None:
            self.send_response(code)
            self.send_header("Content-Length", "0")
            self.end_headers()

    return Handler


def main() -> int:
    secret = os.environ.get("SWITCH_SIGNING_SECRET")
    if not secret:
        print("Set SWITCH_SIGNING_SECRET to the connection's signing secret.", file=sys.stderr)
        return 2
    port = int(os.environ.get("PORT", "8081"))
    print(f"Listening on http://localhost:{port}/switch", flush=True)
    ThreadingHTTPServer(("", port), make_handler(secret)).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
