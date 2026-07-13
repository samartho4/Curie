# Curie — how to actually use context7 + the Slack MCP (your two force-multipliers)

Of your ~20 Cursor tools, exactly two move the needle on this build. Here's the deep playbook.
Both exist to kill the same risk: **Fable had to GUESS Slack's API shapes, and guesses break live.**

## A. context7 — verify every Slack API shape BEFORE you trust code (proven, not theoretical)

context7 serves live Slack docs (`/websites/slack_dev`, 26k snippets). Used it just now and it caught a
**live-breaking bug**: `tools/rts.py` read `m.get("text")`, but `assistant.search.context` returns the
message body in a field called **`content`** (plus `channel_id`, `message_ts`, `author_user_id` — not
`channel`/`ts`/`user`). Result: every RTS hit was silently dropped → the whole search feature returns
nothing. Fixed + unit-checked. **This is the single highest-value tool use in the project so far.**

**The discipline (do this in Cursor for every Slack call you write):**
1. Before writing/trusting a `client.api_call("<method>")`, ask context7: *"exact JSON response shape of
   `<method>`, field names."* Verify the keys your code reads actually exist.
2. Highest-risk call sites to verify first (all currently best-guess):
   - `assistant.search.context` → results.messages[].{content, permalink, channel_id, message_ts, thread_ts,
     author_user_id, context_messages}  ✅ verified + fixed.
   - `slackLists.items.list` → items[].fields[].{key, value, column_id, **text** (flattened convenience),
     rich_text, select[], user[], date[], message[]} + response_metadata.next_cursor  ✅ verified (record_store OK).
   - `slackLists.create` / `items.create` — verify the `initial_fields` rich_text payload shape before the
     List-write path (text fields MUST be Block Kit rich_text in the REQUEST; §4.1).
   - `chat.startStream` / `appendStream` / `stopStream` — verify when you build streaming (Sat).
3. Rule: **context7 for exact API signatures; /docs/*.md for our architecture decisions.** They complement.

## B. Slack MCP (19 tools, Cursor-only) — your live sandbox microscope + test harness

This can't run from Cowork (OAuth), so it's your Cursor superpower. It turns the sandbox into something you
can inspect and drive WITHOUT running the full app — huge for tightening the loop. Map the 19 tools to jobs:

**1. Verify the seed looks real (right after `python -m seed.run`):**
- search messages for `ESM lr 1e-4` → confirm the landmines are there and authored by Anika/Marco/Priya
  (not the bot). This is also a manual proxy for smoke test #3 (are persona messages findable?).
- get channel history for #experiments (C0BGB4YK05C) → eyeball threads, reactions, that it reads like a lab.

**2. De-risk RTS before the app even runs:**
- Use the MCP's search tool with the SAME alias-expanded OR-queries `tools/rts.py` builds
  ("ESM OR ESM-2 fine-tune lr 1e-4") → see what really comes back on THIS workspace. If keyword recall is
  weak, you learn it now (→ backend.md §14 fallback: conversations.history), not during the demo.
- Confirms semantic-vs-keyword behavior live (sandbox has AI Search ON).

**3. Inspect the List once it exists (after the List-write path):**
- read the "Lab Record" list items → confirm hypothesis parent rows + experiment child rows, column values,
  and that `record_store.find_candidates` will match. Ground-truth for param-precise collisions.

**4. Drive the agent end-to-end for testing:**
- post a message `@Curie planning to fine-tune ESM, lr 1e-4, batch 32, v1` into #experiments via the MCP →
  triggers the real app → watch the verdict come back. Scriptable regression of the demo's hero moment.

**Guardrail:** the MCP has WRITE tools (post/react/etc.). During judging (Jul 14–Aug 6) don't let an agent
post/delete in the sandbox unprompted — keep writes deliberate. Read/search freely; write on purpose.

## C. The combined loop (this is the workflow that ships)
context7 (verify the call shape) → write/patch the tool → Slack MCP (run that exact call live, eyeball the
real response) → fix mismatches → `python app.py` + MCP-post a test plan → verdict. Tight, no guessing.
