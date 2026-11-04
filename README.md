# Lead Desk

A small sales desk that runs inside [Switch](https://github.com/sandbox-quantum/switch).
New enquiries land in a chat room, get scored against your own rules, and the
good ones get a drafted reply that waits for a person to say yes.

```
 inbox room                         review room
 ──────────                         ───────────
 enquiry ─► scout scores it ─HOT──► writer drafts a reply
            keeper logs it          you reply APPROVE (or ask for changes)
                                    keeper logs the decision
```

Nothing is sent to a customer without a human approving it.

## What is in here

| File | What it is |
|---|---|
| `lead-desk.template.yaml` | The whole desk: three agents, two linked rooms, and their instructions |
| `data/playbook.md` | The scoring rules, the offer and the tone, for a made-up interiors firm. The template carries a copy as a room document |
| `data/leads.csv` | 20 made-up enquiries in English, Hindi and Marathi |
| `scripts/feed.py` | Sends the sample enquiries into a room through the webhook platform |
| `scripts/receiver.py` | Prints what the agents say back, after checking Switch's signature |
| `docs/walkthrough.md` | A shot list for recording the desk in Console |
| `tests/` | Checks the template, the data, the feed and the signature check |

All names, numbers and messages are invented. Replace `playbook.md` with your
own rules and the same desk works for your business.

## Approvals that scale

An approval step stops working when a person is asked to approve everything: they
start ticking boxes without reading. The desk tries to keep the human step
meaningful in three ways.

- **Tiers.** Every draft is marked `ROUTINE` or `REVIEW`, using rules written
  in the playbook (outside Pune and Mumbai, not a home, a provisional score, a
  request for a price or a completion date). A person approves all routine
  drafts at once with `APPROVE ROUTINE`, and a review draft only by naming the
  lead, for example `APPROVE Vikram`.
- **Evidence on every draft.** Each one carries its tier and the reason, the
  score with its arithmetic, and what the draft commits the firm to, so the
  person approving can check it in seconds.
- **A daily summary.** `@harbor-keeper today` lists what is waiting, review
  drafts first and the longest waiting at the top, and how many approvals were
  in a batch and how many were made one by one.

Nothing is sent without a person. The tiers only decide how much of their
attention a draft asks for. Change the rules in the playbook document and the
next draft follows them.

## The three agents

- **scout** reads each enquiry, scores it with the playbook and replies in the
  thread with one line: `HOT`, `WARM` or `COLD`, and why. Hot leads go to the
  review room.
- **writer** drafts a short first reply in the customer's language and waits.
  It only promises what the playbook allows.
- **keeper** maintains `data/pipeline.md` and answers "today" with counts and
  the two leads that have waited longest.

## Run it

You need Switch Console and a coding agent installed on the same computer (any
one Switch supports, signed in). When Console sets up a server on your
computer it starts a Mattermost alongside it and connects it, so there is
nothing else to install. See Switch's
[Mattermost page](https://docs.switchagents.ai/flintai/switch/deploy/messaging-apps/mattermost)
if you would rather use your own.

1. Clone this repo and copy `data/` into the working directory the agents
   will use (or point the template's `directory` at this folder).
2. In Switch Console, create a team from `lead-desk.template.yaml`. Pick a
   short team name, for example `harbor`. This creates the three agents and the
   `harbor-inbox` and `harbor-review` channels.
3. Open Mattermost from the server's **Home** page (**Sign-in details…** shows
   the login) and open `harbor-inbox`.
4. Send the sample enquiries. Either ask in the channel:

   > @harbor-scout work through data/leads.csv and score every lead

   or post them as if they were arriving one at a time:

   ```bash
   MM_USER=<your username> MM_PASSWORD=<your password> \
     python scripts/seed_mattermost.py --url http://localhost:8065 \
       --team <team slug> --agent harbor-scout --delay 5
   ```

   `--dry-run` prints the messages without connecting, and `--limit 5` sends
   only the first five.
5. Open `harbor-review`, read the drafts and reply `APPROVE` or tell the
   writer what to change.
6. Ask `@harbor-keeper today` for the summary.

## Try your own enquiry

Paste one into the inbox:

> @harbor-scout Anjali here from Pune. Moving in by December, need a kitchen
> and two wardrobes, around 9 lakh. Can a designer come on Saturday?

The playbook gives this 3 + 3 + 2 + 1 = 9 points, so expect `HOT`.

## Demo without a chat app

Two more scripts show the desk without Mattermost, Slack or Teams. They talk
to Switch's "Custom app (webhook)" platform.

```bash
# 1. print what the desk says back (terminal one)
SWITCH_SIGNING_SECRET=<signing secret> python scripts/receiver.py

# 2. send the sample enquiries into the room (terminal two)
SWITCH_EVENTS_URL=<address Switch shows> SWITCH_TOKEN=<inbound token> \
  python scripts/feed.py --join --delay 5
```

`--dry-run` prints the events without sending, and `--limit 5` sends only the
first five. Sending the same file twice is safe: each enquiry has a fixed id and
Switch handles it once. [docs/walkthrough.md](docs/walkthrough.md) is a shot
list for recording the whole desk in Console.

The webhook platform is in an open pull request on Switch and may not be in
your version yet.

## What is verified

- The feed and the receiver, against a running Switch: connection, room
  creation, each enquiry arriving once, a resend ignored, and a signed reply
  printed.
- The Mattermost seed script, against a stand-in for the Mattermost API in the
  tests. It has not been run against a real Mattermost.
- The scout's scoring on all 20 sample enquiries, run by hand.
- The writer's tiers and evidence block on four sample leads, and the keeper's
  summary on a made-up event log, each run by hand outside Switch. Of the four
  drafts, three came out `REVIEW` with the right reason and one `ROUTINE`.
- The template, with Switch's own template reader.
- Not yet seen: the agents answering inside Console. See the walkthrough.

## Check the files

```bash
pip install pyyaml pytest
pytest
```

## Change a rule from the chat

The playbook lives in both rooms as a document called **Lead playbook**, so the whole team can see the rules the scout is using. Ask the scout what it scores on, or tell it to change a rule, for example "enquiries from Nashik now count as local". It applies the new rule from the next enquiry on, and you can put the change into the document so it stays.

## Make it yours

- Change the scoring table and the offer in `data/playbook.md`, and paste the same text into the template's `docs:` content (a test checks the two match).
- Edit the `instructions:` of an agent to change how it behaves.
- Add more rooms or agents in the template; each room names its members.
