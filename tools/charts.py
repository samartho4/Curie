"""charts.py — native Slack `data_visualization` block builder (Block Kit).

VERIFIED LIVE (Block Kit Builder, this workspace, Jul 12 2026): the `data_visualization` block
RENDERS inside a posted channel message (chart types line / bar / area / pie). Confirmed shape:

    {"type": "data_visualization",
     "title": <str, REQUIRED, <=50 chars>,
     "chart": {"type": "line" | "bar" | "area",
               "series": [{"name": <str <=20>,
                           "data": [{"label": <str <=20, == its category>,
                                     "value": <number>}]}],          # one point per category
               "axis_config": {"categories": [<str <=20>, ...],      # REQUIRED for line/bar/area
                               "x_label": <str <=50, optional>,
                               "y_label": <str <=50, optional>}}}
    # "pie" instead carries {"segments": [{"label", "value"}]} (1..6), no axis_config.

By contrast the `alert` and `data_table` blocks are modal-only — they silently DROP in a posted
message — so this module never emits them (posted cards render tabular text via `section` fields).

Pure + dependency-free: functions take/return JSON-serializable dicts, do no I/O, and NEVER raise.
`data_viz_block(...)` returns None when a valid chart cannot be built from the inputs, so callers
append it only when truthy — the chart is always an ADDED block that degrades gracefully, never a
replacement for the text card (frontend §4B skeleton stays intact).
"""
from __future__ import annotations
from typing import Any, Mapping, Optional, Sequence, Union

# Verified runtime limits (docs.slack.dev/reference/block-kit/blocks/data-visualization-block).
MAX_SERIES = 6            # 1..6 series
MAX_POINTS = 20           # 1..20 categories / points per series
MAX_LABEL = 20            # series name · category · point label
MAX_TITLE = 50            # chart title
MAX_AXIS_LABEL = 50       # x_label / y_label
_CHART_TYPES = ("line", "bar", "area", "pie")

# Accepted series inputs: {"name": [values]} mapping, or a list of {"name":…, "data"|"values":[…]}.
SeriesInput = Union[Mapping[str, Sequence[float]], Sequence[Mapping[str, Any]]]


# ---- small pure helpers -----------------------------------------------------------------------

def _trunc(s: Any, limit: int) -> str:
    s = str(s)
    return s if len(s) <= limit else (s[: max(0, limit - 1)] + "…")


def _num(v) -> Optional[float]:
    """Coerce to a finite float, or None (non-numeric / NaN / inf are not chartable)."""
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f or f in (float("inf"), float("-inf")):
        return None
    return f


def _dedupe(labels: Sequence[str]) -> list[str]:
    """Slack requires unique categories & series names; keep them unique AND <=MAX_LABEL."""
    seen: dict[str, int] = {}
    out: list[str] = []
    for lab in labels:
        base = _trunc(lab, MAX_LABEL)
        if base not in seen:
            seen[base] = 1
            out.append(base)
            continue
        seen[base] += 1
        suffix = f" ({seen[base]})"
        out.append(_trunc(base, MAX_LABEL - len(suffix)) + suffix)
    return out


def _normalize_series(series: SeriesInput) -> list[tuple[str, list]]:
    """Accept {name: values} OR [{"name":…, "data"|"values":…}] OR [(name, values)]."""
    if isinstance(series, Mapping):
        items: Sequence[Any] = list(series.items())
    else:
        items = list(series or [])
    out: list[tuple[str, list]] = []
    for item in items:
        if isinstance(item, Mapping):
            name = item.get("name", "")
            values = item.get("data", item.get("values"))
        elif isinstance(item, (tuple, list)) and len(item) == 2:
            name, values = item
        else:
            continue
        out.append((str(name), list(values or [])))
    return out


# ---- the builder ------------------------------------------------------------------------------

def data_viz_block(
    title: str,
    chart_type: str,
    series: SeriesInput,
    categories: Sequence[str],
    x_label: str = "",
    y_label: str = "",
) -> Optional[dict]:
    """Build one valid `data_visualization` block, or None when no valid chart can be made.

    Enforces the verified limits by TRUNCATION / trimming (never raises):
      · title <= 50 chars
      · <= 6 series (extras dropped); series names <= 20 chars, deduped
      · <= 20 categories (extras dropped); labels <= 20 chars, deduped
      · exactly one point per category per series (missing points padded 0.0, extras dropped)
      · non-numeric / NaN / inf values coerced to 0.0
      · point.label is set equal to its category (Slack requires the match)
    Returns None if, after cleaning, there are no categories or no series.
    """
    ct = (chart_type or "").strip().lower()
    if ct not in _CHART_TYPES:
        ct = "bar"

    cats = _dedupe([str(c) for c in (categories or [])][:MAX_POINTS])
    norm = _normalize_series(series)[:MAX_SERIES]
    if not cats or not norm:
        return None

    if ct == "pie":
        # pie carries segments (1..6), no axis_config; take the first series, one seg per category.
        _, values = norm[0]
        segs = [{"label": cat, "value": (_num(values[i]) if i < len(values) else 0.0) or 0.0}
                for i, cat in enumerate(cats)][:6]
        if not segs:
            return None
        return {"type": "data_visualization", "title": _trunc(title, MAX_TITLE),
                "chart": {"type": "pie", "segments": segs}}

    names = _dedupe([n for n, _ in norm])
    series_json = []
    for (_, values), name in zip(norm, names):
        pts = []
        for i, cat in enumerate(cats):
            v = _num(values[i]) if i < len(values) else 0.0   # exactly one point per category
            pts.append({"label": cat, "value": v if v is not None else 0.0})
        series_json.append({"name": name, "data": pts})

    axis: dict = {"categories": cats}                         # REQUIRED for line/bar/area
    if x_label:
        axis["x_label"] = _trunc(x_label, MAX_AXIS_LABEL)
    if y_label:
        axis["y_label"] = _trunc(y_label, MAX_AXIS_LABEL)

    return {"type": "data_visualization", "title": _trunc(title, MAX_TITLE),
            "chart": {"type": ct, "series": series_json, "axis_config": axis}}
