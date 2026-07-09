"""reaction_added.py — Trigger D: 🧪 on a result message logs it to the Lab Record (backend.md §6.2).

Flow: 🧪 reaction -> fetch the reacted message -> LLM-extract {title, status, outcome}
(prompts/log_extract.md; deterministic keyword fallback so the flow survives with no LLM)
-> fuzzy-match a List row by title (create one if none) -> slackLists.items.update
(status select + outcome rich_text + trust select=auto — verified `cells` shape,
docs/platform/api-shapes-verified.md) -> in-thread receipt with Undo / Verify ✓
(frontend.md §4C/§9; act-then-undo, no confirm modal; prior cell values kept 15 min).

Bot token only. Dedup on (channel, ts, reaction) per §7.3. Every step failure-tolerant:
the handler never raises, and any user-visible failure posts a human message + retry button.
Message bodies are never logged (§7.6).
"""
from __future__ import annotations
import datetime, difflib, json, os, pathlib, re, time
from typing import Literal, Optional
from pydantic import BaseModel

from llm import client as llm
from tools import record_store as rs

_REACTION = "test_tube"                       # emoji NAME, no colons
_SEEN: dict[str, float] = {}                  # dedup (channel, ts, reaction) -> t  (§7.3)
_SEEN_TTL = 300.0
_UNDO: dict[str, tuple[float, Optional[dict]]] = {}   # row_id -> (t, prior cells | None=created)
_UNDO_TTL = 900.0                             # frontend §4C: Undo window is 15 min
_SCHEMA_PATH = pathlib.Path(__file__).parent.parent / "seed" / "curie_list_schema.json"
_MATCH_FLOOR = 0.5                            # below this similarity we create a new row

# Frontend §9 verbatim receipt template (+ §4C states).
RECEIPT = "✏️ Logged to *{title}* — status *{status}*. Notebook updated."
REVERTED = "↩️ Reverted."
VERIFIED = "✓ Verified by <@{user}>"
UNDO_EXPIRED = ("Nothing to undo — that write is older than 15 minutes. "
                "Edit the List row directly (it's native).")
UNDO_CREATED = ("This entry was newly created, so there's no earlier value to restore — "
                "remove the row from the List directly if it shouldn't exist.")
FAILURE = ("⚠️ I couldn't log that — the notebook write didn't go through. "
           "Give it a minute, then try again.")


class LogExtract(BaseModel):
    """Strict shape for the log-extraction LLM call (invalid status -> retry -> fallback)."""
    experiment_title: str = ""
    status: Literal["failed", "succeeded", "running", "abandoned"] = "running"
    outcome: str = ""


def register(app):
    @app.event("reaction_added")
    def handle_reaction_added(event, client, logger):
        try:
            if event.get("reaction") != _REACTION:
                return
            item = event.get("item") or {}
            if item.get("type") != "message":
                return
            channel, ts = item.get("channel"), item.get("ts")
            if not channel or not ts or _is_dup(channel, ts, _REACTION):
                return
            _run_log(client, logger, channel, ts)
        except Exception:                      # never a crash out of the handler
            logger.exception("reaction_added: log flow failed")

    @app.action("log_undo")
    def handle_log_undo(ack, body, client, logger):
        ack()
        try:
            row_id = _action_value(body)
            found, prior = _pop_undo(row_id)
            if found and prior:
                ok = _write_cells(client, row_id, prior)
                text = REVERTED if ok else FAILURE
            elif found:
                text = UNDO_CREATED            # created rows: no delete shape verified — be honest
            else:
                text = UNDO_EXPIRED
            _update_receipt(client, body, text)
        except Exception:
            logger.exception("log_undo failed")

    @app.action("log_verify")
    def handle_log_verify(ack, body, client, logger):
        ack()
        try:
            row_id = _action_value(body)
            user = ((body.get("user") or {}).get("id")) or "unknown"
            ok = _write_cells(client, row_id, {"trust": "verified"})
            _update_receipt(client, body, VERIFIED.format(user=user) if ok else FAILURE)
        except Exception:
            logger.exception("log_verify failed")

    @app.action("log_retry")
    def handle_log_retry(ack, body, client, logger):
        ack()
        try:
            channel, _, ts = _action_value(body).partition("|")
            if channel and ts:
                _run_log(client, logger, channel, ts)   # explicit click bypasses dedup
        except Exception:
            logger.exception("log_retry failed")


# ---- the log flow (each step tolerant; a hard stop posts FAILURE + retry) ---------------

def _run_log(client, logger, channel, ts):
    msg = _fetch_message(client, channel, ts)
    text = (msg or {}).get("text", "").strip() if msg else ""
    thread_ts = (msg or {}).get("thread_ts") or ts
    if not text:
        _post_failure(client, channel, thread_ts, ts)
        return
    ex = _extract(text)
    row_id, prior = _match_row(client, ex.experiment_title)
    if row_id:
        if not _write_cells(client, row_id, {"status": ex.status, "outcome": ex.outcome,
                                             "trust": "auto", "updated": _today()}):
            _post_failure(client, channel, thread_ts, ts)
            return
        _remember_undo(row_id, prior)
    else:
        row_id = _create_row(client, ex)
        if not row_id:
            _post_failure(client, channel, thread_ts, ts)
            return
        _remember_undo(row_id, None)           # marker: newly created, nothing to restore
    _post_receipt(client, channel, thread_ts, ex, row_id)


def _fetch_message(client, channel, ts) -> Optional[dict]:
    """conversations.history pinned to ts; conversations.replies fallback for thread replies."""
    try:
        r = _data(client.conversations_history(channel=channel, latest=ts, inclusive=True, limit=1))
        msgs = r.get("messages") or []
        if msgs and msgs[0].get("ts") == ts:
            return msgs[0]
    except Exception:
        pass
    try:
        r = _data(client.conversations_replies(channel=channel, ts=ts, latest=ts,
                                               inclusive=True, limit=1))
        msgs = r.get("messages") or []
        for m in msgs:
            if m.get("ts") == ts:
                return m
        return msgs[0] if msgs else None
    except Exception:
        return None


# ---- extraction (LLM with deterministic fallback — flow works with no API key) ----------

def _extract(text: str) -> LogExtract:
    out = None
    try:
        user = llm.load_prompt("log_extract").replace("{message}", text)
        out = llm.complete("log_extract",
                           system="You are Curie's result-logging extractor. Return only JSON.",
                           user=user, model_cls=LogExtract)
    except Exception:
        out = None
    fallback = _heuristic_extract(text)
    if out is None:
        return fallback
    if not out.experiment_title.strip():
        out.experiment_title = fallback.experiment_title
    if not out.outcome.strip():
        out.outcome = fallback.outcome
    return out


_STATUS_WORDS = (  # first hit wins; order matters (an abandoned failure is "abandoned")
    ("abandoned", ("abandon", "shelv", "gave up", "giving up", "killed", "killing it", "drop this")),
    ("failed", ("fail", "nan", "crash", "diverg", "collaps", "broke", "worse", "no better", "dead")),
    ("succeeded", ("succeed", "success", "worked", "works", "improv", "beat", "better than",
                   "converged", "sota", "new best")),
)


def _heuristic_extract(text: str) -> LogExtract:
    low = text.lower()
    status = "running"
    for name, words in _STATUS_WORDS:
        if any(w in low for w in words):
            status = name
            break
    clean = re.sub(r"<@[A-Z0-9]+>", "", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    title = clean.split(". ", 1)[0].split("\n", 1)[0].rstrip(".")[:120] or "experiment"
    return LogExtract(experiment_title=title, status=status, outcome=clean[:300])


# ---- List row matching + writes (verified shapes; record_store is the read path) ---------

def _match_row(client, title: str) -> tuple[str, Optional[dict]]:
    """Fuzzy-match an experiment row by title. Returns (row_id, prior-values-for-undo)."""
    try:
        store = rs.RecordStore(client, _list_id())
        best, best_score = None, 0.0
        for row in store._items():                       # read path shared with record_store
            fields = rs._row_fields(row)
            if (fields.get("kind") or "").lower() == "hypothesis":
                continue                                 # experiments only
            score = _similarity(title, fields.get("title", ""))
            if score > best_score:
                best, best_score = (row, fields), score
        if best and best_score >= _MATCH_FLOOR:
            row, fields = best
            row_id = row.get("id") or row.get("item_id") or ""
            prior = {"status": fields.get("status", ""), "outcome": fields.get("outcome", ""),
                     "trust": fields.get("trust", "")}
            return (row_id, prior) if row_id else ("", None)
    except Exception:
        pass
    return "", None


def _similarity(a: str, b: str) -> float:
    ta, tb = set(_tokens(a)), set(_tokens(b))
    if not ta or not tb:
        return 0.0
    jaccard = len(ta & tb) / len(ta | tb)
    ratio = difflib.SequenceMatcher(None, " ".join(sorted(ta)), " ".join(sorted(tb))).ratio()
    return max(jaccard, ratio)


def _tokens(s: str) -> list[str]:
    return [t for t in re.sub(r"[^a-z0-9.\- ]+", " ", (s or "").lower()).split() if len(t) > 1]


def _write_cells(client, row_id: str, values: dict) -> bool:
    """slackLists.items.update with the verified `cells` shape (row_id on every cell)."""
    cols = _columns()
    cells = []
    if values.get("status"):
        cells.append({"row_id": row_id, "column_id": cols.get("status", "status"),
                      "select": [values["status"]]})
    if values.get("outcome"):
        cells.append({"row_id": row_id, "column_id": cols.get("outcome", "outcome"),
                      "rich_text": [_rt(values["outcome"])]})
    if values.get("trust"):
        cells.append({"row_id": row_id, "column_id": cols.get("trust", "trust"),
                      "select": [values["trust"]]})
    if values.get("polarity"):                     # Evidence polarity (used by ambient ingest)
        cells.append({"row_id": row_id, "column_id": cols.get("polarity", "polarity"),
                      "select": [values["polarity"]]})
    if values.get("updated"):
        cells.append({"row_id": row_id, "column_id": cols.get("updated", "updated"),
                      "date": [values["updated"]]})       # date is an ARRAY (confirmed live)
    if not cells:
        return False
    try:
        r = _data(client.api_call("slackLists.items.update",
                                  json={"list_id": _list_id(), "cells": cells}))
        return bool(r.get("ok"))
    except Exception:
        return False


def _create_row(client, ex: LogExtract) -> str:
    cols = _columns()
    fields = [
        {"column_id": cols.get("title", "title"), "rich_text": [_rt(ex.experiment_title)]},
        {"column_id": cols.get("kind", "kind"), "select": ["experiment"]},
        {"column_id": cols.get("status", "status"), "select": [ex.status]},
        {"column_id": cols.get("trust", "trust"), "select": ["auto"]},
        {"column_id": cols.get("updated", "updated"), "date": [_today()]},
    ]
    if ex.outcome:
        fields.append({"column_id": cols.get("outcome", "outcome"), "rich_text": [_rt(ex.outcome)]})
    try:
        r = _data(client.api_call("slackLists.items.create",
                                  json={"list_id": _list_id(), "initial_fields": fields}))
        if not r.get("ok", True):
            return ""
        return _item_id(r)
    except Exception:
        return ""


# ---- receipt + failure messages (frontend §4C/§9) ----------------------------------------

def _post_receipt(client, channel, thread_ts, ex: LogExtract, row_id: str):
    line = RECEIPT.format(title=ex.experiment_title, status=ex.status.capitalize())
    blocks = [
        {"type": "context", "elements": [{"type": "mrkdwn", "text": line}]},
        {"type": "actions", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "Undo"},
             "action_id": "log_undo", "value": row_id},
            {"type": "button", "text": {"type": "plain_text", "text": "Verify ✓"},
             "action_id": "log_verify", "value": row_id},
        ]},
    ]
    try:
        client.chat_postMessage(channel=channel, thread_ts=thread_ts, blocks=blocks,
                                text=f"Logged to {ex.experiment_title} — status {ex.status}.")
    except Exception:
        pass


def _post_failure(client, channel, thread_ts, ts):
    blocks = [
        {"type": "section", "text": {"type": "mrkdwn", "text": FAILURE}},
        {"type": "actions", "elements": [
            {"type": "button", "text": {"type": "plain_text", "text": "Try again"},
             "action_id": "log_retry", "value": f"{channel}|{ts}"},
        ]},
    ]
    try:
        client.chat_postMessage(channel=channel, thread_ts=thread_ts, blocks=blocks,
                                text="Curie couldn't log that result.")
    except Exception:
        pass


def _update_receipt(client, body, text: str):
    """Collapse the receipt in place (frontend §10: Undo -> 'Reverted.' via chat.update)."""
    try:
        channel = ((body.get("channel") or {}).get("id")
                   or (body.get("container") or {}).get("channel_id"))
        ts = ((body.get("message") or {}).get("ts")
              or (body.get("container") or {}).get("message_ts"))
        if channel and ts:
            client.chat_update(channel=channel, ts=ts, text=text,
                               blocks=[{"type": "context",
                                        "elements": [{"type": "mrkdwn", "text": text}]}])
    except Exception:
        pass


# ---- small helpers (all failure-tolerant) -------------------------------------------------

def _data(resp):
    return resp.data if hasattr(resp, "data") else resp


def _rt(text: str) -> dict:
    """One Block Kit rich_text block — required payload shape for text/rich_text columns."""
    return {"type": "rich_text", "elements": [
        {"type": "rich_text_section", "elements": [{"type": "text", "text": text or ""}]}]}


def _item_id(resp: dict) -> str:
    for path in (("item", "id"), ("item_id",), ("item", "item_id"), ("id",)):
        cur = resp
        for k in path:
            cur = cur.get(k) if isinstance(cur, dict) else None
            if cur is None:
                break
        if isinstance(cur, str) and cur:
            return cur
    return ""


_SCHEMA_CACHE: dict = {}


def _schema() -> dict:
    global _SCHEMA_CACHE
    if not _SCHEMA_CACHE:
        try:
            _SCHEMA_CACHE = json.loads(_SCHEMA_PATH.read_text())
        except Exception:
            _SCHEMA_CACHE = {}
    return _SCHEMA_CACHE


def _list_id() -> str:
    return os.environ.get("CURIE_LIST_ID") or _schema().get("list_id", "")


def _columns() -> dict:
    return _schema().get("columns") or {}


def _today() -> str:
    return datetime.date.today().isoformat()


def _action_value(body) -> str:
    try:
        return (body.get("actions") or [{}])[0].get("value") or ""
    except Exception:
        return ""


def _remember_undo(row_id: str, prior: Optional[dict]):
    _UNDO[row_id] = (time.time(), prior)


def _pop_undo(row_id: str) -> tuple[bool, Optional[dict]]:
    now = time.time()
    for k, (t, _) in list(_UNDO.items()):
        if now - t > _UNDO_TTL:
            _UNDO.pop(k, None)
    if row_id in _UNDO:
        return True, _UNDO.pop(row_id)[1]
    return False, None


def _is_dup(channel, ts, trigger) -> bool:
    now = time.time()
    for k, t in list(_SEEN.items()):
        if now - t > _SEEN_TTL:
            _SEEN.pop(k, None)
    key = f"{channel}:{ts}:{trigger}"
    if key in _SEEN:
        return True
    _SEEN[key] = now
    return False
