
from supabase_client import supabase
from config import APP_VERSION, PLATFORM, BUILD_TYPE

def log_launch(extra_metadata=None):
    from supabase_client import supabase
    from config import APP_VERSION, PLATFORM, BUILD_TYPE

    if extra_metadata is None:
        extra_metadata = {}

    data = {
        "app_version": APP_VERSION,
        "platform": PLATFORM,
        "build_type": BUILD_TYPE,
        "metadata": extra_metadata
    }

    try:
        res = supabase.table("launch_logs").insert(data).execute()
        # check success
        if res.status_code >= 200 and res.status_code < 300:
            print("Launch logged successfully!")
        else:
            print("Failed to log launch:", res.json())
    except Exception as e:
        print("Could not send analytics (network issue?):", e)