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
    """Answer from the lab's own record. The structured List is the PRIMARY source (it carries the
    OUTCOME field — e.g. "gradient collapse / NaN at epoch 3" — which is the actual reason a run was
    dropped and is NOT a searchable channel message); RTS enriches with the surrounding discussion.
    Returns a Block Kit card: answer → source permalink(s) → disclaimer. Never raises."""
    try:
        record_hits = _record_candidates(question, record)   # authoritative, outcome-bearing
    except Exception:
        record_hits = []
    try:
        rts_hits = _search(question, rts)                     # channel context (noise-filtered)
    except Exception:
        rts_hits = []
    hits = _merge(record_hits, rts_hits)

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
    """≤2 RTS calls: the raw question, then a keyword-only fallback (question words stripped).
    Drops noise hits — other people's questions and bare @mentions never explain a past decision,
    and feeding the asker's own question back as 'evidence' is what made recall answer 'I don't
    see it' even when the record held the answer."""
    if rts is None:
        return []
    hits = rts.search(question, limit=12) or []
    if len([h for h in hits if not _is_noise(h.get("text"))]) < 3:
        kw = _keywords(question)
        if kw and kw.lower() != question.lower():
            more = rts.search(kw, limit=12) or []
            seen = {(h.get("channel"), h.get("ts")) for h in hits}
            for h in more:
                if (h.get("channel"), h.get("ts")) not in seen:
                    hits.append(h)
    hits = [h for h in hits if not _is_noise(h.get("text"))]
    return hits[:6]


def _is_noise(text) -> bool:
    """A hit that can't be an answer: an empty string, a question (ends with '?' or 'why did we…'),
    or a bare @mention with no content."""
    t = (text or "").strip().lower()
    if not t:
        return True
    if t.endswith("?"):
        return True
    if t.startswith("@") and len(t) < 40:
        return True
    if "why did we" in t or "what happened" in t or "whatever happened" in t:
        return True
    return False


def _record_candidates(question: str, record) -> list[dict]:
    """PRIMARY evidence: List rows whose method/params/outcome overlap the question's terms. Reuses
    record_store.find_candidates (the same matcher the collision check trusts), so the OUTCOME field
    — the real reason a run was dropped — becomes a snippet the LLM can ground on. Never raises."""
    if record is None:
        return []
    try:
        if hasattr(record, "available") and not record.available():
            return []
        cands = record.find_candidates(_QueryShim(question)) or []
    except Exception:
        return []
    out = []
    for c in cands:
        text = (c.get("text") or "").strip()
        if not text:
            continue
        out.append({
            "source": "list",
            "title": c.get("title") or "prior run",
            "text": text,
            "permalink": c.get("permalink") or "",
            "outcome": c.get("outcome"),
            "author": "the lab record",
            "channel": None,
            "ts": None,
        })
    return out


class _QueryShim:
    """Adapts a plain question into the (aliases/method/params) shape find_candidates expects."""
    def __init__(self, question: str):
        kw = _keywords(question)
        self.method = kw
        self.aliases = [t for t in kw.split() if len(t) > 1]
        self.params = {}


def _merge(record_hits: list[dict], rts_hits: list[dict]) -> list[dict]:
    """Record candidates first (authoritative, outcome-bearing), then RTS enrichment, deduped by
    permalink. Capped so the LLM prompt stays tight."""
    out, seen = [], set()
    for h in list(record_hits) + list(rts_hits):
        key = h.get("permalink") or (h.get("channel"), h.get("ts")) or h.get("title")
        if key in seen:
            continue
        seen.add(key)
        out.append(h)
    return out[:6]


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
