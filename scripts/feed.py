"""Post the sample enquiries into a Switch room through the webhook platform.

    SWITCH_EVENTS_URL=https://switch.example/messaging/bridges/<id>/events \
    SWITCH_TOKEN=<inbound token> \
    python scripts/feed.py --join --delay 5

Each enquiry becomes one message that mentions the scout. Use --dry-run to see
the events without sending anything. Standard library only.
"""

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

LEADS = Path(__file__).resolve().parent.parent / "data" / "leads.csv"


def slug(text: str) -> str:
    return "-".join("".join(c if c.isalnum() else " " for c in text.lower()).split())


def load_leads(path: Path = LEADS) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def message_text(lead: dict, agent: str) -> str:
    where = ", ".join(
        part for part in (lead["city"], lead["role"], lead["source"]) if part
    )
    return (
        f"@{agent} new enquiry {lead['id']} from {lead['name']} "
        f"({where}, received {lead['received']}):\n{lead['message']}"
    )


def channel(channel_id: str) -> dict:
    return {"id": channel_id, "name": channel_id, "type": "channel"}


def join_event(channel_id: str) -> dict:
    return {
        "version": 1,
        "id": f"join-{channel_id}",
        "type": "channel.joined",
        "channel": channel(channel_id),
    }


def lead_event(lead: dict, channel_id: str, agent: str) -> dict:
    # The id comes from the lead, so sending the same file twice is harmless:
    # Switch handles an event id once.
    event_id = f"lead-{lead['id'].lower()}"
    return {
        "version": 1,
        "id": event_id,
        "type": "message",
        "channel": channel(channel_id),
        "sender": {"id": slug(lead["name"]), "name": lead["name"]},
        "message": {"id": event_id, "text": message_text(lead, agent)},
    }


def post(url: str, token: str, event: dict) -> int:
    request = urllib.request.Request(
        url,
        data=json.dumps(event).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Send the sample leads to a Switch room.")
    p.add_argument("--url", default=os.environ.get("SWITCH_EVENTS_URL"))
    p.add_argument("--token", default=os.environ.get("SWITCH_TOKEN"))
    p.add_argument("--channel", default=os.environ.get("SWITCH_CHANNEL", "leads"))
    p.add_argument("--agent", default=os.environ.get("LEAD_DESK_SCOUT", "harbor-scout"))
    p.add_argument("--csv", type=Path, default=LEADS)
    p.add_argument("--limit", type=int, default=0, help="send only the first N leads")
    p.add_argument("--delay", type=float, default=0, help="seconds between leads")
    p.add_argument("--join", action="store_true", help="send channel.joined first")
    p.add_argument("--dry-run", action="store_true", help="print the events, send nothing")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not args.dry_run and not (args.url and args.token):
        print("Set SWITCH_EVENTS_URL and SWITCH_TOKEN, or use --dry-run.", file=sys.stderr)
        return 2

    leads = load_leads(args.csv)
    if args.limit:
        leads = leads[: args.limit]
    events = [join_event(args.channel)] if args.join else []
    events += [lead_event(lead, args.channel, args.agent) for lead in leads]

    failed = 0
    for number, event in enumerate(events):
        if args.dry_run:
            print(json.dumps(event, ensure_ascii=False))
            continue
        status = post(args.url, args.token, event)
        label = event["message"]["text"].splitlines()[0] if "message" in event else event["type"]
        print(f"{status}  {label}")
        failed += status != 200
        if args.delay and number < len(events) - 1:
            time.sleep(args.delay)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
