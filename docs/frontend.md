# Curie — Product & Frontend Spec (frontend.md)

**Standalone document.** A designer or engineer reading only this file understands *what the product is* and can build every surface, state, and word. Companion: `backend.md` (data, pipelines, APIs). Contract between them: backend.md §11 — the backend fills slots in the five payloads defined here; it never invents layout.

> **Platform note.** Curie's "frontend" is Slack itself. There is no custom CSS, no web app, no responsive grid. The UI vocabulary is **Block Kit** (JSON layout blocks), **native Lists**, **canvases**, **plan-mode streaming**, and the **assistant split-pane**. So this spec replaces "design tokens / breakpoints" with **Slack primitives / surfaces**, but keeps the discipline: every state, every string, every edge case specified.

---

## 1. The product in one screen

A researcher types `@Curie planning to fine-tune ESM, lr 1e-4, batch 32, v2 split` in `#experiments`. A live checklist streams — *Parsing plan ✓ · Searching the record (3 hits) ✓ · Checking literature (1 null result) ✓* — then a **verdict card** lands in-thread:

> ⚠️ **Collision — this was already tried.** Anika ran this on **Mar 12**, it **failed** (gradient collapse, epoch 3). This addresses **H2**, already refuted twice. One param differs: **split v2 vs v1**.
> `[View thread]` `[Full comparison]` `[Proceed anyway]`

That is the whole product in one interaction: **the lab's memory, speaking at the moment of decision.** Everything else — the self-writing record, the hypothesis ledger, the onboarding — exists so that this moment is always right.

**Product promise (the line on the App Home and in the video):** *No experiment starts blind. Curie is the lab's memory — it writes itself.*

---

## 2. Surfaces (Slack's equivalent of "breakpoints")

| Surface | Role | Primary content |
|---|---|---|
| **Channel thread** (`#experiments`) | Where checks happen and results get logged | Plan stream → verdict card; log receipts |
| **Split-pane assistant** (top-bar entry) | 1:1 conversation, Q&A over the record | Suggested prompts, streamed answers, ledger view |
| **DM / Messages tab** | Same as split-pane for users who DM | Q&A, checks |
| **Native List** ("Lab Record") | The database, browsable by humans | Hypothesis parent rows → experiment child rows |
| **Canvas** (one per experiment) | The self-writing notebook page | Goal, params, timeline, outcome, evidence, provenance |
| **App Home** | Dashboard + controls + onboarding | Stats, recent activity, settings, "how to use" |

**Surface selection rule (why each thing lives where it does):** decisions and evidence surface *in the thread where work happens* (never drag the user away); the *browsable state* lives in the List and canvases (persistent, sortable, shareable); *conversation* lives in the split-pane; *orchestration/health* lives in App Home. This mirrors Slack's own agent guidance: act in the flow, persist in dedicated surfaces.

---

## 3. Design primitives (the "token" table, Slack-native)

| Primitive | Value | Usage |
|---|---|---|
| Verdict colors | 🔴 red `danger` / 🟡 yellow / 🟢 green | collision / near-miss / clear — carried by the List `status` select AND the card's leading emoji |
| Status emoji | ⚠️ collision · 🟡 near-miss · ✅ clear · 👀 working · 🧪 log-this · ✓ verified | consistent everywhere; never mixed |
| Evidence polarity | 🟢 Supports · 🔴 Contrasts · ⚪ Mentions | Scite taxonomy; used on every evidence link, in List + canvas |
| Card anatomy | `header` → `section`(s) → `context`(citations) → `actions`(buttons) → `context`(AI disclaimer) | the fixed skeleton of EVERY Curie card (§ below) |
| Citations | `context` block, `<permalink|label>` links, unfurls suppressed | required on every claim (backend F6) |
| Buttons | max 3 per card; primary = the safe/common action | never >3 (mobile truncates) |
| Copy voice | plain, specific, quietly confident; no exclamation; no emoji in body text | "This was already tried." not "Uh oh! Looks like a duplicate!! 🎉" |
| Tone rule | Curie states evidence, never scolds | it's an instrument, not a hall monitor |

**The canonical card skeleton** (every card follows it; only the middle sections vary):
```
header            ← one plain-text line, the verdict/subject
section(s)        ← the substance; mrkdwn; bullets for diffs
context           ← citations: <permalink|source>, spaced
actions           ← ≤3 buttons
context           ← "🤖 Curie · AI-generated · check before acting"  (required, every card)
```

---

## 4. The five payloads (rendering spec — this is the backend contract §11)

### 4A. `stream_plan` — the live check (masks 8–20 s latency; it IS the demo)
Rendered via `chat.startStream(task_display_mode="plan")` + `task_update` chunks. Tasks appear pending → in_progress → complete, each carrying its own `sources`.

| Task id | Label (in_progress → complete) | Source shown on complete |
|---|---|---|
| parse | "Reading the plan" → "Plan understood" | — |
| record | "Searching the lab record" → "Record searched · {n} related" | List row permalinks |
| history | "Reading prior threads" → "Curie work reviewed" | top thread permalink |
| literature | "Checking the literature" → "Literature checked · {n} papers" | DOIs |
| verdict | "Weighing the evidence" → "Done" | — |

- **Motion:** each task flips within ~1 s of its backend step completing; no artificial delay. If a step is skipped (off-domain → no literature), its task is omitted, not shown empty.
- **Degraded (streaming unavailable, backend smoke-test #4 fails):** replace with 👀 reaction + one placeholder message "Checking the record and literature…" then a single `chat.update` to the verdict card. Same information, no stream.
- **A11y:** task labels are full sentences (screen readers announce them); never rely on the emoji alone to convey state.

### 4B. `verdict_card` — the payload everything else serves
Three variants, one skeleton. Header + leading emoji encode the level; body always shows the *diff* and *evidence*, never a bare yes/no.

**Variant: Collision (🔴)**
```
header:   ⚠️ This was already tried
section:  *Anika ran this on Mar 12* — Failed (gradient collapse, epoch 3).
          This addresses *H2: scaling the ESM head beats full fine-tuning* — already refuted (2 against).
section:  *What differs from last time*
          • learning rate 1e-4  ·  same
          • batch 32 vs 64  ·  differs
          • split v2 vs v1  ·  differs   ← only real change
context:  <permalink|Anika's run · Mar 12>   <permalink|H2 in the record>   <doi|Related null result · bioRxiv 2026>
actions:  [View thread]  [Full comparison]  [Proceed anyway]   (primary = View thread)
context:  🤖 Curie · AI-generated · check before acting
```

**Variant: Near-miss (🟡)** — header "🟡 Close to earlier work"; body frames it as *informative, not blocking*: "Similar to Exp #14, but you changed the optimizer — that's genuinely new. Here's what happened last time so you can compare." Same citations + actions minus "Proceed anyway" (nothing to override).

**Variant: Clear (🟢)** — deliberately minimal, because this is the *common* case and must never feel like noise:
```
section:  ✅ No prior work found on this. Good to go.
context:  Searched 6 months of the record + literature · <link|see what I checked>
```
Optional one-line "1 loosely-related thread — view" only when `0.5 ≤ confidence < 0.65` (backend §13). No buttons, no disclaimer-heavy footer — a clear result should read in under a second.

- **Truncation:** diff list caps at 5 params (+"…and N more" linking the canvas). Outcome text caps ~200 chars with "…" → Full comparison modal has the rest.
- **Empty/degraded:** literature unavailable → drop that citation, add context line "Literature check unavailable — based on the lab record only." Never block the verdict on an external failure.

### 4C. `log_receipt` — result logged (act-then-undo)
Posted as a lightweight context message in-thread after a 🧪 reaction or "Log to Curie" shortcut:
```
context:  ✏️ Logged to *Exp: ESM head scaling* — status *Failed*. Notebook updated.
actions:  [Undo]  [Verify ✓]  [Link to hypothesis…]
```
- **Undo** reverts the write (backend keeps prior values 15 min); on click, receipt collapses to "Reverted."
- **Verify ✓** flips trust `auto → verified`, receipt updates to "✓ Verified by <@user>".
- **Link to hypothesis…** opens a modal (§4D-modal) to attach with a polarity.
- **Why act-then-undo, not confirm-first:** confirming every capture makes Curie a nag and defeats "zero data entry." Low-stakes writes happen silently-but-visibly; only destructive or meaning-changing actions (delete, evidence-link) confirm first. (Slack trust guidance: reversibility over interruption.)

### 4D. `ledger_view` — "where does the lab stand?"
The screen that has never existed. Rendered in the split-pane (and mirrored in the List). One section per hypothesis, ordered by activity:
```
header:   Where the lab stands
section:  🔴 *H2 · Scaling the ESM head beats full fine-tuning* — Refuted
          🟢 2 support · 🔴 2 contrast · evidence 14 mo old — re-verify?
          <permalink|Exp Mar 12>  <permalink|Exp Apr 2>  <doi|bioRxiv 2026>
section:  🟢 *H1 · Curriculum ordering improves convergence* — Supported (3 for)
section:  🟡 *H3 · Synthetic pretraining transfers to real assays* — Open (1 running)
context:  Every claim links to its evidence · compiled by Curie from #experiments
```
- **Modal (Link to hypothesis):** title "Link evidence", a `radio_buttons` for polarity (Supports/Contrasts/Mentions), a `static_select` of open hypotheses, submit. Pre-selects the agent's proposed polarity (user reviews, doesn't fill).
- **Empty state:** "No hypotheses tracked yet. Start one: `@Curie track hypothesis: <your claim>`."
- **Aging evidence** (Guru mechanic): any hypothesis whose newest evidence >12 mo shows the "re-verify?" nudge — a quiet trust signal, not an alarm.

### 4E. `error_card` — graceful failure (judges WILL trigger these)
```
section:  I couldn't finish the check — {one plain reason}.
actions:  [Try again]
context:  🤖 Curie
```
Reason strings (never a stack trace): rate-limited → "Slack's search is busy — give it a minute."; LLM/parse fail → "I couldn't read that as an experiment plan — try describing the method, data, and key settings."; not-enabled → "Curie isn't set up in this workspace yet — open my App Home to finish setup." Status indicator (`setStatus`) is ALWAYS cleared, even on error — never leave the app spinning.

---

## 5. The native List — the database as UI (no custom build)

The List *is* the record's UI; Slack renders it. Design responsibility here is **schema + semantics**, not pixels (schema in backend.md §4.1).

- **Two levels:** hypotheses (parent) → experiments (child). Collapse/expand is native. A judge can sort by Status, filter Kind=experiment, group by Owner — like a database, inside Slack. That sortability is the product's credibility in one gesture.
- **Column meaning is the design:** `Status` uses the color language (§3); `Evidence` shows polarity; `Source message` makes every row one click from its origin (provenance, free); `Notebook` opens the canvas; `Trust` shows verified vs auto.
- **The message + canvas columns are the secret:** they turn a spreadsheet row into a cited, expandable lab-notebook entry with zero custom UI.

## 6. The canvas — the self-writing notebook page

One per experiment, fixed section order (so the agent can target edits): **Goal · Parameters (table) · Timeline (each entry cites its message) · Outcome · Evidence links (± polarity) · Provenance**. Footer, always: *"Compiled by Curie from #experiments. Every line links to its source message. Nothing was typed by hand."* — this sentence is the product thesis, printed on the artifact.

- **Live-write moment (the demo's heart):** when a result is logged, the reader watches the Outcome section fill and the Timeline gain a line, in real time. Storyboard this in the video.
- **Empty state:** a freshly-created experiment page shows Goal + Parameters from the plan and "Outcome: pending — react 🧪 on the result message to log it."

## 7. App Home — dashboard, controls, onboarding

Tabs: **Home** (dashboard) and **Messages** (chat). Home layout, top to bottom:
1. `header` "Curie — your lab's memory".
2. Stats `section`: "**{n}** experiments tracked · **{n}** hypotheses · **{n}** collisions caught this month". (Collisions-caught is the value counter; if a compute/CO₂ estimate is enabled, one line: "≈ {n} GPU-days not repeated.")
3. "Recent activity" `section`: last 5 logged experiments, each linking its canvas.
4. "How to use" `section`: the three gestures — mention to check, 🧪 to log, `track hypothesis:` to add a bet.
5. Settings `actions`: [Open the Lab Record] [Ambient mode: On/Off] [Re-run setup].
- **First-run / empty state (F7):** if no List exists, Home replaces stats with a single primary button **[Set up Curie]** and copy: "I'll create your Lab Record and show you how to use me — takes 30 seconds." After setup, pin a "Test Curie in 60 seconds" canvas to `#experiments` with three copy-paste plans (one landmine, one near-miss, one clear) — this is also the judge's on-ramp.

## 8. Split-pane assistant — conversation

- **On open (`assistant_thread_started`):** greeting + context-aware suggested prompts (max 4): "What have we tried on {topic from current channel}?", "Where does the lab stand?", "Check a plan for me", "What failed last quarter?". Prompts adapt to the active channel (`assistant_thread_context_changed`) — showing the same four every time signals a disconnected app.
- **Answers stream** (plan-mode for anything requiring retrieval) and **always end with citations**. Long answers use `section` with `expand:true` (no "see more" click).
- **Thread title** set from the first question so History is browsable.

## 9. Copy deck (exact strings — do not paraphrase in build)

| Moment | String |
|---|---|
| Collision header | `⚠️ This was already tried` |
| Near-miss header | `🟡 Close to earlier work` |
| Clear body | `✅ No prior work found on this. Good to go.` |
| Working status | `Checking the record and literature…` |
| Log receipt | `✏️ Logged to {experiment} — status {status}. Notebook updated.` |
| AI disclaimer (every card) | `🤖 Curie · AI-generated · check before acting` |
| Canvas footer | `Compiled by Curie from #experiments. Every line links to its source. Nothing was typed by hand.` |
| Ledger empty | `No hypotheses tracked yet. Start one: @Curie track hypothesis: <your claim>` |
| Setup CTA | `Set up Curie` / `I'll create your Lab Record and show you how to use me — takes 30 seconds.` |
| Parse-fail error | `I couldn't read that as an experiment plan — try describing the method, data, and key settings.` |

Voice rules: state evidence, don't judge ("This was already tried" not "Don't repeat this!"); one idea per line; numbers and names over adjectives; never an exclamation mark; body copy has no emoji except the status glyph in the header.

## 10. Interaction & motion (what little Slack allows, used deliberately)

| Element | Trigger | Behavior | Timing |
|---|---|---|---|
| 👀 reaction | mention received | added instantly as first ack | <1 s (before any LLM call) |
| Plan stream tasks | each backend step done | flip pending→in_progress→complete | as work completes, no fake delay |
| Verdict card | check done | replaces stream via `stopStream` blocks | — |
| 👀 → ✅ | verdict posted | reaction swap signals "done" | — |
| Log receipt → "Reverted" | Undo click | in-place `chat.update` | <1 s |
| Canvas Outcome fill | result logged | section edit visible in open canvas | real-time |
| `chat.update` cadence | streaming/edits | never more than once per 3 s (rate limit) | ≥3 s spacing |

## 11. Accessibility (Slack handles rendering; these are our obligations)

- **State never by color/emoji alone:** every verdict states its level in words ("This was already tried"), every task label is a full sentence — screen readers convey meaning without the glyph.
- **Citations are labeled links** (`<url|human label>`), never bare URLs, so screen-reader users hear "Anika's run, March 12", not a URL.
- **Buttons have clear text labels** (no icon-only buttons in the critical path); `accessibility_label` set on any icon/feedback button.
- **Keyboard:** all actions are standard Block Kit buttons/selects — natively keyboard-navigable; we add nothing that breaks that.
- **Modals** use labeled inputs with the agent's proposal pre-filled, minimizing typing.
- **No reliance on hover** (Slack mobile has none): everything actionable is a tap target.

## 12. Edge cases (the "what happens when…" table)

| Situation | Behavior |
|---|---|
| Judge types garbage / off-domain plan | `clear` verdict, no false collision; parse-fail → the parse-fail error string |
| Empty workspace, no history | Clear verdicts + App Home nudges toward setup and the pinned test canvas |
| Very long plan / many params | Diff caps at 5 rows +"…N more" → Full comparison modal |
| Literature API down | Verdict still renders; "Literature check unavailable" context line |
| RTS rate-limited | error_card "Slack's search is busy — give it a minute." [Try again] |
| Duplicate/rapid 🧪 reactions | Idempotent (backend §7.3); one receipt only |
| Ambient mode on, chatty channel | Classifier gate ≥0.8; non-plans get no response (silence is correct) |
| Mobile | All cards ≤3 buttons, sections scannable, no hover dependence — already satisfied by §3 rules |
| Result logged wrongly | Undo (15 min) or edit the List row directly (native) |

## 13. What "done" looks like for design (definition of done)

A surface is done when: it uses the canonical card skeleton (§3), its states (default/working/empty/error) are all built (§4, §12), every claim carries a citation (§9), color is never the only signal (§11), and the copy matches the deck verbatim (§9). The product is done when a stranger with Member access can, from the pinned canvas alone, run all three gestures (check / log / track) and see a correct, cited result each time.
