# Curie — Skeptical Audit, Cursor Harness & Fable Brief (Jul 10)

You're right to be skeptical. Here's the honest state, what to keep vs. cut, which of your
20+ Cursor tools actually matter, and a ready-to-run brief for a Fable task.

## 1. Where the code REALLY is (measured, not claimed)

545 lines exist — and every one is **periphery, not spine**:

| Built & good (keep) | Lines | Status |
|---|---|---|
| `llm/client.py` | 65 | clean, OpenAI-default, pydantic-validated. Fine. |
| `tools/scholar.py` | 97 | live-tested vs OpenAlex. Done. |
| `seed/run.py` + `lab_story.yaml` | 204 | dry-tested, persona-ready. Good. |
| `scripts/smoke_tests.py` | 124 | written, **never run**. |
| `eval/cases.yaml` | 55 | 20 cases, no runner. |

**The spine — 0% built. None of these exist:**
- `app.py` — no Bolt entrypoint. `slack run` has nothing to run. **This is the hole.**
- `listeners/` — empty. No app_mention / message.im / reaction_added / app_home_opened handlers.
- `tools/rts.py` — no Real-Time Search wrapper (the load-bearing tech).
- `tools/record_store.py` — no Lists integration (the record).
- `pipeline/preflight.py` — the verdict engine. The heart. Vapor.
- `prompts/*.md` — empty. `llm/client.load_prompt()` points at nothing.
- `eval/run.py` — the harness runner (the credibility artifact). Missing.

**Translation:** we have excellent scaffolding, specs, and 2 leaf tools. We do NOT have a product.
Nothing has touched the live sandbox. Every architecture assumption is still an assumption.

## 2. Direction verdict — keep the plan, fix the sequencing (do NOT rewrite)

Three honest risks, and the fix for each:

1. **Unvalidated architecture (highest risk).** action_token presence, Lists API shape, streaming
   availability, RTS keyword-vs-semantic — all ASSUMED. Smoke tests are written but not run. Building
   the spine before running them risks building on sand. → **Run `scripts/smoke_tests.py` FIRST**, on the
   Mac, before writing more core code. It rewrites the plan if any assumption is wrong (kill-switches, backend.md §14).
2. **Scope ≫ timeline.** ~2.5 solo days left; backend.md §15 lists 10 steps incl. hypothesis ledger,
   App Home, ambient mode, trust states. **Cut all of that to stretch.** The MVP that wins:
   `@Curie <plan>` → streamed verdict card (collision / near-miss / clear, cited) + seed + eval + video.
   The ledger is the "sky" — and the FIRST thing to drop if Saturday runs late.
3. **Over-modularization temptation.** 6 module lanes are fine AS LONG AS you build a **vertical slice
   first** — one thin path (app.py → app_mention handler → preflight → plain-text verdict) that works
   end-to-end against the seeded sandbox — THEN broaden. Do not fill every module speculatively. The
   failure mode is a tidy half-wired skeleton that never runs.

**Structure verdict: sound. Don't restructure. The problem isn't the architecture — it's that the
spine is unbuilt and unproven. Fix by building the thinnest possible working slice next, not more modules.**

## 3. Your Cursor arsenal — harness 3, kill ~15 (this is the real answer)

You asked to "harness everything." The honest move is the opposite: most of what's installed is
**noise that will actively hurt** this project — context bloat, tool-selection confusion, and rabbit-hole
bait (AWS/web). Curie is a solo **Python Socket-Mode Slack app with a Block Kit UI** — no web frontend,
no AWS, no data warehouse.

**HARNESS (keep enabled for this workspace):**
- **`slack` MCP (19 tools)** ⭐⭐⭐ — the single most useful thing you have. Lets a Cursor agent search
  the sandbox, read #experiments, verify seed data, inspect channel/message state — build+test velocity.
  Caution: it has WRITE tools; during the judged window keep it read-only in habit, don't let an agent
  post/delete in the sandbox unprompted.
- **`context7` MCP / skill** ⭐⭐ — up-to-date Bolt/slack-sdk/OpenAI signatures; complements /docs snapshots
  when an agent needs an exact current API shape. Keep.
- **`commit-commands`** ⭐ — clean git flow. Nice-to-have.

**KILL (disable for this workspace — they add zero value and real risk):**
- **All 6 AWS MCPs** (aws-mcp ×2, aws-serverless-mcp, awsiac, awsknowledge, awspricing) — you're hosting
  on your laptop, not AWS. Pure context bloat + rabbit-hole bait. Biggest single cleanup.
- **Web/frontend stack** — shadcn, vercel, clerk, ChatPRD, CopilotKit, typescript-lsp. Curie has no web UI.
- **Plugin-authoring tools** — Create Plugin, create-plugin-scaffold, review-plugin-submission,
  plugin-architect, mcp-server-dev — for building *Cursor plugins*, not this app.
- **dbt Labs, SageMaker** — data/ML infra, irrelevant.
- **greptile** — would be nice for code review, but it's showing **Error** in your MCP list; fix or ignore.

Fewer, sharper tools = a calmer, more correct agent. Turn the noise off in *Tools & MCPs* for Slack4Good.

## 4. What to build next, in order (the only list that matters)

1. **[Mac] Run smoke tests** → commit `smoke_results.json`. Decides architecture paths.
2. **[Mac] `python -m seed.run`** → sandbox looks alive (personas post via chat:write.customize).
3. **Vertical slice:** `app.py` (Bolt Socket Mode) + `listeners/app_mention.py` + `tools/rts.py` +
   `tools/record_store.py` (read) + `pipeline/preflight.py` + `prompts/{parse_plan,check_plan,verdict}.md`
   → goal: `@Curie <plan>` returns a correct **plain-text** cited verdict. NO Block Kit yet.
4. **`eval/run.py`** → run 20 cases, prove zero false collisions.
5. Broaden: plan-mode streaming → Block Kit verdict card → 🧪 logging → (stretch) ledger/App Home.
6. Freeze, seed final, invite judges, record video, submit.

## 5. Fable task brief — paste this into your new task

> **Mission: skeptical architect + spine-builder for Curie (a Slack agent).**
> Read `/docs/backend.md`, `/docs/frontend.md`, `CLAUDE.md`, and the existing code (`llm/`, `tools/`,
> `seed/`, `scripts/`, `eval/`). Then:
> 1. **Audit with fresh eyes (30%).** Is the module structure right for a solo build due in 2 days? Name
>    anything over-engineered or missing. Give a go/no-go on the structure. Be blunt; I have no attachment.
> 2. **Build the vertical slice (70%).** Implement the minimum that makes `@Curie <plan>` produce a correct,
>    cited, PLAIN-TEXT verdict against a seeded #experiments: `app.py` (Bolt, Socket Mode, agent_view — NOT
>    the legacy assistant path, see CLAUDE.md), `listeners/app_mention.py`, `tools/rts.py`
>    (assistant.search.context, bot token + action_token; List-primary then RTS sweep; never persist results),
>    `tools/record_store.py` (read Lists), `pipeline/preflight.py` (check-plan → deterministic exec → verdict,
>    calibration per backend.md §13: "clear" is the confident default, zero false collisions), the referenced
>    `prompts/*.md`, and `eval/run.py`.
> **Constraints:** OpenAI default via `llm/client.py` (don't bypass it). Every claim carries a Slack permalink
> or DOI. Do NOT build the hypothesis ledger, App Home, ambient mode, or Block Kit cards yet — plain text first.
> Do NOT invent new dependencies. You cannot reach the live Slack sandbox (no tokens here) — write code that
> RUNS on the Mac; where you'd need live values, read from env and fail gracefully.
> **Deliver:** the audit verdict as `FABLE_AUDIT.md`, plus the code, plus a 5-line "how to run on the Mac" note.

## 6. Cowork vs Cursor — who runs what
- **Fable task (Cowork subagent, offline):** the audit + writing the spine from specs. Can't touch the live
  sandbox (no tokens/network to your Mac), but can write all the code. Perfect for deep reasoning + generation.
- **Cursor on the Mac (slack MCP + context7):** run smoke tests, seed, `slack run`, iterate against live Slack.
- Rule of thumb: **Fable writes the spine; Cursor proves it against Slack.**
