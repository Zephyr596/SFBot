import torch
import time
import argparse
import pdb

from ipex_llm.transformers import AutoModelForCausalLM
from transformers import LlamaTokenizer

# you could tune the prompt based on your own model,
# Refer to https://huggingface.co/TheBloke/Llama-2-70B-Chat-GGML#prompt-template-llama-2-chat
LLAMA2_PROMPT_FORMAT = """
[INST] <<SYS>>
You are a helpful assistant.
<</SYS>>
{prompt}[/INST]
"""

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Predict Tokens using `generate()` API for Llama2 model')
    parser.add_argument('--repo-id-or-model-path', type=str, default="meta-llama/Llama-2-7b-chat-hf",
                        help='The huggingface repo id for the Llama2 (e.g. `meta-llama/Llama-2-7b-chat-hf` and `meta-llama/Llama-2-13b-chat-hf`) to be downloaded'
                             ', or the path to the huggingface checkpoint folder')
    parser.add_argument('--prompt', type=str, default="What is AI?",
                        help='Prompt to infer')
    parser.add_argument('--n-predict', type=int, default=32,
                        help='Max tokens to predict')

    args = parser.parse_args()
    model_path = "/home/llm/models/Llama-2-7b-chat-hf"

    # Load model in 4 bit,
    # which convert the relevant layers in the model into INT4 format
    #pdb.set_trace()
    model = AutoModelForCausalLM.from_pretrained(model_path,
                                                 trust_remote_code=True,
                                                 load_in_low_bit="sym_int4")
   
    print(model)
    # Load tokenizer
    tokenizer = LlamaTokenizer.from_pretrained(model_path, trust_remote_code=True)
    
    # Generate predicted tokens
    with torch.inference_mode():
        prompt = LLAMA2_PROMPT_FORMAT.format(prompt="What is AI?")
        input_ids = tokenizer.encode(prompt, return_tensors="pt")
        st = time.time()
        # if your selected model is capable of utilizing previous key/value attentions
        # to enhance decoding speed, but has `"use_cache": false` in its model config,
        # it is important to set `use_cache=True` explicitly in the `generate` function
        # to obtain optimal performance with IPEX-LLM INT4 optimizations
        output = model.generate(input_ids,
                                max_new_tokens=args.n_predict)
        end = time.time()
        output_str = tokenizer.decode(output[0], skip_special_tokens=True)
        print(f'Inference time: {end-st} s')
        print('-'*20, 'Prompt', '-'*20)
        print(prompt)
        print('-'*20, 'Output', '-'*20)
        print(output_str)
