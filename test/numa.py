import matplotlib.pyplot as plt

# Define data
labels = ['96-core', '48-core Cross Node', '48-core Same Node']
first_token_times = [4899.69, 4956.55, 4041.76]
next_token_times = [168.24, 377.95, 159.51]

x = range(len(labels))  # Label positions

# Create the first bar chart
# 创建子图，分别绘制 First Token Time 和 Next Token Time，并调整颜色以增加视觉吸引力
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
# plt.rcParams['font.size'] = 17

# 定义颜色
colors1 = ['skyblue', 'lightgreen', 'salmon']
colors2 = ['dodgerblue', 'limegreen', 'red']
hatchs = ['/', '\\', '-']

# 绘制 First Token Time
ax1.bar(labels, first_token_times, color=colors1, hatch=hatchs)
ax1.set_title('First Token Time')
ax1.set_ylabel('Time (ms)')
ax1.set_xlabel('Configuration')
for i, v in enumerate(first_token_times):
    ax1.text(i, v + 50, f"{v:.2f}", ha='center', color='black')

# 绘制 Next Token Time
ax2.bar(labels, next_token_times, color=colors2, hatch=hatchs)
ax2.set_title('Next Token Time')
ax2.set_ylabel('Time (ms)')
ax2.set_xlabel('Configuration')
for i, v in enumerate(next_token_times):
    ax2.text(i, v , f"{v:.2f}", ha='center', color='black')

plt.tight_layout()
plt.savefig("./png/numa.png")
