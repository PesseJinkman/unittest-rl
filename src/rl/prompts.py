"""Prompt templates for the Qwen3 test-generation policy."""
from __future__ import annotations


SYSTEM_PROMPT = (
    "You are a senior Python engineer who writes rigorous, minimal pytest tests. "
    "You output ONE fenced ```python block containing a single pytest test file and nothing else. "
    "Do not explain. Do not include the module under test. "
    "The module under test will be importable as `target_module`. "
    "Use only pytest (no unittest). Do not import os, subprocess, socket, shutil, sys, "
    "ctypes, threading, multiprocessing, requests, urllib, or http. "
    "Write AT LEAST 3 distinct `def test_*` functions covering typical inputs, edge cases, "
    "and error handling. Where the spec says the function raises, use pytest.raises."
)


USER_TEMPLATE = (
    "Write a thorough pytest file for the following module, importable as `target_module`.\n\n"
    "SPEC:\n{spec}\n\n"
    "MODULE:\n```python\n{code}\n```\n\n"
    "Output exactly one ```python ...``` code block."
)


def build_messages(reference_code: str, spec: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_TEMPLATE.format(code=reference_code, spec=spec)},
    ]
