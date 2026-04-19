# unittest-rl

RLVR pipeline that fine-tunes **Qwen3-1.7B** with **TRL + GRPO + LoRA** to generate
high-quality **pytest** test files for Python code, using curriculum learning
across 3 difficulty levels. Reward = pytest passability + hidden-bug catch rate +
branch coverage, computed in a subprocess sandbox.

## Quickstart

```bash
# 1. Install
python -m venv .venv
. .venv/Scripts/activate     # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env         # fill in OPENAI_API_KEY

# 2. Generate dataset (OpenAI)
python scripts/01_gen_dataset.py --config configs/gen_dataset.yaml

# 3. Validate + split
python scripts/02_validate_dataset.py --config configs/gen_dataset.yaml

# 4. (Optional but recommended) SFT warmup on gold tests
python scripts/03_train.py --config configs/train.yaml --stage sft

# 5. GRPO training with curriculum
python scripts/03_train.py --config configs/train.yaml --stage grpo

# 6. Held-out eval: base vs rlvr
python scripts/04_eval.py --config configs/train.yaml

# 7. Generate a test file for any Python module
python scripts/05_generate.py --model rlvr path/to/module.py --out tests/test_module.py --run
```

## Project layout

See `configs/train.yaml` and `configs/gen_dataset.yaml` for knobs.

```
src/
  data_gen/        OpenAI problem synthesis + validation
  sandbox/         pytest subprocess runner + branch coverage
  reward/          code parser + reward scorer
  rl/              prompts, curriculum state machine, GRPO trainer
  eval/            held-out eval + single-file generation CLI
  utils/           io, logging, seeding
scripts/           thin CLI entrypoints
data/problems/     L1/ L2/ L3/ validated problems
data/eval/         held-out split
```

## Reward formula

```
R = 0.40 * pass_ref
  + 0.40 * pass_ref * bug_catch_rate
  + 0.20 * pass_ref * branch_coverage
```

`pass_ref` gating kills the `assert False` exploit. Timeouts and banned imports
incur explicit penalties.

## Curriculum

Rolling mean reward ≥ 0.70 over the last 60 rollouts for 3 consecutive
20-step windows → advance to the next level. Optional hard cap in `train.yaml`.
