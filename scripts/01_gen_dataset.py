"""Generate raw problems via OpenAI. Writes one JSON file per candidate to data/raw/."""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_gen.openai_client import make_client  # noqa: E402
from src.data_gen.synthesize import SynthRequest, synthesize_one  # noqa: E402
from src.utils.io import load_yaml, save_json  # noqa: E402
from src.utils.logging import get_logger  # noqa: E402


log = get_logger("gen")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/gen_dataset.yaml")
    ap.add_argument("--out", default="data/raw")
    args = ap.parse_args()

    load_dotenv()
    cfg = load_yaml(args.config)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    client = make_client()
    model = cfg["openai"]["model"]
    conc = int(cfg["openai"].get("concurrency", 4))

    jobs: list[SynthRequest] = []
    for level, c in cfg["counts"].items():
        n = int(round(c["target"] * float(c.get("overgen_multiplier", 1.5))))
        for _ in range(n):
            jobs.append(SynthRequest(
                level=level,
                n_bugs_min=int(c["buggy_variants_min"]),
                n_bugs_max=int(c["buggy_variants_max"]),
            ))
    log.info("Total synthesis jobs: %d (model=%s, concurrency=%d)", len(jobs), model, conc)

    def _work(req: SynthRequest):
        try:
            p = synthesize_one(
                client, model, req,
                temperature=float(cfg["openai"].get("temperature", 1.0)),
                max_retries=int(cfg["openai"].get("max_retries", 3)),
                request_timeout_s=float(cfg["openai"].get("request_timeout_s", 120)),
            )
            slug = p.data.get("slug") or f"gen_{uuid.uuid4().hex[:8]}"
            out_path = out_dir / req.level / f"{slug}.json"
            # avoid collision
            if out_path.exists():
                out_path = out_dir / req.level / f"{slug}_{uuid.uuid4().hex[:4]}.json"
            save_json(out_path, p.data)
            return (req.level, "ok", str(out_path))
        except Exception as e:
            return (req.level, f"err:{type(e).__name__}:{e}", None)

    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=conc) as ex:
        futs = [ex.submit(_work, j) for j in jobs]
        for f in as_completed(futs):
            lv, status, path = f.result()
            done += 1
            if done % 10 == 0 or status != "ok":
                log.info("[%d/%d] %s %s %s", done, len(jobs), lv, status, path or "")
    log.info("Generated %d candidates in %.1fs -> %s", len(jobs), time.time() - t0, out_dir)


if __name__ == "__main__":
    main()
