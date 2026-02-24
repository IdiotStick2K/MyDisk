import threading
from backend import log_data_once

_stop_event = threading.Event()
_logger_thread = None

def _logger_loop():
    while not _stop_event.is_set():
        try:
            raw_interval = log_data_once()
            interval = raw_interval / 60
            print(f"Interval from logger is {interval}")
        except Exception as e:
            print(f"[Logger] Error: {e}")
            interval = 60
        # Sleeps for the full interval but wakes immediately if stop is called
        _stop_event.wait(timeout=interval * 60)

def start_logger():
    global _logger_thread
    if _logger_thread is not None and _logger_thread.is_alive():
        print("[Logger] Already running.")
        return
    _stop_event.clear()
    _logger_thread = threading.Thread(target=_logger_loop, daemon=True, name="StorageLogger")
    _logger_thread.start()
    print("[Logger] Started.")

def stop_logger():
    global _logger_thread
    _stop_event.set()
    if _logger_thread is not None and _logger_thread.is_alive():
        _logger_thread.join(timeout=5)
    _logger_thread = None
    print("[Logger] Stopped.")

def is_running():
    return _logger_thread is not None and _logger_thread.is_alive()