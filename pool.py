from concurrent.futures import ThreadPoolExecutor
import threading
import time


def task(n):
    time.sleep(n)
    print("Processing {}".format(n))
    print("Task Executed {}".format(threading.current_thread()))


def main():
    print("Starting ThreadPoolExecutor")
    alist = [2, 4, 6]
    executor = ThreadPoolExecutor(max_workers=len(alist))
    for a in alist:
        executor.submit(task, a)
    # with ThreadPoolExecutor(max_workers=3) as executor:
    #     future = executor.submit(task, (2))
    #     future = executor.submit(task, (3))
    #     future = executor.submit(task, (4))
    print("All tasks complete")


if __name__ == '__main__':
    start_time = time.time()
    main()
    end_time = time.time()
    print("Elapsed time was %g seconds" % (end_time - start_time))
