# Curie — Demo Maximization Plan (final ~24h before Mon 5pm PDT)

**Governing idea:** the product path is *complete and proven live* (collision + fix (b), self-writing
record, digest+chart, map, Claude Science → Slack cross-tool, and the proactive belief alert via the
poller). What separates "it works" from "it wins" now is whether the whole **workspace reads like a
real lab's living memory** the moment a judge opens it. So we polish the **surfaces** a judge actually
sees — channels, Files tab, Tools tab, canvases — and we frame the data model in real ELN/LIMS
language. We do **not** rearchitect the code or rename modules this close to the deadline.

Everything below is tagged **[SHIP]** (high impact, low risk — do it), **[STRETCH]** (do if time),
or **[DEFER]** (post-submission / v2). Grounded in `docs/research/curie-data-model-research.md`,
`docs/research/curie-lab-worlds.md`, and fresh Slack-surface research (sources at end).

---

## Front 1 — Polish the workspace as a real lab

Real labs have a *tell* when they're fake: flat, same-voiced personas and a thin channel list. Our
`curie-lab-worlds.md` research already solved this with two fully-built worlds. Decision needed:

- **World 1 — Ossowski Lab (dry protein-ML).** Closest to what's *already seeded* (ESM2, curriculum
  ordering, kcat regression). Pure-computational, so no wet-lab vocabulary to explain to Slack-platform
  judges. Its H1 (curriculum-ordering **split-leakage** gotcha) is an elegant, self-contained "we
  already tried this" that needs zero biology to appreciate. **Lowest-risk upgrade of the current build.**
- **World 2 — Fleming Bay Therapeutics (hybrid wet+dry AMP).** More visceral stakes — a false "clear
  to proceed" burns a **synthesis + assay cycle = real dollars + weeks**, not just GPU-hours. Better
  drama, but requires re-seeding into AMP content (MIC/hemolysis, selectivity ratio) and introduces
  wet-lab terms.

**Recommendation: World 1 (Ossowski Lab).** It's a *polish* of the existing seed, not a rewrite, and
the split-leakage story is the single cleanest "Curie would've caught this" beat for a mixed judging
panel. Keep Fleming Bay as the named v2 direction in the Devpost ("the same memory layer generalizes
to wet-lab DBTL loops where the stakes are dollars, not GPU-hours").

**[SHIP] Concrete polish (all in the seed, no code change):**
- **5 personas with role asymmetry** (PI who only shows up for go/no-go; staff scientist = the human
  memory Curie augments; infra/ML engineer who posts job-died noise; anxious PhD who re-derives the old
  idea; wet-lab-adjacent postdoc who reality-checks). Distinct voices — terse lowercase vs. pedantic-
  with-citations vs. hedging.
- **Richer channel layout:** `#announcements`, `#general`, `#experiments` (the product channel),
  `#embeddings-infra` (Slurm/job-bot noise), `#papers` (journal club — the "why we tried X" context),
  `#external-wetlab-partner` (async data drops), `#random` (social). Their *absence* is a tell; their
  presence sells "lived-in."
- **A dated 6–9 month arc** seeded as backdated List rows + a canvas changelog (message timestamps
  can't be backdated — dates live in List date columns and canvas text, per `HANDOFF`/`MERGE-HANDOFF`).
  The arc must contain the **near-repeat incident** (someone re-proposes the closed curriculum idea from
  a stale branch) — that's the emotional core.

**[DEFER] module renames (listeners/tools/pipeline → ELN terms).** Intellectually it's a nice fit
(see Front 2), but it's **internal — a judge never sees a module name** — and renaming this close to
the deadline risks breaking imports on a live, working deploy. Apply ELN/LIMS naming where it's
*visible* (List/column/canvas names, Devpost copy), not in the package tree. Revisit for v2.

---

## Front 2 — Data model: ELN vs LIMS, and "4 Lists or 2?"

`curie-data-model-research.md` did the deep work: real systems (Benchling, eLabFTW, SciNote, ISA
model, ALCOA+/FAIR) converge on **ELN, not LIMS**. LIMS is sample/inventory logistics (barcodes,
freezer locations, chain-of-custody); **ELN is the *notebook* — hypothesis → experiment → result →
conclusion**, which is exactly Curie. The single most load-bearing finding: ISA defines the
**"Study" = the hypothesis-testing unit that contains multiple Assays** — i.e., the hypothesis must be
a first-class, addressable object *above* individual runs. Curie already does this (hypotheses = parent
rows, experiments = child rows). **That structure is correct and ELN-aligned.**

The research's ideal is **4 cross-referenced Lists** (Hypotheses · Experiments · Results ·
Belief-Updates, + optional Protocols/Reagents registry) because Slack Lists only nest **one** level.

**Decision — "4 or 2":** ship the **current 2-level model** (Hypotheses↔Experiments), because it
works and is already deployed and eval-passing. Do **not** re-architect to 4 Lists before the deadline
— that's the highest-risk change on the board and the judges can't tell 2 well-presented Lists from 4.
Instead:

- **[SHIP] Frame it in ELN language everywhere judges look.** The List is the **"Lab Record"**; the
  hypothesis parent rows are the **"Belief Ledger"**; the already-shipped `status` vs `outcome` split
  (run-state vs evidence-polarity) is exactly the ELN distinction between *what happened* and *what it
  means* — call that out in the Devpost as a deliberate ALCOA+ "don't let interpretation overwrite the
  observation" choice. Provenance = `created_by`/`created_time` system columns (Attributable +
  Contemporaneous) + the append-only belief changes (never overwrite a verdict).
- **[SHIP] Add the two *cheap* enrichments from the research that raise authenticity with near-zero
  risk:** a per-hypothesis **`confidence` rating** column (Slack's native `rating` — literally the
  "Prior" dial the agent checks) and a per-hypothesis **`canvas` column** (the self-writing summary —
  see Front 3). Both are additive columns, not a schema rewrite.
- **[DEFER] the full 4-List model (Results + Belief-Updates as their own Lists, Protocols/Reagents
  registry).** This is the real v2 (there's already `docs/v2-LOCKED-PLAN.md`). Present it as the
  roadmap, don't build it tonight.

**Retrieval angle the user asked about:** ELN framing *improves* retrieval story — because the
hypothesis is addressable, "where does the lab stand?" walks Hypotheses→Experiments deterministically
(no LLM guessing), and RTS alias-expanded search enriches it. That's the "smart retrieval" point:
structured-record-first (the List), literature/RTS second — the Glean pattern already in the code.

---

## Front 3 — Files tab: make the Lab Record *shine*

The Files tab surfaces **files + canvases + lists** together. A judge who clicks Files should see an
authentic lab knowledge base, not an empty tab. Seed it:

- **[SHIP] The "Lab Record" List** — well-populated, dated across the 6-month arc, with the
  status/outcome columns and the hypothesis parents. This is the centerpiece and it already exists;
  just make sure it's rich and clean.
- **[SHIP] Per-hypothesis canvases — the "self-writing lab memory" made visible.** One canvas per
  tracked hypothesis: *current claim · status · evidence for/against (linked) · open questions · next
  planned experiment · dated belief-changelog.* This is the most on-brand artifact we can add — it
  literally *is* "the notebook that keeps itself," and canvases render beautifully in the Files tab.
  Curie can compile/refresh these (the code already has a `canvas` tool). Even 2–3 seeded ones sell it.
- **[SHIP] A pinned "Read me — how the Lab Record works" canvas** in `#experiments` (channel canvas):
  what @Prior does, how to log a run, how to read a verdict. Doubles as judge onboarding.
- **[STRETCH] 2–3 seeded figures/files** (a loss curve, a Spearman-vs-n plot, a one-page protocol PDF)
  so the Files tab has real *files*, not just canvases — reinforces "lived-in."

Best-practice from the knowledge-base research that we already satisfy: **source attribution** — every
Curie verdict links back to the evidence message/row ("Every claim links to its evidence"). Keep that
front-and-center; it's the trust primitive judges reward.

---

## Front 4 — Tools tab: Agents, Workflows, apps, channel templates

This is the biggest *untapped* "platform depth" opportunity, and the research shows it's achievable:

- **[SHIP] Show Curie in the Agents surface.** The app already ships `agent_view` (App Home messages
  tab). Make sure the App Home header reads "**Curie — your lab's memory**" with clean suggested
  prompts, so when a judge opens the agent it's polished. Low effort, high "this is a real agent" signal.
- **[STRETCH — high impact] A "Log a run" Workflow (Workflow Builder form).** Instead of only the
  `📊 Run …` text convention, add a native Slack **form**: scientist clicks a shortcut → fills
  *experiment / status / outcome / params* → the workflow posts the structured run-record to
  `#experiments` → Curie's poller ingests it → belief alert fires. This is *more* "real lab" than typing
  a magic string, and it demonstrates Workflow Builder integration. ~30 min of no-code Slack setup;
  the run-record format it emits is the same one the poller already parses.
- **[STRETCH] A "Lab" channel template.** Channel templates bundle a list + canvases + workflows into
  channel-header tabs. A "New Lab Project" template that instantiates: the Lab Record list, a hypothesis
  canvas, and the log-a-run workflow. Story: "spin up a new project channel and it's lab-ready in one
  click." Strong platform-native narrative and it's a 2026 Slack feature judges may not have seen used.
- **[DEFER] A custom Workflow Builder step ("Preflight this plan").** Deep Bolt integration — Curie
  exposes a reusable step other workflows can call. Great for v2; too much build for tonight.

---

## Prioritized execution order (what I'd actually do next, in order)

1. **[SHIP] Reset + reseed the workspace clean** to the Ossowski World-1 arc (dated 6-month history,
   5 personas, richer channels, the near-repeat incident) — this also fixes the current clutter
   (exp-142…211, probes) and the exp-211 H2→Open flip. *This is the single biggest visual upgrade.*
2. **[SHIP] Seed 2–3 per-hypothesis canvases + the pinned "read me" channel canvas** (Files-tab shine).
3. **[SHIP] Polish App Home** ("Curie — your lab's memory", suggested prompts).
4. **[SHIP] Frame the data model in ELN language** in the Devpost + demo VO (Belief Ledger, status vs
   outcome = ALCOA+, evidence-linked verdicts, ISA "Study" = hypothesis).
5. **[STRETCH] Build the "Log a run" Workflow Builder form** (if time) — strongest single platform beat.
6. **[STRETCH] Build the "Lab" channel template** (if time).
7. Then: **record demo-SKY** on the clean workspace, write Devpost + architecture diagram, submit.

**Deadline guardrail:** items 1–4 are the win; 5–6 are upside. Nothing here touches the working
listeners/pipeline code except optional additive columns, so the proven build stays proven.

---

## Decisions I need from you

1. **Lab world:** polish into **World 1 (Ossowski, dry protein-ML — recommended, closest to current
   seed)** or commit to **World 2 (Fleming Bay, wet+dry AMP — more drama, more re-seeding)**?
2. **Data model scope:** ship the **current 2-level model framed in ELN language + cheap canvas/rating
   enrichments (recommended)**, or invest in the full **4-List** model (risky before deadline)?
3. **Module renames (listeners/tools/pipeline → ELN terms):** **defer to v2 (recommended — invisible to
   judges, risky now)**, or you want it done carefully tonight?
4. **Tools-tab stretch:** build the **Log-a-run Workflow** and/or **Lab channel template**, or keep the
   scope to the [SHIP] items and focus on recording + submission?

---

## Sources (new, Slack surfaces)
- [Use a canvas in Slack](https://slack.com/help/articles/203950418-Use-a-canvas-in-Slack)
- [Canvases — Slack Developer Docs](https://docs.slack.dev/surfaces/canvases/)
- [Guide to Slack channel templates](https://slack.com/help/articles/33223290843667-Guide-to-Slack-channel-templates)
- [Create and share custom channel templates](https://slack.com/help/articles/33777191777043-Create-and-share-custom-channel-templates)
- [Guide to Slack Workflow Builder](https://slack.com/help/articles/360035692513-Guide-to-Slack-Workflow-Builder)
- [Automations: Collect information with a simple form](https://slack.com/help/articles/24720245025555-Automations--Collect-information-with-a-simple-form)
- [Custom Steps for Workflow Builder (Bolt)](https://docs.slack.dev/tools/bolt-python/tutorial/custom-steps-workflow-builder-existing/)
- [Add and manage tabs in channels and DMs](https://slack.com/help/articles/32562841868307-Add-and-manage-tabs-in-channels-and-direct-messages)
- [AI Knowledge Base — best practices (Slack)](https://slack.com/blog/productivity/what-is-an-ai-knowledge-base-tools-features-and-best-practices)

*(ELN/LIMS + lab-world sources are in `docs/research/curie-data-model-research.md` and
`docs/research/curie-lab-worlds.md`.)*
</content>
