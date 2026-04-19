"""Plot training curves from outputs/train_log.csv."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import matplotlib.pyplot as plt


LEVEL_COLORS = {"L1": "#4C9AFF", "L2": "#FFAB00", "L3": "#FF5630"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="outputs/train_log.csv")
    ap.add_argument("--out", default="reports/training_curves.png")
    args = ap.parse_args()

    path = Path(args.csv)
    if not path.exists():
        print(f"No CSV at {path}", file=sys.stderr)
        sys.exit(1)

    steps, reward, pass_r, bugs, cov, levels = [], [], [], [], [], []
    with open(path, "r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                steps.append(int(row["global_step"]))
                reward.append(float(row.get("reward_mean", 0)))
                pass_r.append(float(row.get("pass_ref_rate", 0)))
                bugs.append(float(row.get("bug_catch_rate", 0)))
                cov.append(float(row.get("branch_cov", 0)))
                levels.append(row.get("level", ""))
            except Exception:
                continue

    if not steps:
        print("No rows found", file=sys.stderr)
        sys.exit(1)

    # find level transitions
    boundaries = []
    for i in range(1, len(levels)):
        if levels[i] != levels[i - 1]:
            boundaries.append((steps[i], levels[i - 1], levels[i]))

    fig, axes = plt.subplots(2, 2, figsize=(12, 7), sharex=True)
    for ax, ys, title in zip(
        axes.flat,
        [reward, pass_r, bugs, cov],
        ["reward (mean)", "pass_ref rate", "bug catch rate", "branch coverage"],
    ):
        ax.plot(steps, ys, linewidth=1)
        ax.set_title(title)
        ax.set_ylim(0, 1.05)
        ax.grid(True, alpha=0.3)
        for bstep, prev, nxt in boundaries:
            ax.axvline(bstep, color="gray", linestyle="--", linewidth=1)
            ax.text(bstep, 1.02, f"{prev}->{nxt}", rotation=90, va="bottom",
                    fontsize=8, color="gray")
    for ax in axes[-1]:
        ax.set_xlabel("optimizer step")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=140)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
