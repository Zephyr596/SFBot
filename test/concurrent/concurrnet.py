import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Base data for extrapolation
concurrency_levels = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

# Data for 2 pods
throughput_2pod = np.array([11.6453, 22.0991, 31.7362, 40.5565, 48.5602, 55.7471, 62.1173, 67.6708, 72.4076, 76.3276])
latency_2pod = np.array([73.9925, 78.2973, 82.7094, 87.2289, 91.8556, 96.5897, 101.4311, 106.3798, 111.4358, 116.5992])

# Data for 1 pod
throughput_1pod = np.array([6.08, 11.85, 17.32, 22.50, 27.42, 32.09, 36.51, 40.70, 44.68, 48.45])
latency_1pod = np.array([70.98, 73.35, 75.72, 78.08, 80.45, 82.82, 85.18, 87.55, 89.92, 92.28])

# Create a plot
fig, ax = plt.subplots(figsize=(10, 8))

# Plot data for 2 pods with 'o' marker
scatter1 = ax.scatter(throughput_2pod, latency_2pod, c=concurrency_levels, cmap='viridis', marker='o', s=100, label='2 Pods')

# Plot data for 1 pod with '^' marker
scatter2 = ax.scatter(throughput_1pod, latency_1pod, c=concurrency_levels, cmap='viridis', marker='^', s=100, label='1 Pod')

# Customizing the plot
ax.set_xlabel('Throughput (tokens/s)', fontsize=14)
ax.set_ylabel('Latency (ms)', fontsize=14)
ax.set_title('Performance Comparison of 1 Pod vs 2 Pods', fontsize=16)
ax.grid(True)

# Add colorbar
cbar = plt.colorbar(scatter1)
cbar.set_label('Max Concurrent Requests', fontsize=14)

# Add legend
ax.legend()

# Save the plot
plt.savefig("../png/k8s_comparison_color_mapped.png")
plt.show()
