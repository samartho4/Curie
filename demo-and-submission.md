# Curie — demo video script + Devpost text (grounded in the built product)

Product = **Curie** · agent = **@Prior** · everything below is real & seeded (Antimatter Lab, ESM landmine,
H2 refuted). Record in the actual sandbox. Target 2:45 (judges may stop at 3:00). First 60s decide it.

## A. VIDEO SCRIPT (~2:45, to the second)

**COLD OPEN — no logo, no "meet Curie."** Screen already on #experiments.
- **0:00–0:15 · The problem, enacted.** Time-lapse scroll of #experiments (Anika/Marco/Priya, months of runs).
  VO: *"This is a real lab's Slack. Six months of what worked and what failed — buried here."* Cut: a new member
  DMs a teammate *"why did we abandon the ESM full fine-tune?"* → *"🤷 ask Anika, she left."* Caption: **Labs forget. People leave.**
- **0:15–0:55 · THE CHECK (uncut, visible timer).** Type: `@Prior planning to fine-tune the ESM baseline, lr
  1e-4, batch 32, v1`. The checklist streams — *Checking priors… · Searched the lab record · Checked the
  literature*. The card lands: ⚠️ **This was already tried** — Anika, Mar 12, failed (gradient collapse); settings
  diff (lr/batch/split all match); a bioRxiv null result. Beat. VO: *"Eight seconds. That just saved three weeks."*
  Title card **Curie** flashes now, as punctuation.
- **0:55–1:35 · The record writes itself.** React 🧪 on a failure message → a receipt: *"Logged to ESM full FT —
  Failed. Notebook updated."* Open the **Lab Record** List → the row is there, status Failed, cited to the message.
  VO: *"Nobody filled in a form. Curie compiled it from the conversation."*
- **1:35–2:10 · THE PAYOFF (setup returns).** The new member from the cold open asks **@Prior** *"where does the
  lab stand?"* → the hypothesis map: **H2 🔴 Refuted (2 against) · H1 🟢 Supported (3 for) · H3 🟡 Open (1 running)**,
  every claim one click from its evidence. Hold. VO: *"Everything this lab believes, is testing, and has killed —
  in one view. This screen has never existed."*
- **2:10–2:35 · Zoom out (3 sentences).** *"70 to 90 percent of experiments fail — at Microsoft, at Netflix, and
  in your lab — and that learning is stored nowhere. The state of the art asks scientists to upload and file their
  own data; its flagship screen is an inbox literally called 'Unclassified Data.' Curie's inbox is empty by
  construction — the record writes itself."* Architecture diagram 3s, RTS + MCP + Slack AI highlighted.
- **2:35–2:45 · Close.** *"Curie — your lab's memory. Ask @Prior before you run. No experiment starts blind, no
  result dies unrecorded."* End card: `Try it → paste in #experiments: @Prior planning to fine-tune ESM, lr 1e-4,
  batch 32, v1`.

**Production:** light theme, zoom on every card, visible timer (no sped-up segments — real latency reads as real),
one confident voice at −16 LUFS, no copyrighted music. Record UI and VO separately. Upload ≥24h early; verify
public in incognito. NOT in the video: settings, error states, App Home tour — every second not on the 3 moments is wasted.

## B. DEVPOST TEXT

**Name:** Curie · **Track:** New Slack Agent · **Tagline:** The lab notebook that writes itself.

**First paragraph (what / who / why — put in your own voice, don't ship this verbatim):**
> Curie is a Slack agent that gives a research lab a memory. Post an experiment plan and mention @Prior, and in
> seconds it checks your plan against the lab's entire Slack history, its structured record, and the live
> scientific literature — then tells you, with citations, whether you're about to repeat a failure. Every result
> you react 🧪 to writes itself into a self-maintaining lab notebook, and every hypothesis rolls up its evidence
> into a living map of what the lab believes. It's for the research teams — academic and industry — who run on
> Slack and watch years of hard-won knowledge walk out the door with every person who leaves.

**Impact (be specific):** 70–90% of experiments fail or come back flat even at Microsoft, Netflix, and Airbnb
(Kohavi, HBR 2017) — the most valuable knowledge a team produces and the least recorded. Knowledge workers lose
5.3 hrs/week recreating existing knowledge (Panopto/YouGov); a single repeated failed experiment burns ~$6–15k of
researcher time before compute. Curie turns the conversation a lab is already having into the record it never keeps.

**How it uses the three technologies (all load-bearing):**
- **Real-Time Search API** — the collision check runs at post-time over the lab's private, unpublished history;
  without RTS you'd have to exfiltrate lab data to an external index. Nothing is stored (RTS terms).
- **MCP** — a custom `scholar` server over OpenAlex + bioRxiv brings live literature (incl. null results) into the
  verdict.
- **Slack AI / Agent surface** — plan-mode streaming + Block Kit verdict cards + native Lists (the record) +
  canvases + App Home. Curie couldn't exist as a web app; the plan is *posted in Slack*.

**Why not Claude Tag / an ELN / 83 Sciences?** Claude Tag answers questions; Curie maintains a typed system of
record with verdict instruments. ELNs and 83 Sciences make you leave your work to *file* it (their flagship screen
is literally "Unclassified Data") — Curie removes the filing: the record compiles itself from the conversation.
Scientists already build these evidence maps by hand in Roam (discourse graphs); Curie is the first that writes
itself, from where the lab already talks.

**A note on the name:** the product is **Curie** (Marie Curie's lab notebooks are so meticulous — and radioactive —
they're kept in lead-lined boxes, priceless a century later; a lab's Slack is the opposite). Its agent is **@Prior**,
because every experiment should start by checking your priors. (Simulated lab data; modeled on real ML-lab workflows.)

**Required submission items:** ~3-min public video · this description + impact · architecture diagram (file upload) ·
sandbox URL with slackhack@salesforce.com + testing@devpost.com as Members.
