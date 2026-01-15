from threading import Thread
from multiprocessing import Process, Queue
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(threadName)s] %(levelname)s: %(message)s"
)

def process_worker(start, end, q):
    total = 0
    for i in range(start, end):
        total += i**2
    q.put(total)

def thread_with_processes(number, output_queue):
    q = Queue()
    num_processes = 4
    part = number // num_processes
    processes = []

    start_time = time.time()
    for i in range(num_processes):
        p_start = i * part
        p_end = (i + 1) * part if i < num_processes - 1 else number
        p = Process(target=process_worker, args=(p_start, p_end, q))
        processes.append(p)
        p.start()

    total = 0
    for p in processes:
        p.join()
    while not q.empty():
        total += q.get()

    elapsed = time.time() - start_time
    logging.info(f"Thread with 4 processes finished in {elapsed:.2f} сек, total = {total}")
    output_queue.put((total, elapsed))

def simple_thread(number, output_queue):
    start_time = time.time()
    total = 0
    for i in range(number):
        total += i**2
    elapsed = time.time() - start_time
    logging.info(f"Simple thread finished in {elapsed:.2f} сек, total = {total}")
    output_queue.put((total, elapsed))

if __name__ == "__main__":
    from queue import Queue as ThreadQueue
    number = 50000000
    results_queue = ThreadQueue()

    # Потік без процесів
    t1 = Thread(target=simple_thread, args=(number, results_queue), name="Simple-Thread")
    # Потік з процесами
    t2 = Thread(target=thread_with_processes, args=(number, results_queue), name="Thread-with-Processes")

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Збираємо результати
    results = []
    while not results_queue.empty():
        results.append(results_queue.get())

    for idx, (total, elapsed) in enumerate(results):
        logging.info(f"Thread {idx+1}: total = {total}, час виконання = {elapsed:.2f} сек")
