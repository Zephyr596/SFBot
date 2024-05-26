import matplotlib.pyplot as plt
import numpy as np

# Data
categories = ["STEM", "Social Science", "Humanities", "Other", "Hard", "Average"]
labels = ["Science & Tech", "Social Science", "Humanities", "Other", "Hard", "Average"]
precision_types = ["standard", "sym_int8", "asym_int4", "sym_int4"]
results = {
    "standard": [32.43, 39.12, 39.03, 32.08, 29.73, 35.04],
    "sym_int8": [33.16, 39.39, 37.50, 31.18, 32.17, 34.86],
    "asym_int4": [32.05, 39.24, 32.80, 28.56, 26.94, 32.85],
    "sym_int4": [32.53, 38.67, 36.32, 27.59, 32.12, 33.47]
}

# Setting up the plot
fig, ax = plt.subplots(figsize=(12, 8))

# Calculating bar positions
index = np.arange(len(categories))
bar_width = 0.2

# Colors for better contrast
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
hatchs = ['-', '/', '.', '\\']
# Plotting bars for each precision type
for i, ptype in enumerate(precision_types):
    results_by_type = [results[ptype][j] for j in range(len(categories))]
    ax.bar(index + i * bar_width, results_by_type, bar_width, label=ptype, color=colors[i], hatch=hatchs[i])

# Adding plot labels and title
ax.set_xlabel('Category', fontsize=14)
ax.set_ylabel('Scores', fontsize=14)
ax.set_title('Model Performance Comparison Using C-Eval', fontsize=16)
ax.set_xticks(index + bar_width)
ax.set_xticklabels(labels)
ax.legend()

# Saving the figure
plt.savefig("./png/ceval.png")
