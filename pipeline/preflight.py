"""preflight.py — the verdict engine (backend.md §6.1, calibration §13). Pure logic.

parse plan (LLM) -> compose check-plan (LLM) -> execute deterministically (record -> RTS -> scholar)
-> per-candidate RCS (LLM) -> verdict (LLM) -> DETERMINISTIC calibration guard -> plain-text render.

Providers are INJECTED (record, rts, scholar) so the same engine runs against live Slack (listener)
or an offline seed fixture (eval). Any LLM/JSON failure degrades to a deterministic fallback — never
a guessed verdict (§13). "clear" is the confident default; a false collision is the unforgivable bug.

Provider contract (duck-typed):
  record.find_candidates(plan) -> list[dict]     # List-primary; [] if no List
  rts.search(query) -> list[dict]                # <=3 calls enforced inside rts; [] if unavailable
  scholar.search(query) -> list[dict]            # literature; [] on failure
Each dict: {source, title, text, permalink, outcome, params, ...}
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Optional
from pydantic import BaseModel

from llm import client as llm

# Frontend §9 verbatim strings.
HDR_COLLISION = "⚠️ This was already tried"
HDR_NEAR_MISS = "🟡 Close to earlier work"
BODY_CLEAR = "✅ No prior work found on this. Good to go."
DISCLAIMER = "🤖 Curie · AI-generated · check before acting"
PARSE_FAIL_MSG = ("I couldn't read that as an experiment plan — try describing the method, data, "
                  "and key settings.")
ERROR_MSG = "I couldn't finish the check — something went wrong. Try again."

_CONF_FLOOR = 0.65  # below this, collisions/near-misses demote to clear (§13)


# ---- types --------------------------------------------------------------------------------

class Plan(BaseModel):
    method: str = ""
    params: dict[str, str] = {}
    dataset: Optional[str] = None
    aliases: list[str] = []
    hypothesis_ref: Optional[str] = None


class CheckPlan(BaseModel):
    queries: list[str] = []
    consult_literature: bool = True
    literature_query: str = ""


class Candidate(BaseModel):
    source: Literal["list", "rts", "scholar"]
    title: str = ""
    text: str = ""
    permalink: str = ""
    outcome: Optional[str] = None
    params: dict[str, str] = {}
    rcs_summary: Optional[str] = None


class DiffLine(BaseModel):
    param: str
    plan_value: str
    prior_value: str
    same: bool


class _VerdictJSON(BaseModel):
    """Raw LLM output, pre-calibration."""
    level: Literal["collision", "near_miss", "clear"]
    confidence: float = 0.5
    summary: str = ""
    collision_indices: list[int] = []
    note: str = ""


class Verdict(BaseModel):
    level: Literal["collision", "near_miss", "clear"]
    confidence: float
    summary: str = ""
    collisions: list[Candidate] = []
    literature: list[Candidate] = []
    diff: list[DiffLine] = []
    note: str = ""


@dataclass
class PreflightResult:
    kind: Literal["verdict", "parse_fail", "error"]
    verdict: Optional[Verdict] = None
    message: Optional[str] = None          # user-facing string for parse_fail / error
    rts_degraded: bool = False
    lit_degraded: bool = False
    meta: dict = field(default_factory=dict)


# ---- prompt rendering (safe against literal braces in prompt bodies) ----------------------

def _render(template: str, **kw) -> str:
    out = template
    for k, v in kw.items():
        out = out.replace("{" + k + "}", str(v))
    return out


# ---- LLM steps (each returns None / [] on failure; never raises) --------------------------

def _parse_plan(plan_text: str) -> Optional[Plan]:
    try:
        sys = "You are Curie's plan parser. Return only JSON."
        user = _render(llm.load_prompt("parse_plan"), plan=plan_text)
        return llm.complete("parse", system=sys, user=user, model_cls=Plan)
    except Exception:
        return None


def _check_plan(plan: Plan) -> Optional[CheckPlan]:
    try:
        sys = "You are Curie's retrieval planner. Return only JSON."
        user = _render(llm.load_prompt("check_plan"), plan_json=plan.model_dump_json())
        return llm.complete("check_plan", system=sys, user=user, model_cls=CheckPlan)
    except Exception:
        return None


def _rcs(plan: Plan, cand: Candidate) -> Optional[str]:
    try:
        sys = "You summarize whether prior work collides with a plan. Plain prose, no JSON."
        cand_blob = f"source={cand.source}; title={cand.title}; params={cand.params}; outcome={cand.outcome}; text={cand.text}"
        user = _render(llm.load_prompt("rcs"), plan=_plan_blob(plan), candidate=cand_blob)
        txt = llm.complete("rcs", system=sys, user=user)
        return (txt or "").strip() or None
    except Exception:
        return None


def _verdict(plan: Plan, evidence: list[Candidate]) -> Optional[_VerdictJSON]:
    try:
        sys = "You are Curie. Judge collisions conservatively. Return only JSON."
        user = _render(llm.load_prompt("verdict"), plan=_plan_blob(plan), evidence=_evidence_blob(evidence))
        return llm.complete("verdict", system=sys, user=user, model_cls=_VerdictJSON)
    except Exception:
        return None


def _plan_blob(plan: Plan) -> str:
    return (f"method={plan.method}; params={plan.params}; dataset={plan.dataset}; "
            f"hypothesis_ref={plan.hypothesis_ref}")


def _evidence_blob(evidence: list[Candidate]) -> str:
    lines = []
    for i, c in enumerate(evidence):
        lines.append(f"[{i}] source={c.source} | title={c.title} | params={c.params} | "
                     f"outcome={c.outcome}")
        if c.rcs_summary:
            lines.append(f"    RCS: {c.rcs_summary}")
    return "\n".join(lines) if lines else "(no candidates)"


# ---- the pipeline -------------------------------------------------------------------------

def run_preflight(plan_text: str, *, record, rts, scholar, status=None) -> PreflightResult:
    _set_status(status, "checking the record…")

    plan = _parse_plan(plan_text)
    if plan is None or not (plan.method.strip() or plan.params):
        return PreflightResult("parse_fail", message=PARSE_FAIL_MSG)

    cp = _check_plan(plan) or CheckPlan(
        queries=[_default_query(plan)],
        consult_literature=bool(plan.method.strip()),
        literature_query=plan.method,
    )

    # --- deterministic execution ---
    _set_status(status, "searching the record…")
    slack_dicts: list[dict] = []
    try:
        slack_dicts += record.find_candidates(plan) or []
    except Exception:
        pass
    rts_degraded = False
    for q in [q for q in cp.queries if q][:3]:
        try:
            slack_dicts += rts.search(q) or []
        except Exception:
            pass
    rts_degraded = bool(getattr(rts, "degraded", False))

    # Drop self-retrieval: search can echo back the very plan we're checking (same @mention now
    # indexed in the channel), which would collide the plan with itself — a false collision (§13).
    slack_dicts = [d for d in slack_dicts if not _looks_self(d, plan_text)]

    lit_dicts: list[dict] = []
    lit_degraded = False
    if cp.consult_literature and cp.literature_query.strip():
        _set_status(status, "checking the literature…")
        try:
            lit_dicts = scholar.search(cp.literature_query) or []
        except Exception:
            lit_degraded = True
        lit_degraded = lit_degraded or bool(getattr(scholar, "degraded", False))

    slack_cands = [_to_candidate(d) for d in _dedupe(slack_dicts)][:6]
    lit_cands = [_to_candidate(d, force="scholar") for d in (lit_dicts or [])][:4]

    # Off-domain / no evidence → clear, WITHOUT a verdict LLM call (§13 short-circuit).
    if not slack_cands and not lit_cands:
        return PreflightResult("verdict", verdict=_clear(), rts_degraded=rts_degraded)

    # RCS per Slack candidate (sequential; <=6 small calls).
    _set_status(status, "weighing the evidence…")
    for c in slack_cands:
        c.rcs_summary = _rcs(plan, c)

    evidence = slack_cands + lit_cands
    vj = _verdict(plan, evidence)
    if vj is None:
        return PreflightResult("error", message=ERROR_MSG,
                               rts_degraded=rts_degraded, lit_degraded=lit_degraded)

    verdict = _calibrate(vj, plan, slack_cands, lit_cands)
    return PreflightResult("verdict", verdict=verdict,
                           rts_degraded=rts_degraded, lit_degraded=lit_degraded)


# ---- deterministic calibration guard (backend.md §13 — the safety net) --------------------

def _calibrate(vj: _VerdictJSON, plan: Plan, slack: list[Candidate],
               lit: list[Candidate]) -> Verdict:
    evidence = slack + lit
    cited = [evidence[i] for i in vj.collision_indices if 0 <= i < len(evidence)]
    cited_slack = [c for c in cited if c.source in ("list", "rts")] or slack

    level = vj.level
    note = vj.note or ""

    # A collision REQUIRES a structured Slack candidate that substantiates it.
    if level == "collision":
        substantiated = [c for c in cited_slack if _substantiates(plan, c)]
        if not substantiated:
            # same-method-but-unsubstantiated → near_miss; nothing related → clear
            level = "near_miss" if any(_method_match(plan, c) for c in slack) else "clear"

    if level == "near_miss" and not any(_method_match(plan, c) for c in slack):
        level = "clear"

    # Literature alone can never be a lab collision.
    if level != "clear" and not slack:
        level = "clear"

    # Low confidence demotes to clear with a soft note (§13).
    if level != "clear" and vj.confidence < _CONF_FLOOR:
        level = "clear"
        note = note or "1 loosely-related thread — view."

    if level == "clear":
        return Verdict(level="clear", confidence=max(vj.confidence, 0.65),
                       summary=vj.summary or BODY_CLEAR, literature=lit, note=note)

    primary = _primary_prior(plan, cited_slack, slack)
    diff = _diff(plan, primary) if primary else []
    collisions = [c for c in (cited_slack or slack) if _method_match(plan, c)][:3] or ([primary] if primary else [])
    return Verdict(level=level, confidence=vj.confidence, summary=vj.summary,
                   collisions=collisions, literature=lit, diff=diff, note=note)


def _substantiates(plan: Plan, c: Candidate) -> bool:
    """Collision-worthy: same method AND (dataset match OR >=2 matching params)."""
    if not _method_match(plan, c):
        return False
    param_matches = _param_match_count(plan, c)
    dataset_match = bool(plan.dataset and c.text and plan.dataset.lower() in c.text.lower())
    return dataset_match or param_matches >= 2


def _method_match(plan: Plan, c: Candidate) -> bool:
    tokens = _distinctive(plan.method) | _distinctive(" ".join(plan.aliases))
    if not tokens:
        return False
    hay = f"{c.title} {c.text}".lower()
    return any(t in hay for t in tokens)


def _param_match_count(plan: Plan, c: Candidate) -> int:
    n = 0
    for k, v in (plan.params or {}).items():
        pv = (c.params or {}).get(k)
        if pv is not None and _norm(pv) == _norm(v):
            n += 1
    return n


def _primary_prior(plan: Plan, cited: list[Candidate], all_slack: list[Candidate]) -> Optional[Candidate]:
    pool = [c for c in (cited or all_slack) if c.source == "list"] or (cited or all_slack)
    for c in pool:
        if _method_match(plan, c):
            return c
    return pool[0] if pool else None


def _diff(plan: Plan, prior: Candidate) -> list[DiffLine]:
    keys = list(dict.fromkeys(list(plan.params.keys()) + list((prior.params or {}).keys())))
    out = []
    for k in keys[:5]:
        pv, prv = plan.params.get(k, "—"), (prior.params or {}).get(k, "—")
        out.append(DiffLine(param=k, plan_value=str(pv), prior_value=str(prv),
                            same=(pv != "—" and prv != "—" and _norm(pv) == _norm(prv))))
    return out


def _clear(note: str = "") -> Verdict:
    return Verdict(level="clear", confidence=0.9, summary=BODY_CLEAR, note=note)


# ---- small utils --------------------------------------------------------------------------

_STOP = {"the", "a", "an", "of", "on", "to", "for", "and", "with", "full", "model", "models",
         "run", "test", "try", "using", "use", "new", "our"}


def _distinctive(text: str) -> set[str]:
    return {w for w in _norm(text).split() if len(w) > 2 and w not in _STOP}


def _looks_self(d: dict, plan_text: str) -> bool:
    """True when a candidate is really the plan being checked, echoed by search (self-retrieval).
    Conservative: near-verbatim only, so genuine prior runs (which read differently — outcomes,
    run-ids) are kept. Bias is toward 'clear', never toward a false collision (§13)."""
    a = _distinctive(str(d.get("text") or d.get("content") or ""))
    b = _distinctive(plan_text or "")
    if len(a) < 4 or len(b) < 4:
        return False
    inter = len(a & b)
    return inter / len(a) >= 0.85 and inter / len(b) >= 0.75


def _norm(v) -> str:
    return str(v).strip().lower()


def _default_query(plan: Plan) -> str:
    terms = [plan.method] + list(plan.aliases[:4])
    return " OR ".join(t for t in terms if t) or plan.method


def _to_candidate(d: dict, force: Optional[str] = None) -> Candidate:
    src = force or d.get("source") or "rts"
    if src not in ("list", "rts", "scholar"):
        src = "rts"
    params = d.get("params") or {}
    if isinstance(params, dict):
        params = {str(k): str(v) for k, v in params.items()}
    else:
        params = {}
    return Candidate(
        source=src,
        title=str(d.get("title") or "")[:120],
        text=str(d.get("text") or d.get("abstract_snippet") or ""),
        permalink=str(d.get("permalink") or d.get("url") or d.get("doi") or ""),
        outcome=(str(d["outcome"]) if d.get("outcome") else None),
        params=params,
    )


def _dedupe(dicts: list[dict]) -> list[dict]:
    seen, out = set(), []
    for d in dicts:
        key = (d.get("permalink") or d.get("url") or d.get("title") or "").strip().lower()
        if key and key in seen:
            continue
        seen.add(key)
        out.append(d)
    return out


def _set_status(status, text: str):
    if status:
        try:
            status(text)
        except Exception:
            pass


# ---- plain-text render (frontend §9 copy; Block Kit deferred) ------------------------------

def format_verdict_text(result: PreflightResult) -> str:
    if result.kind == "parse_fail":
        return f"{result.message}\n\n{DISCLAIMER}"
    if result.kind == "error":
        return f"{result.message}\n\n{DISCLAIMER}"

    v = result.verdict
    lines: list[str] = []
    if v.level == "clear":
        lines.append(BODY_CLEAR)
        if v.note:
            lines.append(v.note)
        lines.append("Searched the lab record" + (" + literature" if v.literature else "") + ".")
        return "\n".join(lines) + f"\n\n{DISCLAIMER}"

    lines.append(HDR_COLLISION if v.level == "collision" else HDR_NEAR_MISS)
    if v.summary:
        lines.append(v.summary)
    if v.diff:
        lines.append("")
        lines.append("What differs from last time:")
        for d in v.diff:
            tag = "same" if d.same else "differs"
            lines.append(f"  • {d.param}: {d.plan_value} vs {d.prior_value} — {tag}")
    cites = []
    for c in v.collisions:
        if c.permalink:
            cites.append(f"<{c.permalink}|{c.title or 'prior run'}>")
    for c in v.literature:
        if c.permalink:
            cites.append(f"<{c.permalink}|{c.title or 'paper'}>")
    if cites:
        lines.append("")
        lines.append("Evidence: " + "   ".join(cites))
    if result.lit_degraded:
        lines.append("Literature check unavailable — based on the lab record only.")
    if v.note:
        lines.append(v.note)
    return "\n".join(lines) + f"\n\n{DISCLAIMER}"
