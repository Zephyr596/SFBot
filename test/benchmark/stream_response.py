import matplotlib.pyplot as plt

# token_time = [3941.52, 159.04, 160.14, 158.36, 159.74, 160.08, 161.01, 158.14, 159.10, 159.50, 159.38]

token_time = [2762.88, 139.56, 143.64, 141.80, 143.01, 139.82, 143.64, 138.52, 136.89, 136.83, 140.60]

tokens = range(1, len(token_time) + 1)
# for token, time in zip(tokens, token_time):
# 	plt.text(token, time, str(time), ha='center', va='bottom', fontsize=10)
# 	break
plt.plot(tokens, token_time)
plt.xlabel('Token')
plt.ylabel('Time (ms)')
plt.title('512 Input Token Generation Time')
plt.savefig("../png/stream.png")