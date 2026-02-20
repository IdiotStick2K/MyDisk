# main.py
import os
import sys
import json
import ctypes
import atexit
import tkinter
from tkinter import messagebox

if getattr(sys, "frozen", False):
    script_dir = os.path.dirname(sys.executable)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Kill any previous instance via PID file 
PID_FILE = os.path.join(script_dir, "mydisk.pid")

def _kill_previous():
    if not os.path.exists(PID_FILE):
        return
    try:
        with open(PID_FILE, "r") as f:
            old_pid = int(f.read().strip())
    except (ValueError, IOError):
        try:
            os.remove(PID_FILE)
        except OSError:
            pass
        return

    if old_pid == os.getpid():
        return

    # Open with PROCESS_TERMINATE | SYNCHRONIZE
    handle = ctypes.windll.kernel32.OpenProcess(0x00100001, False, old_pid)
    if handle:
        ctypes.windll.kernel32.TerminateProcess(handle, 0)
        # Wait up to 2 s for it to die so files/ports are freed
        ctypes.windll.kernel32.WaitForSingleObject(handle, 2000)
        ctypes.windll.kernel32.CloseHandle(handle)
        print(f"[Startup] Terminated previous instance (PID {old_pid})")
    else:
        print(f"[Startup] Previous PID {old_pid} already gone")

    try:
        os.remove(PID_FILE)
    except OSError:
        pass

_kill_previous()

# Writing my own PID so the next launch can find and kill myself
with open(PID_FILE, "w") as f:
    f.write(str(os.getpid()))

def _cleanup_pid():
    """Remove the PID file when this process exits cleanly."""
    try:
        if os.path.exists(PID_FILE):
            with open(PID_FILE, "r") as f:
                stored = f.read().strip()
            if stored == str(os.getpid()):
                os.remove(PID_FILE)
    except OSError:
        pass

atexit.register(_cleanup_pid)

def send_initjson_message():
    confirm = messagebox.askyesno(
        "Your storage log is empty!",
        f"Would you like to import one?"
    )
    if not confirm:
        return
    from ui import App
    open_tools = App.open_tools


from backend import initialize_json_files
status = initialize_json_files()
print(status)

settings_file = os.path.join(script_dir, "data", "app_config.json")
try:
    with open(settings_file, "r") as f:
        settings = json.load(f)
except Exception:
    settings = {}

background_logging = settings.get("background_logging", True)


from ui import App
import background

app = App(settings=settings)


if background_logging:
    background.start_logger()

app.create_tray_icon()


app.root.deiconify()
def send_initjson_message():
    confirm = messagebox.askyesno(
        "Your storage log is empty!",
        f"Would you like to import one?"
    )
    if not confirm:
        return
    from ui import App
    app.open_tools()

if status == False:
    send_initjson_message()


# ── Run ───────────────────────────────────────────────────────────────────────
app.run()
