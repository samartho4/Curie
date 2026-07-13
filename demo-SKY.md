# Curie — the SKY demo (v-final). Replaces demo-and-submission.md §A.

Why the old script was weak: it ended on a talking-head stat dump ("70–90% fail at Microsoft…") and only
showed the ONE @mention→card moment. Judges reward what they can SEE working, live, that no one can fake.
This version SHOWS the maximum across surfaces as ONE causal story, and the impact is *demonstrated*, not recited.

## The three insights we're finally using (from all our iterations)
1. **Bubble Lab / Pearl genre** (the winning Slack-agent demo): real tools + real data (live queries, never mocked),
   learning shown on screen, and THE killer beat — *conversation becomes durable autonomous infrastructure*
   ("do this every Monday" → a standing job appears and runs). We steal this exact escalation beat.
2. **The live coding-agent run = the authenticity spine.** Split screen: Slack (where work is DISCUSSED) + a
   terminal/Claude Code (where work is DONE). A REAL experiment launches, fails for real, and its run-record posts
   itself back into Slack → Curie's record writes itself → a hypothesis's evidence ticks up. No scripted competitor
   can fake a real cross-tool loop. This is what replaces the stat dump.
3. **Setup/payoff loop + the "no filing" contrast** (83 Sciences recon): plant "why did we abandon X?" in the cold
   open; pay it off when a new teammate asks Curie and gets the cited answer + the living hypothesis map.

## THE SCRIPT (~2:50, one continuous story, everything on-screen is real)

**COLD OPEN — no logo.** Screen already on #experiments.
- **0:00–0:15 · The villain: forgotten knowledge.** Time-lapse scroll of #experiments (Anika/Marco/Priya, months
  of real runs). A new member DMs: *"why did we kill the ESM full fine-tune?"* → *"🤷 ask Anika, she left."*
  Caption: **Labs forget. People leave. The knowledge was right there.**

- **0:15–0:50 · THE CHECK (live, uncut, visible timer).** Type `@Prior planning to fine-tune the ESM baseline, lr
  1e-4, batch 32, v1`. The plan streams — *Checking priors… · searched the record · checked the literature* — then
  the card: ⚠️ **This was already tried** (Anika, Mar 12, gradient collapse), settings diff (lr/batch/split all
  match), a bioRxiv null result. Beat. VO: *"Real search over the lab's own Slack, real literature, eight seconds."*
  Title card **Curie** as punctuation.

- **0:50–1:35 · THE LIVE RUN — the beat no one can fake.** Split screen. Left = Slack. Right = a terminal. Priya
  clicks *Proceed anyway* + a one-line rationale. On the right, a REAL training script launches (tiny proxy model,
  deliberately hot LR) and **fails for real** — loss → NaN in ~15s, live logs scrolling. Its last line posts a
  structured **run record back into #experiments**. On the left, Curie ingests it: the experiment's List row flips
  to *Failed*, its notebook writes itself, and **H2's evidence count ticks up on screen**. Caption: **Nobody filled
  in a form.** VO: *"The run happens where runs happen. The memory happens where the team lives."*

- **1:35–1:55 · ESCALATION — chat becomes standing infrastructure (Bubble Lab's move).** Priya: *"@Prior from now
  on, preflight every plan in this channel, and every Monday post which of our beliefs new evidence has changed."*
  → a standing-capability card appears (a scheduled job, visible in App Home). Caption: **One sentence → a running guardian.**

- **1:55–2:30 · THE PAYOFF — the cold open returns.** The new member from 0:10 asks **@Prior** *"where does the lab
  stand?"* → the hypothesis map: **H2 🔴 Refuted (2 against) · H1 🟢 Supported (3 for) · H3 🟡 Open (1 running)**,
  every claim one click from its evidence. Hold. VO: *"Everything this lab believes, is testing, and has killed —
  compiled from the conversation. This screen has never existed."*

- **2:30–2:50 · Close (show, don't recite).** Quick cut montage: the List, a self-written notebook canvas, the App
  Home counter ("collisions caught: 4 · GPU-days saved"). VO: *"No filing. No data entry. The record writes itself
  — and no experiment starts blind."* End card: `Curie — your lab's memory · ask @Prior · try it: paste your plan in #experiments`.

## What we must BUILD to shoot this (in priority order)
1. **Run-reporter** (`scripts/demo_run.py` + a `/run-report` inbound path): a real training script that fails fast
   and POSTs a run-record to #experiments; Curie ingests it (reuse the 🧪 logging extractor) → updates the row +
   hypothesis evidence. THIS is the live-run beat. ~½ day, small Fable task, context7 for chat.postMessage/webhook.
2. **Escalation → weekly belief-digest** (`listeners/standing.py` + Bolt scheduler): `@Prior from now on…` registers
   a scheduled task that each Monday posts belief-changes; the ack card shows it's live. ~½ day, Fable task.
3. (stretch) message shortcut "Log to Curie" for the non-reacji log path.

## What we DROP from the demo
- The "70–90% fail at Microsoft/Netflix/Airbnb" recitation → moved to the Devpost TEXT only (one line), never
  spoken on camera. The live run + the ticking evidence count IS the impact, shown.

## Production (unchanged discipline)
Light theme, zoom every card, visible timers, NO sped-up segments (real latency = credibility), one voice −16 LUFS,
no copyrighted music, record UI + VO separately, upload ≥24h early, verify public in incognito. The sandbox judges
test must still work cold WITHOUT the terminal (the Slack-only path stands alone); the live run is the video's spine.

---
## REFINEMENT (v2) — coding-agent run + real-time autonomy (from Samarth's deep-dive)

### The live run = a real CODING AGENT, not a script
- **Producer = Claude Science (hero) or Cursor (backup).** The agent runs the ESM experiment (a tiny proxy that
  fails fast — NaN in ~15s) and **posts the run-record into #experiments via the Slack MCP** it has connected.
  Story judges see: *scientist tells an AI agent to run it → agent runs → the record writes itself → the belief
  updates.* Three real tools (Claude Science + Slack MCP + Curie). This is the "real tools, real data" spine.
- **Curie side to build: ambient ingestion.** A `message.channels` listener in #experiments that detects a
  run-record message (posted by the coding agent), extracts {experiment, status, outcome} (reuse the 🧪 extractor),
  updates the List row + hypothesis evidence — with NO human 🧪 needed. That's the automatic magic.
- Reliability: Claude Science↔Slack MCP is the hero path; if its connector isn't ready on demo day, Cursor's Slack
  MCP is the proven backup (19 tools, already installed). Either posts the identical run-record; Curie ingests the same.

### Autonomy shown in REAL TIME (three visible behaviors, not one un-demoable cron)
1. **Proactive belief-change alert (event-driven — THE star).** The moment the run flips H2 → Refuted, Curie posts,
   unprompted: *"⚠️ Your belief H2 just changed → Refuted. New evidence: exp-142 failed."* Nobody asked. It fires
   live, during the run, because a belief changed. This is the autonomy judges can SEE.
2. **Ambient plan-checking.** After `@Prior from now on, preflight every plan here`, a teammate posts a plan as a
   plain message (no @mention) → Curie checks it anyway. Visible proof of a standing behavior.
3. **Weekly digest via run-now.** `@Prior show this week's digest` runs the exact scheduled job on camera and reveals
   the real output; VO carries the "every Monday, automatically" claim (Bubble Lab's build-then-execute pattern).
   App Home shows "next digest: Monday" as proof it's standing.

### Build list (revised, priority order — all small Fable tasks + context7)
1. **`listeners/ambient.py`** — message.channels listener: (a) ingest run-record messages → update row + evidence →
   (b) if a hypothesis status flips, post the proactive belief-change alert; (c) if ambient-preflight is ON, auto-check
   plan-shaped messages. [enables the live-run ingest + the real-time autonomy star]
2. **`listeners/standing.py`** (or extend ledger) — `@Prior from now on…` enables ambient-preflight + registers the
   weekly digest; `@Prior show this week's digest` / a button triggers it now. App Home shows the standing job.
3. **digest function** over the ledger (belief-changes since last run) — used by both the schedule and run-now.
- The coding-agent side is a DEMO SETUP step (connect Slack MCP in Claude Science/Cursor; a `demo_run` the agent
  executes), not Curie code. Document it in a runbook.

### Demo script delta (replaces the old 1:35–1:55 escalation beat)
- **0:50–1:35 · Live run (Claude Science).** Split screen. In Claude Science: *"run the ESM fine-tune, lr 1e-4,
  batch 32, v1."* Real logs → NaN. It posts the run-record to #experiments (Slack MCP). Curie auto-ingests: row →
  Failed, notebook writes itself. **Then, unprompted, Curie posts the belief-change alert: H2 → Refuted.** VO: *"No
  one told it to say that. A belief changed, so it spoke."* ← the new peak.
- **1:35–1:50 · Standing behavior.** `@Prior from now on preflight every plan here.` A teammate drops a plan, no
  @mention → Curie checks it. Caption: **It acts without being asked.**

---
## CLAUDE SCIENCE runbook (how to show it — solved)
- Claude Science web UI = localhost:8765. Slack connector already ON (project-level; inherits to every session).
- On demo day, in a Claude Science session, prompt: *"Run a quick ESM fine-tune (lr 1e-4, batch 32, v1) on a tiny
  proxy model — it will fail. When done, post a run record to the #experiments Slack channel in EXACTLY this format:
  `📊 Run exp-142 | status: failed | outcome: <one line> | params: model=ESM2, lr=1e-4, batch=32, split=v1`."*
- Claude Science runs it locally, then posts via the Slack connector (as the "Claude" app). Curie's ambient
  listener ingests it → row → Failed → H2 evidence ticks → belief-change alert fires. All real, cross-tool, over MCP.
- Backup if Claude Science's Slack write flakes on the day: Cursor's Slack MCP (19 tools) posts the identical
  run-record; OR `scripts/demo_run.py` (a real failing training script) posts it via chat.postMessage. Same ingest.
