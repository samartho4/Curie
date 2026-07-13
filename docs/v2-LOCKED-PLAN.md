# Curie / Prior v2 — Reconciled Locked Plan

*Merges the other agent's Buildbook with my synthesis (`curie-v2-BUILD-PLAN.md`) and the `CLAUDE.md` naming
canon. Bottom line: the Buildbook is strong and beats my draft on two calls — I'm adopting them. It flags one
"bug" that actually contradicts your own settled naming decision; that's the single real fork left.*

---

## 1. Where the Buildbook improves on my plan — I'm switching to match it

**Lab world → antibody affinity maturation (Helix Bio), not my antimicrobial-peptide pick.**
The deciding factor I under-weighted: the demo trigger you already built and proved live —
`@Prior planning to fine-tune the ESM baseline, lr 1e-4, batch 32, on the v2 split` — is *literally* what an
antibody-ML engineer types. AMP would force me to rewrite that trigger; antibody makes the **existing, working**
trigger bulletproof. And its collision — **clonal-lineage train/test leakage → catastrophic forgetting on ~380
labels** — is a famous, respected pitfall a bio-literate judge will nod at, with a real 2025 paper (nucleotide-
context models beating protein LMs at affinity maturation) to cite. This is the better call. Switching.

**Data model → 2 Lists (Experiments as children of Hypotheses via `parent_item_id`) + a Canvas per experiment,
not my 4-List `reference` model.** Why it's the wiser demo choice:
- It renders as **nested rows** in Slack (a hypothesis with its experiments underneath) — more striking than
  reference links.
- It **aligns with the parent/child code you already have** (`ledger._parent_of` already reads `parent_record_id`;
  `register_hypothesis`/`rollup` already treat hypotheses as parents). So it's *extending* the current
  architecture, not replacing it — far less rework than my 4-list rebuild.
- It still captures the two things I cared about from the ELN research: **run-`Status` split from evidence-`Result`
  polarity** (kills a class of false collisions), and **provenance** (a source-message link per row + the canvas).

My 4-List model (separate Results + append-only Belief-Updates lists) stays in `docs/research/` as the
"if-you-productionize-later" version. Don't build it now.

## 2. The one real conflict — naming (your call)

The Buildbook calls *"compiled by Curie"* a bug and says globally replace **Curie → Prior**. Heads-up: that
contradicts **your own settled decision** in `CLAUDE.md` — **Curie = the product** (Devpost name, App Home header,
the "🤖 Curie" disclaimer, "compiled by Curie", the Marie-Curie radioactive-notebook cold open) and **@Prior = the
agent you @mention** — exactly the **Bubble Lab / @Pearl** pattern you deliberately chose. So "compiled by Curie"
is *intentional brand copy*, not a bug.

The Buildbook's underlying worry is still fair: a judge who misses the product-vs-agent split could read "the bot
is Prior but it signs as Curie" as sloppiness. Two clean resolutions:

- **(Recommended) Keep the dual name, make "Curie = product" visible.** App Home: *"Curie — your lab's memory ·
  talk to it with @Prior."* Video cold-open establishes Curie as the product. Then "compiled by Curie" over a
  @Prior message reads exactly like a Slack app @Pearl signing "Bubble Lab" — correct, not inconsistent. Zero
  rename; keeps the strongest cold-open story.
- **Collapse to a single name "Prior" everywhere.** Simplest, zero possible confusion — but you lose the "Curie"
  brand and the radioactive-notebook cold open (or you re-tell it about "Prior").

This is the one thing I need you to decide before I touch any strings.

## 3. Corrected bug list

- **Bug #2 (H2 ↔ trigger logic) — REAL. Adopting the fix.** Today's H2 ("LoRA head-scaling beats full fine-tune",
  Refuted) doesn't cleanly re-fire on a *full* fine-tune trigger. Restate H2 as a claim about the **fine-tune
  approach the trigger re-proposes**: *"Fine-tuning ESM on our SPR-labeled variants predicts held-out KD well
  enough (Spearman ≥ 0.6) to prioritize the next library without wet-lab — Refuted (clonal-lineage leakage inflated
  ρ0.71→0.2; then catastrophic forgetting on ~380 labels; a nucleotide-context baseline beat it)."* Now
  `fine-tune ESM, lr 1e-4, batch 32, v2 split` re-fires H2 airtight.
- **Bug #1 (Curie → Prior) — NOT a bug per your canon.** Folded into the naming decision above; don't blind-replace.

## 4. Workspace — adopt the Buildbook's Part C + E wholesale

All correct: rename workspace **Prior Lab → Helix Bio** (so it reads as the lab, with the app installed); ~8
legible channels with **every topic/description filled**; the four canvases (Lab Home, How-to, **Test-in-60s**,
**Hypothesis Map**); two Lists with saved views; the reacji legend; the "make the excluded ELN features look rich"
lightweight stand-ins (Samples list, one-tap Trust verify, canvas changelog-as-audit, ask-don't-SQL, run webhook);
and the authenticity checklist — **threads not walls, timestamps spread over ~6 months, ≥5 personas with avatars**.
These are the difference between "real lab" and "staged," and they're right.

## 5. Locked execution order (green-at-every-step) + who does what

**Phase 0 — me, zero side effects (start now):** finalize the antibody canon (5 personas, H1/H2/H3, EXP-01…15 with
the collision numbers *locked* — 650M ESM-2, lr 1e-4, batch 32, ~380 SPR labels, v2 split), the exact List schemas
+ canvas markdown, and the timestamped, threaded seed script — all as paste-ready artifacts in the repo.

**Phase 1 — code, safe:** apply the H2 restatement + the `Status`/`Result` split + whatever the naming choice
implies for canned strings; **re-run the zero-false-collision eval** (the gate).

**Phase 2 — Slack, needs your go (some are yours only):**
- Rename workspace → Helix Bio — **you** (30s).
- Create the 5 persona accounts with avatars/profiles — **you** (I can't create accounts).
- Create channels + user groups, build the 2 Lists + canvases, post the seed history *as the personas* — **I can
  drive these via the Slack tools on your explicit go** (posting-as-personas and channel creation are
  send-on-behalf actions), or hand you a script to run.

**Phase 3 — verify:** live smoke on every demo beat (collision → map → clear → digest → autonomy) + eval green.

## 6. What I need from you

1. **Naming:** keep dual-name (Curie product / @Prior agent, recommended) or collapse to single-name "Prior"?
2. **Nod on antibody + Helix Bio** (or keep the current enzyme story, which is lower-rework but a slightly less
   iconic collision).

On your answer I start **Phase 0 immediately** (no side effects) while you rename the workspace and add the
persona accounts.
