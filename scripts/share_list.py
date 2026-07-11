"""share_list.py — grant humans read access to the bot-owned Lab Record List.

WHY: `slackLists.create` makes the List owned by the bot only, so a human (or a judge)
who clicks "Open the Lab Record" in the App Home hits "You don't have access to this list."
This shares the List (read-only) with the channel Curie operates in, so every channel member
can open the real native Slack List. Uses the sanctioned method — verified against docs.slack.dev:

    slackLists.access.set(list_id, access_level, channel_ids=[...] | user_ids=[...])
      access_level: "read" (view) | "write" (view+edit) | "owner" (users only)
      pass channel_ids OR user_ids, never both.  Needs the `lists:write` scope (bot already has it).

Run it once against the already-created List:

    python -m scripts.share_list                     # share CURIE_LIST_ID -> CURIE_CHANNEL_ID (read)
    python -m scripts.share_list --write             # grant edit too
    python -m scripts.share_list --user U012ABC      # also grant a specific person (e.g. a judge)

Reads config from .env (SLACK_BOT_TOKEN, CURIE_LIST_ID, CURIE_CHANNEL_ID). Never prints secrets.
Failure-tolerant: a bad token or missing scope prints a human hint, never a stack trace.
"""
from __future__ import annotations
import os, sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass  # env may already be exported


def _client():
    token = os.environ.get("SLACK_BOT_TOKEN")
    if not token:
        sys.exit("share_list: SLACK_BOT_TOKEN is not set (put it in .env). Nothing was called.")
    try:
        from slack_sdk import WebClient
    except Exception as e:  # pragma: no cover
        sys.exit(f"share_list: slack_sdk is required (pip install -r requirements.txt): {e}")
    return WebClient(token=token)


def main() -> int:
    list_id = os.environ.get("CURIE_LIST_ID", "").strip()
    channel_id = os.environ.get("CURIE_CHANNEL_ID", "").strip()
    if not list_id:
        sys.exit("share_list: CURIE_LIST_ID is not set (run seed.seed_list first, then paste it into .env).")

    access_level = "write" if "--write" in sys.argv else "read"
    user_ids = [sys.argv[i + 1] for i, a in enumerate(sys.argv) if a == "--user" and i + 1 < len(sys.argv)]

    client = _client()
    from slack_sdk.errors import SlackApiError

    # 1) share with the operating channel so every member (incl. judges added to it) can view.
    if channel_id:
        _try_set(client, list_id, access_level, channel_ids=[channel_id])
    else:
        print("share_list: CURIE_CHANNEL_ID not set — skipping channel share (set it in .env to share to #experiments).")

    # 2) optionally grant named people directly (judges by user id).
    if user_ids:
        _try_set(client, list_id, access_level, user_ids=user_ids)

    print("\nDone. Open the App Home → 'Open the Lab Record' should now load the native List.")
    return 0


def _try_set(client, list_id, access_level, *, channel_ids=None, user_ids=None):
    from slack_sdk.errors import SlackApiError
    target = f"channel {channel_ids}" if channel_ids else f"user(s) {user_ids}"
    payload = {"list_id": list_id, "access_level": access_level}
    if channel_ids:
        payload["channel_ids"] = channel_ids
    if user_ids:
        payload["user_ids"] = user_ids
    try:
        r = client.api_call("slackLists.access.set", json=payload)
        data = r.data if hasattr(r, "data") else r
        if data.get("ok"):
            print(f"  ✓ granted '{access_level}' access to {target}")
        else:
            print(f"  ! access.set returned not-ok for {target}: {data.get('error')}")
    except SlackApiError as e:
        err = ""
        try:
            err = e.response.get("error", "")
        except Exception:
            err = str(e)
        print(f"  ✗ access.set failed for {target}: {err or e}")
        if err in ("missing_scope",):
            print("    hint: the bot needs the `lists:write` scope (reinstall after adding it).")
        elif err in ("paid_teams_only", "not_allowed_token_type"):
            print("    hint: Lists require a paid workspace and a bot token with lists:write.")


if __name__ == "__main__":
    raise SystemExit(main())
