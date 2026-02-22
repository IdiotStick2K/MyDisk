import psutil
import os
import json
import sys
import wmi
from datetime import datetime
import tkinter
from tkinter import messagebox


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
        "analytics_tracking": True
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
        used_history: dict {drive_letter: [used GB values]}
    """

    if log_file is None:
        log_file = os.path.join(os.getcwd(), "data", "storage_log.json")

    logs = read_json(log_file, default=[])

    if not logs:
        return [], [], {}

    timestamps = [datetime.fromisoformat(entry["timestamp"]) for entry in logs]

    drive_names = [d["Drive"] for d in logs[0]["capacity"]]

    used_history = {name: [] for name in drive_names}
    for entry in logs:
        for d in entry["capacity"]:
            used_gb = round(d["Used (MB)"] / 1024, 2)  # MB → GB
            used_history[d["Drive"]].append(used_gb)

    return logs, timestamps, used_history
