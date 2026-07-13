# Curie — master plan for the sky demo (this round)

## Hosting decision (researched)
Free 24/7 hosting is mostly dead in 2026 (Render sleeps 15min, Railway/Fly killed free, Oracle queues).
**Winner: AWS EC2 t2.micro free tier** (12 months, 750 hr/mo) — you have AWS, runs Socket Mode as-is, no code
changes, and it's the judging-window host (Jul 14–Aug 6). Video is recorded on the Mac regardless (Claude Science
live-run is local). So: Mac for the video; AWS for the persistent judging-window deployment.

## Claude Science demo — SOLVED (from the product docs + your screenshots)
Claude Science (localhost:8765) runs code locally AND uses MCP connectors. Your **Slack connector is already ON**
at the project level — that's why there's no per-prompt connect button; every session inherits it. You demo it by
ASKING. The run-record contract (so Curie recognizes it): tell Claude Science to post EXACTLY this shape to #experiments:

    📊 Run exp-142 | status: failed | outcome: NaN at epoch 3, gradient collapse | params: model=ESM2, lr=1e-4, batch=32, split=v1

Claude Science posts it as the "Claude" app (you OAuth'd it). Curie's ambient listener sees the bot_message,
matches the `📊 Run` prefix, ingests → updates the row + hypothesis evidence → fires the belief-change alert.
Story: **Claude Science does the science; Curie (@Prior) keeps the memory — two agents over MCP.**

## What to build this round (one Fable agent, then test live)
1. `listeners/ambient.py` — `message.channels` handler in #experiments:
   - detect run-record `bot_message` (text starts `📊 Run`), NOT our own bot → parse {experiment,status,outcome,params}
     → update List row + hypothesis evidence (reuse reaction_added's extractor/record path).
   - after ingest, if a hypothesis status flips → post the **belief-change alert** (the real-time autonomy star).
   - if ambient-preflight mode ON → plain plan messages get auto-checked (reuse preflight).
2. `listeners/standing.py` — `@Prior from now on…` turns on ambient mode + registers weekly digest;
   `@Prior show this week's digest` runs it now (demo). App Home shows the standing job.
3. digest function over the ledger (belief-changes) — used by run-now + a best-effort weekly thread.

## Sequence (this round)
context7 shapes ✓ → Fable build (ambient+standing+digest) → live test (post a run-record as the bot, watch Curie
ingest + alert) → AWS deploy → live Chrome walkthrough (I drive, you watch).

## Demo (final) lives in demo-SKY.md. Impact stats: TEXT only, never on camera.
