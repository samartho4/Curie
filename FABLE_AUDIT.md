# FABLE_AUDIT.md — fresh-eyes architecture review (Jul 10)

Reviewer stance: no attachment to prior choices; bias toward shipping a working demo by Mon Jul 13.

## Verdict: **GO on the architecture. Do not restructure.** Build the spine; cut the sky.

The 6-module split (`listeners / pipeline / tools / llm / seed / eval`) is the *right* shape for this
problem and is **not** over-engineered — it's under-*populated*. Four of six modules are essentially empty.
The risk here was never the structure; it's that the spine (the thing that turns `@Curie <plan>` into a
verdict) did not exist. Restructuring now would burn the one resource you can't get back: hours.

Why the lanes earn their keep even solo: `llm/client.py` as the single model interface means the OpenAI↔Anthropic
swap and per-task model routing live in one file; `tools/` as thin API wrappers means each Slack/lit dependency
degrades independently (kill-switches, backend §14) without touching the verdict logic; `pipeline/preflight.py`
as pure logic means the verdict engine is **testable offline** — which is what makes a real eval gate possible.
That testability is the whole ballgame for "zero false collisions."

## What's actually broken / wrong in existing code
1. **`llm/client.py` has a runtime crash**: `complete()` calls `_strip_fences(raw)` (line 61) but the helper is
   never defined → `NameError` on the *first* JSON call (i.e. every parse/verdict). Also: the `task` argument is
   dead (CLAUDE.md mandates gpt-4.1-mini for parse/RCS, gpt-4.1 for verdict via `CURIE_MODEL_*`), and a missing
   `OPENAI_API_KEY` / network error raises instead of returning `None`, defeating the §13 deterministic fallback.
   → **Fixed in this pass** (added `_strip_fences`, per-task model routing, broadened the JSON-path except so any
   failure → retry → `None`). This is a bug fix to the shared interface, not a second LLM path.
2. **`tools/scholar.py` docstring oversells**: claims OpenAlex **and** bioRxiv; the code only calls OpenAlex.
   Fine for MVP (OpenAlex alone is enough literature) — leaving as-is, just flagging the doc drift.
3. **`eval/cases.yaml` is 20 cases, spec §8 wants ≥40.** 20 is plenty to prove the *unforgivable* property
   (zero false collisions) for the demo. Defer expansion.
4. **Doc/manifest drift** (already known): backend §3.1 manifest shows the legacy assistant path + omits
   `chat:write.customize` which the live app now has. CLAUDE.md already overrides to agent_view; not a code issue.

## Ruthless MVP cut-list

**BUILD NOW (the vertical slice — the demo lives or dies here):**
- `app.py` (Bolt, Socket Mode), `listeners/app_mention.py`, `tools/rts.py`, `tools/record_store.py` (read),
  `pipeline/preflight.py` (the verdict engine + the **deterministic calibration guard**), `prompts/*.md`,
  `eval/run.py`. Goal: `@Curie <plan>` → correct, cited, **plain-text** collision/near-miss/clear.

**DEFER (clean seams left, no code):**
- Hypothesis ledger (F4/§6.4) — the "sky"; first thing to drop. Verdict model omits `hypothesis_hits` for now.
- App Home / onboarding (§6.5), Block Kit cards + plan-mode streaming (§11), 🧪 result logging (§6.2),
  ambient `message.channels` auto-detection (Trigger C). All post-slice.
- bioRxiv (OpenAlex suffices), semantic-query phrasing niceties (keyword mode is the safe default).

## The one design decision that matters most
The calibration guard is **deterministic, not LLM-trusted.** A collision is asserted only when a *structured*
candidate (a Lab-Record/seed row with real params) matches method AND (dataset OR ≥2 params), and confidence
≥0.65 — enforced in Python *after* the verdict LLM, so a hallucinated "collision" gets demoted to clear. Vague
RTS/literature hits alone can never trigger a collision. This is what makes "zero false collisions" a property
of the code, not a hope about the model.

## Bonus: eval runs offline
`eval/run.py` defaults to an **offline seed-fixture provider** built from `seed/lab_story.yaml` — so the gate
runs on the Mac with just `OPENAI_API_KEY` (no live sandbox needed) and on every change (§8 asks exactly this).
`--live` swaps in the real Slack providers. Without a key it still runs (no crash) and cannot false-collide,
because collisions require the verdict LLM.
