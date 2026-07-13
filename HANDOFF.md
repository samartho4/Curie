# Curie — Claude Code handoff (start here on the Mac)

## State when this was written (Cowork, Fri Jul 10)
- Sandbox **Prior Lab** live (no payment). App **Curie** created, App ID `A0BH74BCN3A`, Socket Mode + Agent
  experience ON, 22 bot + 4 user scopes, events + "Log to Curie" shortcut, MCP-Servers flag present (bonus).
- `.env` exists with 4 keys FILLED by the human (SLACK_BOT_TOKEN, SLACK_APP_TOKEN, CURIE_USER_TOKEN, OPENAI_API_KEY).
  Still to set: CURIE_CHANNEL_ID (create #experiments first), SEED_USER_TOKEN_1..3 (dummy members).
- Scaffold + specs in place. **Read CLAUDE.md first** (agent_view mandate, naming, OpenAI default).

## Already built & verified (don't rebuild)
- `llm/client.py` — one interface, OpenAI default (json_object mode), Anthropic fallback. Compiles.
- `tools/scholar.py` — OpenAlex + bioRxiv literature; **live-tested green** (`python -m tools.scholar selftest`).
  Runs in-process or as FastMCP server (`python -m tools.scholar`).
- `scripts/smoke_tests.py` — the day-one gate. Compiles.
- `seed/lab_story.yaml` — Antimatter Lab: 3 hypotheses (H2 is the refuted demo one), 6 experiments (3 landmines),
  paper-club + general chatter. Deterministic; eval references it.
- `eval/cases.yaml` — 20 labeled cases (6 collision incl. 1 injection, 5 near-miss, 9 clear incl. off-domain +
  ambiguous). Expand toward 40 as time allows. RULE: any false collision = red.

## Your first 4 moves
1. `cp .env … ` already done. `pip install -r requirements.txt`.
2. Create #experiments in the sandbox, set CURIE_CHANNEL_ID in .env.
3. `python scripts/smoke_tests.py api` → then `python scripts/smoke_tests.py listen` and @mention + DM Curie.
   Commit `scripts/smoke_results.json`. It DECIDES: action_token presence, Lists e2e, streaming, semantic,
   user-token RTS. Wire the backend.md §14 kill-switches from the results.
4. Build in backend.md §15 order. Next up: `tools/record_store.py` (Lists), `tools/rts.py`, `pipeline/preflight.py`
   (plain-text E2E first — no Block Kit), then eval, then streaming+cards (frontend.md §4 payloads, copy §9 VERBATIM).

## Build contract reminders
- Product name **Curie** everywhere user-facing; "prior" only as the feature verb ("checking priors…").
- Never persist retrieved Slack data. ≤3 RTS calls/verdict. Every claim carries a citation.
- Seed as dummy MEMBERS not the bot (smoke test #3). Judges scroll — keep it authentic.
- Hosting for Jul 14–Aug 6: laptop + caffeinate + launchd KeepAlive + daily self-ping DM (README).

---
## Update (Jul 10, later) — sandbox config finalized via Chrome
- **#experiments created**: `CURIE_CHANNEL_ID=C0BGB4YK05C` (in .env). Curie bot is a MEMBER of it.
- **App renamed Prior → Curie** everywhere: App name, bot Display Name "Curie", username "curie" (@curie).
- **Scope `chat:write.customize` ADDED + app reinstalled** → seed personas can post as "Anika Rao" w/ avatar.
  Bot token did NOT rotate (token rotation off) — existing SLACK_BOT_TOKEN in .env is still valid, now with the
  new scope. (If auth ever fails, re-copy Bot User OAuth Token from Install App page.)
- **Confirmed on this sandbox**: Slack AI Search / Enterprise search is ON (semantic RTS available);
  Agents & AI Apps ON; Home+Messages tabs ON (agent_view path); "Search Apps" + "MCP Servers" features present.
- The 7 pre-made template users are NOT usable as authors (no tokens/logins) — bot-personas is the seed path.
- Manifest note: backend.md §3.1 lists scopes without chat:write.customize; the live app now HAS it. Reconcile
  the manifest doc if regenerating from it.

---
## Update (Jul 10, session 3) — context7 fixes + List-write path
- **context7 caught a live-breaking bug in `tools/rts.py`**: it read `m["text"]`, but `assistant.search.context`
  returns the body in `content` (+ `channel_id`/`message_ts`/`author_user_id`). Every RTS hit was being dropped.
  FIXED + unit-checked. See `TOOLING.md` for the verify-before-you-trust discipline.
- **List-write path built**: `seed/seed_list.py` — `python -m seed.seed_list` creates the "Lab Record" List
  (§4.1 schema) + hypothesis parent rows + experiment child rows from lab_story.yaml. Dry-run verified.
  → paste the printed `CURIE_LIST_ID=…` into .env so live collisions are param-precise (not just keyword).
- `record_store._flatten_value` now unwraps single-element list values (prevents hypothesis rows leaking
  into collision candidates = a false collision).
- **Updated Mac run order:** pip install → smoke tests → `python -m seed.run` (chatter) →
  `python -m seed.seed_list` (structured rows; set CURIE_LIST_ID) → `python app.py` → `@Curie <plan>`.
- **TOOLING.md** = how to use context7 (verify every Slack API shape) + the Slack MCP 19-tool playbook (Cursor).

---
## Update (Jul 10, session 4) — RAN THE SEQUENCE LIVE + built streaming & cards
Everything below was executed against the real sandbox from Cowork (network reachable; tokens in .env).

**✅ Proven live (not just compiled):**
- pip install ✓ · smoke tests: Lists e2e ✓, `is_ai_search_enabled=true` ✓, RTS user-token (no action_token) ✓,
  bot-token RTS needs action_token ✓ (invalid_action_token), streaming needs thread_ts+recipient ids (fixed).
- `seed.run` → 21 persona messages in #experiments ✓.  `seed.seed_list` → List + 3 hypotheses + 6 experiments ✓,
  **CURIE_LIST_ID=F0BGA5Y80P5 (in .env)**.
- **LIVE PREFLIGHT on the ESM landmine → COLLISION, confidence 0.98**, cited the List row AND real Slack
  permalinks AND literature, correct settings diff. The whole spine works with real Slack RTS + real OpenAI.
- **Streaming + Block Kit card built & rendered live**: `tools/streaming.py` (start→step→stop, graceful
  postMessage fallback), `tools/cards.py` (§9 copy). Streamed a full verdict card in-thread (header/section/
  diff/citations/actions/disclaimer). Wired into `listeners/app_mention.py`.
- `app.py` boots, connects Socket Mode, registers the listener → "⚡️ Bolt app is running!"

**Bugs context7 + live testing caught & fixed:** rts.py read `text` not `content` (dropped every hit);
seed_list wrote `date` as string not array; card button used a non-URL List permalink.

**The ONLY unverified link:** a real `@Curie` mention flowing through Socket Mode → handler. Needs a human to
type it in Slack (user token has no chat:write, and Socket Mode needs a persistent process). Do this on the Mac:
`python app.py`, then in #experiments type `@Curie planning to fine-tune ESM, lr 1e-4, batch 32, v1`.

**Cleanup TODO (before demo/judging):** orphan test artifacts exist — a "SMOKE Lab Record (delete me)" list,
a smoke canvas, and a partial "Lab Record" list from the first seed_list attempt. Deleting them needs the
`files:write` scope (not currently granted). Add it (Chrome, one reinstall) then delete, OR remove them by hand
in the Slack Lists UI. The live List judges should see is **F0BGA5Y80P5**.

**Note:** `search_mode()` reports `keyword` even though AI Search is enabled workspace-wide — pipeline works
great in keyword mode (the live collision proves it). Semantic phrasing for query #1 is an optional enhancement.

---
## Update (Jul 10, session 5) — 🧪 logging + App Home built; sandbox cleaned
- **NEW verified-shapes doc**: `docs/platform/api-shapes-verified.md` — exact shapes (app_home_opened/views.publish,
  reaction_added, slackLists.items.update cells) fetched via context7 so builds don't guess.
- **🧪 result-logging** (`listeners/reaction_added.py` + `prompts/log_extract.md`): react 🧪 on a result →
  extract {status,outcome} → update the matching List row (slackLists.items.update `cells` shape) → post a
  §9 receipt with Undo/Verify. Wired into app.py. Built by a small Fable task.
- **App Home** (`listeners/app_home.py`): app_home_opened → views.publish stats (experiments/hypotheses/
  collisions), recent activity, the three gestures, controls; first-run setup CTA. Wired into app.py. Small Fable task.
- app.py now registers 3 listeners (app_mention, reaction_added, app_home) — boots clean, "⚡️ Bolt app is running!".
- **Sandbox cleaned** (added files:write scope + reinstall): deleted SMOKE list, the partial pre-date-fix list,
  and the smoke canvas. The ONLY List now is the real **Lab Record F0BGA5Y80P5**. Bot token unchanged by reinstall.
- **KNOWN ISSUE — bot shows as "Prior"/@prior, not "Curie"/@curie.** App config Display Name IS "Curie", but the
  installed bot user's profile name is cached; reinstall did NOT refresh it. The app is fully functional as @prior.
  To force @curie: remove the app from the workspace and install fresh (may change bot_id → re-add to #experiments,
  re-verify tokens), OR accept "Prior" as the bot's Slack name. Branding decision for Samarth. (One stray test
  mention from the user remains in #experiments — delete it in Slack; bot can't delete a user's message.)
- **The full @mention→verdict loop still needs the Mac**: Cowork's bash sandbox is per-call (die-with-parent), so
  app.py can't stay running to receive a Socket Mode event here. Every component is proven live; run `python app.py`
  on the Mac + mention the bot to see the streamed card.

---
## Update (Jul 10, session 6) — sky-demo autonomy built; hosting researched
- **Sky demo redesigned** (`demo-SKY.md`): live coding-agent run (Claude Science) → posts run-record to Slack via
  MCP → Curie auto-ingests → **proactive belief-change alert** (event-driven, the real-time autonomy star) →
  ambient plan-checking → hypothesis map. Impact stats moved to TEXT only, off camera.
- **Claude Science demo SOLVED**: Slack connector already ON at project level (inherits to every session); demo by
  asking it to run the experiment + post a `📊 Run …` record to #experiments. Curie ingests. Runbook in demo-SKY.md.
- **Built + verified (Fable + live logic tests):**
  - `listeners/ambient.py` — message.channels handler: ingests `📊 Run` records from OTHER apps (bot_message,
    verified shape), updates row + evidence, fires belief-change alert on a status flip; ambient preflight (flag).
  - `listeners/standing.py` — "from now on" → standing watch + weekly digest; "show this week's digest" → run-now.
  - `pipeline/logging.py` — shared record-write path (ambient + reaction_added). `belief_digest_blocks` in ledger.
  - Wired all into app.py (5 listeners) + app_mention.py (standing route). Boots clean. Digest renders live.
- **Hosting (researched):** free 24/7 hosting is mostly dead in 2026 (Render sleeps, Railway/Fly no free, Oracle
  queues). AWS EC2 t2.micro free tier is the only real free cloud option; **Mac + caffeinate + launchd is the
  zero-friction host** and where the video is recorded anyway. AWS deploy is blocked from Cowork by sandbox file
  boundaries → needs a GitHub push (auth the connector) as the code bridge, then EC2 clones it.
- **Demo staging note:** to show H2 flip live, seed H2 with ONE contrast child so the coding-agent's failed run adds
  the 2nd → flips to Refuted + fires the alert (ambient.py verified this scenario offline).
