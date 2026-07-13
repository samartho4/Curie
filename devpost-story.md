# Curie

**No experiment starts blind.** The lab's memory, in Slack.

---

### Tagline options (for the Devpost tagline field — pick one)

- The lab's memory, in Slack — so no experiment starts blind.
- A self-writing lab record that checks new work against everything the team already tried.
- Curie checks your plan against what the lab already knows, and keeps the record that told it.

---

## Inspiration

Marie Curie's lab notebooks are still radioactive. They're kept in lead-lined boxes, and a researcher who wants to read one signs a liability waiver first. A century later they're priceless.

A lab's Slack is the opposite. It holds most of what a team actually knows — which configs failed, which reagent lot went bad, why someone dropped an approach back in March — and it's worthless the day that person leaves. The knowledge is sitting right there in a channel, but nobody scrolls six months back, so the lab quietly re-runs the dead experiment.

What started this was a small, familiar moment: someone new asks "why did we kill the ESM fine-tune?" and the honest answer is "ask Anika — she left." Curie is an attempt to keep that answer.

## What it does

You mention @Prior with a plan — "planning to fine-tune the ESM baseline, lr 1e-4, batch 32, v1" — and before you start, it checks that plan against what the lab has already done. It searches the team's own Slack history, a structured record of past experiments, and the literature, and comes back with one of three verdicts:

- **Collision** — this was already tried. Here's who, when, the settings that match, and how it went (e.g. "Anika, Mar 12, gradient collapse").
- **Near-miss** — close to something that's been done, and here's the difference.
- **Clear** — nothing found, go ahead.

Every result gets written into a native Slack List — the "Lab Record" — with hypotheses as parent rows and experiments underneath them. React 🧪 on a result and it's logged. Ask "where does the lab stand?" and it draws the current map: which hypotheses are supported, which are refuted, which are still open, each one a click from its evidence.

The part we like most is the record keeping itself. When another agent — we use Claude Science — runs an experiment and posts the result into the channel, Curie reads it, updates the matching row, recomputes the hypothesis, and if a belief actually changed, it says so on its own. No form, no data entry.

## How we built it

Curie is a Slack app, not a wrapper in front of one. It runs on Bolt for Python over Socket Mode and uses the new agent messaging experience — channel mentions, DMs, the message stream in a channel, emoji reactions, and App Home.

The record is Slack itself. One Slack List (through the Lists API), a few canvases, and message permalinks as foreign keys. There is no external database and no vector store, and it never copies Slack data out — partly because Slack's terms say not to, mostly because the live data is the whole point.

Retrieval uses Slack's Real-Time Search (`assistant.search.context`) as the live index, the List as the structured source of truth, and literature last. Queries are alias-expanded and capped at three searches per verdict.

The verdict is deterministic, and that was on purpose. The model's job is deliberately small: turn free text into a set of parameters, and write the explanation. A plain rule compares the parameters and decides collision / near-miss / clear. We don't let the model make the call, because a model at temperature will give you two different answers on the same plan, and the one mistake this product can't make is telling you you've done something you haven't.

The code is split into lanes that don't cross without a reason: listeners (the Bolt handlers), pipeline (pure logic — the verdict engine, logging, the ledger), tools (thin API wrappers), and a single LLM client with JSON-validated output. There's an eval harness of labeled plans whose pass condition is just: zero false collisions. It runs on a small EC2 box.

## Challenges we ran into

The hardest problem was calibration. Early versions were too eager. The model would "find" a collision that wasn't real, or worse, hand back a card that said "no prior work found" in the headline and then listed two matching experiments right underneath it. A verdict that contradicts itself is worse than no verdict. Fixing it meant taking the decision away from the model entirely and adding a guard, plus an eval that fails the build on any false positive. A related bug had a plan colliding with its own message — that one needed an empty-diff check.

The platform is new and moves faster than its own docs. Partway through, the agent messaging experience became mandatory for new apps and the older assistant path was closed, so parts of our written spec were already wrong and the smoke tests, not the documentation, had the final word.

Socket Mode has sharp edges. Two copies of the app running at once will quietly split events between them, so half your mentions land on a dead process. Streaming only works inside a thread. Timestamps are always "now," so a six-month history can't live in message dates — it has to live in the List's date columns instead.

The most stubborn one was live, and it taught us the most. The whole autonomy beat rests on one thing: another agent posts a run-record into the channel, and Curie ingests it unprompted. It just… didn't. Silently. We checked everything — the `message.channels` event was subscribed, `channels:history` was granted, the bot was in the channel, the deployed code was current, we re-registered the subscription and restarted. Mentions arrived fine; plain channel messages never did. On this workspace, that event simply wasn't being delivered. (Along the way we also found the leading 📊 arrives as a `:bar_chart:` shortcode in the payload, not the unicode character, so an exact-match gate had been skipping it — the parser was fine, the gate in front of it wasn't.)

So we stopped fighting the event. The bot already reads the channel through `conversations.history` — which does work — so we added a small poller: every few seconds it reads recent messages, ingests any new run-record exactly the way the event handler would, and shares the same dedup so nothing fires twice. The autonomy beat went from fragile to robust, and it now works even if a judge's workspace has the same delivery quirk. The lesson was blunt: when the platform won't hand you the event, use the read path that already works.

## Accomplishments that we're proud of

It works in a real workspace, live, not in a mock. The collision check returns a correct, self-consistent card on a plan that really was tried before. The Lab Record and the hypothesis map render from real rows. The weekly digest posts with a native chart. And the cross-tool loop fired end to end in front of us: Claude Science posted a run, and seconds later — with nobody asking — Curie announced that a belief had flipped.

The whole memory is Slack-native — no database to run, nothing copied out, no ML infrastructure to keep alive.

And we made "don't cry wolf" into something you can test. The verdict is deterministic and the eval gates on zero false collisions, so the property we care about most isn't a hope, it's checked on every change.

The cross-tool loop is the part that still surprises me: one agent runs the experiment, a different one keeps the lab's memory, and they meet in a Slack channel with no glue code between them.

## What we learned

The query this whole thing lives on — "has this exact thing been tried" — is the specific kind of question language models are worst at. They overweight how similar two things sound and quietly merge things that aren't the same. The fix isn't a smarter prompt, it's a structured layer under the model doing the deterministic part. Slack Lists turned out to be a good enough version of that layer that building our own was never worth it.

We also learned that autonomy has to be shown, not asserted. A scheduled job running quietly at 9am Monday is real, but nobody believes it. An alert that shows up the moment a belief changes, that nobody asked for, is the same feature and it lands completely differently.

## What's next for Curie

- Confidence on records, so a hasty or aging entry counts as weaker evidence instead of being trusted forever.
- Skipping re-checks on cosmetic edits — hash the plan, only re-verify when the substance changes — to protect the search budget.
- A message shortcut, "check this against prior work," for plans that were posted without a mention.
- Proactive staleness: scan the open hypotheses for evidence that's been superseded, and post the update before anyone asks.
- A dated belief-changelog, so "what did we believe in March?" has an honest answer.

And first: folding the poller and the event path into one hardened ingest — so the record writes itself every time, on any workspace, not most of the time.
