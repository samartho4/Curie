"""rts.py — Slack Real-Time Search wrapper over `assistant.search.context` (backend.md §5.1).

Rules baked in here so callers can't get them wrong:
  * Bot token REQUIRES an action_token (present only in app_mention / message.im). No token → no search.
  * User token needs no action_token (Trigger C path).
  * Hard budget of <=3 search calls per verdict (backend N3). Over budget → returns [] silently.
  * NEVER persists results (backend N2) — everything stays in memory, returned as plain dicts.
  * Filters out Curie's own bot messages so we don't cite ourselves.
  * Graceful 429: one retry after Retry-After, then [] with degraded=True.

Returns normalized dicts (NOT pydantic) so this stays a pure API wrapper; pipeline maps them to
Candidate. Shape: {"source":"rts","title","permalink","outcome":None,"params":{},"text","channel","ts"}.
"""
from __future__ import annotations
import re, time
from slack_sdk.errors import SlackApiError

_FORMAT_RE = re.compile(r"<([^|>]+)\|([^>]+)>")          # <url|label> -> label
_MENTION_RE = re.compile(r"<[@#!][^>]+>")                # user/channel/special mentions
_EMOJI_RE = re.compile(r":[a-z0-9_+\-]+:")


def strip_slack_formatting(text: str) -> str:
    if not text:
        return ""
    text = _FORMAT_RE.sub(r"\2", text)
    text = _MENTION_RE.sub("", text)
    text = _EMOJI_RE.sub("", text)
    text = text.replace("*", "").replace("_", "").replace("`", "")
    return re.sub(r"\s+", " ", text).strip()


def search_mode(client) -> str:
    """'semantic' if the sandbox has Slack AI Search, else 'keyword'. Cached on the client object."""
    cached = getattr(client, "_curie_search_mode", None)
    if cached:
        return cached
    mode = "keyword"
    try:
        r = client.api_call("assistant.search.info")
        data = r.data if hasattr(r, "data") else r
        if data.get("semantic_search_enabled") or data.get("is_semantic_search_enabled"):
            mode = "semantic"
    except Exception:
        mode = "keyword"
    try:
        client._curie_search_mode = mode
    except Exception:
        pass
    return mode


class RTS:
    """One instance per verdict — carries the <=3-call budget."""

    def __init__(self, client, *, action_token=None, is_user_token=False,
                 own_bot_user_id=None, own_msg_ts=None, budget=3):
        self.client = client
        self.action_token = action_token
        self.is_user_token = is_user_token
        self.own_bot_user_id = own_bot_user_id
        self.own_msg_ts = str(own_msg_ts) if own_msg_ts else None  # triggering message — never cite it
        self.budget = budget
        self.degraded = False

    def _can_search(self) -> bool:
        if self.budget <= 0:
            return False
        if not self.is_user_token and not self.action_token:
            return False  # bot token with no action_token cannot call RTS
        return True

    def search(self, query: str, *, limit: int = 20) -> list[dict]:
        if not query or not self._can_search():
            return []
        self.budget -= 1
        payload = {
            "query": strip_slack_formatting(query),
            "channel_types": ["public_channel"],
            "content_types": ["messages"],
            "include_context_messages": True,
            "limit": limit,
            "sort": "score",
        }
        if not self.is_user_token and self.action_token:
            payload["action_token"] = self.action_token
        try:
            r = self._call(payload)
        except SlackApiError as e:
            if e.response.get("error") == "ratelimited":
                delay = int(e.response.headers.get("Retry-After", "2")) if getattr(e.response, "headers", None) else 2
                time.sleep(min(delay, 5))
                try:
                    r = self._call(payload)
                except Exception:
                    self.degraded = True
                    return []
            else:
                self.degraded = True
                return []
        except Exception:
            self.degraded = True
            return []
        return self._normalize(r)

    def _call(self, payload):
        r = self.client.api_call("assistant.search.context", json=payload)
        return r.data if hasattr(r, "data") else r

    def _normalize(self, r) -> list[dict]:
        # Verified against docs.slack.dev (Real-Time Search API) via context7, Jul 10:
        # each match = {author_name, author_user_id, channel_id, channel_name,
        #               message_ts, thread_ts, content, permalink, context_messages}.
        # Fallbacks (text/channel/ts/user) keep us robust if the sandbox differs.
        messages = (r.get("results") or {}).get("messages") or []
        # Dotless form of our own ts (e.g. "p1783722835912419") — how it appears inside a permalink;
        # lets us self-exclude even when the ts field lands under an unexpected key in the payload.
        own_perma_frag = ("p" + self.own_msg_ts.replace(".", "")) if self.own_msg_ts else None
        out = []
        for m in messages:
            author = m.get("author_user_id") or m.get("user")
            if self.own_bot_user_id and author == self.own_bot_user_id:
                continue
            channel = m.get("channel_id") or m.get("channel")
            ts = m.get("message_ts") or m.get("ts") or m.get("thread_ts")
            permalink = m.get("permalink") or _archive_link(channel, ts)
            # The plan we're checking is itself indexed — never collide with it. Match on the ts field
            # AND on the permalink (belt-and-suspenders: the permalink encodes the ts even if the
            # response nests/renames the ts field). Biasing toward dropping a self-hit is safe (§13).
            if self.own_msg_ts and _ts_eq(ts, self.own_msg_ts):
                continue
            if own_perma_frag and permalink and own_perma_frag in permalink.replace(".", ""):
                continue
            text = strip_slack_formatting(m.get("content") or m.get("text") or "")
            if not text:
                continue
            out.append({
                "source": "rts",
                "title": text[:90],
                "text": text,
                "permalink": permalink,
                "outcome": None,
                "params": {},
                "channel": channel,
                "ts": ts,
                "author": author,
            })
        return out


def _archive_link(channel, ts) -> str:
    if not channel or not ts:
        return ""
    return f"https://slack.com/archives/{channel}/p{str(ts).replace('.', '')}"


def _ts_eq(a, b) -> bool:
    """Slack ts equality that tolerates float/str drift and the dotless permalink form."""
    if not a or not b:
        return False
    a, b = str(a).strip(), str(b).strip()
    return a == b or a.replace(".", "") == b.replace(".", "")
