# ELN/LIMS Data Model Research → Proposed Data Model for Curie

Research pass on how real Electronic Lab Notebooks (ELNs), Lab Information Management Systems (LIMS), and the
science-data-modeling standards they lean on structure lab memory — done to inform Curie's evolution from a flat
Slack "Lab Record List" into a schema that captures the **hypothesis → experiment → result → belief** chain while
staying implementable on Slack Lists (columns: `text`, `rich_text`, `message`, `number`, `select`/`multi_select`,
`date`, `user`, `attachment`, `checkbox`, `email`, `phone`, `channel`, `rating`, `created_by`/`last_edited_by`,
`created_time`/`last_edited_time`, `vote`, `canvas`, `reference`, `link`, plus a **one-level** parent→subtask item
hierarchy via `parent_item_id`).

---

## 1. Benchling

Benchling is the closest thing the industry has to a "reference" modern ELN/LIMS data model, and it separates
concerns cleanly into three connected systems: the **Registry** (what exists), the **Notebook** (what you did),
and **Workflows** (how work moves between people/stages). This separation — *entity vs. event vs. process* — is
the single most useful idea to borrow.

### 1.1 Registry: entities and schemas

The Registry is "a centralized system for managing and tracking samples such as plasmids, cell lines, and small
molecules... enables teams to standardize data, enforce validation rules" ([Configure Registry schemas](https://help.benchling.com/hc/en-us/articles/39935326052493-Configure-Registry-schemas)).
Key structure:

- **Schemas** define a class of thing (e.g., "Plasmid", "Cell Line", "Small Molecule"). Each schema is a set of
  **fields** — text, dropdown/select, entity-link, unit-aware number — that constrain what can be entered
  ([Configure Registry schemas](https://help.benchling.com/hc/en-us/articles/39935326052493-Configure-Registry-schemas)).
- **Fieldsets** are reusable groups of fields shared across multiple schemas, so "cell density" or "storage
  temperature" is defined once and reused, keeping schemas consistent
  ([Configure Fieldsets](https://help.benchling.com/hc/en-us/articles/34274904142605-How-to-configure-Fieldsets)).
- Every registered **entity** gets a systematic **Registry ID** (prefix + sequence number defined at the schema
  level) plus a human descriptive name — i.e., every "thing" in the lab has a stable, typed, permanent identifier
  independent of any experiment that mentions it
  ([What is the Registry?](https://help.benchling.com/hc/en-us/articles/9684259067917-What-is-the-Registry)).
- **Linked entity fields** are typed pointers: a "DNA Entity Link" field only accepts DNA-type entities, an "AA
  Entity Link" only protein-type entities, a "Custom Entity Link" only a specific custom type. Sequences
  additionally carry semantic "biointelligent links" — part links, transcription links, translation links — that
  encode *how* one registered sequence was derived from another
  ([DNA/RNA sequence overview](https://help.benchling.com/hc/en-us/articles/39110680274189-DNA-and-RNA-sequence-overview);
  [part/transcription/translation links](https://help.benchling.com/hc/en-us/articles/45181683163149-How-to-configure-and-use-part-transcription-and-translation-links)).

**Takeaway for Curie**: separate the *registry of stable things* (reagents, cell lines, constructs, people,
equipment) from the *log of events* (experiments). A "thing" should be citable and typed independent of any one
experiment; an "event" references things by typed link, not by re-typing their attributes inline.

### 1.2 Notebook: entries, Results, and Requests

- A **Notebook Entry** is the atomic unit of "what happened" — free text plus zero or more **structured tables**.
  Entries can be created blank or from admin-configured **templates** that pre-link people, sequences, other
  entries, files, and pre-place specific table types
  ([Plan experiments and collect data in the Notebook](https://help.benchling.com/hc/en-us/articles/39971013709965-Plan-experiments-and-collect-data-in-the-Notebook)).
- **Registration tables** inside an entry are how new entities get born into the Registry *from* an experimental
  context — you don't leave the entry to register a new plasmid, you fill a table row and it mints a Registry ID
  ([Learn Workflows Terminology](https://help.benchling.com/hc/en-us/articles/9684249967885-Learn-Workflows-Terminology)).
- **Result schemas** define structured **Results tables**: standardized, searchable, schema-governed capture of
  measured/assay data *inside* an entry. Submitted results are simultaneously (a) visible in the entry where they
  were recorded and (b) aggregated into a Registry-wide **Results tab**, linked back to their entity and their
  source entry — i.e., results are dual-indexed by "what was measured" and "what was measured about"
  ([Capture data with Results](https://help.benchling.com/hc/en-us/articles/39954660101773-Capture-data-with-Results);
  [Creating Result schemas and tables](https://help.benchling.com/hc/en-us/articles/9684211058957-Creating-Result-schemas-and-tables)).
  "Table Mapping" lets an upstream table's rows auto-populate a downstream Results table, so data provenance is
  structural, not copy-pasted
  ([Creating Result schemas and tables](https://help.benchling.com/hc/en-us/articles/9684211058957-Creating-Result-schemas-and-tables)).
- **Requests** are how one person asks another to run an experiment (e.g., a scientist requests a sequencing run
  from a core facility); a Request has a type-specific schema and an **execution template** that pre-populates the
  entry the fulfilling scientist will write into
  ([Create, manage, and execute legacy Requests](https://help.benchling.com/hc/en-us/articles/39948200885261-Create-manage-and-execute-legacy-Requests)).

### 1.3 Workflows: the closest thing to a hypothesis→run chain

This is Benchling's most directly relevant subsystem for Curie. A **Workflow** is "a sequence of research
processes performed to answer a research question... think of it as a pipe that helps information flow through
all the connected steps"
([Learn Workflows Terminology](https://help.benchling.com/hc/en-us/articles/9684249967885-Learn-Workflows-Terminology)).
Its vocabulary:

| Concept | Definition |
|---|---|
| **Workflow template** | Reusable, versioned, access-controlled definition of an ordered set of **stages** and how they connect |
| **Stage** | A step that modifies/analyzes an entity; defines a default entry template, required results, and who's responsible |
| **Stage run** | *One execution* of a stage — "connects all the inputs that lead to a set of outputs for a given condition." A stage can run multiple times (replicates) |
| **Input samples table** | The "inbox" for a stage run — auto-filled from the *previous* stage's outputs |
| **Output samples table** | The "outbox" — new samples or characterized inputs passed to the *next* stage |
| **Workflow dashboard / summary view** | Aggregated view of all stages, connections, current status, and critical fields extracted from structured tables across the whole chain |

Source: [Learn Workflows Terminology](https://help.benchling.com/hc/en-us/articles/9684249967885-Learn-Workflows-Terminology).

This is structurally a **directed graph of typed events** where edges are literally "output of stage N = input of
stage N+1" — the same source→process→sample graph pattern the ISA model formalizes academically (§5 below). It's
the strongest evidence that "hypothesis → experiment → follow-up experiment" should be modeled as a *chain of
runs linked input→output*, not as free-text references.

---

## 2. eLabFTW (open source — actual data model)

eLabFTW is the most useful system to study because its docs describe the literal underlying structure, not just
UI. Its two top-level entity types:

### 2.1 Experiments

An Experiment entry has ([Experiments](https://doc.elabftw.net/docs/usage/user-guide/experiments/)):

- **Title**, **Custom ID** (auto-incrementing per Category, admin-defined), **Category** (admin-defined, groups
  by project/experiment-type), **Status** (admin-customizable; defaults are `Running`, `Needs to be redone`,
  `Success`, `Fail`), **Tags** (unlimited, team-shared, cross-searchable — "think of them as folders, but more
  powerful because each entry can have many"), **Date** (editable "started on" date, separate from the immutable
  backend creation timestamp), **Permissions** (additive visibility/write ACL over a base permission), **Main
  text** (rich text/Markdown with tables, LaTeX, images), **Custom fields** (arbitrary typed metadata, can be
  grouped), **Steps** (ordered checklist of actions, each individually completable; can be locked in a template
  so they can't be edited/deleted downstream), **Linked Experiments/Resources** (unlimited, bidirectional,
  created either by `#`-mention autocomplete in text or via an explicit link picker), **Attachments** (unlimited,
  type-aware — molecule files render 2D/3D, DNA files get a sequence viewer, images get thumbnails).
- A permanent, immutable **elabid** (`20150526-e72646c3ecf59b4f72147a52707629150bca0f91` style) exists
  specifically "to reference an Experiment with an external database" — i.e., a durable citation key independent
  of title/category/anything editable.
- **Duplicate** creates a new entry with same title+tags+text+links but today's date and status reset to
  `Running`, with an "I" appended to the title — this is eLabFTW's explicit mechanism for **replicates/re-runs**.
- Two independent change-tracking systems: **Revisions** (versions of the main text body only, diffable,
  restorable) and **Changelog** (every other field change). This split matters — free-text narrative and
  structured metadata are versioned separately.

Source: [Experiments | eLabFTW Documentation](https://doc.elabftw.net/docs/usage/user-guide/experiments/).

### 2.2 Resources ("database"/items)

Resources are the *inventory* side — "similar to Experiments, but... for listing and organizing **things** used
in Experiments": antibodies, microscopes, plasmids, drugs, chemicals, equipment. Resources are grouped into
admin-defined **Resource Categories** (name + color), and each category can have multiple **Resource Templates**
(e.g., category "Antibodies" → templates "Primary Antibody" / "Secondary Antibody"). Resources can be made
**bookable** (calendar/scheduler integration) and **procurable** (reorder workflow with a request/approval state
machine). Resources link into Experiments the same `#`-mention way Experiments link to each other
([Resources](https://doc.elabftw.net/docs/usage/user-guide/resources/)).

### 2.3 Links, steps, tags — the mechanics of cross-referencing

- Links are created either inline (`#` + 3 characters of title → autocomplete → Enter) or via an explicit picker,
  and are **bidirectional and unlimited**: linking Experiment B to Resource A also makes A show "all Experiments
  that use this reagent" — the reverse-lookup is a first-class view, not a query you have to construct
  ([Linked Resources/Experiments](https://doc.elabftw.net/docs/usage/user-guide/experiments/#linked-resourcesexperiments)).
- **Import Links** and **Import Body** let a new entry (e.g., "Time travel II", a re-run of "Time travel") pull in
  all of the reagent/equipment links — and optionally the entire text — of the entry it's following up on. This
  is eLabFTW's explicit UX for "this experiment is a follow-up to that one": link first, then one-click-inherit
  its context.
- **Steps** are per-entry ordered, checkable action items; a "Next step" surfaces on the index list; steps can be
  **locked** in a template so a protocol's mandatory steps survive into every instance unedited.
- **Tags** are team-global controlled-ish vocabulary (autocomplete favors reuse) for cross-cutting classification
  orthogonal to Category/Status.

### 2.4 Traceability, audit trail, signatures, provenance (eLabFTW)

eLabFTW's [Traceability and auditability](https://doc.elabftw.net/docs/usage/traceability-and-auditability) page
is the most concrete, implementable description of "provenance" in any tool researched:

- **Trusted timestamps (RFC 3161)**: JSON-export the entry → SHA-256 hash it → send the hash to a Time Stamping
  Authority (DFN.de, Universign, Digicert, Sectigo, GlobalSign, Evidency, or custom) → TSA returns a signed token
  proving the hash existed at time T → bundle JSON + token into an **immutable** archive attached to the entry.
  Independently verifiable later with `openssl ts -verify`, no eLabFTW instance required.
- **Blockchain timestamps**: same hash, submitted to the Bloxberg Ethereum-based consortium chain instead of a
  TSA, again bundled as an immutable, independently-verifiable archive.
- **Three tiers of electronic signature**: (1) *handwritten* — literal signature block in PDF export; (2)
  *simple* — "in an authenticated system where all users are identified and vetted, a signature can be clicking a
  checkbox, leaving a comment, or performing an action such as locking an Experiment," strengthened by MFA; (3)
  *advanced cryptographic* — Ed25519 keypair per user, private key passphrase-protected, signs a hash of the
  entry's full JSON export, records a `meaning` (Review/Approval/etc.), bundles signature + public key +
  verification script into an immutable archive. Any single bit changed in the source data invalidates the
  signature.
- **Changelog vs. Revisions**, as above — two audit granularities for structured metadata vs. free text.
- **Soft delete**: deleting never actually removes a row; it flips `State` from `Normal` to `Deleted` (third state
  is `Archived`). Deleted/archived items are excluded from default search/export but remain queryable via
  advanced filters and are restorable.
- **Sysadmin-level immutable Audit Log** separately records identity/security-relevant events: `Login`, `Logout`,
  `AccountCreated/Validated/Archived/Deleted/Modified`, `PasswordChanged/ResetRequested`, `Users2TeamsModified`,
  `ApiKeyCreated/Deleted`, `ConfigModified`, `Export`, `Import`, `SignatureKeysCreated/SignatureCreated`,
  `ActionRequested`.

**Takeaway for Curie**: provenance isn't one field, it's a stack — (1) a durable citation ID, (2) a
change-log distinguishing narrative edits from metadata edits, (3) a lightweight "who approved this and what did
'approved' mean" signature primitive, (4) an explicit locked/immutable state once something is signed off, and
(5) soft-delete, never hard-delete.

---

## 3. SciNote

SciNote's structure is a strict **4-layer containment hierarchy**: **Team → Projects → Experiments → Tasks**
([SciNote sample and data management](https://www.scinote.net/sample-and-data-management-platform/)). Within that:

- **Protocols/SOPs** are versioned, independently manageable objects — "traceable from creation and optimization,
  to versioning and execution" — and are *executable*: step-by-step, checklist-by-checklist, on any device, with
  the ability to comment on individual steps and connect them to results, instruments, samples, reagents, and
  users ([Protocol & SOP Management](https://www.scinote.net/solutions-for-labs/protocol-sop-management/)).
- A dedicated **Inventory** module manages samples/reagents as records with IDs, description, storage location,
  related documents, status, and availability, centrally and separately from any one experiment
  ([Inventory Management](https://www.scinote.net/product/inventory-management/)).
- **Tasks** are the leaf unit of "an experiment" and are where samples, reagents, protocols, instruments, and
  results actually get cross-linked — full traceability is achieved by linking reagents and protocols *into*
  tasks/results, not by duplicating their data.
- The whole thing is visualized as a flow chart — projects/experiments/tasks with their links rendered as a
  literal graph, not just a table.

Source: [SciNote sample and data management](https://www.scinote.net/sample-and-data-management-platform/).

**Takeaway for Curie**: a strict container hierarchy (workspace → project → experiment → run) plus **separately
versioned protocol objects** that experiments *reference* rather than restate is a proven pattern for keeping
"the same protocol, run five times" from becoming five copies of protocol text.

---

## 4. LabArchives

LabArchives keeps the notebook metaphor closer to paper: **Notebooks → Folders → Pages**, and a page is populated
by adding typed **entries** — Rich Text, Attachment, Image Annotation (a `.jpg/.gif/.png` can be annotated
in-place), and **Widgets** (forms/templates/custom mini-programs embedded as an entry type)
([Quick Start Guide for ELN](https://www.labarchives.com/guides/quick-start-eln); [Quick Start Guide for ELN New Users](https://help.labarchives.com/hc/en-us/articles/11785744037268-Quick-Start-Guide-for-ELN-New-Users)).
**Tagging** is explicitly framed as metadata that "builds an internal vocabulary with your team and improves
search results" — the same cross-cutting classification role tags play in eLabFTW.

**Takeaway for Curie**: LabArchives' contribution is mainly about *entry typing* — the idea that a single page
(≈ a Curie experiment thread) is a sequence of typed, individually-addressable blocks (text / attachment /
annotated image / structured widget) rather than one blob. Slack's `rich_text` block/message-link columns can
play the same role for Curie.

---

## 5. Colabra and Dotmatics/LabGuru (lighter public documentation)

Both platforms have thinner public developer/data-model documentation than Benchling or eLabFTW (they're sold,
not developer-doc-forward open products), so this section is necessarily shallower, but the pattern that emerges
is consistent with the others:

- **Colabra** organizes work as **Projects** containing **Entries** in a social-feed-style interface — team
  members follow projects, comment inline on specific entries/data points (thread-per-datapoint, not one
  undifferentiated chat), and discover related work via tags and search
  ([37degrees ELN landscape 2026](https://www.37degrees.io/resources/eln-landscape-2026/)). Its differentiator is
  making the notebook *conversational* — comments are attached to a specific entry/data point, which is
  structurally close to a Slack thread attached to a Lab Record List row.
- **Dotmatics** (the platform LabGuru now sits under) is described as "schema-driven... with schema mapping so
  controlled structures remain interpretable across systems," offering configurable templates for sample/assay
  tracking with structured metadata and "audit-ready histories"
  ([Dotmatics chemicals & materials blog](https://www.dotmatics.com/blog/streamlining-data-driven-chemicals-and-materials-science-lab-experiments)).
- **LabGuru** specifically: "scientists can design experiments and workflows, capture structured and unstructured
  data, manage projects, and share their work," with customizable experiment templates and integrated
  protocols/SOPs; one third-party comparison describes it as tying "API-driven automation to stable record
  fields" via one consistent schema, with RBAC and audit logging across projects and controlled edits
  ([Top Dotmatics Alternatives, Scispot](https://www.scispot.com/blog/top-dotmatics-alternatives-and-competitors)).

**Takeaway for Curie**: both reinforce the same shape already seen — projects contain experiments, experiments
reference reusable protocol/template objects, structured fields sit alongside unstructured narrative, and
audit/RBAC is a first-class layer, not bolted on. Colabra's inline-comment-per-datapoint pattern is worth noting
specifically because Curie already lives in Slack threads — a Slack thread *is* Colabra's comment-per-entry
mechanism, for free.

---

## 6. The ISA model (Investigation–Study–Assay)

The ISA framework is the academic/standards-body answer to "what's the right shape for experimental metadata,"
maintained by the ISA Working Group (Oxford e-Research Centre and collaborators) since 2007
([ISA commons](https://www.isacommons.org/)). It is the single most directly reusable structure for Curie's
hypothesis→result chain because it was designed by people solving exactly this modeling problem, and it comes
with a precise abstract graph semantics, not just a UI hierarchy.

### 6.1 The three-tier container hierarchy

| Layer | Definition | Example |
|---|---|---|
| **Investigation** | High-level research area / project context — "may be the overall aims of the project, as stated on your grant" | *Central Carbon Metabolism of Sulfolobus solfataricus* |
| **Study** | *A particular biological hypothesis you are planning to test in various ways* — the unit that actually corresponds to a hypothesis | *Comparison of S. solfataricus grown at 70 °C and 80 °C* |
| **Assay** | A specific, individual experiment, measurement, or modeling task | *Transcriptome comparison via cDNA microarray at 70 °C and 80 °C* |

Source: [A Quick guide to using ISA in SEEK](https://docs.seek4science.org/help/isa-guide.html) (FAIRDOM-SEEK
docs; SEEK/FAIRDOMHub are the reference implementations of ISA).
An Investigation can contain multiple Studies; a Study can contain multiple Assays; multiple Assays of different
technologies (transcriptomics, proteomics, metabolomics) can all attach to the *same* Study because they're all
testing the same hypothesis from different angles — this many-Assays-per-Study structure is exactly Curie's
"one hypothesis, several experimental approaches" case.
**Crucially, "Study" in ISA is explicitly defined as the hypothesis-testing unit** — not "Investigation," not
"Assay." This directly validates modeling Curie's hypothesis as its own addressable, referenceable object that
sits *above* individual experiment runs and can have several of them underneath it.

### 6.2 The underlying graph semantics (this is the part worth stealing precisely)

Below the three named tiers, ISA's actual formal model is a **directed acyclic graph where materials and data are
nodes and protocols are edges**: "a protocol takes one or more inputs (biological material or data) and generates
one or more outputs (biological material or data). Therefore protocols correspond to edges in the experimental
graph, while materials and data correspond to the nodes"
([ISA Abstract Model spec](https://isa-specs.readthedocs.io/en/latest/isamodel.html)). Concretely:

- In a **Study**, provenance runs `Source material → [sample collection process] → Sample material` — literally:
  where the material came from, how it was collected/derived, what resulted.
- In an **Assay**, provenance continues `Sample material → [process] → [material/data] → [process] → [data] ...`
  — an arbitrarily long chain of process→output edges, e.g. sample → extraction → extract → sequencing → raw
  reads → analysis → processed result.

This node/edge framing is more precise than "hypothesis → experiment → result": it says *every step is either a
thing (node) or a transformation of things (edge)*, and a "result" is just the terminal node of a data-processing
chain that started at a sample.

### 6.3 ISA-Tab is a tab-delimited implementation; it's the model that generalizes

ISA-Tab is one serialization (there's also ISA-JSON); the format that matters is the *model* — Investigation
metadata file, Study file(s), Assay file(s), all cross-referencing by identifier
([ISA-Tab format spec](https://isa-specs.readthedocs.io/en/latest/isatab.html)). What Curie should borrow is not
the file format but the guarantee ISA is built to provide: **every Study/Assay/Sample/Data node carries enough
metadata to be independently reused or reanalyzed by someone who wasn't in the room** — which is a direct
restatement of FAIR (§8) applied specifically to the hypothesis-chain.

---

## 7. ALCOA+ data integrity and 21 CFR Part 11

These two are regulatory/compliance frameworks rather than data models per se, but they specify *what fields and
mechanisms a record-keeping system must have* to be trustworthy — directly informs which columns Curie's schema
needs even outside a regulated pharma context, because they're the closest thing science has to a checklist for
"is this record actually trustworthy."

### 7.1 ALCOA+

Originally an FDA 1990s concept, now the de facto standard referenced by FDA, WHO, MHRA, and GAMP guidance
([Pharmaguideline ALCOA overview](https://www.pharmaguideline.com/2018/12/alcoa-to-alcoa-plus-for-data-integrity.html);
[Arkivum ALCOA+](https://arkivum.com/blog/alcoa-the-cornerstone-of-data-integrity-in-life-sciences/)):

**Core ALCOA** (5 principles):
- **A**ttributable — data can be traced to the specific person who generated it
- **L**egible — permanent, clear, readable
- **C**ontemporaneous — recorded at the time it was generated (not backfilled later)
- **O**riginal — the first-recorded observation, or a verified true copy
- **A**ccurate — correct, truthful, error-free

**Extended to ALCOA+** (adds):
- **C**omplete — nothing selectively omitted
- **C**onsistent — chronologically ordered, dated, internally coherent
- **E**nduring — durable for the required retention period
- **A**vailable — retrievable/reviewable for its full lifecycle

Source: [Pharmaguideline](https://www.pharmaguideline.com/2018/12/alcoa-to-alcoa-plus-for-data-integrity.html),
[ACRP glossary](https://acrpnet.org/glossary/attributable-legible-contemporaneous-original-accurate-alcoa).

**Direct schema implication**: *Attributable* + *Contemporaneous* together mean every record needs a
**"recorded by" person field distinct from any "performed by" field**, and a system-generated (not user-editable)
timestamp separate from any user-editable "experiment date." *Original* means edits should be tracked, not
overwritten in place (append, don't mutate). *Complete* + *Consistent* argue against letting a "Clear" verdict
exist without the evidence that produced it being linked alongside it.

### 7.2 21 CFR Part 11 — electronic records and signatures

The FDA regulation establishing when an electronic record/signature is legally equivalent to paper+ink
([eCFR Part 11](https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11)). Two requirements
translate directly into schema/column decisions:

- **Audit trails (§11.10(e))**: must be "secure, computer-generated, time-stamped," must "independently record the
  date and time of operator entries and actions that create, modify, or delete electronic records," and — the
  operative constraint — **"record changes shall not obscure previously recorded information"** and must be
  tamper-evident, with *no user, including admins,* able to modify entries
  ([SimplerQMS 21 CFR Part 11 audit trail](https://simplerqms.com/21-cfr-part-11-audit-trail/);
  [Ofni Systems 21 CFR 11.10(e)](https://www.ofnisystems.com/21-cfr-11-10e-audit-trails/)). This is a strong
  argument for **append-only history**, never in-place field overwrites, at least for verdict-bearing fields.
- **Electronic signatures (§11.50, §11.70)**: three mandatory elements — **full printed name**, **date/time of
  signing**, and **meaning** (e.g., Approved / Reviewed / Authored) — and the signature must be **permanently
  bound** to the specific record version it signs, so a later edit of the record doesn't silently carry the old
  signature forward ([GoValidation Part 11 checklist](https://govalidation.com/blog/21-cfr-part-11-electronic-records-checklist/)).
  This "meaning" field — not just *who* signed but *what they meant by signing* — is a detail every tool
  researched (eLabFTW's cryptographic signature `meaning`, Part 11's `§11.50`) converges on independently, and is
  easy to drop if you only model "approved_by."

Curie is not a regulated system and doesn't need cryptographic signing, but ALCOA+ and Part 11 both point at the
same minimal viable "trustworthy record" column set: **who + when (system clock, not user-entered) + what they
asserted + did this obscure or append to prior state**. §9.4 below operationalizes this as Curie's "belief" object.

---

## 8. FAIR data principles

Published 2016, stemming from a 2014 Lorentz Workshop, propagated by the GO FAIR initiative (created by Germany's
BMBF plus the French and Dutch education ministries) ([GO FAIR principles](https://www.go-fair.org/fair-principles/);
[Columbia library FAIR overview](https://library.cumc.columbia.edu/insight/what-are-fair-data-principles)):

- **Findable** — data and metadata have a unique, persistent identifier (e.g., DOI) and sufficiently detailed
  descriptive metadata to be discovered.
- **Accessible** — retrievable via a defined, ideally open-access protocol, even if the data itself later becomes
  restricted (the *metadata record* should remain accessible even when the *data* can't be).
- **Interoperable** — uses a formal, shared, broadly-applicable representation (controlled vocabularies, typed
  fields) so machines as well as humans can combine it with other data.
- **Reusable** — sufficiently well-described (usage license, provenance, community standards) that it can be
  replicated or recombined in future work, by someone who wasn't there.

eLabFTW explicitly designs to this: it ships **RO-Crate**-based `.eln` export (a JSON-LD manifest describing an
experiment dataset), built to the interchange format defined by **The ELN Consortium**
([ELN export in Experiments docs](https://doc.elabftw.net/docs/usage/user-guide/experiments/); [The ELN Consortium](https://the.elnconsortium.org)) —
i.e., a leading open-source ELN treats "can another system read my export and understand what happened" as a
first-class design requirement, not an afterthought.

**Direct schema implication**: every experiment/hypothesis/result needs (a) a stable, permanent, unique ID
independent of title (Findable — this is exactly eLabFTW's `elabid` pattern, §2.1), (b) enough typed metadata to
be understood without reading the whole thread (Interoperable), and (c) enough linked provenance (protocol used,
person, prior hypothesis) to be trusted and reused later by someone who wasn't in the channel when it happened
(Reusable).

---

## 9. PROPOSED DATA MODEL FOR CURIE

### 9.1 Design principles, derived from the research above

1. **Separate the registry of things from the log of events from the graph of process** (Benchling's
   Registry/Notebook/Workflows split, §1). Curie should not let "what a reagent is" live only inside one
   experiment's row.
2. **The hypothesis is its own addressable object, not a column value.** ISA's "Study = the hypothesis-testing
   unit, containing multiple Assays" (§6.1) is the single most load-bearing finding here — it's the reason a flat
   experiment list can't express "these three experiments are all testing the same belief." Curie's current flat
   list conflates hypothesis and experiment into one row; that's the core gap to close.
3. **Model provenance as edges, not prose.** ISA's protocol-as-edge/material-as-node graph (§6.2) and Benchling
   Workflows' input-table/output-table chaining (§1.3) both say the same thing: "this experiment follows up on
   that one" should be a typed link with a reason, not a sentence in a Slack message that Curie has to re-parse
   every time.
4. **A result is not a verdict.** Every tool researched keeps *what was measured* (Result / Results table) distinct
   from *what someone concluded from it* (Status, Signature, Assay outcome). Curie's existing "outcome" column
   conflates these; splitting them is what makes a "Clear" verdict auditable rather than vibes.
5. **Provenance is a stack, not a field** (§2.4, §7): stable ID + append-only change history + recorded-by-person
   + system timestamp + explicit "what this action meant." Curie needs all five, cheaply, on Slack Lists.
6. **Cross-references need to be bidirectional and cheap to make.** eLabFTW's `#`-mention-to-link and
   "Import Links/Import Body" (§2.3) are the UX pattern: Curie's Prior agent should be able to propose "link this
   new experiment to hypothesis H3 and inherit its protocol" the same lightweight way, not require manual list
   surgery.
7. **Stay inside Slack Lists' real constraints.** Confirmed against the live `slackLists.create` schema
   ([Slack API reference](https://docs.slack.dev/reference/methods/slackLists.create/)): column types are `text`,
   `rich_text`, `message`, `number`, `select`, `multi_select`, `date`, `user`, `attachment`, `checkbox`, `email`,
   `phone`, `channel`, `rating`, `created_by`, `last_edited_by`, `created_time`, `last_edited_time`, `vote`,
   `canvas`, `reference`, `link` — richer than CLAUDE.md's shorthand list (it also has `rich_text`,
   `multi_select`, `reference`, `created_time`/`last_edited_time` as native, system-managed columns, which matters
   a lot for provenance, §9.4). Hierarchy is **exactly one level**: a List has a `schema` (top-level item columns)
   and a separate `subtask_schema` (child-item columns), connected via `parent_item_id` on
   `slackLists.items.create` — there is **no multi-level nesting**. This one constraint is why the model below
   uses **four separate top-level Lists linked by `reference`/`link` columns** rather than trying to nest
   Hypothesis → Experiment → Result as parent → subtask → sub-subtask, which Slack Lists cannot do.

### 9.2 Entity overview

Four top-level Slack Lists, each item citable by a stable ID, cross-linked by `reference` columns (Slack's native
"pointer to a record in another List" column type) rather than by nesting:

```
  HYPOTHESES  ───────────────┐
  (the belief; ISA "Study")  │  1
       │ 1                   │
       │  N                  │
       ▼                     │
  EXPERIMENTS  ───reference──┘   (an experiment cites the hypothesis it tests)
  (the run; ISA "Assay" +        also: follows_up_on → reference(Experiments)  [self-referential, for replicates/iterations]
   Benchling "stage run")        also: protocol → reference(Protocols)
       │ 1
       │  N
       ▼
  RESULTS  (the measurement; Benchling "Result", ISA terminal data node)
       │ N
       │  1  (an update to belief cites the results that justified it)
       ▼
  BELIEF UPDATES  (the verdict/ledger entry; the "Curie compiled this" moment)
```

Plus two supporting registries, populated lazily rather than up front:

```
  PROTOCOLS/REAGENTS registry   (Benchling Registry-style; things, not events — optional v1, can start as
                                  a `select` dropdown on Experiments and graduate to its own List later)
```

This keeps Curie's existing flat "Lab Record List" *recognizable* — Experiments is still the row-per-run table
users already know — while adding the two objects that were structurally missing: a first-class **Hypothesis**
above it, and a first-class **Result** (+ **Belief Update**) below it.

### 9.3 List 1 — `Hypotheses` (ISA "Study" analog)

The addressable belief. One row per thing the lab currently believes, is testing, or has tested.

| Column | Type | Notes |
|---|---|---|
| `hypothesis_id` | `text`, primary column | Stable citation key, eLabFTW-`elabid`-style, e.g. `H-2026-014`. Never reused, never edited. Satisfies FAIR "Findable" (§8) |
| `statement` | `rich_text` | The actual claim, e.g. "Compound X reduces biofilm formation in strain Y by >30% at 10µM." Written so it's falsifiable, not just a topic |
| `status` | `select` | `Open` / `Testing` / `Supported` / `Refuted` / `Inconclusive` / `Superseded` — mirrors eLabFTW's admin-editable Status pattern (§2.1) but scoped to belief state, not run state |
| `confidence` | `select` or `rating` | Slack's native `rating` column (emoji + max, e.g. 1–5 stars) works well here as a lightweight Bayesian-prior dial — literally the "Prior" the agent is meant to check |
| `owner` | `user` | Attributable (ALCOA+, §7.1) — whose belief/project this is |
| `origin_thread` | `message` | Slack's native column type that links directly to the message/thread where the hypothesis was first raised — preserves the conversational provenance for free |
| `parent_hypothesis` | `reference` → self (Hypotheses) | For hypothesis refinement/narrowing ("H-014 supersedes H-009") — self-referential like eLabFTW's Experiment-to-Experiment links |
| `created_time` / `last_edited_time` | `created_time` / `last_edited_time` | Slack-system-managed, non-editable — satisfies ALCOA+ "Contemporaneous" without trusting user input |
| `created_by` | `created_by` | Slack-system-managed — satisfies ALCOA+ "Attributable" at the record level, distinct from `owner` (owner can be reassigned; `created_by` cannot) |
| `tags` | `multi_select` | Free cross-cutting classification, eLabFTW/LabArchives-style (§2.3, §4) — project, pathway, compound class, etc. |
| `experiment_count` | `number` (or left as a live count surfaced by Prior, since Lists can't formula-aggregate across items) | How many Experiments cite this hypothesis — Prior can compute and write this back on each new linked experiment |
| `canvas_summary` | `canvas` | Slack's native canvas column — Prior periodically compiles/updates a running canvas doc per hypothesis: current evidence, open questions, next planned experiment. This *is* Curie's "self-writing lab memory" surface |

### 9.4 List 2 — `Experiments` (ISA "Assay" + Benchling "stage run" analog — the enriched Lab Record List)

This is the existing flat list, enriched. One row per actual run.

| Column | Type | Notes |
|---|---|---|
| `experiment_id` | `text`, primary column | Stable ID, e.g. `E-2026-0142`. Independent of title (FAIR Findable) |
| `title` | `text` | Short human label |
| `hypothesis` | `reference` → Hypotheses | **The core new link.** Every experiment must cite the belief it's testing — this is what turns the flat list into a chain. Nullable only for genuinely exploratory/pilot runs, and Prior should flag nulls for follow-up |
| `follows_up_on` | `reference` → self (Experiments) | Self-referential — replaces eLabFTW's "Import Links/Import Body" pattern (§2.3) and Benchling's stage-run input/output chaining (§1.3). Use for replicates, retries, and iterations. A `replicate_of` vs `iterates_on` distinction can be carried in `link_type` below if needed |
| `link_type` | `select` | Companion to `follows_up_on`: `replicate` / `follow_up` / `retry_after_failure` / `control_for` — makes the self-link legible instead of just "related" |
| `protocol` | `reference` → Protocols (or `select` in v1 if Protocols isn't its own List yet) | SciNote's separately-versioned-protocol pattern (§3) and Benchling's stage default-entry-template (§1.3) — the *procedure* is a reusable object an experiment points to, not retyped text |
| `status` | `select` | `Planned` / `Running` / `Needs Redo` / `Complete` — run-level status, mirrors eLabFTW defaults (§2.1) |
| `outcome` | `select` | `Supports` / `Refutes` / `Inconclusive` / `Failed (technical)` — **kept separate from `status`**: a `Complete` run can still have an `Inconclusive` outcome; a `Failed (technical)` outcome (pipette broke) is not evidence against the hypothesis and must not be scored as if it were. This split directly targets CLAUDE.md's "false collision is the unforgivable bug" calibration concern |
| `params` | `rich_text` or a small set of typed columns per lab | Existing flat-list params column, kept as-is — this is where lab-specific structured conditions live (concentration, temperature, timepoint) |
| `performed_by` | `user`, `multi_select`-capable via `user` column's multi-entity format | Who ran it — Attributable (ALCOA+). Distinct from `created_by` (who logged it in Slack, which might be Prior on someone's behalf) |
| `performed_date` | `date`, user-editable | eLabFTW's "date started on" — the *scientific* date, separate from... |
| `logged_time` | `created_time` | ...the *system* timestamp of when the row was actually created — the Contemporaneous check: a large gap between `performed_date` and `logged_time` is itself a data-quality signal Prior can flag |
| `raw_data` | `attachment` | Files, images, instrument exports — eLabFTW/LabArchives attachment pattern |
| `source_thread` | `message` | Link to the Slack thread this experiment was logged from — preserves full conversational context without duplicating it |
| `reagents_used` | `multi_select` or `reference` list → a future Reagents/Registry List | Benchling Registry-style typed pointer to *things* (§1.1) rather than free text, once the lab has enough reagents to justify a registry |
| `tags` | `multi_select` | Cross-cutting, eLabFTW-style |
| `created_by` / `created_time` / `last_edited_by` / `last_edited_time` | system columns | Full Part 11 §11.10(e)-style audit quadruple, free from Slack's native column types — no custom audit table needed |

### 9.5 List 3 — `Results` (Benchling "Results table" + ISA terminal data-node analog)

Splitting Results out from Experiments as its own List (rather than a column) matters for two reasons the
research surfaced repeatedly: (1) Benchling's Results are deliberately dual-indexed — visible in their source
entry *and* aggregated Registry-wide (§1.2) — which a separate, `reference`-linked List gives you natively via
Slack's list views/filters; (2) one experiment run can produce multiple discrete measurements (multiple timepoints,
multiple replicate wells, multiple assay readouts), which a single-row-per-experiment model can't hold cleanly.

| Column | Type | Notes |
|---|---|---|
| `result_id` | `text`, primary column | Stable ID, e.g. `R-2026-0301` |
| `experiment` | `reference` → Experiments | Required — every result must trace to the run that produced it (ISA: data nodes always have an upstream process edge) |
| `measurement` | `text` or `number` | The actual value(s). If genuinely tabular/multi-metric, use `attachment` for a CSV/image and keep this as a one-line summary |
| `unit` | `text` (or `select` from a controlled unit list) | Benchling's "unit-aware number" fields (§1.1) — even a simple controlled-vocabulary `select` beats free text for later cross-experiment comparison |
| `interpretation_note` | `rich_text` | Analyst's read of the number — kept distinct from the number itself (ALCOA+ Original: don't let interpretation overwrite the raw observation) |
| `recorded_by` | `user` | Attributable |
| `recorded_time` | `created_time` | Contemporaneous, system-managed |
| `raw_file` | `attachment` | Instrument export, image, etc. |
| `qc_flag` | `checkbox` or `select` (`Pass`/`Flag`/`Exclude`) | Cheap outlier/QC marker so a flagged result doesn't silently feed a verdict |

### 9.6 List 4 — `Belief Updates` (the ledger — 21 CFR Part 11 signature analog + ALCOA+ append-only)

This is the object that makes Curie's memory *self-writing* rather than just a bigger table: an explicit,
append-only record of "the lab's belief about Hypothesis H changed, here's why, here's who said so." It is the
direct implementation of §7.2's "signature = name + timestamp + meaning, permanently bound to the record version
it signs" — minus any cryptography, since Curie doesn't need Part 11 compliance, just its *shape*.

| Column | Type | Notes |
|---|---|---|
| `update_id` | `text`, primary column | e.g. `U-2026-0057` |
| `hypothesis` | `reference` → Hypotheses | Which belief this update applies to |
| `new_status` | `select` | Mirrors Hypotheses.`status` options — what the belief became |
| `based_on_results` | `reference` (multi) → Results | **The evidence chain.** Every belief change must cite the specific Result rows that justified it — this is the field that turns "Clear" from a vibe into an auditable claim, directly answering ALCOA+ Complete/Consistent (§7.1) |
| `asserted_by` | `user` | Who is making this call — could be a human overriding Prior, or logged as Prior itself if fully automated |
| `meaning` | `select` | `Prior's read` / `Human-reviewed` / `Human-overridden` / `Escalated` — directly mirrors 21 CFR 11.50's mandatory "meaning" element (§7.2) and eLabFTW's signature `meaning` field (Review/Approval/etc., §2.4) |
| `rationale` | `rich_text` | Free-text "why" — the compiled-by-Curie narrative |
| `superseded_by` | `reference` → self (Belief Updates) | Append-only chain: never edit an old belief update in place, write a new one and point back. Directly implements Part 11's "changes shall not obscure previously recorded information" (§7.2) and ALCOA "Original" |
| `created_time` / `created_by` | system columns | Immutable record of when/by-whom this entry itself was written, independent of `asserted_by` |

### 9.7 Optional List 5 — `Protocols` (Benchling Registry / SciNote SOP analog; add when reuse pressure appears)

Not needed for v1 if the lab has few distinct protocols (a `select` dropdown on Experiments is enough), but worth
specifying now since CLAUDE.md's Slack Lists support `canvas` columns well-suited to this:

| Column | Type | Notes |
|---|---|---|
| `protocol_id` | `text`, primary | e.g. `P-003` |
| `name` | `text` | |
| `version` | `number` | SciNote-style protocol versioning (§3) — bump on any procedural change |
| `steps_canvas` | `canvas` | The actual step-by-step procedure, editable as a living canvas — eLabFTW's lockable "Steps" (§2.3) done as a canvas instead of a checklist, since canvases support richer formatting |
| `locked` | `checkbox` | Once a protocol has experiments run against it, lock it (eLabFTW pattern, §2.3) — future changes create a new `version` row instead of mutating this one, preserving what each historical experiment actually followed |
| `superseded_by` | `reference` → self | Same append-only-version chain pattern as Belief Updates |

### 9.8 How this answers the brief's specific chain

`Hypothesis (Hypotheses.statement)` →
`Protocol (Experiments.protocol)` →
`Experiment/Run (Experiments row, one per Benchling "stage run" / ISA "Assay")` →
`Sample/conditions (Experiments.params)` →
`Result (Results rows, N per experiment)` →
`Conclusion (Belief Updates row, citing Results.result_id via based_on_results, changing Hypotheses.status)`

— every arrow above is a `reference` column, not prose, so Prior can walk the graph programmatically (list all
Results for a Hypothesis by following Hypotheses ← Experiments ← Results) exactly the way ISA's process-edge graph
(§6.2) or Benchling's Workflow stage-chain (§1.3) are walked. Cross-experiment links (replicates, follow-ups) are
`Experiments.follows_up_on` self-references, directly modeled on eLabFTW's bidirectional Experiment↔Experiment
links and "Import Links" follow-up pattern (§2.3).

### 9.9 What's deliberately left out of v1, and why

- **No cryptographic signatures / RFC 3161 timestamping.** eLabFTW's Ed25519/TSA machinery (§2.4) is built for
  regulatory defensibility Curie doesn't need; `created_time`/`created_by` system columns plus the append-only
  `Belief Updates` ledger get ALCOA+'s Attributable/Contemporaneous/Original properties without any of that
  infrastructure.
- **No multi-level nesting** (e.g., Sample as a child of Experiment as a child of Hypothesis). Confirmed Slack
  Lists only support one parent→subtask level (`schema` + `subtask_schema`, §9.1) — modeling a full ISA
  Investigation→Study→Assay→Sample→Data depth would require nesting Slack Lists don't have. Four flat, cross-
  referenced Lists sidesteps this cleanly and is arguably easier for a human to browse in the Slack UI anyway.
- **Reagent/entity Registry (§9.7's sibling) deferred.** Benchling's typed Registry (§1.1) is the biggest single
  modeling investment researched and is overkill until a lab has enough recurring reagents/constructs that
  `multi_select` free text on Experiments.reagents_used starts causing real duplication/typo pain.
- **No Investigation-level container above Hypotheses.** ISA's top "Investigation" tier (§6.1) maps to "the whole
  research program," which for Curie is better served by the Slack **channel** itself (a channel already
  functions as the project-level container) than by a fifth List — avoids modeling a container Slack already
  gives you for free.

---

## Sources

- [Configure Registry schemas – Benchling](https://help.benchling.com/hc/en-us/articles/39935326052493-Configure-Registry-schemas)
- [Create and manage entities with the Registry – Benchling](https://help.benchling.com/hc/en-us/articles/39953982240397-Create-and-manage-entities-with-the-Registry)
- [What is the Registry? – Benchling](https://help.benchling.com/hc/en-us/articles/9684259067917-What-is-the-Registry)
- [How to configure Fieldsets – Benchling](https://help.benchling.com/hc/en-us/articles/34274904142605-How-to-configure-Fieldsets)
- [DNA and RNA sequence overview – Benchling](https://help.benchling.com/hc/en-us/articles/39110680274189-DNA-and-RNA-sequence-overview)
- [How to configure and use part, transcription, and translation links – Benchling](https://help.benchling.com/hc/en-us/articles/45181683163149-How-to-configure-and-use-part-transcription-and-translation-links)
- [Plan experiments and collect data in the Notebook – Benchling](https://help.benchling.com/hc/en-us/articles/39971013709965-Plan-experiments-and-collect-data-in-the-Notebook)
- [Capture data with Results – Benchling](https://help.benchling.com/hc/en-us/articles/39954660101773-Capture-data-with-Results)
- [Creating Result schemas and tables – Benchling](https://help.benchling.com/hc/en-us/articles/9684211058957-Creating-Result-schemas-and-tables)
- [Create, manage, and execute legacy Requests – Benchling](https://help.benchling.com/hc/en-us/articles/39948200885261-Create-manage-and-execute-legacy-Requests)
- [Learn Workflows Terminology – Benchling](https://help.benchling.com/hc/en-us/articles/9684249967885-Learn-Workflows-Terminology)
- [Experiments | eLabFTW Documentation](https://doc.elabftw.net/docs/usage/user-guide/experiments/)
- [Resources | eLabFTW Documentation](https://doc.elabftw.net/docs/usage/user-guide/resources/)
- [Traceability and auditability | eLabFTW Documentation](https://doc.elabftw.net/docs/usage/traceability-and-auditability)
- [Metadata and Custom Fields | elabftw DeepWiki](https://deepwiki.com/elabftw/elabftw/3.3-metadata-and-custom-fields)
- [The ELN Consortium](https://the.elnconsortium.org)
- [SciNote sample and data management platform](https://www.scinote.net/sample-and-data-management-platform/)
- [SciNote Inventory Management](https://www.scinote.net/product/inventory-management/)
- [SciNote Protocol & SOP Management](https://www.scinote.net/solutions-for-labs/protocol-sop-management/)
- [Quick Start Guide for ELN – LabArchives](https://www.labarchives.com/guides/quick-start-eln)
- [Quick Start Guide for ELN New Users – LabArchives](https://help.labarchives.com/hc/en-us/articles/11785744037268-Quick-Start-Guide-for-ELN-New-Users)
- [37degrees: Electronic lab notebooks in 2026](https://www.37degrees.io/resources/eln-landscape-2026/)
- [Dotmatics: Streamlining Data-Driven Chemicals and Materials Science Lab Experiments](https://www.dotmatics.com/blog/streamlining-data-driven-chemicals-and-materials-science-lab-experiments)
- [Scispot: Top Dotmatics Alternatives & Competitors](https://www.scispot.com/blog/top-dotmatics-alternatives-and-competitors)
- [ISA commons](https://www.isacommons.org/)
- [A Quick guide to using ISA in SEEK | FAIRDOM-SEEK Documentation](https://docs.seek4science.org/help/isa-guide.html)
- [ISA Abstract Model — ISA Model and Serialization Specifications](https://isa-specs.readthedocs.io/en/latest/isamodel.html)
- [ISA-Tab format — ISA Model and Serialization Specifications](https://isa-specs.readthedocs.io/en/latest/isatab.html)
- [ALCOA, ALCOA+ and ALCOA++ Principles | Pharmaguideline](https://www.pharmaguideline.com/2018/12/alcoa-to-alcoa-plus-for-data-integrity.html)
- [ALCOA+ Principles: Data Integrity in Life Sciences | Arkivum](https://arkivum.com/blog/alcoa-the-cornerstone-of-data-integrity-in-life-sciences/)
- [Attributable, Legible, Contemporaneous, Original, Accurate (ALCOA) – ACRP](https://acrpnet.org/glossary/attributable-legible-contemporaneous-original-accurate-alcoa)
- [eCFR :: 21 CFR Part 11 – Electronic Records; Electronic Signatures](https://www.ecfr.gov/current/title-21/chapter-I/subchapter-A/part-11)
- [FDA 21 CFR Part 11 Audit Trails: Definition, Requirements, and Compliance | SimplerQMS](https://simplerqms.com/21-cfr-part-11-audit-trail/)
- [21 CFR 11.10(e): Audit Trails | Ofni Systems](https://www.ofnisystems.com/21-cfr-11-10e-audit-trails/)
- [21 CFR Part 11 Compliance Checklist 2026 | GoValidation](https://govalidation.com/blog/21-cfr-part-11-electronic-records-checklist/)
- [FAIR Principles | GO FAIR](https://www.go-fair.org/fair-principles/)
- [What Are the FAIR Data Principles? | Columbia Health Sciences Library](https://library.cumc.columbia.edu/insight/what-are-fair-data-principles)
- [slackLists.create method | Slack Developer Docs](https://docs.slack.dev/reference/methods/slackLists.create/)
- [slackLists.items.create method | Slack Developer Docs](https://docs.slack.dev/reference/methods/slackLists.items.create/)
