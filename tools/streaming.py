"""Plan-mode streaming for Curie's verdict (frontend.md §4A).

Live-verified shapes (Jul 10, this sandbox):
  chat.startStream REQUIRES thread_ts, and in a CHANNEL also recipient_team_id + recipient_user_id.
  Use top-level `markdown_text` consistently for start/append (mixing chunk modes → streaming_mode_mismatch).
  stopStream can carry final `blocks` (the Block Kit verdict card).
Every method degrades gracefully: if streaming is unavailable, we fall back to a single chat.postMessage
so the verdict ALWAYS lands (backend.md §14 kill-switch).
"""
from __future__ import annotations
from slack_sdk.errors import SlackApiError


class Streamer:
    def __init__(self, client, channel, thread_ts, recipient_user_id=None, recipient_team_id=None):
        self.c = client
        self.channel = channel
        self.thread_ts = thread_ts
        self.uid = recipient_user_id
        self.team = recipient_team_id
        self.ts = None
        self.ok = False          # streaming active?
        self._buf = "*Checking priors…*"

    def start(self, text="*Checking priors…*"):
        self._buf = text
        payload = {"channel": self.channel, "thread_ts": self.thread_ts,
                   "task_display_mode": "plan", "markdown_text": text}
        if self.uid:
            payload["recipient_user_id"] = self.uid
        if self.team:
            payload["recipient_team_id"] = self.team
        try:
            r = self.c.api_call("chat.startStream", json=payload)
            self.ts = r.get("ts") or r.get("message_ts")
            self.ok = bool(self.ts)
        except SlackApiError:
            self.ok = False
        return self.ok

    def step(self, line: str):
        """Append a progress line (e.g. '✓ Searched the record — 3 hits')."""
        self._buf += f"\n{line}"
        if not self.ok:
            return
        try:
            self.c.api_call("chat.appendStream",
                            json={"channel": self.channel, "ts": self.ts, "markdown_text": f"\n{line}"})
        except SlackApiError:
            self.ok = False  # stop trying; stop() will fall back

    def stop(self, blocks, fallback_text="Curie verdict"):
        """Finalize with the Block Kit verdict card. Falls back to postMessage if streaming failed."""
        if self.ok and self.ts:
            try:
                self.c.api_call("chat.stopStream",
                                json={"channel": self.channel, "ts": self.ts,
                                      "blocks": blocks, "text": fallback_text})
                return self.ts
            except SlackApiError:
                pass  # fall through to postMessage
        # fallback: single message in-thread with the card
        r = self.c.chat_postMessage(channel=self.channel, thread_ts=self.thread_ts,
                                    blocks=blocks, text=fallback_text)
        return r.get("ts")
