"""Smoke tests: sandbox runner, coverage, reward scorer, curriculum, parser."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.reward.parse import extract_python_block, parse_test_output
from src.reward.scorer import RewardConfig, score
from src.rl.curriculum import CurriculumState
from src.sandbox.coverage import run_pytest_with_coverage
from src.sandbox.runner import run_pytest


REF = """
def clamp(x, lo, hi):
    if lo > hi:
        raise ValueError("lo > hi")
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x
"""

# bug: off-by-one on the upper bound
BUG_OFFBY = """
def clamp(x, lo, hi):
    if lo > hi:
        raise ValueError("lo > hi")
    if x < lo:
        return lo
    if x > hi - 1:
        return hi
    return x
"""

# bug: never raises
BUG_NORAISE = """
def clamp(x, lo, hi):
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x
"""

GOOD_TESTS = """
from target_module import clamp
import pytest

def test_inside():
    assert clamp(5, 0, 10) == 5

def test_below():
    assert clamp(-3, 0, 10) == 0

def test_above():
    assert clamp(15, 0, 10) == 10

def test_edge_upper():
    assert clamp(10, 0, 10) == 10

def test_raises():
    with pytest.raises(ValueError):
        clamp(5, 10, 0)
"""

BAD_ALWAYS_FAIL = """
def test_a():
    assert False

def test_b():
    assert False
"""

EMPTY_TESTS = """
def test_noop():
    assert True
"""


def test_run_pytest_pass():
    r = run_pytest(REF, GOOD_TESTS)
    assert r.timeout is False
    assert r.passed == 5
    assert r.failed == 0
    assert r.errors == 0


def test_run_pytest_detects_bug():
    r = run_pytest(BUG_NORAISE, GOOD_TESTS)
    assert r.timeout is False
    # at least one test (test_raises) should fail
    assert (r.failed + r.errors) >= 1


def test_coverage_reports_nonzero_branches():
    r = run_pytest_with_coverage(REF, GOOD_TESTS)
    assert r.timeout is False
    assert r.passed >= 3
    assert r.branch_coverage > 0.5  # our tests cover all branches


def test_parse_extracts_block():
    text = "here you go:\n```python\ndef test_x():\n    assert 1\n```\ndone"
    p = parse_test_output(text, banned_imports=["os"])
    assert p.ok
    assert p.num_test_funcs == 1


def test_parse_rejects_no_test_funcs():
    text = "```python\nx = 1\n```"
    p = parse_test_output(text, banned_imports=[])
    assert not p.ok
    assert "no_test_functions" in p.reason


def test_parse_detects_banned_import():
    text = "```python\nimport os\ndef test_x():\n    assert 1\n```"
    p = parse_test_output(text, banned_imports=["os"])
    assert p.ok
    assert "os" in p.banned_imports


def test_scorer_rewards_good_tests():
    cfg = RewardConfig(banned_imports=["os", "subprocess"])
    out = f"```python\n{GOOD_TESTS}\n```"
    rb = score(out, REF, [BUG_OFFBY, BUG_NORAISE], cfg)
    assert rb.parse_ok
    assert rb.pass_ref == 1.0
    assert rb.n_variants_caught >= 1
    assert rb.branch_cov > 0.5
    assert rb.reward > 0.6


def test_scorer_blocks_assert_false_exploit():
    """Tests that always fail should get ~0 reward despite 'catching' all bugs."""
    cfg = RewardConfig(banned_imports=[])
    out = f"```python\n{BAD_ALWAYS_FAIL}\n```"
    rb = score(out, REF, [BUG_OFFBY, BUG_NORAISE], cfg)
    # pass_ref=0 => composed reward = 0 (modulo penalties)
    assert rb.pass_ref == 0.0
    assert rb.reward == 0.0


def test_scorer_min_tests_gate():
    cfg = RewardConfig(banned_imports=[], min_tests=2)
    out = f"```python\n{EMPTY_TESTS}\n```"
    rb = score(out, REF, [], cfg)
    assert rb.reward == 0.0


def test_curriculum_advances_on_threshold():
    c = CurriculumState(levels=["L1", "L2", "L3"], eval_window_steps=5,
                        rolling_n=10, advance_threshold=0.7, consecutive_windows=2)
    assert c.level == "L1"
    # push 15 high rewards across 15 steps; windows at step 5, 10, 15
    for _ in range(15):
        c.record_rewards([0.9, 0.9])
        c.maybe_advance()
    assert c.level == "L2"


def test_curriculum_does_not_advance_when_low():
    c = CurriculumState(levels=["L1", "L2"], eval_window_steps=5,
                        rolling_n=10, advance_threshold=0.7, consecutive_windows=2)
    for _ in range(20):
        c.record_rewards([0.3, 0.2])
        c.maybe_advance()
    assert c.level == "L1"
