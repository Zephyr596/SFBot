import matplotlib.pyplot as plt
import numpy as np
from ipex_llm.transformers import AutoModelForCausalLM
import time

model_paths = ["/home/llm/models/Llama-2-7b-chat-hf", "/home/llm/models/Llama-2-13b-chat-hf"]
models_labels = ['Llama-2-7b', 'Llama-2-13b']

def timer(low_bit, model_path, num_runs=5):
    times = []
    for _ in range(num_runs):
        st = time.perf_counter()
        if low_bit == "":
            model = AutoModelForCausalLM.from_pretrained(model_path, trust_remote_code=True)
        else:
            model = AutoModelForCausalLM.from_pretrained(model_path, load_in_low_bit=low_bit)
        end = time.perf_counter()
        del model
        times.append(end - st)
    return np.mean(times), np.std(times)

low_bits = ["", "sym_int4", "asym_int4", "sym_int8"]
labels = ["Standard", "Symmetric INT4", "Asymmetric INT4", "INT8"]
mean_load_times = [[], []]  # Two lists for the two models
std_devs = [[], []]

# Collect data for each model and quantization method
for model_path, model_data, model_std_dev in zip(model_paths, mean_load_times, std_devs):
    for low_bit in low_bits:
        mean_time, std_dev = timer(low_bit, model_path)
        print(f"{model_path}, {low_bit}, {mean_time}, {std_dev}")
        model_data.append(mean_time)
        model_std_dev.append(std_dev)


# Plotting the data
x = np.arange(len(labels))  # the label locations
width = 0.35  # the width of the bars

fig, ax = plt.subplots()
rects1 = ax.bar(x - width/2, mean_load_times[0], width, yerr=std_devs[0], label=models_labels[0], capsize=5, color='royalblue')
rects2 = ax.bar(x + width/2, mean_load_times[1], width, yerr=std_devs[1], label=models_labels[1], capsize=5, color='seagreen')

ax.set_ylabel('Load Time (seconds)')
ax.set_title('Load Time by Model and Quantization Method')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.legend()

ax.bar_label(rects1, padding=3)
ax.bar_label(rects2, padding=3)

fig.tight_layout()

plt.savefig("./png/time.png")

"""
          Llma-2-7b   LLama-2-13b
Standard  30.1276     64.7866
SYM_INT4  1.68288	  9.57686
ASYM_INT4 11.8801     30.0044
INT8      34.3865     73.7418
"""