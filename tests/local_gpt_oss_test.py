#!/usr/bin/env python3
"""Test script for OpenAI GPT-OSS-20B local model loading and inference."""

import os
from transformers import AutoModelForCausalLM, AutoTokenizer

# Allow override via env var; default to GPT-OSS-20B
model_name = os.getenv("LOCAL_LLM_MODEL", "openai/gpt-oss-20b")

print(f"🧪 Testing GPT-OSS model: {model_name}")
print("⚠️  Note: First run will download ~10GB model files")

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto",
    trust_remote_code=True,
    low_cpu_mem_usage=True,
)

prompt = "Give me a short introduction to large language model."
messages = [{"role": "user", "content": prompt}]

text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer([text], return_tensors="pt").to(model.device)

generated = model.generate(
    **inputs,
    max_new_tokens=128,
    do_sample=True,
    top_p=0.9,
    temperature=0.8,
)
output_ids = generated[0][len(inputs.input_ids[0]):]
print("content:", tokenizer.decode(output_ids, skip_special_tokens=True))
