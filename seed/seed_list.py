"""seed_list.py — create the native Slack List "Lab Record" and seed it from lab_story.yaml.

This is the Lists WRITE path (backend.md §4.1 schema, §5.3 call shapes). It is the counterpart
to tools/record_store.py (the READ path): both address columns by the §4.1 `key`s and treat text
fields as Block Kit rich_text, so what we write here flattens back cleanly on read.

What `python -m seed.seed_list` does:
  1. slackLists.create(name="Lab Record", schema=<§4.1 schema>) with the BOT token; capture the
     column_ids Slack returns and build a {key -> column_id} map.
  2. Insert each hypothesis as a PARENT row (kind=hypothesis); then each experiment as a CHILD row
     via parent_item_id (kind=experiment). Orphan experiments (hypothesis: null) become top-level
     experiment rows. Fields map to the schema: title, kind, status, owner, params, outcome
     (+ updated/trust/polarity — same List the ledger reads, cheap to fill honestly).
  3. Print `CURIE_LIST_ID=<id>` for pasting into .env, and cache {list_id, columns} to
     seed/curie_list_schema.json (CURIE_LIST_SCHEMA per §4.1 — config, not Slack data).

Constraints honored: BOT token only (SLACK_BOT_TOKEN); no user tokens. Owners are the seed's dummy
personas (bot-authored, decided Jul 10) — a `user` column needs a real Slack user id, which we only
set if SEED_OWNER_<HANDLE>=Uxxxx is provided; otherwise owner is left blank (never a bad write).
Fails gracefully when env/token is absent; nothing hits the network without a bot token.

    python -m seed.seed_list          # create + seed the List, print CURIE_LIST_ID
    python -m seed.seed_list --dry     # build + print every payload, call nothing (offline-safe)

Text fields MUST be Block Kit rich_text in request payloads (plain `text` is rejected). Rate limits:
create is Tier 2 (20/min), items are Tier 3 (50/min) — we sleep gently between item writes.
"""
from __future__ import annotations
import json, os, sys, time, pathlib

try:
    import yaml
except Exception as e:  # pragma: no cover - dependency guard
    sys.exit(f"seed_list: PyYAML is required (pip install -r requirements.txt): {e}")

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass  # dotenv is optional; env may already be exported

ROOT = pathlib.Path(__file__).parent
STORY = yaml.safe_load((ROOT / "lab_story.yaml").read_text())
SCHEMA_CACHE = ROOT / "curie_list_schema.json"
DRY = "--dry" in sys.argv

# ── Exact `schema` argument for slackLists.create (backend.md §4.1, copied verbatim) ─────────────
SCHEMA = [
    {"key": "title", "name": "Title", "type": "text", "is_primary_column": True},
    {"key": "kind", "name": "Kind", "type": "select", "options": {"format": "single_select", "choices": [
        {"value": "hypothesis", "label": "Hypothesis", "color": "purple"},
        {"value": "experiment", "label": "Experiment", "color": "blue"}]}},
    {"key": "status", "name": "Status", "type": "select", "options": {"format": "single_select", "choices": [
        {"value": "open", "label": "Open", "color": "yellow"},
        {"value": "running", "label": "Running", "color": "blue"},
        {"value": "succeeded", "label": "Succeeded", "color": "green"},
        {"value": "failed", "label": "Failed", "color": "red"},
        {"value": "abandoned", "label": "Abandoned", "color": "gray"},
        {"value": "supported", "label": "Supported", "color": "green"},
        {"value": "refuted", "label": "Refuted", "color": "red"}]}},
    {"key": "owner", "name": "Owner", "type": "user", "options": {"format": "single_entity"}},
    {"key": "params", "name": "Params", "type": "rich_text"},
    {"key": "outcome", "name": "Outcome", "type": "rich_text"},
    {"key": "polarity", "name": "Evidence", "type": "select", "options": {"format": "single_select", "choices": [
        {"value": "supports", "label": "Supports", "color": "green"},
        {"value": "contrasts", "label": "Contrasts", "color": "red"},
        {"value": "mentions", "label": "Mentions", "color": "gray"}]}},
    {"key": "source", "name": "Source message", "type": "message"},
    {"key": "notebook", "name": "Notebook", "type": "canvas"},
    {"key": "trust", "name": "Trust", "type": "select", "options": {"format": "single_select", "choices": [
        {"value": "verified", "label": "✓ Owner-verified", "color": "green"},
        {"value": "auto", "label": "Auto-logged", "color": "gray"}]}},
    {"key": "updated", "name": "Updated", "type": "date"},
]

# status/status-like value -> Evidence polarity toward the hypothesis.
_POLARITY = {
    "succeeded": "supports", "supported": "supports",
    "failed": "contrasts", "refuted": "contrasts",
}


# ── field-value builders (§5.3: initial_fields=[{column_id, rich_text|select|user|date|...}]) ────

def _rich_text_block(text: str) -> dict:
    """A single Block Kit rich_text block — the required shape for text/rich_text columns."""
    return {"type": "rich_text", "elements": [
        {"type": "rich_text_section", "elements": [{"type": "text", "text": text or ""}]}]}


def _rich(column_id: str, text: str) -> dict | None:
    if not text:
        return None
    # `rich_text` value is a LIST of rich_text blocks (like message blocks).
    return {"column_id": column_id, "rich_text": [_rich_text_block(text)]}


def _select(column_id: str, value: str) -> dict | None:
    if not value:
        return None
    # single_select expects a list of option values.
    return {"column_id": column_id, "select": [value]}


def _user(column_id: str, user_id: str) -> dict | None:
    if not user_id:
        return None
    return {"column_id": column_id, "user": [user_id]}


def _date(column_id: str, value: str) -> dict | None:
    if not value:
        return None
    # verified via context7 (slackLists.items.list): date is an ARRAY, e.g. ["2026-03-12"].
    return {"column_id": column_id, "date": [str(value)]}


# ── response shape helpers (defensive across sandbox variance) ───────────────────────────────────

def _as_data(resp):
    return resp.data if hasattr(resp, "data") else resp


def _extract_list_id(resp: dict) -> str:
    for path in (("list_id",), ("list", "id"), ("list", "list_id"),
                 ("list_metadata", "id"), ("list_metadata", "list_id"), ("id",)):
        cur = resp
        for k in path:
            cur = cur.get(k) if isinstance(cur, dict) else None
            if cur is None:
                break
        if isinstance(cur, str) and cur:
            return cur
    return ""


def _extract_columns(resp: dict) -> list[dict]:
    """Find the returned schema/columns list wherever the sandbox put it."""
    for path in (("list", "schema"), ("list", "columns"), ("list", "list_metadata", "schema"),
                 ("list_metadata", "schema"), ("list_metadata", "columns"),
                 ("schema",), ("columns",)):
        cur = resp
        for k in path:
            cur = cur.get(k) if isinstance(cur, dict) else None
            if cur is None:
                break
        if isinstance(cur, list) and cur and isinstance(cur[0], dict):
            return cur
    return []


def _column_map(columns: list[dict]) -> dict:
    """Build {schema key -> column_id}. Match on `key`, falling back to `name`."""
    name_to_key = {c["name"]: c["key"] for c in SCHEMA}
    out: dict[str, str] = {}
    for col in columns:
        cid = col.get("id") or col.get("column_id")
        if not cid:
            continue
        key = col.get("key") or col.get("column_key")
        if not key:
            key = name_to_key.get(col.get("name"))  # match by display name if no key echoed
        if key:
            out[key] = cid
    return out


def _extract_item_id(resp: dict) -> str:
    for path in (("item", "id"), ("item_id",), ("item", "item_id"), ("id",)):
        cur = resp
        for k in path:
            cur = cur.get(k) if isinstance(cur, dict) else None
            if cur is None:
                break
        if isinstance(cur, str) and cur:
            return cur
    return ""


# ── row field assembly ───────────────────────────────────────────────────────────────────────────

def _render_params(params: dict | None) -> str:
    """Dict -> 'k: v, k2: v2' (round-trips through record_store._parse_params)."""
    if not params:
        return ""
    return ", ".join(f"{k}: {v}" for k, v in params.items())


def _title_from_plan(exp: dict) -> str:
    """A readable, searchable title: first sentence of the plan, else the ref."""
    plan = (exp.get("plan") or "").strip()
    if plan:
        head = plan.split(". ", 1)[0].rstrip(".")
        return head[:120]
    return exp.get("ref", "experiment")


def _owner_id(handle: str) -> str:
    """Resolve a persona handle -> Slack user id, only if provided via env (else '')."""
    if not handle:
        return ""
    for var in (f"SEED_OWNER_{handle.upper()}", f"CURIE_OWNER_{handle.upper()}"):
        v = os.environ.get(var)
        if v:
            return v.strip()
    return ""


def _compact(fields: list) -> list:
    return [f for f in fields if f]


def _hypothesis_fields(cid, hypo: dict) -> list:
    return _compact([
        _rich(cid("title"), hypo.get("text", "")),
        _select(cid("kind"), "hypothesis"),
        _select(cid("status"), hypo.get("status", "open")),
        _select(cid("trust"), "auto"),
    ])


def _experiment_fields(cid, exp: dict) -> list:
    status = exp.get("status", "open")
    return _compact([
        _rich(cid("title"), _title_from_plan(exp)),
        _select(cid("kind"), "experiment"),
        _select(cid("status"), status),
        _user(cid("owner"), _owner_id(exp.get("owner", ""))),
        _rich(cid("params"), _render_params(exp.get("params"))),
        _rich(cid("outcome"), exp.get("outcome", "")),
        _select(cid("polarity"), _POLARITY.get(status, "mentions")),
        _select(cid("trust"), "auto"),
        _date(cid("updated"), exp.get("date", "")),
    ])


# ── main ──────────────────────────────────────────────────────────────────────────────────────────

def _build_client():
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        sys.exit("seed_list: SLACK_BOT_TOKEN is not set (put it in .env). Nothing was called.")
    try:
        from slack_sdk import WebClient
    except Exception as e:  # pragma: no cover - dependency guard
        sys.exit(f"seed_list: slack_sdk is required (pip install -r requirements.txt): {e}")
    return WebClient(token=token)


def main() -> int:
    hyps = STORY.get("hypotheses", []) or []
    exps = STORY.get("experiments", []) or []

    if DRY:
        # Offline preview: fake ids so payloads are fully visible without any network call.
        column_ids = {c["key"]: f"Col_{c['key']}" for c in SCHEMA}
    else:
        from slack_sdk.errors import SlackApiError
        client = _build_client()
        try:
            resp = _as_data(client.api_call("slackLists.create", json={"name": "Lab Record", "schema": SCHEMA}))
        except SlackApiError as e:
            return _fail("slackLists.create", e)
        list_id = _extract_list_id(resp)
        column_ids = _column_map(_extract_columns(resp))
        if not list_id:
            sys.exit("seed_list: slackLists.create returned no list_id — cannot continue.\n"
                     f"  response was: {json.dumps(resp)[:500]}")
        if not column_ids:
            # Fall back to addressing columns by the keys we defined (Slack may accept keys as ids).
            print("  ! no column_ids echoed by create; falling back to schema keys as column ids")
            column_ids = {c["key"]: c["key"] for c in SCHEMA}
        _share_with_channel(client, list_id)   # humans/judges can open the List (else it's bot-only)

    def cid(key: str) -> str:
        # Always resolvable: mapped id, else the key itself (works when keys double as ids).
        return column_ids.get(key, key)

    def create_item(fields: list, parent_item_id: str | None = None) -> str:
        payload = {"list_id": None if DRY else list_id, "initial_fields": fields}
        if parent_item_id:
            payload["parent_item_id"] = parent_item_id
        if DRY:
            tag = "child " if parent_item_id else "parent"
            print(f"  [{tag}] slackLists.items.create initial_fields=")
            print("    " + json.dumps(fields, ensure_ascii=False))
            return f"dry-{parent_item_id or 'root'}-{len(fields)}"
        r = _as_data(client.api_call("slackLists.items.create", json=payload))
        time.sleep(0.3)  # items are Tier 3 (50/min)
        return _extract_item_id(r)

    print(f"Seeding List 'Lab Record': {len(hyps)} hypotheses + {len(exps)} experiments"
          f"{'  (DRY RUN — no API calls)' if DRY else ''}")

    # 1) Hypotheses -> parent rows; remember each row id by its H-id so children can link.
    hypo_row_id: dict[str, str] = {}
    from slack_sdk.errors import SlackApiError  # local import keeps --dry import-light
    try:
        for h in hyps:
            rid = create_item(_hypothesis_fields(cid, h))
            hypo_row_id[h.get("id", "")] = rid
            print(f"  ✓ hypothesis {h.get('id')} ({h.get('status')}) -> {rid or '(no id)'}")

        # 2) Experiments -> child rows under their hypothesis (orphans stay top-level).
        for e in exps:
            parent = hypo_row_id.get(e.get("hypothesis")) if e.get("hypothesis") else None
            rid = create_item(_experiment_fields(cid, e), parent_item_id=parent)
            link = f"under {e.get('hypothesis')}" if parent else "top-level"
            mark = "  [LANDMINE]" if e.get("landmine") else ""
            print(f"  ✓ experiment {e.get('ref')} ({e.get('status')}, {link}){mark} -> {rid or '(no id)'}")
    except SlackApiError as e:
        return _fail("slackLists.items.create", e)

    if DRY:
        print("\nDRY RUN complete — no List was created. Re-run without --dry to write to Slack.")
        return 0

    # 3) Emit CURIE_LIST_ID + cache the schema map (CURIE_LIST_SCHEMA, §4.1).
    try:
        SCHEMA_CACHE.write_text(json.dumps({"list_id": list_id, "columns": column_ids}, indent=2))
        cache_note = f"schema map -> {SCHEMA_CACHE.name}"
    except Exception as ex:
        cache_note = f"(could not write {SCHEMA_CACHE.name}: {ex})"

    print("\n✓ List seeded. Paste this into .env:")
    print(f"CURIE_LIST_ID={list_id}")
    print(f"  {cache_note}")
    return 0


def _share_with_channel(client, list_id: str) -> None:
    """Grant the operating channel READ access so humans (and judges) can open the List instead of
    hitting 'you don't have access'. slackLists.access.set — verified shape (access_level=read,
    channel_ids). Best-effort: a share failure never blocks seeding (rerun scripts.share_list)."""
    channel_id = os.environ.get("CURIE_CHANNEL_ID", "").strip()
    if not channel_id:
        print("  (CURIE_CHANNEL_ID not set — List stays bot-only; run `python -m scripts.share_list` after)")
        return
    try:
        r = _as_data(client.api_call("slackLists.access.set",
                                     json={"list_id": list_id, "access_level": "read",
                                           "channel_ids": [channel_id]}))
        print(f"  ✓ shared List with channel {channel_id} (read)" if r.get("ok")
              else f"  ! could not share List: {r.get('error')} (run `python -m scripts.share_list`)")
    except Exception as ex:
        print(f"  ! could not share List ({ex}); run `python -m scripts.share_list` to retry")


def _fail(where: str, e) -> int:
    err = ""
    try:
        err = e.response.get("error", "")
    except Exception:
        err = str(e)
    print(f"seed_list: {where} failed: {err or e}", file=sys.stderr)
    if err in ("missing_scope", "not_allowed_token_type", "invalid_auth"):
        print("  hint: the bot needs the `lists:write` scope and Agents & AI Apps enabled (backend.md §3).",
              file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
