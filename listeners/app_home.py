"""app_home.py — App Home dashboard (frontend.md §7; shape: docs/platform/api-shapes-verified.md).

`app_home_opened` (Home tab ONLY — the Messages tab is the agent_view DM loop, not ours to publish
over) -> views.publish a per-user Home: header + promise, stats counted live from the Lab Record
(via tools.record_store, the sanctioned List read path), last-5 recent activity, the three
gestures, and controls. First-run (CURIE_LIST_ID unset) replaces stats with the §9 setup CTA.

Bot token only. Every Slack call is failure-tolerant: the handlers never raise, and a failed
stats read degrades to the setup/empty copy instead of fake numbers. Collisions-caught is an
in-process counter (`note_collision()`, wired from the verdict path later) — 0 when unknown,
never invented.
"""
from __future__ import annotations
import time

from tools import record_store as rs
from pipeline import ledger

# ---- copy (frontend.md §7 layout, §9 deck verbatim, §1 product promise) -------------------
HEADER = "Curie — your lab's memory"
PROMISE = "No experiment starts blind. Curie is the lab's memory — it writes itself."
STATS = "*{ex}* experiments tracked · *{hy}* hypotheses · *{co}* collisions caught this month"
SETUP_CTA = "Set up Curie"
SETUP_COPY = "I'll create your Lab Record and show you how to use me — takes 30 seconds."
SETUP_NOTE = ("Setup isn't automated from this button yet — in the repo, run "
              "`python -m seed.seed_list`, put the printed `CURIE_LIST_ID` in `.env`, "
              "and restart me. This tab refreshes each time you open it.")
RECENT_HEADING = "*Recent activity*"
RECENT_EMPTY = "Nothing logged yet — react 🧪 on a result message to log it."
LEDGER_HEADING = "*Where the lab stands*  ·  every claim, one click from its evidence"
_STATUS_EMOJI = {"supported": "🟢", "refuted": "🔴", "open": "🟡"}
HOW_TO = (
    "*How to use Curie*\n"
    "• *Check a plan* — mention `@Curie` with an experiment plan; I check it against the "
    "lab record, Slack history, and the literature.\n"
    "• *Log a result* — react 🧪 on a result message; I write it to the Lab Record.\n"
    "• *Track a bet* — `@Curie track hypothesis: <your claim>` adds it to the hypothesis ledger."
)
OPEN_RECORD = "Open the Lab Record"
RERUN_SETUP = "Re-run setup"

# ---- collisions-caught counter (in-memory; resets on restart — honest, never faked) --------
_COLLISIONS = {"month": "", "count": 0}


def note_collision() -> None:
    """Increment the value counter. Call when a preflight verdict lands as a collision."""
    month = time.strftime("%Y-%m")
    if _COLLISIONS["month"] != month:
        _COLLISIONS["month"], _COLLISIONS["count"] = month, 0
    _COLLISIONS["count"] += 1


def _collisions_this_month() -> int:
    return _COLLISIONS["count"] if _COLLISIONS["month"] == time.strftime("%Y-%m") else 0


def register(app):
    @app.event("app_home_opened")
    def handle_app_home_opened(event, client, logger):
        try:
            if event.get("tab") != "home":     # Messages tab = agent_view chat; publish Home only
                return
            user = event.get("user")
            if user:
                _publish(client, user, logger)
        except Exception:                      # never a crash out of the handler
            logger.exception("app_home_opened: publish failed")

    @app.action("home_setup")
    def handle_home_setup(ack, body, client, logger):
        """Minimal stub: refresh the dashboard and say how setup actually runs (no fake progress)."""
        ack()
        try:
            user = (body.get("user") or {}).get("id")
            if user:
                _publish(client, user, logger, note=SETUP_NOTE)
        except Exception:
            logger.exception("home_setup failed")

    @app.action("home_open_record")
    def handle_home_open_record(ack):
        ack()   # URL button navigates client-side; ack just silences Bolt's unhandled-action warning


# ---- view assembly (pure except the List read + URL derivation) ---------------------------

def _publish(client, user_id: str, logger, note: str = ""):
    blocks = _home_blocks(client)
    if note:
        blocks.append(_ctx(note))
    try:
        client.views_publish(user_id=user_id, view={"type": "home", "blocks": blocks})
    except Exception:
        logger.exception("views.publish failed")


def _home_blocks(client) -> list[dict]:
    blocks = [_h(HEADER), _ctx(PROMISE)]
    store = rs.RecordStore(client)             # env CURIE_LIST_ID; read-only

    if not store.available():                  # first-run / empty state (frontend §7 F7)
        blocks += [
            _s(f"*{SETUP_CTA}*\n{SETUP_COPY}"),
            {"type": "actions", "elements": [
                {"type": "button", "style": "primary",
                 "text": {"type": "plain_text", "text": SETUP_CTA, "emoji": True},
                 "action_id": "home_setup"},
            ]},
            _div(),
            _s(HOW_TO),
        ]
        return blocks

    rows = [rs._row_fields(r) for r in store._items()]   # shared read path (as reaction_added)
    hypotheses = sum(1 for f in rows if (f.get("kind") or "").lower() == "hypothesis")
    experiments = len(rows) - hypotheses       # non-hypothesis = experiment (record_store semantics)

    blocks.append(_s(STATS.format(ex=experiments, hy=hypotheses, co=_collisions_this_month())))
    ledger_md = _belief_ledger_lines(client)
    if ledger_md:                              # the crown: hypothesis roll-up, right under the stats
        blocks.append(_div())
        blocks.append(_s(LEDGER_HEADING + "\n" + ledger_md))
    blocks.append(_div())
    blocks.append(_s(RECENT_HEADING + "\n" + _recent_lines(rows)))
    blocks.append(_div())
    blocks.append(_s(HOW_TO))

    elements = []
    url = _list_url(client, store.list_id)
    if url:                                    # never a non-URL in a button (cards.py lesson)
        elements.append({"type": "button",
                         "text": {"type": "plain_text", "text": OPEN_RECORD, "emoji": True},
                         "url": url, "action_id": "home_open_record"})
    elements.append({"type": "button",
                     "text": {"type": "plain_text", "text": RERUN_SETUP, "emoji": True},
                     "action_id": "home_setup"})
    blocks.append({"type": "actions", "elements": elements})
    return blocks


def _belief_ledger_lines(client) -> str:
    """The hypothesis roll-up (the ledger 'crown'): each tracked belief + status + evidence counts.
    Reuses pipeline.ledger's deterministic grouping/rollup so App Home and the 'where the lab
    stands' card never disagree. Returns '' on any failure or when nothing is tracked."""
    try:
        hypos, children = ledger._group(ledger._read_rows(rs.RecordStore(client)))
    except Exception:
        return ""
    if not hypos:
        return ""
    lines = []
    for h in hypos[:6]:
        kids = children.get(h.get("row_id"), [])
        status = ledger.rollup(h, kids)
        sup = sum(1 for k in kids if (k.get("polarity") or "").strip().lower() == "supports")
        con = sum(1 for k in kids if (k.get("polarity") or "").strip().lower() == "contrasts")
        title = (h.get("title") or "(hypothesis)").strip()[:90]
        lines.append(f"{_STATUS_EMOJI.get(status, '🟡')} *{title}* — {status.capitalize()}"
                     f"  ·  🟢 {sup} · 🔴 {con}")
    return "\n".join(lines)


def _recent_lines(rows: list[dict]) -> str:
    """Last 5 experiments (title + status), newest `updated` first; missing dates sort last."""
    recent = [f for f in rows if (f.get("kind") or "").lower() != "hypothesis"]
    recent.sort(key=lambda f: f.get("updated") or "", reverse=True)   # ISO dates sort lexically
    lines = []
    for f in recent[:5]:
        title = (f.get("title") or "(untitled experiment)").strip()[:80]
        status = (f.get("status") or "").strip()
        lines.append(f"• *{title}* — {status.capitalize()}" if status else f"• *{title}*")
    return "\n".join(lines) if lines else RECENT_EMPTY


# ---- List URL (Lists are files: files.info permalink first, workspace-URL fallback) --------

def _list_url(client, list_id: str) -> str:
    if not list_id:
        return ""
    cached = getattr(client, "_curie_list_url", "")
    if cached:
        return cached
    url = ""
    try:                                       # files:read is in our bot scopes (backend §3.1)
        r = client.files_info(file=list_id)
        data = r.data if hasattr(r, "data") else r
        url = ((data.get("file") or {}).get("permalink")) or ""
    except Exception:
        url = ""
    if not url.startswith("http"):
        try:
            auth = client.auth_test()
            base = (auth.get("url") or "").rstrip("/")
            team = auth.get("team_id") or ""
            url = f"{base}/lists/{team}/{list_id}" if base and team else ""
        except Exception:
            url = ""
    if not url.startswith("http"):
        return ""                              # underivable -> omit the button (task contract)
    try:
        client._curie_list_url = url           # cache successes only; failures retry next open
    except Exception:
        pass
    return url


# ---- block helpers ------------------------------------------------------------------------

def _h(text: str) -> dict:
    return {"type": "header", "text": {"type": "plain_text", "text": text[:150], "emoji": True}}


def _s(md: str) -> dict:
    return {"type": "section", "text": {"type": "mrkdwn", "text": md[:2900]}}


def _ctx(md: str) -> dict:
    return {"type": "context", "elements": [{"type": "mrkdwn", "text": md[:1900]}]}


def _div() -> dict:
    return {"type": "divider"}
