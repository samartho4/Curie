# Curie v2 — Research Synthesis & Design Decisions

*Distills three deep-research streams (competitors, ELN/LIMS data models, credible lab worlds) into
concrete changes to Curie's data model, listeners, tools, and narrative. Full source reports live in
`docs/research/`. Platform facts verified against `/websites/slack_dev` via context7, Jul 11 2026.*

---

## TL;DR — the one structural gap

Curie's pipeline (detect → verdict → ledger → logging) works. The thing holding it back is **one modeling
mistake**: the current flat "Lab Record List" conflates *hypothesis*, *experiment*, and *conclusion* into a
single row. Every mature system we studied — and the ISA scientific-metadata standard — keeps these separate:

> **ISA defines "Study" as *the hypothesis-testing unit*, containing multiple "Assays" (individual experiments).**
> A hypothesis is an object that sits *above* experiments and accumulates evidence over time.

That single fix — promote the hypothesis to a first-class, addressable object — is what turns Curie from "a
smarter search over a table" into "the lab's memory of what it believes and why." Everything else below is in
service of that.

---

## 1. What the competitors teach (the steals)

Eight products torn down (`docs/research/curie-competitive-teardown.md`). The ones that change Curie:

- **Unblocked** — *authority/freshness ranking as an explicit named function*, not embedding similarity. Curie's
  tie-break should be spelled out: **structured List record > recent Slack message with explicit outcome
  language ("failed", "abandoned") > older message > literature.** This is directly our differentiator.
- **Guru** — *verification as a ranking signal, never a hard gate.* A stale/ambiguous prior record can be flagged
  `low confidence` and down-weighted, but still counts as prior art on day one. (Guru gates; we must not — it
  would make collision-check useless until someone does manual review.)
- **Notion** — *hash-before-recompute (Page State).* Hash the normalized plan (method + params + hypothesis); if a
  scientist edits a plan message but the substance is unchanged, skip the full re-verdict and re-post the cached
  one. Protects the ≤3-RTS-call budget and literature quota.
- **Dust (Tracker)** — *event-triggered staleness detection is a proven production pattern*, structurally
  identical to our belief-updates feature. Validates the direction; we don't need Temporal to do it.
- **Bubble Lab** — *the execution trace IS the audit log.* Every verdict should be reconstructable as an ordered
  trace (RTS query → List lookup → LLM verdict, with counts/latency). This is what makes "we already tried this"
  defensible when a scientist pushes back — and it makes "false collision is the unforgivable bug" *auditable*.
- **PromptQL / Glean** — *query-pushdown, don't prompt-stuff.* LLM retrieval degrades exactly on our core query
  ("has this reagent+method+split combination been tried"). Filter the List server-side / in code; never paste
  the whole list into the prompt and ask the model to eyeball it.
- **Slack's own docs** — the **structured-state object** `{goal, constraints, decisions, artifacts, sources}` is
  Slack's *first-party* recommendation, not our invention. Adopt it verbatim for pipeline state.

## 2. What ELN/LIMS teaches (the data model)

Full report: `docs/research/curie-data-model-research.md`. Convergent principles across Benchling, eLabFTW
(open-source, real schema), SciNote, the ISA standard, ALCOA+ / 21 CFR Part 11, and FAIR:

1. **Separate the registry of *things* from the log of *events* from the graph of *process*** (Benchling).
2. **Hypothesis is its own object** (ISA "Study"), above experiments — the load-bearing fix.
3. **Model provenance as edges, not prose** — "this experiment follows up on that one" is a typed link, not a
   sentence Curie has to re-parse.
4. **A result is not a verdict** — keep *what was measured* separate from *what was concluded*. Our current
   `outcome` column conflates them; splitting `status` (run state) from `outcome` (evidence direction) directly
   targets the false-collision bug (a broken pipette is `Failed (technical)`, **not** evidence against the
   hypothesis).
5. **Provenance is a stack**: stable ID + append-only history + recorded-by + system timestamp + "what this
   assertion meant." All achievable free via Slack's system columns.

### Proposed v2 data model — four cross-linked Slack Lists

Verified: Slack Lists have a native **`reference` column** whose `list_record: {list_id, row_id}` is
**writable via `slackLists.items.create/.update`** — so cross-list links work through the API (not just the UI).
Hierarchy is one level only, which is *why* we use four flat lists linked by references rather than nesting.

```
HYPOTHESES ──1:N──> EXPERIMENTS ──1:N──> RESULTS ──N:1──> BELIEF UPDATES
(ISA "Study")       (ISA "Assay")        (measurement)     (the "compiled by Curie" ledger entry)
   ▲                    │
   └── belief state     ├─ hypothesis   → reference(Hypotheses)   ← turns the flat list into a chain
       accumulates      ├─ follows_up_on → reference(self)        ← replicates / retries / iterations
       over time        └─ protocol      → reference(Protocols, optional v1)
```

- **Hypotheses** — `id`, `statement` (falsifiable), `status` (Open/Testing/Supported/Refuted/Inconclusive/
  Superseded), `confidence` (rating = the literal "Prior"), `owner`, `origin_thread` (message col),
  `canvas_summary` (a living per-hypothesis canvas — *this* is "self-writing memory made visible").
- **Experiments** — the enriched current list. Adds `hypothesis` (reference), `follows_up_on` (self-ref) +
  `link_type`, and the crucial **`status` (run) split from `outcome` (evidence)**.
- **Results** — `experiment` (reference), `measurement`+`unit`, `interpretation_note` (kept apart from the raw
  number), `qc_flag`. One experiment can yield many results.
- **Belief Updates** — the ledger. `hypothesis`, `new_status`, `based_on_results` (multi-reference = the evidence
  chain), `meaning` (Prior's read / Human-reviewed / Overridden), `superseded_by` (append-only, never edit).

## 3. New listeners & tools the research earns us

| Add | Source | Value |
|---|---|---|
| **Message shortcut** "Check against prior work" | Slack-recommended "act on this message" pattern | Run a preflight on any past plan without re-posting/@-mentioning. Reuses the whole pipeline. |
| **`link_shared` unfurl** for List permalinks | Slack surfaces | Sharing a hypothesis/record link unfurls a Block Kit card (statement, status, confidence) — makes the List a visible source of truth. |
| **App Home belief ledger** | Slack + Guru | Persistent "where the lab stands": open hypotheses, confidence trend, recent verdicts, retry buttons. Product surface = "Curie" branding. |
| **Staleness Tracker** (scheduled) | Dust Tracker | Scans open hypotheses whose evidence was superseded; posts a belief update proactively. The real "autonomy" beat. |
| **Hash-gate re-verdict** | Notion Page State | Skip recompute on no-op plan edits; protects RTS/literature budget. |
| **Trace object on every tool call** | Bubble Lab | Powers the "Checking priors…" stream *and* the disputable audit trail. |

## 4. The lab world (narrative)

Full report + personas + hypotheses: `docs/research/curie-lab-worlds.md`. Two candidates, both grounded in real
2024–2026 literature:

- **World 1 — The Ossowski Lab** (dry-lab protein-ML: ESM2, enzyme-kcat regression). Elegant, self-contained ML
  "gotcha" hypotheses (curriculum-ordering split-leakage). Safer, no wet-lab vocab. Fallback.
- **World 2 — Fleming Bay Therapeutics** (hybrid wet+dry antimicrobial-peptide discovery, design-build-test-learn
  loop; 5 personas incl. a wet-lab microbiologist and a peptide chemist). **Recommended.** The wet/dry split is
  exactly where "we already tried this" costs *real money and weeks* (a synthesis+assay cycle), so a false "clear"
  has visceral, demo-worthy stakes. Hypotheses (charge-ladder selectivity, multi-task MIC+hemolysis, imperfect
  amphipathicity, motif-grafting) are checkable against a physical assay — legible to a judge, precise enough for
  an ML-for-science expert.

The user already gestured at "antimicrobial lab / antibody labs" — World 2 matches that instinct and is the
research's recommendation.

## 5. Scope — what to land now vs. aspirational

There is a working, demo-ready pipeline. The honest framing: v2 is a real upgrade, but rebuilding the schema +
re-seeding + rewiring `record_store`/`ledger`/`preflight` is a destabilizing change with the video still to
record. Three tiers:

- **Tier 1 — safe, high-leverage, land now:** split `status`/`outcome`; add the trace object + authority-ranking
  tie-break; hash-gate re-verdict; the message-shortcut entry point. All additive; none rip out the working path.
- **Tier 2 — the structural upgrade:** stand up the **Hypotheses** + **Results** + **Belief Updates** Lists,
  wire `reference` links, re-seed the chosen lab world. This is where the "first-class hypothesis" payoff lives —
  ambitious but the highest-value change. Needs careful re-seed + eval re-run (zero false collisions).
- **Tier 3 — aspirational:** `link_shared` unfurls, per-hypothesis living canvases, scheduled staleness Tracker,
  App Home ledger v2. Each independent; add as time allows.

---

## Open decisions (for Samarth)

1. **Lab world** — World 2 (AMP, recommended) vs World 1 (protein-ML) vs a hybrid.
2. **Data-model scope** — full Tier-2 rebuild now, enrich-in-place, or design-only until after the video.
3. **Which Tier-1/Tier-3 capabilities to prioritize** — message shortcut, `link_shared` unfurl, App Home
   ledger, staleness Tracker, hash-gate.
