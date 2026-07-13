#!/usr/bin/env python3
"""apply_manifest.py — push manifest.json to the Slack app config via `apps.manifest.update`.

This makes the app's Event Subscriptions + scopes reproducible from version control instead of
hand-toggling the dashboard. The one change that fixes the ambient run-record ingest is the
`message.channels` bot event (already present in manifest.json).

Requires an *App Configuration Token* (xoxe-...), NOT a bot/user token. Generate one at
https://api.slack.com/apps → "Your App Configuration Tokens" (or `slack` CLI). Then:

    export SLACK_CONFIG_ACCESS_TOKEN=xoxe-...
    export SLACK_APP_ID=A0BH...            # your app id
    python scripts/apply_manifest.py

Notes on what takes effect immediately vs. needs a reinstall:
  * Adding/removing an EVENT (e.g. message.channels) takes effect without reinstall.
  * Adding a bot SCOPE (e.g. channels:history) requires you to REINSTALL the app afterward
    (Slack will not grant a new scope until the user re-approves). This script prints a
    reminder; it cannot perform the reinstall (that is an OAuth approval the human must click).

Never prints token values. Read-your-own-config only.
"""
from __future__ import annotations

import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

API = "https://slack.com/api/apps.manifest.update"
ROOT = pathlib.Path(__file__).resolve().parent.parent


def _require(name: str) -> str:
    val = os.environ.get(name)
    if not val:
        sys.exit(f"apply_manifest: missing env var {name} (see the module docstring).")
    return val


def main() -> None:
    token = _require("SLACK_CONFIG_ACCESS_TOKEN")   # xoxe-... app configuration token
    app_id = _require("SLACK_APP_ID")

    manifest_path = ROOT / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text())
    except Exception as e:                            # noqa: BLE001
        sys.exit(f"apply_manifest: could not read/parse {manifest_path}: {e}")

    body = urllib.parse.urlencode({
        "app_id": app_id,
        "manifest": json.dumps(manifest),
    }).encode()
    req = urllib.request.Request(
        API, data=body,
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:                            # noqa: BLE001
        sys.exit(f"apply_manifest: request failed: {e}")

    if not data.get("ok"):
        # Slack returns granular errors under 'errors' for manifest validation.
        print("apply_manifest: FAILED —", data.get("error"))
        for err in data.get("errors", []) or []:
            print("   •", err.get("message") or err)
        sys.exit(1)

    print("apply_manifest: OK — manifest applied to", app_id)
    if data.get("permissions_updated"):
        print("   ⚠ Bot scopes changed → you MUST reinstall the app (OAuth re-approval) for")
        print("     the new scope (channels:history) to take effect, then restart the service.")
    else:
        print("   Event subscription updated. message.channels is now active; no reinstall needed")
        print("     if channels:history was already granted. Restart the service to reconnect.")


if __name__ == "__main__":
    main()
