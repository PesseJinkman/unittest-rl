"""Curriculum controller: rolling mean reward threshold advancement."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class CurriculumState:
    levels: list[str]
    eval_window_steps: int = 20
    rolling_n: int = 60
    advance_threshold: float = 0.70
    consecutive_windows: int = 3
    force_advance_cap: int | None = None

    level_idx: int = 0
    step: int = 0
    steps_on_level: int = 0
    rolling_rewards: deque = field(default_factory=lambda: deque(maxlen=60))
    window_hits: int = 0
    events: list[dict] = field(default_factory=list)

    def __post_init__(self):
        self.rolling_rewards = deque(maxlen=self.rolling_n)

    @property
    def level(self) -> str:
        return self.levels[self.level_idx]

    @property
    def at_final_level(self) -> bool:
        return self.level_idx >= len(self.levels) - 1

    def record_rewards(self, rewards: Iterable[float]) -> None:
        for r in rewards:
            self.rolling_rewards.append(float(r))
        self.step += 1
        self.steps_on_level += 1

    def maybe_advance(self) -> bool:
        """Called after each optimizer step; returns True if we just advanced."""
        if self.at_final_level:
            return False
        # evaluate at window boundaries
        if self.step == 0 or self.step % self.eval_window_steps != 0:
            # still allow force-advance check
            if self.force_advance_cap and self.steps_on_level >= self.force_advance_cap:
                return self._advance(reason="force_cap")
            return False
        if not self.rolling_rewards:
            return False
        mean = sum(self.rolling_rewards) / len(self.rolling_rewards)
        if mean >= self.advance_threshold:
            self.window_hits += 1
        else:
            self.window_hits = 0
        if self.window_hits >= self.consecutive_windows:
            return self._advance(reason=f"threshold(mean={mean:.3f})")
        if self.force_advance_cap and self.steps_on_level >= self.force_advance_cap:
            return self._advance(reason="force_cap")
        return False

    def _advance(self, reason: str) -> bool:
        if self.at_final_level:
            return False
        prev = self.level
        self.level_idx += 1
        self.steps_on_level = 0
        self.window_hits = 0
        self.rolling_rewards.clear()
        self.events.append({
            "step": self.step,
            "from": prev,
            "to": self.level,
            "reason": reason,
        })
        return True

    def snapshot(self) -> dict:
        mean = (sum(self.rolling_rewards) / len(self.rolling_rewards)) if self.rolling_rewards else 0.0
        return {
            "step": self.step,
            "level": self.level,
            "steps_on_level": self.steps_on_level,
            "rolling_mean": mean,
            "rolling_n": len(self.rolling_rewards),
            "window_hits": self.window_hits,
        }
