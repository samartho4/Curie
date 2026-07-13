# Curie — The Lab Notebook That Writes Itself
### Full product, engineering & design specification (deep dive)

*Companion to `slack-hackathon-winning-strategy.md`. That doc has the hackathon logistics and the idea's evolution; this is the build- and product-depth pass. Aim: not "a hackathon project" but the v0 of something real.*

---

## 0. One paragraph

Scientists already narrate their work in Slack — hypotheses, runs, parameters, failures, figures, decisions. Curie is an agent that listens to that stream and silently compiles it into a structured, living lab record: every experiment becomes a typed **Slack List** row and a self-writing **canvas** page, failures are preserved for the first time, and a **pre-flight check** warns you before you run something the lab already tried. It's an electronic lab notebook that requires zero data entry because the data entry already happened — in Slack. Free, private (nothing leaves the workspace), and native to the tool labs already live in.

---

## 1. The problem, precisely

Three failures compound in every lab:

1. **The notebook nobody keeps.** Electronic Lab Notebooks (ELNs) are mandated and universally resented. Benchling — the category leader — runs ~$5,000–7,000/user/year; a startup's two-year total cost of ownership is estimated near **$246,000**, and academic/under-resourced labs are simply priced out (sources §11). The reason they're hated is singular and damning: **they demand you leave your workflow to do data entry.** Compliance decays to near-zero between audits.

2. **The failures that vanish.** Journals publish ~positive results. A failed run — the abandoned architecture, the toxic reagent concentration, the hyperparameter that diverged — is recorded nowhere durable. So it gets repeated: by the next grad student, by the lab next door, by the same person in eight months. This is a load-bearing cause of the reproducibility crisis.

3. **The memory that graduates.** When a person leaves, their context leaves. Onboarding a new researcher takes months not because the knowledge doesn't exist, but because it's unfindable — trapped in scrollback and departed heads.

**Common root cause:** the system of record is disconnected from the site of work. Curie's thesis: **make the site of work (Slack) the system of record**, and let an agent do the transcription humans won't.

---

## 2. Why Slack, why now (the "this could only exist here" test)

This isn't a chatbot that happens to live in Slack. It is only possible because of four things Slack shipped, three of them recently:

- **Lists API** (`slackLists.*`) — a real typed-record store *inside* Slack, with columns of type select, user, date, number, link, message, reference, rating, checkbox. Experiments become queryable rows, not prose. Most hackathon entrants don't know this exists.
- **Work Objects** (shipped Oct 2025) — external/domain entities get first-class unfurls + a **flexpane** detail surface + a **Related Conversations** tab that auto-aggregates every place the entity was mentioned. An "Experiment" becomes a clickable object with a rich detail pane.
- **Real-Time Search API** — reason over private, unpublished lab history at query time, with **zero external storage** (a hard requirement for unpublished science).
- **Canvas API** — living documents the agent authors and RTS can later search.

No standalone ELN can touch the conversation stream where science is actually narrated. No general assistant (Claude Tag) maintains a typed system of record with lifecycle state. Curie sits in the one seat that can see both.

---

## 3. Product architecture — the four layers

```
┌─────────────────────────────────────────────────────────────────┐
│  CAPTURE  — turn conversation into structured events              │
│    • message classifier: is this an experiment signal?           │
│    • 🧪 reacji + "Log to Curie" message shortcut (explicit)   │
│    • lifecycle extractor: planned→running→succeeded/failed/       │
│      abandoned + params, outcome, artifacts                      │
│    • EVERY state change ≥ ambiguous → confirm button (HITL)      │
├─────────────────────────────────────────────────────────────────┤
│  RECORD  — the system of record (the moat)                       │
│    • Slack List "Experiments": one typed row per experiment     │
│    • per-experiment Canvas page: goal/params/timeline/figures/  │
│      outcome, auto-compiled, human-correctable                  │
│    • Experiment = Work Object: unfurl + flexpane + related convo │
│    • Negative Results Log: first-class, filterable view         │
├─────────────────────────────────────────────────────────────────┤
│  INTELLIGENCE  — make the record active, not passive            │
│    • Pre-flight check: new plan → collision vs record + RTS +   │
│      literature (scholar-mcp) → streamed verdict card           │
│    • Ask-the-lab (split pane): "what have we tried on X?" →     │
│      cited answer across record + raw history + literature      │
│    • Weekly digest canvas: what ran, what shipped, what failed  │
├─────────────────────────────────────────────────────────────────┤
│  BRIDGE (optional, never load-bearing)                          │
│    • Claude Science / HPC posts machine run-records via Slack   │
│      MCP server → auto-ingested as ground-truth experiments    │
└─────────────────────────────────────────────────────────────────┘
```

The genius move for judging: layers 1–3 are self-contained and demo live in a seeded sandbox. Layer 4 is the "and it scales to your real compute" flourish that no judge needs to run.

---

## 4. The data model (this is where engineering taste shows)

### 4.1 The "Experiments" Slack List — column schema

Built once via `slackLists.create`, then rows via `slackLists.items.create` with typed `initial_fields`. Verified column types and IDs come back from the create call; store the `column_id` map.

| Column | Type | Notes |
|---|---|---|
| Title | text (rich_text) | "Fine-tune ESM-2 on v2 split" |
| Status | select | `planned` / `running` / `succeeded` / `failed` / `abandoned` |
| Owner | user | extracted from the message author |
| Started | date | |
| Method | select | domain-tuned: `fine-tune`, `ablation`, `pretrain`, `assay`… |
| Key params | text | canonicalized: `lr=1e-4; batch=32; split=v2` |
| Outcome | text | one line; empty until resolved |
| Failure mode | select | `—` / `divergence` / `OOM` / `data-leak` / `null-result`… |
| Source thread | message | deep link to the originating Slack message |
| Canvas | link | the experiment's self-writing page |
| Confidence | rating | agent's extraction confidence (1–5); low = nudge human |

Why a List and not a database: it's **natively viewable, sortable, filterable, and @-mentionable inside Slack** by every lab member with zero new UI, and it survives if Curie is uninstalled. The record belongs to the lab, not to us. That's the anti-lock-in story ELN incumbents can't tell (§11).

### 4.2 The per-experiment canvas

`conversations.canvases.create` (or standalone `canvases.create`) with markdown. One page per experiment, edited in place via `canvases.edit` with `insert_after`/section ops as the experiment evolves. Structure:

```
# {Title}   {status emoji}
**Owner** @user · **Started** 2026-07-02 · **Status** failed
## Hypothesis / Goal
{compiled from the planning message}
## Parameters
| param | value |            ← markdown table (≤300 cells)
## Timeline
- 07-02 planned  <link to msg>
- 07-03 running   <link>
- 07-05 failed: gradient collapse @ epoch 3  <link>
## Figures
{image permalinks pulled from thread uploads}
## Outcome & Notes
{final state, human-correctable}
## Related literature
{scholar-mcp hits}
```

Canvas caveat (verified): **Block Kit is not supported inside canvases** — content is markdown only. So interactivity (buttons, confirms) lives in messages and the Work Object flexpane; the canvas is the readable artifact. Design around this, don't fight it.

### 4.3 Experiment as a Work Object

Register an `Experiment` entity. When an experiment's canvas link or a Curie deep-link is shared, `link_shared` → `chat.unfurl` with entity metadata → compact card (title, status, owner, outcome). Click → `entity_details_requested` → `entity.presentDetails` flexpane with the full record + **Related Conversations** (Slack auto-aggregates every thread that referenced this experiment — free provenance graph). Editable via the `work-object-edit` view submission. This is the feature that makes it feel like a *product*, not a bot, and almost nobody at the hackathon will use it.

> Engineering honesty: Work Objects + Lists + Canvas is a lot of surface. §8 sequences them so each is independently shippable and the demo degrades gracefully. If Work Objects slip, the List + canvas still carry the product.

---

## 5. The capture pipeline — the hard problem, designed carefully

Turning messy chat into a clean record is the actual engineering challenge. Three principles:

**5.1 Explicit beats ambient.** The reliable signal is a human tapping 🧪 on a message or using the "Log to Curie" shortcut. Ambient classification (watching #experiments and inferring) is a *supplement* with a high confidence bar, never the primary path. This is both a reliability decision and a trust decision — the docs are emphatic that agents need visible, bounded autonomy.

**5.2 Extraction as structured function-calling.** On a captured message + its thread (`conversations.replies`), one LLM call returns strict JSON: `{action: create|update, status, title, params{}, outcome, failure_mode, confidence}`. Validate before any write; on low confidence, don't guess — post an ephemeral "Log this as a new experiment? [Yes/Edit/No]".

**5.3 Every write is reversible and attributed.** State transitions post a small confirm card ("Mark *ESM-2 fine-tune* as **failed**? — pulled from @sam's message [link]"). One tap commits to the List + canvas. Undo on every action. The lab always sees Curie's identity as distinct from humans (design principle #2 in Slack's own guidance).

**Canonicalization** (research-engineer detail that makes collision-detection actually work): parameters are normalized before storage and comparison — `1e-4`, `0.0001`, `lr 1e-4` → `lr=1.0e-4`; `bs`/`batch`/`batch_size` → `batch`; dataset aliases resolved. This normalized signature is what the pre-flight check diffs. Get this right and near-miss detection ("same except batch size") becomes reliable instead of magic.

---

## 6. The intelligence layer

### 6.1 Pre-flight check (the flagship moment)
New plan detected → extract normalized signature → three parallel retrievals:
- structured match against the Experiments List (exact + near-miss on the signature),
- RTS over raw history (catches things never formally logged),
- `scholar-mcp` literature (OpenAlex + bioRxiv) for published null results.

Rendered as **plan-mode streaming** (`chat.startStream` `task_display_mode: plan`): tasks flip pending→complete with per-task sources, then `chat.stopStream` lands the verdict card (collision / near-miss / clear + settings diff + citations + `Proceed anyway → rationale`). Latency becomes theater. Verdict quality is gated by the eval harness (§9).

### 6.2 Ask-the-lab
Split-pane assistant. Suggested prompts derived from live channel context. "What have we tried on ESM?" → structured, cited answer joining the List, raw RTS history, and literature. This is the onboarding superpower and the daily-use hook that fixes Preflight's frequency problem — people ask far more than they pre-register.

### 6.3 Weekly digest
Scheduled canvas: ran / shipped / failed / awaiting-decision, with a one-line "failures worth remembering." Turns the record into a ritual and a PI dashboard — the multiplayer, compounding-value surface.

---

## 7. Design & UX (25% of score — treat as first-class)

**Identity & trust.** Curie always speaks as itself, never impersonates. Every autonomous write is visible and reversible. Confirms on ambiguity. AI-content disclaimer in a context block on generated text (marketplace guideline).

**Surface discipline.** Channel = ambient capture + verdicts. List = the queryable record. Canvas = the readable artifact. Flexpane = single-experiment deep dive. Split pane = conversational recall. App Home = control tower (recent captures, pending confirmations, digest settings, "experiments needing outcomes"). Each surface does one job.

**The signature aesthetic — "watch it write itself."** The demo-defining, screenshot-defining moment: a failed run gets a 🧪 tap and the canvas page *composes on screen* while the List row flips to `failed`. Nobody typed a notebook entry. That single interaction carries the whole pitch.

**Naming.** "Curie" (Franklin) — a human name, science's most cited story of credit and knowledge lost. Passes Slack's "name it like a human" test. The agent's verb is "log it" / "ask the lab."

**Empty & error states.** First run: App Home explains the three ways to feed Curie. No history yet: Ask-the-lab offers to import by scanning a channel. RTS rate-limited: honest "retry in a minute," never a stack trace.

---

## 8. Build sequence (maps onto the 5-day plan; each step independently demoable)

1. **Spine (must):** slack create agent scaffold → capture via 🧪 reacji + shortcut → extractor → **write one List row**. The instant a tap creates a typed row, the product exists.
2. **Canvas (must):** per-experiment page created on first capture, updated on state change. Now "watch it write itself" is real.
3. **Pre-flight query (must):** signature diff over the List + RTS + scholar-mcp, plan-mode streamed verdict. The flagship moment.
4. **Ask-the-lab (should):** split-pane cited recall. Cheap given the retrieval stack already exists.
5. **Work Object (should):** Experiment unfurl + flexpane + related conversations. The "it's a product" layer.
6. **Digest + App Home polish (nice):** scheduled canvas, control tower.
7. **Bridge (stretch):** Claude Science/HPC run-records via Slack MCP server.

Cut line for a solo build lands around step 5; steps 1–3 alone are a winning, coherent submission. Pre-register the fallback so you never scramble.

---

## 9. Reliability & evaluation (the research-engineer signature)

- **Verdict eval harness:** ~40 labeled plans (landmines / near-misses / clean / off-domain / adversarial) × expected verdicts, scripted, run before every submission-bound change. Target: **zero false collisions**; "no collision" is the confident default. Ship the number ("40-case eval, 0 false positives") in README + video.
- **Extraction eval:** ~30 messages × expected structured output; measures capture precision/recall so you can tune the confidence threshold honestly.
- **Idempotency:** dedupe on (author, thread_ts, signature) so a double-tap or re-processed event never creates twin records.
- **Rate-limit grace:** RTS special limits + Lists Tier 3; backoff + user-visible "working, one moment."
- **Zero-storage compliance:** no external copy of Slack data; the List/canvas live in Slack; we store only metadata + column-id maps.

---

## 10. The sky roadmap (what to say when a judge asks "where does this go?")

- **v1 (hackathon):** one lab, one workspace, self-writing record + pre-flight + recall.
- **v2:** cross-lab **federated negative-results network** — opt-in, privacy-preserving sharing of *failure signatures* (not data) so "someone, somewhere already found this dead end" works across institutions. The anti-reproducibility-crisis play at ecosystem scale.
- **v3:** methods-section & data-availability draft generated from the structured record at paper time — closing the loop back to publication, but now with failures included.
- **Business:** free for academic/under-resourced labs (Good-track heart, and the wedge ELN incumbents can't undercut); paid org tier for biotech (governance, audit, Marketplace). The record is portable and Slack-owned — the explicit anti-lock-in answer to the incumbents' most-hated trait.

Positioning line: *"Benchling costs a quarter-million over two years and scientists still don't fill it in. Curie is free, and it fills itself in."*

---

## 11. Sources

- Slack Lists API — [`slackLists.items.create` reference](https://docs.slack.dev/reference/methods/slackLists.items.create) (column/field types, scopes, rate limits, paid-plan note); [Lists surface overview](https://docs.slack.dev/surfaces/lists)
- Slack Canvas API — [Canvases surface & markdown/table spec](https://docs.slack.dev/surfaces/canvases) (Block Kit unsupported in canvases; 300-cell tables; image permalinks)
- Work Objects — [overview](https://docs.slack.dev/messaging/work-objects-overview) (unfurl + flexpane + related conversations; `entity.presentDetails`; `work-object-edit`)
- Real-Time Search API — [usage guide](https://docs.slack.dev/apis/web-api/real-time-search-api) (action_token, keyword vs semantic, zero-storage terms)
- Developing agents — [response loop, streaming, plan mode](https://docs.slack.dev/ai/developing-agents)
- ELN market grounding — [Scispot: Benchling pricing guide](https://www.scispot.com/blog/the-complete-guide-to-benchling-pricing-plans-costs-and-alternatives-for-biotech-research); [Sapio: 6 biggest ELN complaints](https://www.sapiosciences.com/blog/the-6-biggest-complaints-about-electronic-lab-notebooks-and-how-to-avoid-them/); [NIH: FAQ on ELN use](https://oir.nih.gov/sourcebook/intramural-program-oversight/electronic-lab-notebooks/frequently-asked-questions-about-use-elns-nih)
