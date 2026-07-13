#!/usr/bin/env python3
"""verify_ambient.py — prove the ambient run-record ingest works end-to-end on the LIVE bot.

Run this AFTER adding the `message.channels` event (+ `channels:history` scope) and restarting
the service. It posts one run-record to #experiments using the developer USER token (so it looks
like another agent posted it — the bot must not ignore it as its own), waits, then checks whether
the bot posted a top-level proactive belief-change alert.

    export SLACK_BOT_TOKEN=xoxb-...        # to auth.test + read the channel
    export CURIE_USER_TOKEN=xoxp-...       # to POST the run-record as a non-bot user
    export CURIE_CHANNEL_ID=C0BG...        # #experiments
    python scripts/verify_ambient.py

Safe + idempotent-ish: only posts to CURIE_CHANNEL_ID, one probe message per run. Never prints
tokens. This is a diagnostic, not part of the app.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request

BASE = "https://slack.com/api/"
ALERT_PREFIX = "⚠️ Heads up"   # "⚠️ Heads up" — the belief-change alert opener


def _call(method: str, token: str, **params) -> dict:
    body = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(
        BASE + method, data=body,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _need(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        sys.exit(f"verify_ambient: missing env var {name} (see the module docstring).")
    return v


def main() -> None:
    bot = _need("SLACK_BOT_TOKEN")
    channel = _need("CURIE_CHANNEL_ID")
    user = os.environ.get("CURIE_USER_TOKEN")

    auth = _call("auth.test", bot)
    if not auth.get("ok"):
        sys.exit(f"verify_ambient: auth.test failed: {auth.get('error')}")
    print(f"verify_ambient: bot OK as @{auth.get('user')} in team {auth.get('team')}")

    if not user:
        print("verify_ambient: no CURIE_USER_TOKEN set — cannot post a non-bot probe. Post a")
        print("   '\U0001f4ca Run ... | status: failed | params: ...' message yourself, then re-check.")
        return

    probe = ("\U0001f4ca Run verify-{n} | status: failed | outcome: probe run for wiring check "
             "| params: model=probe, lr=1e-4, batch=32, split=v1").format(n=int(time.time()) % 100000)
    sent = _call("chat.postMessage", user, channel=channel, text=probe)
    if not sent.get("ok"):
        sys.exit(f"verify_ambient: could not post probe: {sent.get('error')}")
    print("verify_ambient: probe run-record posted; waiting 10s for the bot to ingest…")
    time.sleep(10)

    hist = _call("conversations.history", bot, channel=channel, limit="8")
    if not hist.get("ok"):
        sys.exit(f"verify_ambient: conversations.history failed: {hist.get('error')}")
    alerts = [m for m in hist.get("messages", [])
              if (m.get("text") or "").startswith(ALERT_PREFIX)]
    if alerts:
        print("verify_ambient: PASS ✅ — bot posted a proactive belief-change alert:")
        print("   ", (alerts[0].get("text") or "")[:160])
    else:
        print("verify_ambient: FAIL ❌ — no top-level '⚠️ Heads up' alert appeared.")
        print("   Check: (1) message.channels is in Event Subscriptions, (2) channels:history")
        print("   scope is granted (reinstall if just added), (3) the bot is a member of the")
        print("   channel, (4) the service was restarted, (5) CURIE_CHANNEL_ID matches this channel.")
        sys.exit(1)


if __name__ == "__main__":
    main()
