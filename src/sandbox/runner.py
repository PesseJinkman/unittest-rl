"""Isolated pytest execution sandbox.

Runs a generated test file against a target module in a fresh temp directory
using a subprocess with a timeout and a stripped environment.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class RunResult:
    passed: int = 0
    failed: int = 0
    errors: int = 0
    collected: int = 0
    timeout: bool = False
    returncode: int = 0
    stdout_tail: str = ""
    stderr_tail: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# pytest summary regexes: "3 passed", "1 failed", "2 errors", "5 passed, 1 failed in ..."
_SUMMARY_RE = re.compile(
    r"(?P<n>\d+)\s+(?P<kind>passed|failed|errors|error|skipped)",
    re.IGNORECASE,
)
_COLLECTED_RE = re.compile(r"collected\s+(\d+)\s+item", re.IGNORECASE)


def _parse_pytest_output(stdout: str) -> dict:
    out = {"passed": 0, "failed": 0, "errors": 0, "collected": 0}
    m = _COLLECTED_RE.search(stdout)
    if m:
        out["collected"] = int(m.group(1))
    # scan final summary lines (last ~10 lines)
    tail = "\n".join(stdout.splitlines()[-15:])
    for m in _SUMMARY_RE.finditer(tail):
        n = int(m.group("n"))
        kind = m.group("kind").lower()
        if kind == "passed":
            out["passed"] = n
        elif kind == "failed":
            out["failed"] = n
        elif kind in ("error", "errors"):
            out["errors"] = n
    if out["collected"] == 0:
        out["collected"] = out["passed"] + out["failed"] + out["errors"]
    return out


def _clean_env() -> dict:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUNBUFFERED": "1",
    }
    # Windows needs SYSTEMROOT, APPDATA, etc. for many stdlib / site code paths
    for key in ("SYSTEMROOT", "SYSTEMDRIVE", "TEMP", "TMP",
                "USERPROFILE", "HOMEPATH", "HOMEDRIVE",
                "APPDATA", "LOCALAPPDATA", "PROGRAMDATA",
                "PROGRAMFILES", "PROGRAMFILES(X86)",
                "VIRTUAL_ENV", "CONDA_PREFIX"):
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def run_pytest(
    module_code: str,
    test_code: str,
    module_filename: str = "target_module.py",
    test_filename: str = "test_target.py",
    timeout_s: float = 15.0,
) -> RunResult:
    """Write module + test to a tempdir and run pytest in a subprocess."""
    with tempfile.TemporaryDirectory(prefix="utrl_") as tmp:
        tmpdir = Path(tmp)
        (tmpdir / module_filename).write_text(module_code, encoding="utf-8")
        (tmpdir / test_filename).write_text(test_code, encoding="utf-8")
        # ensure no conftest interference
        (tmpdir / "conftest.py").write_text("", encoding="utf-8")

        cmd = [
            sys.executable,
            "-m", "pytest",
            "-q",
            "--tb=no",
            "--disable-warnings",
            "-p", "no:cacheprovider",
            str(tmpdir),
        ]
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(tmpdir),
                env=_clean_env(),
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            return RunResult(
                timeout=True,
                returncode=-1,
                stdout_tail=(e.stdout or "")[-500:] if isinstance(e.stdout, str) else "",
                stderr_tail=(e.stderr or "")[-500:] if isinstance(e.stderr, str) else "",
            )

        parsed = _parse_pytest_output(proc.stdout)
        return RunResult(
            passed=parsed["passed"],
            failed=parsed["failed"],
            errors=parsed["errors"],
            collected=parsed["collected"],
            timeout=False,
            returncode=proc.returncode,
            stdout_tail=proc.stdout[-800:],
            stderr_tail=proc.stderr[-400:],
        )
