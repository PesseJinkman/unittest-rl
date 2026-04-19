"""Validate raw problems, write accepted ones to data/problems/{L1,L2,L3}/<slug>/,
split into train/eval, and optionally generate gold tests for SFT warmup."""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_gen.openai_client import make_client  # noqa: E402
from src.data_gen.synthesize import synthesize_gold_test  # noqa: E402
from src.data_gen.validate import validate_problem  # noqa: E402
from src.utils.io import append_jsonl, load_json, load_yaml, save_json, write_text  # noqa: E402
from src.utils.logging import get_logger  # noqa: E402


log = get_logger("validate")


def _write_problem_dir(out_root: Path, problem: dict, accepted_variants: list[dict]) -> Path:
    slug = problem["slug"]
    level = problem["level"]
    pdir = out_root / level / slug
    if pdir.exists():
        # uniqueify
        pdir = out_root / level / f"{slug}_{int(time.time()*1000)%10000}"
    pdir.mkdir(parents=True, exist_ok=True)
    write_text(pdir / "reference.py", problem["reference_code"].rstrip() + "\n")
    write_text(pdir / "spec.md", problem["spec"].strip() + "\n")
    (pdir / "buggy").mkdir(exist_ok=True)
    for v in accepted_variants:
        write_text(pdir / "buggy" / f"{v['id']}.py", v["code"].rstrip() + "\n")
    meta = {
        "slug": slug,
        "level": level,
        "entrypoints": problem["entrypoints"],
        "sample_inputs": problem.get("sample_inputs", []),
        "buggy_variants": [{"id": v["id"], "description": v.get("description", "")}
                           for v in accepted_variants],
    }
    save_json(pdir / "meta.json", meta)
    return pdir


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/gen_dataset.yaml")
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data/problems")
    ap.add_argument("--eval-out", default="data/eval")
    ap.add_argument("--no-gold", action="store_true", help="Skip gold test generation")
    args = ap.parse_args()

    load_dotenv()
    cfg = load_yaml(args.config)
    raw_root = Path(args.raw)
    out_root = Path(args.out)
    eval_root = Path(args.eval_out)

    banned = list(cfg["validation"]["banned_imports"])
    t_out = float(cfg["validation"]["sample_input_timeout_s"])

    # gather candidates
    candidates: list[Path] = []
    for level_dir in sorted(raw_root.iterdir()) if raw_root.exists() else []:
        if level_dir.is_dir():
            candidates.extend(sorted(level_dir.glob("*.json")))
    log.info("Found %d raw candidates", len(candidates))

    accepted_by_level: dict[str, list[tuple[dict, list[dict]]]] = {}
    rejected = 0

    def _work(path: Path):
        try:
            problem = load_json(path)
        except Exception as e:
            return (path, None, f"load_err:{e}")
        res = validate_problem(problem, banned_imports=banned, sample_input_timeout_s=t_out)
        if not res.ok:
            return (path, None, res.reason)
        return (path, (problem, res.accepted_variants or []), "ok")

    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(_work, p) for p in candidates]
        for i, f in enumerate(as_completed(futs), 1):
            path, payload, reason = f.result()
            if payload is None:
                rejected += 1
                if i % 20 == 0 or rejected <= 10:
                    log.info("[%d/%d] REJECT %s : %s", i, len(candidates), path.name, reason)
                continue
            problem, variants = payload
            accepted_by_level.setdefault(problem["level"], []).append((problem, variants))

    # cap to target per level, split train/eval, write files
    rng = random.Random(0)
    train_frac = float(cfg["splits"]["train_frac"])
    gold_rows_path = Path(cfg["gold_tests"]["output_path"])

    for level, items in accepted_by_level.items():
        target = int(cfg["counts"][level]["target"])
        rng.shuffle(items)
        items = items[:target]
        n_eval = max(2, int(round(len(items) * (1 - train_frac))))
        eval_items = items[:n_eval]
        train_items = items[n_eval:]

        log.info("Level %s: accepted=%d kept=%d train=%d eval=%d",
                 level, len([x for x in accepted_by_level[level]]),
                 len(items), len(train_items), len(eval_items))

        for prob, vars_ in train_items:
            _write_problem_dir(out_root, prob, vars_)
        for prob, vars_ in eval_items:
            _write_problem_dir(eval_root, prob, vars_)

    log.info("Rejected %d / %d", rejected, len(candidates))

    # optional: gold tests for SFT warmup over training problems
    if not args.no_gold and cfg.get("gold_tests", {}).get("enabled", True):
        client = make_client()
        model = cfg["openai"]["model"]
        gold_rows_path.unlink(missing_ok=True)
        count = 0
        for level_dir in sorted(out_root.iterdir()):
            if not level_dir.is_dir():
                continue
            for pdir in sorted(level_dir.iterdir()):
                meta = load_json(pdir / "meta.json")
                ref = (pdir / "reference.py").read_text(encoding="utf-8")
                spec = (pdir / "spec.md").read_text(encoding="utf-8")
                try:
                    test_code = synthesize_gold_test(client, model, ref, spec)
                except Exception as e:
                    log.warning("gold-fail %s: %s", meta["slug"], e)
                    continue
                append_jsonl(gold_rows_path, {
                    "slug": meta["slug"],
                    "level": meta["level"],
                    "reference_code": ref,
                    "spec": spec,
                    "test_code": test_code,
                })
                count += 1
                if count % 10 == 0:
                    log.info("gold[%d] %s/%s", count, meta["level"], meta["slug"])
        log.info("Wrote %d gold test rows -> %s", count, gold_rows_path)


if __name__ == "__main__":
    main()
