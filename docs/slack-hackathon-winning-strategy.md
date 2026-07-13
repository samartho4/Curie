# Curie — Slack Agent Builder Challenge strategy (v7, final canon)

**Deadline: Mon July 13, 5:00pm PDT · Track: NEW SLACK AGENT · Judging: July 14–Aug 6 · Winners: Aug 11**
**Prizes: 1st $8,000 + Dreamforce + cert · 2nd $4,000 · cross-track: Best UX / Most Innovative / Best Tech Implementation ($2k each; one prize max per project)**

v7 = the merge: this doc's product/track/competitor canon + the parallel iterations in this folder (cairn-strategy: agent_view platform fix, passive-growth answer; groundhog-plan: mute-proofing, MoSCoW discipline; product-spec: anti-lock-in story; §9–11: 83Sciences/Bubble Lab recon, live demo, name). **NAME DECIDED: Curie.** Build layer: `prior-product-spec.md`, `backend.md`, `frontend.md` — **Rosalind→Curie find-replace applied July 10 (env prefixes `CURIE_*`, shortcut "Log to Curie", manifest names; spec file renamed).** `cairn-`/`groundhog-` docs are superseded but keep their §-references noted here.

---

## 1. The product

**Curie — the lab notebook that writes itself, and the living map of what your lab believes.**

Three layers, one spine:

1. **The record (spine).** Experiments become first-class objects in a native **Slack List**: owner, status (planned/running/failed/succeeded), params, source **message column** (provenance built in), **canvas column** (each experiment's self-writing notebook page), verified/auto trust state (Guru pattern). Compiled by the agent from #experiments chatter + 🧪 reacji + message shortcuts. Act-then-undo, not confirm-everything.
2. **The hypothesis ledger (crown).** Hypotheses as parent rows; experiments as evidence beneath (`parent_item_id` — native Lists hierarchy). Evidence links carry **Scite's taxonomy: supports / contrasts / mentions** — for internal results AND external papers (scholar-mcp). Roll-up on screen: *H1 Supported (3) · H2 Refuted (2) · H3 Open (1 running).* Explicit registration only (`@Curie track hypothesis: …`); links proposed by the agent, human-confirmed.
3. **Preflight (flagship query).** `@Curie <plan>` → streamed check → verdict card: collision/near-miss/clear, settings diff, literature nulls — and the kill line: *"this addresses H2 — the lab already knows the answer."*

**Positioning sentences (use verbatim in the description):**
- *"Claude Tag answers questions; Curie maintains a typed system of record with verdict instruments."*
- *"Scite classifies evidence polarity across 1.6B published citations. Curie is Scite for what your lab knows but never published."*
- *"Researchers already build discourse graphs by hand in Roam (Chan; Protocol Labs). Curie is the first one that writes itself — from where the lab already talks."*
- Generality is structure, not a second demo vertical: *"Hypotheses → experiments → evidence is how every strategic team works. Labs are the beachhead."*

**Name (DECIDED — §11 has the full rationale):** **Curie.** Three true lab meanings in one word: *prior work* ("did you check Curie?" — the preflight action), *Bayesian prior* (a belief updated as evidence arrives — literally the hypothesis ledger; the name IS the product thesis), *preregistration* ("register your prior"). Verb-able, @handle-clean, not a person, not a generic AI name. Tagline: *"Curie — the memory of what your lab believes, and why."*

**Two positioning lines rescued from the product spec (use them):**
- Anti-lock-in: *"The record is a native Slack List and canvases — it belongs to the lab and survives even if Curie is uninstalled. That's the story no ELN incumbent can tell."*
- The Benchling kill-shot: *"Benchling costs a quarter-million over two years and scientists still don't fill it in. Curie is free, and it fills itself in."*

**The behavior-change objection, answered (from the cairn iteration — a judge WILL ask "what if nobody posts plans?"):** the corpus grows passively — 🧪 reacji on any result, message shortcut, run-record ingestion from real tools, literature unfurls — so the record grows without ritual; the `@Curie` check is the optional high-value moment, not a mandatory habit.

## 2. Architecture (canon)

```
Slack sandbox workspace (seeded: 6 months of lab history via 2–3 real dummy member accounts)
 ├─ #experiments — trigger surface · pinned "Test Curie in 60s" canvas
 ├─ Bolt for Python app (`slack create agent` scaffold, Claude SDK variant)
 │   ├─ TRIGGERS: @mention (app_mention → action_token ✅) · DM (message.im → token ✅)
 │   │            · ambient channel listener (user-token search path) · 🧪 reacji · msg shortcut
 │   ├─ VERDICT ENGINE (PromptQL pattern): LLM writes check-plan → deterministic execution:
 │   │     1. Lists query (PRIMARY — structured record, no token drama)
 │   │     2. RTS assistant.search.context sweep (≤3 calls; OR-queries + term_clauses;
 │   │        keyword-mode design, semantic if sandbox has AI Search; include_bots handled)
 │   │     3. conversations.replies context pull on hits
 │   │     4. scholar-mcp (OpenAlex + bioRxiv ✅ verified; retraction flag)
 │   │     5. RCS (PaperQA2 pattern): per-candidate contextual summary → verdict LLM
 │   ├─ OUTPUT: plan-mode streaming (task_update chunks w/ sources) → stopStream verdict card
 │   │     (header · diff fields · [View thread] [Full comparison] [Proceed anyway → rationale])
 │   ├─ RECORD: slackLists.create / items.* (bot token, lists:write) + canvas per experiment
 │   ├─ LEDGER: parent rows (hypotheses) ← evidence links (supports/contrasts/mentions)
 │   └─ COMPLIANCE: zero storage of retrieved Slack data (RTS terms) — everything per-request;
 │         permissions inherited from Slack at query time (Glean's nine-figure problem, free)
 └─ Judge path: paste the end-card plan → verdict in ~10s → click H2 → the map. 60 seconds.
```

**Mechanics locked by research:** action_token is required for bot-token RTS and only arrives via app_mention/DM — ambient mode runs on a stored user token (documented, sandbox-legal). Semantic search is plan-gated (email Slack partnerships day one; design for keyword mode: stemming yes, synonyms no → alias-expanded OR-queries). Lists/canvas/streaming are paid-plan features → the dev sandbox is fully featured. Honest latency is 8–15s → the plan-stream is the answer, not a spinner. RTS 429s get a graceful retry message.

**⚠️ PLATFORM MANDATE (June 30, 2026 changelog — from the cairn/groundhog iterations; build on the wrong surface and you lose a day):** new apps can ONLY use the **Agent messaging experience (`agent_view`)** — the legacy Assistant path (`assistant_thread_started`, threadStarted callbacks, Chat/History tabs) is closed to new apps. Consequences: use `app_home_opened` (check `tab="messages"`) to detect DM open; suggested prompts render atop the Messages tab. **Pin: Slack CLI ≥ 4.4.0 · Bolt-Python ≥ 1.29.0 · slack-sdk ≥ 3.43.0.**

## 3. Verified facts base (safe to say out loud; sources in research history)

- **Platform:** `slackLists.create` supports full programmatic schema incl. message + canvas columns on a bot token; `parent_item_id` gives native hierarchy; RTS searches canvases too; plan/task-card streaming blocks are purpose-built; Slackbot MCP Client exists but is still rolling out (bonus only — check the App Settings flag).
- **Impact:** 70–90% of experiments fail or come back flat at Microsoft/Bing/Google/Netflix/Airbnb (Kohavi; HBR 2017) — the most valuable knowledge a team produces, and the least recorded. Knowledge workers waste **5.3 hrs/week** waiting for or *recreating* existing knowledge (Panopto/YouGov); **42%** of institutional knowledge lives in one head; the F500 lose **$31.5B/yr** (IDC). Bottom-up: one repeated failed experiment ≈ **$6–15k** of researcher time. Energy garnish only: ~450 kWh per duplicated week-long 8×A100 fine-tune (A100 ≈ 0.34 kW measured, LLM360 K2).
- **Curie art = pipes:** RSpace/LabCollector (ELN→Slack notifications), W&B `wandb.alert`, Statsig/Optimizely (significance alerts). Nothing compiles the record FROM the conversation — in science or industry. ELN adoption is blocked by workflow friction (74% cite double data entry) while >70% of non-users want one.
- **Competitor steals:** PromptQL plan-then-execute · Glean graph-first hybrid retrieval + query-time ACLs · Elicit published eval accuracy + per-field citations · Scite polarity taxonomy · PaperQA2 RCS + retraction checks · Dust event→pipeline architecture shape · Guru verifier/trust-interval states · discourse-graph vocabulary (question/claim/evidence, support/opposition edges).

## 4. THE DEMO (the deliverable that decides everything)

Judges spend 5–7 minutes per project, watch dozens back-to-back, and aren't required to pass 3:00. The video carries all four criteria; the sandbox verifies it; the description confirms it. Design principle: **a judge remembers exactly one thing per video — so build one continuous causal story whose payoff recontextualizes everything they just saw. Not a feature tour.**

### Dramaturgy v7 — one experiment's life, LIVE across the two surfaces where science actually happens

Screen = split for the middle act: **Slack left (where work is discussed), terminal/Claude Science right (where work is done).** Curie is the memory layer bridging them — showing both, live, is the one thing no scripted competitor can fake. Target **2:45** (judges bail at 3:00; leave slack). **Mute-proof everything:** judges skim with sound off — every VO claim also appears as a terse on-screen caption.

**COLD OPEN — no logo, no title, no "meet Curie."**

- **0:00–0:15 · The problem, enacted.** Time-lapse scroll of #experiments — months in three seconds. New member DMs a teammate: *"why did we abandon the transformer baseline?"* → *"🤷 ask Anika — she left last year."* Caption: **Labs forget. People leave.** (Plants the payoff question.)
- **0:15–0:45 · THE CHECK — uncut, visible timer.** Priya: *"@Curie planning to fine-tune the ESM baseline, lr 1e-4, batch 32, v2 split."* Live plan streams — `Search lab record ✓ 3 hits · RTS sweep ✓ · Literature ✓ 1 null result` — tiny captions naming each API as it fires. Verdict card: ⚠️ **"Addresses H2 — already refuted twice."** Settings diff. bioRxiv null. Beat. Caption: **8 seconds, uncut.** Title card — *Curie* — NOW, as punctuation.
- **0:45–1:35 · THE LIVE RUN (the beat that makes it real).** She clicks **Proceed anyway** + one-line rationale. The right pane wakes: a **real run launches in Claude Science / Claude Code** — and on camera it *inherits the Slack context* (the agent reads the plan + Curie's warning via the Slack MCP server; show the tool-call line). Real logs scroll. The loss goes NaN — a **genuinely real, honestly engineered failure** (tiny proxy model, deliberately hot LR → dies in ~15s; real code, real crash, zero fakery). The run's hook posts a structured **run record back to #experiments** → the experiment's notebook canvas writes itself → List row flips **Failed** → **H2 evidence ticks 2 → 3.** Caption: **Nobody wrote anything down.** VO: *"The run happens where runs happen — my coding agent. The memory happens where the team lives."*
- **1:35–1:50 · ESCALATION (Bubble Lab's genre-winning beat, science-flavored).** Priya: *"@Curie — from now on, preflight every plan in this channel, and every Monday post which of our beliefs new evidence has contradicted."* → a standing capability card appears. Caption: **Chat → standing guardian.**
- **1:50–2:20 · THE PAYOFF — the setup returns.** The new member from 0:10 asks *Curie* the same question → cited answer, real permalinks. Then: *"Where does the lab stand?"* → **the hypothesis map.** Hold. Caption: **Every claim, one click from its evidence.** VO: *"This screen has never existed before."*
- **2:20–2:38 · Zoom out — three sentences.** *"70 to 90 percent of experiments fail, even at Microsoft and Netflix — and that learning is stored nowhere. The state of the art asks scientists to upload, classify, and route their own data — its flagship screen is an inbox literally called 'Unclassified Data.' Curie's version of that inbox is empty by construction: the record writes itself."* Architecture diagram 3s, three required techs highlighted. *(Name 83Sciences in the description, not on camera.)*
- **2:38–2:50 · Close + the bridge.** Tagline: *"Curie — the memory of what your lab believes, and why."* **End card = the judge's next action:** `Try it → paste in #experiments: "@Curie planning to fine-tune ESM, lr 1e-4, batch 32, v2 split"`.

**Script budget: ~300 words at ~130 wpm.** Table-read, cut 15%. Record UI passes and VO separately.

**Live-run production engineering:** the failure must be real AND fast — a real training script on a tiny proxy model with a deliberately hot learning rate → NaN inside ~15s. Rehearse the full cross-tool take end-to-end twice before recording. **Fallback rule (Sunday-noon gate):** if the run-record hook isn't rock-solid, use a *pre-recorded real run* (still genuine footage, captured earlier — never a mock); if even that's shaky, the 🧪-tap version ships. The judge's sandbox never depends on any of this — the Slack-only path stands alone.

### Production checklist

- One-take feel: cut only on natural channel-switch clicks. 1080p+, light theme, zoom-ins on every card (Block Kit detail is invisible at full-screen), cursor halo on clicks.
- Honest speed: visible timer during the streamed check; zero sped-up segments — judges are jaded by fake-fast AI demos; real latency handled beautifully reads as engineering.
- Cast the workspace: dummy members with human names and avatar photos; clean sidebar; months of plausible history (judges WILL scroll it).
- Audio: single confident voice, −16 LUFS; no music bed (or ≤−20dB, never copyrighted — rules).
- **NOT in the video:** App Home tour, onboarding, settings, feedback buttons, error states, any second vertical. Every secondary second steals from the moments. (Error handling and empty states belong in the description text.) *(Note: the Claude Science / coding-agent live run IS now in the video — §4 v7 — because it's the authenticity spine; what stays out is bridge configuration/setup.)*
- Upload ≥24h before deadline; verify public in an incognito window.

### The second demo — the judge's sandbox hour

- Pinned canvas in #experiments: **"Test Curie in 60 seconds"** — three paste-ready plans (landmine → ⚠️, near-miss → 🟡, clean → ✅), identical to the video's end card.
- Split-pane suggested prompts mirror the same three, plus *"Where does the lab stand?"*
- The Experiments List and hypothesis map are pre-populated so pure browsing impresses before a judge types anything.
- First-run grace: a judge who opens a fresh channel or DM gets one crisp onboarding path ("New experiments channel? I'll set up your List.").
- The full judge path gets tested July 12 **from a fresh non-admin member account.**

## 5. Calendar (Wed eve → Mon 5pm PDT; bars are pass/fail)

- **Wed Jul 8 (tonight):** Devpost registration + draft submission saved · Slack Developer Program + payment method + sandbox (event code `SABC-7X2K-M9PL-4QFN` for personal email) · `slack create agent` scaffold runs · email Slack partnerships re: AI Search on the sandbox · join #slack-agent-builder-challenge.
- **Thu Jul 9:** **Smoke tests first (30 min):** ① app_mention carries action_token (incl. thread replies) ② RTS returns seeded messages ③ bot-authored vs user-authored searchability ④ `assistant.search.info` — semantic on? ⑤ user-token ambient search ⑥ Slackbot-MCP flag present? ⑦ Lists end-to-end (create → row → canvas column). **Noon gate:** if RTS is unreliable on config strings → List-primary + `conversations.history` fallback (pre-approved; RTS checkbox rides on Q&A + cross-ref paths). Then: seed script (2–3 dummy accounts, 6 months, 5–6 landmines) · plain-text verdict pipeline · draft the Devpost description in your own voice · Mermaid diagram stub. **Bar: colliding plan → correct cited warning; clean plan → confident ✅.**
- **Fri Jul 10:** scholar-mcp (search / null-results / retraction flag) · verdict engine refactor to check-plan → deterministic execution · RCS per-candidate summaries · **PM: eval harness — 40 plans × expected verdicts (landmines, near-misses, clean, off-domain, adversarial), target zero false collisions, numbers into README** · RTS rate-limit grace path. **Bar: eval green.**
- **Sat Jul 11:** Plan-mode streaming → final verdict card (prototype in Block Kit Builder first; confirm-modal microcopy: *"Preview of what I'll write — approve to save"*, the Dalton trust pattern) · 🧪/shortcut → record → canvas page · List + trust states · App Home **"Pending confirmations" block** (inline Review-queue, +1h) · **hypothesis ledger IF the spine landed Friday** (else it ships seed-only and the pitch still works) · **PM: the live-run loop for the video** — run-record hook (coding-agent/Claude Science → #experiments; webhook is fine) + context-inheritance path (Slack MCP read or paste-fallback) + the fast-failing proxy training script, rehearsed twice · split-pane suggested prompts · *stretch:* the Monday belief-digest scheduled task (the escalation beat — Bolt scheduler + one LLM pass over the ledger; only if everything above is green). **Bar: every demo beat works live, on demand.**
- **Sun Jul 12:** Feature freeze at noon. Final seed pass · invite slackhack@salesforce.com + testing@devpost.com as **Members**, verify in member list · record + edit video, upload, incognito check · diagram into the **file-upload field** (not the carousel) · description final · **SUBMIT** (organizers review early submissions for eligibility).
- **Mon Jul 13:** Buffer only. Fix whatever Devpost flags. Deadline 5:00pm PDT — no late submissions.

**Stretch stack (strict order, cut from the bottom):** evidence aging / re-verify nudges → Slackbot MCP tools (`preflight_check`, `search_negative_results`) if the flag exists → Claude Science run-record feed → arXiv/bioRxiv unfurls.

## 6. Submission checklist

- [ ] Track: New Slack Agent · first description paragraph answers what/who/why in your own voice (organizers: AI boilerplate is "obvious and forgettable")
- [ ] "Why not Claude Tag?" answered in one sentence · simulated-lab data labeled honestly
- [ ] ~3-min public video (incognito-verified, no copyrighted music, uploaded ≥24h early)
- [ ] Architecture diagram via the file-upload field — not the image carousel
- [ ] Sandbox URL on the form · both judge emails as **Members**, visible in the member list
- [ ] Agent installed + works cold · pinned 60-second test canvas · fresh-account judge-path test done
- [ ] Eval numbers in README and spoken in the video
- [ ] One prize max per project; multiple submissions allowed only if substantially different — don't, you're solo

## 7. Fine print

- IP stays yours; Salesforce gets an evaluation/promotion license. AI-assisted coding is explicitly allowed. India is eligible; government-entity employees are not. RTS terms forbid storing retrieved data — the per-request architecture already complies. An AI-content disclaimer in the verdict card's context block matches Slack's marketplace guidance.
- Anthropic AI for Science credits (≤$30k) close **July 15** — same project narrative, second application, 10 minutes.

## 8. Lessons ledger (what five critique rounds established — do not relitigate)

1. Judges test alone in your sandbox for weeks → everything must work cold, in one action.
2. The tech must be load-bearing ("meaningfully worse without it"), never checkbox-bolted.
3. Reactive Q&A demos read as RAG wrappers; proactive structured verdicts and self-writing records do not.
4. One thing done completely beats four features — the growth-channel hedge died for this.
5. A notebook records the past; the hypothesis ledger changes what happens next. That's the sky.
6. The verdict engine's failure mode — a false collision on a judge's arbitrary plan — is the existential risk: eval harness non-negotiable, "no collision" the confident default.
7. Scope is the enemy: daily pass/fail bars, noon gates, stretch cut from the bottom, submit a day early.
8. Impact claims must survive a skeptic: Kohavi / Panopto / IDC and bottom-up dollars; $28B and CO₂ are garnish only.
9. The demo is one causal story with a setup/payoff loop, honest latency made beautiful, and an end card that tells the judge exactly what to type next.

---

## 9. Competitor teardown — 83Sciences (live recon) + Bubble Lab (demo genre)

### 83Sciences (platform.83sciences.ai) — clicked through every screen, July 9

**What it is:** a complete, well-built science research *platform*. Left-nav: Home, Notebook, Files, **To File**, Science Explorer, Table Templates, **Provenance**, **Review**, **AI**, Settings, Research Tools. Findings per screen:
- **Science Explorer** — "Scientific Objects": Samples / Experiments / Experimental Sets, columns Name·Row ID·Experimental Set·Primary Experiment·Composition·Measurement. A rigorous structured object model; **experiments are first-class objects** (validates our core).
- **Provenance** — "Object Relationship Graph": Sample lineage · Measurement evidence · File provenance · Notebook context · Full graph, with 1/2/3-hop neighborhoods. **This is the evidence/discourse graph, already built** — for physical lab objects.
- **Review** — "Human Review Queue": an Agent Queue of *draft agent proposals* + *notepage extraction awaiting review*. **The self-writing-notebook + human-confirm pattern, already shipped.**
- **AI** — an assistant named **"Dalton"** (John Dalton — a scientist surname; the exact naming convention our earlier "Rosalind" used, which is one more reason we moved off it). "Any changes are previewed for your approval before they are saved."

**Why this is the most important thing we've found — it sharpens the moat instead of threatening it:**
1. **It's a destination, not the flow.** A standalone web app you must go to. **"To File" is a top-level nav item** — the data-entry burden is so central it's primary navigation. That IS the ELN-adoption killer (74% cite double data entry). Our entire thesis in one contrast: *83Sciences has a "To File" button. Curie has no filing — the record writes itself from the conversation you're already having.*
2. **It's empty until you populate it.** Every counter read 0 samples / 0 experiments / 0 measurements. Cold-start incarnate. We compile from six months of existing Slack history — value on day one.
3. **It's wet-lab shaped** (samples, compositions, measurements) and requires migration + training. We're a Slack app that installs in a minute and meets computational/experiment-driven teams where they already talk.
4. **It validates everything structural** — experiments-as-objects, provenance graph, review-queue agent, scientist-named assistant — which de-risks our concept and lets us cite a real, funded platform as proof the category is real. We are the *flow-native, zero-filing, auto-populated* answer to the same problem.

**One-liner for the pitch:** *"Platforms like 83Sciences prove labs want a structured, provenance-aware record. They also prove why labs don't keep one: you have to leave your work and file it. Curie removes the filing."*

**Public-site recon (83sciences.ai, July 10) — completes the picture:** their motion is **services-heavy by design**: *"We come in person to help your lab set up"* capture tools, a queryable "lab brain," and agents that understand failed experiments **"and propose optimized process conditions"** (that last part = our roadmap slide, stated by a funded competitor). Pipeline on the homepage: capture → structure → shorten → insights → discovery; logos: Stanford, Harvard, Columbia, MIT. Second one-liner this earns: *"83 Sciences digs up what got buried — in person. Curie means it never gets buried: captured at the moment of creation, in the tool the lab already talks in."* Capture-at-source vs. excavation-after-the-fact.

**Visual recon addendum (inside platform.83sciences.ai, July 10 — screenshots taken, fresh "Antimatters" workspace):** it's a genuinely well-built platform, which makes the structural findings more valuable, not less:
1. **The zero-state is everywhere and it's the whole story.** Notebook: *"Create the first notebook entry"* — a manual form (title · project · Standard/High-throughput toggle · entry-type dropdown "Procedure" · Create). Dashboard counters all 0. Provenance: "0 nodes · 0 edges." Sidebar permanently reads "0 projects, 0 samples, 0 measurements." The architecture is beautiful and **dead until humans feed it**. → Build consequence for Curie: the pre-populated sandbox isn't demo garnish, it's the categorical difference on display; and the first-run path must never show a Curie zero-state to a judge.
2. **"To File" resolves to a page titled "Unclassified Data"** — an inbox with Upload, type filters, status chips (Active/To File/Project Only/Measurement) and a **ROUTING column**. The flagship workflow of the state of the art is manually uploading, classifying, and routing your own data. → Demo zoom-out line upgraded (see §4): *"…its flagship screen is an inbox called 'Unclassified Data.' Curie's version of that inbox is empty by construction."*
3. **Every nav click = "Loading your workspace… signing you into your lab"** (multi-second full reload, every time). The destination-app tax, felt. → Description line: *"No new tab. No new login. No filing."*
4. **Dalton is a bare chat page** (Sessions list + "Message the assistant…"), plus a floating sparkle button — *AI as a place you go*. Its one good move we steal: **"Any changes are previewed for your approval before they are saved"** — adopt that exact trust-microcopy pattern in Curie's confirm modals. Curie's counter-position: no chat page at all — the agent lives at the decision points (plan posted, result logged, paper shared).
5. **Review = "Human Review Queue"** with two lanes (Agent Queue: draft agent proposals · Notepage Review: extraction awaiting review). Validated pattern, wrong location — ours is inline confirm buttons + a small **"Pending confirmations" block in App Home** (+1h, Design points, added to Sat list).
6. **Provenance graph UI vocabulary worth stealing for the roadmap/description:** view modes (Sample lineage / Measurement evidence / File provenance / Notebook context / Full graph), focus object, **neighborhood hops 1/2/3**. "Evidence neighborhoods" is good language for how the hypothesis map's [view evidence] deepens.
7. **Dashboard "Research Tools": Email Upload · Notepage Ingestion · ActionGraph Builder · Route Selection** — they're building many capture ramps because capture is their bottleneck, and every ramp is still manual-ish. Curie's ramps (🧪 reacji, shortcut, run-reporter, ambient) are the in-flow equivalents of the same list.

### Bubble Lab / "Pearl" (YC W26, 4,000+ operators) — the winning Slack-agent demo genre

From the launch + demo transcript. Pearl is a horizontal ops "super-employee" in Slack. Its demo is a masterclass in this exact hackathon category:
1. **Capabilities shown as extensible** — 3 built-in (web research, flow assistant, chart maker), then *click to add* Postgres, Gmail, Jira, Stripe, PostHog live. Breadth made visible.
2. **Real tools, real data** — "most common errors?" → live Postgres query; "open invoices?" → live Stripe sandbox → table in Slack. Not mocked answers.
3. **Learning shown live** — "I don't count quota limits as an error, remember that" → memory updates on screen → smarter next time.
4. **THE killer beat: conversation → durable autonomous workflow.** "Pull invoices daily at 8am, post to channel, draft chase emails" → Pearl builds a deterministic scheduled workflow *from the Slack chat*, shows it in the dashboard, mock-executes it, and real Slack messages + real Gmail drafts appear. **Chat becomes running infrastructure.**

**What we steal, and where we're different:**
- **Steal the escalation-to-autonomy beat** — it's the strongest move in the genre and we were missing it. A one-off `@Curie <plan>` check becomes a *standing capability*: "from now on, preflight every plan in #experiments, keep the hypothesis map live, and each Monday post which of our beliefs new evidence has contradicted or made stale." Conversation → standing autonomous guardian, shown in App Home / a dashboard. (Bolt scheduled triggers + our record; the Monday belief-digest is a genuinely novel autonomous behavior.)
- **Steal the "real tools, real data" authenticity bar** — which is exactly your live-coding-agent idea (see §10).
- **Where we win vs Pearl:** Pearl is breadth with *no opinion about the structure of the work* — it does tasks. Curie is depth with a strong opinion: the hypothesis→experiment→evidence graph. Pearl automates your ops; Curie is the reasoning-and-memory layer for how a lab *thinks*. For a science submission judged on Quality of Idea, the opinionated structure is the moat Pearl doesn't have.
- **Pivot note (bubblelab.ai live, July 10) — the ending of the Pearl story proves our thesis:** the launch-era "Pearl, ops super-employee" framing is gone; the site now sells *"the infrastructure platform for private professional communities"* — applications, matchmaking, **member intelligence**, analytics — i.e., a **vertical system-of-record compiled on top of Slack conversations** ("we enrich the Slack experience… surface insights on top of the conversations already happening"). Within months, the horizontal agent verticalized onto structured records. That is lessons-ledger #4 happening in production at a funded YC company. The escalation-to-autonomy demo beat survives the pivot (it's a technique, and we keep it); the strategic read is: we're starting where they ended up.

### The synthesized "sky" product (what both competitors push us toward)

**Curie — the autonomous memory & reasoning layer for a research team.** It watches the lab's conversation *and its actual runs*, maintains a living map of every hypothesis and its evidence (internal + literature), checks every new experiment against everything the lab already knows, and **proactively tells the lab when its beliefs change.** Flow-native (beats 83Sciences's filing burden), opinionated-structure (beats Bubble Lab's structureless ops), auto-populated (beats cold start), and escalates from one-off check to standing guardian (Bubble Lab's winning move, science-flavored).

## 10. Demo v6 draft — MERGED into §4 (v7 dramaturgy). Kept below for the reasoning record only.

The problem with "one cut, days later, the run fails" is that it looks staged, and jaded judges discount staged. The fix you proposed — run it live with a real coding agent — is right, and it becomes a structural advantage: **Curie is the memory layer bridging where work is *discussed* (Slack) and where work is *done* (the terminal / Claude Code / Claude Science / W&B).** Showing both surfaces, live, is something no scripted competitor can fake.

**The continuous, un-cut loop (screen = split: Slack left, terminal/Claude Science right):**
1. **Discuss.** In #experiments a researcher types the real plan. `@Curie` preflights it live → streamed check → ⚠️ "addresses H2, refuted twice." (Slack surface.)
2. **Decide.** Proceed anyway + one-line rationale. (Bounded autonomy, real click.)
3. **Do — for real.** Cut to the right pane: an *actual* run launches in Claude Science / Claude Code / a training script — real logs, real progress. No jump cut; the work genuinely happens.
4. **Capture — for real.** The run finishes/fails and a hook posts the result back to Slack (a `wandb.alert`-style callback, or the coding agent itself posts). `@Curie` ingests it → the experiment's notebook canvas writes itself → List row flips to *Failed* → **H2's evidence ticks 2 → 3.** The chain is real, end to end, across two real tools.
5. **Escalate (Bubble Lab beat).** "@Curie, from now on watch this channel and post a weekly belief-change digest." → a standing autonomous capability appears in App Home. Chat → running infrastructure.
6. **Payoff (unchanged, still the emotional peak).** New teammate asks "where does the lab stand?" → the living hypothesis map.

**Why this wins all four criteria at once:** Tech Implementation (real cross-tool integration, RTS+MCP+Lists+streaming+scheduled autonomy, visibly load-bearing) · Design (the split-surface story, honest latency) · Impact (every team that runs experiments) · Quality of Idea (a self-writing discourse graph fed by ground-truth runs — exists nowhere). It also makes the Claude Science bridge *the demo's spine* rather than a cut stretch item — which fits your setup perfectly since you run Claude Science locally.

**Scope guard (unchanged discipline):** the sandbox must still work cold for a judge with zero external tools — so the Slack-only path (paste plan → verdict → map) remains the fallback and the pinned-canvas test. The live cross-tool loop is the *video's* spine; the sandbox proves the Slack half unaided. Build the Slack half first (Thu–Fri); wire the live run-capture hook Saturday; if it slips, the video uses a pre-recorded real run (still real footage, just captured earlier), never a fake.

## 11. Name — DECIDED: **Curie** (was "Rosalind")

83Sciences names its agent "Dalton"; scientist-surname is a real convention, but "Rosalind" carried a heavy real-person association (and rosalind.info is a famous bioinformatics platform — a direct collision in our own field) and didn't say what the product does. The decision:

**Curie** — because in a research lab it means three true things at once:
- **Curie work / prior art** — "did you check prior?" is literally the preflight action.
- **Bayesian prior** — a belief you update as evidence arrives. That is *exactly* the hypothesis ledger: each hypothesis is a prior, each experiment updates its credence. **The name is the product thesis.**
- **Preregistration** — "register your prior" ties to open-science hypothesis registration.

Short, works as a verb and an @handle (`@Curie, has anyone tried this?`), research-resonant, not a person, not a generic AI name. Tagline: *"Curie — the memory of what your lab believes, and why."*

**Alternates if you want options:**
- **Trellis** — the invisible structure a growing thing climbs; brandable, ownable, evocative of a knowledge graph, but less literal.
- **Curie** — scientist surname (matches Dalton's genre); Marie Curie's lab notebooks are so meticulously preserved they're still kept in lead-lined boxes — "the best-kept lab notebooks in history." Good story, but the same real-person weight that sank Rosalind.
- **Ledger** — literal (the hypothesis ledger), plain.

Lead recommendation: **Curie.** Lock it before Thursday so the sandbox, List names, and description are consistent from the first commit. *(Locked July 10; build docs renamed.)*

**One collision caution (July 10):** "Curie Labs" is an existing AI-for-science startup (tabular foundation models / TabPFN). The app name **Curie** is fine for the hackathon and as a Slack app; just don't brand the org "Curie Labs" if this goes commercial, and say "Curie for Slack" where disambiguation matters.
