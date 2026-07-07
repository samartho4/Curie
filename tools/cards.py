"""Block Kit rendering for Curie's verdict card (frontend.md §4B + copy deck §9).

Canonical skeleton (every card): header → section(s) → context(citations) → actions(≤3) → context(disclaimer).
Pure functions: Verdict -> list[block dict]. No I/O. Copy strings are verbatim from frontend.md §9.
"""
from __future__ import annotations

DISCLAIMER = "🤖 Curie · AI-generated · check before acting"
_HEADER = {"collision": "⚠️ This was already tried",
           "near_miss": "🟡 Close to earlier work",
           "clear": "✅ No prior work found on this"}


def _h(text): return {"type": "header", "text": {"type": "plain_text", "text": text[:150], "emoji": True}}
def _s(md): return {"type": "section", "text": {"type": "mrkdwn", "text": md[:2900]}}
def _ctx(md): return {"type": "context", "elements": [{"type": "mrkdwn", "text": md[:1900]}]}
def _div(): return {"type": "divider"}


def _is_url(s: str) -> bool:
    return bool(s) and s.startswith("http")


def _first_url(v) -> str:
    """First collision with a real https permalink (List rows carry bare record ids, not URLs)."""
    for c in (v.collisions or []):
        if _is_url(c.permalink):
            return c.permalink
    return ""


def _citations(v) -> str:
    parts = []
    for c in (v.collisions or [])[:3]:
        if _is_url(c.permalink):
            parts.append(f"<{c.permalink}|{(c.title or 'prior run')[:40]}>")
    for l in (v.literature or [])[:2]:
        if _is_url(l.permalink):
            parts.append(f"<{l.permalink}|{(l.title or 'paper')[:40]}>")
    return "  ·  ".join(parts)


def _diff_md(v) -> str:
    if not v.diff:
        return ""
    lines = []
    for d in v.diff[:5]:
        mark = "· same" if d.same else "· *differs*"
        lines.append(f"• {d.param}: `{d.plan_value}` vs `{d.prior_value}`  {mark}")
    if len(v.diff) > 5:
        lines.append(f"…and {len(v.diff) - 5} more")
    return "*What differs from last time*\n" + "\n".join(lines)


def verdict_blocks(v, plan_text: str = "") -> list[dict]:
    """Render a Verdict (pipeline.preflight.Verdict) as Block Kit blocks."""
    if v.level == "clear":
        # deliberately minimal — the common case must never read as noise (frontend §4B)
        blocks = [_s(f"✅ *No prior work found on this. Good to go.*")]
        srch = "Searched the lab record + literature"
        if v.note:
            srch += f" · {v.note}"
        blocks.append(_ctx(srch))
        return blocks

    blocks = [_h(_HEADER[v.level])]
    if v.summary:
        blocks.append(_s(v.summary))
    diff = _diff_md(v)
    if diff:
        blocks.append(_s(diff))
    cites = _citations(v)
    if cites:
        blocks.append(_ctx("Evidence: " + cites))

    _url = _first_url(v)
    actions = [{"type": "button", "text": {"type": "plain_text", "text": "View thread"},
                "url": _url, "action_id": "view_thread"}] if _url else []
    actions.append({"type": "button", "text": {"type": "plain_text", "text": "Full comparison"}, "action_id": "full_comparison"})
    if v.level == "collision":
        actions.append({"type": "button", "text": {"type": "plain_text", "text": "Proceed anyway"},
                        "style": "danger", "action_id": "proceed_anyway"})
    blocks.append({"type": "actions", "elements": actions[:3]})
    blocks.append(_ctx(DISCLAIMER))
    return blocks
