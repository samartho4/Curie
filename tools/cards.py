"""Block Kit rendering for Curie's verdict card (frontend.md §4B + copy deck §9).

Canonical skeleton (every card): header → section(s) → context(citations) → actions(≤3) → context(disclaimer).
Pure functions: Verdict -> list[block dict]. No I/O. Copy strings are verbatim from frontend.md §9.
"""
from __future__ import annotations
import re

from tools import charts

DISCLAIMER = "🤖 Curie · AI-generated · check before acting"

# Param keys under which a prior run could carry a chartable numeric SERIES (sweep / per-step
# metric). Deliberately narrow: no current seed/record row uses any of these, so the collision
# chart never fabricates — it appears only if a real series is ever logged (see _metric_series).
_SERIES_KEYS = ("series", "sweep", "curve", "trajectory", "metrics", "history")
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


def _num(v):
    try:
        f = float(v)
        return None if (f != f) else f          # drop NaN
    except (TypeError, ValueError):
        return None


def _parse_series_cell(raw) -> list[tuple[str, float]]:
    """Parse a param cell into >=1 (label, value) points, or [] if it isn't a numeric series.
    Accepts 'x1=y1, x2=y2' / 'x1: y1; x2: y2' (labelled) or a bare 'y1, y2, y3' list (indexed).
    Any non-numeric value voids the whole cell (a real series is all numbers)."""
    if not isinstance(raw, str) or not raw.strip():
        return []
    parts = [p for p in re.split(r"[,;]", raw) if p.strip()]
    if not parts:
        return []
    if all(("=" in p or ":" in p) for p in parts):
        pairs: list[tuple[str, float]] = []
        for p in parts:
            sep = "=" if "=" in p else ":"
            lab, val = p.split(sep, 1)
            n = _num(val)
            if n is None:
                return []
            pairs.append((lab.strip()[:20], n))
        return pairs
    out: list[tuple[str, float]] = []
    for i, p in enumerate(parts, 1):
        n = _num(p)
        if n is None:
            return []
        out.append((str(i), n))
    return out


def _metric_series(v):
    """Return (title, categories, values) for a TRUTHFUL numeric series carried by the primary
    collision candidate, else None. Conservative by design — fires ONLY on an explicit signal:
    a `metric_series` attribute on the candidate, or a param whose KEY is series-like and whose
    VALUE parses to >=2 numeric points. No current seed/record row carries either, so this never
    fabricates: the collision card stays text-only until a real sweep / per-step metric is logged."""
    prim = next(iter(v.collisions or []), None)
    if prim is None:
        return None
    ms = getattr(prim, "metric_series", None)   # structured escape hatch (absent in today's record)
    if isinstance(ms, dict):
        cats = [str(x)[:20] for x in (ms.get("categories") or [])]
        vals = [n for n in (_num(x) for x in (ms.get("values") or [])) if n is not None]
        if len(vals) >= 2 and len(cats) == len(vals):
            return (str(ms.get("title") or (prim.title or "prior run"))[:50], cats, vals)
    for k, raw in (prim.params or {}).items():
        if str(k).strip().lower() not in _SERIES_KEYS:
            continue
        pts = _parse_series_cell(raw)
        if len(pts) >= 2:
            return (f"{(prim.title or 'prior run')[:32]} · {k}"[:50],
                    [p[0] for p in pts], [p[1] for p in pts])
    return None


def _collision_metric_chart(v):
    """A small line chart of the matched prior run's metric series, or None when none exists.
    Additive: the caller appends it only when truthy, so the text card is never altered otherwise."""
    ser = _metric_series(v)
    if not ser:
        return None
    title, cats, vals = ser
    return charts.data_viz_block(title, "line", [{"name": "prior run", "data": vals}], cats)


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
    chart = _collision_metric_chart(v)     # truthful prior-run series only; None → card unchanged
    if chart:
        blocks.append(chart)
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
