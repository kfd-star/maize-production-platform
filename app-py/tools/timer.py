import time

class Timer:
    def __init__(self):
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def stop(self):
        end_time = time.time()
        execution_time = end_time - self.start_time
        print(f"任务执行时间: {execution_time}秒")
        self.start_time = None

def timer(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        print(f"任务执行时间: {execution_time}秒")
        return result
    return wrapper