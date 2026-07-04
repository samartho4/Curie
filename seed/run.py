"""Seed the sandbox with the Antimatter Lab's ~6 months of history (backend.md §9).

Bot-persona authorship (decided Jul 10): posts via bot token with a per-persona display name.
Requires the `chat:write.customize` scope for username/icon override — if absent, falls back to a
"*Name:* text" prefix so authorship is still legible (uglier, but zero-scope). Smoke test #3 then
confirms RTS finds these messages (include_bots=true in tools/rts.py).

Idempotent-ish: writes seed/seed_state.json (ts of every posted message) so a re-run can skip/clean.
Narrative DATES live in the message text (Slack timestamps will be "now" — normal, judges read text).

    python -m seed.run           # post everything to #experiments (+ general flavor to #general)
    python -m seed.run --dry     # print what would post, call nothing
"""
from __future__ import annotations
import json, os, sys, time, pathlib, yaml
from dotenv import load_dotenv
load_dotenv()
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

ROOT = pathlib.Path(__file__).parent
STORY = yaml.safe_load((ROOT / "lab_story.yaml").read_text())
STATE = ROOT / "seed_state.json"
DRY = "--dry" in sys.argv

BOT = os.environ["SLACK_BOT_TOKEN"]
CH = os.environ["CURIE_CHANNEL_ID"]
GENERAL = os.environ.get("CURIE_GENERAL_ID")  # optional; else general flavor also goes to #experiments
client = WebClient(token=BOT)

PERSONA_ICON = {"anika": ":woman_scientist:", "marco": ":man_scientist:", "priya": ":scientist:"}
NAME = {m["handle"]: m["name"] for m in STORY["members"]}
_customize_ok = True  # flips false on first scope error
posted: list[dict] = []


def _post(channel, who, text, thread_ts=None):
    global _customize_ok
    name = NAME.get(who, who)
    if DRY:
        print(f"  [{channel}] {name}: {text[:70]}{'  ⤷reply' if thread_ts else ''}")
        return {"ts": f"dry-{len(posted)}"}
    kwargs = dict(channel=channel, text=text, thread_ts=thread_ts)
    if _customize_ok:
        kwargs.update(username=name, icon_emoji=PERSONA_ICON.get(who, ":test_tube:"))
    try:
        r = client.chat_postMessage(**kwargs)
    except SlackApiError as e:
        if _customize_ok and e.response.get("error") in ("missing_scope", "not_allowed"):
            print("  ! chat:write.customize missing — falling back to name-prefix authorship")
            _customize_ok = False
            r = client.chat_postMessage(channel=channel, text=f"*{name}:* {text}", thread_ts=thread_ts)
        else:
            raise
    posted.append({"channel": channel, "ts": r["ts"], "who": who})
    time.sleep(0.4)  # gentle on rate limits
    return r


def _react(channel, ts, emoji):
    if DRY:
        print(f"    +:{emoji}:")
        return
    try:
        client.reactions_add(channel=channel, timestamp=ts, name=emoji)
    except SlackApiError:
        pass


def seed_experiments():
    for exp in STORY["experiments"]:
        head = _post(CH, exp["owner"], exp["plan"])
        parent = head["ts"]
        for msg in exp.get("thread", []):
            _post(CH, msg["who"], msg["text"], thread_ts=parent)
        # outcome reaction: failures get a marker so 🧪-logging has something to grab in the demo
        if exp["status"] == "failed":
            _react(CH, parent, "test_tube")
        print(f"✓ seeded {exp['ref']} ({exp['status']}{'  [LANDMINE]' if exp.get('landmine') else ''})")


def seed_flavor():
    gen = GENERAL or CH
    for m in STORY.get("general", []):
        _post(gen, m["who"], m["text"])
    for m in STORY.get("paper_club", []):
        _post(CH, m["who"], m["text"])
    print("✓ seeded paper-club + general flavor")


if __name__ == "__main__":
    print(f"Seeding '{STORY['lab']['name']}' → channel {CH}{'  (DRY RUN)' if DRY else ''}")
    seed_experiments()
    seed_flavor()
    if not DRY:
        STATE.write_text(json.dumps(posted, indent=2))
        print(f"\n✓ {len(posted)} messages posted. State → {STATE.name}")
        print("Next: run smoke test #3 — search for 'ESM lr 1e-4' via user token; confirm these are found.")
