"""Generate a pytest test file for an arbitrary Python module."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.eval.model_io import generate_one, load_policy  # noqa: E402
from src.reward.parse import extract_python_block  # noqa: E402
from src.rl.prompts import build_messages  # noqa: E402
from src.sandbox.runner import run_pytest  # noqa: E402
from src.utils.io import load_yaml, write_text  # noqa: E402
from src.utils.logging import get_logger  # noqa: E402


log = get_logger("generate")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("module", help="path to Python module to test")
    ap.add_argument("--config", default="configs/train.yaml")
    ap.add_argument("--model", choices=["base", "rlvr", "sft"], default="rlvr")
    ap.add_argument("--adapter", default=None, help="override adapter dir")
    ap.add_argument("--out", default=None, help="output test file path")
    ap.add_argument("--spec", default="", help="optional spec text")
    ap.add_argument("--max-new-tokens", type=int, default=768)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--run", action="store_true", help="execute pytest on the result")
    args = ap.parse_args()

    cfg = load_yaml(args.config)
    mod_path = Path(args.module)
    code = mod_path.read_text(encoding="utf-8")

    if args.adapter:
        adapter = args.adapter
    elif args.model == "base":
        adapter = None
    elif args.model == "sft":
        adapter = str(Path(cfg["sft_warmup"]["output_dir"]) / "final")
    else:
        adapter = str(Path(cfg["grpo"]["output_dir"]) / "final")

    model, tok = load_policy(
        cfg["model"]["name"],
        adapter_dir=adapter,
        dtype=cfg["model"].get("dtype", "bfloat16"),
        attn_implementation=cfg["model"].get("attn_implementation", "sdpa"),
    )
    spec = args.spec or f"Module at {mod_path.name}. Infer behavior from the code."
    messages = build_messages(code, spec)
    raw = generate_one(model, tok, messages,
                       max_new_tokens=args.max_new_tokens, temperature=args.temperature)
    test_code = extract_python_block(raw)
    if not test_code.strip():
        log.error("Model produced no code.")
        sys.exit(2)

    out_path = Path(args.out) if args.out else mod_path.with_name(f"test_{mod_path.stem}.py")
    write_text(out_path, test_code.rstrip() + "\n")
    log.info("Wrote %s (%d chars)", out_path, len(test_code))

    if args.run:
        # The prompt tells the model to import from `target_module`, so execute
        # with that canonical name regardless of the user-facing filename.
        r = run_pytest(module_code=code, test_code=test_code,
                       module_filename="target_module.py",
                       test_filename="test_target.py",
                       timeout_s=20.0)
        print("\n--- pytest ---")
        print(r.stdout_tail)
        print(f"passed={r.passed} failed={r.failed} errors={r.errors} timeout={r.timeout}")


if __name__ == "__main__":
    main()
