# Curie Demo Lab Worlds — Research Report & Two Candidate Designs

This report grounds two candidate "lab worlds" for the Curie demo in how real computational-biology / protein-ML / antimicrobial-peptide / antibody-discovery teams are actually organized, staffed, and how they use Slack, plus what current (2024–2026) research hypotheses in these fields actually look like. Sources are cited inline; a consolidated source list is at the end.

---

## Part 0 — Research findings that shaped both worlds

### 0.1 How real teams are structured and staffed

Real interdisciplinary protein-ML groups are **not** three interchangeable "ML person" roles — they have distinct functions that create natural, asymmetric Slack traffic:

- **PI (Principal Investigator)**: sets scientific direction, is often *not* in the daily technical weeds, appears in Slack mostly for go/no-go calls, funding-deadline pressure, and paper strategy.
- **Staff Scientist**: a senior, often permanent non-faculty role with "substantial intellectual independence" — designs and executes complex studies, leads high-impact projects day to day, mentors postdocs/grad students, and is usually the person who actually runs the lab's technical culture ([NIH Staff Scientist description](https://hr.nih.gov/careers/open-positions/job-27e8fcff-dcfe-48f8-8d8f-d8ae6cf914bf)).
- **ML/Computational staff scientists or ML engineers**: contribute to 2–3 projects simultaneously, "design, develop, and evaluate machine learning approaches," and do the unglamorous but critical work of "data wrangling, harmonization, standardization, and quality control" ([Indeed/HR postings synthesis](https://www.indeed.com/q-computational-biology-jobs.html); [Latent Labs MTS-ML posting](https://www.latentlabs.com/job/member-of-technical-staff-mlbiology/)).
- **Postdocs / grad students**: run the actual experiments (wet or dry), are the ones who post "my run just finished" or "the assay failed" messages, and are highly variable in Slack voice — some terse, some chatty.
- **Wet-lab scientists / research associates**: exist as a distinct role from computational staff in hybrid labs; they don't write model code but post assay results, order reagents, and flag protocol issues.
- In real AI-native biotechs (BigHat Biosciences, Absci, Generate Biomedicines), this splits further into **Data Science teams** (own the pipelines that turn assay data into model-ready datasets) vs. **wet-lab/CFPS (cell-free protein synthesis) teams** vs. **ML/platform teams** — a real "lab-in-the-loop" design ([BigHat Biosciences overview](https://www.genengnews.com/topics/artificial-intelligence/ai-created-antibodies-drive-innovation-at-bighat-biosciences/); [BigHat careers/CBInsights](https://www.cbinsights.com/company/bighat-biosciences)).
- Interdisciplinary teams that mix "machine learners, protein engineers and biologists" jointly are explicitly called out in the literature as the structure that produces high-impact discoveries — and also the structure most prone to communication gaps that a memory tool like Curie would fix ([role of organizational structure in science, PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9371286/)).

**Implication for the demo**: 3 flat, similarly-voiced "ML person" personas reads as fake. A credible lab needs at least one senior technical non-PI voice (staff scientist), one infra/data-plumbing voice, and — for the hybrid world — a wet-lab voice that never talks about hyperparameters.

### 0.2 How real labs actually use Slack

- Daniel MacArthur's lab at the Broad Institute: **23 scientists, >400,000 messages since 2014, ~500 messages/day**, organized into channels "by task, project, or topic," used heavily for search-driven onboarding and keeping the lab-wide to-do list current ([Nature, "How scientists use Slack"](https://www.nature.com/articles/541123a)).
- Casey Greene's computational biology team (Perelman School of Medicine) uses a **Bonusly plugin** to publicly thank people who answer questions in-channel — a realistic detail that signals a highly active, computationally-fluent lab culture ([same Nature piece](https://www.nature.com/articles/541123a)).
- Labs commonly pipe **instrument/job output straight into Slack** — e.g., a dedicated channel that receives an email-to-Slack bridge from lab instruments, or (in ML-heavy groups) Slurm cluster notifications on job `BEGIN`/`END`/`FAIL` ([Slurm+Slack notification pattern](https://slack.com/blog/collaboration/setting-up-slack-for-small-teams); general HPC/Slurm-Slack integration pattern is standard in academic ML clusters, e.g. [MIT CSAIL Slurm docs](https://tig.csail.mit.edu/shared-computing/slurm/)).
- Standard channel taxonomy in academic groups: an `#announcements` channel, a general lab channel, then topic/project channels, plus soft social channels (`#food`, `#random`, `#papers`/`#journal-club`) ([Stanford Medicine Slack guidance](https://med.stanford.edu/irt/slack/slack_channel_names.html); [academic dept channel example](https://lcolladotor.github.io/2018/06/19/using-slack-for-academic-departmental-communication/)).

**Implication for the demo**: channel layout should mix (a) project/hypothesis channels, (b) an infra/compute channel with bot noise, (c) a literature/journal-club channel, (d) a wet-lab-specific channel in the hybrid world, and (e) a purely social channel — because real labs have all of these and their absence is a "tell."

### 0.3 Current (2024–2026) technical substance, by area

**(a) Protein language models (PLMs) for property/fitness prediction**
- ESM2 does zero-shot fitness prediction via masked-marginal log-odds ratios and is evaluated on **ProteinGym** (250+ deep mutational scanning assays) and **FLIP** (Fitness Landscape Inference for Proteins) ([ESM-2 background](https://www.emergentmind.com/topics/protein-language-model-esm-2); [ProteinGym, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10723403/)).
- A live, technically specific failure mode: PLM-based fitness/regression models **overfit and fail to extrapolate to higher-order mutants / larger mutational distance from the training distribution** — ProteinGym explicitly benchmarks this, and recent work shows "zero-shot methods... often fail to predict strongly epistatic multi-mutant effects" ([Investigating determinants of ML performance for protein fitness, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12278695/); [ProteinGym](https://pmc.ncbi.nlm.nih.gov/articles/PMC10723403/)).
- Low-data / few-shot fine-tuning is an active 2024–2025 topic: parameter-efficient **LoRA fine-tuning** of PLMs (e.g., Ankh-base) for **enzyme kcat (catalytic turnover) regression** in low-data regimes, and **ranking-based loss functions** (vs. plain regression loss) shown to work better in low-data settings ([Leveraging PLM embeddings for kcat prediction, arXiv](https://arxiv.org/html/2505.03066v1); [likelihood-based few-shot fitness fine-tuning, bioRxiv](https://www.biorxiv.org/content/10.1101/2024.05.28.596156v3.full)).
- **Feature dimensionality vs. overfitting**: medium-sized ESM2 variants (650M) can match larger 15B-parameter models on transfer learning while using far fewer effective embedding dimensions, and smaller embedding dimensionality reduces overfitting risk in small-dataset regimes ([efficient inference/fine-tuning of PLMs, iScience/PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12481099/)).
- **Contrastive learning** is a live direction for enzyme-function/reaction alignment — dual-encoder contrastive models that align reaction embeddings with enzyme sequence embeddings to screen libraries for novel activity ([dual-encoder contrastive learning accelerates enzyme discovery, PNAS](https://www.pnas.org/doi/10.1073/pnas.2520070123)).
- Structure-aware augmentation: designed sequences are commonly validated via **ProteinMPNN → refold with ESMFold/AlphaFold2 → self-consistency RMSD** as a designability check ([2025/2026 protein design foundation models overview](https://rewire.it/blog/protein-design-foundation-models-in-2026/)).

**(b) Antimicrobial peptide (AMP) design**
- Core design logic: AMPs work primarily via **cationic, amphipathic α-helices** that first bind anionic bacterial membranes electrostatically, then insert hydrophobic faces to disrupt the membrane (carpet, toroidal-pore, barrel-stave, aggregate mechanisms) ([amphipathic design review, ChemMedChem 2024](https://chemistry-europe.onlinelibrary.wiley.com/doi/10.1002/cmdc.202300480); [membrane damage mechanisms, Biomolecules 2025](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12292791/)).
- **2024–2025 specific finding**: "imperfectly"/controlled-disruption of amphipathicity (vs. textbook "perfect" amphipathic helices) can *increase* selectivity/cell-selectivity — a concrete, non-obvious, testable design rule ([imperfect amphipathicity for selectivity, PubMed 2024](https://pubmed.ncbi.nlm.nih.gov/39484706/)).
- Standard assay pair used to evaluate any candidate: **MIC (minimum inhibitory concentration, broth microdilution)** for potency, and **hemolysis assay (HC10/HC50 against human RBCs)** for host toxicity; the ratio (**selectivity ratio / therapeutic index**) is the actual optimization target, not raw potency ([therapeutic index / selectivity ratio definitions](https://www.science.org/doi/10.1126/sciadv.aay6817)).
- Generative modeling: **FBGAN (feedback GAN)** trains a generator against a classifier-in-the-loop; 2025 extensions add a **global quantitative activity regression module** and multifunctional-attribute prediction to push past simple binary "AMP or not" classifiers ([hybrid generative model for multifunctional AMPs, PMC 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12347886/); [DLFea4AMPGen, Nature Communications 2025](https://www.nature.com/articles/s41467-025-64378-y)).

**(c) Antibody affinity maturation / developability**
- ML-guided affinity maturation of camelid VHH domains achieved **50–70-fold affinity improvements into the picomolar range and 4–5x higher expression**, while simultaneously optimizing multiple properties — a real, cited, and impressive 2025 result to reference as "the kind of thing we're chasing" ([multidimensional VHH maturation, PMC 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12785217/)).
- **The core, well-documented tension**: affinity maturation frequently **degrades developability** — optimizing for binding correlates *inversely* with polyreactivity, hydrophobicity, and thermal stability. This is exactly the kind of "we already tried this and it backfired" hypothesis Curie should catch ([affinity-developability trade-off](https://academic.oup.com/bib/article/26/5/bbaf445/8245188)).
- Standard developability assay panel: **PSR (polyspecificity reagent binding)**, **HIC (hydrophobic interaction chromatography)**, **AC-SINS (affinity-capture self-interaction nanoparticle spectroscopy, measures self-association)** — used together as the ground truth that ML developability classifiers are trained/evaluated against ([PLM antibody developability prediction study](https://pmc.ncbi.nlm.nih.gov/articles/PMC12674332/)).
- **CDR-H3 generative design**: IgLM (infilling language model, trained on ~558M chains) generates diverse CDR-H3 libraries with tunable diversity via sampling temperature; a live 2025–2026 concern is that generated CDR-H3s can still contain **known liability motifs** (e.g., RR dipeptide, unpaired Trp) that raise polyreactivity/clearance risk even when the sequence looks "natural" by perplexity ([IgLM, Cell Systems](https://www.cell.com/cell-systems/fulltext/S2405-4712(23)00271-5); [H3BERTa liability motif finding, 2025](https://www.biorxiv.org/content/10.1101/2025.11.03.686198v1.full.pdf)).
- Real AI-native antibody companies (BigHat's Milliner platform, Absci, Generate Biomedicines) run literal **design-build-test-learn (DBTL)** loops: ML proposes sequences → high-throughput wet lab (often cell-free protein synthesis, CFPS) expresses and assays them → results retrain the model ([BigHat/Milliner DBTL description](https://www.genengnews.com/topics/artificial-intelligence/ai-created-antibodies-drive-innovation-at-bighat-biosciences/); [DBTL cycle description, Scientist.com](https://www.scientist.com/blog/accelerating-the-design-build-test-learn-cycle-for-ai-driven-antibody-discovery)).

These findings directly shaped the hypotheses below — each one is phrased so an ML-for-science reviewer would recognize the specific, falsifiable claim, the exact experiment that tests it, and why re-running it blind (without Curie) would waste a design-build-test-learn cycle.

---

## World 1 — Dry-lab protein-ML group

### Premise
A university-affiliated computational protein engineering lab that builds and benchmarks protein language models for enzyme property prediction and generative design — no wet lab of its own; it collaborates with external wet-lab partners who send back assay data on a lag, which is exactly the kind of asynchronous, easy-to-lose context Curie is built to preserve.

### Lab name
**The Ossowski Lab for Protein Representation Learning** (informally: "the Oss lab" / workspace name `ossowski-lab`) — housed in a genomics/computational biology department. (Named for a fictional PI; no real person implied.)

### Personas (5)

1. **Dr. Elena Ossowski — PI.** Trained as a structural biologist, pivoted hard into ML around 2019; still reviews every paper draft personally and is the one who says "no" to scope creep. Voice: short, direct, deadline-focused messages, often just a question mark or "status?" at 11pm before a grant deadline; rarely in the technical Slack threads day-to-day but shows up decisively when a result affects the R01 renewal story.

2. **Dr. Marcus Chen — Staff Scientist (Computational).** The lab's technical backbone; has been there 6 years, has intellectual ownership of the modeling pipeline, mentors everyone else, and is the person who actually remembers what was tried in 2024. Voice: precise, slightly pedantic, posts long threaded explanations with citations, uses "per our March analysis" unironically — exactly the human whose job Curie is meant to augment (and whose worst nightmare is being asked to re-derive that memory from scratch).

3. **Priya Raghunathan — ML/Research Engineer.** Owns the training infra, the embedding cache, the eval harness, and the Slurm cluster; not a co-author-chasing scientist, a builder. Voice: terse, all-lowercase, drops job IDs and wandb links, uses "lol" genuinely, the person who posts "job died, OOM again, bumping batch size down."

4. **Sam Okafor — 4th-year PhD student.** Owns the enzyme-activity regression project end to end; anxious about a paper deadline, posts hypotheses as questions, over-explains negative results out of a fear of looking like they wasted compute. Voice: hedging, lots of "I think," "does this seem right to anyone," genuinely excited when something works.

5. **Dr. Wei-Ling Tan — Postdoc.** Came from a wet-lab enzymology background before switching to computation, so acts as the translator between the lab's models and its external experimental collaborators (a synthetic biology company that runs the actual kcat/kM assays). Voice: calm, practical, the one who says "let's just check what the assay error bars actually are before we chase a 0.02 Spearman improvement."

### Research arc (9 months, roughly aligned to the demo's implied timeline)

- **Month 1–2 — Baselines.** Stand up ESM2-650M zero-shot and linear-probe baselines on the lab's internal enzyme-activity dataset (a curated set of ~40 engineered variants of a industrial esterase, with wet-lab kcat/kM from the external partner) and validate against public benchmarks (ProteinGym, FLIP) to make sure the pipeline isn't broken before trusting it on real data.
- **Month 2–3 — H1 launched.** Sam proposes curriculum ordering (easy→hard by mutational distance) to stabilize few-shot fine-tuning; first pass looks promising on a held-out random split.
- **Month 3–4 — Reality check.** Wei-Ling flags that the "promising" H1 result doesn't hold on a *positional* (contiguous) split — classic overfitting-to-mutation-distribution failure mode from the literature. Team spends 3 weeks chasing this before Marcus traces it to leakage between train/val folds.
- **Month 4–5 — H2 launched.** Priya builds LoRA fine-tuning infra; Marcus proposes ranking loss vs. MSE regression loss for the low-data kcat regression task, motivated directly by 2025 literature on low-data PLM fine-tuning.
- **Month 5–6 — External data lands.** The wet-lab partner sends back a second, larger batch of variants (~120) — this is the moment a "did we already test this" query becomes valuable, because the new batch overlaps in mutation space with an earlier internal pilot nobody but Marcus fully remembers.
- **Month 6–7 — H3 launched, contrastive embeddings.** Motivated by 2025 dual-encoder contrastive work, the team tries aligning sequence embeddings with a reaction/substrate representation to improve extrapolation to novel substrates.
- **Month 7–8 — Near-miss repeat.** Sam, working from an old branch, independently re-proposes almost exactly the curriculum-ordering idea from Month 2 as a "new" fix for a stalled H3 training run — not realizing it's the same failure mode Wei-Ling already diagnosed. This is the central "Curie would have caught this" moment.
- **Month 8–9 — Paper push.** Consolidate H2 (ranking loss) as the shipped result, H1 as a documented negative result (curriculum ordering doesn't help once split leakage is fixed — a useful negative result for the paper's ablations), H3 as an open/ongoing direction with a promising but not-yet-significant early signal.

### Slack channel layout

| Channel | Purpose |
|---|---|
| `#announcements` | Lab-wide, PI-driven: deadlines, meeting changes, paper acceptances. |
| `#general` | Default landing channel, low-signal. |
| `#enzyme-activity-proj` | The active project: enzyme kcat/kM regression — this is where most tracked-hypothesis traffic lives. |
| `#embeddings-infra` | Priya's domain: training infra, Slurm job bot notifications (`BEGIN`/`END`/`FAIL`), wandb run links, embedding cache status. |
| `#papers` | Journal club / "did anyone see this preprint" — high literature-citation density, good source of "why we tried X" context. |
| `#external-wetlab-partner` | Shared/Connect channel with the assay partner; slower cadence, higher formality, data drops happen here. |
| `#random` | Social; low but nonzero volume (coffee, conference travel, lab dog). |
| `#curie-alerts` *(product surface)* | Where @Prior posts collision warnings and digest summaries. |

### Tracked Hypotheses

**H1 — "Curriculum ordering (easy→hard by mutational distance from wild-type) improves convergence and final Spearman correlation when fine-tuning ESM2-650M for few-shot enzyme-activity (kcat) regression, compared to random-order fine-tuning."**
- *Motivation:* Low-data PLM fine-tuning is known to be unstable and prone to overfitting on the training mutation distribution ([likelihood-based few-shot fine-tuning](https://www.biorxiv.org/content/10.1101/2024.05.28.596156v3.full); [ProteinGym extrapolation results](https://pmc.ncbi.nlm.nih.gov/articles/PMC10723403/)).
- *Experiment:* Fine-tune ESM2-650M with LoRA on the ~40-variant internal dataset, comparing curriculum-ordered vs. randomly-shuffled mini-batches, evaluated with **both** a random split and a positional/contiguous split (per ProteinGym's cross-validation scheme) to separate genuine generalization from split leakage.
- *Outcome:* **Initially "supported"** on the random split (+0.06 Spearman) — **then refuted** once evaluated on the positional split, where the gain vanishes and the curriculum-ordered model is *statistically indistinguishable* from random ordering. Root cause: curriculum ordering by mutational distance correlates with the random split's train/val boundary, creating leakage, not a genuine curriculum-learning effect.
- *Failure mode a "we already tried this" warning prevents:* Exactly the Month 7–8 scenario above — a team member re-derives the same idea from a stale branch, burns a week of GPU time and a sprint of attention re-litigating a question that was already closed with a clear negative result, because the negative result and its root cause (split leakage, not a real effect) lived only in a Slack thread and Marcus's memory.

**H2 — "A pairwise ranking loss (margin-based, à la RankNet) outperforms plain MSE regression loss for fine-tuning PLM embeddings to predict kcat in the low-data regime (n < 150 labeled variants)."**
- *Motivation:* Directly from 2025 literature recommending ranking-based losses over regression losses in low-data PLM fine-tuning ([Ankh-base LoRA kcat regression, arXiv](https://arxiv.org/html/2505.03066v1)).
- *Experiment:* Same ~40-variant dataset plus the Month 5–6 external batch (~120 additional variants) once it arrives; compare 5-fold CV Spearman correlation for MSE-loss vs. ranking-loss fine-tuning heads on frozen vs. LoRA-adapted ESM2 embeddings, holding architecture and compute budget fixed.
- *Outcome:* **Supported.** Ranking loss gives a consistent, moderate improvement (+0.09 Spearman at n=40, narrowing to +0.03 at n=160 as more data arrives) — the team adopts it as the default fine-tuning objective and it becomes the paper's shipped method.
- *Failure mode a warning prevents:* Once H2 is settled, a natural but wasteful next move is to "double-check" by re-running the exact same MSE-vs-ranking comparison from scratch on every new data drop instead of just confirming the ranking-loss model calibrates well on the new points — Curie flags that this specific comparison has already been run and answered, redirecting effort to calibration-checking instead of re-litigating the loss function choice.

**H3 — "Aligning ESM2 sequence embeddings with a substrate/reaction embedding via a contrastive (dual-encoder) objective improves extrapolation to enzyme variants tested against *novel* substrates not seen during fine-tuning, compared to sequence-only embeddings."**
- *Motivation:* 2025 dual-encoder contrastive learning work for enzyme–reaction association, applied here to the substrate-extrapolation problem rather than enzyme retrieval ([dual-encoder contrastive learning accelerates enzyme discovery, PNAS](https://www.pnas.org/doi/10.1073/pnas.2520070123)).
- *Experiment:* Hold out one of the three substrates in the external dataset entirely from contrastive pretraining; train the dual-encoder on the other two; evaluate zero-shot Spearman correlation on the held-out substrate's activity data, compared against a sequence-only fine-tuned baseline (the H2 model).
- *Outcome:* **Open.** Early signal is promising (+0.11 Spearman over the H2 baseline on the held-out substrate) but the effect is within noise given only 3 substrates total to cross-validate over — the team flags this explicitly as "encouraging but not yet a real result" pending a 4th substrate's data, expected after the demo's timeframe.
- *Failure mode a warning prevents:* Because H3 is explicitly open/unresolved, the risk isn't a repeat — it's someone quietly treating the +0.11 as settled and citing it in the paper draft before the 4th substrate confirms it. Curie's value here is a different but related pattern: flagging that a claim is being asserted with more confidence than its evidence currently supports, based on the hypothesis's tracked status.

---

## World 2 — Hybrid wet+dry antimicrobial-peptide discovery lab

### Premise
A biotech-style translational lab running a real design-build-test-learn loop for antimicrobial peptides against drug-resistant Gram-negative bacteria — small enough that everyone is in the same Slack, but split cleanly between people who write model code and people who run MIC plates, which is exactly the two-culture gap where undocumented tribal knowledge (and repeated failed peptide designs) goes to die.

### Lab name
**Fleming Bay Therapeutics** (nod to Alexander Fleming; internal workspace `flemingbay`, self-consciously informal internally — people call it "the Bay").

### Personas (5)

1. **Dr. Aisha Okonkwo-Reyes — PI / CSO.** Ex-pharma (spent 8 years at a large biotech before founding this), obsessed with therapeutic index, not potency alone — repeatedly reminds the team that "a peptide that kills the bug and the patient is not a drug." Voice: sharp, business-and-science bilingual, posts "what's our TI on this" as almost a verbal tic; shows up in Slack for milestone reviews and investor-update pressure.

2. **Dr. Rana Al-Sayed — Staff Scientist, Computational.** Runs the generative modeling pipeline and owns the ML side of the DBTL loop; the person who actually remembers which peptide scaffolds have already been tried and failed. Voice: methodical, cites therapeutic-index numbers from memory, the lab's de facto "institutional memory" before Curie existed — making her simultaneously the best-positioned person to appreciate Curie and the person most exhausted by manually being the memory.

3. **Devon Marsh — Wet-Lab Scientist (Microbiology).** Runs MIC broth microdilution assays and hemolysis assays on every candidate batch; has zero interest in the model internals, cares about assay reproducibility and plate-to-plate variance. Voice: plainspoken, slightly skeptical of "the algorithm's" picks, posts assay results as clean tables, the person who says "MIC came back weird, rerunning before anyone gets excited."

4. **Jun-ho Park — ML Engineer.** Builds and trains the generative model (a FBGAN-style setup) and the developability/hemolysis classifiers; owns the compute pipeline and the "which candidates go to synthesis" ranking queue. Voice: enthusiastic, sometimes over-promises ("this batch looks incredible") before Devon's assay data comes back and tempers it — a believable and slightly comic recurring dynamic.

5. **Dr. Naledi Mokoena — Postdoc, Peptide Chemistry.** Bridges design and synthesis; flags when a computationally "great" sequence is a nightmare to actually synthesize (e.g., aggregation-prone during solid-phase synthesis) — a real-world constraint models routinely ignore. Voice: precise, occasionally exasperated ("great Spearman correlation, terrible to synthesize"), the reality-check on pure in-silico enthusiasm.

### Research arc (9 months)

- **Month 1–2 — Platform stand-up.** Rana and Jun-ho get the FBGAN-style generator running against a classifier trained on public AMP databases (DBAASP/DRAMP-style data); Devon validates the MIC/hemolysis assay pipeline against known reference peptides (e.g., magainin, LL-37 fragments) to establish baseline assay noise.
- **Month 2–3 — H1 launched, first design round.** First round of 24 generated candidates synthesized and tested; Naledi flags 6 of 24 as synthesis-problematic before they even reach Devon's bench.
- **Month 3–4 — Early disappointment.** Round 1 MIC data comes back mediocre; several "high-confidence" model picks turn out non-potent. Team debates whether the classifier or the generator is the problem.
- **Month 4–5 — H2 launched, therapeutic index becomes the target.** Aisha pushes the team to stop optimizing raw potency and explicitly optimize the *selectivity ratio* (hemolysis vs. MIC) — motivated by the field's known potency/toxicity trade-off. Jun-ho retrains the classifier as a **multi-task** model predicting both MIC and HC10.
- **Month 5–6 — H3 launched, amphipathicity design rule.** Rana proposes testing the 2024–2025 "imperfect amphipathicity" finding directly — deliberately disrupting the perfect helical wheel pattern in a subset of generated candidates to test whether it improves selectivity, as reported in recent literature.
- **Month 6–7 — Near-repeat incident.** A new contractor/rotating student, unaware of Month 3–4's Round 1 post-mortem, proposes re-running the *exact same* "just crank up cationic residue count to boost potency" strategy that Round 1 already showed increases hemolysis faster than it increases potency — almost exactly the failure Curie is designed to catch, because the Round 1 conclusion lived in a two-week-old thread nobody resurfaced.
- **Month 7–8 — H4 launched, structure-conditioned scaffold reuse.** Team pivots part of the pipeline to grafting successful amphipathic motifs from validated Round-2 hits onto new scaffolds, rather than generating fully de novo, after de novo generation plateaus.
- **Month 8–9 — Lead selection.** Two candidates from the H2/H3 combined approach clear a pre-set therapeutic index bar and move toward in vivo mouse infection model discussions (explicitly *not* run yet — future work) — a believable, non-overclaiming endpoint for a 9-month arc.

### Slack channel layout

| Channel | Purpose |
|---|---|
| `#announcements` | Lab-wide, PI/Aisha driven: milestones, investor updates, safety notices. |
| `#general` | Default landing channel. |
| `#amp-design-round` | The core project channel: generative model proposals, ranked candidate lists — high hypothesis-tracking traffic. |
| `#wet-lab-assays` | Devon's domain: MIC/hemolysis results, plate photos, "assay came back weird, rerunning" posts. |
| `#ml-pipeline` | Jun-ho/Rana's domain: model training runs, classifier retraining, compute job bot notifications. |
| `#synthesis-chem` | Naledi's domain: peptide synthesizability flags, solid-phase synthesis issues, purity/aggregation notes. |
| `#papers` | Literature discussion — where the "imperfect amphipathicity" paper gets shared and debated before H3 launches. |
| `#random` | Social; lab lunch, conference travel. |
| `#curie-alerts` *(product surface)* | Where @Prior posts collision warnings and digest summaries. |

### Tracked Hypotheses

**H1 — "Increasing net cationic charge (from +4 to +7) on the α-helical scaffold family increases antimicrobial potency (lower MIC) against *E. coli* and *P. aeruginosa* without a proportional increase in hemolytic activity (HC10)."**
- *Motivation:* Cationic charge drives initial electrostatic binding to anionic bacterial membranes, the textbook first step of AMP mechanism ([amphipathic AMP design review](https://chemistry-europe.onlinelibrary.wiley.com/doi/10.1002/cmdc.202300480)).
- *Experiment:* Synthesize a charge-ladder series (+4, +5, +6, +7) holding hydrophobicity and helicity roughly constant; run MIC broth microdilution against *E. coli* and *P. aeruginosa* reference strains and a human RBC hemolysis assay (HC10) on each variant.
- *Outcome:* **Refuted (partially).** MIC does improve modestly from +4→+6, but hemolysis increases *faster* than potency from +6→+7 — net selectivity ratio peaks at +5/+6 and then drops sharply, i.e., "more cationic" is not simply "better." This matches the known potency-toxicity trade-off in the field.
- *Failure mode a "we already tried this" warning prevents:* Precisely the Month 6–7 near-repeat: a team member unaware of this result re-proposes "just increase charge further" as a fix for a stalled round, which would burn a synthesis-and-assay cycle (real dollars and ~2 weeks) re-discovering a result that's already on record, with the exact charge/selectivity curve already characterized.

**H2 — "Multi-task classifier training (jointly predicting MIC and HC10 hemolysis, rather than a single binary 'AMP/non-AMP' classifier) improves the *generator's* ability to propose candidates with high selectivity ratio (HC10/MIC), not just high raw potency."**
- *Motivation:* The field's generative AMP models have historically optimized simple activity classifiers; 2025 work explicitly extends FBGAN-style pipelines with quantitative multi-attribute prediction modules instead of binary classifiers ([hybrid generative model for multifunctional AMPs, PMC 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12347886/)).
- *Experiment:* Retrain the classifier-in-the-loop as a multi-task regressor (MIC, HC10) instead of a binary AMP classifier; regenerate a matched-size candidate batch under the new reward signal; synthesize and assay a random sample of the top-ranked candidates from both the old and new generator, blinded to Devon during assay so plate-reading isn't biased.
- *Outcome:* **Supported.** The multi-task-guided batch has a significantly higher median selectivity ratio (2.3x improvement) than the binary-classifier batch at matched potency, becoming the lab's new default generation objective.
- *Failure mode a warning prevents:* After H2 is adopted as the default, someone proposes "let's also try the old binary classifier again, just to double check it's really worse" using a full synthesis batch — Curie flags that this A/B comparison already ran with a clear, statistically supported result, saving a redundant $[synthesis+assay] cycle; if a re-check is warranted it should be a smaller confirmatory batch, not a full repeat.

**H3 — "Deliberately disrupting perfect amphipathicity (introducing 1–2 'face-crossing' hydrophobic residues into the polar face of the helical wheel) improves cell selectivity (lower hemolysis at matched MIC) compared to idealized amphipathic designs, consistent with recent literature on imperfect amphipathicity."**
- *Motivation:* Directly tests a specific, counter-intuitive, recently published finding — that textbook "perfect" amphipathic helix design is not optimal for selectivity ([imperfect amphipathicity for enhanced selectivity, PubMed 2024](https://pubmed.ncbi.nlm.nih.gov/39484706/)).
- *Experiment:* Take a set of validated Round 2 amphipathic hits (from H1/H2) as scaffolds; generate matched pairs — one idealized-amphipathic variant, one with controlled hydrophobic-face disruption — holding charge and length constant; assay both for MIC and HC10.
- *Outcome:* **Supported, but narrower than the literature suggested.** The selectivity improvement replicates for the *P. aeruginosa*-active scaffold family but not for the *E. coli*-active family, where disruption just reduces potency without a compensating selectivity gain — a real, reportable nuance (effect is scaffold-family-dependent, not universal).
- *Failure mode a "we already tried this" warning prevents:* The dangerous mistake here isn't repeating the whole experiment — it's someone generalizing the *E. coli* null result to conclude "imperfect amphipathicity doesn't work for us" and abandoning the approach lab-wide, when the tracked, scaffold-family-qualified result is more precise than that. Curie surfaces the *actual* qualified finding (works for one scaffold family, not the other) instead of letting a coarser, wrong memory ("we tried that, didn't work") propagate.

**H4 — "Grafting the validated amphipathic hydrophobic-face motif from the lab's best Round 2/3 hit onto a new, unrelated scaffold backbone preserves potency and selectivity better than generating a fully de novo sequence with the same target charge/hydrophobicity profile."**
- *Motivation:* Mirrors a real, pragmatic move biotech AMP/antibody pipelines make once de novo generation plateaus — reuse a validated "warhead"/motif on new scaffolds rather than pure de novo search, analogous to CDR-grafting logic in antibody design ([DBTL cycle description, general pattern](https://www.scientist.com/blog/accelerating-the-design-build-test-learn-cycle-for-ai-driven-antibody-discovery)).
- *Experiment:* Take the top motif from the best H3 hit; graft it onto three structurally distinct scaffold backbones (varying length and loop content); generate three matched de novo controls with the same target charge/hydrophobicity/length; synthesize and assay all six, comparing MIC and selectivity ratio.
- *Outcome:* **Open.** Two of three grafted variants outperform their de novo-matched controls; the third grafted variant is *worse* than its de novo control, and Naledi separately flags synthesis difficulty (aggregation during solid-phase synthesis) on that same variant — confounding whether the potency loss is a genuine biological effect or a synthesis/purity artifact. Team explicitly marks this open pending a repeat synthesis with an improved purification protocol.
- *Failure mode a "we already tried this" warning prevents:* Because this is marked open with a specific *confound* (possible synthesis artifact, not necessarily a real biological negative result), the risk is someone citing "grafting didn't work for scaffold C" as a clean negative result in a future design decision — Curie's value is preserving the *nuance* (open, confounded by synthesis quality, re-test planned) rather than letting it calcify into a wrong "already tried, failed" data point that blocks a future legitimate attempt.

---

## Recommendation

**World 2 (Fleming Bay Therapeutics)** is the stronger demo choice for a research-engineer client who wants credibility with an ML-for-science audience, for three reasons:

1. **The wet/dry split is exactly where "we already tried this" bugs actually live in real translational labs** — a synthesis-and-assay cycle costs real time and money, so a false "clear to proceed" verdict (Curie's most dangerous failure mode per the project's own calibration rules) has visible, dramatic stakes: money and weeks, not just GPU-hours.
2. **The hypotheses are checkable against a physically real assay (MIC/hemolysis)**, which makes "supported / refuted / open" verdicts easy for a non-specialist judge to follow while still being technically precise enough (selectivity ratio, scaffold-family-dependent effects, synthesis confounds) to satisfy an ML-for-science reviewer.
3. **The near-repeat scenarios are more visceral**: "someone about to re-run a synthesis batch that already failed" reads as higher-stakes than "someone about to re-run a training job" — better demo drama.

**World 1 (Ossowski Lab)** is the safer, lower-production-complexity fallback if the demo needs to stay purely computational (e.g., simpler to narrate without introducing wet-lab vocabulary to judges), and its H1 (curriculum-ordering split-leakage story) is a genuinely elegant, self-contained "gotcha" that doesn't require any biology background to appreciate — it's a pure ML methodology trap, which may land better if the judging panel skews more toward Slack-platform judges than domain scientists.

Either world satisfies the specificity bar the client is asking for: named personas with real role asymmetry, hypotheses phrased with the technical precision of an actual ProteinGym/AMP/antibody-developability paper, and failure modes that are grounded in real, cited 2024–2026 findings rather than generic "the model didn't work" hand-waving.

---

## Sources

**Team structure & lab operations**
- [NIH Staff Scientist position description](https://hr.nih.gov/careers/open-positions/job-27e8fcff-dcfe-48f8-8d8f-d8ae6cf914bf)
- [Latent Labs, Member of Technical Staff – ML for Biology](https://www.latentlabs.com/job/member-of-technical-staff-mlbiology/)
- [Role of machine and organizational structure in science, PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9371286/)
- [BigHat Biosciences overview, GEN](https://www.genengnews.com/topics/artificial-intelligence/ai-created-antibodies-drive-innovation-at-bighat-biosciences/)
- [BigHat Biosciences, CBInsights](https://www.cbinsights.com/company/bighat-biosciences)
- [Antibody design enters the AI era, Nature](https://www.nature.com/articles/d43747-024-00030-w)

**Slack usage in real labs**
- [How scientists use Slack, Nature](https://www.nature.com/articles/541123a)
- [Working Scientist podcast: Slack and lab life, Nature](https://www.nature.com/articles/d41586-019-01375-4)
- [Stanford Medicine Slack channel naming guidance](https://med.stanford.edu/irt/slack/slack_channel_names.html)
- [Using Slack for Academic Departmental Communication](https://lcolladotor.github.io/2018/06/19/using-slack-for-academic-departmental-communication/)
- [Setting up Slack for small teams](https://slack.com/blog/collaboration/setting-up-slack-for-small-teams)
- [MIT CSAIL Slurm cluster docs](https://tig.csail.mit.edu/shared-computing/slurm/)

**(a) Protein language models / fitness prediction**
- [ESM-2 Protein Language Model overview](https://www.emergentmind.com/topics/protein-language-model-esm-2)
- [ProteinGym: Large-Scale Benchmarks for Protein Design and Fitness Prediction, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10723403/)
- [Investigating the determinants of performance in ML for protein fitness prediction, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12278695/)
- [Leveraging Protein Language Model Embeddings for Catalytic Turnover Prediction of Adenylate Kinase Orthologs in a Low-Data Regime, arXiv](https://arxiv.org/html/2505.03066v1)
- [Likelihood-based Fine-tuning of Protein Language Models for Few-shot Fitness Prediction and Design, bioRxiv](https://www.biorxiv.org/content/10.1101/2024.05.28.596156v3.full)
- [Efficient inference, training, and fine-tuning of protein language models, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12481099/)
- [Dual-encoder contrastive learning accelerates enzyme discovery, PNAS](https://www.pnas.org/doi/10.1073/pnas.2520070123)
- [Protein Design Foundation Models in 2026 overview](https://rewire.it/blog/protein-design-foundation-models-in-2026/)

**(b) Antimicrobial peptide design**
- [Deep Learning for Antimicrobial Peptides: Computational Models and Databases, JCIM](https://pubs.acs.org/doi/10.1021/acs.jcim.5c00006)
- [Computational Design of Potentially Multifunctional Antimicrobial Peptide Candidates via a Hybrid Generative Model, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12347886/)
- [DLFea4AMPGen, Nature Communications 2025](https://www.nature.com/articles/s41467-025-64378-y)
- [The amphipathic design in helical antimicrobial peptides, ChemMedChem 2024](https://chemistry-europe.onlinelibrary.wiley.com/doi/10.1002/cmdc.202300480)
- [Development of α-Helical AMPs with Imperfect Amphipathicity for Superior Activity and Selectivity, PubMed](https://pubmed.ncbi.nlm.nih.gov/39484706/)
- [Insights into Membrane Damage by α-Helical and β-Sheet Peptides, PMC 2025](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12292791/)
- [Enhanced therapeutic index of an antimicrobial peptide in mice, Science Advances](https://www.science.org/doi/10.1126/sciadv.aay6817)

**(c) Antibody affinity maturation / developability**
- [Multidimensional maturation of antibody variable domains with machine-learning assistance, PMC 2025](https://pmc.ncbi.nlm.nih.gov/articles/PMC12785217/)
- [Significantly enhancing human antibody affinity via deep learning and computational biology-guided single-point mutations, Briefings in Bioinformatics](https://academic.oup.com/bib/article/26/5/bbaf445/8245188)
- [A high-throughput platform for biophysical antibody developability assessment to enable AI/ML model training, PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12674332/)
- [Application of protein language models for antibody developability prediction](https://www.researchgate.net/publication/402939806_Application_of_protein_language_models_for_antibody_developability_prediction)
- [IgLM: Infilling language modeling for antibody sequence design, Cell Systems](https://www.cell.com/cell-systems/fulltext/S2405-4712(23)00271-5)
- [H3BERTa: A CDR-H3-specific language model for antibody repertoire analysis, bioRxiv 2025](https://www.biorxiv.org/content/10.1101/2025.11.03.686198v1.full.pdf)
- [Accelerating the Design–Build–Test–Learn Cycle for AI-Driven Antibody Discovery](https://www.scientist.com/blog/accelerating-the-design-build-test-learn-cycle-for-ai-driven-antibody-discovery)
