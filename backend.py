import psutil
import os
import json
import sys
import wmi
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb
from ttkbootstrap.scrolled import ScrolledFrame   


if getattr(sys, "frozen", False):
    base_dir = os.path.dirname(sys.executable)  
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))  


data_dir = os.path.join(base_dir, "data")
os.makedirs(data_dir, exist_ok=True)


# Default files

FILES = {
    "storage_log.json": [],
    "drives.json": [],
    "app_config.json": {
        "logging_interval_minutes": 10,
        "max_log_entries": 10000,
        "background_logging": True,
        "analytics_tracking": True,
        "theme": "cosmo"
    }
}

APP_VERSION = "Beta 0.2.6"


print("Base dir:", base_dir)
print("Data dir:", data_dir)


print(f"Active Directory: {base_dir}")
# Initialize files

def initialize_json_files():
    """Ensure all JSON files exist with defaults."""
    log_status = True
    for filename, default_data in FILES.items():
        file_path = os.path.join(data_dir, filename)

        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            try:
                with open(file_path, "w") as f:
                    json.dump(default_data, f, indent=4)
                    if filename == "storage_log.json":
                        log_status = False
                print(f"[CREATE] {filename}")
            except Exception as e:
                print(f"[ERROR] Failed to create {filename}: {e}")
        else:
            print(f"[EXISTS] {filename}")
    return log_status
        

# ---UTILITY---

def launch_log():
    return


def startup_logs():
    return

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

def append_log_line(log_file, snapshot):
    with open(log_file, "a") as f:
        f.write(json.dumps(snapshot) + "\n")

def capacity_changed(old, new, threshold_mb=50):
    """
    Check if any drive's used space changed more than `threshold_mb` MB.
    old/new: list of dicts from get_drive_capacity() with "Used (MB)" keys
    """
    if not old:
        return True  # No previous data → always log

    if len(old) != len(new):
        return True  # Drive count changed → log

    for o, n in zip(old, new):
        if abs(o.get("Used (MB)", 0) - n.get("Used (MB)", 0)) >= threshold_mb:
            return True

    return False



# ---GET INFO---
def list_drive_names():

    drives = []

    for partition in psutil.disk_partitions():

        if partition.fstype == "":
            continue

        letter = partition.device.replace("\\", "")
        drives.append(letter)
        
    print(drives)
    return drives

def list_drive_hardware():
    c = wmi.WMI()
    drives = []
    log_file = os.path.join(os.getcwd(), "data/drives.json")
    
    for disk in c.Win32_DiskDrive():
        # Try/except for fields that might be missing
        try:
            drive_info = {
                "model": getattr(disk, "Model", None),
                "serial": getattr(disk, "SerialNumber", None),
                "firmware": getattr(disk, "FirmwareRevision", None),
                "interface": getattr(disk, "InterfaceType", None),
                "media_type": getattr(disk, "MediaType", None),
                "manufacturer": getattr(disk, "Manufacturer", None),
                "status": getattr(disk, "Status", None),
                "size_gb": round(int(getattr(disk, "Size", 0)) / (1024**3), 2),
                "bytes_per_sector": getattr(disk, "BytesPerSector", None),
                "total_sectors": getattr(disk, "TotalSectors", None),
                "total_tracks": getattr(disk, "TotalTracks", None),
                "partitions": getattr(disk, "Partitions", None),
                "capabilities": list(getattr(disk, "Capabilities", []))
            }
        except Exception as e:
            print(f"Error reading disk info: {e}")
            drive_info = {}

        drives.append(drive_info)
    write_json(log_file, drives)
    print(drives)
    return drives
    
# ---Get info helpers---
def get_drive_hardware():
    """
    Reads drives.json, formats the disk info nicely, and returns
    a list of dictionaries ready for the UI.
    """
    log_file = os.path.join(os.getcwd(), "data", "drives.json")
    

    if not os.path.exists(log_file):
        return []  


    try:
        with open(log_file, "r") as f:
            drives = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

   
    formatted_drives = []
    for d in drives:
       
        if not d:
            continue

        # Format each field for human readability
        formatted_drives.append({
            "Model": d.get("model", "Unknown"),
            "Serial": d.get("serial", "Unknown"),
            "Firmware": d.get("firmware", "N/A"),
            "Interface": d.get("interface", "N/A"),
            "Media Type": d.get("media_type", "N/A"),
            "Manufacturer": d.get("manufacturer", "Unknown"),
            "Status": d.get("status", "Unknown"),
            "Size (GB)": f"{d.get('size_gb', 0):,.2f}", 
            "Partitions": d.get("partitions", 0),
            "Capabilities": ", ".join(map(str, d.get("capabilities", []))) if d.get("capabilities") else "None"

        })
    return formatted_drives

def get_drive_capacity():
    """
    Returns used / free / total capacity for each mounted drive.
    """

    drives_capacity = []

    for partition in psutil.disk_partitions():

        if partition.fstype == "":
            continue

        drive_letter = partition.device

        try:
            usage = psutil.disk_usage(partition.mountpoint)

            drive_data = {
                "Drive": drive_letter,
                "Total (MB)": round(usage.total / (1024**2), 1),
                "Used (MB)": round(usage.used / (1024**2), 1),
                "Free (MB)": round(usage.free / (1024**2), 1),
                "Usage (%)": usage.percent
            }

            drives_capacity.append(drive_data)

        except PermissionError:

            continue

    return drives_capacity


    
def log_data_once():

    settings_file = os.path.join(os.getcwd(), "data", "app_config.json")
    settings = read_json(settings_file, default={})
    log_file = os.path.join(os.getcwd(), "data", "storage_log.json")

    raw_log_interval = settings.get("logging_interval_minutes", 10)
    log_interval = raw_log_interval * 60
    print(settings, log_interval)

    current_capacity = get_drive_capacity()

    # Read last entry
    logs = read_json(log_file, default=[])
    last_entry = logs[-1]["capacity"] if logs else None

    if capacity_changed(last_entry, current_capacity, threshold_mb=50):
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "capacity": current_capacity
        }
        logs.append(snapshot)
        write_json(log_file, logs)
        print("[LOGGED STORAGE]", snapshot["timestamp"])
    else:
        print("[SKIPPED] No change in drive usage")

    return log_interval

def load_storage_logs(log_file=None):
    """
    Reads the storage_log.json file and returns formatted data.
    Converts MB → GB for display.
    Returns:
        logs: list of dicts
        timestamps: list of datetime objects
        used_history: dict {drive_letter: [used GB values per timestamp, None if absent]}
    """
    if log_file is None:
        log_file = os.path.join(os.getcwd(), "data", "storage_log.json")

    logs = read_json(log_file, default=[])
    if not logs:
        return [], [], {}

    timestamps = [datetime.fromisoformat(entry["timestamp"]) for entry in logs]

    # Collect every drive ever seen, not just drives in the first snapshot
    all_drives = sorted({d["Drive"] for entry in logs for d in entry.get("capacity", [])})
    used_history = {drive: [] for drive in all_drives}

    for entry in logs:
        present = {d["Drive"]: round(d["Used (MB)"] / 1024, 2) for d in entry.get("capacity", [])}
        for drive in used_history:
            used_history[drive].append(present.get(drive, None))  # None where drive was absent

    return logs, timestamps, used_history

def storage_log_viewer():
    logs, timestamps, used_history = load_storage_logs()

    total_logs = len(timestamps)

    print(total_logs)

    return

def storage_log_viewer_window(self):
    win = tb.Toplevel(self.root)
    win.title("Storage Log Viewer")
    win.geometry("1200x700")

    tb.Label(win, text="Storage Log Viewer", font=("Helvetica", 16, "bold")).pack(pady=(10, 2))
    tb.Separator(win, orient="horizontal").pack(fill="x", padx=20, pady=(0, 10))
    tb.Label(win, text="Double click on a timestamp to edit data values", font=("Helvetica", 8, "bold")).pack(pady=(10, 2))

    logs, timestamps, used_history = load_storage_logs()

    
    main_frame = tb.Frame(win)
    main_frame.pack(fill="both", expand=True, padx=10, pady=5)

    
    left_frame = tb.Frame(main_frame)
    left_frame.pack(side="left", fill="both", expand=True)

    
    right_frame = tb.Frame(main_frame, width=280)
    right_frame.pack(side="right", fill="y", padx=(10, 0))
    right_frame.pack_propagate(False)

    # ── Treeview 
    columns = ("timestamp", "drive", "used_gb", "free_gb", "total_gb", "pct", "delta")
    tree = tb.Treeview(
        left_frame,
        columns=columns,
        show="tree headings",
        selectmode="browse",
        bootstyle="info"
    )
    tree.heading("#0",          text="")
    tree.heading("timestamp",   text="Timestamp")
    tree.heading("drive",       text="Drive")
    tree.heading("used_gb",     text="Used (GB)")
    tree.heading("free_gb",     text="Free (GB)")
    tree.heading("total_gb",    text="Total (GB)")
    tree.heading("pct",         text="Usage %")
    tree.heading("delta", text="Change")

    tree.column("#0",          width=30,  stretch=False)
    tree.column("timestamp",   width=180, anchor="w")
    tree.column("drive",       width=70,  anchor="center")
    tree.column("used_gb",     width=100, anchor="center")
    tree.column("free_gb",     width=100, anchor="center")
    tree.column("total_gb",    width=100, anchor="center")
    tree.column("pct",         width=80,  anchor="center")
    tree.column("delta", width=90, anchor="center")

    scrollbar = tb.Scrollbar(left_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    tree.pack(fill="both", expand=True)

    # ── Populate tree 
    # Map iid → log index for operations
    snapshot_iid_map = {}  # iid → log index

    def populate_tree():
        tree.delete(*tree.get_children())
        snapshot_iid_map.clear()
    
        for i, entry in enumerate(logs):
            ts = entry["timestamp"]
            capacity = entry.get("capacity", [])
    
            parent = tree.insert(
                "", "end",
                values=(ts, "", "", "", "", "", ""),
                open=False,
                tags=("snapshot",)
            )
            snapshot_iid_map[parent] = i
    
            # Build a lookup for the previous snapshot's drives
            prev_used = {}
            if i > 0:
                for pd in logs[i - 1].get("capacity", []):
                    prev_used[pd["Drive"]] = pd["Used (MB)"]
    
            for d in capacity:
                used_gb  = round(d["Used (MB)"]  / 1024, 2)
                free_gb  = round(d["Free (MB)"]  / 1024, 2)
                total_gb = round(d["Total (MB)"] / 1024, 2)
                pct      = d["Usage (%)"]
    
                # Delta vs previous snapshot
                if i == 0 or d["Drive"] not in prev_used:
                    delta_str = "—"
                    delta_tag = "normal"
                else:
                    delta_mb = d["Used (MB)"] - prev_used[d["Drive"]]
                    delta_gb = round(delta_mb / 1024, 2)
                    if delta_gb > 0:
                        delta_str = f"+{delta_gb} GB"
                        delta_tag = "delta_up"
                    elif delta_gb < 0:
                        delta_str = f"{delta_gb} GB"
                        delta_tag = "delta_down"
                    else:
                        delta_str = "No change"
                        delta_tag = "normal"
    
                pct_tag = "critical" if pct >= 90 else "warning" if pct >= 80 else "normal"
                tree.insert(
                    parent, "end",
                    values=("", d["Drive"], used_gb, free_gb, total_gb, f"{pct}%", delta_str),
                    tags=(pct_tag, delta_tag)
                )
    
        tree.tag_configure("snapshot",   font=("Helvetica", 9, "bold"))
        tree.tag_configure("critical",   foreground="#FF5252")
        tree.tag_configure("warning",    foreground="#FFD740")
        tree.tag_configure("normal",     foreground="#00C8AA")
        tree.tag_configure("delta_up",   foreground="#FF5252")
        tree.tag_configure("delta_down", foreground="#00C8AA")

    populate_tree()

    # ── Summary panel
    tb.Label(right_frame, text="Summary", font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(0, 8))
    tb.Separator(right_frame, orient="horizontal").pack(fill="x", pady=(0, 10))

    right_scrollbar = tb.Scrollbar(right_frame, orient="vertical")
    right_scrollbar.pack(side="right", fill="y")
    
    summary_text_widget = tk.Text(
        right_frame, font=("Helvetica", 9), wrap="word",
        yscrollcommand=right_scrollbar.set,
        state="disabled", relief="flat", width=28
    )
    summary_text_widget.pack(fill="both", expand=True)
    right_scrollbar.config(command=summary_text_widget.yview)

    def update_summary():
        summary_text_widget.config(state="normal")
        summary_text_widget.delete("1.0", "end")

        if not logs:
            summary_text_widget.insert("end", "No log data.")
            summary_text_widget.config(state="disabled")
            return
    
        total_snapshots = len(logs)
        all_drives = sorted({d["Drive"] for e in logs for d in e.get("capacity", [])})
        first_ts = logs[0]["timestamp"]
        last_ts  = logs[-1]["timestamp"]
    
        # Time span
        from datetime import datetime
        first_dt = datetime.fromisoformat(first_ts)
        last_dt  = datetime.fromisoformat(last_ts)
        span     = last_dt - first_dt
        span_str = f"{span.days}d {span.seconds // 3600}h"
    
        # Per drive stats across all logs
        drive_stats = {drive: {"used": []} for drive in all_drives}
        for entry in logs:
            present = {d["Drive"]: d for d in entry.get("capacity", [])}
            for drive in all_drives:
                if drive in present:
                    drive_stats[drive]["used"].append(present[drive]["Used (MB)"])
    
        # Latest snapshot
        latest       = logs[-1].get("capacity", [])
        latest_lookup = {d["Drive"]: d for d in latest}
    
        # Previous snapshot for latest delta
        prev_lookup = {}
        if len(logs) >= 2:
            for d in logs[-2].get("capacity", []):
                prev_lookup[d["Drive"]] = d
    
        lines = [
            f"Snapshots:     {total_snapshots}",
            f"Drives:        {', '.join(all_drives)}",
            f"Span:          {span_str}",
            f"First:  {first_ts[:19]}",
            f"Last:   {last_ts[:19]}",
            "",
            "── Per Drive (All Time) ──",
        ]
    
        for drive in all_drives:
            used_list = drive_stats[drive]["used"]
            if not used_list:
                continue
            min_gb   = round(min(used_list)  / 1024, 2)
            max_gb   = round(max(used_list)  / 1024, 2)
            avg_gb   = round(sum(used_list)  / len(used_list) / 1024, 2)
            growth   = round((used_list[-1] - used_list[0]) / 1024, 2) if len(used_list) > 1 else 0
            growth_str = f"+{growth}" if growth >= 0 else str(growth)
    
            # Latest values
            cur = latest_lookup.get(drive)
            cur_str = f"{round(cur['Used (MB)']/1024,2)} GB / {cur['Usage (%)']}%" if cur else "N/A"
    
            # Latest delta
            prev = prev_lookup.get(drive)
            if cur and prev:
                d_gb = round((cur["Used (MB)"] - prev["Used (MB)"]) / 1024, 2)
                d_str = f"+{d_gb} GB" if d_gb >= 0 else f"{d_gb} GB"
            else:
                d_str = "—"
    
            lines += [
                f"\n{drive}",
                f"  Now:     {cur_str}",
                f"  Last Δ:  {d_str}",
                f"  Min:     {min_gb} GB",
                f"  Max:     {max_gb} GB",
                f"  Avg:     {avg_gb} GB",
                f"  Growth:  {growth_str} GB",
            ]
    
        # Total free space across latest snapshot
        total_free = sum(round(d["Free (MB)"] / 1024, 2) for d in latest)
        total_used = sum(round(d["Used (MB)"] / 1024, 2) for d in latest)
        total_cap  = sum(round(d["Total (MB)"] / 1024, 2) for d in latest)
    
        lines += [
            "",
            "── Latest Totals (All Drives) ──",
            f"  Used:  {round(total_used, 2)} GB",
            f"  Free:  {round(total_free, 2)} GB",
            f"  Total: {round(total_cap,  2)} GB",
            f"  Avg Usage: {round(total_used/total_cap*100, 1) if total_cap else 0}%",
        ]
    
        summary_text_widget.insert("end", "\n".join(lines))
        summary_text_widget.config(state="disabled")

    update_summary()

    # ── Edit panel (shown on double click) 
    def on_double_click(event):
        iid = tree.focus()
        if not iid or iid not in snapshot_iid_map:
            return  # clicked a drive child row, not a snapshot

        log_idx = snapshot_iid_map[iid]
        entry   = logs[log_idx]

        edit_win = tb.Toplevel(win)
        edit_win.title(f"Edit Snapshot — {entry['timestamp'][:19]}")
        edit_win.geometry("500x400")

        tb.Label(edit_win, text=f"Editing: {entry['timestamp'][:19]}",
                 font=("Helvetica", 11, "bold")).pack(pady=(10, 5))
        tb.Separator(edit_win, orient="horizontal").pack(fill="x", padx=20, pady=(0, 10))

        edit_frame = tb.Frame(edit_win)
        edit_frame.pack(fill="both", expand=True, padx=20)

        # Build entry fields per drive
        drive_vars = {}
        for d in entry["capacity"]:
            tb.Label(edit_frame, text=d["Drive"], font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(8, 2))
            row = tb.Frame(edit_frame)
            row.pack(fill="x")
            vars_for_drive = {}
            for field in ["Used (MB)", "Free (MB)", "Total (MB)", "Usage (%)"]:
                tb.Label(row, text=field, width=12, anchor="w").pack(side="left")
                var = tk.StringVar(value=str(d[field]))
                tb.Entry(row, textvariable=var, width=12).pack(side="left", padx=(0, 10))
                vars_for_drive[field] = var
            drive_vars[d["Drive"]] = vars_for_drive

        def save_edits():
            try:
                for d in entry["capacity"]:
                    dvars = drive_vars[d["Drive"]]
                    d["Used (MB)"]  = float(dvars["Used (MB)"].get())
                    d["Free (MB)"]  = float(dvars["Free (MB)"].get())
                    d["Total (MB)"] = float(dvars["Total (MB)"].get())
                    d["Usage (%)"]  = float(dvars["Usage (%)"].get())
                _save_logs(logs)
                populate_tree()
                update_summary()
                edit_win.destroy()
            except ValueError:
                tb.dialogs.Messagebox.show_error("All values must be numbers.", title="Invalid Input")

        tb.Button(edit_win, text="Save", bootstyle="primary", command=save_edits).pack(pady=10)

    tree.bind("<Double-1>", on_double_click)

    # ── Operations toolbar 
    tb.Separator(win, orient="horizontal").pack(fill="x", padx=10, pady=(8, 4))
    ops_frame = tb.Frame(win)
    ops_frame.pack(fill="x", padx=10, pady=4)

    # Delete selected snapshot
    def delete_selected():
        iid = tree.focus()
        if not iid or iid not in snapshot_iid_map:
            tb.dialogs.Messagebox.show_warning("Select a snapshot row to delete.", title="No Selection")
            return
        log_idx = snapshot_iid_map[iid]
        confirm = messagebox.askyesno("Delete Entry",
                                      f"Delete snapshot:\n{logs[log_idx]['timestamp'][:19]}?")
        if confirm:
            logs.pop(log_idx)
            _save_logs(logs)
            populate_tree()
            update_summary()

    # Wipe by date range
    def wipe_by_date():
        wipe_win = tb.Toplevel(win)
        wipe_win.title("Wipe by Date Range")
        wipe_win.geometry("360x200")

        tb.Label(wipe_win, text="Wipe entries between these dates",
                 font=("Helvetica", 10, "bold")).pack(pady=(15, 5))
        tb.Label(wipe_win, text="Format: YYYY-MM-DD", font=("Helvetica", 8, "italic")).pack()

        f = tb.Frame(wipe_win)
        f.pack(pady=10)
        tb.Label(f, text="From:", width=6).pack(side="left")
        from_var = tk.StringVar()
        tb.Entry(f, textvariable=from_var, width=14).pack(side="left", padx=5)
        tb.Label(f, text="To:", width=4).pack(side="left")
        to_var = tk.StringVar()
        tb.Entry(f, textvariable=to_var, width=14).pack(side="left", padx=5)

        def do_wipe():
            try:
                from datetime import datetime
                from_dt = datetime.fromisoformat(from_var.get().strip())
                to_dt   = datetime.fromisoformat(to_var.get().strip())
                before  = len(logs)
                logs[:] = [e for e in logs
                            if not (from_dt <= datetime.fromisoformat(e["timestamp"]) <= to_dt)]
                removed = before - len(logs)
                _save_logs(logs)
                populate_tree()
                update_summary()
                wipe_win.destroy()
                tb.dialogs.Messagebox.show_info(f"Removed {removed} entries.", title="Done")
            except ValueError:
                tb.dialogs.Messagebox.show_error("Invalid date format.", title="Error")

        tb.Button(wipe_win, text="Wipe", bootstyle="danger", command=do_wipe).pack(pady=5)

    # Wipe by drive
    def wipe_by_drive():
        all_drives = sorted({d["Drive"] for e in logs for d in e.get("capacity", [])})
        wipe_win = tb.Toplevel(win)
        wipe_win.title("Wipe Drive from Logs")
        wipe_win.geometry("300x180")

        tb.Label(wipe_win, text="Remove a drive from all log entries",
                 font=("Helvetica", 10, "bold")).pack(pady=(15, 10))

        drive_var = tk.StringVar(value=all_drives[0] if all_drives else "")
        tb.Combobox(wipe_win, values=all_drives, textvariable=drive_var,
                    state="readonly", width=16).pack()

        def do_wipe():
            target = drive_var.get()
            for entry in logs:
                entry["capacity"] = [d for d in entry["capacity"] if d["Drive"] != target]
            _save_logs(logs)
            populate_tree()
            update_summary()
            wipe_win.destroy()
            tb.dialogs.Messagebox.show_info(f"Removed {target} from all entries.", title="Done")

        tb.Button(wipe_win, text="Remove Drive", bootstyle="danger", command=do_wipe).pack(pady=10)

    tb.Button(ops_frame, text="Delete Selected",  bootstyle="danger-outline",  command=delete_selected).pack(side="left", padx=4)
    tb.Button(ops_frame, text="Wipe by Date",     bootstyle="warning-outline", command=wipe_by_date).pack(side="left", padx=4)
    tb.Button(ops_frame, text="Wipe by Drive",    bootstyle="warning-outline", command=wipe_by_drive).pack(side="left", padx=4)
    tb.Button(ops_frame, text="Close",            bootstyle="secondary",       command=win.destroy).pack(side="right", padx=4)


def _save_logs(logs, log_file=None):
    """Write the in-memory logs list back to disk."""
    if log_file is None:
        log_file = os.path.join(os.getcwd(), "data", "storage_log.json")
    with open(log_file, "w") as f:
        json.dump(logs, f, indent=4)