import logging
import os
import threading
import time
from multiprocessing import Process, Queue

def timer_monitor(start_time, stop):
    while not stop.is_set():
        elapsed = time.time() - start_time
        print(f"--- [Timer Thread]: Минуло {elapsed:.1f} сек... ---")
        time.sleep(1)


def ticket_generator(start, end, output_queue):
    for i in range(start, end+1):
            ticket_digits = [int(d) for d in f"{i:06d}"]
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

if __name__ == '__main__':
    q1 = Queue()
    q2 = Queue()

    total_tickets = 100000
    num_of_procs = os.cpu_count()
    step = total_tickets // num_of_procs

    start_time = time.time()

    stop_event = threading.Event()
    monitor_thread = threading.Thread(target=timer_monitor, args=(start_time, stop_event))
    monitor_thread.start()
    processes = []
    for i in range(num_of_procs):
        p1 = Process(target=ticket_generator, args=(i*step, (i+1)*step, q1))
        p2 = Process(target=get_lucky_tickets, args=(q1,q2))
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


    stop_event.set()
    for p in processes:
        p[0].join()
        p[1].join()
    monitor_thread.join()

    print(f"\nЗавершено! Знайдено щасливих квитків: {len(lucky_tickets_list)}")
    print(f"Загальний час: {time.time() - start_time:.2f} сек")
