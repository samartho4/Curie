#!/usr/bin/env python3
"""Curie smoke tests — RUN FIRST (backend.md §12). Results select architecture paths (§14).

Usage:
  python scripts/smoke_tests.py api      # pure Web-API tests (needs SLACK_BOT_TOKEN, CURIE_CHANNEL_ID)
  python scripts/smoke_tests.py listen   # Socket-Mode probe: @mention the app within 120s;
                                         # dumps whether action_token is present (needs SLACK_APP_TOKEN too)
Writes scripts/smoke_results.json. Never prints tokens.
"""
import json, os, sys, time
from dotenv import load_dotenv
load_dotenv()
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

BOT = os.environ.get("SLACK_BOT_TOKEN"); USER = os.environ.get("CURIE_USER_TOKEN")
CH  = os.environ.get("CURIE_CHANNEL_ID")
results = {}

def record(name, ok, detail=""):
    results[name] = {"ok": ok, "detail": str(detail)[:300]}
    print(f"{'✅' if ok else '❌'} {name}: {detail}")

def api_error(e): return e.response.get("error", str(e)) if isinstance(e, SlackApiError) else str(e)

def t_lists(c):
    """#6 Lists end-to-end: create w/ full schema incl message+canvas cols, parent+child rows."""
    schema = [
      {"key":"title","name":"Title","type":"text","is_primary_column":True},
      {"key":"status","name":"Status","type":"select","options":{"format":"single_select","choices":[
        {"value":"open","label":"Open","color":"yellow"},{"value":"failed","label":"Failed","color":"red"}]}},
      {"key":"owner","name":"Owner","type":"user","options":{"format":"single_entity"}},
      {"key":"source","name":"Source message","type":"message"},
      {"key":"notebook","name":"Notebook","type":"canvas"}]
    r = c.api_call("slackLists.create", json={"name":"SMOKE Lab Record (delete me)","schema":schema})
    lid = r["list_id"]; cols = {col["key"]: col["id"] for col in r.get("list_metadata",{}).get("schema",[])}
    rt = lambda s: [{"type":"rich_text","elements":[{"type":"rich_text_section","elements":[{"type":"text","text":s}]}]}]
    p = c.api_call("slackLists.items.create", json={"list_id":lid,"initial_fields":[
        {"column_id":cols["title"],"rich_text":rt("H-smoke: parent hypothesis")}]})
    ch = c.api_call("slackLists.items.create", json={"list_id":lid,"parent_item_id":p["item"]["id"],
        "initial_fields":[{"column_id":cols["title"],"rich_text":rt("Exp-smoke: child row")}]})
    return f"list={lid} parent={p['item']['id']} child={ch['item']['id']} cols={list(cols)}"

def t_search_info(c):
    """#7 semantic vs keyword"""
    r = c.api_call("assistant.search.info")
    return json.dumps({k:v for k,v in r.data.items() if k!="ok"})[:250]

def t_rts_bot_no_token(c):
    """#1b expected FAIL: bot-token RTS without action_token (documents the requirement)"""
    try:
        c.api_call("assistant.search.context", json={"query":"smoke test query","limit":1})
        return (True, "unexpectedly succeeded — bot RTS may not need action_token on this sandbox!")
    except SlackApiError as e:
        return (True, f"failed as documented → error='{api_error(e)}' (action_token required)")

def t_rts_user(c_user):
    """#5 user-token RTS without action_token"""
    r = c_user.api_call("assistant.search.context", json={"query":"experiment","limit":3,
        "channel_types":["public_channel"],"content_types":["messages"]})
    msgs = r.get("results",{}).get("messages",[])
    return f"{len(msgs)} results; keys={list(msgs[0].keys())[:8] if msgs else 'n/a'}"

def t_stream(c):
    """#4 plan-mode streaming available?"""
    r = c.api_call("chat.startStream", json={"channel":CH,"task_display_mode":"plan",
        "chunks":[{"type":"markdown_text","markdown_text":"smoke: stream probe"}]})
    ts = r.get("ts") or r.get("message_ts")
    c.api_call("chat.stopStream", json={"channel":CH,"ts":ts,
        "chunks":[{"type":"markdown_text","markdown_text":"done"}]})
    return f"stream ok ts={ts}"

def t_canvas(c):
    r = c.api_call("canvases.create", json={"title":"SMOKE canvas (delete me)",
        "document_content":{"type":"markdown","markdown":"# Smoke\nEvery line cites its message."}})
    return f"canvas_id={r.get('canvas_id')}"

def t_agent_view_probe(c):
    """#8 which messaging experience? Inspect app config indirectly via auth + note for manual check."""
    who = c.auth_test()
    return f"bot={who['user']} team={who['team']} — verify Agents & AI Apps toggle + Agent (not Assistant) experience in App Settings UI"

def run_api():
    c = WebClient(token=BOT)
    for name, fn, cl in [
        ("6_lists_e2e", t_lists, c), ("7_search_info", t_search_info, c),
        ("1b_rts_bot_no_actiontoken", t_rts_bot_no_token, c),
        ("4_streaming", t_stream, c), ("canvas_create", t_canvas, c),
        ("8_agent_view_probe", t_agent_view_probe, c)]:
        try:
            out = fn(cl)
            if isinstance(out, tuple): record(name, out[0], out[1])
            else: record(name, True, out)
        except Exception as e: record(name, False, api_error(e))
    if USER:
        try: record("5_rts_user_token", True, t_rts_user(WebClient(token=USER)))
        except Exception as e: record("5_rts_user_token", False, api_error(e))
    else: record("5_rts_user_token", False, "CURIE_USER_TOKEN not set — Trigger C undecided")
    print("\nNOTE #3 (bot- vs user-authored searchability) needs seeded messages — rerun after seed: eval via 5_rts_user_token query hits.")

def run_listen():
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler
    app = App(token=BOT)
    @app.event("app_mention")
    def h(body, event, say):
        keys = sorted(event.keys())
        has = "action_token" in event or "action_token" in body.get("event", {})
        record("1_app_mention_action_token", has, f"event keys={keys}")
        say(text=f"smoke: action_token present = {has}", thread_ts=event.get("thread_ts") or event["ts"])
        json.dump(results, open("scripts/smoke_results.json","w"), indent=2); os._exit(0)
    @app.event("message")
    def dm(body, event):
        if event.get("channel_type") == "im":
            has = "action_token" in event
            record("2_message_im_action_token", has, f"keys={sorted(event.keys())}")
    print("Listening 120s — @mention the app in #experiments (and DM it) now…")
    h = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]); h.connect(); time.sleep(120); h.close()

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "api"
    (run_listen if mode == "listen" else run_api)()
    json.dump(results, open("scripts/smoke_results.json","w"), indent=2)
    print("\nSaved scripts/smoke_results.json — feed this file to the coding agent; it selects §14 fallbacks.")
