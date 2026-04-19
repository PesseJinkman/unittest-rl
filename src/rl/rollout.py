"""Reward function factory + IterableDataset for curriculum-driven GRPO training."""
from __future__ import annotations

import random
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator

import torch.utils.data as torch_data

from ..reward.scorer import RewardBreakdown, RewardConfig, score
from .curriculum import CurriculumState
from .dataset import Problem
from .prompts import build_messages


@dataclass
class TrainBuffer:
    """Shared buffer of recent reward breakdowns; drained by a Trainer callback."""
    lock: threading.Lock = field(default_factory=threading.Lock)
    pending: list[RewardBreakdown] = field(default_factory=list)

    def push(self, rbs: list[RewardBreakdown]) -> None:
        with self.lock:
            self.pending.extend(rbs)

    def drain(self) -> list[RewardBreakdown]:
        with self.lock:
            out = self.pending
            self.pending = []
        return out


class CurriculumIterableDataset(torch_data.IterableDataset):
    """Infinite stream of {'prompt', 'reference_code', 'buggy_variants', 'slug', 'level'}
    sampled from the CURRENT curriculum level. The `tokenizer.apply_chat_template` is
    applied here so TRL receives a plain text prompt."""

    def __init__(
        self,
        problems_by_level: dict[str, list[Problem]],
        curriculum: CurriculumState,
        tokenizer,
        seed: int = 0,
        max_prompt_tokens: int = 1024,
    ):
        super().__init__()
        self.problems_by_level = problems_by_level
        self.curriculum = curriculum
        self.tokenizer = tokenizer
        self.rng = random.Random(seed)
        self.max_prompt_tokens = max_prompt_tokens

    def __iter__(self) -> Iterator[dict[str, Any]]:
        while True:
            level = self.curriculum.level
            pool = self.problems_by_level.get(level) or []
            if not pool:
                # fall back to any non-empty level
                for lv in self.curriculum.levels:
                    if self.problems_by_level.get(lv):
                        pool = self.problems_by_level[lv]
                        level = lv
                        break
                if not pool:
                    raise RuntimeError("No problems available in any level")
            p = self.rng.choice(pool)
            messages = build_messages(p.reference_code, p.spec)
            prompt_text = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            ids = self.tokenizer.encode(prompt_text)
            if len(ids) > self.max_prompt_tokens:
                ids = ids[-self.max_prompt_tokens:]
                prompt_text = self.tokenizer.decode(ids, skip_special_tokens=False)
            yield {
                "prompt": prompt_text,
                "reference_code": p.reference_code,
                "buggy_variants": p.variant_codes,
                "slug": p.slug,
                "level": level,
            }


def make_reward_fn(
    reward_cfg: RewardConfig,
    buffer: TrainBuffer,
) -> Callable[..., list[float]]:
    """Returns a reward function compatible with TRL's GRPOTrainer.

    Signature: reward_fn(prompts, completions, **kwargs) -> list[float]
    kwargs contain dataset column values as lists aligned to completions.
    """

    def _reward(prompts=None, completions=None, **kwargs) -> list[float]:
        if completions is None:
            return []
        refs = kwargs.get("reference_code") or []
        variants_list = kwargs.get("buggy_variants") or []
        n = len(completions)

        # Normalize completions: TRL sometimes passes list[str], sometimes list[list[msg]]
        def _to_text(c) -> str:
            if isinstance(c, str):
                return c
            if isinstance(c, list) and c and isinstance(c[0], dict):
                return "\n".join(m.get("content", "") for m in c)
            return str(c)

        texts = [_to_text(c) for c in completions]

        results: list[RewardBreakdown] = [None] * n  # type: ignore[list-item]

        def _score_one(i: int) -> None:
            ref = refs[i] if i < len(refs) else ""
            vars_ = variants_list[i] if i < len(variants_list) else []
            try:
                rb = score(texts[i], ref, list(vars_), reward_cfg)
            except Exception as e:
                rb = RewardBreakdown(reason=f"scorer_exc:{type(e).__name__}")
            results[i] = rb

        # limit outer parallelism since scorer already parallelizes variants internally
        outer_workers = max(1, min(4, n))
        with ThreadPoolExecutor(max_workers=outer_workers) as ex:
            list(ex.map(_score_one, range(n)))

        buffer.push(results)
        return [rb.reward for rb in results]

    return _reward
