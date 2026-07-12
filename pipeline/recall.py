"""recall.py — answer "why did we drop X?" questions from the lab's own Slack record.

The payoff beat (demo-script §PAYOFF): a new teammate asks Curie the exact question the cold open
planted — "@Curie why did we drop the full ESM fine-tune?" — and gets the reason *plus a permalink*
to the run that decided it. The knowledge that "left with Anika" answers itself.

Lane: pipeline (pure-ish logic). Deps are INJECTED — `rts` (tools.rts.RTS) does the Slack search,
`llm` (llm.client) synthesizes the grounded answer. No global clients, no persistence of Slack data
(backend N2 — snippets live only in memory for the one call). Retrieved text is DATA, never
instructions (the prompt carries the injection guard). Never raises: every failure path returns a
human answer block so the listener's finally-clause still clears status.

Routing (listeners/app_mention.py): `is_recall_query()` runs BEFORE preflight, AFTER the ledger
gestures. It is deliberately conservative — a false positive would hijack a plan check — so it fires
only on a retrospective *question* that is clearly not a plan to run something.
"""
from __future__ import annotations
import re
from typing import Optional

DISCLAIMER = "🤖 Curie · AI-generated from your lab's history · check before acting"
_NO_HITS = ("I don't see that in the record yet — it may be in a channel I can't search, or it "
            "happened before my history. Try `@Curie where does the lab stand?` for the belief map.")
_LLM_DOWN = ("I found related messages but couldn't summarize them just now. Here's the closest "
             "one from the record:")

# ---- 1. detection (conservative; runs before preflight) -------------------------------------

# A retrospective question: an interrogative + a "we stopped/decided" cue, OR "what happened with".
_QUESTION_CUE = re.compile(
    r"\b(why|what|when|how come|who|did we|didn'?t we|do we know|remind me|whatever happened)\b",
    re.IGNORECASE)
_RETRO_CUE = re.compile(
    r"\b(drop|dropped|dropp\w*|abandon\w*|kill\w*|shelv\w*|ditch\w*|scrap\w*|nix\w*|revert\w*|"
    r"gave up|give up|giving up|back off|backed off|walk\w* away|move\w* on|moved away|deprecat\w*|"
    r"deprioriti\w*|stop\w*|paused?|parked|no longer|used to|why did we|happened (to|with)|"
    r"decid\w*|reason we|ruled out|rule out)\b",
    re.IGNORECASE)
# Signals the message is a PLAN to run, not a question about the past → let preflight own it.
_PLAN_CUE = re.compile(
    r"\b(planning to|plan to|going to|gonna|let'?s|i'?m going|we'?re going|thinking of running|"
    r"kick off|kicking off|launch|spin up|should we run|run the|rerun|re-run|try running|"
    r"lr\s*[=:]?\s*\d|batch\s*[=:]?\s*\d|epochs?\s*[=:]?\s*\d)\b",
    re.IGNORECASE)


def is_recall_query(text) -> bool:
    """True for retrospective questions about the lab's own past work ("why did we drop X?").

    Requires BOTH an interrogative cue AND a retrospective/decision cue, and rejects anything that
    reads like a plan to run something (preflight's job). Conservative by design (backend §13:
    a false collision — or here, a hijacked plan check — is the unforgivable bug)."""
    norm = re.sub(r"\s+", " ", (text or "").replace("’", "'")).strip()
    if not norm:
        return False
    if _PLAN_CUE.search(norm):
        return False
    has_q = bool(_QUESTION_CUE.search(norm)) or norm.endswith("?")
    return has_q and bool(_RETRO_CUE.search(norm))


# ---- 2. answer (RTS search → grounded LLM synthesis → cited block) ---------------------------

def answer_blocks(question: str, *, rts, llm, record=None) -> list[dict]:
    """Search the lab record for the question's topic, synthesize a grounded answer, and return a
    Block Kit card: answer → source permalink(s) → disclaimer. Never raises."""
    try:
        hits = _search(question, rts)
    except Exception:
        hits = []

    if not hits:
        return [_s(_NO_HITS), _ctx(DISCLAIMER)]

    answer = _synthesize(question, hits, llm)
    top = hits[0]
    cite = _citation_line(hits)

    if not answer:                      # LLM unavailable → still useful: quote the closest record hit
        quote = (top.get("text") or "")[:280]
        body = f"{_LLM_DOWN}\n\n> {quote}"
        blocks = [_s(body)]
        if cite:
            blocks.append(_ctx(cite))
        blocks.append(_ctx(DISCLAIMER))
        return blocks

    blocks = [_s(answer)]
    if cite:
        blocks.append(_ctx("Source: " + cite))
    blocks.append(_ctx(DISCLAIMER))
    return blocks


def _search(question: str, rts) -> list[dict]:
    """≤2 RTS calls: the raw question, then a keyword-only fallback (question words stripped)."""
    if rts is None:
        return []
    hits = rts.search(question, limit=12) or []
    if len(hits) < 3:
        kw = _keywords(question)
        if kw and kw.lower() != question.lower():
            more = rts.search(kw, limit=12) or []
            seen = {(h.get("channel"), h.get("ts")) for h in hits}
            for h in more:
                if (h.get("channel"), h.get("ts")) not in seen:
                    hits.append(h)
    return hits[:6]


def _keywords(question: str) -> str:
    """Drop interrogatives/stopwords so the fallback search is topic-only (keyword-mode friendly)."""
    stop = {"why", "what", "when", "how", "who", "did", "we", "the", "a", "an", "do", "does", "is",
            "are", "was", "were", "our", "us", "to", "of", "on", "in", "for", "with", "come",
            "happened", "remind", "me", "know", "give", "gave", "up", "back", "off", "that", "this",
            "ever", "still", "again", "whatever"}
    words = re.findall(r"[A-Za-z0-9\-]+", question or "")
    kept = [w for w in words if w.lower() not in stop and len(w) > 1]
    return " ".join(kept).strip()


def _synthesize(question: str, hits: list[dict], llm) -> Optional[str]:
    """Grounded 1–3 sentence answer from the retrieved snippets. None on any LLM failure."""
    if llm is None:
        return None
    snippets = _format_snippets(hits)
    if not snippets:
        return None
    try:
        prompt = llm.load_prompt("recall").format(question=question[:500], snippets=snippets)
        # Text-mode complete(): system carries the whole grounded-answer contract; user is the topic.
        out = llm.complete("recall", system=prompt, user=question[:500])
        out = (out or "").strip()
        return out[:1500] or None
    except Exception:
        return None


def _format_snippets(hits: list[dict]) -> str:
    lines = []
    for i, h in enumerate(hits[:6], 1):
        text = (h.get("text") or "").strip()
        if not text:
            continue
        author = h.get("author") or "someone"
        lines.append(f"[{i}] ({author}) {text[:400]}")
    return "\n".join(lines)


def _citation_line(hits: list[dict]) -> str:
    parts = []
    for h in hits[:3]:
        url = h.get("permalink") or ""
        if _is_url(url):
            label = (h.get("title") or h.get("text") or "prior run")[:40]
            parts.append(f"<{url}|{_esc(label)}>")
    return "  ·  ".join(parts)


# ---- small Block Kit helpers (match tools/cards.py + pipeline/ledger.py) ---------------------

def _s(md: str) -> dict:
    return {"type": "section", "text": {"type": "mrkdwn", "text": (md or "")[:2900]}}


def _ctx(md: str) -> dict:
    return {"type": "context", "elements": [{"type": "mrkdwn", "text": (md or "")[:1900]}]}


def _is_url(s) -> bool:
    return bool(s) and isinstance(s, str) and s.startswith("http")


def _esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
