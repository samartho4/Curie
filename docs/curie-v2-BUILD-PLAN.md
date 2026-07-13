# Curie v2 — Build Plan & Recommendation

*Read this before I change anything. It makes firm calls (you asked for "what's really best"), shows exactly what
I'd build and in what order, and ends with a one-line approval ask. Nothing in Slack or the code changes until you
say go. Backing research: `docs/curie-v2-synthesis.md` + `docs/research/`.*

---

## Recommendation in one line

Commit to **World 2 — Fleming Bay Therapeutics (antimicrobial-peptide discovery)** and build the **four-list,
hypothesis-first data model**, sequenced so the live detector stays green at every single step. Reasoning and the
exact build order are below.

---

## 1. Lab world → **World 2 (antimicrobial peptides).** Why it's the *best* demo, not just a good one.

The video's job is to make a mixed judge panel *feel* the "we already tried this" moment in ~20 seconds. AMP wins
on the four axes that decide a demo:

- **Legibility.** MIC (does it kill the bacterium) and hemolysis (does it kill human red blood cells) need zero
  setup. The optimization target — *therapeutic index*, "kill the bug, not the patient" — is a one-liner.
  Antibody developability (PSR / HIC / AC-SINS) is cooler to insiders but costs a paragraph of explanation the
  video can't spare.
- **Stakes.** A wet+dry loop means a false "clear to proceed" burns a **synthesis + assay cycle — real money and
  ~2 weeks**, not a re-run GPU job. That is exactly Curie's unforgivable-bug scenario, made physical and visible.
- **A perfect hero-collision.** "Just crank the cationic charge up to boost potency" is intuitive, tempting, and
  *wrong* (hemolysis climbs faster than potency past +6). A new team member re-proposing it is the most natural
  "Curie just saved you a batch" beat in the entire problem space.
- **Verdict range.** The four hypotheses naturally yield a **supported**, a **refuted**, an **open-but-confounded**,
  and a **qualified** result — so the demo can show calibration *both* ways: Curie doesn't cry wolf, *and* it won't
  flatten a nuanced finding into a wrong blanket memory.

Antibody affinity-maturation (your other instinct) is a strong fallback and arguably higher-prestige in 2026, but
it's a harder 3-minute watch. If you'd rather go antibody, say so and I'll re-cast — the data model below is
identical either way.

### The cast (5 — the role asymmetry is what makes the Slack traffic read as real)

| Person | Role | Voice / demo function |
|---|---|---|
| **Dr. Aisha Okonkwo-Reyes** | PI / CSO (ex-pharma) | "What's our TI on this?" — shows up for go/no-go. Frames *why* a false clear is expensive. |
| **Dr. Rana Al-Sayed** | Staff Scientist, Computational | Owns the generative pipeline; *was* the lab's human memory before Curie. The person Curie augments. |
| **Devon Marsh** | Wet-Lab Scientist (Microbiology) | Runs MIC/hemolysis plates; skeptical of "the algorithm's" picks. Posts assay results as clean tables. The wet-lab voice that never says "hyperparameter." |
| **Jun-ho Park** | ML Engineer | Trains the model; over-promises ("this batch looks incredible") before Devon's data lands. Believable, slightly comic. |
| **Dr. Naledi Mokoena** | Postdoc, Peptide Chemistry | Flags when a "great" sequence is a nightmare to synthesize. The real-world constraint models ignore. |

### The hypothesis ledger the demo revolves around

| ID | Claim (falsifiable) | Outcome | Demo role |
|---|---|---|---|
| **H1** | Raising net cationic charge +4→+7 boosts potency without a proportional hemolysis increase | **Refuted** — selectivity peaks at +5/+6, then hemolysis outpaces potency | **The hero collision.** The near-repeat a newcomer proposes; Curie warns with the exact charge/selectivity curve already on record. |
| **H2** | A multi-task MIC+HC10 classifier beats a binary AMP classifier at proposing high-selectivity candidates | **Supported** (2.3× median selectivity) | The "clear — adopt it" anchor; the lab's new default. |
| **H3** | Imperfect amphipathicity (disrupting the perfect helix) improves selectivity | **Supported, but scaffold-family-dependent** (holds for *P. aeruginosa* family, not *E. coli*) | **The nuanced memory.** Curie preserves the *qualifier* instead of letting "we tried that, didn't work" propagate. |
| **H4** | Grafting a validated motif onto new scaffolds beats de novo generation | **Open — confounded** by a synthesis artifact on one variant | **The calibration case.** Curie refuses to call it a settled negative; keeps the "re-test planned" nuance. |

The **clean "✅ good to go" beat** uses a plan genuinely outside all four (e.g., "try a D-amino-acid backbone for
protease stability") → Curie returns clear. That's the calibration proof shot (and the bug I fixed earlier — no
self-collision).

### Channel map (what the workspace becomes)

`#announcements` · `#general` · `#amp-design-round` (core, most hypothesis traffic) · `#wet-lab-assays` (Devon:
MIC/hemolysis, plate photos) · `#ml-pipeline` (Jun-ho/Rana: training runs, job-bot noise) · `#synthesis-chem`
(Naledi: synthesizability flags) · `#papers` (where the imperfect-amphipathicity paper gets shared before H3) ·
`#random` · `#curie-alerts` (product surface).

---

## 2. Data model → **the four-list, hypothesis-first build.** Built additively.

The structural fix (promote hypothesis to a first-class object) via four flat Slack Lists linked by native
`reference` columns (API-writable — verified). Condensed schema; full column-by-column in the synthesis doc.

| List | Is | Key columns |
|---|---|---|
| **Hypotheses** | the belief (ISA "Study") | `id`, `statement`, `status` (Open/Testing/Supported/Refuted/Inconclusive/Superseded), `confidence` (rating = the literal "Prior"), `owner`, `origin_thread`, `canvas_summary` (living per-hypothesis canvas) |
| **Experiments** | the run (ISA "Assay") — *today's list, enriched* | + `hypothesis` (→Hypotheses), `follows_up_on` (→self) + `link_type`, and **`status` (run state) split from `outcome` (evidence direction)** |
| **Results** | the measurement | `experiment` (→Experiments), `measurement`+`unit`, `interpretation_note` (kept apart from the raw number), `qc_flag` |
| **Belief Updates** | the ledger ("compiled by Curie") | `hypothesis`, `new_status`, `based_on_results` (multi-→Results = the evidence chain), `meaning`, `superseded_by` (append-only) |

**The two changes that matter most for calibration:** (1) splitting `status` from `outcome` means a broken-pipette
`Failed (technical)` run is no longer scored as evidence *against* a hypothesis — it kills a whole class of false
collisions; (2) `based_on_results` makes every "Supported/Refuted" verdict cite the exact rows that justify it —
turning a verdict from a vibe into an auditable claim.

### Sequencing that keeps the demo green (the "never break the detector" rule)

- **Phase A — additive, zero risk to the live path.** Add the `outcome`-vs-`status` split and the trace object to
  the *existing* Experiments list + preflight. Re-run the offline eval (must stay zero false collisions). Demo
  still works throughout.
- **Phase B — stand up the new Lists.** Create Hypotheses, Results, Belief Updates; seed World 2. The detector
  keeps reading Experiments; the ledger starts reading Hypotheses. Wire `reference` links.
- **Phase C — migrate reads.** Point ledger/verdict evidence at the linked graph (walk Hypotheses ← Experiments ←
  Results). Re-run eval + a live smoke on every hypothesis beat.
- **Phase D — the high-wattage surfaces** (see §3), each independent and add-as-time-allows.

No phase is merged if it leaves the detector broken. The eval harness (zero false collisions) is the gate between
every phase.

---

## 3. Capabilities → **build them all, in this order** (value × safety)

| # | Capability | Demo payoff | Touches | Risk |
|---|---|---|---|---|
| 1 | **status/outcome split + verdict trace** | Fewer false collisions; a verdict you can defend row-by-row | preflight, cards | Low (additive) |
| 2 | **hash-gate re-verdict** | Protects the ≤3-RTS budget; instant on no-op edits | app_mention, preflight | Low |
| 3 | **Four-list model + World 2 re-seed** | The first-class-hypothesis payoff; a credible lab | seed, record_store, ledger | Medium — gated by eval |
| 4 | **App Home belief ledger** | Persistent "where the lab stands" home tab: open hypotheses, confidence trend, retries | app_home | Low-med |
| 5 | **Per-hypothesis living canvas** | *Self-writing memory made visible* — Curie compiles a canvas per hypothesis | tools/canvas, ledger | Med |
| 6 | **Staleness Tracker (scheduled)** | The real autonomy beat — proactive belief update when evidence is superseded | new pipeline job | Med |
| 7 | **message shortcut + link_shared unfurl** | "Check this against prior work" on any old message; record links unfurl as cards | listeners | Low |

My honest read: **1–5 are the ones that win the category** (they make Curie feel like a memory, not a search box).
6 and 7 are genuine wow-adds if time allows, and since you said sky's the limit, I'd build them too — but after
1–5 are solid and the video is safe.

---

## 4. How this plays in the ~3-minute video

1. **Cold open** — Curie story (the radioactive-notebook line), then: a lab's Slack scrollback is worthless the
   day someone leaves. Cut to #amp-design-round.
2. **Hero collision** — a newcomer posts "let's just push cationic charge to +8 for more potency." Curie streams
   "Checking priors…", returns **⚠️ already tried** with H1's charge/selectivity curve and the permalink to the
   Round-1 post-mortem. *This is the money shot; stakes = a wasted synthesis batch.*
3. **Where the lab stands** — the hypothesis map (H1 refuted, H2 supported, H3 supported-but-qualified, H4 open).
4. **Nuance** — someone says "imperfect amphipathicity didn't work" → Curie corrects: it *did*, for one scaffold
   family (H3's qualifier preserved).
5. **Clear** — a genuinely novel plan (D-amino-acid backbone) → **✅ good to go.** Calibration proof.
6. **Autonomy** — the staleness Tracker posts a belief update on its own; App Home shows the living ledger.
7. **Close** — "compiled by Curie" — the notebook that keeps itself.

The data-model and world choices above exist to make beats 2–6 land. That's why they're worth the rebuild.

---

## 5. What I need from you

Just two confirmations and I start Phase A immediately:

1. **World 2 (AMP)** as recommended — or swap to antibody / adjust the cast?
2. **"Do everything" scope confirmed** — build capabilities 1–7 in order, green-at-every-step?

Everything here is reversible on paper until you approve. Say go and I'll begin with the safe Phase-A changes and
re-run the eval before anything touches live Slack.
