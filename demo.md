# Curie — demo (the one I actually record)

**~2:45. One take feel. I'm talking like I'm showing a labmate, not pitching.** Slack on the left the
whole time; Claude Science slides in once. Every spoken line has a 3–5 word caption on screen (judges
watch muted). ~290 words of VO — read it once out loud, then cut anything that sounds like an ad.

Voice check: I *know* this product. I'm not selling it, I'm using it. Short sentences. No "revolutionary",
no "seamless", no stats read aloud. If a line feels like a headline, rewrite it as a sentence I'd actually say.

Format below: **SAY** = what I speak · **SCREEN** = what's visible · **CUT** = the only edits that matter.

---

### 0:00 — Cold open · *the problem, not a logo*
**SCREEN:** `#experiments`, already open. Fast scroll up through six months of runs, then settle at the
bottom on Priya's message: *"did anyone try the full ESM fine-tune? can't find anything"* → Marco:
*"Anika ran a bunch of ESM stuff but she left last month. good luck."*
**SAY:** *"This is our lab's Slack. Six months of experiments in here — and the person who ran half of them
just left. So when someone new wants to try something, they can't tell what we've already done."*
**CAPTION:** **The knowledge leaves when the people do.**
> No title card yet. Let the problem sit for a second.

### 0:15 — The check · *ask before you burn a week*
**SCREEN:** Priya types the plan (see cue sheet #1). It streams — *Checking priors… reading the record,
searching Slack, checking the literature* — then the ⚠️ card resolves.
**SAY:** *"So instead of guessing, she asks Curie first. It reads our whole history and the literature —
takes about eight seconds — and stops her. We already tried this. Anika, back in March. It blew up —
gradient collapse. Same model, same learning rate, same batch."*
**CAPTION:** **Already tried. Already failed. Cited.**
> Title card **Curie** drops here, as punctuation — right after "it blew up." Don't cut the 8s wait; the wait is the proof.

### 0:50 — The live run · *the part I like* — CUT ①
**SCREEN:** Window slides to a **split** — Slack left, **Claude Science** right. In Claude Science I type
the run prompt (cue #2). It posts `📊 Run … LoRA beat the baseline, +2.6%` into Slack through its own
connector — tagged *Sent using Claude*. Cut back to Slack full-frame. Wait. ~8s later Curie posts on its own.
**SAY:** *"Here's the part I like. This is Claude Science — a different tool, where the actual work happens.
I tell it to log the run. It drops the result straight into Slack. And then, nobody asked it to — Curie
notices the belief it was tracking just changed."*
**CAPTION:** **Nobody wrote it down. Curie was watching.**
> **CUT ①** = Slack → split-screen (slide, ~0.3s) and back. This is the only "production" moment. Real latency stays in.

### 1:35 — One sentence, standing · *the Bubble-Lab move*
**SCREEN:** Priya types the standing instruction (cue #3). A small card confirms: preflight **on**,
Monday digest **scheduled**.
**SAY:** *"And you set it up the way you'd ask a teammate. One sentence — and now it checks every plan
automatically, and posts what changed every Monday. No dashboard, no settings."*
**CAPTION:** **One sentence → a standing habit.**

### 1:55 — Where the lab stands · *the map nobody built*
**SCREEN:** `@Curie where does the lab stand?` → the hypothesis list + native bar chart. Hold. Quick flash of App Home.
**SAY:** *"Any time, you can just ask where things stand. And this map — nobody made it. It's built from the
conversation we were already having. Every line links back to the run that earned it."*
**CAPTION:** **Every belief, one click from its evidence.**

### 2:15 — The callback + close · *the opening question, answered* — CUT ②
**SCREEN:** Priya asks the cold-open question for real: `@Curie why did we drop the full ESM fine-tune?`
→ the answer lands with **Anika's run as a permalink**. Hold one beat on the link. Then a slow montage,
~1.3s each: the **Lab Notebook** canvas (the line *"no filing, no forms, no data entry"* readable) →
**Files** (every canvas stamped *Curie*) → **Tools** (the two workflows) → **App Home** ledger. End on the
quiet, complete `#experiments`.
**SAY:** *"And that question from the start — the one nobody could answer? She just asks. There's Anika's
run, the reason, the link. Anika left in March. Her reasoning didn't. And none of this was typed up by
anyone — it wrote itself, out of the conversation. That's the whole idea. A lab notebook that keeps itself."*
**CAPTION (on the permalink):** **Anika left. Her reasoning stayed.**
> **CUT ②** = the montage. Five held frames, no fancy transitions — straight cuts on the beat.

### 2:40 — End card
**SCREEN:** Black. One line, then the try-it prompt.
**SAY:** *(silence — let it read)*
- **Line:** *A lab notebook that keeps itself.*
- **Try it:** `@Curie planning to fine-tune ESM2, lr 1e-4, batch 32, v1`

---

## The only cuts (so editing stays minimal)
- **CUT ①** (0:50): Slack → split with Claude Science, then back. A slide or hard cut — 0.3s. That's it.
- **CUT ②** (2:15→2:40): the closing montage — five straight cuts, ~1.3s each. No crossfades, no motion.
- Everything else is **one continuous screen recording.** Record the VO separately and lay it under. If a
  single beat misfires, re-record just that beat — they're independent.

## What I deliberately don't show
App Home tour, settings, onboarding, error states, a second use-case. Every extra second steals from the callback.
