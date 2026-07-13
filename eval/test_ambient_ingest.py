"""Offline END-TO-END test for ambient run-record ingest (listeners/ambient.py) — NO network.

The live symptom (a "📊 Run …" channel message produced no ingest and no alert) is app CONFIG:
the deployed app wasn't subscribed to `message.channels` (+ needs `channels:history`) — fixed via
manifest.json, a human dashboard/reinstall action. THIS test rules out a SECOND bug in the code
path itself: parse → param-aware row resolution → belief-flip simulation (pipeline.ledger) →
List write (pipeline.logging → listeners.reaction_added atoms) → ONE proactive top-level alert.

A FakeSlackClient serves slackLists.items.list / items.update / items.create + chat.postMessage
against in-memory rows shaped EXACTLY like the live API returns them (rich_text title, single-
select lists, `parent_record_id` hierarchy — verified live Jul 10), and update/create payloads are
validated against the cached column-id schema the write atoms use (seed/curie_list_schema.json).

Runs with NO OpenAI key and NO Slack. `python -m eval.test_ambient_ingest`.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Env BEFORE importing app modules (the path reads CURIE_LIST_ID / CURIE_CHANNEL_ID at call time,
# but set-first keeps this hermetic even if import-time reads ever appear).
os.environ["CURIE_LIST_ID"] = "F0FAKELIST"
os.environ["CURIE_CHANNEL_ID"] = "C0FAKECHAN"

import copy, datetime, json, pathlib

from listeners import ambient
from tools import record_store as rs

CH = os.environ["CURIE_CHANNEL_ID"]
LIST_ID = os.environ["CURIE_LIST_ID"]
TODAY = datetime.date.today().isoformat()

# ---- column-id ↔ key map (the SAME cached schema reaction_added/ledger address columns with) --
_KEYS = ("title", "kind", "status", "owner", "params", "outcome", "polarity",
         "source", "notebook", "trust", "updated")
COL_TO_KEY = {k: k for k in _KEYS}          # bare-key fallback (write atoms use keys w/o cache)
try:
    _schema = json.loads((pathlib.Path(__file__).parent.parent
                          / "seed" / "curie_list_schema.json").read_text())
    COL_TO_KEY.update({v: k for k, v in (_schema.get("columns") or {}).items()})
except Exception:
    pass
_VALUE_KEYS = ("rich_text", "select", "date", "text", "message", "user", "number")


# ---- fakes -----------------------------------------------------------------------------------

class FakeLogger:
    def __init__(self): self.exceptions = []
    def exception(self, *a, **k): self.exceptions.append(a[0] if a else "")
    def info(self, *a, **k): pass
    def warning(self, *a, **k): pass
    def debug(self, *a, **k): pass
    def error(self, *a, **k): pass


def _rt(text):
    return [{"type": "rich_text", "elements": [
        {"type": "rich_text_section", "elements": [{"type": "text", "text": text}]}]}]


def make_row(row_id, parent=None, *, title, kind, status, polarity=None, params=None,
             outcome=None, trust="auto", updated="2026-07-01"):
    """One item EXACTLY as slackLists.items.list returns it (fields keyed by column `key`)."""
    fields = [
        {"key": "title", "rich_text": _rt(title)},
        {"key": "kind", "select": [kind]},
        {"key": "status", "select": [status]},
        {"key": "trust", "select": [trust]},
        {"key": "updated", "date": [updated]},
    ]
    if polarity:
        fields.append({"key": "polarity", "select": [polarity]})
    if params:
        fields.append({"key": "params", "text": params})
    if outcome:
        fields.append({"key": "outcome", "rich_text": _rt(outcome)})
    row = {"id": row_id, "fields": fields}
    if parent:
        row["parent_record_id"] = parent    # items.list returns parent_record_id (verified live)
    return row


class FakeSlackClient:
    """In-memory stand-in for slack_sdk WebClient — only the surface the ingest path touches.
    Contract violations (wrong list_id, unknown column_id, malformed cell) are RECORDED in
    .errors, not raised — the app swallows exceptions, so raising would hide the root cause."""

    def __init__(self, rows):
        self.rows = rows            # canonical store; update/create mutate it
        self.posts = []             # every chat_postMessage kwargs
        self.updates = []           # items.update payloads
        self.creates = []           # items.create payloads
        self.calls = []             # every api_call method name
        self.errors = []            # fake-API contract violations
        self._n = 0

    # -- WebClient surface ---------------------------------------------------------------
    def auth_test(self):
        return {"ok": True, "bot_id": "B0CURIE", "user_id": "U0CURIE", "user": "prior"}

    def chat_postMessage(self, **kwargs):
        self.posts.append(copy.deepcopy(kwargs))
        return {"ok": True, "channel": kwargs.get("channel"), "ts": "1789000100.000001"}

    def api_call(self, method, json=None, **kwargs):
        self.calls.append(method)
        payload = json or {}
        if payload.get("list_id") != LIST_ID and method.startswith("slackLists."):
            self.errors.append(f"{method}: wrong list_id {payload.get('list_id')!r}")
        if method == "slackLists.items.list":
            return {"ok": True, "items": copy.deepcopy(self.rows),
                    "response_metadata": {"next_cursor": ""}}
        if method == "slackLists.items.update":
            for cell in payload.get("cells") or []:
                self._apply_cell(cell)
            self.updates.append(copy.deepcopy(payload))
            return {"ok": True}
        if method == "slackLists.items.create":
            row = self._create_row(payload)
            self.creates.append(copy.deepcopy(payload))
            return {"ok": True, "item": {"id": row["id"]}}
        self.errors.append(f"unmodeled api_call {method!r}")
        return {"ok": False, "error": "fake_unmodeled_method"}

    # -- internals -------------------------------------------------------------------------
    def _key_for(self, column_id, ctx):
        key = COL_TO_KEY.get(column_id or "")
        if not key:
            self.errors.append(f"{ctx}: unknown column_id {column_id!r}")
        return key

    def _cell_value(self, cell, ctx):
        present = [k for k in _VALUE_KEYS if k in cell]
        if len(present) != 1:
            self.errors.append(f"{ctx}: cell must carry exactly one value payload, got {present}")
            return None
        return {present[0]: copy.deepcopy(cell[present[0]])}

    def _apply_cell(self, cell):
        row = next((r for r in self.rows if r["id"] == cell.get("row_id")), None)
        if row is None:
            self.errors.append(f"items.update: unknown row_id {cell.get('row_id')!r}")
            return
        key = self._key_for(cell.get("column_id"), "items.update")
        val = self._cell_value(cell, "items.update")
        if not key or val is None:
            return
        new_field = {"key": key, **val}
        for i, f in enumerate(row["fields"]):
            if f.get("key") == key:
                row["fields"][i] = new_field
                return
        row["fields"].append(new_field)

    def _create_row(self, payload):
        self._n += 1
        fields = []
        for f in payload.get("initial_fields") or []:
            key = self._key_for(f.get("column_id"), "items.create")
            val = self._cell_value(f, "items.create")
            if key and val is not None:
                fields.append({"key": key, **val})
        row = {"id": f"RecFAKE{self._n:03d}", "fields": fields}
        if payload.get("parent_item_id"):
            row["parent_record_id"] = payload["parent_item_id"]
        self.rows.append(row)
        return row


# ---- seed: hypothesis H, one contrasts child + one running child → rollup == "open" ----------

def seed():
    return [
        make_row("RecHYP001", title="Full fine-tuning beats LoRA on protein stability",
                 kind="hypothesis", status="open", updated="2026-07-01"),
        make_row("RecEXP001", "RecHYP001", title="Full FT llama-7b split v2", kind="experiment",
                 status="failed", polarity="contrasts",
                 params="model=llama-7b, lr=1e-4, batch=32, split=v2",
                 outcome="NaN collapse at step 40", updated="2026-07-03"),
        make_row("RecEXP002", "RecHYP001", title="Full FT llama-7b split v1", kind="experiment",
                 status="running",
                 params="model=llama-7b, lr=1e-4, batch=32, split=v1",
                 updated="2026-07-05"),
    ]


def fields_of(client, row_id):
    row = next(r for r in client.rows if r["id"] == row_id)
    return rs._row_fields(row)      # assert through the REAL read path


_FAILED = []


def check(case, name, cond, got=""):
    print(f"{case} {'PASS' if cond else 'FAIL'} — {name}" + ("" if cond else f"  [got {got!r}]"))
    if not cond:
        _FAILED.append(f"{case}: {name}")


# ============ CASE A: failed run on the RUNNING sibling → flip → ONE top-level alert ==========
print("CASE A — run-record matches the RUNNING child; rollup open → refuted")
c, log = FakeSlackClient(seed()), FakeLogger()
ambient._ingest_run_record(c, log, CH,
    "📊 Run exp-142 | status: failed | outcome: NaN loss collapse at step 900 | "
    "params: model=llama-7b, lr=1e-4, batch=32, split=v1")
f2 = fields_of(c, "RecEXP002")
check("A", "resolved the RUNNING child param-aware (split=v1 beats the v2 sibling)",
      f2.get("status") == "failed", f2.get("status"))
check("A", "items.update wrote polarity=contrasts on that row",
      f2.get("polarity") == "contrasts", f2.get("polarity"))
check("A", "wrote the outcome text", "NaN loss collapse" in f2.get("outcome", ""), f2.get("outcome"))
check("A", "stamped updated=today", f2.get("updated") == TODAY, f2.get("updated"))
check("A", "hypothesis row status kept honest → refuted",
      fields_of(c, "RecHYP001").get("status") == "refuted", fields_of(c, "RecHYP001").get("status"))
f1 = fields_of(c, "RecEXP001")
check("A", "already-contrasts sibling untouched",
      f1.get("status") == "failed" and "step 40" in f1.get("outcome", ""),
      (f1.get("status"), f1.get("outcome")))
check("A", "EXACTLY ONE chat_postMessage", len(c.posts) == 1, len(c.posts))
post = c.posts[0] if c.posts else {}
check("A", "alert is top-level (no thread_ts)", "thread_ts" not in post, post)
check("A", "alert posted in the ingest channel", post.get("channel") == CH, post.get("channel"))
check("A", 'alert text startswith "⚠️ Heads up — your belief"',
      str(post.get("text", "")).startswith("⚠️ Heads up — your belief"), post.get("text"))
check("A", 'alert text contains "→ *Refuted*"',
      "→ *Refuted*" in str(post.get("text", "")), post.get("text"))
check("A", "alert carries blocks", bool(post.get("blocks")), post.get("blocks"))
check("A", "exactly 2 List writes (evidence row + hypothesis status) and 0 creates",
      len(c.updates) == 2 and len(c.creates) == 0, (len(c.updates), len(c.creates)))
check("A", "fake-API contract clean (list_id / column ids / cell shapes)", not c.errors, c.errors)

# ============ CASE B: run matches the ALREADY-contrasts child → write, NO alert ================
print("\nCASE B — run-record matches the already-contrasts child; rollup stays open")
c, log = FakeSlackClient(seed()), FakeLogger()
ambient._ingest_run_record(c, log, CH,
    "📊 Run exp-141-rerun | status: failed | outcome: NaN again at step 55 | "
    "params: model=llama-7b, lr=1e-4, batch=32, split=v2")
f1 = fields_of(c, "RecEXP001")
check("B", "resolved the contrasts child (split=v2) and re-wrote status=failed",
      f1.get("status") == "failed" and len(c.updates) == 1, (f1.get("status"), len(c.updates)))
check("B", "outcome updated on that row", "NaN again" in f1.get("outcome", ""), f1.get("outcome"))
check("B", "polarity still contrasts", f1.get("polarity") == "contrasts", f1.get("polarity"))
check("B", "ZERO belief alerts posted", len(c.posts) == 0, c.posts)
check("B", "hypothesis status untouched (still open)",
      fields_of(c, "RecHYP001").get("status") == "open", fields_of(c, "RecHYP001").get("status"))
check("B", "running sibling untouched",
      fields_of(c, "RecEXP002").get("status") == "running", fields_of(c, "RecEXP002").get("status"))
check("B", "fake-API contract clean", not c.errors, c.errors)

# ============ CASE C: run matches NOTHING → no crash, no alert (new orphan row is fine) ========
print("\nCASE C — run-record matches nothing (params + title all miss)")
c, log = FakeSlackClient(seed()), FakeLogger()
ambient._ingest_run_record(c, log, CH,
    "📊 Run zz-probe-77 | status: failed | outcome: sensor glitch | params: rig=z9, seed=none")
check("C", "no crash and ZERO alerts posted", len(c.posts) == 0, c.posts)
check("C", "no existing row was written (0 updates)", len(c.updates) == 0, len(c.updates))
check("C", "seeded rows unchanged",
      fields_of(c, "RecEXP001").get("status") == "failed"
      and fields_of(c, "RecEXP002").get("status") == "running"
      and fields_of(c, "RecHYP001").get("status") == "open", "seed mutated")
newr = [r for r in c.rows if r["id"].startswith("RecFAKE")]
check("C", "unmatched run created ONE new experiment row (designed fallback)",
      len(newr) == 1 and rs._row_fields(newr[0]).get("kind") == "experiment"
      and rs._row_fields(newr[0]).get("status") == "failed"
      and "zz-probe-77" in rs._row_fields(newr[0]).get("title", ""),
      [rs._row_fields(r) for r in newr])
check("C", "fake-API contract clean", not c.errors, c.errors)

# ============ CASE D: the FULL registered handler (event → guards → ingest → alert) ============
print("\nCASE D — @app.event('message') wiring: guards + ingest through the registered handler")


class StubApp:
    def __init__(self): self.handlers = {}
    def event(self, name):
        def deco(fn):
            self.handlers[name] = fn
            return fn
        return deco


stub = StubApp()
ambient.register(stub)
handler = stub.handlers.get("message")
check("D", "register() subscribed a 'message' handler (needs message.channels in the manifest)",
      callable(handler), stub.handlers)

RUN_TEXT = ("📊 Run exp-142 | status: failed | outcome: NaN loss collapse at step 900 | "
            "params: model=llama-7b, lr=1e-4, batch=32, split=v1")
c, log = FakeSlackClient(seed()), FakeLogger()
ev = {"type": "message", "subtype": "bot_message", "bot_id": "B0SCIENCE",
      "channel": CH, "ts": "1789000001.000100", "text": RUN_TEXT}
handler(ev, c, log)                      # another agent's bot_message → must ingest
check("D", "bot_message from ANOTHER agent ingests end-to-end (row flipped)",
      fields_of(c, "RecEXP002").get("polarity") == "contrasts",
      fields_of(c, "RecEXP002").get("polarity"))
check("D", "…and posts exactly one belief alert", len(c.posts) == 1, len(c.posts))
handler(ev, c, log)                      # exact replay (Bolt redelivery) → deduped
check("D", "replayed event (same ts) does not double-post", len(c.posts) == 1, len(c.posts))
c2, log2 = FakeSlackClient(seed()), FakeLogger()
handler({"type": "message", "bot_id": "B0CURIE", "channel": CH,
         "ts": "1789000002.000200", "text": RUN_TEXT}, c2, log2)
check("D", "Curie's OWN message is ignored", not c2.posts and not c2.updates,
      (c2.posts, c2.updates))
c3, log3 = FakeSlackClient(seed()), FakeLogger()
handler({"type": "message", "user": "U0HUMAN", "channel": "C0ELSEWHERE",
         "ts": "1789000003.000300", "text": RUN_TEXT}, c3, log3)
check("D", "other channels are ignored (CURIE_CHANNEL_ID scope)",
      not c3.posts and not c3.updates and not c3.calls, (c3.posts, c3.updates, c3.calls))
c4, log4 = FakeSlackClient(seed()), FakeLogger()
handler({"type": "message", "subtype": "message_changed", "channel": CH,
         "ts": "1789000004.000400", "text": RUN_TEXT}, c4, log4)
check("D", "edited messages (subtype=message_changed) are ignored",
      not c4.posts and not c4.updates, (c4.posts, c4.updates))
c5, log5 = FakeSlackClient(seed()), FakeLogger()
handler({"type": "message", "user": "U0HUMAN", "channel": CH,
         "ts": "1789000005.000500", "text": "📊 Run"}, c5, log5)
check("D", "degenerate '📊 Run' (no fields) is a no-op, not a crash",
      not c5.posts and not c5.updates and not c5.creates, (c5.posts, c5.updates))
for nm, lg in (("A", log), ("D-own", log2), ("D-chan", log3), ("D-edit", log4), ("D-degen", log5)):
    if lg.exceptions:
        check("D", f"no swallowed handler exceptions ({nm})", False, lg.exceptions)
check("D", "no swallowed handler exceptions anywhere",
      not any(lg.exceptions for lg in (log, log2, log3, log4, log5)), "see above")

# ---- verdict ---------------------------------------------------------------------------------
print()
if _FAILED:
    print(f"❌ AMBIENT INGEST E2E FAILED — {len(_FAILED)} check(s):")
    for f in _FAILED:
        print("   • " + f)
    sys.exit(1)
print("✅ AMBIENT INGEST E2E PASSES — parse → param-aware resolve → List write → belief flip → "
      "one top-level alert, fully offline. Remaining live gap is app config only "
      "(message.channels event + channels:history scope → manifest.json).")
sys.exit(0)
