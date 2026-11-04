import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

import seed_mattermost


class FakeMattermost(BaseHTTPRequestHandler):
    posts: list = []
    seen_auth: list = []

    def log_message(self, *args):
        pass

    def reply(self, body, headers=None, status=200):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def body(self):
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")

    def do_POST(self):
        if self.path == "/api/v4/users/login":
            body = self.body()
            if body["password"] != "right":
                return self.reply({"message": "bad login"}, status=401)
            return self.reply({"id": "u1"}, {"Token": "session-token"})
        self.seen_auth.append(self.headers.get("Authorization"))
        self.posts.append(self.body())
        self.reply({"id": "p1"}, status=201)

    def do_GET(self):
        self.seen_auth.append(self.headers.get("Authorization"))
        if self.path == "/api/v4/teams/name/shop":
            return self.reply({"id": "team1"})
        if self.path == "/api/v4/teams/team1/channels/name/harbor-inbox":
            return self.reply({"id": "chan1"})
        self.reply({"message": "not found"}, status=404)


@pytest.fixture
def server(monkeypatch):
    FakeMattermost.posts = []
    FakeMattermost.seen_auth = []
    httpd = HTTPServer(("127.0.0.1", 0), FakeMattermost)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    monkeypatch.setenv("MM_PASSWORD", "right")
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def run(url, *extra):
    return seed_mattermost.main(
        ["--url", url, "--user", "me", "--team", "shop", "--delay", "0", *extra]
    )


def test_each_lead_is_posted_to_the_inbox_and_mentions_the_scout(server):
    assert run(server, "--limit", "3") == 0
    assert len(FakeMattermost.posts) == 3
    assert {p["channel_id"] for p in FakeMattermost.posts} == {"chan1"}
    assert all(p["message"].startswith("@harbor-scout new enquiry L00") for p in FakeMattermost.posts)
    assert set(FakeMattermost.seen_auth) == {"Bearer session-token"}


def test_the_channel_follows_the_agent_name(server):
    assert run(server, "--limit", "1", "--agent", "harbor-scout") == 0
    assert run(server, "--limit", "1", "--agent", "other-scout") == 1


def test_a_wrong_password_sends_nothing(server, monkeypatch, capsys):
    monkeypatch.setenv("MM_PASSWORD", "wrong")
    assert run(server) == 1
    assert FakeMattermost.posts == []
    assert "401" in capsys.readouterr().err


def test_dry_run_prints_and_never_connects(capsys):
    assert seed_mattermost.main(["--dry-run", "--limit", "2", "--url", "http://127.0.0.1:1"]) == 0
    out = capsys.readouterr().out
    assert out.count("new enquiry") == 2
    assert "nothing sent" in out


def test_missing_credentials_are_reported(monkeypatch, capsys):
    monkeypatch.delenv("MM_PASSWORD", raising=False)
    assert seed_mattermost.main(["--team", "shop"]) == 2
    assert "MM_PASSWORD" in capsys.readouterr().err
