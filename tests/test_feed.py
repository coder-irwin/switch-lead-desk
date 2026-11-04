import hashlib
import hmac
import json

import feed
import receiver

LEAD = {
    "id": "L001",
    "name": "Rohan Deshmukh",
    "city": "Pune",
    "role": "owner",
    "source": "WhatsApp",
    "received": "2026-11-02 10:07",
    "message": "wants a modular kitchen",
}
SECRET = "s" * 32


def test_a_lead_becomes_a_message_event_that_mentions_the_scout():
    event = feed.lead_event(LEAD, "leads", "harbor-scout")
    assert event["version"] == 1
    assert event["type"] == "message"
    assert event["channel"] == {"id": "leads", "name": "leads", "type": "channel"}
    assert event["sender"] == {"id": "rohan-deshmukh", "name": "Rohan Deshmukh"}
    text = event["message"]["text"]
    assert text.startswith("@harbor-scout new enquiry L001 from Rohan Deshmukh")
    assert "Pune, owner, WhatsApp" in text
    assert text.endswith("wants a modular kitchen")


def test_the_event_id_is_stable_so_a_resend_is_ignored():
    first = feed.lead_event(LEAD, "leads", "harbor-scout")
    again = feed.lead_event(LEAD, "leads", "harbor-scout")
    assert first["id"] == again["id"] == "lead-l001"
    assert first["message"]["id"] == first["id"]


def test_the_join_event_has_no_message():
    event = feed.join_event("leads")
    assert event["type"] == "channel.joined"
    assert "message" not in event and "sender" not in event


def test_the_sample_file_loads_every_lead():
    leads = feed.load_leads()
    assert len(leads) == 20
    assert all(feed.lead_event(lead, "leads", "x")["message"]["text"] for lead in leads)


def test_dry_run_prints_events_and_sends_nothing(capsys, monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("dry run must not send")

    monkeypatch.setattr(feed, "post", refuse)
    assert feed.main(["--dry-run", "--join", "--limit", "2"]) == 0
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert [e["type"] for e in lines] == ["channel.joined", "message", "message"]
    assert lines[1]["id"] == "lead-l001"


def test_it_asks_for_the_address_and_token_when_not_a_dry_run(capsys, monkeypatch):
    monkeypatch.delenv("SWITCH_EVENTS_URL", raising=False)
    monkeypatch.delenv("SWITCH_TOKEN", raising=False)
    assert feed.main(["--limit", "1"]) == 2
    assert "SWITCH_EVENTS_URL" in capsys.readouterr().err


def test_sending_uses_the_bearer_token_and_reports_failures(monkeypatch, capsys):
    seen = []

    def fake_post(url, token, event):
        seen.append((url, token, event["id"]))
        return 401 if len(seen) == 2 else 200

    monkeypatch.setattr(feed, "post", fake_post)
    code = feed.main(["--url", "http://x/events", "--token", "t" * 24, "--limit", "3"])
    assert code == 1
    assert [s[2] for s in seen] == ["lead-l001", "lead-l002", "lead-l003"]
    assert all(s[:2] == ("http://x/events", "t" * 24) for s in seen)
    assert "401" in capsys.readouterr().out


def sign(body: bytes, stamp: int, secret: str = SECRET) -> dict:
    digest = hmac.new(secret.encode(), str(stamp).encode() + b"." + body, hashlib.sha256)
    return {
        "X-Switch-Timestamp": str(stamp),
        "X-Switch-Signature": "v1=" + digest.hexdigest(),
    }


def test_the_receiver_accepts_a_correct_signature():
    body = b'{"type":"message.created"}'
    assert receiver.signature_is_valid(sign(body, 1000), body, SECRET, now=1000)


def test_the_receiver_refuses_a_wrong_secret_a_changed_body_and_an_old_timestamp():
    body = b'{"type":"message.created"}'
    headers = sign(body, 1000)
    assert not receiver.signature_is_valid(headers, body, "z" * 32, now=1000)
    assert not receiver.signature_is_valid(headers, body + b" ", SECRET, now=1000)
    assert not receiver.signature_is_valid(headers, body, SECRET, now=1000 + 301)
    assert not receiver.signature_is_valid({}, body, SECRET, now=1000)


def test_the_receiver_prints_replies_and_ignores_other_events():
    reply = {"type": "message.created", "sender": {"name": "harbor-scout"}, "text": "HOT"}
    assert "harbor-scout" in receiver.describe(reply)
    assert receiver.describe({"type": "ping"}) is None
    assert receiver.describe({"type": "typing"}) is None
