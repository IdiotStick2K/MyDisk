# ui.py
import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from backend import get_drive_hardware, get_drive_capacity, load_storage_logs, log_data_once
import pyperclip
import background  # import module, not specific functions — so we can call start/stop
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
import os
import json
from PIL import Image
import pystray
import sys
import threading
import shutil

# ── Path helpers 
if getattr(sys, "frozen", False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

data_dir = os.path.join(base_dir, "data")


# ── Utility 
def copy_to_clipboard(value, label="Value"):
    pyperclip.copy(str(value))
    print(f"{label} copied to clipboard")


def read_json(file_path, default=None):
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default


def write_json(file_path, data):
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error writing JSON to {file_path}: {e}")
        return False


# ── App 
class App:
    def __init__(self, settings=None):
        self.root = tb.Window(themename="cosmo")
        self.root.title("MyDisk")
        self.root.geometry("800x600")
        # Hide immediately; main.py controls initial visibility
        self.root.withdraw()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.settings = settings if settings is not None else self._load_settings()
        self.tray_icon = None

        self.buttons = {
            "Disk Info":        self.open_disk_info,
            "Storage Logs":     self.open_storage_logs,
            "Storage Summary":  self.open_storage_summary,
            "Tools":            self.open_tools,
            "Settings": self.open_settings
        }

        self.create_main_menu()

    # ── Settings 
    def _load_settings(self):
        settings_file = os.path.join(os.getcwd(), "data", "app_config.json")
        default = {
            "background_logging": True,
            "logging_interval_minutes": 10,
            "max_log_entries": 10000,
        }
        return read_json(settings_file, default=default)

    def _save_settings(self):
        settings_file = os.path.join(os.getcwd(), "data", "app_config.json")
        write_json(settings_file, self.settings)

    # ── Tray
    def create_tray_icon(self):
        icon_path = os.path.join(base_dir, "art", "MyDiskLogo.png")
        icon_image = Image.open(icon_path)
        menu = pystray.Menu(
            pystray.MenuItem("Open MyDisk",   lambda icon, item: self.root.after(0, self.root.deiconify)),
            pystray.MenuItem("Restart MyDisk", lambda icon, item: self.root.after(0, self.restart_app)),
            pystray.MenuItem("Exit",           lambda icon, item: self.root.after(0, self.quit_app)),
        )
        self.tray_icon = pystray.Icon("MyDisk", icon_image, "MyDisk", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True, name="TrayIcon").start()

    # ── Close / Quit
    def on_close(self):
        """Called when the user clicks the window's X button."""
        if self.settings.get("background_logging", True):
            # Keep process alive; just hide the window
            self.root.withdraw()
        else:
            # No background mode — exit completely
            self.quit_app()

    def quit_app(self):
        """Fully shut down the application."""
        background.stop_logger()
        try:
            if self.tray_icon:
                self.tray_icon.stop()
        except Exception:
            pass
        self.root.destroy()
        

    def restart_app(self):
        """Kill self and relaunch — main.py's _kill_previous will handle the rest."""
        import subprocess
        background.stop_logger()
        try:
            if self.tray_icon:
                self.tray_icon.stop()
        except Exception:
            pass
        subprocess.Popen([sys.executable] + sys.argv, creationflags=0x08000000)
        self.root.destroy()

    def run(self):
        self.root.mainloop()

    # ── Main menu 
    def create_main_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        header = tb.Label(self.root, text="Welcome to MyDisk!", font=("Helvetica", 18, "bold"))
        header.pack(pady=30)

        btn_frame = tb.Frame(self.root)
        btn_frame.pack(pady=20, fill="x")

        for text, func in self.buttons.items():
            style = "secondary" if text in ("Tools", "Settings") else "primary"
            btn = tb.Button(btn_frame, text=text, bootstyle=style, width=20, command=func)
            btn.pack(pady=10)

        ver_lbl = tb.Label(self.root, text="Version: Beta 0.2.0", font=("Helvetica", 7, "italic"))
        ver_lbl.pack(pady=20, side="bottom")
        ver_lbl.pack_configure(anchor="center")

        exit_btn = tb.Button(self.root, text="Exit", bootstyle="danger", command=self.quit_app)
        exit_btn.pack(side="bottom", pady=20)

    # ── Sub-windows
    def open_disk_info(self, win=None):
        if win is None or not win.winfo_exists():
            win = tb.Toplevel(self.root)
        else:
            for widget in win.winfo_children():
                widget.destroy()

        win.title("Disk Info")
        win.geometry("1100x600")

        header = tb.Label(win, text="Disk Info Window", font=("Helvetica", 16, "bold"))
        header.pack(pady=10)

        from backend import list_drive_hardware
        list_drive_hardware()
        drives = get_drive_hardware()

        if not drives:
            tb.Label(win, text="No drive data found.").pack(pady=10)
            return

        container = tb.Frame(win)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tb.Canvas(container)
        scrollbar = tb.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tb.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for drive in drives:
            frame = tb.Frame(scrollable_frame)
            frame.pack(fill="x", padx=5, pady=2)
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
                frame, text="Copy", bootstyle="secondary",
                command=lambda t=drive_text: pyperclip.copy(t)
            )
            copy_btn.pack(side="left", padx=10)

        button_frame = tb.Frame(win)
        button_frame.pack(side="bottom", fill="x", pady=10)
        inner_frame = tb.Frame(button_frame)
        inner_frame.pack()
        tb.Button(inner_frame, text="Refresh", bootstyle="info",  command=lambda: self.open_disk_info(win)).pack(side="left", padx=5)
        tb.Button(inner_frame, text="Close",   bootstyle="secondary", command=win.destroy).pack(side="left", padx=5)
        button_frame.pack_configure(anchor="center")

    def open_storage_logs(self, win=None):
        if win is None or not win.winfo_exists():
            win = tb.Toplevel(self.root)
        else:
            for widget in win.winfo_children():
                widget.destroy()
    
        self._logs_window = win
        win.title("Storage Logs")
        win.geometry("800x800")
    
        header = tb.Label(win, text="Storage Logs", font=("Helvetica", 16, "bold"))
        header.pack(pady=10)
    
        logs, timestamps, used_history = load_storage_logs()
    
        fig, ax = plt.subplots(figsize=(8, 5))
    
        if not logs:
            ax.text(0.5, 0.5, "No log data available.", ha="center", va="center", transform=ax.transAxes)
        else:
            lines = {}
            for drive_name, used_values in used_history.items():
                line, = ax.plot(timestamps, used_values, marker="o", label=drive_name, picker=5)
                lines[drive_name] = line
            ax.set_xlabel("Time")
            ax.set_ylabel("Used (GB)")
            ax.set_title("Drive Usage Over Time")
            ax.legend()
            fig.autofmt_xdate()
    
        # --- Event handler for clicks ---
        def on_pick(event):
            line = event.artist
            ind = event.ind[0]  # index of the clicked point
            snapshot = logs[ind]  # use index to match timestamp
    
            text_lines = [f"Snapshot timestamp: {snapshot['timestamp']}"]
            for d in snapshot.get("capacity", []):
                text_lines.append(
                    f"{d['Drive']}: Used {round(d['Used (MB)']/1024,2)} GB, "
                    f"Free {round(d['Free (MB)']/1024,2)} GB, "
                    f"Usage {d['Usage (%)']}%"
                )
    
            self.details_text.config(text="\n".join(text_lines))
    
        canvas_widget = FigureCanvasTkAgg(fig, master=win)
        canvas_widget.draw()
        canvas_widget.get_tk_widget().pack(fill="x", expand=True, padx=10, pady=10)
    
        # Connect the pick event
        fig.canvas.mpl_connect("pick_event", on_pick)
    
        toolbar = NavigationToolbar2Tk(canvas_widget, win)
        toolbar.update()
        canvas_widget.get_tk_widget().pack(fill="x", expand=True, padx=10, pady=(0, 10))
    
        details_frame = tb.Frame(win)
        details_frame.pack(fill="x", padx=10, pady=10)
        tb.Label(details_frame, text="Point Details", font=("Helvetica", 12, "bold")).pack(anchor="w")
        self.details_text = tb.Label(
            details_frame, text="Click a point on the chart to see details.", anchor="w", justify="left"
        )
        self.details_text.pack(fill="x", pady=5)
    
        button_frame = tb.Frame(win)
        button_frame.pack(side="bottom", fill="x", pady=10)
        inner_frame = tb.Frame(button_frame)
        inner_frame.pack()
        tb.Button(inner_frame, text="Refresh", bootstyle="info", command=lambda: self.open_storage_logs(win)).pack(side="left", padx=5)
        tb.Button(inner_frame, text="Close", bootstyle="secondary", command=win.destroy).pack(side="left", padx=5)
        button_frame.pack_configure(anchor="center")

    def open_storage_summary(self):
        win = tb.Toplevel(self.root)
        win.title("Storage Summary")
        win.geometry("800x800")

        tb.Label(win, text="Storage Summary", font=("Helvetica", 16, "bold")).pack(pady=20)

        drive_frame = tb.Frame(win)
        

        def display_drives():
            for widget in drive_frame.winfo_children():
                widget.destroy()
            drives = get_drive_capacity()
            if not drives:
                tb.Label(drive_frame, text="No drive data found.").pack(pady=10)
                return

            total_system_gb = 0
            total_system_used_gb = 0

            for row in tree.get_children():
                tree.delete(row)



            for drive in drives:
                used_gb  = round(drive["Used (MB)"]  / 1024, 2)
                free_gb  = round(drive["Free (MB)"]  / 1024, 2)
                total_gb = round(drive["Total (MB)"] / 1024, 2)
                total_system_gb += round(total_gb, 2)
                total_system_used_gb += round(used_gb, 2)

                tree.insert("", "end", values=(
                    drive['Drive'], total_gb, used_gb, free_gb, drive["Usage (%)"]
                    ))

                '''text = (
                    f"Drive: {drive['Drive']} | Total: {total_gb} GB | "
                    f"Used: {used_gb} GB | Free: {free_gb} GB | Usage: {drive['Usage (%)']} %"
                )'''

                if total_system_gb > 0:
                    total_used_percentage = round((total_system_used_gb / total_system_gb) * 100, 2)
                else:
                    total_used_percentage = 0

            

                # tb.Label(drive_frame, text=text, anchor="w").pack(fill="x", padx=5, pady=2)

            totals_text = (
                f"Total system capacity: {total_system_gb}GB\n"
                f"Total system usage: {total_system_used_gb}GB\n"
                f"Total system capacity used: {total_used_percentage}%\n"
                )
            total_text_lbl = tb.Label(drive_frame, text=totals_text, anchor="center", font=("Helvetica", 16, "bold")).pack(fill="x", padx=5, pady=5)

        table_frame = tb.Frame(win)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        separator = ttk.Separator(win, orient=tk.HORIZONTAL)
        upperseparator = ttk.Separator(win, orient=tk.HORIZONTAL)

        columns = ("Drive", "Total (GB)", "Used (GB)", "Free (GB)", "Usage (%)")

        tree = tb.Treeview(
            master=table_frame,
            columns=columns,
            show="headings",
            bootstyle="secondary")

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, anchor=W, width=100)

        upperseparator.pack(fill=tk.X, pady=5, ipady=6)
        drive_frame.pack(fill="both", expand=True, padx=10, pady=2)
        separator.pack(fill=tk.X, pady=5)
        tree.pack(fill=BOTH, expand=True)

        display_drives()

        button_frame = tb.Frame(win)
        button_frame.pack(side="bottom", pady=5)
        tb.Button(button_frame, text="Refresh", bootstyle="info",      command=display_drives).pack(side="left", padx=5)
        tb.Button(button_frame, text="Close",   bootstyle="secondary",  command=win.destroy).pack(side="left", padx=5)
        button_frame.pack_configure(anchor="center")

    def open_tools(self):
        win = tb.Toplevel(self.root)
        win.title("Tools")
        win.geometry("800x400")
        
       
        tb.Label(win, text="Tools", font=("Helvetica", 16, "bold")).pack(pady=(10, 2))
        tb.Label(win, text="MyDisk Tools", font=("Helvetica", 13, "italic")).pack(pady=(2, 20))
        
       
        tools_frame = tb.Frame(win)
        tools_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Button functions
        def import_storagelog():
            dest_file = os.path.join(data_dir, "storage_log.json")

            selected_file = filedialog.askopenfilename(
                title="Select a JSON storage file",
                filetypes=[("JSON Files", "*.json")],
                initialdir=os.getcwd())

            if not selected_file:
                return

            if os.path.exists(dest_file):
                confirm = messagebox.askyesno(
                    "Overwrite Storage Log?",
                    f"This will replace the current storage log with:\n\n{os.path.basename(selected_file)}\n\nAre you sure?"
                )
                if not confirm:
                    return

            try:
                shutil.copyfile(selected_file, dest_file)
                messagebox.showinfo(
                    "Import Succesful!",
                    f"Storage file imported and saved as 'storage_log.json' in the app data folder."
                )
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import file:\n{str(e)}")



        def add_tool_row(button_texts, commands, description, button_styles=None):
            """
            button_texts : list of str
            commands     : list of functions
            description  : str
            button_styles: list of styles (optional)
            """
            row_frame = tb.Frame(tools_frame)
            row_frame.pack(fill="x", pady=5, anchor="center")
            
            
            for i, txt in enumerate(button_texts):
                style = button_styles[i] if button_styles else "info"
                tb.Button(row_frame, text=txt, bootstyle=style, command=commands[i]).pack(anchor="center", padx=5)
            
     
            tb.Label(tools_frame, text=description, font=("Helvetica", 8, "italic"), wraplength=760, justify="center").pack(anchor="center", padx=5, pady=(2, 10))
        

        add_tool_row(
            button_texts=["Log Disks"],
            commands=[log_data_once],
            description="Logs the current capacity of all disks."
        )
        
        add_tool_row(
            button_texts=["Import Storage File"],
            commands=[import_storagelog],
            description = (
                "Makes importing an old storage file easy!\n"
                "Simply navigate to your old storage file\n"
                "(MyDisk->dist->MyDisk->data->storage_log.json), select it, and press Open!"
)
            )
        
        '''add_tool_row(
            button_texts=["Placeholder Button 1", "Placeholder Button 2"],
            commands=[lambda: print("1"), lambda: print("2")],
            description="This is an example row with multiple buttons on the same line.",
            button_styles=["primary", "secondary"]
        )'''
        

        bottom_frame = tb.Frame(win)
        bottom_frame.pack(side="bottom", fill="x", pady=10)
        
        tb.Button(bottom_frame, text="Close", bootstyle="secondary", command=win.destroy).pack(anchor="center", padx=5)

    def open_settings(self):
        win = tb.Toplevel(self.root)
        win.title("Settings")
        win.geometry("800x300")

        tb.Label(win, text="Settings",                   font=("Helvetica", 16, "bold")).pack(pady=(10, 2))
        tb.Label(win, text="MyDisk Application Settings", font=("Helvetica", 9, "italic")).pack(pady=(2, 25))

        frame = tb.Frame(win)
        frame.pack(fill="both", expand=True, padx=20)

        bg_var = tk.BooleanVar(value=self.settings.get("background_logging", True))
        tb.Checkbutton(
            frame, text="Background Logging", variable=bg_var,
            bootstyle="primary", onvalue=True, offvalue=False
        ).pack(anchor="w", pady=10)

        def write_settings():
            self.settings["background_logging"] = bg_var.get()
            self._save_settings()
            # Apply immediately: start or stop logger depending on new value
            if self.settings["background_logging"]:
                background.start_logger()
            else:
                background.stop_logger()

        bottom_button_frame = tb.Frame(win)
        bottom_button_frame.pack(side="bottom", fill="x", pady=10)
        inner_bottom = tb.Frame(bottom_button_frame)
        inner_bottom.pack()
        tb.Button(inner_bottom, text="Save Settings", bootstyle="primary",   command=write_settings).pack(side="left", padx=5)
        tb.Button(inner_bottom, text="Close",          bootstyle="secondary", command=win.destroy).pack(side="left", padx=5)


if __name__ == "__main__":
    app = App()
    app.create_tray_icon()
    app.root.deiconify()
    app.run()