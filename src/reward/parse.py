"""Parse model output into a runnable pytest source file."""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field


_FENCE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


@dataclass
class ParsedTest:
    ok: bool = False
    code: str = ""
    num_test_funcs: int = 0
    reason: str = ""
    banned_imports: list[str] = field(default_factory=list)


def extract_python_block(text: str) -> str:
    """Return the first fenced python block, or the raw text if none found."""
    if text is None:
        return ""
    m = _FENCE_RE.search(text)
    if m:
        return m.group(1).strip()
    # if the model produced raw code, accept it as-is
    return text.strip()


def _count_test_funcs(tree: ast.AST) -> int:
    n = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_"):
                n += 1
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name.startswith("test_"):
                    n += 1
    return n


def _find_banned_imports(tree: ast.AST, banned: set[str]) -> list[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                top = a.name.split(".")[0]
                if top in banned:
                    found.add(top)
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod in banned:
                found.add(mod)
    return sorted(found)


def parse_test_output(text: str, banned_imports: list[str] | None = None) -> ParsedTest:
    banned = set(banned_imports or [])
    code = extract_python_block(text)
    if not code:
        return ParsedTest(ok=False, code="", reason="empty_output")
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return ParsedTest(ok=False, code=code, reason=f"syntax_error: {e.msg}")

    n = _count_test_funcs(tree)
    if n == 0:
        return ParsedTest(ok=False, code=code, num_test_funcs=0, reason="no_test_functions")

    bad = _find_banned_imports(tree, banned)
    return ParsedTest(ok=True, code=code, num_test_funcs=n, banned_imports=bad)
