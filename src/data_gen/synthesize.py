"""Synthesize Python problems (+ reference + subtly buggy variants) with OpenAI."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .openai_client import chat_json, make_client


SYSTEM_PROMPT = """You are a senior Python engineer curating problems for a test-generation benchmark.
You output STRICT JSON conforming to the schema the user provides. No prose, no markdown.
All code MUST be self-contained, pure Python (standard library only), and safe to execute.
Never use: os, subprocess, socket, shutil, sys, ctypes, threading, multiprocessing, requests, urllib, http, open() for writing, eval, exec, __import__.
Never perform I/O. Never sleep. Deterministic behavior only.
"""


LEVEL_DESCRIPTIONS = {
    "L1": (
        "LEVEL 1 — Easy. A single pure function on primitives or lists/strings. "
        "No classes, no exceptions. Clear input/output contract. "
        "Examples: clamp, is_palindrome, run_length_encode, moving_average."
    ),
    "L2": (
        "LEVEL 2 — Medium. A single function with multiple branches, edge cases, "
        "and possibly raising ValueError/TypeError on bad input. May use dicts, sets, sorting. "
        "Examples: parse_version, merge_intervals, group_anagrams, validate_iban."
    ),
    "L3": (
        "LEVEL 3 — Hard. A small class OR 2–3 interacting functions with internal state, "
        "order-dependent behavior, and non-trivial invariants. "
        "Examples: LRUCache class, IntervalSet class, simple expression tokenizer, rolling-window statistic."
    ),
}


SCHEMA_TEMPLATE = """Return a JSON object with exactly these fields:
{{
  "slug": "snake_case_identifier",                       // unique, 3-40 chars
  "spec": "<=600 char natural-language spec describing behavior and edge cases",
  "reference_code": "<complete, self-contained Python module defining the entrypoints>",
  "entrypoints": ["func_or_class_name", ...],            // 1 to 3 names that tests will call
  "sample_inputs": [                                     // 3-6 DIFFERENT call examples
     {{"call": "entrypoint_name", "args": [...], "kwargs": {{}}}}
  ],
  "buggy_variants": [                                     // {n_bugs_min}..{n_bugs_max} SUBTLE wrong versions of reference_code
     {{"id": "bug_01", "description": "<=120 char description of the bug", "code": "<full module code, same public API>"}}
  ]
}}

Rules:
- `reference_code` MUST run without errors on every sample_inputs[i].
- Every buggy variant MUST keep the same public API (same entrypoint names/signatures) so the same tests can target it.
- Every buggy variant MUST produce a DIFFERENT observable result than reference on at least one sample_input (different return value, or reference raises and buggy does not / vice versa). Subtle off-by-one, wrong operator, missing edge case, wrong default, swapped branches, etc.
- Do NOT produce trivial stubs (e.g., `return None` or `pass`). Bugs must be subtle.
- Do NOT import any banned module. Standard library only.
- Keep `reference_code` under 60 lines.
"""


@dataclass
class SynthRequest:
    level: str
    n_bugs_min: int
    n_bugs_max: int
    ideas_hint: str = ""


@dataclass
class RawProblem:
    level: str
    data: dict[str, Any]


def _build_user_prompt(req: SynthRequest) -> str:
    schema = SCHEMA_TEMPLATE.format(n_bugs_min=req.n_bugs_min, n_bugs_max=req.n_bugs_max)
    hint = f"\nIdea hint (optional, pick something else if you prefer): {req.ideas_hint}" if req.ideas_hint else ""
    return (
        f"{LEVEL_DESCRIPTIONS[req.level]}\n\n"
        f"Generate ONE problem at this level.{hint}\n\n"
        f"{schema}"
    )


def synthesize_one(
    client,
    model: str,
    req: SynthRequest,
    *,
    temperature: float = 1.0,
    max_retries: int = 3,
    request_timeout_s: float = 120.0,
) -> RawProblem:
    obj = chat_json(
        client,
        model=model,
        system=SYSTEM_PROMPT,
        user=_build_user_prompt(req),
        temperature=temperature,
        max_retries=max_retries,
        request_timeout_s=request_timeout_s,
    )
    obj["level"] = req.level
    return RawProblem(level=req.level, data=obj)


# --- gold test generation (for SFT warmup) ---

GOLD_SYSTEM = """You are a senior Python engineer writing rigorous pytest tests.
You output STRICT JSON: {"test_code": "<full pytest file contents>"}.
The test file must `from target_module import ...` the entrypoints and use ONLY pytest (no unittest).
Include positive cases, edge cases, and at least one `pytest.raises` where appropriate.
Never import banned modules (os, subprocess, socket, shutil, sys, ctypes, threading, multiprocessing, requests, urllib, http).
"""

GOLD_USER = """Write a thorough pytest file for the following module. Aim for >=5 test functions and high branch coverage.
The module will be importable as `target_module`.

MODULE:
```python
{code}
```

SPEC:
{spec}

Return JSON: {{"test_code": "<file contents>"}}
"""


def synthesize_gold_test(
    client,
    model: str,
    reference_code: str,
    spec: str,
    *,
    temperature: float = 0.7,
    max_retries: int = 3,
    request_timeout_s: float = 120.0,
) -> str:
    obj = chat_json(
        client,
        model=model,
        system=GOLD_SYSTEM,
        user=GOLD_USER.format(code=reference_code, spec=spec),
        temperature=temperature,
        max_retries=max_retries,
        request_timeout_s=request_timeout_s,
    )
    code = obj.get("test_code", "")
    # strip accidental fences
    m = re.match(r"^\s*```(?:python|py)?\s*\n(.*?)```\s*$", code, re.DOTALL | re.IGNORECASE)
    if m:
        code = m.group(1)
    return code.strip() + "\n"
