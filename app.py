"""app.py — Curie's entrypoint. Bolt for Python, Socket Mode (backend.md N4, CLAUDE.md agent_view).

    python app.py

Needs SLACK_BOT_TOKEN + SLACK_APP_TOKEN in .env (see .env.sample). No public URL (Socket Mode).
Fails with a readable message — never a stack trace — if required config is missing.
"""
from __future__ import annotations
import os, sys
from dotenv import load_dotenv

load_dotenv()


def _require(*names):
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        print("Curie can't start — missing env vars: " + ", ".join(missing))
        print("Set them in .env (see .env.sample), then re-run `python app.py`.")
        sys.exit(1)


def main():
    _require("SLACK_BOT_TOKEN", "SLACK_APP_TOKEN")
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler
    from listeners import app_mention, reaction_added, app_home, ambient, standing

    app = App(token=os.environ["SLACK_BOT_TOKEN"])
    app_mention.register(app)
    reaction_added.register(app)   # 🧪 → log result to the Lab Record
    app_home.register(app)         # App Home dashboard
    ambient.register(app)          # run-record ingest + belief alert + ambient preflight
    standing.register(app)         # 'from now on' standing watch + weekly digest
    ambient.start_run_poller(app)  # fallback ingest via conversations.history (message.channels
                                   # isn't delivered on this workspace; poll instead)

    # Startup probe (non-fatal): which search mode does this sandbox give us?
    try:
        from tools.rts import search_mode
        mode = search_mode(app.client)
        print(f"Curie: RTS search mode = {mode}")
    except Exception:
        pass
    if not os.environ.get("CURIE_LIST_ID"):
        print("Curie: no CURIE_LIST_ID set — running RTS-only (Lab Record read path disabled).")

    print("Curie is listening (Socket Mode). Mention @Prior in your #experiments channel, or DM it.")
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()


if __name__ == "__main__":
    main()
