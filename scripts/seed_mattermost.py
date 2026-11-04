"""Post the sample enquiries into the inbox channel on a Mattermost server.

    MM_URL=http://localhost:8065 MM_USER=you MM_PASSWORD=... \
    python scripts/seed_mattermost.py --team myteam --agent harbor-scout

Each enquiry becomes one message from your account that mentions the scout.
Use --dry-run to print the messages without logging in. Standard library only.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

from feed import load_leads, message_text


class MattermostError(Exception):
    pass


def call(base: str, path: str, token: str | None = None, body: dict | None = None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        f"{base.rstrip('/')}/api/v4{path}",
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read() or b"{}")
            return payload, response.headers
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")[:200]
        raise MattermostError(f"{path} answered {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise MattermostError(f"could not reach {base}: {error.reason}") from error


def log_in(base: str, user: str, password: str) -> str:
    _, headers = call(base, "/users/login", body={"login_id": user, "password": password})
    token = headers.get("Token")
    if not token:
        raise MattermostError("login worked but Mattermost sent no token")
    return token


def channel_id(base: str, token: str, team: str, channel: str) -> str:
    team_info, _ = call(base, f"/teams/name/{team}", token)
    found, _ = call(base, f"/teams/{team_info['id']}/channels/name/{channel}", token)
    return found["id"]


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Send the sample leads to a Mattermost channel.")
    p.add_argument("--url", default=os.environ.get("MM_URL", "http://localhost:8065"))
    p.add_argument("--user", default=os.environ.get("MM_USER"))
    p.add_argument("--team", default=os.environ.get("MM_TEAM"))
    p.add_argument("--channel", help="default: <agent prefix>-inbox")
    p.add_argument("--agent", default="harbor-scout", help="the scout's name")
    p.add_argument("--delay", type=float, default=5.0, help="seconds between messages")
    p.add_argument("--limit", type=int, default=0, help="send only the first N leads")
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    leads = load_leads()
    if args.limit:
        leads = leads[: args.limit]
    messages = [message_text(lead, args.agent) for lead in leads]

    if args.dry_run:
        for text in messages:
            print(text, end="\n\n")
        print(f"{len(messages)} messages, nothing sent")
        return 0

    password = os.environ.get("MM_PASSWORD")
    if not (args.user and password and args.team):
        print("Set MM_USER, MM_PASSWORD and --team (or MM_TEAM).", file=sys.stderr)
        return 2
    channel = args.channel or args.agent.rsplit("-", 1)[0] + "-inbox"
    try:
        token = log_in(args.url, args.user, password)
        target = channel_id(args.url, token, args.team, channel)
        for i, text in enumerate(messages, 1):
            call(args.url, "/posts", token, {"channel_id": target, "message": text})
            print(f"sent {i}/{len(messages)}: {leads[i - 1]['name']}")
            if i < len(messages):
                time.sleep(args.delay)
    except MattermostError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
