"""Single LLM interface for all of Curie (backend.md §7.4).

Every LLM call goes through complete(). JSON tasks validate against a pydantic model with one
retry, then return None so the caller can use a deterministic fallback (never a guessed verdict).
Default provider OpenAI; Anthropic optional fallback behind the same interface.
"""
from __future__ import annotations
import json, os, pathlib
from typing import Type, TypeVar, overload
from pydantic import BaseModel, ValidationError

_PROMPTS = pathlib.Path(__file__).parent.parent / "prompts"
T = TypeVar("T", bound=BaseModel)

# Per-task model routing (CLAUDE.md: gpt-4.1-mini for parse/RCS, gpt-4.1 for verdict).
# Override via CURIE_MODEL_MINI / CURIE_MODEL_VERDICT; OPENAI_MODEL is the final fallback.
_VERDICT_TASKS = {"verdict"}


def load_prompt(name: str) -> str:
    return (_PROMPTS / f"{name}.txt").read_text()


def _strip_fences(s: str) -> str:
    """Tolerate ```json ... ``` (or bare ```) fences some models wrap JSON in."""
    s = s.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[-1] if "\n" in s else s[3:]
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
    return s.strip()


def _model_for(task: str) -> str:
    # Verdict uses the big model (OPENAI_MODEL, default gpt-4.1); parse/check/RCS use the mini model.
    if task in _VERDICT_TASKS:
        return os.environ.get("CURIE_MODEL_VERDICT", os.environ.get("OPENAI_MODEL", "gpt-4.1"))
    return os.environ.get("CURIE_MODEL_MINI", "gpt-4.1-mini")


def _openai_call(system: str, user: str, json_mode: bool, model: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    kwargs = dict(
        model=model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0,
    )
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    return client.chat.completions.create(**kwargs).choices[0].message.content or ""


def _anthropic_call(system: str, user: str, json_mode: bool, model: str) -> str:
    from anthropic import Anthropic
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    sys = system + ("\n\nReturn ONLY valid JSON, no prose." if json_mode else "")
    msg = client.messages.create(
        model=os.environ.get("ANTHROPIC_MODEL", model),
        max_tokens=1500, temperature=0, system=sys,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")


def _raw(system: str, user: str, json_mode: bool, model: str) -> str:
    fn = _anthropic_call if os.environ.get("CURIE_LLM") == "anthropic" else _openai_call
    return fn(system, user, json_mode, model)


@overload
def complete(task: str, *, system: str, user: str, model_cls: Type[T]) -> T | None: ...
@overload
def complete(task: str, *, system: str, user: str) -> str: ...

def complete(task, *, system, user, model_cls=None):
    """One interface for every LLM call.

    Text mode → returns str (raises on hard failure; callers wrap).
    JSON mode (model_cls set) → validates against the pydantic model, one retry, then returns
    None so the caller can fall back deterministically (backend.md §13 — never a guessed verdict).
    ANY failure in JSON mode (bad JSON, missing key, network, API error) resolves to None.
    """
    model = _model_for(task)
    if model_cls is None:
        return _raw(system, user, json_mode=False, model=model).strip()
    for attempt in range(2):
        try:
            raw = _raw(system, user, json_mode=True, model=model)
            return model_cls.model_validate_json(_strip_fences(raw))
        except (ValidationError, json.JSONDecodeError):
            if attempt == 0:
                user += "\n\nYour previous reply was not valid JSON for the schema. Return ONLY the JSON object."
        except Exception:
            # Missing API key, network, rate limit, provider error → deterministic fallback.
            return None
    return None
