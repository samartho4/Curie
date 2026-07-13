# Curie — Backend Engineering Spec (backend.md)

**Standalone document.** A human or coding agent reading only this file can build the complete backend.
Companion: `frontend.md` (surfaces, Block Kit, copy, states). Contract between the two: §11.

---

## 0. What this system is

Curie is a Slack-native agent for research labs. It does three things:

1. **Preflight** — when a researcher posts an experiment plan, Curie checks it against (a) the lab's structured experiment record, (b) raw Slack history, and (c) live scientific literature, then replies in-thread with a **verdict card**: collision / near-miss / clear, with cited evidence.
2. **Self-writing record** — experiments are first-class objects in a native Slack **List**; each has a self-compiling **canvas** notebook page. Outcomes are logged via 🧪 reaction or message shortcut. Nobody does data entry.
3. **Hypothesis ledger** — hypotheses are parent rows in the List; experiments and external papers link to them as evidence with polarity **supports / contrasts / mentions** (Scite taxonomy). Statuses roll up: Open / Supported / Refuted.

Design lineage (why the architecture looks like this): plan-then-execute separation (PromptQL), List-primary hybrid retrieval (Glean), per-candidate contextual summarization "RCS" (PaperQA2), evidence polarity (Scite), trust states (Guru), discourse-graph data model (Joel Chan).

**Glossary**
| Term | Meaning |
|---|---|
| RTS | Slack Real-Time Search API (`assistant.search.context`) |
| action_token | One-shot token in certain event payloads; REQUIRED for bot-token RTS calls |
| Verdict | Structured output of a Preflight check: `{level, collisions[], literature[], hypothesis_hits[], diff}` |
| Record | One experiment = one Slack List row + one canvas page |
| Ledger | Hypothesis parent rows + evidence edges |
| Check plan | Deterministic sequence of retrieval steps composed by the LLM, executed outside the LLM |

---

## 1. Requirements

### Functional
- F1: `@Curie <plan text>` in a channel → verdict card in-thread within 20 s, streamed as a live plan.
- F2: DM / split-pane assistant: same check + Q&A over the record ("what have we tried on ESM?", "where does the lab stand?").
- F3: 🧪 reaction or message shortcut "Log to Curie" on any message → extract outcome → create/update List row + canvas page (act-then-undo, no confirm modal for low-stakes writes).
- F4: `@Curie track hypothesis: <text>` → parent row in Ledger. Agent proposes evidence links (confirm buttons); outcomes roll up to hypothesis status.
- F5: Verdict must consult: List (primary), RTS (secondary sweep), scholar-mcp (literature), Ledger (hypothesis hits).
- F6: Every claim in every output carries a citation (Slack permalink or DOI/URL).
- F7: First-run: empty workspace/channel → guided setup (create List, explain triggers).
- F8: Eval harness: ≥40 labeled plans; CI-style run; zero false collisions target.

### Non-functional
- N1: p50 verdict latency ≤ 12 s, p95 ≤ 20 s; perceived latency masked by streaming (see §11).
- N2: **Zero-storage compliance**: RTS terms forbid storing/copying retrieved Slack data. No local index, no embedding store of Slack content. Slack (Lists/canvases) is the only persistence for record data. Local disk may hold: config, eval fixtures, run logs (metadata only).
- N3: Rate-limit safety: ≤3 RTS calls per verdict; `chat.update` ≥3 s apart; Lists writes Tier 2/3 aware; graceful 429 path.
- N4: Single-process deployable by one person (`slack run`, Socket Mode). No external DB, no queue infra.
- N5: Judge-proof: works cold for a stranger with Member access; all failure modes produce human messages, never stack traces.

### Constraints
- Bolt for Python 3.11+, Slack CLI scaffold (`slack create agent`, Casey template, Claude Agent SDK variant — or `bolt-python-assistant-template`).
- LLM: Anthropic API (any current Sonnet-class model); all LLM calls behind one internal interface (§7.4) so the model is swappable.
- Runs in a Slack Developer Program sandbox (paid-plan features incl. Lists, canvases, Agents & AI Apps enabled).
- Solo developer; every component must degrade independently (see kill-switches, §14).

---

## 2. High-level architecture

```
                        ┌──────────────────────────── Slack workspace ────────────────────────────┐
                        │  #experiments channel · DMs · split-pane assistant · App Home           │
                        │  Experiments+Hypotheses List (native) · per-experiment canvases         │
                        └───────▲──────────────────────────────▲────────────────────▲─────────────┘
                                │ Block Kit / streams          │ Lists & Canvas API │ events (Socket Mode)
                                │                              │                    │
┌───────────────────────────────┴──────────────────────────────┴────────────────────┴─────────────┐
│                                   prior (single Python process, Bolt)                        │
│                                                                                                 │
│  listeners/            pipeline/                    tools/                    llm/              │
│  ├ app_mention  ──────▶ preflight.py  ──────────▶  ├ record_store.py (Lists) ├ client.py       │
│  ├ assistant (im)      │  1 parse_plan             ├ rts.py (assistant.search.context)          │
│  ├ reaction_added ────▶│  2 compose check plan     ├ replies.py (conversations.replies)         │
│  ├ message_shortcut    │  3 execute plan (determ.) ├ scholar.py (MCP client → scholar-mcp)      │
│  ├ block_actions       │  4 RCS summaries          └ canvas.py                                  │
│  └ app_home_opened     │  5 verdict compose                                                     │
│                        └ ledger.py (hypotheses)     eval/ (harness + fixtures)                  │
│                        └ logging.py (🧪 → record)   seed/ (workspace seeder)                     │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │ MCP (stdio or HTTP)
                                     ┌──────────▼──────────┐        ┌──────────────────────┐
                                     │ scholar-mcp (Python │  HTTPS │ OpenAlex API (no key)│
                                     │ FastMCP server)     ├───────▶│ bioRxiv API (no key) │
                                     └─────────────────────┘        └──────────────────────┘
```

**Data flow (Preflight, the core loop):** event → parse plan (LLM) → check plan (LLM, JSON) → deterministic execution: List query → RTS sweep (≤3 calls) → `conversations.replies` on top hits → scholar-mcp → RCS per candidate (LLM, parallel) → verdict compose (LLM, JSON) → render (frontend contract §11).

Trade-off note: single process + in-memory job state (dict keyed by `thread_ts`) instead of a queue/DB. Acceptable: hackathon scale is ~1 concurrent user; restart loses only in-flight jobs (users just re-mention). Revisit with Temporal/queue if this ever ships for real (Dust's pattern).

---

## 3. Slack app configuration

### 3.1 Manifest essentials (`manifest.json`)
```json
{
  "display_information": { "name": "Curie" },
  "features": {
    "bot_user": { "display_name": "Curie", "always_online": true },
    "app_home": { "home_tab_enabled": true, "messages_tab_enabled": true },
    "assistant_view": {
      "assistant_description": "The lab's memory. No experiment starts blind.",
      "suggested_prompts": []
    },
    "shortcuts": [
      { "name": "Log to Curie", "type": "message", "callback_id": "log_result",
        "description": "Log this message as an experiment outcome" }
    ]
  },
  "oauth_config": {
    "scopes": {
      "bot": [
        "assistant:write", "app_mentions:read", "chat:write", "reactions:read", "reactions:write",
        "channels:history", "groups:history", "im:history", "mpim:history",
        "search:read.public", "search:read.files", "search:read.users",
        "lists:read", "lists:write", "canvases:read", "canvases:write",
        "users:read", "commands", "files:read"
      ],
      "user": ["search:read.public", "search:read.private", "search:read.im", "search:read.mpim"]
    }
  },
  "settings": {
    "event_subscriptions": {
      "bot_events": [
        "app_mention", "message.im", "message.channels",
        "assistant_thread_started", "assistant_thread_context_changed",
        "reaction_added", "app_home_opened"
      ]
    },
    "interactivity": { "is_enabled": true },
    "socket_mode_enabled": true
  }
}
```
Also toggle ON in App Settings: **Agents & AI Apps** (enables split pane, `assistant.*` methods, streaming).

### 3.2 Token model — read carefully, this is the #1 foot-gun
- **Bot token (`xoxb`)**: all writes (chat, Lists, canvas, reactions) + RTS **only when an `action_token` is present**.
- `action_token` is present in: `app_mention` payloads, `message.im` payloads. It is **NOT** present in plain `message.channels` events (only when the app is mentioned).
- **User token (`xoxp`, developer's own, obtained via OAuth install flow)**: RTS **without** action_token → powers (a) ambient channel listening (Trigger C), (b) any check where the event's token was consumed/expired. Store in env (`CURIE_USER_TOKEN`); never log it.
- Env vars: `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN` (Socket Mode), `CURIE_USER_TOKEN`, `ANTHROPIC_API_KEY`, `CURIE_CHANNEL_ID` (#experiments), `CURIE_LIST_ID` (set by setup), `CURIE_MODE` (`full|preflight_only` kill-switch).

### 3.3 Triggers
| Trigger | Event | RTS token path | Use |
|---|---|---|---|
| A (canonical) | `app_mention` in channel | bot + event.action_token | `@Curie <plan>` / `track hypothesis:` |
| B | `message.im` (assistant/DM) | bot + event.action_token | Q&A, checks from split pane |
| C (ambient, flag-gated) | `message.channels` in `CURIE_CHANNEL_ID` | user token (no action_token needed) | plan auto-detection; classifier gate, §6.3 |
| D | `reaction_added` (🧪, emoji name `test_tube`) | n/a (no search) | result logging |
| E | message shortcut `log_result` | n/a | result logging (explicit) |

---

## 4. Data model

**Persistence = Slack itself.** One List (two-level), N canvases, plus message permalinks as foreign keys. No other datastore (N2).

### 4.1 The List (created by setup routine via `slackLists.create`)
Parent rows = **hypotheses**. Child rows (`parent_item_id`) = **experiments**. One List keeps rollups trivial and the judge-visible surface singular. Orphan experiments (no hypothesis) are top-level rows with `kind=experiment`.

Schema (exact `schema` argument for `slackLists.create`):
```json
[
 {"key":"title","name":"Title","type":"text","is_primary_column":true},
 {"key":"kind","name":"Kind","type":"select","options":{"format":"single_select","choices":[
   {"value":"hypothesis","label":"Hypothesis","color":"purple"},
   {"value":"experiment","label":"Experiment","color":"blue"}]}},
 {"key":"status","name":"Status","type":"select","options":{"format":"single_select","choices":[
   {"value":"open","label":"Open","color":"yellow"},
   {"value":"running","label":"Running","color":"blue"},
   {"value":"succeeded","label":"Succeeded","color":"green"},
   {"value":"failed","label":"Failed","color":"red"},
   {"value":"abandoned","label":"Abandoned","color":"gray"},
   {"value":"supported","label":"Supported","color":"green"},
   {"value":"refuted","label":"Refuted","color":"red"}]}},
 {"key":"owner","name":"Owner","type":"user","options":{"format":"single_entity"}},
 {"key":"params","name":"Params","type":"rich_text"},
 {"key":"outcome","name":"Outcome","type":"rich_text"},
 {"key":"polarity","name":"Evidence","type":"select","options":{"format":"single_select","choices":[
   {"value":"supports","label":"Supports","color":"green"},
   {"value":"contrasts","label":"Contrasts","color":"red"},
   {"value":"mentions","label":"Mentions","color":"gray"}]}},
 {"key":"source","name":"Source message","type":"message"},
 {"key":"notebook","name":"Notebook","type":"canvas"},
 {"key":"trust","name":"Trust","type":"select","options":{"format":"single_select","choices":[
   {"value":"verified","label":"✓ Owner-verified","color":"green"},
   {"value":"auto","label":"Auto-logged","color":"gray"}]}},
 {"key":"updated","name":"Updated","type":"date"}
]
```
Notes: text fields MUST be written as Block Kit `rich_text` (plain `text` is rejected in request payloads). Capture returned `column_id`s at creation and cache in `CURIE_LIST_SCHEMA` (JSON file — config, not Slack data). Rate limits: create Tier 2 (20/min), items Tier 3 (50/min).

### 4.2 Canonical in-code types (pydantic)
```python
class Plan(BaseModel):            # parsed from a plan message
    method: str; params: dict[str, str]; dataset: str | None
    aliases: list[str]            # LLM-expanded synonyms for retrieval
    hypothesis_ref: str | None    # optional "H2" or free text

class Candidate(BaseModel):       # one prior-work hit, any source
    source: Literal["list","rts","scholar"]
    title: str; permalink: str    # Slack permalink or DOI/URL
    outcome: str | None; params: dict[str,str]
    rcs_summary: str | None       # filled by RCS pass

class Verdict(BaseModel):
    level: Literal["collision","near_miss","clear"]
    confidence: float             # <0.65 ⇒ demote to "clear" with a note (§13 calibration)
    collisions: list[Candidate]; literature: list[Candidate]
    hypothesis_hits: list[HypoHit]  # {hypo_row_id,title,status,evidence_counts}
    diff: list[DiffLine]            # {param, plan_value, prior_value, same: bool}
```

### 4.3 Experiment canvas page (`canvases.create` → id stored in the row's canvas column)
Deterministic markdown template — sections in fixed order so `canvases.edit` can target them:
`# {title}` / `## Goal` / `## Parameters` (table) / `## Timeline` (bullet: ts, author, permalink, one-liner) / `## Outcome` / `## Evidence links` (hypothesis ± polarity) / `## Provenance` (source permalinks; "compiled by Curie — every line cites its message").

---

## 5. External API contracts (exact call shapes)

### 5.1 RTS — `assistant.search.context`
```python
client.assistant_search_context(
    query="ESM OR ESM-2 OR protein language model fine-tune",  # alias-expanded, formatting stripped
    action_token=event.get("action_token"),   # REQUIRED with bot token; omit on user token
    channel_types=["public_channel"],
    content_types=["messages"],
    include_context_messages=True,            # surrounding thread comes back free
    limit=20, sort="score")
```
Budget: ≤3 calls/verdict — (1) method+aliases, (2) dataset/params clause via `term_clauses` CNF, (3) optional time-boxed sweep. Check `assistant.search.info` once at startup: if semantic search enabled, phrase query #1 as a natural-language question; else keyword mode (stemming yes, synonyms no — aliases do that work). Filter `is_author_bot` hits pointing at Curie's own messages. Verdict candidates from the **List come first**; RTS enriches (Glean pattern). Never persist RTS results (N2).

### 5.2 Thread context — `conversations.replies(channel, ts, limit=50)` on top-2 RTS hits only (Tier 3).

### 5.3 Lists
- `slackLists.create(name="Lab Record", schema=…)` — setup only.
- `slackLists.items.create(list_id, parent_item_id?, initial_fields=[{column_id, rich_text|select|user|date|message|canvas…}])`
- `slackLists.items.update(...)` — status flips, outcome, trust.
- Read/query: `slackLists.items.list(list_id)` then filter in-process (record count is small; avoids depending on server-side filter semantics).

### 5.4 Canvas — `canvases.create(title, document_content={type:"markdown", markdown})`, `canvases.edit(canvas_id, changes=[{operation:"replace", section_id?, document_content}])`, `canvases.sections.lookup` to find section ids.

### 5.5 scholar-mcp (our own FastMCP server; stdio-launched by the app, or HTTP)
```
search_literature(query: str, limit: int = 8) -> [{title, year, authors, doi, url, abstract_snippet, venue, cited_by, is_retracted}]
find_null_results(topic: str, limit: int = 8) -> same shape   # query augmented with negation heuristics
get_paper(doi_or_url: str) -> full metadata + abstract
```
Backends: OpenAlex `GET https://api.openalex.org/works?search=…&per-page=…` (no key; include `mailto` param, be a good citizen); bioRxiv `GET https://api.biorxiv.org/details/biorxiv/{from}/{to}/{cursor}`. `is_retracted` from OpenAlex `is_retracted` field (PaperQA2-style enrichment). 10 s timeout; on failure return `[]` + `degraded:true` (verdict renders a "literature unavailable" context line — never blocks).

### 5.6 Streaming (backend side of the §11 contract)
`chat.startStream(channel, thread_ts, task_display_mode="plan")` → `chat.appendStream(chunks=[{type:"task_update", task:{task_id,title,status,output?,sources?}} | {type:"markdown_text",…}])` → `chat.stopStream(blocks=<verdict card>)`. Blocks only at stop. Fallback if streaming unavailable (smoke test #4): plain message → single `chat.update` (≥3 s spacing).

---

## 6. Pipelines

### 6.1 Preflight (trigger A/B/C)
```
1  ack: reactions.add 👀 + assistant.threads.setStatus("checking the record…")
2  parse_plan      LLM → Plan (JSON mode; on parse failure → clarify message, stop)
3  check_plan      LLM → ordered steps from: list_query, rts_query(q), thread_pull(hit),
                   scholar_search(q), ledger_lookup(ref) — max 6 steps, validated against
                   whitelist, then EXECUTED DETERMINISTICALLY (PromptQL pattern; the LLM
                   never sees raw execution errors, the executor handles them)
4  gather          run steps; collect Candidates (List → RTS → replies → scholar)
5  RCS             per candidate (parallel, asyncio.gather): LLM one-para contextual
                   summary: "what does this actually say about THIS plan?" (PaperQA2)
6  verdict         LLM → Verdict (JSON mode) with calibration rules (§13)
7  render          stream task updates during 4-6; stopStream with verdict card (§11)
8  cleanup         reactions.remove 👀 / add ✅; setStatus("")
```
Per-verdict LLM budget: 1 parse + 1 plan + ≤6 RCS + 1 verdict ≈ 9 calls, small contexts.

### 6.2 Result logging (trigger D/E)
`reaction_added(test_tube)` or shortcut → fetch message (+ thread head via `conversations.replies`) → LLM extract `{experiment_ref|new, status, outcome, params?}` → match to existing row (title fuzzy + owner + recency; else create) → `items.update`/`items.create` (trust=`auto`) → append canvas Timeline/Outcome → post context line: *"✏️ Logged to Exp ‹title› — Failed. [Undo] [Verify ✓] [Link to hypothesis…]"*. **Undo** = revert stored pre-write field values (kept in-memory 15 min) . **Verify** = trust→`verified`. No confirm modal before the write (act-then-undo).

### 6.3 Ambient classifier (trigger C, `CURIE_MODE=full` only)
Cheap LLM gate: "is this message an experiment plan? yes/no + confidence". Fire Preflight only ≥0.8; else silent. Never respond twice to a message already handled via Trigger A.

### 6.4 Ledger
- `track hypothesis:` → parent row (kind=hypothesis, status=open) + ack card.
- Evidence link: on verdict/logging, LLM proposes `{hypothesis_row, polarity}` → **confirm button** (writes are cheap to propose, links change meaning — this is the one place we confirm-first) → child-row `polarity` set / paper appended to hypothesis canvas.
- Rollup after any evidence change: `supports≥2 and contrasts==0 → supported`; `contrasts≥2 and supports==0 → refuted`; else `open`. Deterministic function, unit-tested; LLM never sets status.
- Evidence age: rollup stamps `updated`; ledger queries older than 12 months render "aging evidence — re-verify?" (Guru).

### 6.5 First-run setup
`app_home_opened` with no `CURIE_LIST_ID`, or `@Curie setup` → create List (4.1), pin a "Test Curie in 60 seconds" canvas to the channel, persist ids to config, post welcome (copy in frontend.md).

---

## 7. Cross-cutting

**7.1 Errors.** Every listener wrapped: user-facing failures post a human message with a retry button (copy in frontend.md §E); `setStatus("")` always cleared in `finally`. RTS 429 → single retry after `Retry-After`, then "rate-limited, try again in a minute". scholar-mcp failure → degraded verdict, never a block.
**7.2 Rate limits.** Client-side token buckets: RTS 3/verdict; `chat.update` 1 per 3 s per message; Lists Tier 2/3 with jittered backoff on `ratelimited`.
**7.3 Idempotency.** Dedup key = `(channel, message_ts, trigger)` in an in-memory TTL set; reaction spam or Bolt redelivery can't double-log.
**7.4 LLM interface.** One module `llm/client.py`: `complete(task: str, system: str, user: str, json_schema: dict|None)`; JSON mode validated by pydantic; 1 retry on validation failure then deterministic fallback (§13). All prompts in `prompts/*.md`, versioned.
**7.5 Observability.** Per response log line (local file, metadata only — no Slack content): `{trigger, latency_ms, rts_calls, llm_calls, verdict_level, confidence, fallback_used}`.
**7.6 Security.** Never log tokens or message bodies; user token only ever used server-side for RTS; deny Trigger C outside `CURIE_CHANNEL_ID`; prompt-injection posture — retrieved Slack/literature text is data, never instructions (delimited in prompts; write-actions never triggered by retrieved content).

---

## 8. Eval harness (`eval/`)

Fixtures: `eval/cases.yaml`, ≥40 entries: `{plan_text, expected_level, expected_collision_ref?, note}` across landmines (seeded exact-collisions), near-misses (one param differs), clears, off-domain ("testing a CNN on MNIST"), adversarial (prompt-injection-ish plan text), ambiguous. Runner: `python -m eval.run` executes the full pipeline against the seeded sandbox, prints a confusion matrix + per-case diffs, exits non-zero on any **false collision** (the unforgivable error; false "clear" on a near-miss is tolerable). Run on every change from July 10 PM onward; final numbers go in README and the demo video.

## 9. Seed script (`seed/`)

Populates the sandbox with ~6 months of realistic ML-lab history **posted as 2–3 dummy member accounts** (user tokens in env) — never as the bot (RTS may exclude bot-authored messages by default; that alone can kill the demo). Content: `#experiments` (plans, run chatter, failures WITH reasons), `#paper-club`, `#general`; 5–6 landmine configs a judge will plausibly re-type; 3 hypotheses + 8 linked experiments (List rows seeded via API after setup); a few bridge-format run-record messages. Deterministic from `seed/lab_story.yaml` so eval fixtures reference stable content. Label the workspace as a simulated lab (description + channel topic).

## 10. Deployment & runbook

```
slack login → slack create prior (Bolt Python assistant template) → configure manifest (§3)
→ toggle Agents & AI Apps + install → .env (§3.2) → slack run   # Socket Mode, no public URL
python -m seed.run      # once
python -m eval.run      # gate
```
Judge access: invite slackhack@salesforce.com + testing@devpost.com as **Members**; verify with a fresh non-admin test account first.

## 11. Backend↔frontend contract

Backend emits only these five payload types; `frontend.md` owns their rendering, copy, and states:
`stream_plan` (task list w/ per-task sources) · `verdict_card` (Verdict object) · `log_receipt` (context line + Undo/Verify/Link) · `ledger_view` (hypothesis rollups) · `error_card` (code + retry action). Block Kit JSON for each lives in frontend.md §C; backend fills slots, never invents layout.

## 12. Smoke tests (run BEFORE building — day one, ~30 min)

1. `app_mention` payload contains `action_token`? (also: mention inside a thread reply?)
2. Bot-token `assistant.search.context` + that token returns a seeded message?
3. Seeded **user-authored** vs bot-authored messages both searchable? (`include_bots` behavior)
4. `chat.startStream` with `task_display_mode="plan"` works on this sandbox? (else fallback §5.6)
5. User-token RTS without action_token works? (Trigger C viability)
6. `slackLists.create` with §4.1 schema + child row + canvas column end-to-end?
7. `assistant.search.info` → semantic or keyword-only?
Record results in README; they select between primary paths and pre-registered fallbacks (§14).

## 13. Verdict calibration rules (encoded in the verdict prompt + executor)

- "Clear" is the confident default. A collision REQUIRES ≥1 candidate whose RCS summary explicitly matches method AND (dataset or ≥2 params).
- `confidence < 0.65` → demote to `clear` + context line "1 loosely-related thread — view".
- Off-domain plans (no candidates from any source) short-circuit to `clear` WITHOUT a verdict LLM call.
- Deterministic fallback on any LLM/JSON failure: "I couldn't complete the check — [Retry]" (never a guessed verdict).

## 14. Kill-switches & fallbacks (pre-registered)

| Risk (smoke test) | Fallback |
|---|---|
| RTS keyword match unreliable (#2/#7) | Collision search via `conversations.history` over #experiments; RTS remains on Q&A path |
| Streaming absent (#4) | 👀 + placeholder + single `chat.update` card |
| Lists API gap (#6) | Master canvas index table instead of List (`CURIE_MODE=preflight_only` hides ledger) |
| Ledger slips past Sat noon | Ship experiment record only; hypotheses stay in seed-data pitch |
| Ambient classifier flaky | Ship Triggers A/B/D/E only |

## 15. Build order (maps to the July calendar)

1. Smoke tests (§12) → 2. seed (§9) → 3. Preflight plain-text E2E (§6.1 steps 1-6, no Block Kit) → 4. scholar-mcp (§5.5) → 5. eval harness (§8) + calibration (§13) → 6. record + logging (§6.2) → 7. streaming + cards (§11, with frontend.md) → 8. ledger (§6.4) → 9. App Home/onboarding (§6.5) → 10. hardening (§7) → freeze, video, submit.
