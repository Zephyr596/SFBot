import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
# Generate data points for concurrency levels from 1 to 10 based on the trends observed

# Base data for extrapolation
concurrency_levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
throughput_2pod = [11.6453, 22.0991, 31.7362, 40.5565, 48.5602, 55.7471, 62.1173, 67.6708, 72.4076, 76.3276] 
next_latency_2pod = [73.9925, 78.2973, 82.7094, 87.2289, 91.8556, 96.5897, 101.4311, 106.3798, 111.4358, 116.5992]

concurrency_levels = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
throughput_1pod = [6.08, 11.85, 17.32, 22.50, 27.42, 32.09, 36.51, 40.70, 44.68, 48.45]
next_latency_1pod = [70.98, 73.35, 75.72, 78.08, 80.45, 82.82, 85.18, 87.55, 89.92, 92.28]


# Create DataFrame for plotting
interpolated_data = {
    "Throughput (token/s)": throughput,
    "Latency (ms)": next_latency,
    "Max Concurrent Req": concurrency_levels
}
interpolated_df = pd.DataFrame(interpolated_data)

# Generate scatter plot with interpolated data
fig, ax = plt.subplots(figsize=(8, 6))
interpolated_df.plot(kind='scatter', x='Throughput (token/s)', y='Latency (ms)', c='Max Concurrent Req', colormap='viridis', ax=ax)
ax.set_title('Concurrent request performance when worker pod is 1')
ax.set_xlabel('Throughput (token/s)')
ax.set_ylabel('Latency (ms)')
ax.grid(True)

plt.savefig("../png/k8s_1.png")
