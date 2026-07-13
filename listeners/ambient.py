"""ambient.py — autonomy in #experiments: ingest run-records posted by OTHER agents (e.g. Claude
Science over the Slack MCP) and, flag-gated, preflight plain plan messages with no @mention.

`message.channels` handler (MASTER-PLAN). Guards: channel == CURIE_CHANNEL_ID (when set), ignore
Curie's OWN messages (bot_id / user), dedup on ts. The handler never raises.

Two behaviors:
  1) Run-record ingest — text starts with "📊 Run" (the MASTER-PLAN contract). Parse
     {experiment, status, outcome, params} from the `key: value | key: value` shape, update the
     matching List row + Evidence polarity via pipeline.logging.record_result (the shared write
     path reused from the 🧪 flow), then recompute the parent hypothesis rollup — and if its status
     flips, post a proactive belief-change alert (the real-time autonomy star). Nobody filed a form.
  2) Ambient preflight — when _AMBIENT_ON (module flag, set by listeners.standing) and a HUMAN
     posts a plan-shaped message with no @mention, preflight it anyway and post the verdict card
     (reuses pipeline.preflight + tools.cards). Channel messages carry no action_token, so RTS is
     unavailable here — preflight runs over the Lab Record + literature only (degrades cleanly).

No Slack content is logged.
"""
from __future__ import annotations
import os, re, time, logging, threading
from typing import Optional

from pipeline import logging as reclog
from pipeline import ledger
from pipeline import preflight
from tools.record_store import RecordStore
from tools import record_store as rs
from tools.cards import verdict_blocks
from tools.rts import RTS

# ---- module flag: ambient preflight (listeners.standing flips this) -------------------------
_AMBIENT_ON = False


def set_ambient_preflight(on: bool) -> None:
    global _AMBIENT_ON
    _AMBIENT_ON = bool(on)


def ambient_preflight_on() -> bool:
    return _AMBIENT_ON


# ---- copy / patterns ------------------------------------------------------------------------
BELIEF_ALERT = ("⚠️ Heads up — your belief *{claim}* just changed → *{status}*. "
                "New evidence: {experiment} {run_status}.")
_RUN_PREFIX = "📊 Run"
# Robust run-record gate: an optional leading 📊 / :bar_chart: shortcode (or none), then "Run",
# any case. In production the event text can carry the emoji as the ":bar_chart:" shortcode rather
# than the unicode glyph — an exact-unicode startswith("📊 Run") silently missed those, so ingest
# never ran. Matching the shortcode form here is the fix; the parser was already emoji-agnostic.
_RUN_RE = re.compile(r"^\s*(?:📊|:bar_chart:|:chart[a-z_]*:)?\s*run\b", re.IGNORECASE)


def _looks_like_run_record(text: str) -> bool:
    return bool(_RUN_RE.match(text or ""))


_SEEN: dict[str, float] = {}
_SEEN_TTL = 300.0

_PLAN_RE = re.compile(
    r"(?:\blr\b|\bbatch\b|\bepoch|\bsplit\b|fine[\- ]?tune|\blora\b|dropout|\brank\b|"
    r"\bmodel\b|\d+e-?\d|\bv\d\b)", re.IGNORECASE)

_STATUS_MAP = {
    "fail": "failed", "failed": "failed", "failure": "failed", "crash": "failed",
    "crashed": "failed", "nan": "failed", "error": "failed", "diverged": "failed",
    "success": "succeeded", "succeeded": "succeeded", "succeed": "succeeded",
    "pass": "succeeded", "passed": "succeeded", "done": "succeeded",
    "complete": "succeeded", "completed": "succeeded",
    "running": "running", "in_progress": "running", "in-progress": "running",
    "started": "running", "start": "running",
    "abandoned": "abandoned", "abandon": "abandoned", "killed": "abandoned",
    "cancelled": "abandoned", "canceled": "abandoned",
}


def register(app):
    @app.event("message")
    def handle_message(event, client, logger):
        try:
            print("CURIE-DIAG ambient msg arrived: subtype=%r has_bot_id=%s ch_is_curie=%s"
                  % (event.get("subtype"), bool(event.get("bot_id")),
                     event.get("channel") == os.environ.get("CURIE_CHANNEL_ID")), flush=True)
            if event.get("subtype") not in (None, "bot_message"):
                return                              # skip edits/joins/thread_broadcast/etc.
            channel = event.get("channel")
            ts = event.get("ts")
            if not channel or not ts:
                return
            curie_channel = os.environ.get("CURIE_CHANNEL_ID")
            if curie_channel and channel != curie_channel:
                return                              # scope to #experiments when configured
            own_bot_id, own_user = _own_identity(client)
            if _is_own(event, own_bot_id, own_user):
                return                              # never react to our own messages
            if _is_dup(ts):
                return
            text = (event.get("text") or "").strip()
            if not text:
                return

            if _looks_like_run_record(text):
                print("CURIE-DIAG ambient routing to run ingest (text_len=%s)" % len(text),
                      flush=True)
                _ingest_run_record(client, logger, channel, text)
                return

            if (_AMBIENT_ON and not event.get("bot_id") and _looks_like_plan(text)
                    and own_user and f"<@{own_user}>" not in text):
                _ambient_preflight(client, logger, event, channel, text)
        except Exception:
            logger.exception("ambient: message handler failed")


# ---- run-record poller (fallback ingest when message.channels isn't delivered) --------------
# Belt-and-suspenders. Some workspaces don't deliver message.channels over Socket Mode even with
# the event subscribed + channels:history granted + the bot in-channel (observed live on the
# Prior Lab dev sandbox: app_mention arrives, message.channels never does). conversations.history
# DOES work with the bot token, so we poll #experiments for new run-records and ingest them the
# same way the event handler would. Dedup shares _SEEN, so a record is never double-ingested if
# the event ever does start arriving. Daemon thread; never raises to the caller.

_POLL_SECONDS = float(os.environ.get("CURIE_POLL_SECONDS", "8"))
_poller_log = logging.getLogger("curie.run_poller")


def start_run_poller(app) -> None:
    channel = os.environ.get("CURIE_CHANNEL_ID")
    if not channel:
        print("CURIE-DIAG run-poller NOT started: CURIE_CHANNEL_ID unset", flush=True)
        return
    client = app.client

    def _loop():
        last_ts = "%.6f" % time.time()          # only ingest records posted AFTER startup
        print("CURIE-DIAG run-poller started (channel=%s every %ss)" % (channel, _POLL_SECONDS),
              flush=True)
        while True:
            try:
                r = client.conversations_history(channel=channel, oldest=last_ts, limit=25)
                data = r.data if hasattr(r, "data") else r
                msgs = data.get("messages", []) or []
                own_bot_id, own_user = _own_identity(client)
                for m in sorted(msgs, key=lambda x: float(x.get("ts", "0"))):
                    ts = m.get("ts")
                    if not ts:
                        continue
                    if float(ts) > float(last_ts):
                        last_ts = ts
                    if _is_own(m, own_bot_id, own_user) or _is_dup(ts):
                        continue
                    text = (m.get("text") or "").strip()
                    if not text:
                        continue
                    if _looks_like_run_record(text):
                        print("CURIE-DIAG run-poller -> ingest (ts=%s)" % ts, flush=True)
                        _ingest_run_record(client, _poller_log, channel, text)
                    elif (ambient_preflight_on() and not m.get("bot_id")
                          and _looks_like_plan(text) and own_user
                          and ("<@%s>" % own_user) not in text):
                        print("CURIE-DIAG run-poller -> ambient preflight (ts=%s)" % ts, flush=True)
                        _ambient_preflight(client, _poller_log, m, channel, text)
            except Exception:
                _poller_log.exception("run-poller iteration failed")
            time.sleep(_POLL_SECONDS)

    threading.Thread(target=_loop, name="curie-run-poller", daemon=True).start()


# ---- 1) run-record ingest -------------------------------------------------------------------

def _ingest_run_record(client, logger, channel, text):
    parsed = _parse_run_record(text)
    if not parsed:
        return
    status = _norm_status(parsed["status"])
    polarity = reclog.polarity_for(status)
    if not _match_query(parsed):
        return

    # Resolve the target row PARAM-AWARE (run-records are param-rich; title Jaccard alone can pick
    # the wrong sibling, e.g. the v2 LoRA row over the v1 full-FT row). None -> record_result will
    # match by title or create a new experiment row.
    row_id = _resolve_experiment_row(client, parsed)

    # Detect a belief flip BEFORE writing (rollup is evidence-only; simulate the one change).
    belief = (_belief_change_for_row(client, row_id, polarity)
              if row_id and polarity in ("supports", "contrasts") else None)

    res = reclog.record_result(client, title=_match_query(parsed), status=status,
                               outcome=parsed["outcome"], polarity=polarity, row_id=row_id)
    if not res.ok:
        return

    if belief:
        try:                                        # keep the hypothesis row's status honest
            if belief.get("hyp_row_id"):
                reclog.write_cells(client, belief["hyp_row_id"], {"status": belief["new"]})
        except Exception:
            pass
        _post_belief_alert(client, channel, belief,
                           parsed.get("experiment") or "a new run", status)


def _resolve_experiment_row(client, parsed: dict) -> Optional[str]:
    """Best experiment row for a run-record: rank by (# matching params, title similarity).
    Params (split/model/lr/batch…) are the decisive signal that separates sibling runs. Returns a
    row_id only when it clears a floor (>=1 param match OR >=0.5 title similarity), else None."""
    try:
        rows = RecordStore(client, os.environ.get("CURIE_LIST_ID"))._items()
    except Exception:
        return None
    if not rows:
        return None
    want = {_n(k): _n(v) for k, v in (parsed.get("params") or {}).items()}
    query = _match_query(parsed)
    best_id, best = None, (-1, -1.0)
    for r in rows:
        f = rs._row_fields(r)
        if (f.get("kind") or "").lower() == "hypothesis":
            continue                                # experiments only
        rp = {_n(k): _n(v) for k, v in rs._parse_params(f.get("params", "")).items()}
        pmatch = sum(1 for k, v in want.items() if rp.get(k) == v)
        score = (pmatch, reclog.similarity(query, f.get("title", "")))
        if score > best:
            best, best_id = score, (r.get("id") or r.get("item_id") or "")
    if best_id and (best[0] >= 1 or best[1] >= 0.5):
        return best_id
    return None


def _belief_change_for_row(client, row_id: str, new_polarity: str) -> Optional[dict]:
    """Would setting `row_id`'s polarity to `new_polarity` flip its parent hypothesis's rollup?
    Reads current state, finds the parent, simulates the one change in memory. None if no flip."""
    try:
        hypos, children = ledger._group(
            ledger._read_rows(RecordStore(client, os.environ.get("CURIE_LIST_ID"))))
    except Exception:
        return None
    for hyp in hypos:
        kids = children.get(hyp.get("row_id"), [])
        if not any(k.get("row_id") == row_id for k in kids):
            continue
        old = ledger.rollup(hyp, kids)
        sim = [dict(k, polarity=new_polarity) if k.get("row_id") == row_id else k for k in kids]
        new = ledger.rollup(hyp, sim)
        if old != new:
            return {"hyp_title": hyp.get("title", ""), "old": old, "new": new,
                    "hyp_row_id": hyp.get("row_id", "")}
        return None
    return None


def _n(s) -> str:
    return str(s).strip().lower()


def _parse_run_record(text: str) -> Optional[dict]:
    """`📊 Run <exp> | status: … | outcome: … | params: k=v, …` -> dict. Split on '|' first so
    outcome commas/colons survive; split each segment on the FIRST ':' only."""
    segs = [s.strip() for s in text.split("|")]
    if not segs:
        return None
    exp = re.sub(r"^[^0-9A-Za-z]*\bRun\b\s*", "", segs[0], flags=re.IGNORECASE).strip()
    fields: dict[str, str] = {}
    for seg in segs[1:]:
        if ":" in seg:
            k, v = seg.split(":", 1)
            fields[k.strip().lower()] = v.strip()
    status = fields.get("status", "")
    outcome = fields.get("outcome", "")
    params = rs._parse_params(fields.get("params", ""))     # shared 'k=v, k2=v2' parser
    if not exp and not status:
        return None
    return {"experiment": exp, "status": status, "outcome": outcome, "params": params}


def _match_query(parsed: dict) -> str:
    """Build a rich match string (experiment + params + outcome) so the title fuzzy-match in
    record_store/reaction_added can find the seeded experiment row (its title carries the params)."""
    parts = [parsed.get("experiment", "")]
    for k, v in (parsed.get("params") or {}).items():
        parts.append(f"{k} {v}")
    if parsed.get("outcome"):
        parts.append(parsed["outcome"])
    return " ".join(p for p in parts if p).strip()


def _norm_status(s: str) -> str:
    s = (s or "").strip().lower()
    if s in _STATUS_MAP:
        return _STATUS_MAP[s]
    return s if s in ("failed", "succeeded", "running", "abandoned") else "running"


def _post_belief_alert(client, channel, belief: dict, experiment: str, run_status: str):
    claim = ledger._esc(belief.get("hyp_title") or "(hypothesis)")[:200]
    text = BELIEF_ALERT.format(claim=claim, status=(belief.get("new") or "").capitalize(),
                               experiment=experiment, run_status=run_status)
    try:                                            # proactive -> top-level, not threaded
        client.chat_postMessage(channel=channel, text=text,
                                blocks=[{"type": "section",
                                         "text": {"type": "mrkdwn", "text": text}}])
    except Exception:
        pass


# ---- 2) ambient preflight (flag-gated) ------------------------------------------------------

class _AmbientScholar:
    """Adapter so preflight can call scholar.search(query) uniformly (matches app_mention)."""
    degraded = False

    def search(self, query: str):
        try:
            from tools import scholar as _sch
            return _sch.search_literature(query, 6)
        except Exception:
            self.degraded = True
            return []


def _ambient_preflight(client, logger, event, channel, text):
    thread_ts = event.get("thread_ts") or event.get("ts")
    try:
        _bid, own_user = _own_identity(client)
        rts = RTS(client, action_token=event.get("action_token"), is_user_token=False,
                  own_bot_user_id=own_user, own_msg_ts=event.get("ts"), budget=3)   # no action_token in channels -> record+lit only
        record = RecordStore(client, os.environ.get("CURIE_LIST_ID"))
        result = preflight.run_preflight(text, record=record, rts=rts, scholar=_AmbientScholar())
        if result.kind == "verdict" and result.verdict is not None:
            client.chat_postMessage(channel=channel, thread_ts=thread_ts,
                                    blocks=verdict_blocks(result.verdict, text),
                                    text="Curie preflight")
    except Exception:
        logger.exception("ambient preflight failed")


# ---- identity / dedup -----------------------------------------------------------------------

def _own_identity(client):
    """(bot_id, bot_user_id) for THIS app, cached on the client (shared with app_mention)."""
    bid = getattr(client, "_curie_bot_id", "unset")
    uid = getattr(client, "_curie_bot_user_id", None)
    if bid != "unset":
        return bid, uid
    bid = uid = None
    try:
        a = client.auth_test()
        a = a.data if hasattr(a, "data") else a
        bid = a.get("bot_id")
        uid = a.get("user_id")
    except Exception:
        pass
    try:
        client._curie_bot_id = bid
        client._curie_bot_user_id = uid
    except Exception:
        pass
    return bid, uid


def _is_own(event, own_bot_id, own_user) -> bool:
    if own_bot_id and event.get("bot_id") == own_bot_id:
        return True
    if own_user and event.get("user") == own_user:
        return True
    return False


def _looks_like_plan(text: str) -> bool:
    return len(text) >= 8 and bool(_PLAN_RE.search(text))


def _is_dup(ts) -> bool:
    now = time.time()
    for k, t in list(_SEEN.items()):
        if now - t > _SEEN_TTL:
            _SEEN.pop(k, None)
    if ts in _SEEN:
        return True
    _SEEN[ts] = now
    return False
