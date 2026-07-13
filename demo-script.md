# Curie — demo script (show, don't tell)

**Lab:** Anfinsen Lab · **Agent:** `@Curie` (product, agent, mention, icon — all one name now)
**Length:** 2:30–2:40 (judges bail at 3:00) · **Criteria:** Creativity · Functionality · Impact (+ Best UX / Most Innovative / Best Tech)

**The one rule:** never *say* what Curie does — *show* it doing it, on one unbroken thread. One hypothesis
("scaling the ESM head") is set up, hit, updated, and answered across the whole film. Every spoken line is also
an on-screen caption (mute-proof). Nothing is mocked — every beat below has already run live.

**What we cut and why:** the old script *told* judges a statistic ("70–90% of experiments fail, even at Microsoft
and Netflix"). Statistics are telling. We deleted all of it. The waste is now *enacted* in the first ten seconds —
a real scientist about to re-run a dead experiment — so the judge feels it instead of being quoted it. Let them do
the multiplication in their own head; that's what makes them lean in.

---

## The spine (memorize this, everything else serves it)

> A lab's memory lives in Slack — and Slack forgets. Curie is the notebook that keeps itself: it reads the plan
> before you run it, catches the experiment you already failed, and writes the record while you work — so the
> knowledge stays when the person leaves.

Marie Curie's notebooks are so meticulous they're still radioactive, kept in lead-lined boxes, priceless a century
on. A lab's scrollback is the opposite — worthless the day someone leaves. That contrast is the whole pitch. Say it
once, at the end, and only if there's room.

---

## PRE-RECORD SETUP (do once, before rolling)

1. **Deploy** current code (App-Home Belief Ledger + ambient-preflight poller live). Cursor prompt at the bottom.
   **NOTE (Jul 13):** two changes since the last running build need one `python app.py` restart to go live —
   the `@Curie` copy fix and the new **recall intent** (`pipeline/recall.py`) that powers the PAYOFF beat
   ("why did we drop the full ESM fine-tune?"). Without the restart, that one question falls back to the plan
   parser; the rest of the film is unaffected.
2. **Clean start state — the recording-day reset checklist** (learned from the Jul 13 live walkthrough):
   - **Reseed the List** so H2 ("scaling the ESM head") reads **Refuted / 0-for-2** again. This is what makes the
     autonomy star land: the belief-change alert is **flip-triggered** (it fires only when a hypothesis *changes
     status*), so H2 must start Refuted for the Claude-Science LoRA win to flip it Refuted→Open **on camera**. In a
     messy state where H2 is already Open/Supported, the run ingests but no alert fires. (`python -m seed.seed_list`
     → new `CURIE_LIST_ID` in `.env` → restart → re-share the List.)
   - **Remove the stale `📊 Run exp-301 … +2.1% Spearman (succeeded)` record** (and the old belief-change alert). That
     lingering *success* is why the collision card sometimes cites "+2.1% improvement" instead of Anika's gradient
     collapse — the record holds both and the LLM picks one. Clear it and the collision cites the failure every time.
   - **Reconcile the two experiment channels.** Claude Science flagged it live: the old `#experiments`
     (`C0BGB4YK05C`, exp-208–211) is now **#experiments-old**, and the new `#experiments` (`C0BGT5XV082`) has
     exp-301/314. Point `CURIE_CHANNEL_ID` at the one true channel and make sure the seeded history + the run beat
     live in the SAME channel, or the map/collision read from a different place than the camera shows.
   - **Delete today's test messages** in `#experiments` (the two `@Curie` plan/recall probes + exp-314) so the cold-
     open scroll is clean.
3. **Stage the room** (all built already — just confirm on camera):
   - Workspace reads **Anfinsen Lab** (rename saved server-side; if the client still shows "Prior Lab," fully quit
     and reopen Slack once so the boot cache refreshes).
   - Sidebar is a real lab: **`#experiments`** (the star — history, charts, Lab Record) · **`#embeddings-infra`** (GPU
     & pipelines) · **`#papers`** (paper club — foreshadows the H2 collision) · **`#wetlab-collab`** (Reyes-lab assays,
     the H3 ground truth) · **`#general`** · **`#random`**. No sales/social clutter. All seeded with real multi-author
     chatter (Anika · Marco · Priya).
   - **Curie** under Agents & apps with the purple bell-curve avatar; the same icon on every Curie message.
   - **Files tab** already holds the self-writing record: Canvases (the master **Lab Notebook** front page +
     H1/H2/H3 hypothesis notebooks + **Protocols**, **Compute & pipelines**, **Wet-lab & instruments**) and Lists
     (Reading list, Assay tracker, **Datasets & model registry**). **Tools tab** holds the **Curie** agent + TWO
     published workflows — **Log a run** (dry-lab, in #experiments) and **Request wet-lab assay** (wet-lab, in
     #wetlab-collab). Together they read as a real lab's whole operating surface, all Slack-native.
   - Light theme, cursor halo on, zoom-ins ready.
4. **Two windows, split-screen:** Slack (left, main), **Claude Science** (right, `localhost:8765`) for the run beat.
5. **One silent dry run** end-to-end before the real take. If a beat misfires, it's independent — re-run just that beat.

---

## THE FILM (beat by beat)

### 0:00–0:12 · COLD OPEN — the loss, enacted *(Impact)*
- **Screen:** a 3-second time-lapse scroll up `#experiments` — six months of real names, plots, dead ends flying by.
  It stops on a new member's DM: *"why did we drop the full ESM fine-tune?"* → a teammate: *"🤷 ask Anika — she left."*
- **Caption:** **Every lab's memory lives in Slack. Slack forgets.**
- **VO:** *(silence — let the shrug land.)*
- *No logo, no "meet Curie." Plant the question. We will answer it at 2:05 with a citation.*

### 0:12–0:48 · THE CHECK — uncut, real clock *(Functionality · Tech)*
- **Type in `#experiments`:** `@Curie planning to fine-tune ESM2-650M, lr 1e-4, batch 32, on the v1 split — full fine-tune.`
- **Screen:** the plan streams, sources naming themselves as they fire — *reading the plan · checking the record ·
  searching Slack · checking the literature · weighing the evidence.* Tiny captions echo each source. Don't cut — the
  wait is the proof it's really working.
- **Payoff — the verdict card:** ⚠️ **"This was already tried — and it failed."** Cites the exact run: *Anika,
  March 12 — gradient collapse at epoch 3, loss went NaN.* Then the honest diff: model / lr / batch **identical**,
  split differs. Beat on it.
- **Caption:** **Eight seconds. It read the lab's whole history — and the literature — before a GPU spun up.**
  → **Title card: *Curie*** (drops here, as punctuation, not an intro).
- *This is the beat that makes them believe. A real collision, a real citation, a real "what's different."*

### 0:48–1:38 · THE LIVE RUN — the cross-tool autonomy star *(Creativity · Tech — the peak)*
- **Cut to Claude Science (right pane).** Prompt it in plain English: *"Log our latest ESM run to #experiments:
  scaling the ESM head with LoRA, it beat the baseline this time, +2.6% Spearman."* Claude Science posts a
  structured **`📊 Run` record** into Slack through its own connector. Show the message land, tagged *sent from
  Claude Science* — a genuinely different tool.
- **Back to Slack. Wait for it — do not touch anything.** ~8s later, **unprompted**, Curie speaks at top level:
  ⚠️ **"Heads up — the evidence on *scaling the ESM head* just changed. It failed twice before; this run beat the
  baseline. That belief is now Open again."** The List row flips in the same motion.
- **Caption:** **Nobody wrote it down. Nobody asked Curie to speak. It was watching the lab think.**
- **VO:** *"The run happened in the coding tool. The memory happened where the team actually talks. Curie is the
  bridge between them — and it noticed on its own."*
- *This is the moment judges haven't seen before: not a bot you query, a colleague that keeps up.*
- **Slack-native variant (safer, connector-free — use if you'd rather not leave Slack):** in `#experiments`, click the
  **▶ Log a run** button right in the composer → a Workflow-Builder form pops (Experiment · Status · Outcome · Params)
  → submit → the identical `📊 Run …` record posts and Curie ingests it the same way. Same autonomy loop, zero code,
  pure Slack. This is a real published Workflow (Tools tab → Workflows → *Log a run*), not a mock.

### 1:38–1:58 · ESCALATION — one sentence becomes a standing guardian *(Creativity — the Bubble-Lab beat)*
- **Type:** `@Curie from now on, check every plan in this channel before we run it — and every Monday, tell us which beliefs the week's evidence changed.`
- **Screen:** a **standing-capability card** confirms it — ambient preflight **on**, Monday digest **scheduled**.
- **Caption:** **One sentence → a permanent lab habit.**
- *No new UI to learn. You delegate to Curie the way you'd delegate to a person.*

### 1:58–2:22 · PAYOFF — the record, made visible *(Quality of idea · UX)*
*(The cold-open question gets its answer in the CLOSE — hold it. This beat is the map: the whole lab, compiled.)*
- **Type:** `@Curie where does the lab stand?` → the **hypothesis map** renders with a **native Slack bar chart**
  (*Evidence per hypothesis*, supports vs contrasts): 🟡 **Scaling the ESM head — Open** (it flipped Refuted→Open one
  beat ago, on camera, when the LoRA run landed) · 🟢 **Curriculum ordering — Supported** · 🟡 **Synthetic
  pretraining — Open (1 running).** Every claim is a link to the evidence that earned it. Hold one second.
- **Then flash App Home** — the same ledger under *"Curie — your lab's memory · it writes itself,"* live counters:
  **6 experiments tracked · 3 hypotheses · 1 collision caught this month.** Same truth, two surfaces, zero upkeep.
- **Caption:** **Every belief, one click from the evidence that earned it.**
- **VO:** *"This map never existed before. Nobody built it. It compiled itself — from the conversation the lab was already having."*

### 2:22–2:52 · CLOSE — the vision, earned *(Impact)* — the SKY version (~30s; let it breathe)

The close has **four movements**. It's allowed to run long — this is the part a judge remembers. Every frame below
is a real screen already in the sandbox (I verified each live on Jul 13); nothing here is a mock. Shoot each frame
at rest, cursor still, light theme, then cut on the beat. Keep the reset done first so the state is pristine.

**① THE CALLBACK — the gut-punch (2:22–2:31, ~9s).** *Bookend the cold open.* Same new teammate, same question they
asked at 0:10, now typed to Curie: `@Curie why did we drop the full ESM fine-tune?` Hold on the streamed
*"Searching the lab's memory…"* then the answer landing with **Anika's run permalink** under *Source:*.
- **Caption (mute-proof):** **Anika left in March. Her reasoning didn't.**
- **VO (quiet, let it sit):** *"The person who ran this left three months ago. The answer stayed."*
- *This is the emotional peak — the knowledge outlived the person. Do not rush it. One full second on the permalink.*

**② THE PROOF — "nobody built any of this" (2:31–2:42, ~11s).** A fast montage, each frame held ~1.3s, cursor still.
Shoot these exact screens, in this order (all confirmed live):
  1. The **Lab Notebook** canvas, top of frame — the subtitle reads *"The self-writing record. Curie compiles this
     from the conversation in #experiments — no filing, no forms, no data entry."* **Let that line be readable — it
     IS the thesis.**
  2. Scroll the same canvas one beat: **Active hypotheses** (🟢 H1 · 🔴 H2 + the ⚠️ landmine · 🟡 H3), then
     **Methods → Protocols**, **Data & models → Datasets & model registry / Reading list / Assay tracker**.
  3. **Files → Canvases** list: every row stamped **"Curie · edited today"** — Lab Notebook, the three hypothesis
     notebooks, Protocols, Compute & pipelines, Wet-lab & instruments. Linger half a beat on the *Curie* byline.
  4. **Tools → Managed by you:** the two published workflows — **▶ Log a run** ("Curie reads it into the Lab
     Record") and **Request wet-lab assay** ("Curie logs results when they land").
  5. **App Home:** *"Curie — your lab's memory · it writes itself"* with the live counters — **6 experiments tracked ·
     3 hypotheses · 1 collision caught this month** — and the hypothesis stack under *Where the lab stands.*
- **VO (over the montage, steady):** *"Nobody wrote any of this down. No filing. No forms. No data entry. It
  compiled itself — out of the conversation the lab was already having."*

**③ THE METAPHOR — earn the name (2:42–2:49, ~7s).** Slow push on the clean `#experiments` channel, the record
quietly complete behind the text.
- **VO (slow, three beats):** *"Marie Curie's notebooks are still radioactive — a hundred years on, kept in
  lead-lined boxes, too valuable to throw away. Every lab's Slack is the opposite: priceless while you're there —
  gone the day you leave."*
- **Caption:** **One of these labs never forgets.**

**④ THE LANDING (2:49–2:52, ~3s).** Cut to black. One line fades up, then the end card.
- **The line (this is the nail):** ***Curie is the notebook that keeps itself.***
- **End card — the judge's next move (leave it on screen 3s):** *Try it — in any channel:*
  `@Curie planning to fine-tune ESM2, lr 1e-4, batch 32, v1`
- **Tagline under it:** ***Curie — the memory of what your lab believes, and why.***

**Alt final lines (pick by how the VO lands):** *"The person leaves. The knowledge stays."* · *"A lab's memory
should outlive its members. Now it does."* · *"Six months of work, and none of it walked out the door."*

**Why this close wins:** it doesn't *describe* the product — it re-asks the cold-open question and lets the answer
arrive, then proves with five real screens that the whole record wrote itself, then names the feeling (a notebook
that outlives the people). Impact shown, not claimed.

---

## LIVE-RUN RUNBOOK (the exact order I drive in Chrome — follow it beat for beat)

1. **Slack → `#experiments`.** Post the ESM plan mention → screenshot the **collision card** (must cite Anika's
   *failed* March run, not a rerun). This is the make-or-break beat; verify the citation before moving on.
2. **Claude Science tab.** Prompt it to post the `📊 Run … scaling the ESM head … beat baseline` record → confirm
   "posted to #experiments."
3. **Slack.** Wait one poll interval (~8s) → screenshot the **unprompted belief-change alert** + the flipped row.
4. **Slack.** Post the "from now on… every Monday…" line → screenshot the **standing-capability card**.
5. **Slack.** Post `@Curie why did we drop the full ESM fine-tune?` → screenshot the **cited answer + permalink**.
6. **Slack.** Post `@Curie where does the lab stand?` → screenshot the **map + native bar chart**.
7. **Curie → Home tab.** Screenshot the **Belief Ledger** ("Curie — your lab's memory").
8. **Files tab.** Show **Canvases** (H1 · H2 · H3 hypothesis notebooks + Lab Record) and **Lists** (Reading list,
   Assay tracker, Lab Record) → open the **H2 notebook** for one beat (claim · evidence for/against · landmine · what
   would change our mind) → screenshot. This is the self-writing record made visible.
9. **`#experiments` composer.** Click the **▶ Log a run** button → the form pops → submit a run → screenshot the
   `📊 Run …` record landing (and, if you want the full loop on camera, wait one poll interval for Curie to ingest it).
   *(Optional — dry-run this once before the real take so you know the format parses.)*
10. **Tools tab.** Show **Agents → Curie** and **Workflows → Log a run** side by side — the Slack-native surfaces a
    Slack judge will recognize instantly.

Verify each beat visually before the next. Beats are independent — a miss is a re-shoot of one beat, not the film.

---

## FALLBACKS
- **Autonomy star slow?** The `📊 Run` post and the alert are both real — just wait the poll interval; never fake it.
  Worst case, drop in a genuine pre-recorded take of this exact beat.
- **Judge's sandbox never depends on the cross-tool run.** The Slack-only path (paste plan → verdict → map → App
  Home) stands alone and is exactly what a judge reproduces from the end card.
- **Client still says "Prior Lab"?** Quit + reopen Slack once (server-side name is already "Anfinsen Lab").

---

## Naming note (settled, verified live July 13)
Setting the app icon + display name propagated everywhere: the agent now shows as **Curie** with the purple
bell-curve avatar, and **`@Curie` resolves** in autocomplete. The old `@Prior` dual-name workaround is retired —
product, agent, mention, and icon are all **Curie**. Use `@Curie` in every on-screen mention and every caption.

## Cursor prompt — redeploy the two staged code changes (only if not already live)
```
Two files: listeners/ambient.py (poller also ambient-preflights plan messages when that mode is on) and
listeners/app_home.py (App Home shows the Belief Ledger under the stats).
1. rsync listeners/ambient.py + listeners/app_home.py to the EC2 curie app dir.
2. sudo systemctl restart curie
3. Confirm "Curie is listening (Socket Mode)." + "CURIE-DIAG run-poller started …".
```
