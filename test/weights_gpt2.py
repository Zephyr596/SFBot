import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import numpy as np
import matplotlib.pyplot as plt
from copy import deepcopy

torch.manual_seed(0)



def absmax_quantize(X):
    # Calculate scale
    scale = 127 / torch.max(torch.abs(X))

    # Quantize
    X_quant = (scale * X).round()

    # Dequantize
    X_dequant = X_quant / scale

    return X_quant.to(torch.int8), X_dequant


def zeropoint_quantize(X):
    # Calculate value range (denominator)
    x_range = torch.max(X) - torch.min(X)
    x_range = 1 if x_range == 0 else x_range

    # Calculate scale
    scale = 255 / x_range

    # Shift by zero-point
    zeropoint = (-scale * torch.min(X) - 128).round()

    # Scale and round the inputs
    X_quant = torch.clip((X * scale + zeropoint).round(), -128, 127)

    # Dequantize
    X_dequant = (X_quant - zeropoint) / scale

    return X_quant.to(torch.int8), X_dequant


device = 'cpu'

model_path = "/home/llm/models/gpt2"

model = AutoModelForCausalLM.from_pretrained(pretrained_model_name_or_path=model_path).to(device)

tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path = model_path)

# print(f"Model size: {model.get_memory_footprint():,} bytes")

# # Extract weights of the first layer
# weights = model.transformer.h[0].attn.c_attn.weight.data
# print("Original weights:")
# print(weights)

# # Quantize layer using absmax quantization
# weights_abs_quant, _ = absmax_quantize(weights)
# print("\nAbsmax quantized weights:")
# # print(weights_abs_quant)

# # Quantize layer using absmax quantization
# weights_zp_quant, _ = zeropoint_quantize(weights)
# print("\nZero-point quantized weights:")
# # print(weights_zp_quant)

def flatten_params(params):
    flat_list = []
    for param in params:
        flat_list.extend(param.cpu().detach().numpy().flatten())
    return np.array(flat_list)

# Store original weights
weights = [param.data.clone() for param in model.parameters()]
flat_weights = flatten_params(weights)
print(flat_weights)
# weights = np.array(weights)
# print(weights.shape)

# Create model to quantize
model_abs = deepcopy(model)

# Quantize all model weights
weights_abs = []
for param in model_abs.parameters():
    _, dequantized = absmax_quantize(param.data)
    param.data = dequantized
    weights_abs.append(dequantized)

# Create model to quantize
model_zp = deepcopy(model)

# Quantize all model weights
weights_zp = []
for param in model_zp.parameters():
    _, dequantized = zeropoint_quantize(param.data)
    param.data = dequantized
    weights_zp.append(dequantized)

plt.figure(figsize=(10, 6))
print("开始绘制图一")
plt.hist(weights.flatten(), bins=50, alpha=0.5, label='Original Weights', color='blue')
print("开始绘制图二")
plt.hist(weights_abs.flatten(), bins=50, alpha=0.5, label='DeQuantized Weights', color='red')
plt.legend()
plt.title('Histogram Comparison of Original and Quantized Weights')
plt.xlabel('Weight Value')
plt.ylabel('Frequency')
print("Created!")
plt.savefig('gpt2_abs.png')
