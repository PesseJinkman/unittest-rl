"""Load validated problems from disk into an in-memory structure usable by training."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Problem:
    slug: str
    level: str
    spec: str
    reference_code: str
    entrypoints: list[str]
    sample_inputs: list[dict[str, Any]]
    buggy_variants: list[dict[str, Any]]  # each: {"id", "description", "code"}

    @property
    def variant_codes(self) -> list[str]:
        return [v["code"] for v in self.buggy_variants]


def load_problem_dir(problem_dir: Path) -> Problem:
    meta = json.loads((problem_dir / "meta.json").read_text(encoding="utf-8"))
    ref = (problem_dir / "reference.py").read_text(encoding="utf-8")
    spec = (problem_dir / "spec.md").read_text(encoding="utf-8")
    variants = []
    buggy_dir = problem_dir / "buggy"
    if buggy_dir.is_dir():
        for vmeta in meta.get("buggy_variants", []):
            vpath = buggy_dir / f"{vmeta['id']}.py"
            if vpath.exists():
                variants.append({
                    "id": vmeta["id"],
                    "description": vmeta.get("description", ""),
                    "code": vpath.read_text(encoding="utf-8"),
                })
    return Problem(
        slug=meta["slug"],
        level=meta["level"],
        spec=spec,
        reference_code=ref,
        entrypoints=meta["entrypoints"],
        sample_inputs=meta.get("sample_inputs", []),
        buggy_variants=variants,
    )


def load_problems(root: Path, levels: list[str] | None = None) -> dict[str, list[Problem]]:
    """Return {level: [Problem, ...]}."""
    out: dict[str, list[Problem]] = {}
    levels = levels or ["L1", "L2", "L3"]
    for lv in levels:
        lv_dir = root / lv
        if not lv_dir.is_dir():
            out[lv] = []
            continue
        probs = []
        for d in sorted(lv_dir.iterdir()):
            if d.is_dir() and (d / "meta.json").exists():
                try:
                    probs.append(load_problem_dir(d))
                except Exception:
                    continue
        out[lv] = probs
    return out
