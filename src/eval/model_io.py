"""Shared model loading helpers for eval and generate scripts."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_policy(
    base_name: str,
    adapter_dir: str | None = None,
    *,
    dtype: str = "bfloat16",
    attn_implementation: str = "sdpa",
    device_map: str = "auto",
):
    """Load base model, optionally stacking a PEFT adapter on top."""
    torch_dtype = {"bfloat16": torch.bfloat16, "float16": torch.float16,
                   "float32": torch.float32}[dtype]
    tok = AutoTokenizer.from_pretrained(base_name, trust_remote_code=True)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        base_name,
        torch_dtype=torch_dtype,
        trust_remote_code=True,
        attn_implementation=attn_implementation,
        device_map=device_map,
    )
    if adapter_dir:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, adapter_dir)
    model.eval()
    return model, tok


@torch.inference_mode()
def generate_one(
    model,
    tok,
    messages: list[dict],
    *,
    max_new_tokens: int = 768,
    temperature: float = 0.0,
    top_p: float = 1.0,
) -> str:
    prompt_text = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    enc = tok(prompt_text, return_tensors="pt").to(model.device)
    gen_kwargs = dict(
        max_new_tokens=max_new_tokens,
        pad_token_id=tok.pad_token_id,
        eos_token_id=tok.eos_token_id,
    )
    if temperature and temperature > 0:
        gen_kwargs.update(do_sample=True, temperature=temperature, top_p=top_p)
    else:
        gen_kwargs.update(do_sample=False)
    out = model.generate(**enc, **gen_kwargs)
    new_tokens = out[0, enc["input_ids"].shape[1]:]
    return tok.decode(new_tokens, skip_special_tokens=True)
