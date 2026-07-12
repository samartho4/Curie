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

ok = (r1.level == "clear" and r2.level == "collision" and r3.level == "clear" and r4.level == "clear"
      and r5.level == "clear"
      and r6.level == "collision" and len(r6.diff) >= 1 and len(_r6_matching) >= 1)
print("\n" + ("✅ CALIBRATION GUARD PASSES — false/empty-diff collisions blocked, real ones kept"
              if ok else "❌ GUARD FAILED"))
sys.exit(0 if ok else 1)
