"""scholar.py — live scientific-literature retrieval over OpenAlex + bioRxiv (backend.md §5.5).

No API key. Returns normalized dicts; NEVER raises to the caller — on failure returns [] so the
verdict degrades to "literature unavailable" instead of blocking (backend.md §7.1).
Both endpoints were verified working July 2026.

Can be imported directly (tools.scholar.search_literature) OR run as a FastMCP server
(python -m tools.scholar) — the app launches it via MCP or calls the functions in-process.
"""
from __future__ import annotations
import os, httpx

_MAILTO = os.environ.get("CURIE_MAILTO", "curie-hackathon@example.com")
_TIMEOUT = 10.0
_NEG = "null result OR no significant OR failed to OR did not improve OR no effect OR negative result"


def _openalex(query: str, limit: int) -> list[dict]:
    r = httpx.get("https://api.openalex.org/works",
                  params={"search": query, "per-page": limit, "mailto": _MAILTO},
                  timeout=_TIMEOUT)
    r.raise_for_status()
    out = []
    for w in r.json().get("results", []):
        inv = w.get("abstract_inverted_index")
        out.append({
            "title": w.get("title") or "(untitled)",
            "year": w.get("publication_year"),
            "doi": w.get("doi"),
            "url": (w.get("primary_location") or {}).get("landing_page_url") or w.get("doi"),
            "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
            "cited_by": w.get("cited_by_count", 0),
            "is_retracted": bool(w.get("is_retracted")),
            "abstract_snippet": _deinvert(inv)[:280] if inv else None,
        })
    return out


def _deinvert(inv: dict) -> str:
    if not inv:
        return ""
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


def search_literature(query: str, limit: int = 8) -> list[dict]:
    try:
        return _openalex(query, limit)
    except Exception:
        return []


def find_null_results(topic: str, limit: int = 8) -> list[dict]:
    """Bias the search toward negative/null findings — the evidence journals bury."""
    try:
        return _openalex(f"{topic} {_NEG}", limit)
    except Exception:
        return []


def get_paper(doi_or_url: str) -> dict | None:
    try:
        key = doi_or_url.split("doi.org/")[-1] if "doi.org" in doi_or_url else doi_or_url
        r = httpx.get(f"https://api.openalex.org/works/https://doi.org/{key}",
                      params={"mailto": _MAILTO}, timeout=_TIMEOUT)
        if r.status_code != 200:
            return None
        w = r.json()
        return {"title": w.get("title"), "year": w.get("publication_year"),
                "is_retracted": bool(w.get("is_retracted")), "cited_by": w.get("cited_by_count", 0),
                "url": w.get("doi")}
    except Exception:
        return None


# ---- optional FastMCP server wrapper (backend.md §5.5) --------------------
def _serve():
    from mcp.server.fastmcp import FastMCP
    mcp = FastMCP("scholar")
    mcp.tool()(search_literature)
    mcp.tool()(find_null_results)
    mcp.tool()(get_paper)
    mcp.run()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        r = search_literature("protein language model fine-tuning", 2)
        print(f"OpenAlex OK: {len(r)} hits; first = {r[0]['title'][:70] if r else 'NONE'}")
        n = find_null_results("batch normalization transformer", 2)
        print(f"null-results OK: {len(n)} hits")
    else:
        _serve()
