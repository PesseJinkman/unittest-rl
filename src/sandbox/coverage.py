"""Branch coverage measurement via coverage.py in a subprocess."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .runner import _clean_env, _parse_pytest_output


@dataclass
class CoverageResult:
    branch_coverage: float = 0.0     # 0..1 for the target module
    line_coverage: float = 0.0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    collected: int = 0
    timeout: bool = False
    returncode: int = 0
    stdout_tail: str = ""


def run_pytest_with_coverage(
    module_code: str,
    test_code: str,
    module_filename: str = "target_module.py",
    test_filename: str = "test_target.py",
    timeout_s: float = 25.0,
) -> CoverageResult:
    """Run pytest under coverage.py --branch and return branch coverage for the target module."""
    with tempfile.TemporaryDirectory(prefix="utrl_cov_") as tmp:
        tmpdir = Path(tmp)
        module_path = tmpdir / module_filename
        module_path.write_text(module_code, encoding="utf-8")
        (tmpdir / test_filename).write_text(test_code, encoding="utf-8")
        (tmpdir / "conftest.py").write_text("", encoding="utf-8")
        rc_path = tmpdir / ".coveragerc"
        rc_path.write_text(
            "[run]\n"
            "branch = True\n"
            f"source = {tmpdir.as_posix()}\n"
            "disable_warnings = module-not-imported,no-data-collected,module-not-measured\n",
            encoding="utf-8",
        )
        json_path = tmpdir / "coverage.json"

        env = _clean_env()
        env["COVERAGE_RCFILE"] = str(rc_path)

        cmd_run = [
            sys.executable, "-m", "coverage", "run",
            "--rcfile", str(rc_path),
            "-m", "pytest",
            "-q", "--tb=no", "--disable-warnings",
            "-p", "no:cacheprovider",
            str(tmpdir),
        ]
        try:
            proc = subprocess.run(
                cmd_run,
                cwd=str(tmpdir),
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as e:
            return CoverageResult(
                timeout=True,
                returncode=-1,
                stdout_tail=(e.stdout or "")[-500:] if isinstance(e.stdout, str) else "",
            )

        parsed = _parse_pytest_output(proc.stdout)
        res = CoverageResult(
            passed=parsed["passed"],
            failed=parsed["failed"],
            errors=parsed["errors"],
            collected=parsed["collected"],
            timeout=False,
            returncode=proc.returncode,
            stdout_tail=proc.stdout[-600:],
        )

        # Export JSON report
        try:
            subprocess.run(
                [sys.executable, "-m", "coverage", "json",
                 "--rcfile", str(rc_path), "-o", str(json_path), "-q"],
                cwd=str(tmpdir),
                env=env,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return res

        if not json_path.exists():
            return res
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            return res

        files = data.get("files", {})
        # find target module entry (match by basename)
        target_key = None
        for k in files.keys():
            if Path(k).name == module_filename:
                target_key = k
                break
        if target_key is None:
            # fall back to totals
            tot = data.get("totals", {})
            res.branch_coverage = float(tot.get("percent_covered_branches", 0.0)) / 100.0
            res.line_coverage = float(tot.get("percent_covered", 0.0)) / 100.0
            return res

        summary = files[target_key].get("summary", {})
        # coverage.py: percent_covered_branches when branch=True
        branch_pct = summary.get("percent_covered_branches")
        if branch_pct is None:
            # derive: covered_branches / num_branches if present, else fall back to line cov
            nb = summary.get("num_branches") or 0
            cb = summary.get("covered_branches") or 0
            branch_pct = (100.0 * cb / nb) if nb > 0 else summary.get("percent_covered", 0.0)
        res.branch_coverage = float(branch_pct) / 100.0
        res.line_coverage = float(summary.get("percent_covered", 0.0)) / 100.0
        return res
