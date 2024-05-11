# 假设这是你的生成器函数定义
def my_generator(n):
    for i in range(n):
        yield i

# 创建生成器对象
gen = my_generator(5)

# 使用for循环迭代生成器
for _ in gen:
    continue