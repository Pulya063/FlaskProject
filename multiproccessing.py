from concurrent.futures.process import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from multiprocessing import Queue
from os import cpu_count
from threading import Thread
import logging
from time import perf_counter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(processName)s/%(threadName)s] %(message)s")

def lucky_tickets(start_stop):
    start, stop = start_stop
    tickets = []
    for i in range(start, stop+1):
        ticket = [int(d) for d in f"{i:06d}"]
        if sum(ticket[:3]) == sum(ticket[3:]):
            tickets.append(ticket)
    return tickets

if __name__ == "__main__":
    total_tickets = 1000000
    num_workers = cpu_count()
    parts = []
    part = total_tickets // num_workers
    for i in range(num_workers):
        parts.append([i * part, ((i + 1) * part) - 1])
    parts[-1][1] += 1
    simple_timer = perf_counter()
    logging.info(f"Запуск задач для {total_tickets} квитків (розподіл на {num_workers} чанків)\n")

    print("1. Запуск Single-threaded...")
    start_time = perf_counter()
    result = lucky_tickets([0, total_tickets])
    stop_time = perf_counter()
    simple_timer = stop_time - start_time
    logging.info(f"Результат: {len(result)}, Час: {simple_timer:.4f} сек\n")

    print("2. Запуск Multithreading...")
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        result_thread = list(executor.map(lucky_tickets, parts))
    stop_time = perf_counter()
    thread_timer = stop_time - start_time
    logging.info(f"Результат: {sum(len(i) for i in result_thread)}, Час: {thread_timer:.4f} сек")
    logging.info(f"Прискорення: {simple_timer / thread_timer:.2f}x\n")

    print("3. Запуск Multiprocessing...")
    start_time = perf_counter()
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        result_processes = list(executor.map(lucky_tickets, parts))
    stop_time = perf_counter()
    processes_timer = stop_time - start_time
    logging.info(f"Результат: {sum(len(i) for i in result_processes)}, Час: {processes_timer:.4f} сек")
    logging.info(f"Прискорення: {simple_timer / processes_timer:.2f}x\n")

