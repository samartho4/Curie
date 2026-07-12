"""Offline regression test for the calibration guard (backend.md §13) — the zero-false-collision
safety net. Runs with NO OpenAI key and NO Slack. `python -m eval.test_calibration`."""
import sys; import os, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline.preflight import _calibrate, Plan, Candidate, _VerdictJSON

# CASE 1: LLM HALLUCINATES a collision on an off-domain plan with an unrelated candidate.
# Guard MUST demote to clear (the unforgivable-bug prevention).
plan_offdomain = Plan(method="train a CNN on MNIST", params={"lr":"1e-3"}, dataset="MNIST", aliases=[])
unrelated = Candidate(source="rts", title="ESM fine-tune", text="fine-tune ESM2 lr 1e-4 batch 32 v1",
                      params={"lr":"1e-4","batch":"32"})
vj_halluc = _VerdictJSON(level="collision", confidence=0.9, summary="COLLISION!", collision_indices=[0])
r1 = _calibrate(vj_halluc, plan_offdomain, [unrelated], [])
print(f"CASE1 hallucinated collision on off-domain → {r1.level!r}  (must be 'clear')")

# CASE 2: REAL landmine — same method + dataset + params. Guard MUST keep it a collision.
plan_land = Plan(method="fine-tune ESM baseline full", params={"lr":"1e-4","batch":"32"}, dataset="v1",
                 aliases=["ESM2","ESM"])
prior = Candidate(source="rts", title="Anika ESM full FT", text="fine-tune ESM baseline full lr 1e-4 batch 32 v1 NaN gradient collapse",
                  outcome="failed", params={"lr":"1e-4","batch":"32","split":"v1"})
vj_real = _VerdictJSON(level="collision", confidence=0.85, summary="Already tried, failed", collision_indices=[0])
r2 = _calibrate(vj_real, plan_land, [prior], [])
print(f"CASE2 real landmine collision       → {r2.level!r}  (must be 'collision')")

# CASE 3: literature-only 'collision' (no slack candidate) MUST become clear.
lit = Candidate(source="scholar", title="Some null result paper", text="null result", permalink="doi:x")
vj_lit = _VerdictJSON(level="collision", confidence=0.9, collision_indices=[0])
r3 = _calibrate(vj_lit, plan_land, [], [lit])
print(f"CASE3 literature-only collision      → {r3.level!r}  (must be 'clear')")

# CASE 4: low-confidence collision demotes to clear.
vj_lowconf = _VerdictJSON(level="collision", confidence=0.4, collision_indices=[0])
r4 = _calibrate(vj_lowconf, plan_land, [prior], [])
print(f"CASE4 low-confidence (0.4) collision → {r4.level!r}  (must be 'clear')")

# CASE 5: THE LIVE SELF-COLLISION BUG. Search echoed the triggering message back as a candidate.
# An RTS/message hit has NO structured params, so the diff's prior side is all "—" (empty diff).
# The empty-diff guard MUST refuse to call this a collision even though the LLM did and the echo's
# free text trivially "matches" the method + dataset. Downgrades to clear (no genuine prior).
plan_gat = Plan(method="train a GAT on the reaction-network dataset", params={"lr": "3e-4", "batch": "64"},
                dataset="reaction-network", aliases=["GAT", "graph attention network"])
echo = Candidate(source="rts", title="train a GAT on the reaction-network dataset, Adam, lr 3e-4, batch 64",
                 text="train a GAT on the reaction-network dataset, Adam, lr 3e-4, batch 64",
                 permalink="https://slack.com/archives/CXX/p1783722835912419", params={})  # RTS => no params
vj_echo = _VerdictJSON(level="collision", confidence=0.9, summary="Already tried!", collision_indices=[0])
r5 = _calibrate(vj_echo, plan_gat, [echo], [])
print(f"CASE5 empty-diff self-echo collision → {r5.level!r}  (must be 'clear'; diff rows={len(r5.diff)})")

# CASE 6: the ESM landmine MUST stay a collision AND carry a non-empty diff with a real matching
# param (protects the one working true-positive).
r6 = _calibrate(vj_real, plan_land, [prior], [])
_r6_matching = [d for d in r6.diff if d.same]
print(f"CASE6 ESM landmine → {r6.level!r} (must be 'collision'); "
      f"diff rows={len(r6.diff)} matching={len(_r6_matching)} (both must be >=1)")

# CASE 7: THE LIVE FALSE-CLEAR FIX. A COMPLETED experiment reported in CHAT (free text; RTS gives it
# params={}) that carries a RESULT signal (done / R2 / converged / epochs) AND matches method +
# dataset + config → a GENUINE collision. Params are text-extracted so the diff is NON-EMPTY. This is
# GAT-201 from the deployed-bug report; before the fix it wrongly returned "clear".
plan_gat2 = Plan(method="train a GAT on the reaction-network dataset", params={"lr": "3e-4", "batch": "64"},
                 dataset="reaction-network", aliases=["GAT", "graph attention network"])
completed = Candidate(source="rts",
    title="exp GAT-201 done: trained a GAT on the reaction-network dataset",
    text="exp GAT-201 done: trained a GAT on the reaction-network dataset, v2 split — R2 0.74, "
         "converged in 40 epochs. Best yield model yet, lr 3e-4 batch 64",
    permalink="https://slack.com/archives/CXX/p1783700000000000", params={})  # RTS => no params
vj_completed = _VerdictJSON(level="collision", confidence=0.9,
                            summary="GAT-201 already ran this config", collision_indices=[0])
r7 = _calibrate(vj_completed, plan_gat2, [completed], [])
_r7_matching = [d for d in r7.diff if d.same]
print(f"CASE7 completed CHAT prior + result  → {r7.level!r} (must be 'collision'); "
      f"diff rows={len(r7.diff)} matching={len(_r7_matching)} (both must be >=1)")

# CASE 8: a PLAN RE-POST (someone restating the plan; future-tense, NO result/outcome signal) must
# stay CLEAR even though it names the same method + dataset + params. No completed run => no collision.
echo_plan = Candidate(source="rts", title="planning GAT run",
    text="planning to train a GAT on the reaction-network dataset next week, Adam optimizer, lr 3e-4, batch 64",
    permalink="https://slack.com/archives/CXX/p1783699999999999", params={})
vj_echo2 = _VerdictJSON(level="collision", confidence=0.9, summary="looks already tried", collision_indices=[0])
r8 = _calibrate(vj_echo2, plan_gat2, [echo_plan], [])
print(f"CASE8 plan re-post (no result)       → {r8.level!r} (must be 'clear'; diff rows={len(r8.diff)})")

# CASE 9: a CLEAR card must be SELF-CONSISTENT — no diff prose, no citations, no leaked collision note.
from tools.cards import verdict_blocks


def _card_text(blocks):
    out = []
    for b in blocks:
        t = b.get("text")
        if isinstance(t, dict) and isinstance(t.get("text"), str):
            out.append(t["text"])
        for e in (b.get("elements") or []):
            et = e.get("text") if isinstance(e, dict) else None
            if isinstance(et, str):
                out.append(et)
    return " ".join(out).lower()


_flat9 = _card_text(verdict_blocks(r8))
_clean_card = all(m not in _flat9 for m in
                  ("differs", "evidence:", "already tried", "match the plan", " vs "))
print(f"CASE9 clear card is self-consistent  → clean={_clean_card} (must be True; text={_flat9!r})")

ok = (r1.level == "clear" and r2.level == "collision" and r3.level == "clear" and r4.level == "clear"
      and r5.level == "clear"
      and r6.level == "collision" and len(r6.diff) >= 1 and len(_r6_matching) >= 1
      and r7.level == "collision" and len(r7.diff) >= 1 and len(_r7_matching) >= 1
      and r8.level == "clear"
      and _clean_card)
print("\n" + ("✅ CALIBRATION GUARD PASSES — false/empty-diff collisions blocked, completed chat "
              "priors caught, real ones kept, clear cards self-consistent"
              if ok else "❌ GUARD FAILED"))
sys.exit(0 if ok else 1)
