from ui import App
from backend import initialize_json_files, list_drive_hardware

if __name__ == "__main__":
    initialize_json_files()
    list_drive_hardware()
    app = App()
    app.run()

