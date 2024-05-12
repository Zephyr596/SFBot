from ipex_llm.transformers import AutoModelForCausalLM
import torch
import os

model_path = "/home/llm/models/Llama-2-13b-chat-hf"

model = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True)
model_sym = AutoModelForCausalLM.from_pretrained(model_path, load_in_low_bit="sym_int4")
model_asym = AutoModelForCausalLM.from_pretrained(model_path, load_in_low_bit="asym_int4")
model_int8 = AutoModelForCausalLM.from_pretrained(model_path, load_in_low_bit="sym_int8")

print("Standard model memory footprint (MB):", model.get_memory_footprint() / (1024 * 1024))
print("Symmetric int4 model memory footprint (MB):", model_sym.get_memory_footprint() / (1024 * 1024))
print("Asymmetric int4 model memory footprint (MB):", model_asym.get_memory_footprint() / (1024 * 1024))
print("Symmetric int8 model memory footprint (MB):", model_int8.get_memory_footprint() / (1024 * 1024))
