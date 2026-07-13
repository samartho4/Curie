"""reset_demo.py — strip today's DEMO/TEST messages out of #experiments so the channel is pristine
for recording. The seeded Anika/Marco/Priya history is NEVER touched.

SAFE BY DESIGN:
  * Dry-run by default — prints exactly what it WOULD delete, deletes nothing.
  * Pass --go to actually delete.
  * Only removes messages that match test markers (Curie's own card/alert text, the `📊 Run exp-301/
    exp-314` records) or that start with a user @mention (the `@Curie …` probes). Seed messages are
    plain scientist chatter and match none of these.

    python -m scripts.reset_demo          # dry run — review the list first
    python -m scripts.reset_demo --go     # delete for real

Deletion uses the user (workspace-owner) token when present (it can remove anyone's messages,
including the Claude-app run records), and falls back to the bot token for Curie's own messages.
Anything it can't delete is reported so you can remove those few by hand.
"""
from __future__ import annotations
import os, sys, time
from dotenv import load_dotenv
load_dotenv()
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

CH = os.environ["CURIE_CHANNEL_ID"]
GO = "--go" in sys.argv
bot = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
owner_tok = os.environ.get("CURIE_USER_TOKEN") or os.environ.get("SEED_USER_TOKEN_1")
owner = WebClient(token=owner_tok) if owner_tok else None

# Phrases that ONLY appear in demo/test output — never in the seeded lab chatter.
MARKERS = (
    "📊 run exp-301", "📊 run exp-314", "| status: succeeded", "| status: failed |",
    "checking priors", "searching the lab's memory", "this was already tried",
    "close to earlier work", "no prior work found on this", "where the lab stands",
    "i don't see that in the record", "evidence per hypothesis", "compiled by curie",
    "heads up", "what differs from last time", "proceed anyway", "full comparison",
)

def is_test(m: dict) -> bool:
    t = (m.get("text") or "").lower()
    # a message that starts with a user mention is a `@Curie …` probe
    if (m.get("text") or "").lstrip().startswith("<@"):
        return True
    # Block Kit cards carry their text in blocks; flatten a little
    if not t:
        t = str(m.get("blocks") or "").lower()
    return any(mk in t for mk in MARKERS)

def preview(m: dict) -> str:
    txt = (m.get("text") or "").replace("\n", " ")
    if not txt and m.get("blocks"):
        txt = "[block-kit card]"
    return txt[:80]

def collect() -> list[dict]:
    victims, seen = [], set()
    cursor = None
    while True:
        r = bot.conversations_history(channel=CH, limit=200, cursor=cursor)
        for m in r.get("messages", []):
            parent_test = is_test(m)
            if parent_test and m["ts"] not in seen:
                victims.append(m); seen.add(m["ts"])
            # if the top-level message is a probe/card, its whole thread is demo too
            if m.get("reply_count"):
                rr = bot.conversations_replies(channel=CH, ts=m["ts"], limit=200)
                for rm in rr.get("messages", [])[1:]:
                    if (parent_test or is_test(rm)) and rm["ts"] not in seen:
                        victims.append(rm); seen.add(rm["ts"])
        cursor = (r.get("response_metadata") or {}).get("next_cursor")
        if not cursor:
            break
    # delete newest first so thread parents go after their replies
    victims.sort(key=lambda m: float(m["ts"]), reverse=True)
    return victims

def delete(m: dict) -> bool:
    for client in (owner, bot):
        if not client:
            continue
        try:
            client.chat_delete(channel=CH, ts=m["ts"])
            return True
        except SlackApiError:
            continue
    return False

def main() -> int:
    victims = collect()
    print(f"\n{'DELETING' if GO else 'DRY RUN — would delete'} {len(victims)} message(s) in {CH}:\n")
    for m in victims:
        print(f"  {m['ts']}  {preview(m)}")
    if not GO:
        print("\n(nothing deleted) — re-run with --go to delete these.")
        return 0
    ok = fail = 0
    for m in victims:
        if delete(m):
            ok += 1
        else:
            fail += 1
            print(f"  ! could not delete {m['ts']} — remove by hand: {preview(m)}")
        time.sleep(0.4)
    print(f"\n✓ deleted {ok}; {fail} left for manual cleanup.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
