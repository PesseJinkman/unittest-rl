"""Validate synthesized problems: reference runs, variants are distinguishable, no banned imports."""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..sandbox.runner import _clean_env


_SLUG_RE = re.compile(r"^[a-z][a-z0-9_]{2,39}$")


@dataclass
class ValidationResult:
    ok: bool
    reason: str = ""
    accepted_variants: list[dict[str, Any]] | None = None


def _has_banned_import(code: str, banned: set[str]) -> str | None:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"syntax_error: {e.msg}"
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                top = a.name.split(".")[0]
                if top in banned:
                    return f"banned_import:{top}"
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod in banned:
                return f"banned_import:{mod}"
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in ("eval", "exec", "__import__"):
                return f"banned_call:{node.func.id}"
    return None


def _build_harness(sample_inputs: list[dict[str, Any]]) -> str:
    """Python script that imports target_module, executes each sample call,
    prints JSON list of {'ok': bool, 'value': repr | None, 'exc': str | None}."""
    return (
        "import json, traceback, importlib\n"
        "mod = importlib.import_module('target_module')\n"
        f"samples = {json.dumps(sample_inputs)}\n"
        "out = []\n"
        "for s in samples:\n"
        "    name = s['call']\n"
        "    args = s.get('args') or []\n"
        "    kwargs = s.get('kwargs') or {}\n"
        "    try:\n"
        "        fn = getattr(mod, name)\n"
        "        val = fn(*args, **kwargs)\n"
        "        try:\n"
        "            rep = repr(val)\n"
        "        except Exception:\n"
        "            rep = '<unreprable>'\n"
        "        out.append({'ok': True, 'value': rep, 'exc': None})\n"
        "    except BaseException as e:\n"
        "        out.append({'ok': False, 'value': None, 'exc': type(e).__name__ + ':' + str(e)[:120]})\n"
        "print('__RESULT__' + json.dumps(out))\n"
    )


def _run_harness(module_code: str, harness: str, timeout_s: float) -> list[dict[str, Any]] | None:
    with tempfile.TemporaryDirectory(prefix="utrl_val_") as tmp:
        tmpdir = Path(tmp)
        (tmpdir / "target_module.py").write_text(module_code, encoding="utf-8")
        (tmpdir / "_run.py").write_text(harness, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, str(tmpdir / "_run.py")],
                cwd=str(tmpdir),
                env=_clean_env(),
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return None
        # find line beginning with __RESULT__
        for line in proc.stdout.splitlines()[::-1]:
            if line.startswith("__RESULT__"):
                try:
                    return json.loads(line[len("__RESULT__"):])
                except Exception:
                    return None
        return None


def _outputs_differ(a: dict[str, Any], b: dict[str, Any]) -> bool:
    if a["ok"] != b["ok"]:
        return True
    if a["ok"]:
        return a["value"] != b["value"]
    # both raised: count different exception types as different
    ea = (a["exc"] or "").split(":", 1)[0]
    eb = (b["exc"] or "").split(":", 1)[0]
    return ea != eb


def validate_problem(
    problem: dict[str, Any],
    *,
    banned_imports: list[str],
    sample_input_timeout_s: float = 5.0,
) -> ValidationResult:
    required = ("slug", "spec", "reference_code", "entrypoints", "sample_inputs", "buggy_variants")
    for k in required:
        if k not in problem:
            return ValidationResult(False, f"missing_field:{k}")

    slug = str(problem["slug"])
    if not _SLUG_RE.match(slug):
        return ValidationResult(False, f"bad_slug:{slug!r}")

    sample_inputs = problem["sample_inputs"]
    if not isinstance(sample_inputs, list) or len(sample_inputs) < 2:
        return ValidationResult(False, "need_>=2_sample_inputs")

    banned = set(banned_imports)
    # reference
    ref_code = problem["reference_code"]
    b = _has_banned_import(ref_code, banned)
    if b:
        return ValidationResult(False, f"reference_{b}")

    harness = _build_harness(sample_inputs)
    ref_out = _run_harness(ref_code, harness, sample_input_timeout_s)
    if ref_out is None:
        return ValidationResult(False, "reference_timeout_or_crash")
    # reference must succeed on every declared sample input (contract in synth prompt)
    if not all(x["ok"] for x in ref_out):
        bad = next((x["exc"] for x in ref_out if not x["ok"]), None)
        return ValidationResult(False, f"reference_fails_sample:{bad}")

    variants = problem["buggy_variants"]
    if not isinstance(variants, list) or len(variants) < 2:
        return ValidationResult(False, "need_>=2_buggy_variants")

    accepted = []
    for v in variants:
        vcode = v.get("code", "")
        b = _has_banned_import(vcode, banned)
        if b:
            continue
        # must keep same entrypoints
        try:
            vtree = ast.parse(vcode)
        except SyntaxError:
            continue
        defined_names: set[str] = set()
        for node in vtree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                defined_names.add(node.name)
        if not set(problem["entrypoints"]).issubset(defined_names):
            continue

        v_out = _run_harness(vcode, harness, sample_input_timeout_s)
        if v_out is None:
            continue
        # reject variants that crash on ALL inputs
        if not any(x["ok"] for x in v_out):
            continue
        # must differ from reference on at least one input
        diffs = sum(1 for a, b_ in zip(ref_out, v_out) if _outputs_differ(a, b_))
        if diffs == 0:
            continue
        accepted.append(v)

    if len(accepted) < 2:
        return ValidationResult(False, f"not_enough_distinguishable_variants({len(accepted)})")

    return ValidationResult(True, "ok", accepted_variants=accepted)
