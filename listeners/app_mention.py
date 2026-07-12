"""app_mention.py — Trigger A: `@Curie <experiment plan>` in a channel (backend.md §3.3, §6.1).

Agent messaging experience path (CLAUDE.md): NO legacy assistant callbacks. This handler:
  ack (👀 + assistant status) -> capture action_token -> run preflight -> reply plain-text in-thread
  -> swap 👀→✅ and clear status in finally. Every failure posts a human message; status always clears.
"""
from __future__ import annotations
import os, re, time

from pipeline import preflight
from pipeline import recall
from tools.rts import RTS
from tools.record_store import RecordStore
from tools import scholar as scholar_mod
from tools.streaming import Streamer
from tools.cards import verdict_blocks
from pipeline import ledger
from listeners import standing
from listeners import app_home
from llm import client as llm_client

_MENTION_RE = re.compile(r"<@[A-Z0-9]+>")
_SEEN: dict[str, float] = {}          # dedup (channel, ts) -> t  (§7.3 idempotency)
_SEEN_TTL = 300.0


class _LiveScholar:
    """Adapter so preflight can call scholar.search(query) uniformly."""
    degraded = False

    def search(self, query: str):
        try:
            return scholar_mod.search_literature(query, 6)
        except Exception:
            self.degraded = True
            return []


def register(app):
    @app.event("app_mention")
    def handle_app_mention(body, event, client, logger):
        channel, ts = event.get("channel"), event.get("ts")
        thread_ts = event.get("thread_ts") or ts
        if _is_dup(channel, ts):
            return
        plan_text = _MENTION_RE.sub("", event.get("text", "")).strip()
        action_token = event.get("action_token") or body.get("event", {}).get("action_token")
        _run_plan(client, logger, channel=channel, ts=ts, thread_ts=thread_ts,
                  user=event.get("user"), action_token=action_token, plan_text=plan_text)

    @app.event("message")
    def handle_direct_message(body, event, client, logger):
        # Agent messaging experience: the App Home "Messages" tab is a DM loop (message.im). Channel
        # messages are ambient.py's job — we take ONLY IMs here. action_token IS present in message.im
        # payloads (CLAUDE.md §2), so RTS works from a DM exactly like an @mention.
        if event.get("channel_type") != "im" or event.get("subtype") is not None or event.get("bot_id"):
            return
        channel, ts = event.get("channel"), event.get("ts")
        thread_ts = event.get("thread_ts") or ts
        if _is_dup(channel, ts):
            return
        plan_text = _MENTION_RE.sub("", event.get("text", "")).strip()
        action_token = event.get("action_token") or body.get("event", {}).get("action_token")
        _run_plan(client, logger, channel=channel, ts=ts, thread_ts=thread_ts,
                  user=event.get("user"), action_token=action_token, plan_text=plan_text)


def _run_plan(client, logger, *, channel, ts, thread_ts, user, action_token, plan_text):
    """Shared intake for @mention (channel) and DM (message.im): route deterministic gestures, else
    run the streamed preflight and post the verdict card. Every failure is a human message; the
    assistant status always clears in `finally`."""
    if not channel or not ts:
        return
    if not plan_text or plan_text.lower() in ("setup", "help"):
        client.chat_postMessage(channel=channel, thread_ts=thread_ts,
                                text="Mention me with an experiment plan and I'll check it against "
                                     "the lab record, history, and literature — e.g. "
                                     "`@Curie fine-tune ESM2-650M, lr 1e-4, batch 32, v1 split`.")
        return

    # ---- ledger gestures route BEFORE preflight (deterministic, no LLM) ----
    _claim = ledger.is_track_hypothesis(plan_text)
    if _claim:
        client.chat_postMessage(channel=channel, thread_ts=thread_ts,
            text=ledger.register_hypothesis(_claim,
                record=RecordStore(client, os.environ.get("CURIE_LIST_ID")), client=client))
        return
    if ledger.is_stand_query(plan_text):
        client.chat_postMessage(channel=channel, thread_ts=thread_ts,
            blocks=ledger.ledger_view_blocks(RecordStore(client, os.environ.get("CURIE_LIST_ID"))),
            text=ledger.HEADER)
        return
    if standing.is_standing(plan_text):
        standing.handle_standing(plan_text, client=client, channel=channel, thread_ts=thread_ts)
        return
    # Recall: "why did we drop X?" — answer from the lab's own record with a permalink, don't
    # preflight it as a plan. Runs before preflight; conservative detector (recall.is_recall_query).
    if recall.is_recall_query(plan_text):
        _answer_recall(client, logger, channel=channel, ts=ts, thread_ts=thread_ts,
                       user=user, action_token=action_token, question=plan_text)
        return

    bot_user_id = _bot_user_id(client)
    _react(client, channel, ts, "eyes", add=True)
    _status(client, channel, thread_ts, "checking the record and literature…")
    # plan-mode streaming (frontend §4A): live "Checking priors…" checklist, then the card at stop.
    streamer = Streamer(client, channel, thread_ts,
                        recipient_user_id=user, recipient_team_id=_team_id(client))
    streamer.start("*Checking priors…*")
    try:
        rts = RTS(client, action_token=action_token, is_user_token=False,
                  own_bot_user_id=bot_user_id, own_msg_ts=ts, budget=3)
        record = RecordStore(client, os.environ.get("CURIE_LIST_ID"))
        streamer.step("• Reading the plan")
        result = preflight.run_preflight(
            plan_text, record=record, rts=rts, scholar=_LiveScholar(),
            status=lambda s: (_status(client, channel, thread_ts, s) or
                              (streamer.step("• " + s) if s else None)),
        )
        _err = f"{preflight.ERROR_MSG}"
        if result.kind == "verdict":
            blocks = verdict_blocks(result.verdict, plan_text)
            if getattr(result.verdict, "level", "") == "collision":
                app_home.note_collision()          # feeds the App Home "collisions caught" stat
        elif result.kind == "parse_fail":
            blocks = [{"type": "section", "text": {"type": "mrkdwn", "text":
                getattr(preflight, "PARSE_FAIL_MSG",
                        "I couldn't read that as an experiment plan — describe the method, data, and key settings.")}}]
        else:
            blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": _err}},
                      {"type": "context", "elements": [{"type": "mrkdwn", "text": preflight.DISCLAIMER}]}]
        streamer.stop(blocks, fallback_text="Curie verdict")
        _react(client, channel, ts, "white_check_mark", add=True)
    except Exception:                          # never a stack trace to the user
        logger.exception("preflight failed")
        streamer.stop([{"type": "section", "text": {"type": "mrkdwn", "text": preflight.ERROR_MSG}},
                       {"type": "context", "elements": [{"type": "mrkdwn", "text": preflight.DISCLAIMER}]}],
                      fallback_text="Curie couldn't finish the check")
    finally:
        _react(client, channel, ts, "eyes", add=False)
        _status(client, channel, thread_ts, "")       # always clear (§7.1)


def _answer_recall(client, logger, *, channel, ts, thread_ts, user, action_token, question):
    """Recall path: stream 'Searching the lab's memory…', then post the grounded, cited answer.
    Mirrors the preflight scaffolding (👀 → status → stream → ✅) so the UX is identical; every
    failure is a human message and the status always clears in finally (frontend §7.1)."""
    bot_user_id = _bot_user_id(client)
    _react(client, channel, ts, "eyes", add=True)
    _status(client, channel, thread_ts, "searching the lab's memory…")
    streamer = Streamer(client, channel, thread_ts,
                        recipient_user_id=user, recipient_team_id=_team_id(client))
    streamer.start("*Searching the lab's memory…*")
    try:
        rts = RTS(client, action_token=action_token, is_user_token=False,
                  own_bot_user_id=bot_user_id, own_msg_ts=ts, budget=3)
        streamer.step("• Reading the question")
        streamer.step("• Searching the record")
        blocks = recall.answer_blocks(question, rts=rts, llm=llm_client,
                                      record=RecordStore(client, os.environ.get("CURIE_LIST_ID")))
        streamer.step("• Writing the answer")
        streamer.stop(blocks, fallback_text="Curie — from the lab's record")
        _react(client, channel, ts, "white_check_mark", add=True)
    except Exception:
        logger.exception("recall failed")
        streamer.stop([{"type": "section", "text": {"type": "mrkdwn", "text": preflight.ERROR_MSG}},
                       {"type": "context", "elements": [{"type": "mrkdwn", "text": preflight.DISCLAIMER}]}],
                      fallback_text="Curie couldn't finish that lookup")
    finally:
        _react(client, channel, ts, "eyes", add=False)
        _status(client, channel, thread_ts, "")


# ---- helpers (all failure-tolerant; ack/cleanup must never crash the handler) ----

def _bot_user_id(client):
    cached = getattr(client, "_curie_bot_user_id", None)
    if cached:
        return cached
    try:
        uid = client.auth_test().get("user_id")
    except Exception:
        uid = None
    try:
        client._curie_bot_user_id = uid
    except Exception:
        pass
    return uid


def _team_id(client):
    cached = getattr(client, "_curie_team_id", None)
    if cached:
        return cached
    try:
        tid = client.auth_test().get("team_id")
    except Exception:
        tid = None
    try:
        client._curie_team_id = tid
    except Exception:
        pass
    return tid


def _react(client, channel, ts, name, add=True):
    try:
        (client.reactions_add if add else client.reactions_remove)(
            channel=channel, timestamp=ts, name=name)
    except Exception:
        pass


def _status(client, channel, thread_ts, text):
    try:
        client.api_call("assistant.threads.setStatus",
                        json={"channel_id": channel, "thread_ts": thread_ts, "status": text})
    except Exception:
        pass


def _is_dup(channel, ts) -> bool:
    now = time.time()
    for k, t in list(_SEEN.items()):
        if now - t > _SEEN_TTL:
            _SEEN.pop(k, None)
    key = f"{channel}:{ts}"
    if key in _SEEN:
        return True
    _SEEN[key] = now
    return False
