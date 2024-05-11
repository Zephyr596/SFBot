from torchviz import make_dot
import torch
from ipex_llm.transformers import AutoModelForCausalLM
from transformers import LlamaTokenizer

LLAMA2_PROMPT_FORMAT = """
[INST] <<SYS>>
You are a helpful assistant.
<</SYS>>
{prompt}[/INST]
"""

model_path = "/home/llm/models/Llama-2-7b-chat-hf"


model = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True)
print(model)
tokenizer = LlamaTokenizer.from_pretrained(model_path, trust_remote_code=True)

prompt = LLAMA2_PROMPT_FORMAT.format(prompt="Once upon a time")
input_ids = tokenizer.encode(prompt, return_tensors="pt")


# # 运行模型
# outputs = model(input_ids)
# logits = outputs.logits  # 获取模型的输出

# # 创建可视化图
# dot = make_dot(logits, params=dict(model.named_parameters()))
# dot.render('model_visualization', format='png')  # 输出图像到文件

"""
LlamaForCausalLM(
  (model): LlamaModel(
    (embed_tokens): Embedding(32000, 4096, padding_idx=0)
    (layers): ModuleList(
      (0-31): 32 x LlamaDecoderLayer(
        (self_attn): LlamaSdpaAttention(
          (q_proj): Linear(in_features=4096, out_features=4096, bias=False)
          (k_proj): Linear(in_features=4096, out_features=4096, bias=False)
          (v_proj): Linear(in_features=4096, out_features=4096, bias=False)
          (o_proj): Linear(in_features=4096, out_features=4096, bias=False)
          (rotary_emb): LlamaRotaryEmbedding()
        )
        (mlp): LlamaMLP(
          (gate_proj): Linear(in_features=4096, out_features=11008, bias=False)
          (up_proj): Linear(in_features=4096, out_features=11008, bias=False)
          (down_proj): Linear(in_features=11008, out_features=4096, bias=False)
          (act_fn): SiLU()
        )
        (input_layernorm): LlamaRMSNorm()
        (post_attention_layernorm): LlamaRMSNorm()
      )
    )
    (norm): LlamaRMSNorm()
  )
  (lm_head): Linear(in_features=4096, out_features=32000, bias=False)
)
"""