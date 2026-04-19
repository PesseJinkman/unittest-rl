"""Composite reward: pytest passability + hidden-bug catch rate + branch coverage."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any

from ..sandbox.coverage import run_pytest_with_coverage
from ..sandbox.runner import run_pytest
from .parse import parse_test_output


@dataclass
class RewardConfig:
    w_pass: float = 0.40
    w_bugs: float = 0.40
    w_cov: float = 0.20
    min_tests: int = 2
    pytest_timeout_s: float = 15.0
    coverage_timeout_s: float = 25.0
    banned_imports: list[str] = field(default_factory=list)
    penalty_timeout: float = 0.2
    penalty_banned_import: float = 0.5
    parallel_workers: int = 8


@dataclass
class RewardBreakdown:
    reward: float = 0.0
    pass_ref: float = 0.0
    bug_catch: float = 0.0
    branch_cov: float = 0.0
    n_tests: int = 0
    n_variants: int = 0
    n_variants_caught: int = 0
    timeouts: int = 0
    parse_ok: bool = False
    reason: str = ""
    banned_imports: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = self.__dict__.copy()
        d["banned_imports"] = list(self.banned_imports)
        return d


def _variant_catches(module_code: str, test_code: str, timeout_s: float) -> tuple[bool, bool]:
    """Return (caught, timeout). A variant is 'caught' if any test fails/errors
    when run against the buggy code."""
    r = run_pytest(module_code, test_code, timeout_s=timeout_s)
    if r.timeout:
        return (False, True)
    caught = (r.failed + r.errors) > 0
    return (caught, False)


def score(
    test_output: str,
    reference_code: str,
    buggy_variants: list[str],
    cfg: RewardConfig,
) -> RewardBreakdown:
    """Compute composite reward breakdown for one generated test output."""
    parsed = parse_test_output(test_output, banned_imports=cfg.banned_imports)
    rb = RewardBreakdown(parse_ok=parsed.ok, n_tests=parsed.num_test_funcs,
                         n_variants=len(buggy_variants), reason=parsed.reason,
                         banned_imports=parsed.banned_imports)
    if not parsed.ok:
        return rb
    if parsed.num_test_funcs < cfg.min_tests:
        rb.reason = f"too_few_tests({parsed.num_test_funcs}<{cfg.min_tests})"
        return rb

    # 1. pass on reference + coverage (single combined run)
    cov_res = run_pytest_with_coverage(
        module_code=reference_code,
        test_code=parsed.code,
        timeout_s=cfg.coverage_timeout_s,
    )
    timeouts = 1 if cov_res.timeout else 0
    pass_ref = 0.0
    if (not cov_res.timeout
            and cov_res.collected >= cfg.min_tests
            and cov_res.failed == 0
            and cov_res.errors == 0
            and cov_res.passed >= cfg.min_tests):
        pass_ref = 1.0

    rb.pass_ref = pass_ref
    rb.branch_cov = max(0.0, min(1.0, cov_res.branch_coverage))

    # 2. buggy variants (only if we got at least a parseable test; bug-catch term is
    # gated by pass_ref in the composition, but we still measure it for logging)
    caught = 0
    if buggy_variants:
        workers = max(1, min(cfg.parallel_workers, len(buggy_variants)))
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [
                ex.submit(_variant_catches, v, parsed.code, cfg.pytest_timeout_s)
                for v in buggy_variants
            ]
            for fut in futs:
                try:
                    c, to = fut.result()
                    if to:
                        timeouts += 1
                    elif c:
                        caught += 1
                except Exception:
                    pass
    rb.n_variants_caught = caught
    rb.timeouts = timeouts
    rb.bug_catch = (caught / len(buggy_variants)) if buggy_variants else 0.0

    # 3. compose
    r = (cfg.w_pass * rb.pass_ref
         + cfg.w_bugs * rb.pass_ref * rb.bug_catch
         + cfg.w_cov * rb.pass_ref * rb.branch_cov)

    # penalties
    if timeouts > 0:
        r -= cfg.penalty_timeout
    if parsed.banned_imports:
        r -= cfg.penalty_banned_import

    rb.reward = max(0.0, min(1.0, r))
    return rb
