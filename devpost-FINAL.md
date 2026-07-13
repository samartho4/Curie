# Curie

**The lab's memory, in Slack. It writes itself, so no experiment starts blind and no one keeps an ELN.**

*Product: Curie · you talk to it as @Prior · shown in a simulated computational protein-ML lab.*

## Inspiration

Marie Curie's lab notebooks are still radioactive. They're kept in lead-lined boxes, and you sign a waiver to read one. A century later they're priceless.

A lab's Slack is the opposite. It holds what the team actually knows: which config failed, which approach got dropped in March and why. And it's worthless the day the person who knew it leaves.

The fix is supposed to already exist. It's the electronic lab notebook. But scientists don't keep them up. Filing your own work into a second system is a chore, so it doesn't happen, and the knowledge stays stuck in a channel nobody scrolls back through. So the lab quietly re-runs the dead experiment.

It started with one moment. Someone new asks, "why did we kill the ESM fine-tune?" and the honest answer is "ask Anika, she left." Curie is an attempt to keep that answer.

## What it does

You mention @Prior with a plan, say "fine-tuning ESM, lr 1e-4, batch 32, v1," and before you spend the compute it checks that plan against what the lab has already done: your Slack history, a structured record of past experiments, and the literature. It comes back with one of three verdicts:

- **Collision.** Already tried. Here's who, when, the settings that match, and how it went.
- **Near-miss.** Close to something that's been done, and here's the difference.
- **Clear.** Nothing found, go ahead.

There's no filing. The record writes itself. When someone posts a result, or another agent runs an experiment and drops the numbers in the channel, Curie reads it, updates the matching row, recomputes the hypothesis, and if a belief changed it says so on its own: *"your belief 'scaling the ESM head beats full fine-tuning' just changed to refuted."* Ask "where does the lab stand?" and it draws the map of what's supported, refuted, and still open, with every claim one click from its evidence.

## How we built it

![Curie's architecture: Slack holds the memory, Curie checks plans and writes the record](https://raw.githubusercontent.com/samartho4/Slack4Good/main/docs/architecture-diagram.png)

The record lives in Slack, not in a database of our own. It's a List we call the Lab Record, plus a few canvases and links back to the original messages. There's no database and no vector store. Curie itself is a small Bolt for Python app on EC2, connected to Slack over Socket Mode.

It does the two things in the diagram. When someone posts a plan and mentions Curie, it searches the Lab Record, the channel (through Slack's Real-Time Search), and the literature, then posts back a verdict. When someone posts a run, Curie reads it, updates the row and the hypothesis, and posts an alert if a belief changed.

The design choice that mattered: Curie doesn't let the model decide the verdict. The model turns the plan into parameters and writes the wording, and a rule compares the parameters and picks collision, near-miss, or clear. The same model can answer the same question two ways, and this was the one place we couldn't allow that. An eval fails the build on a single false collision.

## Challenges we ran into

Early on, Curie flagged collisions that weren't real. Once it returned a card that said "no prior work found" and then listed two matching experiments right under it. That's when we took the verdict away from the model and gave it to a rule, and set the eval to fail the build on any false positive.

The bug that took longest was that plain channel messages never reached the app. Everything checked out. The event was subscribed, the scope was granted, the bot was in the channel, and the code was right. We put a log line at the top of the handler and it never printed. Mentions worked and messages didn't. We couldn't find why, so we stopped depending on delivery and poll the channel every few seconds instead.

## Accomplishments that we're proud of

It works end to end in a live workspace on real data: the collision check, the hypothesis map, the weekly chart, and the belief alert that posts on its own. The record is just a Slack List and some canvases, with no database and nothing stored outside Slack, so if you remove Curie the record is still there.

## What we learned

Language models are bad at the exact question this product is about: is a new plan the same as one we already ran? They treat things that sound similar as the same, so we kept that comparison in code and used the model only for reading and writing text. The other lesson is that autonomy only convinces people when they can watch it happen. An alert that shows up the moment a belief changes does that. The same check on a schedule nobody sees does not.

## What's next for Curie

- Confidence on records, so a hasty or aging entry counts as weaker evidence.
- Skip re-checks on cosmetic edits: hash the plan, and re-verify only when the substance changes.
- A message shortcut, "check this against prior work," for plans posted without a mention.
- Proactive staleness: flag a hypothesis whose evidence has been superseded, before anyone asks.
- The wet lab, where a repeated experiment costs a synthesis run and two weeks, not GPU-hours.
