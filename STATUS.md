# Curie — where we are & what's next (read me first)

**Curie** = the self-writing lab memory in Slack. You mention **@Prior** to check an experiment plan against
everything the lab already knows. Product name = Curie; agent handle = @Prior (Bubble Lab → @Pearl pattern).

## ✅ DONE and verified LIVE (real Slack + real OpenAI, from this machine)
1. **Preflight verdict** — `@Prior <plan>` → streamed "Checking priors…" checklist → Block Kit verdict card
   (collision / near-miss / clear) with settings diff, Slack + literature citations. Live test on the ESM
   landmine returned **COLLISION, confidence 0.98**, correctly cited.
2. **Self-writing record** — native Slack List "Lab Record" (`CURIE_LIST_ID=F0BGA5Y80P5`): 3 hypotheses + 6
   experiments, parent/child linked. Seeded live.
3. **🧪 result-logging** — react 🧪 on a result → extracts outcome → updates the List row → posts a receipt.
4. **App Home dashboard** — stats, recent activity, the three gestures, first-run setup.
5. **Hypothesis ledger** — `@Prior track hypothesis: …` + "where does the lab stand?" → the map:
   H2 🔴 Refuted, H1 🟢 Supported, H3 🟡 Open, each linked to evidence. Rendered live.
- **Sandbox is seeded & clean** (one List, 21 persona messages in #experiments). AI Search ON. Tokens in `.env`.
- 11 Python modules, all compile; `app.py` boots to "⚡️ Bolt app is running!". Zero-false-collision guard
  unit-tested (`eval/test_calibration.py`).

## ▶️ WHAT YOU DO ON THE MAC (the sandbox is already seeded — do NOT re-seed)
```
cd ~/Pictures/Slack4Good
pip install -r requirements.txt          # once
python app.py                            # keep it running (Socket Mode; no public URL)
```
Then in Slack **#experiments**, type:  `@Prior planning to fine-tune the ESM baseline, lr 1e-4, batch 32, v1`
→ watch the streamed checklist resolve into the collision card. Try `@Prior where does the lab stand?` too.

**Why the Mac:** the app must stay running to catch the Slack event; Cowork's sandbox is torn down between
steps so it can't host a persistent listener. Every piece is already proven live — this just wires the last hop.

**Hosting during judging (Jul 14–Aug 6):** keep app.py running on the laptop — `caffeinate -dimsu` so it never
sleeps, plus a launchd KeepAlive so it restarts on crash/reboot (see README).

## 🧹 One-minute cleanups (on the Mac, optional)
- Delete the single leftover `@Prior planning to fine-tune…` test mention still in #experiments (I posted it to
  test; the bot can't delete a user's message, so do it by hand: hover → ⋯ → Delete).

## ⏭️ WHAT'S LEFT (all non-code — the product is done)
1. **Record the ~3-min demo video** (storyboard drafted; see `demo-and-submission.md`).
2. **Write the Devpost text** (first paragraph + impact; draft in `demo-and-submission.md`, put it in YOUR voice).
3. **Architecture diagram** (Mermaid → export PNG; upload via Devpost file field, not the carousel).
4. **Submit** on Devpost: track = New Slack Agent; invite slackhack@salesforce.com + testing@devpost.com as
   **Members** of the sandbox; video public (test incognito); submit by **Sun Jul 12** (organizers reward early).

## Key facts (don't lose these)
- Bot handle **@Prior** · Product **Curie** · App ID `A0BH74BCN3A` · #experiments `C0BGB4YK05C` · List `F0BGA5Y80P5`
- `.env` (gitignored) holds all tokens + OPENAI_API_KEY + CURIE_LIST_ID. Never commit it.
- Naming rationale + all build decisions: `CLAUDE.md`. Full session log: `HANDOFF.md`. Strategy: `docs/`.
