"""ledger.py — hypothesis ledger: track bets, roll up evidence, render "where does the lab stand?"

backend.md §6.4 (rollup rules) + frontend.md §4D (ledger_view layout) + §9 (copy deck, verbatim).
pipeline lane: pure-ish logic — deps (record, client) are INJECTED, no global clients, and NO LLM
calls anywhere in this module. The ledger is deterministic; the LLM never sets a hypothesis status.

The listener routes these BEFORE preflight:
    claim = ledger.is_track_hypothesis(plan_text)   # "@Prior track hypothesis: <claim>"
    ledger.is_stand_query(plan_text)                # "where does the lab stand?" / "lab status" …

Data model (backend §4.1): hypotheses are PARENT rows (kind=hypothesis) in the Lab Record List;
experiments are child rows (parent_item_id) whose Evidence `polarity` select (supports/contrasts/
mentions) is the rollup input. Reads reuse tools.record_store's row/field flatteners (the
sanctioned List read path, shared with reaction_added and app_home). The one write here
(slackLists.items.create, BOT token) addresses columns via the ids cached in
seed/curie_list_schema.json, falling back to schema keys as ids (seed_list pattern).

Failure posture (§7.1): nothing here raises to the caller — a failed write returns a human
string, a failed/empty read renders the §9 empty state. No Slack content is ever logged.
"""
from __future__ import annotations
import datetime
import json
import os
import pathlib
import re
from collections import defaultdict
from typing import Optional

from tools import record_store as rs

# ---- copy (frontend.md §4D layout + §9 deck; voice: plain, specific, no exclamation) --------
HEADER = "Where the lab stands"
# §9 verbatim, encoded for mrkdwn: &lt;/&gt; render as < > (a raw "<your claim>" would be
# swallowed as a broken link control sequence).
LEDGER_EMPTY = ("No hypotheses tracked yet. Start one: "
                "`@Prior track hypothesis: &lt;your claim&gt;`")
LEDGER_FOOTER = "Every claim links to its evidence · compiled by Curie from #experiments"
# Weekly belief-digest copy (used by the run-now path + the best-effort Monday schedule).
DIGEST_HEADER = "This week's belief changes"
DIGEST_EMPTY = ("No beliefs changed this week — nothing new was supported or refuted. "
                "The lab's priors held. Ask “where does the lab stand?” for the full map.")
DIGEST_FOOTER = "Compiled by Curie from #experiments · every Monday"
AGING_NOTE = "evidence {months} mo old — re-verify?"   # §4D Guru mechanic: newest evidence >12 mo
NO_EVIDENCE = "no evidence linked yet"
TRACK_ACK = ("🟡 Tracking: *{claim}* — Open. Results logged with 🧪 roll up as evidence. "
             "Ask “where does the lab stand?” any time.")
TRACK_EMPTY = ("Give the hypothesis a claim — e.g. "
               "`@Prior track hypothesis: curriculum ordering improves convergence`.")
TRACK_FAIL = ("⚠️ I couldn't add that hypothesis to the ledger — the write didn't go through. "
              "Give it a minute, then try again.")
NOT_SET_UP = "Curie isn't set up in this workspace yet — open my App Home to finish setup."  # §4E

_STATUS_EMOJI = {"refuted": "🔴", "supported": "🟢", "open": "🟡"}   # §3 verdict colors
_STALE_MONTHS = 12          # §4D: aging nudge when newest evidence is older than this
_MAX_SECTIONS = 20          # well under Slack's 50-block cap; the ledger stays scannable

_SCHEMA_PATH = pathlib.Path(__file__).parent.parent / "seed" / "curie_list_schema.json"


# ---- 1. gesture detection (deterministic, runs before preflight) ----------------------------

# Tolerates a leading mention remnant, "please", en/em dashes, and multi-line claims.
_TRACK_RE = re.compile(
    r"\btrack\s+(?:a\s+|the\s+)?hypothesis\s*[:\-–—]\s*(.+)$",
    re.IGNORECASE | re.DOTALL)

_STAND_PHRASES = (
    "where does the lab stand", "where the lab stands", "where do we stand",
    "what have we tried", "what has the lab tried", "what've we tried",
    "lab status", "status of the lab", "state of the lab",
    "hypothesis ledger", "show the ledger", "open the ledger", "show ledger",
)


def is_track_hypothesis(text) -> Optional[str]:
    """Return the claim from `track hypothesis: <claim>`, else None."""
    m = _TRACK_RE.search(text or "")
    if not m:
        return None
    claim = re.sub(r"\s+", " ", m.group(1)).strip().strip("\"'“”").strip()
    return claim or None


def is_stand_query(text) -> bool:
    """True for ledger-view asks: 'where does the lab stand', 'what have we tried', 'lab status'…

    Conservative on purpose — a false positive here would hijack a plan check (routing runs
    before preflight). Bare 'ledger' only counts when it's essentially the whole message.
    """
    norm = re.sub(r"\s+", " ", (text or "").lower().replace("’", "'")).strip(" ?!.")
    if not norm:
        return False
    if any(p in norm for p in _STAND_PHRASES):
        return True
    return bool(re.fullmatch(r"(?:the |our )?ledger", norm))


# ---- 2. register a hypothesis (parent row: kind=hypothesis, status=open) --------------------

def register_hypothesis(claim: str, *, record, client) -> str:
    """Create the parent row via slackLists.items.create (bot token). Returns the ack string.

    Never raises: any failure returns a human message (§7.1). No parent_item_id — hypotheses
    are top-level rows; experiments attach underneath them (seed_list / backend §4.1).
    """
    claim = (claim or "").strip()
    if not claim:
        return TRACK_EMPTY
    list_id = _list_id(record)
    if not list_id:
        return NOT_SET_UP
    cols = _columns()

    def cid(key: str) -> str:                    # keys double as ids when no cache (seed_list)
        return cols.get(key, key)

    fields = [
        {"column_id": cid("title"), "rich_text": [_rt(claim)]},
        {"column_id": cid("kind"), "select": ["hypothesis"]},
        {"column_id": cid("status"), "select": ["open"]},
        {"column_id": cid("trust"), "select": ["auto"]},
        {"column_id": cid("updated"), "date": [_today()]},   # date is an ARRAY (verified live)
    ]
    try:
        r = client.api_call("slackLists.items.create",
                            json={"list_id": list_id, "initial_fields": fields})
        data = r.data if hasattr(r, "data") else r
        if not (data or {}).get("ok", True):
            return TRACK_FAIL
    except Exception:
        return TRACK_FAIL
    return TRACK_ACK.format(claim=_esc(claim)[:200])


# ---- 3. rollup (backend §6.4 — deterministic, unit-testable, no LLM) -------------------------

def rollup(hyp, experiments) -> str:
    """supports>=2 and contrasts==0 -> 'supported'; contrasts>=2 and supports==0 -> 'refuted';
    else 'open'. Evidence-only by design: `hyp` (its stored status included) never decides —
    the LLM/stale rows must not outvote the evidence. Accepts dicts or objects with .polarity.
    """
    supports = contrasts = 0
    for e in experiments or []:
        p = _polarity_of(e)
        if p == "supports":
            supports += 1
        elif p == "contrasts":
            contrasts += 1
    if supports >= 2 and contrasts == 0:
        return "supported"
    if contrasts >= 2 and supports == 0:
        return "refuted"
    return "open"


def _polarity_of(e) -> str:
    v = e.get("polarity", "") if isinstance(e, dict) else getattr(e, "polarity", "")
    return (v or "").strip().lower()


# ---- 4. ledger_view blocks (frontend §4D — the payoff screen) --------------------------------

def ledger_view_blocks(record) -> list[dict]:
    """Read the List through `record` (RecordStore-shaped), group experiments under their
    hypothesis, and render §4D: header, one section per hypothesis (status emoji + counts +
    evidence permalinks + aging nudge), footer. Empty/unreadable record -> §9 empty state.
    """
    hypos, children = _group(_read_rows(record))
    blocks = [_h(HEADER)]
    if not hypos:
        blocks.append(_s(LEDGER_EMPTY))
        return blocks

    _sort_by_activity(hypos, children)           # §4D: ordered by activity, newest first
    for hyp in hypos[:_MAX_SECTIONS]:
        blocks.append(_s(_hypo_md(hyp, children.get(hyp["row_id"], []))))
    if len(hypos) > _MAX_SECTIONS:
        blocks.append(_ctx(f"…and {len(hypos) - _MAX_SECTIONS} more in the Lab Record"))
    blocks.append(_ctx(LEDGER_FOOTER))
    return blocks


# ---- weekly belief digest (used by listeners.standing: run-now + Monday schedule) ------------

def belief_digest_blocks(record) -> list[dict]:
    """Every hypothesis that has RESOLVED (rollup -> supported/refuted), with its evidence counts,
    framed as this week's belief changes. Empty state when nothing has resolved.

    Reuses the same read/group/rollup path as the ledger view. We never persist Slack data, so
    there's no per-week diff store — this shows where beliefs currently stand (the VO carries the
    'every Monday' cadence). Refutations first (most actionable). Never raises.
    """
    try:
        hypos, children = _group(_read_rows(record))
    except Exception:
        hypos, children = [], {}

    resolved = []
    for hyp in hypos:
        kids = children.get(hyp.get("row_id"), [])
        status = rollup(hyp, kids)
        if status in ("supported", "refuted"):
            resolved.append((hyp, kids, status))

    blocks = [_h(DIGEST_HEADER)]
    if not resolved:
        blocks.append(_s(DIGEST_EMPTY))
        blocks.append(_ctx(DIGEST_FOOTER))
        return blocks

    resolved.sort(key=lambda t: 0 if t[2] == "refuted" else 1)   # refutations first
    for hyp, kids, status in resolved[:_MAX_SECTIONS]:
        emoji = _STATUS_EMOJI.get(status, "🟡")
        supports = sum(1 for k in kids if k.get("polarity") == "supports")
        contrasts = sum(1 for k in kids if k.get("polarity") == "contrasts")
        title = _esc(hyp.get("title") or "(untitled hypothesis)")[:200]
        blocks.append(_s(f"{emoji} *{title}* — {status.capitalize()}\n"
                         f"🟢 {supports} for · 🔴 {contrasts} against"))
    blocks.append(_ctx(DIGEST_FOOTER))
    return blocks


def _hypo_md(hyp: dict, kids: list[dict]) -> str:
    """One §4D section: '🔴 *claim* — Refuted' + counts/aging line + up to 3 evidence links."""
    status = rollup(hyp, kids)
    emoji = _STATUS_EMOJI.get(status, "🟡")
    title = _esc(hyp.get("title") or "(untitled hypothesis)")[:200]
    running = sum(1 for k in kids if k.get("status") == "running")

    head = f"{emoji} *{title}* — {status.capitalize()}"
    if status == "open" and running:
        head += f" ({running} running)"
    lines = [head]

    if kids:
        supports = sum(1 for k in kids if k.get("polarity") == "supports")
        contrasts = sum(1 for k in kids if k.get("polarity") == "contrasts")
        counts = f"🟢 {supports} support · 🔴 {contrasts} contrast"
        months = _months_stale(kids)
        if months is not None and months > _STALE_MONTHS:
            counts += " · " + AGING_NOTE.format(months=months)
        lines.append(counts)
    else:
        lines.append(NO_EVIDENCE)

    links = [f"<{k['link']}|{_esc(k.get('title') or 'experiment')[:40]}>"
             for k in kids if _is_url(k.get("link"))][:3]
    if links:
        lines.append("  ".join(links))
    return "\n".join(lines)


# ---- List reading + grouping (reuses record_store's flatteners; failure -> []) ---------------

def _read_rows(record) -> list[dict]:
    try:
        if record is None:
            return []
        if hasattr(record, "available") and not record.available():
            return []
        return [r for r in (record._items() or []) if isinstance(r, dict)]
    except Exception:
        return []


def _group(rows: list[dict]) -> tuple[list[dict], dict[str, list[dict]]]:
    """Split rows into hypothesis entries and {parent row id -> child experiment entries}."""
    hypos: list[dict] = []
    children: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        fields = rs._row_fields(row)
        entry = {
            "row_id": _row_id(row),
            "title": (fields.get("title") or "").strip(),
            "status": (fields.get("status") or "").strip().lower(),
            "polarity": (fields.get("polarity") or "").strip().lower(),
            "updated": (fields.get("updated") or "").strip(),
            "link": _source_link(row),
        }
        if (fields.get("kind") or "").lower() == "hypothesis":
            hypos.append(entry)
        else:                                    # non-hypothesis = experiment (record_store semantics)
            pid = _parent_of(row)
            if pid:
                children[pid].append(entry)      # orphans live in the List, not the ledger view
    return hypos, children


def _sort_by_activity(hypos: list[dict], children: dict[str, list[dict]]) -> None:
    def newest(h: dict) -> datetime.date:
        dates = [_parse_date(h.get("updated"))]
        dates += [_parse_date(k.get("updated")) for k in children.get(h["row_id"], [])]
        dates = [d for d in dates if d]
        return max(dates) if dates else datetime.date.min
    hypos.sort(key=newest, reverse=True)


def _row_id(row: dict) -> str:
    return row.get("id") or row.get("item_id") or ""


def _parent_of(row: dict) -> str:
    """Child rows carry their hypothesis's row id; be liberal about where the API puts it.
    VERIFIED LIVE (Jul 10): slackLists.items.list returns it as `parent_record_id`."""
    for k in ("parent_record_id", "parent_item_id", "parent_id", "parent_row_id"):
        v = row.get(k)
        if isinstance(v, str) and v:
            return v
    v = row.get("parent") or row.get("parent_item")
    if isinstance(v, str):
        return v
    if isinstance(v, dict):
        return v.get("id") or v.get("item_id") or ""
    return ""


def _source_link(row: dict) -> str:
    """Permalink from the `source` message column (record_store flattens text, not message[])."""
    fields = row.get("fields") or row.get("column_values") or []
    if isinstance(fields, dict):
        fields = list(fields.values())
    src_col = _columns().get("source", "")
    for f in fields:
        if not isinstance(f, dict):
            continue
        key = f.get("key") or f.get("column_key")
        if key != "source" and not (src_col and f.get("column_id") == src_col):
            continue
        for v in (f.get("message") or []):
            if isinstance(v, str) and _is_url(v):
                return v
            if isinstance(v, dict):
                u = v.get("permalink") or v.get("url") or ""
                if _is_url(u):
                    return u
        t = f.get("text")
        if isinstance(t, str) and _is_url(t):
            return t
    return ""


# ---- evidence aging (§4D: quiet trust signal, never an alarm) --------------------------------

def _months_stale(kids: list[dict]) -> Optional[int]:
    """Months since the NEWEST child evidence; None when no evidence carries a date."""
    dates = [d for d in (_parse_date(k.get("updated")) for k in kids) if d]
    if not dates:
        return None
    days = (datetime.date.today() - max(dates)).days
    return None if days < 0 else round(days / 30.44)


def _parse_date(s) -> Optional[datetime.date]:
    try:
        return datetime.date.fromisoformat((s or "").strip()[:10])
    except Exception:
        return None


# ---- column ids / list id (config cache, not Slack data) -------------------------------------

_SCHEMA_CACHE: dict = {}


def _schema() -> dict:
    global _SCHEMA_CACHE
    if not _SCHEMA_CACHE:
        try:
            _SCHEMA_CACHE = json.loads(_SCHEMA_PATH.read_text())
        except Exception:
            _SCHEMA_CACHE = {}
    return _SCHEMA_CACHE


def _columns() -> dict:
    return _schema().get("columns") or {}


def _list_id(record) -> str:
    return (getattr(record, "list_id", "") or os.environ.get("CURIE_LIST_ID")
            or _schema().get("list_id", ""))


# ---- small helpers (Block Kit style matches tools/cards.py) -----------------------------------

def _h(text: str) -> dict:
    return {"type": "header", "text": {"type": "plain_text", "text": text[:150], "emoji": True}}


def _s(md: str) -> dict:
    return {"type": "section", "text": {"type": "mrkdwn", "text": md[:2900]}}


def _ctx(md: str) -> dict:
    return {"type": "context", "elements": [{"type": "mrkdwn", "text": md[:1900]}]}


def _is_url(s) -> bool:
    return bool(s) and isinstance(s, str) and s.startswith("http")


def _esc(s: str) -> str:
    """Escape Slack mrkdwn control characters in user/record text (titles, claims)."""
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _rt(text: str) -> dict:
    """One Block Kit rich_text block — required payload shape for text/rich_text columns."""
    return {"type": "rich_text", "elements": [
        {"type": "rich_text_section", "elements": [{"type": "text", "text": text or ""}]}]}


def _today() -> str:
    return datetime.date.today().isoformat()
