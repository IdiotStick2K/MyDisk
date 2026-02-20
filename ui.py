# ui.py
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from backend import get_drive_hardware, get_drive_capacity, load_storage_logs, log_data_once
import pyperclip
from background import start_logger
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import os
import json
from PIL import Image
import pystray
import sys


start_logger()



def copy_to_clipboard(value, label="Value"):
    pyperclip.copy(str(value))
    print(f"{label} copied to clipboard")

def read_json(file_path, default=None):
    """
    Reads JSON from a file. Returns `default` if file doesn't exist or is invalid.
    """
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def write_json(file_path, data):
    """
    Writes JSON to a file, pretty-printed.
    """
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error writing JSON to {file_path}: {e}")
        return False

if getattr(sys, "frozen", False):
    base_dir = os.path.dirname(sys.executable)  
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))  


data_dir = os.path.join(base_dir, "data")

class App:
    def __init__(self):
        # The main Tkinter app
        self.root = tb.Window(themename="cosmo")
        self.root.title("MyDisk")
        self.root.geometry("800x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)


        # Dictionary to hold button/window functions
        self.buttons = {
            "Disk Info": self.open_disk_info,
            "Storage Logs": self.open_storage_logs,
            "Storage Summary": self.open_storage_summary,
            "Tools": self.open_tools,
           # "Settings": self.open_settings
            # Add more buttons here easily
        }

        self.create_main_menu()
        self.settings = self.load_settings()
        self.tray_icon = None
        self.create_tray_icon()


    # Utility helpers
    def load_settings(self):
        settings_file = os.path.join(os.getcwd(), "data", "app_config.json")
        default_settings = {
            "background_logging": False,
            "logging_interval_minutes": 10,
            "max_log_entries": 10000
        }
        settings = read_json(settings_file, default=default_settings)
        return settings

    def create_tray_icon(self):
        icon_path = os.path.join(base_dir, "art", "MyDiskLogo.png")
        icon_image = Image.open(icon_path)
        menu = pystray.Menu(
            pystray.MenuItem("Open MyDisk", lambda: self.root.deiconify()),
            pystray.MenuItem("Restart MyDisk", self.restart_app),
            pystray.MenuItem("Exit", lambda: self.quit_app())
        )
    
        self.tray_icon = pystray.Icon("MyDisk", icon_image, "MyDisk", menu)

        import threading
        threading.Thread(target=self.tray_icon.run, daemon=True).start()




    def create_main_menu(self):
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()

        # Header
        header = tb.Label(self.root, text="Welcome to MyDisk!", font=("Helvetica", 18, "bold"))
        header.pack(pady=30)

        # Frame for buttons
        btn_frame = tb.Frame(self.root)
        btn_frame.pack(pady=20, fill="x")

        # Create buttons dynamically
        for text, func in self.buttons.items():

            style = "primary"

            if text == "Tools":
                style = "secondary"

            if text == "Settings":
                style = "secondary"


            btn = tb.Button(btn_frame, text=text, bootstyle=style, width=20, command=func)
            btn.pack(pady=10)

        ver_lbl = tb.Label(self.root, text="Version: Beta 0.1.5", font=("Helvetica", 7, "italic"))
        ver_lbl.pack(pady=20, side="bottom")
        ver_lbl.pack_configure(anchor="center")

        # Exit button
        exit_btn = tb.Button(self.root, text="Exit", bootstyle="danger", command=self.root.destroy)
        exit_btn.pack(side="bottom", pady=20)



    # --- windows ---

    def open_disk_info(self):
        # Open a new window
        win = tb.Toplevel(self.root)
        win.title("Disk Info")
        win.geometry("1100x600")
    
        header = tb.Label(win, text="Disk Info Window", font=("Helvetica", 16, "bold"))
        header.pack(pady=10)
        
        get_drive_hardware()
        drives = get_drive_hardware()
        print(drives)
        print("Activated disk info menu")
    
        if not drives:
            tb.Label(win, text="No drive data found.").pack(pady=10)
            return
    
        # --- SCROLLABLE CANVAS SETUP ---
        container = tb.Frame(win)
        container.pack(fill="both", expand=True, padx=10, pady=10)
    
        canvas = tb.Canvas(container)
        scrollbar = tb.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tb.Frame(canvas)
    
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
    
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
    
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
        # --- DISPLAY DRIVES ---
        for drive in drives:
            frame = tb.Frame(scrollable_frame)
            frame.pack(fill="x", padx=5, pady=2)
    
            # Format drive info string
            drive_text = (
                f"Model: {drive.get('Model', 'N/A')} | "
                f"Size: {drive.get('Size (GB)', 'N/A')} GB | "
                f"Serial: {drive.get('Serial', 'N/A')} | "
                f"Firmware Version: {drive.get('Firmware', 'N/A')} | "
                f"Partitions #: {drive.get('Partitions', 'N/A')}"
            )
    
            lbl = tb.Label(frame, text=drive_text, anchor="w")
            lbl.pack(side="left", padx=5)
    
            copy_btn = tb.Button(
                frame,
                text="Copy",
                bootstyle="secondary",
                command=lambda text=drive_text: pyperclip.copy(text)
            )
            copy_btn.pack(side="left", padx=10)
    

        # --- Buttons frame ---

        button_frame = tb.Frame(win)
        button_frame.pack(side="bottom", fill="x", pady=10) 

        inner_frame = tb.Frame(button_frame)
        inner_frame.pack()
        
        refresh_btn = tb.Button(inner_frame, text="Refresh", bootstyle="info", command=lambda: self.open_disk_info(win))
        refresh_btn.pack(side="left", padx=5)
        
        close_btn = tb.Button(inner_frame, text="Close", bootstyle="secondary", command=win.destroy)
        close_btn.pack(side="left", padx=5)

        button_frame.pack_configure(anchor="center")




    def open_storage_logs(self, win=None):

        

        if win is None or not win.winfo_exists():
            win = tb.Toplevel(self.root)
        else:
            for widget in win.winfo_children():
                widget.destroy()

        self._logs_window = win


        win.title("Storage Logs")
        win.geometry("900x900")

        header = tb.Label(win, text="Storage Logs", font=("Helvetica", 16, "bold"))
        header.pack(pady=10)

        def on_chart_click(event):
            print("Chart clicked")
            line = event.artist
            index = event.ind[0]
        
            timestamp = line.get_xdata()[index]
            used_value = line.get_ydata()[index]


        
            snapshot = logs[index]

        
            if not snapshot:
                return
        
            details_lines = [f"Timestamp: {timestamp}", ""]
        
            details_lines.append(
                f"Used: {used_value} GB"
            )
        
            self.details_text.config(text="\n".join(details_lines))


        logs, timestamps, used_history = load_storage_logs()

        if not logs:
            tb.Label(win, text="No storage logs found..").pack(pady=10)
            return

        content_frame = tb.Frame(win)
        content_frame.pack(fill="both", expand=True)

        snapshot_frame = tb.Frame(win)
        snapshot_frame.pack(fill="both", expand=False, padx=10, pady=10)

        latest_snapshot = logs[-1]["capacity"]
        tb.Label(snapshot_frame, text="Latest Snapshot", font=("Helvetica", 14, "bold")).pack(pady=5)

        for drive in latest_snapshot:
            total_gb = round(drive["Total (MB)"] / 1024, 2)
            used_gb = round(drive["Used (MB)"] / 1024, 2)
            free_gb = round(drive["Free (MB)"] / 1024, 2)

            text = (
                f"Drive: {drive['Drive']} | "
                f"Total: {total_gb} GB | "
                f"Used: {used_gb} GB | "
                f"Free: {free_gb} GB | "
                f"Usage: {drive['Usage (%)']} %"
            )
            tb.Label(snapshot_frame, text=text, anchor="center").pack(fill="x", pady=2)

        # matplotlib charts
        fig, ax = plt.subplots(figsize=(6, 3))
        for drive, usage in used_history.items():
            ax.plot(timestamps, usage, marker="o", label=drive, picker=5)

        ax.set_title("Drive Usage Over Time")
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("Used (GB)")
        ax.legend()
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        fig.canvas.mpl_connect("pick_event", on_chart_click)




        toolbar = NavigationToolbar2Tk(canvas, win)
        toolbar.update()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=(0,10))

        # Click data

        details_frame = tb.Frame(win)
        details_frame.pack(fill="x", padx=10, pady=10)
        details_frame.pack_configure(anchor="center")

        details_header = tb.Label(
            details_frame,
            text="Point Details",
            font=("Helvetica", 12, "bold")
        )
        details_header.pack(anchor="w")

        self.details_text = tb.Label(
            details_frame,
            text="Click a point on the chart to see details.",
            anchor="w",
            justify="left"
        )
        self.details_text.pack(fill="x", pady=5)


        # --- Buttons frame ---

        button_frame = tb.Frame(win)
        button_frame.pack(side="bottom", fill="x", pady=10) 

        inner_frame = tb.Frame(button_frame)
        inner_frame.pack()
        
        refresh_btn = tb.Button(inner_frame, text="Refresh", bootstyle="info", command=lambda: self.open_storage_logs(win))
        refresh_btn.pack(side="left", padx=5)
        
        close_btn = tb.Button(inner_frame, text="Close", bootstyle="secondary", command=win.destroy)
        close_btn.pack(side="left", padx=5)

        button_frame.pack_configure(anchor="center")


    def open_storage_summary(self):

        win = tb.Toplevel(self.root)
        win.title("Storage Summary")
        win.geometry("800x300")

        header = tb.Label(win, text="Storage Summary", font=("Helvetica", 16, "bold"))
        header.pack(pady=20)

        drive_frame = tb.Frame(win)
        drive_frame.pack(fill="both", expand=True, padx=10, pady=10)

        def display_drives():
            for widget in drive_frame.winfo_children():
                widget.destroy()

            drives = get_drive_capacity()

            if not drives:
                tb.Label(drive_frame, text="No drive data found.").pack(pady=10)
                return

            for drive in drives:
                used_gb = round(drive["Used (MB)"] / 1024, 2)
                free_gb = round(drive["Free (MB)"] / 1024, 2)
                total_gb = round(drive["Total (MB)"] / 1024, 2)
    
                text = (
                    f"Drive: {drive['Drive']} | "
                    f"Total: {total_gb} GB | "
                    f"Used: {used_gb} GB | "
                    f"Free: {free_gb} GB | "
                    f"Usage: {drive['Usage (%)']} %"
                )

                lbl = tb.Label(drive_frame, text=text, anchor="w")
                lbl.pack(fill="x", padx=5, pady=2)

        display_drives()

        # Buttons
        button_frame = tb.Frame(win)
        button_frame.pack(side="bottom", pady=10)

        refresh_btn = tb.Button(button_frame, text="Refresh", bootstyle="info", command=display_drives)
        refresh_btn.pack(side="left", padx=5)

        close_btn = tb.Button(button_frame, text="Close", bootstyle="secondary", command=win.destroy)
        close_btn.pack(side="left", padx=5)

        button_frame.pack_configure(anchor="center")

    def open_tools(self):
        win = tb.Toplevel(self.root)
        win.title("Tools")
        win.geometry("800x300")

        header = tb.Label(win, text="Tools", font=("Helvetica", 16, "bold"))
        header.pack(pady=(10,2))

        lower_header = tb.Label(win, text="MyDisk Tools", font=("Helvetica", 13, "italic"))
        lower_header.pack(pady=(2,25))

        # Top buttons

        top_button_frame = tb.Frame(win)
        top_button_frame.pack(side="top", fill="x", pady=10)

        inner_top = tb.Frame(top_button_frame)
        inner_top.pack()

        log_disk_btn = tb.Button(inner_top, text="Log Disks", bootstyle="info", command=log_data_once)
        log_disk_btn.pack(side="left", padx=5)
        lgdsk_lbl = tb.Label(win, text="Logs the current capacity of all disks", font=("Helvetica", 8, "italic"))
        lgdsk_lbl.pack(pady=(2,25))

        # Bottom buttons
        bottom_button_frame = tb.Frame(win)
        bottom_button_frame.pack(side="bottom", fill="x", pady=10)

        inner_bottom = tb.Frame(bottom_button_frame)
        inner_bottom.pack()

        close_btn = tb.Button(inner_bottom, text="Close", bootstyle="secondary", command=win.destroy)
        close_btn.pack(side="left", padx=5)

    def open_settings(self):
        win = tb.Toplevel(self.root)
        win.title("Settings")
        win.geometry("800x300")
    
        # --- Header ---
        header = tb.Label(win, text="Settings", font=("Helvetica", 16, "bold"))
        header.pack(pady=(10,2))
    
        lower_header = tb.Label(win, text="MyDisk Application Settings", font=("Helvetica", 9, "italic"))
        lower_header.pack(pady=(2,25))
    
        # --- Frame for toggles ---
        frame = tb.Frame(win)
        frame.pack(fill="both", expand=True, padx=20)
    

        settings_file = os.path.join(os.getcwd(), "data", "app_config.json")
        self.settings_file = settings_file
        self.load_settings()  
        print(self.settings)

        self.bg_logging_var = tk.BooleanVar(value=self.settings.get("background_logging", False))
        self.bg_logging_toggle = tb.Checkbutton(
            frame,
            text="Background Logging",
            variable=self.bg_logging_var,
            bootstyle="primary",
            onvalue=True,
            offvalue=False
        )
        self.bg_logging_toggle.pack(anchor="w", pady=10)


        def write_settings():

            data = {
                "background_logging": self.bg_logging_var.get()
            }

            write_json(settings_file, data)
            
            with open(settings_file, "w") as f:
                json.dump(data, f, indent=4)
    
    
        # --- Bottom buttons ---
        bottom_button_frame = tb.Frame(win)
        bottom_button_frame.pack(side="bottom", fill="x", pady=10)
    
        inner_bottom = tb.Frame(bottom_button_frame)
        inner_bottom.pack()
    
        # Save Button
        save_btn = tb.Button(inner_bottom, text="Save Settings", bootstyle="primary", command=write_settings)
        save_btn.pack(side="left", padx=5)
    
        # Close Button
        close_btn = tb.Button(inner_bottom, text="Close", bootstyle="secondary", command=win.destroy)
        close_btn.pack(side="left", padx=5)












    def run(self):
        self.root.mainloop()

    def quit_app(self):

        if hasattr(self, "bg_thread") and self.bg_thread.is_alive():
            self.bg_stop_event.set()
            self.bg_thread.join()
        

        try:
            self.tray_icon.stop()
        except:
            pass
    
        self.root.destroy()


    def on_close(self):
        if self.settings.get("background_logging", True):
            self.root.withdraw()   
            # tray already created, nothing else needed
        else:
            if self.tray_icon:
                self.tray_icon.stop()
            self.quit_app()

    def restart_app(self):
        """Restart MyDisk safely from tray"""
        import subprocess, sys, time, os
    
        flag_file = os.path.join(os.getcwd(), "restart.flag")
        with open(flag_file, "w") as f:
            f.write("1")
    
        # Quit current instance
        self.quit_app()
    
        # Small delay so mutex is released and OS closes EXE cleanly
        time.sleep(0.2)
    
        # Relaunch EXE without creating new console
        subprocess.Popen([sys.executable] + sys.argv, creationflags=0x08000000)




if __name__ == "__main__":
    app = App()
    app.run()
