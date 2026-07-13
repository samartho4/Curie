# Writing a Devpost story that reads as human, not generated

Distilled from Devpost's own judging guidance + how winning submissions actually read. Use this as the
checklist for `devpost-FINAL.md`.

## What judges actually do
- They skim **dozens** of projects, ~5–7 minutes each, video + text together. The first 60 seconds (and
  first paragraph) decide whether they lean in. ([Devpost judging tips](https://info.devpost.com/blog/hackathon-judging-tips))
- They check **requirements first** — miss one and you're disqualified before the story matters.
  ([submission & judging criteria](https://info.devpost.com/blog/understanding-hackathon-submission-and-judging-criteria))
- They score on **Quality of idea · Implementation · Impact** (this challenge: Creativity · Functionality
  · Impact). The text's job is to *confirm* what the video showed and answer "what / who / why."
- Organizers say **AI-boilerplate is "obvious and forgettable."** Enthusiasm and specificity signal real effort.

## The voice (how to sound human)
1. **First person, past tense, plain.** "We built…", "the hardest part was…". Not "Curie leverages
   cutting-edge AI to revolutionize…".
2. **Concrete beats abstract.** Name the real thing: *"lr 1e-4, batch 32, gradient collapse at epoch 3,"*
   not *"suboptimal hyperparameters."* One true detail is worth a paragraph of adjectives.
3. **Show the seams.** Admit what broke and how you found it. The `:bar_chart:` shortcode, the log line
   that never printed — those are what make it believable. Judges trust a story that isn't airbrushed.
4. **No superlatives, no hype adjectives.** Cut "seamless, powerful, innovative, revolutionary,
   game-changing, robust, cutting-edge." If a sentence still works with the adjective deleted, delete it.
5. **Short paragraphs, short sentences.** 2–4 sentences per paragraph. White space is a feature.
6. **One idea per section.** Follow the prompted headings exactly; don't repeat yourself across them.
7. **A specific opening image, not a thesis.** Start with the *moment* (the radioactive notebooks; "ask
   Anika, she left"), then let the reader infer the point. Don't announce "In today's fast-paced world…".

## Structure (the given headings, and what each is for)
- **Inspiration** — the moment/problem, human and specific. 2–3 short paragraphs. No product yet.
- **What it does** — plainly, what a user does and gets. Concrete verbs. The three verdicts. The one
  surprising thing (it writes itself).
- **How we built it** — the real stack + the *one interesting decision* (deterministic verdict, no DB).
  Enough that an engineer nods; not a changelog.
- **Challenges** — the honest debugging arc. The hardest bug, told like a story with a resolution.
- **Accomplishments** — 3–5 things, each falsifiable ("works live in a real workspace," "eval gates on
  zero false collisions"). Pride, not marketing.
- **What we learned** — 2–3 genuine takeaways (structured layer beats prompt-engineering; autonomy must
  be *shown*). A learning, not a lesson-plan.
- **What's next** — a short bullet list of concrete, believable next steps. Not a roadmap fantasy.

## Formatting
- Markdown is supported — use light **bold** for the 3 verdicts / key terms, bullets only in What's next
  (and sparingly). No walls of bold. No emoji spam (one or two, purposeful).
- Put the **architecture diagram in the file-upload field**, not the image carousel.
- Label simulated data honestly ("a simulated lab modeled on real comp-bio workflows").
- Answer the obvious skeptic question in one line ("why not just ask Slack AI?").

## Fast self-edit pass (do this last)
- [ ] Delete every hype adjective; re-read — does it still say the same thing? (It will.)
- [ ] First paragraph: is it a *moment*, or a *thesis*? Make it a moment.
- [ ] Any sentence that could appear in *any* project's writeup? Cut or make it specific to Curie.
- [ ] Read it aloud. Anywhere you wouldn't say it out loud to a friend, rewrite.
- [ ] Under ~700 words total. Shorter is more confident.
