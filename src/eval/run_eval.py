"""Evaluate base vs RLVR adapter on held-out problems."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from ..reward.scorer import RewardConfig, score
from ..rl.dataset import load_problems
from ..rl.prompts import build_messages
from ..utils.io import save_json
from ..utils.logging import get_logger
from .model_io import generate_one, load_policy


log = get_logger("eval")


def _reward_config_from_cfg(cfg: dict[str, Any]) -> RewardConfig:
    r = cfg["reward"]
    return RewardConfig(
        w_pass=float(r["w_pass"]),
        w_bugs=float(r["w_bugs"]),
        w_cov=float(r["w_cov"]),
        min_tests=int(r["min_tests"]),
        pytest_timeout_s=float(r["pytest_timeout_s"]),
        coverage_timeout_s=float(r["coverage_timeout_s"]),
        banned_imports=list(r["banned_imports"]),
        penalty_timeout=float(r["penalty_timeout"]),
        penalty_banned_import=float(r["penalty_banned_import"]),
        parallel_workers=int(r["parallel_workers"]),
    )


def evaluate(
    cfg: dict[str, Any],
    adapter_dir: str | None,
    label: str,
    eval_dir: Path,
    *,
    max_new_tokens: int = 768,
    temperature: float = 0.0,
) -> dict[str, Any]:
    log.info("Loading policy: %s (adapter=%s)", cfg["model"]["name"], adapter_dir)
    model, tok = load_policy(
        cfg["model"]["name"],
        adapter_dir=adapter_dir,
        dtype=cfg["model"].get("dtype", "bfloat16"),
        attn_implementation=cfg["model"].get("attn_implementation", "sdpa"),
    )
    problems_by_level = load_problems(eval_dir, levels=cfg["curriculum"]["levels"])
    rcfg = _reward_config_from_cfg(cfg)

    rows = []
    for level, probs in problems_by_level.items():
        for p in probs:
            messages = build_messages(p.reference_code, p.spec)
            t0 = time.time()
            completion = generate_one(
                model, tok, messages,
                max_new_tokens=max_new_tokens, temperature=temperature,
            )
            gen_s = time.time() - t0
            rb = score(completion, p.reference_code, p.variant_codes, rcfg)
            rows.append({
                "label": label, "level": level, "slug": p.slug,
                "reward": rb.reward, "pass_ref": rb.pass_ref,
                "bug_catch": rb.bug_catch, "branch_cov": rb.branch_cov,
                "n_tests": rb.n_tests, "n_variants": rb.n_variants,
                "n_variants_caught": rb.n_variants_caught,
                "parse_ok": int(rb.parse_ok), "reason": rb.reason,
                "gen_s": round(gen_s, 2),
            })
            log.info("[%s] %s/%s rew=%.2f pass=%.0f bugs=%.2f cov=%.2f%s",
                     label, level, p.slug, rb.reward, rb.pass_ref, rb.bug_catch, rb.branch_cov,
                     f" ({rb.reason})" if rb.reason else "")
    return {"label": label, "rows": rows}


def aggregate(rows: list[dict]) -> dict[str, Any]:
    by_level: dict[str, list[dict]] = {}
    for r in rows:
        by_level.setdefault(r["level"], []).append(r)
    out: dict[str, Any] = {"per_level": {}}
    def _mean(xs):
        return (sum(xs) / len(xs)) if xs else 0.0
    all_rows = rows
    out["overall"] = {
        "n": len(all_rows),
        "reward": _mean([r["reward"] for r in all_rows]),
        "pass_ref": _mean([r["pass_ref"] for r in all_rows]),
        "bug_catch": _mean([r["bug_catch"] for r in all_rows]),
        "branch_cov": _mean([r["branch_cov"] for r in all_rows]),
    }
    for lv, rs in by_level.items():
        out["per_level"][lv] = {
            "n": len(rs),
            "reward": _mean([r["reward"] for r in rs]),
            "pass_ref": _mean([r["pass_ref"] for r in rs]),
            "bug_catch": _mean([r["bug_catch"] for r in rs]),
            "branch_cov": _mean([r["branch_cov"] for r in rs]),
        }
    return out


def render_markdown(base_agg: dict, rlvr_agg: dict, out_md: Path) -> None:
    def _row(label, d):
        return (f"| {label} | {d['n']} | {d['reward']:.3f} | "
                f"{100*d['pass_ref']:.1f}% | {100*d['bug_catch']:.1f}% | {100*d['branch_cov']:.1f}% |")

    lines = []
    lines.append("# Held-out evaluation: base vs RLVR\n")
    lines.append("## Overall")
    lines.append("")
    lines.append("| Model | N | Reward | Pass@ref | Bug catch | Branch cov |")
    lines.append("|---|---|---|---|---|---|")
    lines.append(_row("base", base_agg["overall"]))
    lines.append(_row("rlvr", rlvr_agg["overall"]))
    lines.append("")
    levels = sorted(set(base_agg["per_level"]) | set(rlvr_agg["per_level"]))
    for lv in levels:
        lines.append(f"## {lv}")
        lines.append("")
        lines.append("| Model | N | Reward | Pass@ref | Bug catch | Branch cov |")
        lines.append("|---|---|---|---|---|---|")
        if lv in base_agg["per_level"]:
            lines.append(_row("base", base_agg["per_level"][lv]))
        if lv in rlvr_agg["per_level"]:
            lines.append(_row("rlvr", rlvr_agg["per_level"][lv]))
        lines.append("")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text("\n".join(lines), encoding="utf-8")
