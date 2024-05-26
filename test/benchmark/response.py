import matplotlib.pyplot as plt
import numpy as np

data_int4 = [
    (32, [2.0826747976243496, 2.229557222686708, 2.3633068818598986, 2.3645077161490917]),
    (256, [2.6115091256797314, 2.5966229205951095, 2.5931835174560547, 2.592905214987695]),
    (512, [5.293188823387027, 5.293878334574401, 5.293075506575406, 5.2930555790662766]),
    (1024, [11.318652239628136, 11.322007364593446, 11.325061233714223, 11.320399543270469])
]

data = [
    (32, [4.205271264538169, 4.2903669364750385, 4.113870704546571, 4.093328752554953]),
    (256, [5.059052825905383, 4.948360200040042, 4.922397517599165, 4.947699690237641]),
    (512, [11.694352191872895, 11.610576120205224, 11.599959883838892, 11.69382556155324]),
    (1024, [24.098206428810954, 24.11817590892315, 24.1252215616405, 24.142265174537897])
]

# 提取信息
input_lengths = [str(item[0]) for item in data]
times_int4 = [item[1] for item in data_int4]
means_int4 = [np.mean(t) for t in times_int4]
stds_int4 = [np.std(t) for t in times_int4]

times = [item[1] for item in data]
means = [np.mean(t) for t in times]
stds = [np.std(t) for t in times]

x = np.arange(len(input_lengths))  # the label locations

# 绘制柱形图
width = 0.35  # the width of the bars
fig, ax = plt.subplots(figsize=(10, 6))
rects1 = ax.bar(x - width/2, means, width, label='Original Model', color='skyblue', yerr=stds, capsize=5, hatch='/')
rects2 = ax.bar(x + width/2, means_int4, width, label='SYM_Int4 Quantized Model', color='lightgreen', yerr=stds_int4, capsize=5, hatch='\\')

# 添加文本标签、标题和自定义x轴刻度标签等
ax.set_xlabel('Input Length')
ax.set_ylabel('Time (seconds)')
ax.set_title('Model Generation Time vs Input Length')
ax.set_xticks(x)
ax.set_xticklabels(input_lengths)
ax.legend()

# 保存图像
plt.savefig("../png/input_response.png")

