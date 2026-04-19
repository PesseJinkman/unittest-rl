"""Eval base vs RLVR on held-out problems and print a markdown report."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.eval.run_eval import aggregate, evaluate, render_markdown  # noqa: E402
from src.utils.io import load_yaml, save_json  # noqa: E402
from src.utils.logging import get_logger  # noqa: E402


log = get_logger("eval-cli")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/train.yaml")
    ap.add_argument("--rlvr-adapter", default=None,
                    help="Path to RLVR adapter (defaults to <grpo.output_dir>/final)")
    ap.add_argument("--sft-adapter", default=None,
                    help="Optional SFT-warmup adapter to use as 'base' baseline")
    ap.add_argument("--eval-dir", default=None)
    ap.add_argument("--report-dir", default="reports")
    args = ap.parse_args()

    cfg = load_yaml(args.config)
    eval_dir = Path(args.eval_dir or cfg["data"]["eval_dir"])
    rlvr_adapter = args.rlvr_adapter or str(Path(cfg["grpo"]["output_dir"]) / "final")

    ts = time.strftime("%Y%m%d-%H%M%S")
    report_dir = Path(args.report_dir)
    report_dir.mkdir(parents=True, exist_ok=True)

    base = evaluate(cfg, adapter_dir=args.sft_adapter, label="base", eval_dir=eval_dir)
    rlvr = evaluate(cfg, adapter_dir=rlvr_adapter, label="rlvr", eval_dir=eval_dir)

    base_agg = aggregate(base["rows"])
    rlvr_agg = aggregate(rlvr["rows"])

    out_json = report_dir / f"eval_{ts}.json"
    save_json(out_json, {"base": {"rows": base["rows"], "agg": base_agg},
                         "rlvr": {"rows": rlvr["rows"], "agg": rlvr_agg}})
    out_md = report_dir / f"eval_{ts}.md"
    render_markdown(base_agg, rlvr_agg, out_md)
    log.info("Wrote %s and %s", out_md, out_json)
    print(out_md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
