# Curie — FINAL demo script (the one we shoot / run live)

**Lab:** Anfinsen Lab · **Agents:** Curie (product) / @Prior (handle) · **Target:** ~2:45 (judges bail at 3:00)
**Criteria to hit:** Creativity · Functionality · Impact (+ cross-track Best UX / Most Innovative / Best Tech)
**Golden rule:** ONE continuous causal story with a setup→payoff loop. Mute-proof — every VO line also a caption.
Every beat below is **proven live** already (collision+fix(b), poller autonomy star, digest+chart, map+chart,
escalation, App Home ledger). Nothing here is a mock.

---

## PRE-RECORD SETUP (do once, before rolling)

1. **Deploy** the pending code (App Home Belief-Ledger + ambient-preflight poller) — Cursor prompt below.
2. **Reset to a clean start state** (pick one):
   - *Pristine:* `python -m seed.seed_list` → paste new `CURIE_LIST_ID` in `.env` → restart curie → re-share List.
   - *Targeted (lower risk):* delete the exp-142…211 / probe / GAT test posts in #experiments; set the ESM
     experiment rows back to **failed/contrasts** so H2 reads **Refuted (0·2)** again.
3. **Rename workspace** "Prior Lab" → **"Anfinsen Lab"** (Settings → Workspace name).
4. **Build the two surface artifacts** (I do these live in Chrome):
   - *Files tab:* a pinned **"Lab Record — read me"** channel canvas (what @Prior does, how to log a run, how to
     read a verdict) + confirm the **Lab Record list** shows in Files.
   - *Tools tab:* a **"Log a run"** Workflow Builder form (experiment · status · outcome · params → posts a
     `📊 Run …` record → Curie's poller ingests it).
5. **Cast the workspace:** clean sidebar (channels: #experiments, #embeddings-infra, #papers, #general, #random),
   light theme, zoom-ins ready, cursor halo on.
6. **One dry run end-to-end** before the real take. Keep Claude Science + Slack web both open, split-screen.

---

## THE SCRIPT (beat-by-beat)

### 0:00–0:15 · COLD OPEN — the problem, enacted *(Impact)*
- **Screen:** time-lapse scroll of #experiments — months of real lab chatter in 3 seconds. A new member DMs:
  *"why did we drop the full ESM fine-tune?"* → *"🤷 ask Anika — she left."*
- **Caption:** **Labs forget. People leave.**  · **VO:** *(none yet — let it land.)*
- *No logo. No "meet Curie." Plant the payoff question.*

### 0:15–0:48 · THE CHECK — uncut, visible timer *(Functionality, Tech)*
- **Type (in #experiments):** `@Prior planning to fine-tune ESM2-650M, lr 1e-4, batch 32, v1 split — full fine-tune.`
- **Screen:** the live plan streams — *Checking priors… reading the plan · checking the record · searching the
  record · checking the literature · weighing the evidence* — tiny captions naming each source as it fires.
- **Payoff:** verdict card ⚠️ **"This was already tried."** Collision vs `exp E-…` — param diff (model/lr/batch
  **same**, split differs), the honest "what differs." Beat.
- **Caption:** **8 seconds. It reads your history, Slack, and the literature.** → **Title card: *Curie*** (now, as punctuation).

### 0:48–1:40 · THE LIVE RUN — the cross-tool autonomy star *(Creativity, Tech — the peak)*
- **Screen:** cut to **Claude Science** (right pane). Prompt it: *"Log our latest ESM run to #experiments: exp-142,
  ESM2 v1 full fine-tune, succeeded, +2.1% Spearman."* → Claude Science posts the structured **`📊 Run` record**
  to Slack via its connector (real cross-tool, "posted to #experiments, verbatim").
- **Back to Slack:** ~8s later, **unprompted**, Curie's poller ingests it → the List row updates → and Curie posts
  top-level: **⚠️ "Heads up — your belief *Scaling the ESM head…* just changed → *Open*. New evidence: exp-142 succeeded."**
- **Caption:** **Nobody wrote anything down. Nobody asked Curie to speak.**  · **VO:** *"The run happens where runs
  happen — the coding agent. The memory happens where the team lives. Curie is the bridge, and it noticed on its own."*
- **1:30–1:40 · Files-tab proof:** click **Files → the Lab Record** (list) + the **"Lab Record" canvas**. Caption:
  **The notebook keeps itself.**

### 1:40–1:58 · ESCALATION — chat → standing guardian *(Creativity — the Bubble Lab beat)*
- **Type:** `@Prior from now on preflight every plan in this channel, and every Monday post which beliefs new evidence changed.`
- **Screen:** a **standing-capability card** appears (ambient preflight ON + weekly digest scheduled).
- **Caption:** **One sentence → a standing guardian.**

### 1:58–2:28 · PAYOFF — the setup returns *(Quality of Idea, UX)*
- **The new member from 0:10 asks Curie the same question** → cited answer with a real permalink.
- **Then type:** `@Prior where does the lab stand?` → **the hypothesis map** renders: 🔴 Scaling the ESM head —
  Refuted · 🟢 Curriculum ordering — Supported · 🟡 Synthetic pretraining — Open, with the **native evidence bar
  chart**. Hold. Then flash **App Home** — the same Belief Ledger, "Curie — your lab's memory."
- **Caption:** **Every claim, one click from its evidence.**  · **VO:** *"This map has never existed before —
  compiled from the conversation the lab was already having."*

### 2:28–2:45 · ZOOM OUT + CLOSE *(Impact)*
- **VO (3 sentences):** *"70 to 90 percent of experiments fail — even at Microsoft and Netflix — and that learning
  is stored nowhere. Today's tools ask scientists to upload, classify, and route their own data. Curie's inbox is
  empty by construction: the record writes itself, from where the lab already talks."*
- **Screen:** 3-sec architecture diagram (highlight RTS + Lists + streaming + cross-tool poller).
- **End card = the judge's next action:** `Try it → paste in #experiments: "@Prior planning to fine-tune ESM2, lr 1e-4, batch 32, v1"`
- **Tagline:** *Curie — the memory of what your lab believes, and why.*

---

## LIVE-RUN RUNBOOK (what I drive in Chrome, in order — "go fully according to it")

1. **Slack tab** → #experiments. Post the ESM plan as @Prior mention → screenshot the **collision card** (verify fix (b)).
2. **Claude Science tab** → prompt it to post the `📊 Run exp-142 succeeded …` record → confirm "posted to #experiments."
3. **Slack tab** → wait ~8s → screenshot the **belief-change alert** (the autonomy star) + the flipped row.
4. **Files tab** → open the **Lab Record list** + the **"Lab Record" canvas** → screenshot (the self-writing proof).
5. **Slack tab** → post `@Prior from now on preflight every plan … Monday digest` → screenshot the **standing card**.
6. **Slack tab** → post `@Prior where does the lab stand?` → screenshot the **map + chart**.
7. **Agent/Home** → open Curie's **App Home** → screenshot the **Belief Ledger** crown.
8. *(If built)* **Tools tab** → run the **Log-a-run workflow** form → show it posting a run-record → poller ingests.

Each step I verify visually before moving on; if a beat misfires we retry that beat only (the sandbox path is
independent). This is the exact order the video follows.

---

## FALLBACKS
- Autonomy star: if the poller is slow on a take, the `📊 Run` post + the alert are both real — just wait the
  poll interval; never fake it. Worst case, a pre-recorded real take of this beat (genuine footage).
- The judge's sandbox never depends on the cross-tool run — the Slack-only path (paste plan → verdict → map →
  App Home) stands alone and is what a judge reproduces.

---

## Cursor prompt — redeploy the two staged code changes
```
Two files changed: listeners/ambient.py (poller now also ambient-preflights plan messages when that mode is on)
and listeners/app_home.py (App Home now shows the Belief Ledger under the stats).
1. rsync listeners/ambient.py + listeners/app_home.py to the EC2 curie app dir.
2. sudo systemctl restart curie
3. Confirm "Curie is listening (Socket Mode)." + "CURIE-DIAG run-poller started …".
```
