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
| `data/playbook.md` | The scoring rules, the offer and the tone, for a made-up interiors firm |
| `data/leads.csv` | 20 made-up enquiries in English, Hindi and Marathi |
| `tests/` | Checks that the template and the data hang together |

All names, numbers and messages are invented. Replace `playbook.md` with your
own rules and the same desk works for your business.

## The three agents

- **scout** reads each enquiry, scores it with the playbook and replies in the
  thread with one line: `HOT`, `WARM` or `COLD`, and why. Hot leads go to the
  review room.
- **writer** drafts a short first reply in the customer's language and waits.
  It only promises what the playbook allows.
- **keeper** maintains `data/pipeline.md` and answers "today" with counts and
  the two leads that have waited longest.

## Run it

You need a running Switch with Switch Console connected to a machine that has a
coding agent installed (Claude, Codex or OpenCode).

1. Copy `data/` into each agent's working directory, or point the template's
   `directory` at this folder.
2. In Switch Console, create a team from `lead-desk.template.yaml`. Pick a
   short team name, for example `harbor`.
3. Open `harbor-inbox` and ask:

   > @harbor-scout work through data/leads.csv and score every lead

4. Open `harbor-review`, read the drafts and reply `APPROVE` or tell the
   writer what to change.
5. Ask `@harbor-keeper today` for the summary.

## Try your own enquiry

Paste one into the inbox:

> @harbor-scout Anjali here from Pune. Moving in by December, need a kitchen
> and two wardrobes, around 9 lakh. Can a designer come on Saturday?

The playbook gives this 3 + 3 + 2 + 1 = 9 points, so expect `HOT`.

## Check the files

```bash
pip install pyyaml pytest
pytest
```

## Make it yours

- Change the scoring table and the offer in `data/playbook.md`.
- Edit the `instructions:` of an agent to change how it behaves.
- Add more rooms or agents in the template; each room names its members.
