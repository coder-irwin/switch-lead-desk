# Recording walkthrough

A step-by-step script for recording a short demo of the Lead Desk, about four
minutes. Do the setup once, then record from step 5.

## What you need

- Switch running with Switch Console connected (see the Switch repository's
  `docs/old/LOCAL_DEVELOPMENT.md`, "A local Switch Cloud").
- A coding agent installed and signed in on the machine Console runs on.
- A Switch that includes the "Custom app (webhook)" platform. It is in
  pull request #1453 and is not in a release yet, so use that branch.
- This folder, with Python 3.10 or newer.

## Setup

1. Copy `data/` into a folder for the agents, for example `~/lead-desk-agents`.
   The template's `directory` should point there so the agents can read
   `data/playbook.md` and `data/leads.csv`.
2. In Console, create a team from `lead-desk.template.yaml`. Name it `harbor`.
   This creates `harbor-scout`, `harbor-writer` and `harbor-keeper`, and the
   rooms `harbor-inbox` and `harbor-review`.
3. Choose the chat app the rooms mirror to. If you want to show it without
   Slack, connect a webhook app (steps below) and use it as the bridge.
4. Webhook app, in a terminal:

   ```bash
   openssl rand -hex 32          # signing secret
   openssl rand -hex 32          # inbound token
   SWITCH_SIGNING_SECRET=<signing secret> python scripts/receiver.py
   ```

   In Console, open **Connect a messaging app**, choose **Custom app
   (webhook)**, enter `http://localhost:8081/switch`, the two secrets, and
   connect. Console shows the address that ends in `/events`.

## Shot list

| # | Show | Do | You should see |
|---|---|---|---|
| 1 | The two rooms | Open `harbor-inbox`, then `harbor-review` | Each room's kickoff message: the scout says hello and what it treats as hot, the writer says hello |
| 2 | One enquiry | Paste the sample from the README into the inbox, mentioning `@harbor-scout` | A reply in the thread: `Anjali, Pune: HOT (11), because 3 + 3 + 2 + 2 + 1 = 11` |
| 3 | The hot lead moves | Open `harbor-review` | The scout's post addressed to the writer, then a draft reply ending "Reply APPROVE to send, or tell me what to change." |
| 4 | A cold lead stays out | Paste "Price list please." from a made-up name | `COLD` with its points; nothing appears in the review room |
| 5 | Approval | In the review room, ask the writer to shorten the draft, then reply `APPROVE` | An edited draft, then the keeper recording it as approved |
| 6 | The batch | In the inbox, ask `@harbor-scout work through data/leads.csv and score every lead` | One line per lead and a closing count of hot, warm and cold |
| 7 | The summary | Ask `@harbor-keeper today` | Counts per status and the two leads waiting longest |
| 8 | A feed from outside | Run `python scripts/feed.py --url <address> --token <inbound token> --join --delay 5 --limit 5` | Five enquiries arriving in the room one after another, and the scout answering each |

Step 8 needs the room to have the scout in it. A room created by the
`channel.joined` event starts empty: invite the agents with
`!invite-agent harbor-scout` and `!invite-agent harbor-writer` first.

## What has and has not been verified

Checked:

- `scripts/feed.py` and `scripts/receiver.py` against a running Switch with the
  webhook platform: the connection goes active, `channel.joined` creates a
  room, three enquiries arrive in it exactly once, sending them again adds
  nothing, and the receiver verifies Switch's signature and prints Switch's
  reply.
- The tests in `tests/` (`pytest`).
- The scout's instructions, run by hand on all 20 sample enquiries: every score
  matched the playbook arithmetic, and two unclear enquiries got a question.
- The template parses with Switch's own template reader and produces the
  expected rooms and members.

Not checked:

- The agents running inside Console. The writer's drafts, the `APPROVE` step and
  the keeper's pipeline file have not been seen working in a room.
- The exact wording in Console's screens. The shot list names them from the
  documentation, so adjust it to what you see.
- A feed into a room that has agents in it, with the agents answering each
  enquiry.
