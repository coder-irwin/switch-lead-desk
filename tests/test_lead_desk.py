import csv
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = yaml.safe_load((ROOT / "lead-desk.template.yaml").read_text(encoding="utf-8"))


def test_every_room_member_is_a_defined_agent():
    names = {a["name"] for a in TEMPLATE["agents"]}
    for room in TEMPLATE["rooms"]:
        assert set(room["agents"]) <= names


def test_links_join_defined_rooms():
    rooms = {r["name"] for r in TEMPLATE["rooms"]}
    for link in TEMPLATE["links"]:
        assert {link["from"], link["to"]} <= rooms


def test_every_placeholder_is_a_param():
    text = (ROOT / "lead-desk.template.yaml").read_text(encoding="utf-8")
    assert "{team}" in text
    assert "team" in TEMPLATE["params"]


def test_leads_have_unique_ids_and_messages():
    with (ROOT / "data" / "leads.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 20
    assert len({r["id"] for r in rows}) == len(rows)
    assert all(r["message"].strip() for r in rows)


def test_agents_read_files_that_exist():
    text = (ROOT / "lead-desk.template.yaml").read_text(encoding="utf-8")
    assert "data/leads.csv" in text
    for name in ("playbook.md", "leads.csv"):
        assert (ROOT / "data" / name).exists()


def test_the_room_playbook_is_the_playbook_file():
    playbook = (ROOT / "data" / "playbook.md").read_text(encoding="utf-8").strip()
    for room in TEMPLATE["rooms"]:
        docs = {d["name"]: d for d in room["docs"]}
        assert docs["Lead playbook"]["content"].strip() == playbook
