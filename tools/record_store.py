"""record_store.py — read path over the native Slack List "Lab Record" (backend.md §4, §5.3).

The List is the PRIMARY candidate source (Glean pattern: structured record first, RTS enriches).
This module is read-only for the vertical slice (writes = result-logging, deferred).

Degrades cleanly: if CURIE_LIST_ID is unset or the List can't be read, find_candidates() returns []
and the pipeline falls back to RTS-only. Returns plain dicts (pure API wrapper), same normalized
shape as rts.py: {"source":"list","title","permalink","outcome","params","text"}.
"""
from __future__ import annotations
import os

# Column keys we care about (must match the schema in backend.md §4.1 / seed).
_FIELDS = ("title", "params", "outcome", "status", "source")


class RecordStore:
    def __init__(self, client, list_id: str | None = None):
        self.client = client
        self.list_id = list_id or os.environ.get("CURIE_LIST_ID") or ""

    def available(self) -> bool:
        return bool(self.list_id)

    def _items(self) -> list[dict]:
        """Fetch all items; filter in-process (record is small — avoids server-side filter semantics)."""
        if not self.available():
            return []
        items: list[dict] = []
        cursor = None
        try:
            for _ in range(10):  # cap pagination defensively
                payload = {"list_id": self.list_id, "limit": 100}
                if cursor:
                    payload["cursor"] = cursor
                r = self.client.api_call("slackLists.items.list", json=payload)
                data = r.data if hasattr(r, "data") else r
                items.extend(data.get("items", []) or [])
                cursor = (data.get("response_metadata") or {}).get("next_cursor")
                if not cursor:
                    break
        except Exception:
            return []
        return items

    def find_candidates(self, plan) -> list[dict]:
        """Return record rows whose method/aliases/params overlap the plan's terms."""
        rows = self._items()
        if not rows:
            return []
        terms = _plan_terms(plan)
        scored = []
        for row in rows:
            fields = _row_fields(row)
            if _kind_of(fields) == "hypothesis":
                continue  # experiments only for collision matching
            hay = " ".join([
                fields.get("title", ""), fields.get("params", ""),
                fields.get("outcome", ""),
            ]).lower()
            hits = sum(1 for t in terms if t in hay)
            if hits:
                scored.append((hits, row, fields))
        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for _, row, fields in scored[:6]:
            out.append({
                "source": "list",
                "title": fields.get("title") or "(untitled experiment)",
                "text": " ".join(v for v in (fields.get("title"), fields.get("params"), fields.get("outcome")) if v),
                "permalink": _row_permalink(row, fields),
                "outcome": fields.get("outcome") or None,
                "params": _parse_params(fields.get("params", "")),
                "status": fields.get("status"),
            })
        return out


# ---- field extraction helpers (Lists return rich_text; we flatten to plain) ----------------

def _row_fields(row: dict) -> dict:
    """Map a List item's fields (keyed by column key or id) to flat plain-text strings."""
    out = {}
    fields = row.get("fields") or row.get("column_values") or []
    if isinstance(fields, dict):
        fields = list(fields.values())
    for f in fields:
        key = f.get("key") or f.get("column_key") or f.get("column_id")
        if key is None:
            continue
        out[key] = _flatten_value(f)
    return out


def _flatten_value(f: dict) -> str:
    if "rich_text" in f and f["rich_text"]:
        return _flatten_rich_text(f["rich_text"])
    for k in ("text", "value", "select", "date"):
        if f.get(k):
            v = f[k]
            if isinstance(v, str):
                return v
            # single_select / user / date come back as a single-element list in write shape
            # (and often on read too) — unwrap so kind/status compare against bare option values.
            if isinstance(v, (list, tuple)):
                return " ".join(str(x) for x in v if not isinstance(x, (dict, list)))
            return str(v)
    return ""


def _flatten_rich_text(rt) -> str:
    """rich_text is a list of blocks with nested elements holding {'text': ...}."""
    parts: list[str] = []

    def walk(node):
        if isinstance(node, dict):
            if "text" in node and isinstance(node["text"], str):
                parts.append(node["text"])
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for n in node:
                walk(n)

    walk(rt)
    return " ".join(parts).strip()


def _kind_of(fields: dict) -> str:
    return (fields.get("kind") or "").lower()


def _row_permalink(row: dict, fields: dict) -> str:
    # Prefer the row's own permalink if the API returned one; else the source message link.
    return row.get("permalink") or fields.get("source") or row.get("id", "")


def _parse_params(text: str) -> dict:
    """Best-effort 'k: v, k2: v2' or 'k=v' extraction from the flattened Params cell."""
    out: dict[str, str] = {}
    if not text:
        return out
    for chunk in text.replace(";", ",").split(","):
        for sep in (":", "="):
            if sep in chunk:
                k, v = chunk.split(sep, 1)
                k, v = k.strip().lower(), v.strip()
                if k and v:
                    out[k] = v
                break
    return out


def _plan_terms(plan) -> list[str]:
    terms = set()
    for a in getattr(plan, "aliases", []) or []:
        terms.add(str(a).lower())
    m = getattr(plan, "method", "") or ""
    for w in m.lower().split():
        if len(w) > 2:
            terms.add(w)
    for k, v in (getattr(plan, "params", {}) or {}).items():
        terms.add(str(v).lower())
    return [t for t in terms if t]
