import queue
from multiprocessing import Queue, Process
import threading
import logging
import time
import os
from random import randint


def timer_monitor(start_time, stop, count_of_process):
    while not stop.is_set():
        elapsed = time.time() - start_time
        print(f"--- [Timer Thread]: Минуло {elapsed:.1f} сек, оброблено {count_of_process[0]} ---")
        time.sleep(1)


def transaction_generator(count_of_transactions, output_queue):
    for i in range(count_of_transactions):
        amount = randint(-1000, 1000)
        create_transaction = [i, amount]
        output_queue.put(create_transaction)
    output_queue.put(None)

def transaction_filter(input_queue, output_queue):
    while True:
        transaction = input_queue.get()
        if transaction is None:
            output_queue.put(None)
            break
        if transaction[1] > 0:
            output_queue.put(transaction)

def transaction_logger(input_queue, stop_event, count_of_process, shared_stats):
    finished_filters = 0
    with open("bank_log.txt", "w", encoding="utf-8") as f:
        while True:
            try:
                # Чекаємо дані. Якщо черга порожня 0.1 сек — перевіряємо stop_event
                transaction = input_queue.get(timeout=0.1)

                if transaction is None:
                    finished_filters += 1
                    if finished_filters >= count_of_process:
                        break
                    continue

                # Оновлюємо лічильник у спільній пам'яті
                shared_stats[0] += 1
                f.write(f"Успішно: ID {transaction[0]}, Сума: {transaction[1]}\n")

            except queue.Empty:
                if stop_event.is_set():
                    break
                continue

    print(f"Логер: Роботу завершено. Всього записано: {shared_stats[0]}")

if __name__ == '__main__':
    q1 = Queue()
    q2 = Queue()

    processed_count = [0]

    transaction_count = int(input("Count of transactions: "))
    num_of_procs = os.cpu_count()
    step = transaction_count // num_of_procs

    start_time = time.time()

    stop_logging = threading.Event()
    monitor_thread = threading.Thread(target=timer_monitor, args=(start_time, stop_logging, processed_count))
    log_thread = threading.Thread(
        target=transaction_logger,
        args=(q2, stop_logging, num_of_procs, processed_count)
    )

    log_thread.start()
    monitor_thread.start()

    processes = []

    for i in range(num_of_procs):
        p1 = Process(target=transaction_generator, args=(step, q1))
        p2 = Process(target=transaction_filter, args=(q1, q2))
        p1.start()
        p2.start()
        processes.append([p1, p2])

    for p in processes:
        p[0].join()
        p[1].join()

    stop_logging.set()
    log_thread.join()
    monitor_thread.join()

    print(f"\n--- ФІНАЛ ---")
    print(f"Час виконання: {time.time() - start_time:.2f} сек")
    print(f"Результати збережено в bank_log.txt")


