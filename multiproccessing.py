import logging
import os
import threading
import time
from multiprocessing import Process, Queue

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(threadName)s] %(levelname)s: %(message)s")

def ticket_generator(start, end, output_queue):
    for t in range(start, end+1):
            ticket_digits = [int(d) for d in f"{t:06d}"]
            output_queue.put(ticket_digits)
    output_queue.put(None)

def get_lucky_tickets(input_queue, output_queue):
    while True:
        ticket = input_queue.get()
        if ticket is None:
            output_queue.put(None)
            break

        if sum(ticket[:3]) == sum(ticket[3:]):
            output_queue.put(ticket)

def thread_with_processes(all_tickets, start ,output_queue):
    q1 = Queue()
    q2 = Queue()

    num_of_procs = os.cpu_count()
    step = all_tickets // num_of_procs

    processes = []

    for i in range(num_of_procs):
        p1 = Process(target=ticket_generator, args=(i * step, (i + 1) * step, q1))
        p2 = Process(target=get_lucky_tickets, args=(q1, q2))
        processes.append([p1, p2])
        p1.start()
        p2.start()

    lucky_tickets_list = []
    finished_filters = 0

    while finished_filters < num_of_procs:
        lucky_ticket = q2.get()
        if lucky_ticket is None:
            finished_filters += 1
        else:
            lucky_tickets_list.append(lucky_ticket)

    for p in processes:
        p[0].join()
        p[1].join()

    time_of_the_end = time.time() - start
    logging.info(f"Thread with 4 processes finished in {time_of_the_end:.2f} сек, total = {len(lucky_tickets_list)}")
    output_queue.put((len(lucky_tickets_list), time_of_the_end))


def simple_lucky_ticket(tickets ,time_of_start, output_queue):
    tickets_list = []

    for t in range(tickets+1):
        check_ticket = [int(d) for d in f"{t:06d}"]

        if sum(check_ticket[:3]) == sum(check_ticket[3:]):
            tickets_list.append(t)

    result_time = time.time() - time_of_start
    logging.info(f"Thread with 4 processes finished in {result_time:.2f} сек, total = {len(tickets_list)}")
    output_queue.put((len(tickets_list), result_time))

if __name__ == '__main__':
    q = Queue()

    total_tickets = 100000

    start_time = time.time()

    stop_event = threading.Event()

    t1 = threading.Thread(target=thread_with_processes, args=(total_tickets, start_time, q,))
    t2 = threading.Thread(target=simple_lucky_ticket, args=(total_tickets, start_time, q,))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    stop_event.set()

    results = []
    while not q.empty():
        results.append(q.get())

    for idx, (total_lucky_tickets, elapsed) in enumerate(results):
        logging.info(f"Thread {idx + 1}: total = {total_lucky_tickets}, час виконання = {elapsed:.2f} сек")
