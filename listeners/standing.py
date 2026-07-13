"""standing.py — turn a sentence into standing infrastructure (Bubble Lab's escalation beat).

  * "@Curie from now on …"  -> turn ON ambient preflight (listeners.ambient flag) + start a
    best-effort weekly belief-digest thread, then reply with a standing-capability card.
  * "@Curie show this week's digest" / "run the digest" -> post the digest NOW (the demo path).

app_mention.py routes these BEFORE preflight via is_standing() / handle_standing() (deterministic,
no LLM — like the ledger routing). See the wiring note handed back with this change.

Nothing here raises to the caller. The weekly schedule is a daemon thread, started once and fully
guarded, so it can never crash the app (the run-now path is what the demo uses). No Slack content
is logged.
"""
from __future__ import annotations
import datetime, os, re, threading, time

from listeners import ambient
from pipeline import ledger
from tools.record_store import RecordStore

STANDING_ON = "✅ Standing watch on — I'll preflight every plan here and post a weekly belief digest."
STANDING_FAIL = "⚠️ I couldn't set up the standing watch just now — try again in a moment."
_DIGEST_ACTION = "standing_run_digest"

_SCHED_STARTED = False


def _norm(t) -> str:
    return re.sub(r"\s+", " ", (t or "").lower().replace("’", "'")).strip(" ?!.")


# ---- gesture detection (deterministic; runs before preflight) -------------------------------

def is_standing(text) -> bool:
    return _wants_standing_on(text) or _wants_digest_now(text)


def _wants_standing_on(text) -> bool:
    return "from now on" in _norm(text)


def _wants_digest_now(text) -> bool:
    n = _norm(text)
    if any(p in n for p in ("belief digest", "this week's belief", "weekly digest")):
        return True
    return "digest" in n and any(v in n for v in ("show", "run", "post", "give", "see", "display"))


def handle_standing(text, *, client, channel, thread_ts) -> bool:
    """Perform the standing gesture. Returns True when handled. Never raises."""
    try:
        if _wants_standing_on(text):
            ambient.set_ambient_preflight(True)
            _start_weekly_digest(client, channel)
            client.chat_postMessage(channel=channel, thread_ts=thread_ts,
                                    blocks=_standing_card(), text=STANDING_ON)
            return True
        if _wants_digest_now(text):
            _post_digest(client, channel, thread_ts)
            return True
    except Exception:
        _safe_post(client, channel, thread_ts, STANDING_FAIL)
        return True
    return False


def register(app):
    @app.action(_DIGEST_ACTION)
    def handle_run_digest(ack, body, client, logger):
        ack()
        try:
            channel = ((body.get("channel") or {}).get("id")
                       or (body.get("container") or {}).get("channel_id")
                       or os.environ.get("CURIE_CHANNEL_ID"))
            if channel:
                _post_digest(client, channel, None)
        except Exception:
            logger.exception("standing_run_digest failed")


# ---- digest posting -------------------------------------------------------------------------

def _post_digest(client, channel, thread_ts):
    record = RecordStore(client, os.environ.get("CURIE_LIST_ID"))
    blocks = ledger.belief_digest_blocks(record)
    client.chat_postMessage(channel=channel, thread_ts=thread_ts, blocks=blocks,
                            text=ledger.DIGEST_HEADER)


def _standing_card():
    return [
        {"type": "section", "text": {"type": "mrkdwn", "text": "*" + STANDING_ON + "*"}},
        {"type": "context", "elements": [{"type": "mrkdwn",
            "text": "Ambient preflight: on · Weekly belief digest: Mondays · "
                    "ask any time with “show this week's digest”"}]},
        {"type": "actions", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "Show this week's digest"},
             "action_id": _DIGEST_ACTION}]},
    ]


# ---- best-effort weekly schedule (daemon thread; never crashes the app) ---------------------

def _start_weekly_digest(client, channel):
    global _SCHED_STARTED
    if _SCHED_STARTED or not channel:
        return
    _SCHED_STARTED = True
    try:
        threading.Thread(target=_weekly_loop, args=(client, channel), daemon=True).start()
    except Exception:
        _SCHED_STARTED = False


def _weekly_loop(client, channel):
    while True:
        try:
            time.sleep(_seconds_until_next_monday())
            _post_digest(client, channel, None)
            time.sleep(90)                          # step past the target minute; avoid double-fire
        except Exception:
            try:
                time.sleep(3600)                    # back off, then keep the loop alive
            except Exception:
                return


def _seconds_until_next_monday(hour: int = 9) -> float:
    now = datetime.datetime.now()
    days_ahead = (0 - now.weekday()) % 7            # Monday == 0
    target = (now + datetime.timedelta(days=days_ahead)).replace(
        hour=hour, minute=0, second=0, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=7)
    return max(1.0, (target - now).total_seconds())


def _safe_post(client, channel, thread_ts, text):
    try:
        client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=text)
    except Exception:
        pass
