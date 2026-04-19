"""GRPO training entrypoint with curriculum learning and LoRA adapters."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import torch
from peft import LoraConfig, PeftModel, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainerCallback
from trl import GRPOConfig, GRPOTrainer

from ..reward.scorer import RewardConfig
from ..utils.logging import CSVLogger, get_logger
from ..utils.seeding import set_global_seed
from .curriculum import CurriculumState
from .dataset import load_problems
from .rollout import CurriculumIterableDataset, TrainBuffer, make_reward_fn


log = get_logger("grpo")


def _load_model_and_tokenizer(cfg: dict[str, Any]):
    m = cfg["model"]
    name = m["name"]
    dtype_str = m.get("dtype", "bfloat16")
    dtype = {"bfloat16": torch.bfloat16, "float16": torch.float16, "float32": torch.float32}[dtype_str]
    trust = bool(m.get("trust_remote_code", True))
    attn_impl = m.get("attn_implementation", "sdpa")

    tok = AutoTokenizer.from_pretrained(name, trust_remote_code=trust)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token

    model_kwargs: dict[str, Any] = dict(
        torch_dtype=dtype,
        trust_remote_code=trust,
        attn_implementation=attn_impl,
    )
    if m.get("qlora"):
        from transformers import BitsAndBytesConfig
        model_kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=dtype,
        )
    model = AutoModelForCausalLM.from_pretrained(name, **model_kwargs)
    model.config.use_cache = False
    return model, tok


def _apply_lora(model, lora_cfg: dict[str, Any]):
    lc = LoraConfig(
        r=int(lora_cfg["r"]),
        lora_alpha=int(lora_cfg["alpha"]),
        lora_dropout=float(lora_cfg["dropout"]),
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=list(lora_cfg["target_modules"]),
    )
    return get_peft_model(model, lc)


class CurriculumCallback(TrainerCallback):
    """Drain reward buffer after each optim step, update curriculum, log metrics."""

    def __init__(
        self,
        curriculum: CurriculumState,
        buffer: TrainBuffer,
        csv_logger: CSVLogger,
    ):
        self.curriculum = curriculum
        self.buffer = buffer
        self.csv = csv_logger

    def on_step_end(self, args, state, control, **kwargs):
        rbs = self.buffer.drain()
        if not rbs:
            return control
        rewards = [rb.reward for rb in rbs]
        self.curriculum.record_rewards(rewards)
        advanced = self.curriculum.maybe_advance()

        n = max(1, len(rbs))
        row = {
            "global_step": state.global_step,
            "level": self.curriculum.level,
            "steps_on_level": self.curriculum.steps_on_level,
            "batch_size": len(rbs),
            "reward_mean": sum(rewards) / n,
            "reward_max": max(rewards),
            "reward_min": min(rewards),
            "pass_ref_rate": sum(rb.pass_ref for rb in rbs) / n,
            "bug_catch_rate": sum(rb.bug_catch for rb in rbs) / n,
            "branch_cov": sum(rb.branch_cov for rb in rbs) / n,
            "parse_ok_rate": sum(1 for rb in rbs if rb.parse_ok) / n,
            "timeouts": sum(rb.timeouts for rb in rbs),
            "rolling_mean": self.curriculum.snapshot()["rolling_mean"],
            "window_hits": self.curriculum.window_hits,
            "advanced": int(advanced),
        }
        self.csv.log(row)
        log.info(
            "step=%d level=%s sol=%d rew=%.3f pass=%.2f bugs=%.2f cov=%.2f roll=%.3f wh=%d%s",
            state.global_step, row["level"], row["steps_on_level"],
            row["reward_mean"], row["pass_ref_rate"], row["bug_catch_rate"],
            row["branch_cov"], row["rolling_mean"], row["window_hits"],
            " ADVANCED" if advanced else "",
        )
        return control


def train_grpo(cfg: dict[str, Any]) -> None:
    set_global_seed(int(cfg.get("seed", 42)))

    # 1. model + tokenizer
    model, tok = _load_model_and_tokenizer(cfg)

    # 2. load SFT adapter if available, otherwise init fresh LoRA
    sft_dir = Path(cfg.get("sft_warmup", {}).get("output_dir", "outputs/sft")) / "final"
    if sft_dir.exists():
        log.info("Loading SFT adapter from %s", sft_dir)
        model = PeftModel.from_pretrained(model, str(sft_dir), is_trainable=True)
    else:
        log.info("No SFT adapter found at %s, initialising fresh LoRA", sft_dir)
        model = _apply_lora(model, cfg["lora"])
    model.print_trainable_parameters()

    # 3. load problems + curriculum
    problems_root = Path(cfg["data"]["problems_dir"])
    problems_by_level = load_problems(problems_root, levels=cfg["curriculum"]["levels"])
    total = sum(len(v) for v in problems_by_level.values())
    if total == 0:
        raise RuntimeError(f"No problems found under {problems_root}")
    for lv, probs in problems_by_level.items():
        log.info("Level %s: %d problems", lv, len(probs))

    curriculum = CurriculumState(
        levels=list(cfg["curriculum"]["levels"]),
        eval_window_steps=int(cfg["curriculum"]["eval_window_steps"]),
        rolling_n=int(cfg["curriculum"]["rolling_n"]),
        advance_threshold=float(cfg["curriculum"]["advance_threshold"]),
        consecutive_windows=int(cfg["curriculum"]["consecutive_windows"]),
        force_advance_cap=cfg["curriculum"].get("force_advance_cap"),
    )

    # 4. dataset
    train_ds = CurriculumIterableDataset(
        problems_by_level=problems_by_level,
        curriculum=curriculum,
        tokenizer=tok,
        seed=int(cfg.get("seed", 42)),
        max_prompt_tokens=int(cfg["grpo"].get("max_prompt_length", 1024)),
    )

    # 5. reward fn + buffer
    rcfg = cfg["reward"]
    reward_config = RewardConfig(
        w_pass=float(rcfg["w_pass"]),
        w_bugs=float(rcfg["w_bugs"]),
        w_cov=float(rcfg["w_cov"]),
        min_tests=int(rcfg["min_tests"]),
        pytest_timeout_s=float(rcfg["pytest_timeout_s"]),
        coverage_timeout_s=float(rcfg["coverage_timeout_s"]),
        banned_imports=list(rcfg["banned_imports"]),
        penalty_timeout=float(rcfg["penalty_timeout"]),
        penalty_banned_import=float(rcfg["penalty_banned_import"]),
        parallel_workers=int(rcfg["parallel_workers"]),
    )
    buffer = TrainBuffer()
    reward_fn = make_reward_fn(reward_config, buffer)

    # 6. GRPO config
    g = cfg["grpo"]
    grpo_args = GRPOConfig(
        output_dir=g["output_dir"],
        learning_rate=float(g["learning_rate"]),
        per_device_train_batch_size=int(g["per_device_train_batch_size"]),
        gradient_accumulation_steps=int(g["gradient_accumulation_steps"]),
        num_generations=int(g["num_generations"]),
        generation_batch_size=int(g["num_generations"]),
        max_completion_length=int(g["max_completion_length"]),
        temperature=float(g["temperature"]),
        top_p=float(g["top_p"]),
        beta=float(g["beta"]),
        logging_steps=int(g["logging_steps"]),
        save_steps=int(g["save_steps"]),
        max_steps=int(g["max_steps"]),
        num_train_epochs=float(g.get("num_train_epochs", 1)),
        bf16=(cfg["model"]["dtype"] == "bfloat16"),
        gradient_checkpointing=True,
        report_to=["wandb"] if cfg["logging"].get("wandb") else [],
        remove_unused_columns=False,
        seed=int(cfg.get("seed", 42)),
    )

    # 7. CSV logger + callback
    csv_logger = CSVLogger(cfg["logging"]["csv_path"])
    cb = CurriculumCallback(curriculum, buffer, csv_logger)

    def _collate(features):
        # Put a tensor first so accelerate's find_batch_size returns immediately
        # without recursing into the string fields and raising TypeError.
        return {
            "_n": torch.arange(len(features)),
            "prompt": [f["prompt"] for f in features],
            "reference_code": [f["reference_code"] for f in features],
            "buggy_variants": [f["buggy_variants"] for f in features],
            "slug": [f["slug"] for f in features],
            "level": [f["level"] for f in features],
        }

    # 8. Trainer
    trainer = GRPOTrainer(
        model=model,
        processing_class=tok,
        reward_funcs=[reward_fn],
        args=grpo_args,
        train_dataset=train_ds,
        data_collator=_collate,
        callbacks=[cb],
    )

    trainer.train()

    # Save adapter
    out = Path(g["output_dir"]) / "final"
    out.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(out))
    tok.save_pretrained(str(out))

    # Save curriculum events
    import json
    with open(out / "curriculum_events.json", "w", encoding="utf-8") as f:
        json.dump(curriculum.events, f, indent=2)
    log.info("Saved RLVR adapter to %s", out)
