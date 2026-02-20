import threading
import time
from backend import log_data_once

_stop_event = threading.Event()
_logger_thread = None


def _logger_loop():
    while not _stop_event.is_set():
        try:
            interval = log_data_once()
        except Exception as e:
            print(f"[Logger] Error: {e}")
            interval = 60  # fallback
        # Sleep in small increments so we can respond to stop quickly
        for _ in range(int(interval)):
            if _stop_event.is_set():
                return
            time.sleep(1)


def start_logger():
    """Start the background logger thread."""
    global _logger_thread
    if _logger_thread is not None and _logger_thread.is_alive():
        print("[Logger] Already running.")
        return
    _stop_event.clear()
    _logger_thread = threading.Thread(target=_logger_loop, daemon=True, name="StorageLogger")
    _logger_thread.start()
    print("[Logger] Started.")


def stop_logger():
    """Signal the logger thread to stop and wait for it."""
    global _logger_thread
    _stop_event.set()
    if _logger_thread is not None and _logger_thread.is_alive():
        _logger_thread.join(timeout=5)
    _logger_thread = None
    print("[Logger] Stopped.")


def is_running():
    return _logger_thread is not None and _logger_thread.is_alive()