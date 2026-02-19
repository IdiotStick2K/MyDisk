from backend import log_data_once
import threading
import time

def logger_loop():
    while True:
        interval = log_data_once()
        time.sleep(interval)

def start_logger():
    thread = threading.Thread(
        target=logger_loop,
        daemon=True
    )
    thread.start()
