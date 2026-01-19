from multiprocessing import cpu_count

# from celery import Celery
#
# app = Celery('tasks', broker='pyamqp://guest@localhost//')
#
# @app.task
# def add(x, y):
#     return x + y
#
# a = add.delay(4,4)
# print(a.get(timeout=1))

total_tickets = 1000000
num_workers = cpu_count()
part = total_tickets // num_workers

parts = []
for i in range(num_workers):
    parts.append([i * part, ((i + 1) * part) - 1])
parts[-1][1] += 1
print(parts)