# main.py
import os
import sys
import ctypes
import subprocess
import threading
import time
import tkinter as tk
import json
from backend import initialize_json_files
from ui import App


if getattr(sys, "frozen", False):
    script_dir = os.path.dirname(sys.executable)
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)


initialize_json_files()
restart_flag = os.path.join(script_dir, "restart.flag")
first_launch_flag = os.path.join(script_dir, "first_launch.flag")


def single_instance():
    mutex_name = "MyDiskAppMutex_0.1.5"
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    ERROR_ALREADY_EXISTS = 183
    last_error = ctypes.windll.kernel32.GetLastError()
    return last_error != ERROR_ALREADY_EXISTS

if not single_instance():
    sys.exit()


if os.path.exists(restart_flag):
    os.remove(restart_flag)

    subprocess.Popen([sys.executable] + sys.argv, creationflags=0x08000000)
    sys.exit()


app = App()

def restart_app():
    """Restart MyDisk cleanly"""
    with open(restart_flag, "w") as f:
        f.write("1")
    app.quit_app()
app.restart_app = restart_app


settings_file = os.path.join(script_dir, "data", "app_config.json")
with open(settings_file, "r") as f:
    app.settings = json.load(f)


app.create_tray_icon()


def adjust_window():
    time.sleep(0.05)  # tiny delay to avoid race in EXE
    bg_logging = app.settings.get("background_logging", True)
    first_run = not os.path.exists(first_launch_flag)

    if first_run:
        app.root.deiconify()  
        with open(first_launch_flag, "w") as f:
            f.write("1")
    elif bg_logging:
        app.root.deiconify()  
    else:
        app.root.withdraw()   

threading.Thread(target=adjust_window, daemon=True).start()


app.run()
