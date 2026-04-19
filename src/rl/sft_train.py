"""Tiny SFT warmup on gold tests to lift initial pass rate above zero before GRPO."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTConfig, SFTTrainer

from ..utils.io import read_jsonl
from ..utils.logging import get_logger
from ..utils.seeding import set_global_seed
from .prompts import build_messages


log = get_logger("sft")


def _load_model_and_tokenizer(cfg: dict[str, Any]):
    m = cfg["model"]
    dtype = {"bfloat16": torch.bfloat16, "float16": torch.float16, "float32": torch.float32}[m.get("dtype", "bfloat16")]
    tok = AutoTokenizer.from_pretrained(m["name"], trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    mk: dict[str, Any] = dict(torch_dtype=dtype, trust_remote_code=True,
                              attn_implementation=m.get("attn_implementation", "sdpa"))
    if m.get("qlora"):
        from transformers import BitsAndBytesConfig
        mk["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=dtype,
        )
    model = AutoModelForCausalLM.from_pretrained(m["name"], **mk)
    model.config.use_cache = False
    return model, tok


def _build_dataset(jsonl_path: Path, tok) -> Dataset:
    """Expect each row: {'reference_code', 'spec', 'test_code'}."""
    rows = read_jsonl(jsonl_path)
    texts = []
    for r in rows:
        messages = build_messages(r["reference_code"], r["spec"])
        # Append assistant turn with the gold pytest file wrapped in a fenced block
        gold = r["test_code"].strip()
        messages.append({"role": "assistant", "content": f"```python\n{gold}\n```"})
        text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        texts.append({"text": text})
    return Dataset.from_list(texts)


def train_sft(cfg: dict[str, Any]) -> None:
    set_global_seed(int(cfg.get("seed", 42)))
    sw = cfg["sft_warmup"]
    if not sw.get("enabled", True):
        log.info("SFT warmup disabled; skipping.")
        return

    gold_path = Path(sw["gold_path"])
    if not gold_path.exists():
        log.warning("Gold tests not found at %s; skipping SFT warmup.", gold_path)
        return

    model, tok = _load_model_and_tokenizer(cfg)
    lc = LoraConfig(
        r=int(cfg["lora"]["r"]),
        lora_alpha=int(cfg["lora"]["alpha"]),
        lora_dropout=float(cfg["lora"]["dropout"]),
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=list(cfg["lora"]["target_modules"]),
    )
    model = get_peft_model(model, lc)
    model.print_trainable_parameters()

    ds = _build_dataset(gold_path, tok)
    log.info("SFT dataset size: %d", len(ds))

    args = SFTConfig(
        output_dir=sw["output_dir"],
        num_train_epochs=float(sw.get("epochs", 1)),
        learning_rate=float(sw.get("lr", 1e-4)),
        per_device_train_batch_size=int(sw.get("per_device_train_batch_size", 2)),
        gradient_accumulation_steps=int(sw.get("gradient_accumulation_steps", 4)),
        logging_steps=5,
        save_steps=100,
        bf16=(cfg["model"]["dtype"] == "bfloat16"),
        gradient_checkpointing=True,
        max_seq_length=2048,
        packing=False,
        report_to=[],
        dataset_text_field="text",
        remove_unused_columns=True,
        seed=int(cfg.get("seed", 42)),
    )
    trainer = SFTTrainer(
        model=model,
        processing_class=tok,
        args=args,
        train_dataset=ds,
    )
    trainer.train()

    out = Path(sw["output_dir"]) / "final"
    out.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(out))
    tok.save_pretrained(str(out))
    log.info("Saved SFT adapter to %s", out)
