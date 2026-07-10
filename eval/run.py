"""eval/run.py — the verdict gate (backend.md §8, §13).

Runs every labelled plan in eval/cases.yaml through the REAL pipeline (pipeline.preflight) and prints
a confusion matrix. Exits NON-ZERO on any FALSE COLLISION (expected clear/near_miss but got collision) —
the unforgivable bug. A false "clear" on a near_miss/landmine is tolerable (tracked, not gated).

Default = OFFLINE: candidates come from a seed fixture built out of seed/lab_story.yaml, so the gate
runs with only OPENAI_API_KEY (no live Slack). This is the CI gate you run on every change.
    python -m eval.run            # offline seed-fixture providers
    python -m eval.run --live     # hit the live sandbox (bot List + user-token RTS + scholar)

Without an OpenAI key it still runs (no crash): every plan resolves to parse_fail, which cannot be a
false collision — so the run PASSES and proves the harness executes. Real numbers need the key.
"""
from __future__ import annotations
import os, sys, pathlib, yaml
from dotenv import load_dotenv

load_dotenv()
from pipeline import preflight
from tools.record_store import _plan_terms

ROOT = pathlib.Path(__file__).parent
CASES = yaml.safe_load((ROOT / "cases.yaml").read_text())["cases"]
STORY = yaml.safe_load((pathlib.Path(__file__).parent.parent / "seed" / "lab_story.yaml").read_text())

LEVELS = ["collision", "near_miss", "clear"]
GOT_COLS = ["collision", "near_miss", "clear", "parse_fail", "error"]


# ---- offline seed-fixture providers -------------------------------------------------------

class SeedRecord:
    """Turns seed experiments into List-style candidates; matches by term overlap (like record_store)."""

    def __init__(self):
        self.exps = STORY.get("experiments", [])

    def find_candidates(self, plan):
        terms = _plan_terms(plan)
        scored = []
        for e in self.exps:
            hay = " ".join([
                e.get("plan", ""), " ".join(f"{k} {v}" for k, v in (e.get("params") or {}).items()),
                e.get("outcome", ""),
            ]).lower()
            hits = sum(1 for t in terms if t in hay)
            if hits:
                scored.append((hits, e))
        scored.sort(key=lambda x: x[0], reverse=True)
        out = []
        for _, e in scored[:6]:
            out.append({
                "source": "list",
                "title": f"{e.get('owner','?')} — {e.get('plan','')[:70]}",
                "text": f"{e.get('plan','')} {e.get('outcome','')}",
                "permalink": f"https://seed.local/{e['ref']}",
                "outcome": e.get("outcome"),
                "params": {k: str(v) for k, v in (e.get("params") or {}).items()},
                "_ref": e["ref"],
            })
        return out


class _Null:
    degraded = False

    def search(self, query):
        return []


# ---- live providers (Mac only; RTS via user token = no action_token needed) ---------------

def _live_providers():
    from slack_sdk import WebClient
    from tools.rts import RTS
    from tools.record_store import RecordStore
    from tools import scholar as scholar_mod

    bot = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
    user_tok = os.environ.get("CURIE_USER_TOKEN")
    rts = RTS(WebClient(token=user_tok) if user_tok else bot,
              is_user_token=bool(user_tok), budget=3)

    class LiveScholar:
        degraded = False

        def search(self, q):
            try:
                return scholar_mod.search_literature(q, 6)
            except Exception:
                self.degraded = True
                return []

    return RecordStore(bot, os.environ.get("CURIE_LIST_ID")), rts, LiveScholar()


# ---- runner -------------------------------------------------------------------------------

def _got(result) -> str:
    if result.kind == "verdict":
        return result.verdict.level
    return result.kind  # parse_fail | error


def main():
    live = "--live" in sys.argv
    have_llm = bool(os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"))

    if live:
        try:
            record, rts_factory, scholar = _live_providers()
            print("Mode: LIVE (bot List + user-token RTS + scholar)")
        except Exception as e:
            print(f"--live unavailable ({e}); falling back to offline.")
            live = False
    if not live:
        record, scholar = SeedRecord(), _Null()
        print("Mode: OFFLINE (seed fixture)")
    if not have_llm:
        print("!! No OPENAI_API_KEY — plans will parse_fail; run proves the harness executes, "
              "not calibration. Set the key on the Mac for real numbers.\n")

    matrix = {exp: {g: 0 for g in GOT_COLS} for exp in LEVELS}
    false_collisions, false_clears, ref_ok, ref_total = [], [], 0, 0

    for case in CASES:
        expected = case["expected_level"]
        # fresh RTS per verdict (budget) in live mode
        rts = (_live_providers()[1] if live else _Null())
        result = preflight.run_preflight(case["plan"], record=record, rts=rts, scholar=scholar)
        got = _got(result)
        matrix.setdefault(expected, {g: 0 for g in GOT_COLS})
        matrix[expected][got] = matrix[expected].get(got, 0) + 1

        if expected in ("clear", "near_miss") and got == "collision":
            false_collisions.append(case["id"])
        if expected == "collision" and got in ("clear", "near_miss", "parse_fail", "error"):
            false_clears.append(case["id"])
        if expected == "collision" and case.get("collision_ref"):
            ref_total += 1
            if result.kind == "verdict" and any(
                getattr(c, "permalink", "").endswith(case["collision_ref"]) for c in result.verdict.collisions):
                ref_ok += 1
        print(f"  {case['id']:<3} expected={expected:<9} got={got}")

    _print_matrix(matrix)
    print(f"\nFalse collisions (GATE): {len(false_collisions)}  {false_collisions or ''}")
    print(f"False clears (tolerated): {len(false_clears)}  {false_clears or ''}")
    if ref_total:
        print(f"Collision ref hit-rate: {ref_ok}/{ref_total}")

    if false_collisions:
        print("\nFAIL — at least one false collision. This is the unforgivable bug.")
        sys.exit(1)
    print("\nPASS — zero false collisions.")
    sys.exit(0)


def _print_matrix(matrix):
    print("\nConfusion matrix (rows = expected, cols = got):")
    print(f"  {'':<11}" + "".join(f"{g:<11}" for g in GOT_COLS))
    for exp in LEVELS:
        row = matrix.get(exp, {})
        print(f"  {exp:<11}" + "".join(f"{row.get(g,0):<11}" for g in GOT_COLS))


if __name__ == "__main__":
    main()
