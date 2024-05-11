import torch
import time
import argparse
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

from ipex_llm.transformers import AutoModelForCausalLM
from transformers import LlamaTokenizer
from ipex_llm.transformers.low_bit_linear import ggml_int4_convert_fp32

LLAMA2_PROMPT_FORMAT = """
[INST] <<SYS>>
You are a helpful assistant.
<</SYS>>
{prompt}[/INST]
"""

model_path = "/home/llm/models/Llama-2-7b-chat-hf"

model = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True)
model_sym = AutoModelForCausalLM.from_pretrained(model_path, load_in_low_bit = "sym_int4")
model_asym = AutoModelForCausalLM.from_pretrained(model_path, load_in_low_bit = "asym_int4")

weight = []

weight_sym = []

weight_asym = []

for module in model.model.layers:
    for param in module.self_attn.parameters():
        # param = ggml_int4_convert_fp32(param, (4096, 4096), param.numel())
        param.requires_grad = False
        weight.append(param)


for module in model_sym.model.layers:
    for param in module.self_attn.parameters():
        param.requires_grad = False
        param = ggml_int4_convert_fp32(param, (4096, 4096), param.numel())
        weight_sym.append(param)

for module in model_asym.model.layers:
    for param in module.self_attn.parameters():
        param.requires_grad = False
        param = ggml_int4_convert_fp32(param, (4096, 4096), param.numel())
        weight_asym.append(param)

flattened_weight = torch.cat([w.view(-1) for w in weight])
flattened_weight_sym = torch.cat([w.view(-1) for w in weight_sym])
flattened_weight_asym = torch.cat([w.view(-1) for w in weight_sym])

weight_np = flattened_weight.numpy()
weight_sym_np = flattened_weight_sym.numpy()
weight_asym_np = flattened_weight_asym.numpy()



# n, bins, patches = plt.hist([weight_np, weight_sym_np], 
#                             bins=100, alpha=0.75, 
#                             color=['blue', 'red'],
#                             label=['Original_Weight', 'SYM_INT4_Weight'], 
#                             range=(-0.3, 0.3), 
#                             stacked=True)

# plt.title('Comparison of Original and SYM_INT4 Quantized Weights')
# plt.xlabel('Weights')
# plt.ylabel('Count')

# max_count = max(max(n[0]), max(n[1]))
# plt.yticks(ticks=np.linspace(0, max_count, 5), labels=['{:.1f}m'.format(x / 1e6) for x in np.linspace(0, max_count, 5)])

# plt.legend()

# plt.tight_layout()
# plt.savefig("test_sym.png")



n, bins, patches = plt.hist([weight_np, weight_asym_np], 
                            bins=100, alpha=0.75, 
                            color=['blue', 'yellow'],
                            label=['Original_Weight', 'ASYM_INT4_Weight'], 
                            range=(-0.3, 0.3), 
                            stacked=True)

plt.title('Comparison of Original and ASYM_INT4 Quantized Weights')
plt.xlabel('Weights')
plt.ylabel('Count')

max_count = max(max(n[0]), max(n[1]))
plt.yticks(ticks=np.linspace(0, max_count, 5), labels=['{:.1f}m'.format(x / 1e6) for x in np.linspace(0, max_count, 5)])

plt.legend()

plt.tight_layout()
plt.savefig("test_asym.png")
