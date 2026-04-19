"""Train entrypoint: `--stage sft` for warmup, `--stage grpo` for RL."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.utils.io import load_yaml  # noqa: E402
from src.utils.logging import get_logger  # noqa: E402


log = get_logger("train")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/train.yaml")
    ap.add_argument("--stage", choices=["sft", "grpo"], required=True)
    args = ap.parse_args()

    load_dotenv()
    cfg = load_yaml(args.config)

    if args.stage == "sft":
        from src.rl.sft_train import train_sft
        train_sft(cfg)
    else:
        from src.rl.grpo_train import train_grpo
        train_grpo(cfg)


if __name__ == "__main__":
    main()
