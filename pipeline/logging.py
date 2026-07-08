"""logging.py — the shared result-write path (CLAUDE.md pipeline lane: "logging").

Two triggers land an experiment outcome on the "Lab Record" List: the 🧪 reacji
(listeners/reaction_added) and ambient run-record ingest (listeners/ambient). Both go through
record_result() here so the match -> write / create logic lives in ONE place. The proven,
live-verified write atoms (row match, cell write, row create) stay in listeners/reaction_added;
this module gives callers a single named entry point and the status -> Evidence-polarity mapping
(so an ingested result can move a hypothesis rollup) WITHOUT duplicating that code.

The Slack client is injected (never a global). Nothing raises to the caller — every failure
resolves to RecordResult(ok=False) so the listener can post a human message + retry. No Slack
content is ever logged.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from listeners import reaction_added as _ra   # reuse the verified match / write / create atoms

# status (and status-like) value -> Evidence polarity toward the parent hypothesis.
# Mirrors seed/seed_list.py's _POLARITY so ingested results roll up the same way as the seed.
_POLARITY_FOR_STATUS = {
    "succeeded": "supports", "supported": "supports",
    "failed": "contrasts", "refuted": "contrasts",
    "running": None, "abandoned": None, "open": None,
}
_CREATE_STATUS = {"failed", "succeeded", "running", "abandoned"}   # valid experiment statuses


def polarity_for(status: str) -> Optional[str]:
    """'supports' / 'contrasts' for decisive results, else None (neutral / unknown)."""
    return _POLARITY_FOR_STATUS.get((status or "").strip().lower())


@dataclass
class RecordResult:
    ok: bool
    row_id: str = ""
    created: bool = False
    prior: Optional[dict] = None    # prior cell values (for undo); None when the row was created
    matched: bool = False


# ---- thin re-exports so callers use one module for the write API (atoms owned by reaction_added)

def match_row(client, title: str):
    """Fuzzy-match an experiment row by title -> (row_id, prior-values | None)."""
    return _ra._match_row(client, title)


def write_cells(client, row_id: str, values: dict) -> bool:
    """slackLists.items.update with the verified `cells` shape (supports status/outcome/trust/
    updated/polarity)."""
    return _ra._write_cells(client, row_id, values)


def similarity(a: str, b: str) -> float:
    """Reuse reaction_added's token-overlap similarity (for callers that do their own matching)."""
    return _ra._similarity(a, b)


def record_result(client, *, title: str, status: str, outcome: str = "",
                  polarity: Optional[str] = None, trust: str = "auto",
                  create_if_missing: bool = True, row_id: Optional[str] = None) -> RecordResult:
    """Write {status, outcome, polarity?, trust, updated} to an experiment row. If `row_id` is
    given, write to it directly (caller already resolved it, e.g. param-aware); otherwise match by
    `title`, else create a new experiment row. Returns what happened; never raises."""
    prior = None
    if row_id is None:
        try:
            row_id, prior = _ra._match_row(client, title)
        except Exception:
            row_id, prior = "", None

    if row_id:
        values = {"status": status, "outcome": outcome, "trust": trust, "updated": _ra._today()}
        if polarity:
            values["polarity"] = polarity
        try:
            ok = bool(_ra._write_cells(client, row_id, values))
        except Exception:
            ok = False
        return RecordResult(ok=ok, row_id=row_id, created=False, prior=prior, matched=True)

    if not create_if_missing:
        return RecordResult(ok=False)

    ex = _ra.LogExtract(experiment_title=title,
                        status=(status if status in _CREATE_STATUS else "running"),
                        outcome=outcome)
    try:
        new_id = _ra._create_row(client, ex)
    except Exception:
        new_id = ""
    return RecordResult(ok=bool(new_id), row_id=new_id, created=True, prior=None, matched=False)
