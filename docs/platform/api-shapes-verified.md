# Verified Slack API shapes (via context7 /websites/slack_dev + live sandbox tests, Jul 10)

These are CONFIRMED against docs + the live Prior Lab sandbox. Build against THESE, don't guess.
Column ids for our List live in `seed/curie_list_schema.json` (keys: title, kind, status, owner, params,
outcome, polarity, source, notebook, trust, updated). CURIE_LIST_ID=F0BGA5Y80P5.

## app_home_opened → views.publish  (App Home dashboard)
```python
@app.event("app_home_opened")
def home(client, event, logger):
    if event.get("tab") != "home":      # event has a `tab` field; only publish for the Home tab
        return
    client.views_publish(user_id=event["user"], view={"type":"home","blocks":[ ... ]})
```
- Home tab must be enabled in app config (it is). Publish per-user. `event["view"]` holds current state if
  published before. Interactions come as `block_actions` (handle with `@app.action("action_id")`).

## reaction_added  (🧪 result-logging trigger)
```python
@app.event("reaction_added")
def on_react(event, client):
    if event["reaction"] != "test_tube":      # emoji NAME, no colons
        return
    ch = event["item"]["channel"]; ts = event["item"]["ts"]   # the message reacted to
    who = event["user"]                                        # who reacted
    # fetch the message text: client.conversations_replies(channel=ch, ts=ts) or conversations_history(latest=ts, inclusive, limit=1)
```
- `event["item"]` = {type:"message", channel, ts}. `item_user` = original author (may be absent).
- Needs `reactions:read` (have it). To get text, `conversations.history`/`replies` (have channels:history).

## slackLists.items.update  (write outcome/status back to a row)
NOTE: update uses `cells` (with row_id per cell), NOT `initial_fields`.
```python
client.api_call("slackLists.items.update", json={"list_id": LID, "cells": [
  {"row_id": ROW, "column_id": cols["status"],  "select": ["failed"]},
  {"row_id": ROW, "column_id": cols["outcome"], "rich_text": [RT("NaN at epoch 3 — gradient collapse")]},
  {"row_id": ROW, "column_id": cols["trust"],   "select": ["auto"]},
]})
# RT(text) = {"type":"rich_text","elements":[{"type":"rich_text_section","elements":[{"type":"text","text":text}]}]}
```
- select → list of option values; rich_text → list of blocks; date → ["YYYY-MM-DD"] (ARRAY, confirmed live);
  user → [Uxxxx]. Response is just {"ok": true} or {"ok": false, "error": "invalid_row_id"}.
- Child rows carry `parent_record_id` (NOT parent_item_id) on READ — verified live Jul 10.
- Find the row to update: `slackLists.items.list` then match by title (record_store already reads this shape).
- To CREATE a new row instead, use `slackLists.items.create(list_id, parent_item_id?, initial_fields=[...])`.

## Already-verified shapes (from earlier this session)
- RTS `assistant.search.context`: results.messages[].{content, permalink, channel_id, message_ts, author_user_id,
  thread_ts, context_messages}. Bot token REQUIRES action_token; user token does not. (tools/rts.py fixed.)
- `slackLists.items.list`: items[].fields[].{key, value, column_id, text (flattened), rich_text, select[], date[],
  user[], message[]} + response_metadata.next_cursor. (tools/record_store.py reads this.)
- Streaming: chat.startStream requires thread_ts (+ recipient_user_id + recipient_team_id in a channel);
  use top-level markdown_text consistently; stopStream can carry final `blocks`. (tools/streaming.py.)
